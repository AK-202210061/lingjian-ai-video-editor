import json,os,subprocess,sys
from pathlib import Path
from core import Clip,Project,build_render_command,validate_rendered_mp4
from person_ai import process_person_video,MODEL_SHA256

ROOT=Path(__file__).parent;FF=str(ROOT/'ffmpeg.exe');MODEL=ROOT/'models'/'u2net_human_seg.onnx';BASE=Path(sys.argv[1]);BASE.mkdir(parents=True,exist_ok=True);SOURCE=Path(r'G:\DCIM\DJI_001\DJI_20260825051714_0310_D.MP4')
assert MODEL.exists() and MODEL.stat().st_size==175997641
assert SOURCE.exists()
results=[]
for round_no in range(1,6):
    out=BASE/f'person-track-{round_no}.mp4';report=process_person_video(FF,str(SOURCE),0,.34,str(out),str(MODEL),'blur','fast',72)
    meta=validate_rendered_mp4(FF,str(out));assert meta['width']==720 and meta['height']==1280 and report['frames']>=10 and report['tracks'] and out.with_suffix('.tracking.json').exists()
    project=Project('人物跟踪回归');clip=Clip(str(SOURCE),0,.34,'人物片段');clip.person_effect_path=str(out);clip.person_effect_start=0;clip.person_effect_end=.34;clip.person_effect_mode='blur';project.clips.append(clip);saved=BASE/f'person-track-{round_no}.ljproject';project.save(saved);loaded=Project.load(saved);assert loaded.clips[0].person_effect_path==str(out)
    final=BASE/f'person-track-final-{round_no}.mp4';cmd=build_render_command(FF,loaded,str(final),720,1280,'standard');assert str(out) in cmd and str(SOURCE) not in cmd[:cmd.index('-filter_complex')];done=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace',creationflags=0x08000000 if os.name=='nt' else 0);assert done.returncode==0,done.stderr[-1200:];assert validate_rendered_mp4(FF,str(final))['height']==1280
    results.append({'round':round_no,'frames':report['frames'],'track_points':len(report['tracks']),'bytes':out.stat().st_size});print(f'V4.8 PERSON TRACKING ROUND {round_no}/5 PASS',flush=True)
print(json.dumps({'status':'PASS','model_sha256':MODEL_SHA256,'results':results},ensure_ascii=False))
