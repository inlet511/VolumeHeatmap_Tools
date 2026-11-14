"""Load shelf/panel into an already running Houdini, on the UI thread."""
from pathlib import Path

import hou


def load_and_show():
    from . import show
    root = Path(__file__).resolve().parents[2]
    hou.shelves.loadFile(str(root / "toolbar" / "volumeheatmap_exporter.shelf"))
    hou.pypanel.installFile(str(root / "python_panels" / "volumeheatmap_exporter.pypanel"))
    # Add the new shelf to an existing shelf set; keep the user's other shelves.
    desktop = hou.ui.curDesktop()
    dock = desktop.shelfDock()
    for shelf_set in dock.shelfSets():
        shelf = hou.shelves.shelves().get("volumeheatmap_exporter")
        existing = shelf_set.shelves()
        if shelf and shelf not in existing:
            shelf_set.setShelves(existing + (shelf,))
        break
    return show()


def schedule_open():
    import hdefereval
    hdefereval.executeDeferred(load_and_show)
