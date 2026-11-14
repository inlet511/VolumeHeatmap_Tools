"""Editable SOP sampling graph and bounded VolumeHeatmap v1 export."""
import csv
import json
import math
import shutil
import struct
import uuid
from dataclasses import asdict, dataclass, fields
from datetime import datetime
from pathlib import Path

import hou

from .i18n import MessageError, tr

SETTINGS_KEY = "volumeheatmap_exporter_settings"


@dataclass
class Settings:
    source: str = ""
    density_source: str = ""
    temperature_source: str = ""
    start: int = 1
    end: int = 121
    step: int = 3
    duration: float = 5.0
    static_frame: int = 1
    interior_count: int = 800
    shell: bool = False
    shell_count: int = 128
    shell_dynamic: bool = False
    shell_density: float = 1.0
    shell_expansion: float = 0.3
    shell_voxel: float = 0.2
    density_cutoff: float = 0.002
    density_contrast: float = 0.6
    heat_weight: float = 0.25
    seed: int = 17
    output_dir: str = "$HIP/VolumeHeatmapExport"
    target: str = ""


def load_settings(data):
    """Read saved settings, discarding options removed from older versions."""
    names = {field.name for field in fields(Settings)}
    return Settings(**{key: value for key, value in data.items() if key in names})


def key_frames(settings):
    if settings.step < 1 or settings.end <= settings.start:
        raise MessageError("结束帧须大于起始帧，关键帧间隔至少为 1 帧。")
    # Always include the endpoint without silently changing the requested interval.
    count = (settings.end - settings.start) // settings.step + 1
    if (settings.end - settings.start) % settings.step:
        count += 1
    if count > 256:
        raise MessageError("共 {count} 个关键帧，超过 256；请增大关键帧间隔。", count=count)
    frames = list(range(settings.start, settings.end + 1, settings.step))
    if frames[-1] != settings.end:
        frames.append(settings.end)
    if len(frames) > 256:
        raise MessageError("共 {count} 个关键帧，超过 256；请增大关键帧间隔。", count=len(frames))
    return frames


def point_budget(settings):
    return settings.interior_count + (settings.shell_count if settings.shell else 0)


def validate(settings, animation=True):
    if animation:
        key_frames(settings)
    if animation and (not math.isfinite(settings.duration) or not 0 < settings.duration <= 86400):
        raise MessageError("总时间须大于 0 且不超过 86400 秒。")
    if not 1 <= settings.interior_count <= 4096:
        raise MessageError("内部点数须为 1..4096。")
    if settings.shell and (not 1 <= settings.shell_count <= 4096 or
                           settings.shell_expansion < 0 or settings.shell_voxel <= 0):
        raise MessageError("请检查包壳点数、扩张距离和体素大小。")
    if settings.shell_dynamic and settings.shell_density <= 0:
        raise MessageError("包壳密度须大于 0。")
    if point_budget(settings) > 4096:
        raise MessageError("合计最多 {count} 点，超过插件 4096 点限制；请减少采样点。", count=point_budget(settings))
    nums = (settings.density_cutoff, settings.density_contrast, settings.heat_weight,
            settings.shell_expansion, settings.shell_voxel, settings.shell_density)
    if not all(math.isfinite(v) for v in nums):
        raise MessageError("各项参数须为有限数值。")
    if settings.density_cutoff < 0 or settings.density_contrast <= 0 or settings.heat_weight < 0:
        raise MessageError("密度阈值和温度权重不能为负，浓度对比须大于 0。")


def _source_object(node):
    while node is not None:
        if node.type().category() == hou.objNodeTypeCategory() and node.type().name() == "geo":
            return node
        node = node.parent()
    return None


def _dop_merge_sources(node):
    """Read native Object Merge DOP addresses without requiring helper SOPs."""
    prefixes = set()
    count = node.parm("numobj").evalAsInt()
    for index in range(1, count + 1):
        parm = node.parm(f"objpath{index}")
        value = parm.evalAsString().strip() if parm else ""
        prefix, separator, field = value.rpartition("/")
        if separator and ":" in prefix and field in ("density", "temperature"):
            network_path, _, object_path = prefix.partition(":")
            network = node.node(network_path)
            if network and network.childTypeCategory() == hou.dopNodeTypeCategory():
                prefixes.add(network.path() + ":" + object_path)
    if len(prefixes) > 1:
        raise MessageError("此 Object Merge 引用了多个 Pyro 模拟，请指定单一模拟的 DOP 网络或字段来源。")
    if prefixes:
        prefix = prefixes.pop()
        return prefix + "/density", prefix + "/temperature"
    return None


