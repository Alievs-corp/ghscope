from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional, Sequence

import logging

from dateutil.parser import isoparse

from ghscope.analytics.activity import AnalyticsResult, compute_analytics
from ghscope.auth.app import GitHubAuth
from ghscope.auth.token import TokenConfig
from ghscope.client.graphql import GitHubGraphQLClient
from ghscope.collectors.commits import collect_repository_commits
from ghscope.collectors.issues import collect_repository_issues
from ghscope.collectors.pull_requests import collect_repository_pull_requests
from ghscope.collectors.repos import collect_org_repositories, collect_user_repositories
from ghscope.collectors.users import collect_org_members, collect_user
from ghscope.exporters.csv import export_csv
from ghscope.exporters.html import export_html
from ghscope.exporters.json import export_json
from ghscope.exporters.markdown import export_markdown
from ghscope.models import Commit, Issue, PullRequest, Repository, User
from ghscope.report.context import ReportContext


logger = logging.getLogger("ghscope.report.builder")


@dataclass
class ReportBuilder:
    org: Optional[str]
    user: Optional[str]
    since: str
    until: str
    token: Optional[str]
    templates_dir: Optional[Path] = None

    def _parse_dates(self) -> tuple[datetime, datetime]:
        since_dt = isoparse(self.since)
        until_dt = isoparse(self.until)

        if since_dt.tzinfo is None:
            since_dt = since_dt.replace(tzinfo=timezone.utc)
        if until_dt.tzinfo is None:
            until_dt = until_dt.replace(tzinfo=timezone.utc)

        return since_dt, until_dt

    def _templates_dir(self) -> Path:
        if self.templates_dir is not None:
            return self.templates_dir
        return Path(__file__).with_suffix("").parent / "templates"

    def _build_clients(self) -> GitHubGraphQLClient:
        auth = GitHubAuth(TokenConfig(explicit_token=self.token))
        return GitHubGraphQLClient(auth=auth)

    def _collect_scope(
        self,
        client: GitHubGraphQLClient,
        since: datetime,
        until: datetime,
    ) -> tuple[
        Sequence[User],
        Sequence[Repository],
        Sequence[Commit],
        Sequence[PullRequest],
        Sequence[Issue],
    ]:
        users: list[User] = []
        repos: list[Repository] = []

        if self.org:
            users.extend(collect_org_members(client, self.org))
            repos.extend(collect_org_repositories(client, self.org))
        if self.user:
            users.append(collect_user(client, self.user))
            repos.extend(collect_user_repositories(client, self.user))

        commits: list[Commit] = []
        pull_requests: list[PullRequest] = []
        issues: list[Issue] = []
        for repo in repos:
            commits.extend(
                collect_repository_commits(
                    client,
                    repo_full_name=repo.full_name,
                    since=since,
                    until=until,
                ),
            )
            pull_requests.extend(
                collect_repository_pull_requests(
                    client,
                    repo_full_name=repo.full_name,
                    since=since,
                    until=until,
                ),
            )
            issues.extend(
                collect_repository_issues(
                    client,
                    repo_full_name=repo.full_name,
                    since=since,
                    until=until,
                ),
            )

        logger.info(
            "Scope collection complete: %d users, %d repositories, %d commits, %d pull requests, %d issues",
            len(users),
            len(repos),
            len(commits),
            len(pull_requests),
            len(issues),
        )
        return users, repos, commits, pull_requests, issues

    def _build_analytics(
        self,
        since: datetime,
        until: datetime,
        users: Iterable[User],
        repos: Iterable[Repository],
        commits: Iterable[Commit],
        pull_requests: Iterable[PullRequest],
        issues: Iterable[Issue],
    ) -> AnalyticsResult:
        return compute_analytics(
            users=users,
            repositories=repos,
            commits=commits,
            pull_requests=pull_requests,
            issues=issues,
            since=since,
            until=until,
        )

    def _build_context(
        self,
        analytics: AnalyticsResult,
        since: datetime,
        until: datetime,
        users: Iterable[User],
        repos: Iterable[Repository],
        commits: Iterable[Commit],
        pull_requests: Iterable[PullRequest],
        issues: Iterable[Issue],
    ) -> ReportContext:
        return ReportContext(
            org=self.org,
            user=self.user,
            since=since,
            until=until,
            activity=analytics.activity,
            timelines=analytics.timelines,
            users=list(users),
            repositories=list(repos),
            commits=list(commits),
            pull_requests=list(pull_requests),
            issues=list(issues),
            generated_at=datetime.utcnow(),
            templates_dir=self._templates_dir(),
        )

    def build_and_export(
        self,
        format_name: str,
        output_path: Optional[str],
    ) -> None:
        since_dt, until_dt = self._parse_dates()
        client = self._build_clients()
        try:
            users, repos, commits, pull_requests, issues = self._collect_scope(
                client,
                since=since_dt,
                until=until_dt,
            )
        finally:
            client.close()

        analytics = self._build_analytics(
            since=since_dt,
            until=until_dt,
            users=users,
            repos=repos,
            commits=commits,
            pull_requests=pull_requests,
            issues=issues,
        )
        context = self._build_context(
            analytics,
            since=since_dt,
            until=until_dt,
            users=users,
            repos=repos,
            commits=commits,
            pull_requests=pull_requests,
            issues=issues,
        )

        target_path = Path(output_path) if output_path is not None else None
        templates_dir = context.templates_dir
        fmt = format_name.lower()

        if fmt == "md":
            export_markdown(context, templates_dir, target_path)
        elif fmt == "html":
            export_html(context, templates_dir, target_path)
        elif fmt == "pdf":
            if target_path is None:
                raise ValueError("PDF export requires an explicit --output path.")
            from ghscope.exporters.pdf import export_pdf

            export_pdf(context, templates_dir, target_path)
        elif fmt == "json":
            export_json(context, target_path)
        elif fmt == "csv":
            export_csv(context, target_path)
        else:
            raise ValueError(f"Unsupported format: {format_name!r}")

