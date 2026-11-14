# Volume Heatmap Tools

A collection of tools for preparing, sampling and exporting data for the Volume Heatmap plugin for Unreal Engine.

Each tool has its own directory, installation instructions and usage guide. This repository contains companion tools; it does not include the Unreal Engine plugin itself.

## Available tools

| Tool | Host application | Description |
| --- | --- | --- |
| [VolumeHeatmap Exporter](Houdini/VolumeHeatmapExporter/) | Houdini 20.5 / Python 3.11 | Sample Pyro density and temperature fields, generate optional smoke shells, and export static CSV frames or `.vhanim` animations. |

## Getting started

Download this repository using **Code → Download ZIP**, or clone it:

```sh
git clone https://github.com/inlet511/VolumeHeatmap_Tools.git
```

Then follow the README in the tool's directory. You can also distribute an individual tool folder with its contents intact.

## Repository layout

```text
VolumeHeatmap_Tools/
└── Houdini/
    └── VolumeHeatmapExporter/
        ├── README.md
        ├── install.ps1
        ├── python3.11libs/
        ├── python_panels/
        └── toolbar/
```

Additional tools can be added under the directory for their host application and listed in the table above.

## Support

Report problems through [GitHub Issues](https://github.com/inlet511/VolumeHeatmap_Tools/issues). Include the tool version, host application version, reproduction steps and any error messages.
