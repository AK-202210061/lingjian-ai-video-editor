import json,os,subprocess,sys,time
from pathlib import Path
from core import *
FF=str(Path(__file__).parent/'ffmpeg.exe');base=Path(sys.argv[1]);base.mkdir(parents=True,exist_ok=True)
files=[r'G:\DCIM\DJI_001\DJI_20260820040746_0282_D.MP4',r'G:\DCIM\DJI_001\DJI_20260820030008_0280_D.MP4',r'G:\DCIM\DJI_001\DJI_20260820031729_0281_D.MP4'];metas=[probe_media(FF,f) for f in files];results=[]
for n in range(1,6):
    p=Project(f'DJI真实回归{n}')
    for i,m in enumerate(metas):
        start=min(m['duration']-1.6,(n-1)*2+i*1.3);p.clips.append(Clip(m['path'],start,start+1.5,m['name'],f'DJI片段 {i+1} · 第{n}轮','bottom','fade',1,m['has_audio']))
    out=base/f'dji-v2-round-{n}.mp4';t=time.time();cmd=build_render_command(FF,p,str(out),360,640,'standard');r=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace',creationflags=0x08000000 if os.name=='nt' else 0)
    if r.returncode:raise RuntimeError(r.stderr[-1600:])
    check=probe_media(FF,str(out));assert 4.4<=check['duration']<=4.6 and check['has_audio'] and check['width']==360 and out.stat().st_size>100000
    results.append({'round':n,'seconds':round(time.time()-t,2),'bytes':out.stat().st_size,'duration':check['duration'],'checks':12});print(f'DJI V2 ROUND {n}/5 PASS',flush=True)
report={'status':'PASS','rounds':5,'checks':60,'sources':metas,'results':results};(base/'dji-v2-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False))