def detect_sources(path):
    """Resolve standard OBJ/DOP/SOP Pyro outputs without cooking the simulation."""
    node = hou.node(path)
    if node is None:
        raise MessageError("请选择存在的 Pyro 对象、DOP 网络或含体积字段的 SOP。")
    if node.childTypeCategory() == hou.dopNodeTypeCategory():
        return node.path() + ":*/density", node.path() + ":*/temperature"
    if _source_object(node) == node:
        node = node.displayNode()
        if node is None:
            raise MessageError("所选几何对象没有显示输出，请选择 Pyro Solver 或体积缓存 SOP。")
    elif not isinstance(node, hou.SopNode):
        raise MessageError("此节点不是几何对象、体积 SOP 或 DOP 网络。")
    # Follow only the selected display chain. Do not guess using disconnected
    # nodes or enter locked assets. Bake/postprocess may discard temperature.
    # A cache remains an explicit source: never silently bypass it to re-simulate.
    visited = set()
    for _ in range(64):
        if node.path() in visited:
            raise MessageError("数据源连接形成循环，请选择原始体积输出。")
        visited.add(node.path())
        kind = node.type().nameComponents()[2]
        if kind == "object_merge":
            sources = _dop_merge_sources(node)
            if sources:
                return sources
        if kind in ("null", "pyrobakevolume", "pyropostprocess"):
            inputs = node.inputs()
            if inputs and inputs[0] is not None:
                node = inputs[0]
                continue
        return node.path(), node.path()
    raise MessageError("数据源上游层级过深，请直接选择 Pyro Solver 或体积缓存 SOP。")


def resolve_sources(settings):
    if settings.density_source and settings.temperature_source:
        if hou.node(settings.source) is None:
            raise MessageError("请选择存在的数据源对象。")
        return settings.density_source, settings.temperature_source
    density, temperature = detect_sources(settings.source)
    return settings.density_source or density, settings.temperature_source or temperature


def _set(node, name, value):
    parm = node.parm(name)
    if parm is None:
        raise MessageError("当前 Houdini 版本不支持参数 {node_type}/{name}。", node_type=node.type().name(), name=name)
    parm.set(value)


def _node(parent, typ, name):
    return parent.node(name) or parent.createNode(typ, name)


def _field(parent, name, source, field):
    imp = _node(parent, "object_merge", name + "_import")
    _set(imp, "numobj", 1)
    _set(imp, "objpath1", source)
    _set(imp, "xformtype", 1)
    keep = _node(parent, "blast", name)
    keep.setInput(0, imp)
    _set(keep, "group", "@name=" + field)
    _set(keep, "negate", 1)
    return keep


