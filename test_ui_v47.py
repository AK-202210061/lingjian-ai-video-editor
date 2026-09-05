import os,sys
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication,QPushButton
from app_v2 import Main

app=QApplication.instance() or QApplication(sys.argv)
for round_no in range(1,6):
    window=Main();window.resize(1280,800);window.show();app.processEvents()
    assert '4.7.0' in window.windowTitle()
    for value in ('pip_zoom','tear_left','tear_right','pixelize','squeeze','radial','fade_black','fade_white','cover_left','reveal_right'):
        assert window.transition.findData(value)>=0,value
    for value in ('diamond','vertical_strip','split_left','split_right','privacy_blur','vignette'):
        assert window.mask_shape.findData(value)>=0,value
    buttons=[b.text() for b in window.inspector.widget(3).findChildren(QPushButton)]
    for text in ('菱形聚焦','竖条聚焦','左侧分屏','右侧分屏','隐私模糊','电影暗角'):
        assert text in buttons,text
    window.apply_mask_preset('privacy');assert window.mask_shape.currentData()=='privacy_blur'
    window.apply_mask_preset('vignette');assert window.mask_shape.currentData()=='vignette'
    assert window.timeline_scroll.height()>=218
    window.close();app.processEvents();print(f'V4.7 UI ROUND {round_no}/5 PASS')
