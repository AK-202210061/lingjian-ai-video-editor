from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from core import Clip, Project, SFXCue, build_render_command, probe_media, validate_rendered_mp4
from creative_director import apply_global_creative_treatment
from music_library import MUSIC_LIBRARY, resolve_music
from sfx_library import SFX_LIBRARY, resolve_sfx


ROOT = Path(__file__).parent
FFMPEG = str(ROOT / "ffmpeg.exe")
DJI = Path(r"G:\DCIM\DJI_001\DJI_20260825051714_0310_D.MP4")


def plan_fixture():
    roles = (("setup", "建立旅行地点"), ("development", "人物移动推进"),
             ("climax", "发现结果揭示"), ("development", "食物物件特写"),
             ("outro", "结尾情绪回收"))
    return {"decisions": [{"source_path": str(DJI), "source_name": DJI.name, "start": i * 2.,
                            "end": i * 2. + 1.15, "role": role, "reason": reason,
                            "caption": reason, "transition": "none", "capture_order": f"{i:03d}"}
                           for i, (role, reason) in enumerate(roles)]}


def test_planner_five_rounds():
    for density in ("subtle", "balanced", "energetic", "balanced", "subtle"):
        result = apply_global_creative_treatment(plan_fixture(), "旅行叙事", density)
        direction = result["global_creative_direction"]
        assert direction["music_id"] == "travel_breeze"
        assert direction["accent_count"] >= 1
        assert [x["capture_order"] for x in result["decisions"]] == [f"{i:03d}" for i in range(5)]
        assert all(x["effect_id"] in {s["id"] for s in SFX_LIBRARY} for x in result["sound_cues"])


def real_render(round_id: int):
    if not DJI.exists():
        return None
    meta = probe_media(FFMPEG, str(DJI)); plan = apply_global_creative_treatment(plan_fixture(), "旅行叙事", "energetic")
    fonts = ("站酷快乐体", "站酷庆科黄油体", "霞鹜文楷", "站酷快乐体", "霞鹜文楷")
    clips = []
    for i, item in enumerate(plan["decisions"][:3]):
        c = Clip(str(DJI), item["start"] + round_id * .03, item["end"] + round_id * .03,
                 DJI.name, item["caption"], "lower_third", item["transition"], 1., meta["has_audio"])
        c.caption_font = fonts[(i + round_id) % len(fonts)]; c.caption_effect = item.get("caption_effect", "jelly")
        c.caption_color = item.get("caption_color", "#FFE66D"); c.motion_effect = item.get("motion_effect", "slow_push")
        clips.append(c)
    project = Project(title=f"v413-round-{round_id}", clips=clips,
                      bgm=resolve_music(ROOT, MUSIC_LIBRARY[round_id % len(MUSIC_LIBRARY)]["id"]), bgm_volume=.18,
                      bgm_id=MUSIC_LIBRARY[round_id % len(MUSIC_LIBRARY)]["id"], bgm_ducking=True)
    for cue in plan["sound_cues"][:2]:
        project.sfx.append(SFXCue(resolve_sfx(ROOT, cue["effect_id"]), cue["start"], cue["effect_id"], .48, cue["effect_id"]))
    out = ROOT / "discover" / f"v413-real-round-{round_id}.mp4"; out.parent.mkdir(exist_ok=True)
    run = subprocess.run(build_render_command(FFMPEG, project, str(out), 360, 640, "standard"),
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    if run.returncode:
        raise AssertionError(run.stderr[-3000:])
    check = validate_rendered_mp4(FFMPEG, str(out))
    assert check["duration"] > 2.4 and out.stat().st_size > 20000
    return out


if __name__ == "__main__":
    test_planner_five_rounds()
    rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    for i in range(rounds):
        print("PASS", i + 1, real_render(i))

