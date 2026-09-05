"""Read-only regression against the eight user-supplied DJI source files."""
from pathlib import Path

from core import Clip, Project, probe_media
from edit_protocol import build_edit_plan, plan_to_clips, project_quality_gate


ROOT = Path(r"G:\DCIM\DJI_001")
NAMES = [
    "DJI_20260825045333_0306_D.MP4",
    "DJI_20260825045608_0307_D.MP4",
    "DJI_20260825045819_0308_D.MP4",
    "DJI_20260825050341_0309_D.MP4",
    "DJI_20260825051714_0310_D.MP4",
    "DJI_20260825052108_0311_D.MP4",
    "DJI_20260825052734_0312_D.MP4",
    "DJI_20260825053053_0313_D.MP4",
]


def run(ffmpeg: str) -> None:
    paths = [ROOT / name for name in NAMES]
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise AssertionError("真实 DJI 素材缺失：" + ", ".join(missing))
    metas = [probe_media(ffmpeg, str(path)) for path in paths]
    assert all(meta["duration"] > 10 for meta in metas)
    assert [meta["capture_order"] for meta in metas] == sorted(meta["capture_order"] for meta in metas)
    analyses = [{"meta": meta, "segments": []} for meta in metas]

    for round_no in range(1, 6):
        sequence = [{
            "source_index": 7, "start": 6, "end": 9, "role": "hook",
            "caption": "先看最后的结果", "reason": "只允许一次未来结果钩子", "transition": "cut",
        }]
        for i, meta in enumerate(metas):
            sequence.append({
                "source_index": i, "start": 1, "end": min(6, meta["duration"]),
                "role": "setup" if i == 0 else ("outro" if i == len(metas) - 1 else "development"),
                "caption": "", "reason": f"按拍摄顺序推进第 {i + 1} 段", "transition": "cut",
            })
        plan = build_edit_plan(sequence, analyses, 120, "这些素材按顺序拍摄，正文严格遵守真实时间", "real-dji")
        assert plan["validation"]["ok"], plan["validation"]
        assert plan["validation"]["chronology_ratio"] == 1.0
        project = Project(clips=plan_to_clips(plan, Clip), edit_plan=plan)
        report = project_quality_gate(project, {m["path"]: m["duration"] for m in metas})
        assert report["ok"], report

        reversed_sequence = list(sequence)
        reversed_sequence[2], reversed_sequence[3] = reversed_sequence[3], reversed_sequence[2]
        bad = build_edit_plan(reversed_sequence, analyses, 120, "严格拍摄顺序", "real-dji-adversarial")
        assert not bad["validation"]["ok"]
        assert any("真实拍摄顺序" in x for x in bad["validation"]["blockers"])
        print(f"V4.4 REAL DJI ROUND {round_no}/5 PASS")


if __name__ == "__main__":
    run(str(Path(__file__).with_name("ffmpeg.exe")))
