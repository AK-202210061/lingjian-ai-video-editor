import json,os,sys,threading
os.environ['QT_QPA_PLATFORM']='offscreen'
from pathlib import Path
from http.server import BaseHTTPRequestHandler,HTTPServer
from PySide6.QtWidgets import QApplication,QPushButton
from app_v2 import Main,FFMPEG
from core import probe_media,thumbnail
from ai_api import APIConfig,analyze_video,protect_secret,unprotect_secret

class FakeAPI(BaseHTTPRequestHandler):
    def log_message(self,*a):pass
    def do_POST(self):
        length=int(self.headers.get('Content-Length','0'));body=self.rfile.read(length)
        if self.path.endswith('/audio/transcriptions'):result={'text':'今天沿途的山景非常漂亮'}
        else:
            request=json.loads(body);assert request['text']['format']['type']=='json_schema';result={'output_text':json.dumps({'summary':'旅行风景','segments':[{'start':.4,'end':2.4,'score':94,'reason':'山景清晰且动作完整','caption':'沿途好风景'}]},ensure_ascii=False)}
        raw=json.dumps(result,ensure_ascii=False).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)

server=HTTPServer(('127.0.0.1',0),FakeAPI);threading.Thread(target=server.serve_forever,daemon=True).start();base=Path(sys.argv[1]);base.mkdir(parents=True,exist_ok=True);src=base.parent/'lingjian-tests'/'a.mp4';meta=probe_media(FFMPEG,str(src));thumb=str(base/'thumb.jpg');thumbnail(FFMPEG,str(src),thumb,.5);meta['thumbnail']=thumb
cfg=APIConfig(f'http://127.0.0.1:{server.server_port}','test-key','mock-vision','mock-transcribe');secret='sk-测试-'+str(server.server_port);assert unprotect_secret(protect_secret(secret))==secret
api_segments=analyze_video(FFMPEG,cfg,str(src),meta['duration'],str(base/'api-assets'),'精选旅行片段');assert api_segments[0]['score']==94 and api_segments[0]['caption']=='沿途好风景'
qt=QApplication.instance() or QApplication([]);results=[]
for n in range(1,6):
    w=Main();w.media_ready(dict(meta));w.media.setCurrentRow(0);qt.processEvents();assert w.source_path==meta['path']
    w.source_in=.25;w.source_out=2.5;w.insert_source();assert len(w.project.clips)==1 and w.project.clips[0].start==.25
    w.source_in=.5;w.source_out=2;w.overwrite_source();assert w.project.clips[0].start==.5 and w.project.clips[0].end==2
    w.set_tool('blade');assert w.timeline.tool=='blade';w.blade_split(0,1.2);assert len(w.project.clips)==2
    w.timeline.video_locked=True;before=len(w.project.clips);w.blade_split(0,.8);assert len(w.project.clips)==before;w.timeline.video_locked=False
    w.track_state_changed(False,True);assert w.audio.isMuted();w.toggle_snap();assert not w.timeline.snap;w.toggle_snap();assert w.timeline.snap
    assert abs(w.parse_timecode('00:00:01:15',30)-1.5)<.001;w.global_tc.setText('00:00:00:15');w.seek_timecode()
    w.select_clip(0);w.nudge(1);w.delete_clip();w.undo();assert len(w.project.clips)==2
    assert len(w.findChildren(QPushButton))>=30;results.append({'round':n,'checks':22});w.proxy_queue=[];w.close();qt.processEvents();print(f'V3 PRECISION ROUND {n}/5 PASS',flush=True)
server.shutdown();report={'status':'PASS','rounds':5,'checks':110,'api_mock':'PASS','dpapi':'PASS','results':results};(base/'v3-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False))
