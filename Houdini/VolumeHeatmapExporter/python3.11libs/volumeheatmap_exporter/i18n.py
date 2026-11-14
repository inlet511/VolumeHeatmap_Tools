"""Chinese source strings and English UI translations."""

_language = "zh"

EN = {
    "VolumeHeatmap · Pyro 采样与导出": "VolumeHeatmap · Pyro Sampling & Export",
    "1 · Pyro 数据源": "1 · Pyro Source",
    "Pyro 对象 / 体积 SOP": "Pyro Object / Volume SOP",
    "使用当前选中节点": "Use Selected Node",
    "识别字段": "Detect Fields",
    "Density 来源": "Density Source",
    "Temperature 来源": "Temperature Source",
    "2 · 帧范围与播放时间": "2 · Frames & Timing",
    "起始帧": "Start Frame",
    "结束帧": "End Frame",
    "关键帧间隔": "Keyframe Step",
    "总时长 / 秒": "Duration / Seconds",
    "按 Houdini FPS 计算总时间": "Use Houdini FPS",
    "3 · 内部自适应采样": "3 · Adaptive Interior Sampling",
    "内部点数预算": "Interior Point Budget",
    "浓度阈值": "Density Threshold",
    "浓度对比": "Density Contrast",
    "温度区域权重": "Temperature Weight",
    "随机种子": "Random Seed",
    "4 · 包壳采样": "4 · Shell Sampling",
    "启用包壳": "Enable Shell",
    "按体积调整点数": "Adjust Count by Volume",
    "包壳表面点数": "Shell Point Count",
    "包壳点数上限": "Shell Point Limit",
    "每立方单位点数": "Points per Cubic Unit",
    "扩张距离": "Expansion Distance",
    "包壳体素大小": "Shell Voxel Size",
    "5 · 输出": "5 · Output",
    "静帧导出帧号": "Static Frame",
    "静帧帧号设为当前时间轴": "Use Current Frame",
    "导出目录": "Export Folder",
    "采样分支": "Sampling Branch",
    "从采样分支载入设置": "Load Branch Settings",
    "生成 / 更新采样分支": "Create / Update Branch",
    "导出 UE 动画": "Export UE Animation",
    "导出静帧 CSV": "Export Static CSV",
    "选择": "Browse",
    "选择节点": "Select Node",
    "点数上限：{count} / 4096": "Point Limit: {count} / 4096",
    "{count} 个关键帧 · {duration:g} 秒": "{count} Keyframes · {duration:g} Seconds",
    "操作未完成：{error}": "Operation Failed: {error}",
    "请先在网络编辑器中选中 Pyro 对象或体积 SOP。": "Select a Pyro object or volume SOP in the network editor.",
    "已识别字段": "Fields Detected",
    "请选择由此面板生成的采样 Geometry。": "Select a sampling Geometry created by this panel.",
    "已载入此分支保存的设置。": "Branch Settings Loaded",
    "{count} 点 · value {minimum:.5g} .. {maximum:.5g}": "{count} Points · Value {minimum:.5g} .. {maximum:.5g}",
    "导出完成：{path}": "Export Complete: {path}",
    "静帧导出完成：{path}": "Static Export Complete: {path}",
    "已取消导出，原帧位置已恢复。": "Export Cancelled. Original Frame Restored.",
    "已取消静帧导出，原帧位置已恢复。": "Static Export Cancelled. Original Frame Restored.",
    "结束帧须大于起始帧，关键帧间隔至少为 1 帧。": "End frame must exceed start frame; keyframe step must be at least 1.",
    "共 {count} 个关键帧，超过 256；请增大关键帧间隔。": "{count} keyframes exceed the limit of 256. Increase the keyframe step.",
    "总时间须大于 0 且不超过 86400 秒。": "Duration must be greater than 0 and no more than 86400 seconds.",
    "内部点数须为 1..4096。": "Interior point count must be 1..4096.",
    "请检查包壳点数、扩张距离和体素大小。": "Check the shell point count, expansion distance and voxel size.",
    "包壳密度须大于 0。": "Shell sampling density must be greater than 0.",
    "合计最多 {count} 点，超过插件 4096 点限制；请减少采样点。": "The point budget of {count} exceeds 4096. Reduce the point counts.",
    "各项参数须为有限数值。": "All parameter values must be finite.",
    "密度阈值和温度权重不能为负，浓度对比须大于 0。": "Density threshold and temperature weight must be nonnegative; density contrast must be positive.",
    "此 Object Merge 引用了多个 Pyro 模拟，请指定单一模拟的 DOP 网络或字段来源。": "This Object Merge references multiple Pyro simulations. Select one DOP network or specify the field sources.",
    "请选择存在的 Pyro 对象、DOP 网络或含体积字段的 SOP。": "Select an existing Pyro object, DOP network or volume SOP.",
    "所选几何对象没有显示输出，请选择 Pyro Solver 或体积缓存 SOP。": "The selected object has no display output. Select a Pyro Solver or volume cache SOP.",
    "此节点不是几何对象、体积 SOP 或 DOP 网络。": "The node is not a geometry object, volume SOP or DOP network.",
    "数据源连接形成循环，请选择原始体积输出。": "The source contains a dependency cycle. Select the original volume output.",
    "数据源上游层级过深，请直接选择 Pyro Solver 或体积缓存 SOP。": "The source chain is too deep. Select the Pyro Solver or volume cache SOP directly.",
    "请选择存在的数据源对象。": "Select an existing source object.",
    "当前 Houdini 版本不支持参数 {node_type}/{name}。": "This Houdini version does not support parameter {node_type}/{name}.",
    "目标不是此工具创建的采样分支，请清空目标路径后重新生成。": "The target was not created by this tool. Clear the target path and create a new branch.",
    "数据源不能引用工具自己的输出，否则会循环依赖。": "The source cannot reference this tool's output because that creates a dependency cycle.",
    "数据源没有 {name} 体积。请指定保留该字段的 SOP 或 DOP 网络。": "The source has no {name} volume. Select a SOP or DOP network that retains this field.",
    "输出缺少标量点属性 value。": "The output is missing the scalar point attribute 'value'.",
    "当前帧输出 {count} 点；要求 1..4096。请选择存在烟雾或温度的帧。": "The current frame has {count} points; 1..4096 are required. Select a frame with smoke or temperature.",
    "输出缺少标量 value。": "The output is missing the scalar attribute 'value'.",
    "第 {frame:g} 帧有 {count} 点；要求 1..4096。": "Frame {frame:g} has {count} points; 1..4096 are required.",
    "采样数据含无效坐标或数值。": "The samples contain invalid coordinates or values.",
    "导出 VolumeHeatmap": "Exporting VolumeHeatmap",
    "导出 VolumeHeatmap 静帧": "Exporting VolumeHeatmap Static Frame",
    "关键帧时间在 UE float 精度下重叠，请增大总时间。": "Keyframe times overlap at UE float precision. Increase the duration.",
    "文件超出插件导入大小限制。": "The file exceeds the plugin's import size limit.",
}


def set_language(language):
    global _language
    _language = language if language in ("zh", "en") else "zh"


def tr(text, **values):
    translated = EN.get(text, text) if _language == "en" else text
    return translated.format(**values) if values else translated


class MessageError(ValueError):
    """Keep validation messages translatable after the language changes."""
    def __init__(self, text, **values):
        self.text = text
        self.values = values
        super().__init__(text)

    def __str__(self):
        return tr(self.text, **self.values)
