from importlib import resources

__all__ = ["default_theme_css"]

def default_theme_css() -> str:
    """Return the bundled default theme.css content as a string."""
    try:
        return resources.files("melk.resources").joinpath("default_theme.css").read_text()
    except Exception:
        return ""
