import json,subprocess,sys
from pathlib import Path
from core import Clip,Project,build_render_command,probe_media,validate_rendered_mp4

ROOT=Path(__file__).parent;FF=str(ROOT/'ffmpeg.exe');BASE=Path(sys.argv[1]);BASE.mkdir(parents=True,exist_ok=True)
src=BASE.parent/'lingjian-tests'/'a.mp4'
transitions=['none','fade','dissolve','wipe_left','wipe_right','slide_left','slide_right','circle','smooth']
masks=['none','spotlight','ellipse','portrait_card','cinema']
fonts=['微软雅黑','黑体','宋体','等线','Arial','Impact','Consolas']

def run(args):
    p=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',errors='replace')
    if p.returncode:raise AssertionError((p.stderr or '')[-1800:])

for round_no in range(1,6):
    p=Project(title=f'创作者控制测试{round_no}')
    for i,transition in enumerate(transitions):
        start=(i%3)*.55;clip=Clip(str(src),start,start+1.0,f'镜头{i+1}',f'字幕样式 {i+1}','lower_third' if i%2 else 'bottom',transition,1,True)
        clip.transition_duration=.15;clip.caption_font=fonts[i%len(fonts)];clip.caption_size=24+i;clip.caption_color=['#FFFFFF','#FFD43B','#45E0E8'][i%3];clip.caption_bg_opacity=.35+.05*(i%4);clip.mask_shape=masks[i%len(masks)];clip.mask_x=.45+.05*(i%3);clip.mask_y=.5;clip.mask_width=.65;clip.mask_height=.68;clip.mask_feather=12+i;clip.mask_opacity=.9;p.clips.append(clip)
    project_file=BASE/f'creator-{round_no}.ljproject';p.save(project_file);loaded=Project.load(project_file)
    assert loaded.to_dict()['version']==2 and len(loaded.clips)==9
    assert loaded.clips[5].caption_font==fonts[5] and loaded.clips[3].mask_shape=='portrait_card'
    cmd=build_render_command(FF,loaded,str(BASE/f'creator-{round_no}.mp4'),320,180,'standard');graph=cmd[cmd.index('-filter_complex')+1]
    assert 'xfade=transition=' in graph and 'drawtext=' in graph and 'geq=' in graph and 'boxblur=' in graph
    run(cmd);meta=validate_rendered_mp4(FF,str(BASE/f'creator-{round_no}.mp4'))
    assert meta['width']==320 and meta['height']==180 and meta['has_audio']
    # Editing after AI generation remains fully reversible and ordinary.
    before=len(loaded.clips);loaded.split(1,loaded.clips[1].start+.5);loaded.delete(0);loaded.move(1,0)
    assert len(loaded.clips)==before and loaded.clips[0].duration>0
    print(f'CREATOR CONTROLS ROUND {round_no}/5 PASS',flush=True)
print(json.dumps({'status':'PASS','rounds':5,'transitions':len(transitions),'masks':len(masks),'fonts':len(fonts),'features':['split','delete','reorder','subtitle-style','transition','mask','render']},ensure_ascii=False))
