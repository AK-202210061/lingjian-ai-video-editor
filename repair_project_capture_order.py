"""Create a non-destructive capture-order-corrected copy of a LingJian project."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from core import Project, build_render_command, validate_rendered_mp4


def capture_key(clip):
    match = re.search(r"(\d{8})[_-]?(\d{6})", Path(clip.path).name)
    stamp = "".join(match.groups()) if match else Path(clip.path).name.lower()
    return stamp, clip.start


def main():
    if len(sys.argv) != 5:
        raise SystemExit("usage: repair_project_capture_order.py ffmpeg input-project output-project output-mp4")
    ffmpeg, input_project, output_project, output_mp4 = sys.argv[1:]
    project = Project.load(input_project)
    if not project.clips:
        raise SystemExit("project has no clips")

    # Preserve the existing opening result shot, then lock the remaining story.
    hook = project.clips[0]
    body = sorted(project.clips[1:], key=capture_key)
    project.clips = [hook, *body]
    project.title = f"{project.title}-按拍摄顺序修正版"
    project.prompt = f"{project.prompt}；严格按真实拍摄顺序，除成品钩子外不得回跳。"
    project.save(output_project)

    command = build_render_command(ffmpeg, project, output_mp4, 720, 1280, "standard")
    completed = subprocess.run(command)
    if completed.returncode:
        raise SystemExit(completed.returncode)
    meta = validate_rendered_mp4(ffmpeg, output_mp4)
    print(f"PASS clips={len(project.clips)} duration={project.duration:.2f} rendered={meta['duration']:.2f}")


if __name__ == "__main__":
    main()
