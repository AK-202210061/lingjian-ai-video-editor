import os,sys,json,tempfile
os.environ['QT_QPA_PLATFORM']='offscreen'
from pathlib import Path
from PySide6.QtWidgets import QApplication,QListWidgetItem,QPushButton
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from app_v2 import Main,FFMPEG
from core import probe_media,thumbnail,build_proxy_command,proxy_path,Project

qt=QApplication.instance() or QApplication([]);base=Path(sys.argv[1]);base.mkdir(parents=True,exist_ok=True);src=base.parent/'lingjian-tests'/'a.mp4';results=[]
meta=probe_media(FFMPEG,str(src));thumb=str(base/'thumb.jpg');thumbnail(FFMPEG,str(src),thumb,.5);meta['thumbnail']=thumb
for n in range(1,6):
    w=Main();w.media_ready(dict(meta));assert w.media.count()==1 and meta['path'] in w.metas
    w.media.setCurrentRow(0);w.add_selected_media();assert len(w.project.clips)==1 and w.timeline.project is w.project
    w.duplicate_clip();assert len(w.project.clips)==2;w.undo();assert len(w.project.clips)==1;w.redo();assert len(w.project.clips)==2
    w.select_clip(0);w.start.setValue(.2);w.end.setValue(1.7);w.caption.setText(f'第{n}轮');w.apply_clip();assert w.project.clips[0].caption==f'第{n}轮' and abs(w.project.clips[0].duration-1.5)<.01
    w.timeline_move(0,1);assert w.current_clip==1;w.timeline_trim(1,.3,1.5);assert abs(w.project.clips[1].start-.3)<.01
    w.global_seek(.5);assert w.current_clip==0;w.delete_clip();assert len(w.project.clips)==1
    w.auto_save();assert w.autosave.exists();loaded=Project.load(w.autosave);assert loaded.clips
    assert len(w.findChildren(QPushButton))>=20 and w.timeline.width()>=760
    results.append({'round':n,'checks':19});w.close();qt.processEvents();print(f'V2 UI ROUND {n}/5 PASS',flush=True)
report={'status':'PASS','rounds':5,'checks':95,'results':results};(base/'v2-ui-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False))
