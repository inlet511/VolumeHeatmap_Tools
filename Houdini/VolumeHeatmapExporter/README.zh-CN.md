# VolumeHeatmap Exporter for Houdini

[English](README.md) | **简体中文** | [全部工具](../../README.zh-CN.md)

**版本 1.2.0**

将 Houdini Pyro 场转换为 Unreal Engine 的 Volume Heatmap 插件可使用的采样数据。工具在独立 Geometry 对象中创建可编辑的 SOP 网络，读取原始温度场，并导出静帧 CSV 或 `.vhanim` 动画。

## 功能

- 选择普通 Pyro Geometry 对象、DOP 网络、Pyro Solver SOP 或体积缓存。
- 根据密度与温度权重，自适应分配内部采样点预算。
- 沿烟雾轮廓生成包壳，并向外扩张。
- 使用固定包壳点数，或根据包壳包围的体积逐帧调整点数。
- 独立设置源帧范围、关键帧间隔与动画总时长。
- 无需配置动画范围即可导出静帧。
- 即时切换中英文，保留当前参数。
- 将生成的 SOP 节点和采样设置保存在 HIP 文件中。

## 环境要求

| 项目 | 说明 |
| --- | --- |
| Houdini | 目标环境为 Houdini 20.5 / Python 3.11，其他版本尚未验证。 |
| 操作系统 | 附带安装脚本适用于 Windows，下文也提供手动注册 Houdini Package 的方法。 |
| 源数据 | 模拟或缓存中需要包含名为 `density` 和 `temperature` 的体积场。 |
| Unreal Engine | 使用导出文件需要安装 Volume Heatmap 插件。 |
| Python 依赖 | 仅使用 Houdini 自带的 Python、Qt 绑定和标准库，无需 pip 安装或 MCP 服务。 |

## 安装

### Windows

1. 下载或克隆本仓库。
2. 将工具文件夹保留在固定位置。安装脚本会向 Houdini 注册该目录，不会把工具复制到偏好设置目录。
3. 在 `Houdini/VolumeHeatmapExporter` 目录打开 PowerShell，执行：

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\install.ps1
   ```

   默认会在 Windows“文档”中的 Houdini 20.5 偏好设置目录下，向 `packages` 文件夹写入 `volumeheatmap_exporter.json`。如果已存在同名配置，脚本会先备份再替换。

   如果使用自定义 Houdini 偏好设置目录：

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\install.ps1 -HoudiniPreferences 'D:\HoudiniPrefs\houdini20.5'
   ```

4. 重启 Houdini。
5. 在工具架菜单启用 **VolumeHeatmap**，点击 **Pyro Exporter**。

面板顶部的 **语言 / Language** 可切换 **中文** 与 **English**。初始默认为中文，语言选择会保存在本机。

### 手动注册 Package

在 Houdini 用户偏好设置的 `packages` 目录中创建 `volumeheatmap_exporter.json`：

```json
{
  "enable": true,
  "hpath": "D:/HoudiniTools/VolumeHeatmap_Tools/Houdini/VolumeHeatmapExporter"
}
```

将 `hpath` 替换为工具文件夹的绝对路径，使用正斜杠，然后重启 Houdini。其他操作系统也可使用相同的 Package 结构注册，但尚未验证这些环境。

### 其他打开方式

创建 Python Panel 面板，选择 **VolumeHeatmap Exporter**；或在 Houdini 的 **Windows → Python Shell** 中执行：

```python
import volumeheatmap_exporter
volumeheatmap_exporter.show()
```

## 快速开始

1. 正常创建 Pyro 模拟。导出较长动画前，建议先缓存，并保留 `density` 和 `temperature`。
2. 选择 Pyro Geometry 对象、DOP 网络、Solver SOP 或体积缓存。
3. 点击工具面板中的 **使用当前选中节点**。手动修改源路径后，可点击 **识别字段** 重新识别。
4. 设置 **内部点数预算**，例如 `800`。
5. 按需打开 **启用包壳**，设置包壳点数与扩张距离。
6. 点击 **生成 / 更新采样分支**。输出通常位于 `/obj/VH_PyroExport/OUT_HEATMAP`；存在同名对象时，Houdini 会为新分支分配唯一名称。
7. 设置 **导出目录**，按照下文导出静帧或动画。
8. 保存 HIP 文件，以保留生成的分支和设置。

