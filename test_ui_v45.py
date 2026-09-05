import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QPushButton

from app_v2 import Main, STYLE


app = QApplication.instance() or QApplication([])
app.setStyle("Fusion")
app.setStyleSheet(STYLE)

for round_no in range(1, 6):
    window = Main()
    window.show()
    app.processEvents()
    buttons = window.findChildren(QPushButton)
    labels = [button.text() for button in buttons]
    assert window.windowTitle().startswith("灵剪 AI 视频编辑器 4.5.0")
    assert window.centralWidget().objectName() == "appRoot"
    assert window.inspector.objectName() == "inspectorTabs"
    assert [window.inspector.tabText(i) for i in range(window.inspector.count())] == [
        "剪辑", "字幕", "转场", "蒙版", "AI", "接口", "导出",
    ]
    assert "✦ 生成方案并预览" in labels
    assert "检查当前时间线" in labels
    assert "导出前质量检查" in labels
    assert "↑  导出" in labels
    assert len(buttons) >= 45
    assert window.timeline.width() >= 760
    assert window.inspector.width() >= 390
    assert "rgba(255,255,255,224)" in STYLE and "border-top:1px solid #FFFFFF" in STYLE
    assert window.source_video.autoFillBackground() and window.video.autoFillBackground()
    window.close()
    app.processEvents()
    print(f"V4.5 UI ROUND {round_no}/5 PASS")
