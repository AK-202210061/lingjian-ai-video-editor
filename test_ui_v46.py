import os,sys
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication,QPushButton,QScrollArea
from app_v2 import Main,MaskGuide

app=QApplication.instance() or QApplication(sys.argv)
for round_no in range(1,6):
    window=Main();window.resize(1280,800);window.show();app.processEvents()
    assert '4.6.0' in window.windowTitle()
    assert window.timeline_scroll.height()>=218
    assert window.timeline.height()>=212
    assert window.vertical_workspace.count()==2
    assert window.inspector.tabText(3)=='智能蒙版'
    mask_page=window.inspector.widget(3)
    assert isinstance(mask_page,QScrollArea)
    assert isinstance(window.mask_guide,MaskGuide)
    buttons=[b.text() for b in mask_page.findChildren(QPushButton)]
    for text in ('✦  自动推荐','人物聚焦','美食 / 商品','口播卡片','电影感遮幅','▶  应用并生成真实效果预览'):
        assert text in buttons
    window.apply_mask_preset('person');assert window.mask_shape.currentData()=='spotlight' and window.mask_feather.value()==34
    window.apply_mask_preset('product');assert window.mask_shape.currentData()=='ellipse' and window.mask_y.value()==.56
    before=window.vertical_workspace.sizes()[1];window.toggle_timeline_space();app.processEvents();after=window.vertical_workspace.sizes()[1];assert after>before
    window.close();app.processEvents();print(f'V4.6 UI ROUND {round_no}/5 PASS')
