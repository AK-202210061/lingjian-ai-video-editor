import os,sys
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication
from app_v2 import Main
from edit_protocol import OPENING_PRESETS,apply_opening_treatment

app=QApplication.instance() or QApplication(sys.argv)
for round_no in range(1,6):
    window=Main();window.resize(1280,800);window.show();window.inspector.setCurrentIndex(4);app.processEvents()
    assert '4.12.1' in window.windowTitle()
    assert window.opening_style.count()==len(OPENING_PRESETS)+1
    assert window.sfx_combo.count()==10
    assert window.title_effect.count()==3
    assert window.title_effect.findData('bounce')>=0
    assert window.title_effect.findData('text_window')>=0
    assert window.overlay_track.count()==5
    assert window.overlay_mask.findData('ellipse')>=0
    assert window.overlay_layout.findData('full')>=0
    for preset_id in OPENING_PRESETS:assert window.opening_style.findData(preset_id)>=0,preset_id
    assert '高级开头' in window.cloud_btn.text()
    window.timeline.set_playhead(1.25);window.add_sfx_at_playhead();assert len(window.project.sfx)==1 and abs(window.project.sfx[0].start-1.25)<.001
    window.sfx_list.setCurrentRow(0);window.remove_sfx();assert len(window.project.sfx)==0
    assert window.timeline_scroll.height()>=218
    window.close();app.processEvents();print(f'V4.9 UI ROUND {round_no}/5 PASS')
