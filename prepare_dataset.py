"""Optional helper: organize a dataset already downloaded on your computer.

Expected input:
raw_dataset/
  real/
  ai/

Copies supported image files into dataset/real and dataset/ai. This script
does not download images or verify licensing/labels.
"""
import argparse
import shutil
from pathlib import Path

EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="raw_dataset")
    parser.add_argument("--output", default="dataset")
    args = parser.parse_args()
    source, output = Path(args.source), Path(args.output)
    count = 0
    for label in ("real", "ai"):
        src = source / label
        if not src.is_dir():
            print(f"Skipping missing folder: {src}")
            continue
        dst = output / label
        dst.mkdir(parents=True, exist_ok=True)
        for path in src.rglob("*"):
            if path.is_file() and path.suffix.lower() in EXTENSIONS:
                target = dst / f"{path.parent.name}_{path.name}"
                shutil.copy2(path, target)
                count += 1
    print(f"Copied {count} images into {output.resolve()}")
    print("Check labels, licenses, class balance, and duplicates before training.")


if __name__ == "__main__":
    main()
