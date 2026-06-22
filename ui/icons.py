def get_pipeline_icon(status: str) -> str:
    match status:
        case 'success':
            return '✅'
        case 'failed':
            return '❌'
        case 'running':
            return '🏃'
        case _:
            return '❓'