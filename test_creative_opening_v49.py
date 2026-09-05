from __future__ import annotations

import json
import subprocess
from pathlib import Path

from core import Clip, Project, build_render_command
from edit_protocol import (OPENING_PRESETS, apply_opening_treatment, build_edit_plan,
                           plan_preview_text, plan_to_clips)


ROOT = Path(__file__).resolve().parent
FFMPEG = str(ROOT / "ffmpeg.exe")
SOURCES = [
    Path(r"G:\DCIM\DJI_001\DJI_20260825051714_0310_D.MP4"),
    Path(r"G:\DCIM\DJI_001\DJI_20260825052108_0311_D.MP4"),
    Path(r"G:\DCIM\DJI_001\DJI_20260825052734_0312_D.MP4"),
]
OUT_DIR = ROOT.parent.parent / "work" / "v49-opening-tests"


def base_plan():
    analyses = [{"meta": {"path": str(source), "name": source.name,
                           "duration": 120.0, "has_audio": True,
                           "capture_order": f"2026082505{17+i*4:02d}14"}, "segments": []}
                for i, source in enumerate(SOURCES)]
    sequence = [
        {"source_index": 0, "start": 0.0, "end": .8, "role": "hook",
         "caption": "今天，从这里出发", "reason": "开场钩子", "transition": "cut"},
        {"source_index": 1, "start": .9, "end": 1.7, "role": "setup",
         "caption": "先看看沿途", "reason": "建立环境", "transition": "cut"},
        {"source_index": 2, "start": 1.8, "end": 2.6, "role": "development",
         "caption": "故事正式开始", "reason": "进入正文", "transition": "cut"},
    ]
    return build_edit_plan(sequence, analyses, 2.4, "旅行 Vlog，真实顺序", "test")


def run():
    for source in SOURCES:
        if not source.exists(): raise FileNotFoundError(source)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results = []
    for round_no, preset_id in enumerate(OPENING_PRESETS, 1):
        plan = apply_opening_treatment(base_plan(), preset_id, "旅行叙事")
        creative = plan["creative_direction"]
        assert creative["preset_id"] == preset_id
        assert len(creative["shots"]) >= 1
        assert plan["validation"]["ok"], plan["validation"]
        preview = plan_preview_text(plan)
        assert creative["name"] in preview and "高级开篇" in preview and "蒙版" in preview
        clips = plan_to_clips(plan, Clip)
        if preset_id == "hollow_vlog":
            assert len(clips) == 4
            assert clips[0].title_effect == "text_window" and clips[0].title_text == "VLOG"
            assert len(clips[0].title_fill_segments) == len(SOURCES)
            assert len({x["path"] for x in clips[0].title_fill_segments}) == len(SOURCES)
            assert "个性标题 text_window" in preview
        elif preset_id == "carousel_flash":
            assert len(clips) == 6
            assert len({c.path for c in clips[:3]}) == len(SOURCES)
            assert all(c.role == "hook" for c in clips[:3])
        else:
            assert [c.mask_shape for c in clips[:3]] == [x[0] for x in OPENING_PRESETS[preset_id]["beats"]]
            if preset_id == "bounce_time":
                assert clips[0].title_effect == "bounce" and clips[0].title_text == "时光回溯"
        project = Project(title=f"opening-{preset_id}", clips=clips, edit_plan=plan)
        output = OUT_DIR / f"opening-{round_no}-{preset_id}.mp4"
        command = build_render_command(FFMPEG, project, str(output), 360, 640, "standard")
        rendered = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        assert rendered.returncode == 0, rendered.stderr.decode("utf-8", "replace")[-2000:]
        decoded = subprocess.run([FFMPEG, "-v", "error", "-i", str(output), "-f", "null", "NUL"],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        assert decoded.returncode == 0, decoded.stderr.decode("utf-8", "replace")
        assert output.stat().st_size > 5000
        results.append({"round": round_no, "preset": preset_id,
                        "bytes": output.stat().st_size, "masks": [c.mask_shape for c in clips]})
    report = OUT_DIR / "results.json"
    report.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"passed": len(results), "rounds": results}, ensure_ascii=False))


if __name__ == "__main__":
    run()
