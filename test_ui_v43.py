import os
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication, QPushButton

from app_v2 import Main


app = QApplication.instance() or QApplication(sys.argv)
for round_no in range(1, 6):
    window = Main()
    assert "4.3.0" in window.windowTitle()
    assert window.profile_status.text()
    labels = [button.text() for button in window.findChildren(QPushButton)]
    assert "学习当前人工时间线" in labels
    prompt = window.edit_prompt()
    assert "个人剪辑偏好" in prompt and "拍摄顺序" in prompt
    window.close()
    app.processEvents()
    print(f"V4.3 UI ROUND {round_no}/5 PASS", flush=True)

print("V4.3 UI + LOCAL PROFILE PASS: 5 rounds")
