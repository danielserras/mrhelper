from dataclasses import dataclass
from datetime import datetime, timezone

import config


@dataclass
class MergeRequest:
    title: str
    description: str
    project: str
    author: str
    state: str
    iid: int
    project_id: int
    web_url: str
    comments: int
    approvers: list
    approved_by_me: str
    comment_count: int
    approval_state: str
    created_at: datetime
    pipeline_status: str
    stale_icon: str
    conflict_icon: str

    @staticmethod
    def from_gitlab_data(
            mr: dict,
            approvals: dict,
            comments: list,
            details: dict,
            pipeline_status: str,
            project_name: str
    ) -> 'MergeRequest':

        updated_at = datetime.fromisoformat(mr['updated_at'].replace('Z', '+00:00'))
        stale_icon = MergeRequest.calculate_stale_icon(approvals, comments, updated_at)
        conflict_icon = MergeRequest.calculate_conflict_icon(details)
        approved_by_me = MergeRequest.calculate_approved_by_me(approvals)

        return MergeRequest(
            title=mr.get('title', '-'),
            description=mr.get('description', ''),
            project=project_name,
            author=mr.get('author', {}).get('username', '-'),
            state=mr.get('state', '-'),
            iid=mr.get('iid'),
            project_id=mr.get('project_id'),
            web_url=mr.get('web_url', '-'),
            comments=len(comments),
            approvers=approvals.get('approved_by', []),
            approved_by_me=approved_by_me,
            comment_count=len(comments),
            approval_state=approved_by_me,
            created_at=datetime.fromisoformat(mr.get('created_at').replace('Z', '+00:00')),
            pipeline_status=pipeline_status,
            stale_icon=stale_icon,
            conflict_icon=conflict_icon,
        )

    @staticmethod
    def calculate_conflict_icon(details: dict) -> str:
        conflict_icon = '❌'
        if details.get('has_conflicts') or details.get('merge_status') in {'cannot_be_merged', 'unchecked'}:
            conflict_icon = '✅'
        return conflict_icon

    @staticmethod
    def calculate_stale_icon(approvals: dict, comments: list, updated_at: datetime) -> str:
        now = datetime.now(timezone.utc)
        stale_icon = '--'
        if (now - updated_at).days > 3:
            stale_icon = '⚠️'
            if len(approvals.get('approved_by', [])) == 0 and len(comments) == 0:
                stale_icon = '🔥'
        return stale_icon

    @staticmethod
    def calculate_approved_by_me(approvals: dict) -> str:
        if approvals.get("user_has_approved", False):
            return '✅'
        return '❌'

