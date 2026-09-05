import os,sys,json
os.environ['QT_QPA_PLATFORM']='offscreen'
from PySide6.QtWidgets import QApplication,QPushButton
from app import Main
from core import Clip

qt=QApplication.instance() or QApplication(sys.argv);results=[]
for n in range(1,6):
    w=Main();assert w.windowTitle().startswith('灵剪 AI');assert w.media is not None and w.timeline is not None
    buttons=w.findChildren(QPushButton);assert len(buttons)>=12
    w.project.clips=[Clip(__file__,0,2,'测试片段.mp4',f'字幕{n}')];w.refresh();assert w.timeline.count()==1
    w.timeline.setCurrentRow(0);assert w.caption.text()==f'字幕{n}'
    w.caption.setText(f'修改{n}');w.end.setValue(1.5);w.apply_clip();assert w.project.clips[0].caption==f'修改{n}' and w.project.clips[0].end==1.5
    results.append({'round':n,'buttons':len(buttons),'checks':8});w.close();qt.processEvents();print(f'UI ROUND {n}/5 PASS',flush=True)
Path=None
report={'status':'PASS','rounds':5,'total_checks':40,'results':results}
open(sys.argv[1] if len(sys.argv)>1 else 'ui-report.json','w',encoding='utf-8').write(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False))
