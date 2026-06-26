from version import __version__


GITHUB_USERNAME = "danielserras"


def build_footer_label() -> str:
    return f"{GITHUB_USERNAME} | v{__version__}"
