import os,sys
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication
from app_v2 import Main,ROOT

app=QApplication.instance() or QApplication(sys.argv)
for round_no in range(1,6):
    window=Main();window.resize(1280,800);window.show();window.inspector.setCurrentIndex(3);app.processEvents()
    assert '4.10.0' in window.windowTitle();assert (ROOT/'models'/'u2net_human_seg.onnx').exists();assert window.person_track_btn.text()=='✦  AI 抠人并跟踪当前片段';assert window.person_mode.count()==3 and window.person_quality.count()==3;assert window.person_strength.value()==72;assert window.timeline_scroll.height()>=218
    window.close();app.processEvents();print(f'V4.8 UI ROUND {round_no}/5 PASS')
