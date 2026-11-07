"""Put Thai-capable fonts in fonts/ for CI renders.

The real fonts (Tahoma/Consolas) are proprietary and not in the repo. On a Linux runner we use the
TLWG fonts, falling back to DejaVu; metrics differ slightly, which only affects typography, not the
duration/frames/loudness checks. Locally, if fonts/ already has the real files, nothing is touched.
"""
import os
import shutil
import sys

TARGETS = {
    "tahoma.ttf": [
        "/usr/share/fonts/truetype/tlwg/Garuda.ttf",
        "/usr/share/fonts/truetype/tlwg/Loma.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ],
    "tahomabd.ttf": [
        "/usr/share/fonts/truetype/tlwg/Garuda-Bold.ttf",
        "/usr/share/fonts/truetype/tlwg/Loma-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ],
    "consola.ttf": [
        "/usr/share/fonts/truetype/tlwg/TlwgMono.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    ],
    "consolab.ttf": [
        "/usr/share/fonts/truetype/tlwg/TlwgMono-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    ],
}


def main():
    os.makedirs("fonts", exist_ok=True)
    for name, candidates in TARGETS.items():
        dst = os.path.join("fonts", name)
        if os.path.exists(dst) and os.path.getsize(dst) > 50_000:
            print(f"{dst}: already present, leaving it")
            continue
        for src in candidates:
            if os.path.exists(src):
                shutil.copyfile(src, dst)
                print(f"{dst} <- {src}")
                break
        else:
            print(f"{dst}: no candidate font found", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
