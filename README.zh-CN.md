# Volume Heatmap Tools

[English](README.md) | **简体中文**

为 Unreal Engine 的 Volume Heatmap 插件提供数据制作、采样与导出的配套工具集。

每个工具都有独立目录、安装说明和使用指南。本仓库包含配套工具，不包含 Unreal Engine 插件本体。

## 工具列表

| 工具 | 宿主软件 | 功能 |
| --- | --- | --- |
| [VolumeHeatmap Exporter](Houdini/VolumeHeatmapExporter/README.zh-CN.md) | Houdini 20.5 / Python 3.11 | 对 Pyro 密度与温度场进行采样，可生成烟雾包壳，导出静帧 CSV 或 `.vhanim` 动画。 |

## 开始使用

通过 **Code → Download ZIP** 下载本仓库，或使用 Git 克隆：

```sh
git clone https://github.com/inlet511/VolumeHeatmap_Tools.git
```

然后按照对应工具目录中的 README 安装使用。也可以保留文件结构，单独分发某个工具文件夹。

## 仓库结构

```text
VolumeHeatmap_Tools/
└── Houdini/
    └── VolumeHeatmapExporter/
        ├── README.md
        ├── README.zh-CN.md
        ├── install.ps1
        ├── python3.11libs/
        ├── python_panels/
        └── toolbar/
```

后续工具可放在对应宿主软件的目录下，并添加到上方工具列表中。

## 问题反馈

请通过 [GitHub Issues](https://github.com/inlet511/VolumeHeatmap_Tools/issues) 反馈问题，并提供工具版本、宿主软件版本、复现步骤和报错信息。
