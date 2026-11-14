"""Houdini tools for VolumeHeatmap scalar animation interchange."""

__version__ = "1.2.0"


def show():
    # Shelf callbacks run on Houdini's UI thread. Never call Qt through an RPC worker.
    from .panel import show_window
    return show_window()


def reload_panel():
    """Reload the floating panel from Houdini's Python Shell/main UI thread."""
    import importlib
    from . import core, i18n, panel

    previous = panel._window
    settings = previous.collect() if previous is not None else None
    geometry = previous.saveGeometry() if previous is not None else None
    importlib.invalidate_caches()
    importlib.reload(i18n)
    importlib.reload(core)
    importlib.reload(panel)
    window = panel.show_window()
    if settings is not None:
        window.populate(settings)
        window.restoreGeometry(geometry)
    if previous is not None:
        previous.close()
        previous.deleteLater()
    return window
