# VolumeHeatmap Exporter for Houdini

**Version 1.2.0**

Convert Houdini Pyro fields into sample data for the Volume Heatmap plugin for Unreal Engine. The exporter creates an editable SOP network in a separate Geometry object, samples the original temperature field, and exports a static CSV frame or a `.vhanim` animation.

## Features

- Select a standard Pyro Geometry object, DOP network, Pyro Solver SOP or volume cache.
- Allocate an interior point budget according to density and temperature importance.
- Add a shell that follows the smoke contour and expands outward.
- Use a fixed shell point count or adjust it per frame according to enclosed volume.
- Choose the source frame range, keyframe interval and animation duration independently.
- Export a single frame without configuring an animation range.
- Switch between English and Chinese without resetting parameters.
- Save generated SOP nodes and sampling settings with the HIP file.

## Requirements

| Requirement | Details |
| --- | --- |
| Houdini | Target environment: Houdini 20.5 with Python 3.11. Other versions have not been verified. |
| Operating system | The included installer is for Windows. A manual Houdini Package setup is described below. |
| Source data | Volume fields named `density` and `temperature`, from a simulation or cache. |
| Unreal Engine | The Volume Heatmap plugin is required to consume the exported files. |
| Python dependencies | Only Houdini's bundled Python, Qt bindings and standard library are required. No pip installation or MCP server is needed. |

## Installation

### Windows

1. Download or clone this repository.
2. Keep the tool folder in a permanent location. The installer registers this folder in Houdini; it does not copy it into the preferences directory.
3. Open PowerShell in `Houdini/VolumeHeatmapExporter` and run:

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\install.ps1
   ```

   By default, the script writes `volumeheatmap_exporter.json` to the `packages` folder in your Windows Documents/Houdini 20.5 preferences directory. An existing package file is backed up before replacement.

   For a custom Houdini preferences directory:

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\install.ps1 -HoudiniPreferences 'D:\HoudiniPrefs\houdini20.5'
   ```

4. Restart Houdini.
5. Enable the **VolumeHeatmap** shelf from the shelf menu and click **Pyro Exporter**.

The **Language** selector at the top of the panel offers **中文** and **English**. Chinese is the initial default; your selection is remembered locally.

### Manual package registration

Create `volumeheatmap_exporter.json` inside the `packages` directory of your Houdini user preferences:

```json
{
  "enable": true,
  "hpath": "D:/HoudiniTools/VolumeHeatmap_Tools/Houdini/VolumeHeatmapExporter"
}
```

Replace `hpath` with the absolute path to this tool folder, using forward slashes. Restart Houdini. The same package structure can be registered on other operating systems, but those environments have not been verified.

### Other ways to open the panel

Use a Python Panel pane and select **VolumeHeatmap Exporter**, or run this in Houdini's **Windows → Python Shell**:

```python
import volumeheatmap_exporter
volumeheatmap_exporter.show()
```

## Quick start

1. Create a normal Pyro simulation. Cache it with both `density` and `temperature` retained before exporting a long animation.
2. Select the Pyro Geometry object, DOP network, solver SOP or volume cache.
3. Click **Use Selected Node** in the exporter. Use **Detect Fields** to refresh the detected sources after editing the source path.
4. Set **Interior Point Budget**, for example `800`.
5. Optionally enable **Enable Shell** and configure its point count and expansion.
6. Click **Create / Update Branch**. The output is usually `/obj/VH_PyroExport/OUT_HEATMAP`; Houdini gives additional branches a unique name.
7. Set **Export Folder**, then export a static frame or animation using the instructions below.
8. Save the HIP file to preserve the generated branch and its settings.

The original Pyro object does not need any exporter-specific helper nodes. Imports, sampling and shell construction are created in the separate sampling branch. Updating the branch reapplies the panel settings to its generated nodes.

## Selecting Pyro fields

| Selected source | How it is resolved |
| --- | --- |
| Geometry object | Follows the object's display output. |
| Pyro Bake Volume / Pyro Post-Process | Follows the first input to find the original volume data. |
| DOP network | Reads `density` and `temperature` from the simulation. |
| Native Object Merge reading a DOP density/temperature field | Derives the corresponding DOP field addresses. |
| Pyro Solver SOP or volume cache | Uses the selected SOP directly as the field source. |

Automatic detection does not inspect every disconnected node or modify the simulation. Custom networks may require choosing a more direct source or overriding **Density Source** and **Temperature Source**. A selected cache is not automatically bypassed to run the simulation upstream. If the cache does not contain `temperature`, export that field into the cache or select another output that retains it.

### Understanding DOP field addresses

For example:

```text
/obj/pyro_simulation:*/temperature
```

- `/obj/pyro_simulation` identifies the DOP network.
- `:` separates the node path from the DOP data address.
- `*` matches simulation objects inside that network.
- `/temperature` identifies the field to import.

This is an Object Merge field address, not the path to a SOP node you can browse to. Choose the DOP network in **Pyro Object / Volume SOP**, then click **Detect Fields** to fill these addresses. For multiple simulations in one network, specify the intended field addresses manually to avoid combining unrelated objects.

## Interior sampling

| Control | Effect |
| --- | --- |
| Interior Point Budget | Caps the requested number of adaptive interior points. Start with 400–800. |
| Density Threshold | Rejects low sampling weights and sets the density contour threshold used to build the shell. |
| Density Contrast | Values below 1 give thin smoke more relative weight; values above 1 favor dense regions. |
| Temperature Weight | Adds importance to hot regions with little smoke. Set to 0 for density-only allocation. |
| Random Seed | Controls the sampling seed. |