def build(settings):
    validate(settings, animation=False)
    density_source, temperature_source = resolve_sources(settings)
    root = hou.node(settings.target) if settings.target else None
    if root and root.userData("volumeheatmap_exporter") != "1":
        raise MessageError("目标不是此工具创建的采样分支，请清空目标路径后重新生成。")
    if root is None:
        root = hou.node("/obj").createNode("geo", "VH_PyroExport", run_init_scripts=False)
        root.setUserData("volumeheatmap_exporter", "1")
    settings.target = root.path()
    source_obj = _source_object(hou.node(settings.source))
    if source_obj:
        root.setWorldTransform(source_obj.worldTransform())
    else:
        root.setWorldTransform(hou.hmath.identityTransform())
    for src in (density_source, temperature_source):
        if src.startswith(root.path() + "/"):
            raise MessageError("数据源不能引用工具自己的输出，否则会循环依赖。")
    density = _field(root, "density", density_source, "density")
    temp = _field(root, "temperature", temperature_source, "temperature")
    weight = _node(root, "volumewrangle", "sampling_importance")
    weight.setInput(0, density)
    weight.setInput(1, temp)
    _set(weight, "exportlist", "density")
    _set(weight, "snippet", f'''float d=max(f@density,0.0);
float t=max(volumesample(1,"temperature",@P),0.0);
float w=max(d,{settings.heat_weight!r}*t);
f@density=w>{settings.density_cutoff!r}?pow(w,{settings.density_contrast!r}):0.0;''')
    scatter = _node(root, "scatter", "interior_samples")
    scatter.setInput(0, weight)
    _set(scatter, "forcetotal", 1)
    _set(scatter, "npts", settings.interior_count)
    _set(scatter, "useemergencylimit", 1)
    _set(scatter, "emergencylimit", settings.interior_count)
    _set(scatter, "seed", settings.seed)
    _set(scatter, "randomizeorder", 0)
    _set(scatter, "relaxiterations", 2)
    merged = _node(root, "merge", "all_sample_positions")
    merged.setInput(0, scatter)
    merged.setInput(1, None)
    merged.setInput(2, None)
    remove_boundary_nodes(root)
    if settings.shell:
        # Convert the actual density contour to an SDF, dilate, then sample its surface.
        # Convert Volume accepts classic volumes; convert VDB also handles sparse sources.
        classic = _node(root, "convertvdb", "density_to_classic")
        classic.setInput(0, density)
        _set(classic, "conversion", 0)
        mesh = _node(root, "convertvolume", "smoke_contour")
        mesh.setInput(0, classic)
        _set(mesh, "iso", max(settings.density_cutoff, 0.000001))
        sdf = _node(root, "vdbfrompolygons", "contour_sdf")
        sdf.setInput(0, mesh)
        _set(sdf, "voxelsize", settings.shell_voxel)
        _set(sdf, "exteriorbandvoxels", max(3, math.ceil(settings.shell_expansion / settings.shell_voxel) + 3))
        expand = _node(root, "vdbreshapesdf", "expand_smoke_shell")
        expand.setInput(0, sdf)
        _set(expand, "operation", "dilate")
        _set(expand, "useworldspaceunits", 1)
        _set(expand, "radiusworld", settings.shell_expansion)
        surface = _node(root, "convertvdb", "expanded_surface")
        surface.setInput(0, expand)
        _set(surface, "conversion", 2)
        shell_input = surface
        if settings.shell_dynamic:
            # Signed tetrahedra measure the enclosed mesh, rather than its AABB.
            # Centering avoids precision loss for fields far from the origin.
            budget = _node(root, "attribwrangle", "shell_volume_budget")
            budget.setInput(0, surface)
            _set(budget, "class", 0)
            _set(budget, "snippet", f'''vector origin = getbbox_center(0);
float volume = 0;
for (int prim = 0; prim < nprimitives(0); prim++) {{
    int pts[] = primpoints(0, prim);
    if (len(pts) < 3) continue;
    vector a = point(0, "P", pts[0]) - origin;
    for (int i = 1; i + 1 < len(pts); i++) {{
        vector b = point(0, "P", pts[i]) - origin;
        vector c = point(0, "P", pts[i+1]) - origin;
        volume += dot(a, cross(b, c)) / 6.0;
    }}
}}
f@shell_volume = abs(volume);
float desired = ceil(f@shell_volume * {settings.shell_density!r});
i@shell_sample_count = f@shell_volume > 0 ? int(clamp(desired, 1, {settings.shell_count})) : 0;''')
            shell_input = budget
        shell_pts = _node(root, "scatter", "shell_samples")
        shell_pts.setInput(0, shell_input)
        _set(shell_pts, "forcetotal", 1)
        shell_pts.parm("npts").deleteAllKeyframes()
        if settings.shell_dynamic:
            shell_pts.parm("npts").setExpression('detail("../shell_volume_budget", "shell_sample_count", 0)',
                                                  language=hou.exprLanguage.Hscript)
        else:
            _set(shell_pts, "npts", settings.shell_count)
        _set(shell_pts, "seed", settings.seed + 1)
        _set(shell_pts, "relaxiterations", 2)
        _set(shell_pts, "useemergencylimit", 1)
        _set(shell_pts, "emergencylimit", settings.shell_count)
        merged.setInput(1, shell_pts)
    read = _node(root, "attribfromvolume", "read_raw_temperature")
    read.setInput(0, merged)
    read.setInput(1, temp)
    for key, value in (("field", "temperature"), ("name", "value"), ("type", 0), ("size", 1), ("monoenable", 0)):
        _set(read, key, value)
    color = _node(root, "color", "preview_color")
    color.setInput(0, read)
    for key, value in (("class", 2), ("colortype", 3), ("rampattribute", "value")):
        _set(color, key, value)
    color.parmTuple("ramprange").set((0, 1))
    color.parm("ramp").set(hou.Ramp((hou.rampBasis.Linear,) * 4, (0, 0.3, 0.7, 1),
                                   ((0.02, 0.05, 0.3), (0, 0.6, 1), (1, 0.7, 0.05), (1, 0.02, 0.01))))
    out = _node(root, "null", "OUT_HEATMAP")
    out.setInput(0, color)
    out.setDisplayFlag(True)
    out.setRenderFlag(True)
    comments = {"sampling_importance": "Density-weighted allocation; source fields stay unchanged.",
                "interior_samples": "Interior point budget from VolumeHeatmap Exporter panel.",
                "expand_smoke_shell": "Dilate the density contour in Houdini units, then scatter on its surface.",
                "shell_volume_budget": "Point count = ceil(enclosed shell volume * density), capped by shell budget.",
                "read_raw_temperature": "All sample groups read real temperature; no forced zero values.",
                "OUT_HEATMAP": "Export P/value as field_blend. Positions may change across frames."}
    for name, comment in comments.items():
        n = root.node(name)
        if n:
            n.setComment(comment)
            n.setGenericFlag(hou.nodeFlag.DisplayComment, False)
    root.layoutChildren()
    root.setUserData(SETTINGS_KEY, json.dumps(asdict(settings), ensure_ascii=False))
    return root, out


