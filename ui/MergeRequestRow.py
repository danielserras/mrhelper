import re
from rich.text import Text
from models.MergeRequest import MergeRequest

class MergeRequestRow:
    PIPELINE_ICONS = {
        "success": "✅",
        "failed": "❌",
        "running": "🏃",
        "pending": "⏳",
        "canceled": "🚫",
        "unknown": "❔",
    }

    @classmethod
    def from_merge_request(cls, mr: MergeRequest, show_full_title: bool = False, seen: bool = False) -> list[Text]:
        approves_count = len(mr.approvers)
        approves_style = 'green' if approves_count >= 2 else 'red'
        
        return [
            Text(mr.author, justify='left'),
            Text(mr.project, justify='left'),
            Text(
                mr.title if show_full_title else cls.shorten_title(mr.title),
                justify='left'
            ),
            Text(cls.clean_text(str(approves_count)), style=approves_style, justify='center'),
            Text(cls.clean_text(mr.approved_by_me), justify='center'),
            Text(cls.safe_icon('✅' if seen else '❌'), justify='center'),
            Text(cls.clean_text(str(mr.comments)), justify='center'),
            Text(mr.created_at.strftime('%Y-%m-%d'), justify='center'),
            Text(cls.safe_icon(mr.conflict_icon), justify='center'),
            Text(cls.safe_icon(cls.PIPELINE_ICONS.get(mr.pipeline_status, '❔')), justify='center'),
        ]

    @staticmethod
    def shorten_title(title: str, max_len: int = 15) -> str:
        return title if len(title) <= max_len else title[:max_len - 3] + '...'

    @staticmethod
    def clean_text(text: str) -> str:
        return re.sub(r'\s+', ' ', text).strip()

    @staticmethod
    def safe_icon(value: str) -> str:
        # Keep only allowed icon characters
        cleaned = re.sub(r"[^\w❌🔥⚠️✅⏳🏃🚫❔]", "", value or "")
        return cleaned.strip()[:1] or "--"