The sampling weight is `max(density, Temperature Weight × temperature)`, followed by thresholding and the density contrast exponent. This changes point allocation only. Exported `value` remains the sampled original `temperature`.

## Shell sampling

Enable **Enable Shell** to extract the smoke's density contour, convert it to an SDF, expand it and sample the resulting surface.

| Control | Effect |
| --- | --- |
| Shell Point Count | Fixed point count when volume adjustment is disabled. |
| Adjust Count by Volume | Recomputes the shell point count at each source frame. |
| Shell Point Limit | Maximum shell point count when volume adjustment is enabled. |
| Points per Cubic Unit | Number of shell points requested per cubic Houdini unit of enclosed volume. |
| Expansion Distance | Outward offset in Houdini units. A starting value is `0.3`. |
| Shell Voxel Size | SDF resolution. Smaller values improve detail and cost more time and memory. A starting value is `0.2`. |

In dynamic mode:

```text
requested count = ceil(expanded shell volume × points per cubic unit)
```

The result is capped by **Shell Point Limit**. A nonempty shell with positive volume receives at least one point; an empty surface produces no shell points. The volume is measured from the expanded surface rather than its bounding box. For a density of `2`, a volume of `20` requests `40` points, while a volume of `80` requests `160` points, until the limit is reached.

Both modes place points on the shell surface. All points read the original temperature; shell points are not forced to zero. There is no separate box-boundary sampling option.

## Exporting an animation

1. Set **Start Frame**, **End Frame** and **Keyframe Step**. The step is measured in Houdini frames.
2. Set **Duration / Seconds**. **Use Houdini FPS** calculates the natural duration from the source range and Houdini's FPS.
3. Choose **Export Folder** and click **Export UE Animation**.

The end frame is always included, even when the step does not divide the range evenly. For example, frames `1–121` with step `3` produce `41` keys. A duration of `5` seconds places those keys `0.125` seconds apart. Changing duration remaps playback time without changing the sampled source frames.

Each export creates a new timestamped folder:

```text
<export folder>/<timestamp>/
├── ThermalField.vhanim
├── FirstFrame.csv
└── ExportInfo.json
```

Animations use the `VolumeHeatmap.Animation` version 1 format with `field_blend` transitions, allowing point positions and counts to vary between keys. `FirstFrame.csv` contains the first animation key as a static frame. `ExportInfo.json` records settings, source frames, point counts, value ranges and UE bounds.

## Exporting a static frame

1. Set **Static Frame**, or click **Use Current Frame**.
2. Choose **Export Folder**.
3. Click **Export Static CSV**.

Static export does not require a valid animation range. It creates a timestamped folder containing `Frame.csv` and `ExportInfo.json`.

The default output folder is `$HIP/VolumeHeatmapExport`. Save the HIP file first or choose an explicit output directory. Exports restore the original timeline frame after sampling or cancellation. Completed exports are written to a temporary directory before being renamed to the final timestamped directory.

## Coordinates, values and Unreal Engine

CSV files contain metadata comments followed by these columns:

```csv
index,x,y,z,value
```

Coordinate conversion is:

```text
UE X = Houdini X × 100
UE Y = Houdini Z × 100
UE Z = Houdini Y × 100
```

Positions are exported in centimeters. When choosing a Geometry object or one of its SOPs, the exporter uses that object's local space and excludes its object transform. Direct DOP selection uses the imported simulation field coordinates. Check alignment if the source object has a nonidentity transform.

`value` contains raw Pyro `temperature`. It is not automatically converted to degrees Celsius.

Import the `.vhanim` or CSV through the Volume Heatmap plugin's animation or sample-frame import workflow. Use **Fit Bounds to Data** on the Volume Heatmap component and check its transform to align the field with your source mesh. This tool exports field data; it does not export the heat-source mesh.

## Limits and troubleshooting

- **Point limit:** Interior Point Budget + Shell Point Limit must not exceed **4096**. In fixed mode, use Shell Point Count instead. The actual number of points can be lower.
- **Key limit:** A maximum of **256** animation keys. Increase Keyframe Step for longer sequences.
- **Empty frames:** A completely empty sample frame cannot be exported. Choose a source range that contains usable data.
- **Missing temperature:** Retain the original temperature field in the solver/cache. A render-oriented bake can discard it.
- **Missing shell:** Confirm smoke is present. Try a lower density threshold or smaller shell voxel size.
- **Dynamic count looks constant:** The count may have reached Shell Point Limit. Reduce Points per Cubic Unit or raise the limit while staying within the total point budget.
- **Slow export:** Cache the simulation first, reduce the number of keys or use a larger shell voxel size. Exporting uncached frames may cause Houdini to simulate them.
- **Tool not found:** Check the package path, restart Houdini and enable the VolumeHeatmap shelf. No MCP connection is required.
- **Older HIP files:** Retired box-boundary settings are ignored. Updating a managed branch disconnects the old boundary nodes and removes them when no custom nodes reference them.

## Updating and uninstalling

To update, replace the tool files or pull the latest repository changes. If the path changes, run the installer again. Restart Houdini, or reload the floating panel from Houdini's Python Shell:

```python
import importlib
import volumeheatmap_exporter
importlib.reload(volumeheatmap_exporter).reload_panel()
```

The reload preserves the floating panel's sampling parameters. Close and recreate an embedded Python Panel to refresh that instance.

To uninstall, remove `volumeheatmap_exporter.json` from your Houdini preferences `packages` directory and restart Houdini. Generated sampling nodes already saved in a HIP remain in the scene.
