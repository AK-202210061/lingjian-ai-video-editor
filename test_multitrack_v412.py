from __future__ import annotations
import json,subprocess
from pathlib import Path
from core import Clip,OverlayClip,Project,build_render_command
from edit_protocol import apply_opening_treatment,plan_to_clips,plan_to_overlays
from test_creative_opening_v49 import base_plan

ROOT=Path(__file__).resolve().parent
FFMPEG=str(ROOT/'ffmpeg.exe')
OUT=ROOT.parent.parent/'work'/'v412-multitrack-tests'
SOURCES=[Path(r'G:\DCIM\DJI_001\DJI_20260825051714_0310_D.MP4'),Path(r'G:\DCIM\DJI_001\DJI_20260825052108_0311_D.MP4'),Path(r'G:\DCIM\DJI_001\DJI_20260825052734_0312_D.MP4')]

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    for source in SOURCES:assert source.exists(),source
    results=[]
    for round_no in range(1,6):
        main=Clip(str(SOURCES[0]),0,2.6,SOURCES[0].name,has_audio=True)
        overlays=[
            OverlayClip(str(SOURCES[1]),.9,2.1,.15,SOURCES[1].name,2,'pip_right','ellipse',.76,.25,.36,.29,10.,.94,True),
            OverlayClip(str(SOURCES[2]),1.8,2.7,.42,SOURCES[2].name,3,'pip_left','none',.24,.55,.30,.24,8.,.86,True),
        ]
        if round_no%2==0:overlays[0].mask_shape='circle';overlays[0].x=.68
        project=Project(title=f'multitrack-{round_no}',clips=[main],overlays=overlays)
        saved=OUT/f'round-{round_no}.ljproject';project.save(saved);loaded=Project.load(saved)
        assert len(loaded.overlays)==2 and loaded.overlays[0].track==2 and loaded.overlays[1].track==3
        output=OUT/f'multitrack-{round_no}.mp4'
        render=subprocess.run(build_render_command(FFMPEG,loaded,str(output),360,640,'standard'),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        assert render.returncode==0,render.stderr.decode('utf-8','replace')[-4000:]
        decode=subprocess.run([FFMPEG,'-v','error','-i',str(output),'-f','null','NUL'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        assert decode.returncode==0,decode.stderr.decode('utf-8','replace')
        assert output.stat().st_size>10000
        results.append({'round':round_no,'tracks':[x.track for x in loaded.overlays],'bytes':output.stat().st_size})
    for preset in ('bounce_time','carousel_flash','split_rhythm'):
        plan=apply_opening_treatment(base_plan(),preset,'旅行叙事')
        overlays=plan_to_overlays(plan,OverlayClip)
        assert len(overlays)==2 and [x.track for x in overlays]==[2,3]
        assert 'AI 多轨合成' in __import__('edit_protocol').plan_preview_text(plan)
        if preset=='bounce_time':
            ai_output=OUT/'ai-bounce-v2-v3.mp4';ai_project=Project(title='ai-multitrack',clips=plan_to_clips(plan,Clip),overlays=overlays,edit_plan=plan)
            ai_render=subprocess.run(build_render_command(FFMPEG,ai_project,str(ai_output),360,640,'standard'),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            assert ai_render.returncode==0,ai_render.stderr.decode('utf-8','replace')[-4000:]
            assert ai_output.stat().st_size>10000
    (OUT/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'status':'PASS','rounds':results,'ai_presets':3},ensure_ascii=False))

if __name__=='__main__':run()
