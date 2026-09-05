from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from core import Project,SFXCue,build_render_command
from edit_protocol import OPENING_PRESETS,apply_opening_treatment,plan_to_clips
from sfx_library import SFX_LIBRARY,resolve_sfx
from test_creative_opening_v49 import base_plan

ROOT=Path(__file__).resolve().parent
FFMPEG=str(ROOT/'ffmpeg.exe')
OUT=ROOT.parent.parent/'work'/'v410-sfx-tests'

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    for item in SFX_LIBRARY:
        path=Path(resolve_sfx(ROOT,item['id']))
        assert path.exists() and path.stat().st_size>1000,path
        check=subprocess.run([FFMPEG,'-v','error','-i',str(path),'-f','null','NUL'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        assert check.returncode==0,(path,check.stderr.decode('utf-8','replace'))
    results=[]
    for round_no,preset_id in enumerate(list(OPENING_PRESETS)[:5],1):
        plan=apply_opening_treatment(base_plan(),preset_id,'旅行叙事')
        assert plan['sound_cues'] and len(plan['sound_cues'])==len(plan['creative_direction']['sounds'])
        if preset_id=='carousel_flash':
            assert [x['effect_id'] for x in plan['sound_cues']]==['clock_tick','clock_tock','clock_tick']
        clips=plan_to_clips(plan,__import__('core').Clip)
        cues=[]
        for raw in plan['sound_cues']:
            path=resolve_sfx(ROOT,raw['effect_id']);cues.append(SFXCue(path,raw['start'],raw['effect_id'],raw['volume'],raw['effect_id']))
        project=Project(title=f'sfx-{preset_id}',clips=clips,edit_plan=plan,sfx=cues)
        saved=OUT/f'sfx-{round_no}.ljproject';project.save(saved);loaded=Project.load(saved)
        assert len(loaded.sfx)==len(cues) and all(x.effect_id for x in loaded.sfx)
        output=OUT/f'sfx-{round_no}-{preset_id}.mp4'
        render=subprocess.run(build_render_command(FFMPEG,loaded,str(output),360,640,'standard'),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        assert render.returncode==0,render.stderr.decode('utf-8','replace')[-3000:]
        probe=subprocess.run([FFMPEG,'-hide_banner','-i',str(output),'-af','volumedetect','-f','null','NUL'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',errors='replace')
        assert probe.returncode==0 and 'max_volume:' in probe.stderr and 'max_volume: -inf' not in probe.stderr
        max_volume=re.search(r'max_volume:\s*([^\s]+)',probe.stderr).group(1)
        results.append({'round':round_no,'preset':preset_id,'sfx':len(cues),'bytes':output.stat().st_size,'max_volume':max_volume})
    (OUT/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'status':'PASS','library':len(SFX_LIBRARY),'rounds':results},ensure_ascii=False))

if __name__=='__main__':run()