def remove_boundary_nodes(root):
    """Remove the retired Box branch when no custom nodes depend on it."""
    nodes = tuple(n for n in (root.node("boundary_samples"), root.node("range_boundary")) if n)
    paths = {node.path() for node in nodes}
    for node in nodes:
        refs = tuple(node.outputs()) + tuple(node.dependents(include_children=False))
        if any(ref.path() not in paths for ref in refs):
            return
    if nodes:
        root.deleteItems(nodes)


def inspect(root):
    """Bounded current-frame geometry inspection; called inside Houdini."""
    out = root.node("OUT_HEATMAP")
    density = root.node("density").geometry()
    temp = root.node("temperature").geometry()
    for name, geo in (("density", density), ("temperature", temp)):
        if not geo.prims():
            raise MessageError("数据源没有 {name} 体积。请指定保留该字段的 SOP 或 DOP 网络。", name=name)
    geo = out.geometry()
    errors = [(n.name(), n.errors()) for n in root.children() if n.errors()]
    if errors:
        raise ValueError(str(errors))
    attr = geo.findPointAttrib("value")
    if attr is None or attr.size() != 1:
        raise MessageError("输出缺少标量点属性 value。")
    count = geo.intrinsicValue("pointcount")
    if not 1 <= count <= 4096:
        raise MessageError("当前帧输出 {count} 点；要求 1..4096。请选择存在烟雾或温度的帧。", count=count)
    values = geo.pointFloatAttribValues("value")
    box = geo.boundingBox()
    return {"points": count, "value_min": min(values), "value_max": max(values),
            "bounds_min": list(box.minvec()), "bounds_size": list(box.sizevec())}


def _read_points(node):
    geo = node.geometry()
    attr = geo.findPointAttrib("value")
    if attr is None or attr.size() != 1:
        raise MessageError("输出缺少标量 value。")
    count = geo.intrinsicValue("pointcount")
    if not 1 <= count <= 4096:
        raise MessageError("第 {frame:g} 帧有 {count} 点；要求 1..4096。", frame=hou.frame(), count=count)
    samples = []
    for p in geo.points():
        x, y, z = p.position()
        position = [100 * x, 100 * z, 100 * y]
        value = float(p.attribValue(attr))
        if not all(math.isfinite(v) and abs(v) <= 1e9 for v in position) or not math.isfinite(value) or abs(value) > 1e20:
            raise MessageError("采样数据含无效坐标或数值。")
        samples.append({"index": len(samples), "position": position, "value": value})
    return samples