原始 Pyro 对象内部无需预先创建专用辅助节点。字段导入、采样和包壳节点均由工具在独立分支中创建。更新分支时，面板设置会重新应用到生成的节点。

## 选择 Pyro 字段

| 所选数据源 | 识别方式 |
| --- | --- |
| Geometry 对象 | 沿对象的显示输出查找。 |
| Pyro Bake Volume / Pyro Post-Process | 沿第一个输入追溯原始体积数据。 |
| DOP 网络 | 从模拟中读取 `density` 和 `temperature`。 |
| 读取 DOP 密度或温度场的原生 Object Merge | 推导对应的 DOP 字段地址。 |
| Pyro Solver SOP 或体积缓存 | 直接将所选 SOP 作为字段来源。 |

自动识别不会遍历所有未连接节点，也不会修改模拟。对于自定义网络，可能需要选择更直接的数据源，或手动覆盖 **Density 来源** 与 **Temperature 来源**。工具不会自动绕过选中的缓存去运行上游模拟。如果缓存没有 `temperature`，需要将该字段写入缓存，或选择保留该字段的其他输出。

### DOP 字段地址

例如：

```text
/obj/pyro_simulation:*/temperature
```

- `/obj/pyro_simulation`：DOP 网络路径。
- `:`：分隔节点路径和 DOP 内部数据地址。
- `*`：匹配网络中的模拟对象。
- `/temperature`：需要导入的温度场。

这是 Object Merge 使用的字段地址，不是可以在节点浏览器中直接选择的 SOP 节点路径。在 **Pyro 对象 / 体积 SOP** 中选择 DOP 网络，再点击 **识别字段** 即可自动填写。如果一个网络包含多个模拟，请手动指定目标对象的字段地址，避免合并无关对象。

## 内部采样

| 控件 | 作用 |
| --- | --- |
| 内部点数预算 | 自适应内部点数的上限，建议从 400–800 点开始。 |
| 浓度阈值 | 排除低采样权重区域，同时作为生成烟雾包壳的密度轮廓阈值。 |
| 浓度对比 | 小于 1 时提高薄烟的相对采样权重，大于 1 时偏向高浓度区域。 |
| 温度区域权重 | 为烟少但温度高的区域增加采样权重，设为 0 时仅按密度分配。 |
| 随机种子 | 控制采样的随机种子。 |

采样权重为 `max(density, 温度区域权重 × temperature)`，再经过阈值过滤和浓度对比指数处理。这仅改变点的分配，导出的 `value` 仍是原始 `temperature` 的采样值。

## 包壳采样

打开 **启用包壳** 后，工具提取烟雾的密度轮廓，将其转换为 SDF，向外扩张后在表面布点。

| 控件 | 作用 |
| --- | --- |
| 包壳表面点数 | 未启用动态调整时使用的固定点数。 |
| 按体积调整点数 | 根据每个源帧重新计算包壳点数。 |
| 包壳点数上限 | 动态模式允许的最大包壳点数。 |
| 每立方单位点数 | 每立方 Houdini 单位的包壳体积对应的采样点数。 |
| 扩张距离 | 以 Houdini 单位表示的向外偏移距离，可从 `0.3` 开始。 |
| 包壳体素大小 | SDF 分辨率，越小越精细，也越耗时和占用内存，可从 `0.2` 开始。 |

动态模式的计算方式：

```text
请求点数 = ceil(扩张后的包壳体积 × 每立方单位点数)
```

最终点数受 **包壳点数上限** 限制。具有正体积的非空包壳至少分配一个点；空表面不生成包壳点。体积从扩张后的表面计算，而非使用包围盒体积。例如密度为 `2` 时，体积 `20` 请求 `40` 点，体积 `80` 请求 `160` 点，达到上限后不再增加。

两种模式都只在包壳表面布点。所有点均读取原始温度，包壳点不会强制赋零。工具不再提供独立的 Box 外围点功能。

## 导出动画

1. 设置 **起始帧**、**结束帧** 和 **关键帧间隔**，间隔单位为 Houdini 帧。
2. 设置 **总时长 / 秒**。点击 **按 Houdini FPS 计算总时间** 可根据源帧范围和 Houdini FPS 计算自然播放时长。
3. 设置 **导出目录**，点击 **导出 UE 动画**。

