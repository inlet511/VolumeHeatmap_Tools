"""Bilingual Qt panel. All Qt work stays on Houdini's main thread."""
import json
from dataclasses import asdict

import hou
from hutil.Qt import QtCore, QtWidgets

from . import core, i18n

_window = None


class ExportPanel(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.preferences = QtCore.QSettings("VolumeHeatmap", "HoudiniExporter")
        i18n.set_language(self.preferences.value("language", "zh"))
        self._texts = []
        self._status_text = ""
        self._status_values = {}
        self.bind_text(self.setWindowTitle, "VolumeHeatmap · Pyro 采样与导出")
        self.settings = core.Settings(static_frame=int(hou.frame()))
        self.controls = {}
        outer = QtWidgets.QVBoxLayout(self)
        language_row = QtWidgets.QHBoxLayout()
        language_row.addStretch()
        language_row.addWidget(QtWidgets.QLabel("语言 / Language"))
        self.language = QtWidgets.QComboBox()
        self.language.addItem("中文", "zh")
        self.language.addItem("English", "en")
        self.language.setCurrentIndex(1 if self.preferences.value("language", "zh") == "en" else 0)
        language_row.addWidget(self.language)
        outer.addLayout(language_row)
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        body = QtWidgets.QWidget()
        self.body = QtWidgets.QVBoxLayout(body)
        scroll.setWidget(body)
        outer.addWidget(scroll)
        form = self.group("1 · Pyro 数据源")
        self.path(form, "source", "Pyro 对象 / 体积 SOP", browse="node")
        row = QtWidgets.QHBoxLayout()
        for text, callback in (("使用当前选中节点", self.use_selected), ("识别字段", self.detect)):
            button = self.button(text)
            button.clicked.connect(callback)
            row.addWidget(button)
        form.addRow(row)
        self.path(form, "density_source", "Density 来源", browse="node")
        self.path(form, "temperature_source", "Temperature 来源", browse="node")
        form = self.group("2 · 帧范围与播放时间")
        self.number(form, "start", "起始帧", -100000, 100000)
        self.number(form, "end", "结束帧", -100000, 100000)
        self.number(form, "step", "关键帧间隔", 1, 10000)
        self.number(form, "duration", "总时长 / 秒", 0.001, 86400, decimals=3)
        natural = self.button("按 Houdini FPS 计算总时间")
        natural.clicked.connect(self.natural_duration)
        form.addRow(natural)
        self.timing = QtWidgets.QLabel()
        self.timing.setWordWrap(True)
        form.addRow(self.timing)
        form = self.group("3 · 内部自适应采样")
        self.number(form, "interior_count", "内部点数预算", 1, 4096)
        self.number(form, "density_cutoff", "浓度阈值", 0, 100, decimals=5)
        self.number(form, "density_contrast", "浓度对比", 0.05, 4, decimals=2)
        self.number(form, "heat_weight", "温度区域权重", 0, 10, decimals=2)
        self.number(form, "seed", "随机种子", 0, 100000)
        form = self.group("4 · 包壳采样")
        self.check(form, "shell", "启用包壳")
        self.check(form, "shell_dynamic", "按体积调整点数")
        self.number(form, "shell_count", "包壳表面点数", 1, 4096)
        self.shell_count_label = form.labelForField(self.controls["shell_count"])
        self.number(form, "shell_density", "每立方单位点数", 0.00001, 100000, decimals=5)
        self.number(form, "shell_expansion", "扩张距离", 0, 1000, decimals=3)
        self.number(form, "shell_voxel", "包壳体素大小", 0.01, 100, decimals=3)
        self.budget = QtWidgets.QLabel()
        self.budget.setWordWrap(True)
        self.body.addWidget(self.budget)
        form = self.group("5 · 输出")
        self.number(form, "static_frame", "静帧导出帧号", -100000, 100000)
        current = self.button("静帧帧号设为当前时间轴")
        current.clicked.connect(lambda: self.controls["static_frame"].setValue(int(hou.frame())))
        form.addRow(current)
        self.path(form, "output_dir", "导出目录", browse="directory")
        self.path(form, "target", "采样分支", browse="node")
        reload_button = self.button("从采样分支载入设置")
        reload_button.clicked.connect(self.load_target)
        form.addRow(reload_button)
        self.body.addStretch()
        buttons = QtWidgets.QHBoxLayout()
        self.preview_button = self.button("生成 / 更新采样分支")
        self.preview_button.clicked.connect(self.preview)
        self.export_button = self.button("导出 UE 动画")
        self.export_button.clicked.connect(self.export)
        buttons.addWidget(self.preview_button)
        self.static_button = self.button("导出静帧 CSV")
        self.static_button.clicked.connect(self.export_static)
        buttons.addWidget(self.static_button)
        buttons.addWidget(self.export_button)
        outer.addLayout(buttons)
        self.status = QtWidgets.QLabel("")
        self.status.setWordWrap(True)
        self.status.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        outer.addWidget(self.status)
        self.populate(self.settings)
        for widget in self.controls.values():
            for item in widget if isinstance(widget, list) else [widget]:
                if isinstance(item, QtWidgets.QAbstractSpinBox):
                    item.valueChanged.connect(self.refresh_summary)
                elif isinstance(item, QtWidgets.QCheckBox):
                    item.toggled.connect(self.refresh_summary)
        self.refresh_summary()
        # Restore the most recently created branch in this HIP.
        managed = [n for n in hou.node("/obj").children() if n.userData(core.SETTINGS_KEY)]
        if managed:
            try:
                self.populate(core.load_settings(json.loads(managed[-1].userData(core.SETTINGS_KEY))))
            except (ValueError, TypeError):
                pass
        self.language.currentIndexChanged.connect(self.change_language)

    def bind_text(self, setter, text):
        self._texts.append((setter, text))
        setter(i18n.tr(text))

    def label(self, text):
        label = QtWidgets.QLabel()
        self.bind_text(label.setText, text)
        return label

    def button(self, text):
        button = QtWidgets.QPushButton()
        self.bind_text(button.setText, text)
        return button

    def change_language(self, *_):
        language = self.language.currentData()
        i18n.set_language(language)
        self.preferences.setValue("language", language)
        self.preferences.sync()
        for setter, text in self._texts:
            setter(i18n.tr(text))
        self.refresh_summary()
        self.set_status(self._status_text, **self._status_values)

    def set_status(self, text, **values):
        self._status_text = text
        self._status_values = values
        self.status.setText(i18n.tr(text, **values))

    def group(self, title):
        box = QtWidgets.QGroupBox()
        self.bind_text(box.setTitle, title)
        form = QtWidgets.QFormLayout(box)
        form.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)
        self.body.addWidget(box)
        return form

    def number(self, form, key, label, low, high, decimals=None):
        widget = QtWidgets.QSpinBox() if decimals is None else QtWidgets.QDoubleSpinBox()
        if decimals is not None:
            widget.setDecimals(decimals)
            widget.setSingleStep(0.1 if decimals <= 3 else 0.001)
        widget.setRange(low, high)
        self.controls[key] = widget
        form.addRow(self.label(label), widget)

    def check(self, form, key, label):
        widget = QtWidgets.QCheckBox()
        self.bind_text(widget.setText, label)
        self.controls[key] = widget
        form.addRow(widget)

    def path(self, form, key, label, browse):
        row = QtWidgets.QHBoxLayout()
        widget = QtWidgets.QLineEdit()
        self.controls[key] = widget
        row.addWidget(widget)
        button = self.button("选择")
        button.clicked.connect(lambda: self.choose(key, browse))
        row.addWidget(button)
        form.addRow(self.label(label), row)

    def choose(self, key, kind):
        if kind == "node":
            # HOM expects a node object here, not the path string returned by the chooser.
            current_path = self.controls[key].text().strip()
            initial_node = hou.node(current_path) if current_path else None
            path = hou.ui.selectNode(initial_node=initial_node or hou.node("/obj"), title=i18n.tr("选择节点"))
        else:
            path = hou.ui.selectFile(start_directory=hou.expandString(self.controls[key].text()),
                                     file_type=hou.fileType.Directory, title=i18n.tr("导出目录"))
        if path:
            self.controls[key].setText(path)
            if key == "source":
                self.detect()

    def collect(self):
        data = {}
        for key, widget in self.controls.items():
            if isinstance(widget, list):
                data[key] = tuple(w.value() for w in widget)
            elif isinstance(widget, QtWidgets.QCheckBox):
                data[key] = widget.isChecked()
            elif isinstance(widget, QtWidgets.QLineEdit):
                data[key] = widget.text().strip()
            else:
                data[key] = widget.value()
        return core.Settings(**data)

    def populate(self, settings):
        settings = core.load_settings(asdict(settings))
        self.settings = settings
        # Summaries must see a complete set of values when restoring a panel.
        blocked = []
        for widget in self.controls.values():
            for item in widget if isinstance(widget, list) else [widget]:
                blocked.append((item, item.blockSignals(True)))
        for key, value in asdict(settings).items():
            widget = self.controls[key]
            if isinstance(widget, list):
                for w, v in zip(widget, value):
                    w.setValue(v)
            elif isinstance(widget, QtWidgets.QCheckBox):
                widget.setChecked(value)
            elif isinstance(widget, QtWidgets.QLineEdit):
                widget.setText(value)
            else:
                widget.setValue(value)
        for widget, was_blocked in blocked:
            widget.blockSignals(was_blocked)
        self.refresh_summary()

    def refresh_summary(self, *_):
        s = self.collect()
        count = core.point_budget(s)
        self.budget.setText(i18n.tr("点数上限：{count} / 4096", count=count))
        self.budget.setStyleSheet("color: #ef7777;" if count > 4096 else "")
        self.shell_count_label.setText(i18n.tr("包壳点数上限" if s.shell_dynamic else "包壳表面点数"))
        for key in ("shell_count", "shell_dynamic", "shell_expansion", "shell_voxel"):
            self.controls[key].setEnabled(s.shell)
        self.controls["shell_density"].setEnabled(s.shell and s.shell_dynamic)
        try:
            n = len(core.key_frames(s))
            self.timing.setText(i18n.tr("{count} 个关键帧 · {duration:g} 秒", count=n, duration=s.duration))
        except ValueError as e:
            self.timing.setText(str(e))

    def report_error(self, exc):
        self.set_status("操作未完成：{error}", error=exc)
        hou.ui.displayMessage(str(exc), severity=hou.severityType.Error, title="VolumeHeatmap")

    def use_selected(self):
        selected = hou.selectedNodes()
        if not selected:
            self.set_status("请先在网络编辑器中选中 Pyro 对象或体积 SOP。")
            return
        self.controls["source"].setText(selected[-1].path())
        self.detect()

    def detect(self):
        try:
            density, temperature = core.detect_sources(self.controls["source"].text())
            self.controls["density_source"].setText(density)
            self.controls["temperature_source"].setText(temperature)
            # Selecting a different source starts a new graph instead of modifying the old one.
            self.controls["target"].clear()
            self.set_status("已识别字段")
        except Exception as e:
            self.report_error(e)

    def natural_duration(self):
        s = self.collect()
        self.controls["duration"].setValue(max(0.001, (s.end - s.start) / hou.fps()))

    def load_target(self):
        try:
            node = hou.node(self.controls["target"].text())
            data = node.userData(core.SETTINGS_KEY) if node else None
            if not data:
                raise i18n.MessageError("请选择由此面板生成的采样 Geometry。")
            settings = core.load_settings(json.loads(data))
            settings.target = node.path()
            self.populate(settings)
            self.set_status("已载入此分支保存的设置。")
        except Exception as e:
            self.report_error(e)

    def preview(self):
        try:
            s = self.collect()
            with hou.undos.group("VolumeHeatmap sampling setup"):
                root, _ = core.build(s)
            self.controls["target"].setText(root.path())
            info = core.inspect(root)
            self.set_status("{count} 点 · value {minimum:.5g} .. {maximum:.5g}",
                            count=info['points'], minimum=info['value_min'], maximum=info['value_max'])
        except Exception as e:
            self.report_error(e)

    def export(self):
        s = self.collect()
        try:
            core.validate(s)
            self.preview_button.setEnabled(False)
            self.export_button.setEnabled(False)
            self.static_button.setEnabled(False)
            destination = core.export(s)
            self.controls["target"].setText(s.target)
            self.set_status("导出完成：{path}", path=str(destination))
        except hou.OperationInterrupted:
            self.set_status("已取消导出，原帧位置已恢复。")
        except Exception as e:
            self.report_error(e)
        finally:
            self.controls["target"].setText(s.target)
            self.preview_button.setEnabled(True)
            self.export_button.setEnabled(True)
            self.static_button.setEnabled(True)

    def export_static(self):
        s = self.collect()
        try:
            core.validate(s, animation=False)
            for b in (self.preview_button, self.static_button, self.export_button):
                b.setEnabled(False)
            destination = core.export_static(s)
            self.set_status("静帧导出完成：{path}", path=str(destination / "Frame.csv"))
        except hou.OperationInterrupted:
            self.set_status("已取消静帧导出，原帧位置已恢复。")
        except Exception as e:
            self.report_error(e)
        finally:
            self.controls["target"].setText(s.target)
            for b in (self.preview_button, self.static_button, self.export_button):
                b.setEnabled(True)


def show_window():
    global _window
    if _window is None:
        _window = ExportPanel(hou.qt.mainWindow())
        _window.setWindowFlags(QtCore.Qt.Window)
        _window.resize(620, 780)
    _window.show()
    _window.raise_()
    _window.activateWindow()
    return _window