def export(settings):
    validate(settings)
    source_frames = key_frames(settings)
    root, out = build(settings)
    original_frame = hou.frame()
    frames = []
    lower = [math.inf] * 3
    upper = [-math.inf] * 3
    previous = -1.0
    try:
        with hou.InterruptableOperation(tr("导出 VolumeHeatmap"), open_interrupt_dialog=True) as operation:
            for i, frame in enumerate(source_frames):
                operation.updateProgress(i / len(source_frames))
                hou.setFrame(frame)
                inspect(root)
                points = _read_points(out)
                seconds = settings.duration * (frame - settings.start) / (settings.end - settings.start)
                f32 = struct.unpack("f", struct.pack("f", seconds))[0]
                if f32 <= previous:
                    raise MessageError("关键帧时间在 UE float 精度下重叠，请增大总时间。")
                previous = f32
                for point in points:
                    for axis, value in enumerate(point["position"]):
                        lower[axis] = min(lower[axis], value)
                        upper[axis] = max(upper[axis], value)
                frames.append({"time": seconds, "points": points})
            operation.updateProgress(1.0)
    finally:
        hou.setFrame(original_frame)
    data = {"format": "VolumeHeatmap.Animation", "version": 1,
            "coordinateSpace": "local", "positionUnit": "cm", "timeUnit": "seconds",
            "duration": settings.duration, "transition": "field_blend", "frames": frames}
    payload = json.dumps(data, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    if len(payload) > 64 * 1024 * 1024 or len(payload.encode("utf-8")) > 128 * 1024 * 1024:
        raise MessageError("文件超出插件导入大小限制。")
    base = Path(hou.expandString(settings.output_dir)).expanduser()
    base.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    destination = base / stamp
    temporary = base / (".partial-" + uuid.uuid4().hex)
    temporary.mkdir()
    try:
        (temporary / "ThermalField.vhanim").write_text(payload, encoding="utf-8")
        with (temporary / "FirstFrame.csv").open("w", encoding="utf-8", newline="") as stream:
            stream.write("# VolumeHeatmap.SampleFrame v1\n# coordinateSpace=local;positionUnit=cm\n")
            writer = csv.writer(stream, lineterminator="\n")
            writer.writerow(["index", "x", "y", "z", "value"])
            for p in frames[0]["points"]:
                writer.writerow([p["index"], *p["position"], p["value"]])
        info = {"settings": asdict(settings), "source_frames": source_frames,
                "key_count": len(frames), "points_per_key": [len(f["points"]) for f in frames],
                "ue_bounds_min": lower, "ue_bounds_size": [b - a for a, b in zip(lower, upper)],
                "value_min": min(p["value"] for f in frames for p in f["points"]),
                "value_max": max(p["value"] for f in frames for p in f["points"]),
                "axis_mapping": "UE cm = 100 * Houdini (X,Z,Y); source object transform excluded when selecting a geometry object/SOP"}
        (temporary / "ExportInfo.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.rename(destination)
    except Exception:
        shutil.rmtree(temporary)
        raise
    return destination


def export_static(settings):
    """Export one explicitly chosen frame as a plugin-compatible UTF-8 CSV."""
    validate(settings, animation=False)
    original_frame = hou.frame()
    try:
        with hou.InterruptableOperation(tr("导出 VolumeHeatmap 静帧"), open_interrupt_dialog=True) as operation:
            operation.updateProgress(0)
            hou.setFrame(settings.static_frame)
            root, out = build(settings)
            info = inspect(root)
            points = _read_points(out)
            operation.updateProgress(1)
    finally:
        hou.setFrame(original_frame)
    base = Path(hou.expandString(settings.output_dir)).expanduser()
    base.mkdir(parents=True, exist_ok=True)
    destination = base / (datetime.now().strftime("%Y%m%d-%H%M%S-%f") + "-frame")
    temporary = base / (".partial-" + uuid.uuid4().hex)
    temporary.mkdir()
    try:
        with (temporary / "Frame.csv").open("w", encoding="utf-8", newline="") as stream:
            stream.write("# VolumeHeatmap.SampleFrame v1\n# coordinateSpace=local;positionUnit=cm\n")
            writer = csv.writer(stream, lineterminator="\n")
            writer.writerow(["index", "x", "y", "z", "value"])
            for p in points:
                writer.writerow([p["index"], *p["position"], p["value"]])
        positions = [p["position"] for p in points]
        lower = [min(p[i] for p in positions) for i in range(3)]
        upper = [max(p[i] for p in positions) for i in range(3)]
        info.update({"settings": asdict(settings), "source_frame": settings.static_frame,
                     "ue_bounds_min": lower, "ue_bounds_size": [b-a for a,b in zip(lower,upper)],
                     "axis_mapping": "UE cm = 100 * Houdini (X,Z,Y)"})
        (temporary / "ExportInfo.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.rename(destination)
    except Exception:
        shutil.rmtree(temporary)
        raise
    return destination