工具始终包含结束帧，即使间隔无法整除帧范围。例如 `1–121` 帧、间隔 `3`，会生成 `41` 个关键帧。总时长为 `5` 秒时，这些关键帧相隔 `0.125` 秒。修改总时长只重映射播放时间，不改变采样的源帧。

每次导出会创建新的时间戳文件夹：

```text
<导出目录>/<时间戳>/
├── ThermalField.vhanim
├── FirstFrame.csv
└── ExportInfo.json
```

动画采用 `VolumeHeatmap.Animation` 第 1 版格式，使用 `field_blend` 过渡，允许关键帧之间的点位置与数量变化。`FirstFrame.csv` 是首个动画关键帧的静帧数据。`ExportInfo.json` 记录设置、源帧、点数、数值范围和 UE 边界。

## 导出静帧

1. 设置 **静帧导出帧号**，或点击 **静帧帧号设为当前时间轴**。
2. 设置 **导出目录**。
3. 点击 **导出静帧 CSV**。

静帧导出不要求配置有效的动画范围。输出为时间戳文件夹中的 `Frame.csv` 和 `ExportInfo.json`。

默认导出目录为 `$HIP/VolumeHeatmapExport`，请先保存 HIP 文件，或明确指定输出目录。采样完成或取消后，工具会恢复原时间轴帧位置。文件写入完成后，临时目录才会重命名为最终的时间戳目录。

## 坐标、数值与 Unreal Engine

CSV 文件先包含元数据注释，再包含以下列：

```csv
index,x,y,z,value
```

坐标转换规则为：

```text
UE X = Houdini X × 100
UE Y = Houdini Z × 100
UE Z = Houdini Y × 100
```

位置单位为厘米。选择 Geometry 对象或其 SOP 时，导出对象局部空间坐标，不包含对象变换；直接选择 DOP 网络时，使用导入的模拟字段坐标。如果源对象具有非单位变换，请检查对齐情况。

`value` 保存原始 Pyro `temperature`，不会自动转换为摄氏度。

通过 Volume Heatmap 插件的动画或采样帧导入流程加载 `.vhanim` 或 CSV。使用 Volume Heatmap 组件上的 **Fit Bounds to Data** 匹配数据边界，并检查变换，使热力场与源模型对齐。本工具导出场数据，不导出热源网格模型。

## 限制与常见问题

- **点数限制：** 内部点数预算 + 包壳点数上限不能超过 **4096**；固定模式使用包壳表面点数计算，实际点数可能更少。
- **关键帧限制：** 动画最多 **256** 个关键帧，较长序列可增大关键帧间隔。
- **空帧：** 完全没有采样点的帧无法导出，请选择包含有效数据的帧范围。
- **缺少 temperature：** 在 Solver 或缓存中保留原始温度场，用于渲染的 Bake 可能丢弃该字段。
- **没有包壳：** 确认当前帧存在烟雾，尝试降低浓度阈值或减小包壳体素大小。
- **动态点数看起来不变：** 可能已达到包壳点数上限。降低每立方单位点数，或在总点数预算允许的范围内提高上限。
- **导出慢：** 先缓存模拟，减少关键帧数量，或增大包壳体素大小。导出未缓存帧可能触发 Houdini 模拟。
- **找不到工具：** 检查 Package 路径，重启 Houdini 并启用 VolumeHeatmap 工具架，无需 MCP 连接。
- **旧 HIP 文件：** 已移除的 Box 外围点设置会被忽略。更新工具分支时会断开旧外围点节点；没有自定义节点引用时会将其删除。

## 更新与卸载

更新时，替换工具文件或拉取仓库最新内容。如果工具路径改变，请重新运行安装脚本。重启 Houdini，或在 Houdini Python Shell 中重新载入浮动面板：

```python
import importlib
import volumeheatmap_exporter
importlib.reload(volumeheatmap_exporter).reload_panel()
```

重新载入会保留浮动面板当前的采样参数。如果使用嵌入式 Python Panel，请关闭后重新创建该面板实例。

卸载时，删除 Houdini 偏好设置 `packages` 目录中的 `volumeheatmap_exporter.json`，然后重启 Houdini。已经保存在 HIP 文件中的采样节点仍会保留在场景内。
