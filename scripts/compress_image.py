#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from PIL import Image, ImageOps


def parse_size(value: str) -> int:
    text = value.strip().lower()
    if text.endswith("kb"):
        return int(float(text[:-2].strip()) * 1024)
    if text.endswith("mb"):
        return int(float(text[:-2].strip()) * 1024 * 1024)
    return int(text)


def format_size(num: int) -> str:
    if num >= 1024 * 1024:
        return f"{num / (1024 * 1024):.2f}MB"
    if num >= 1024:
        return f"{num / 1024:.1f}KB"
    return f"{num}B"


def save_png(img: Image.Image, path: Path) -> None:
    img.save(path, format="PNG", optimize=True, compress_level=9)


def save_jpeg(img: Image.Image, path: Path, quality: int) -> None:
    rgb = ImageOps.exif_transpose(img).convert("RGB")
    rgb.save(path, format="JPEG", quality=quality, optimize=True, progressive=True)


def save_webp(img: Image.Image, path: Path, quality: int) -> None:
    rgb = ImageOps.exif_transpose(img).convert("RGB")
    rgb.save(path, format="WEBP", quality=quality, method=6)


def output_path(src: Path, custom: str | None) -> Path:
    if custom:
        return Path(custom)
    return src.with_name(f"{src.stem}-compressed{src.suffix}")


def try_save(img: Image.Image, src: Path, dst: Path, format_name: str, quality: int | None = None) -> int:
    if dst.exists():
        dst.unlink()
    if format_name == "PNG":
        save_png(img, dst)
    elif format_name == "JPEG":
        save_jpeg(img, dst, quality or 85)
    elif format_name == "WEBP":
        save_webp(img, dst, quality or 85)
    else:
        raise ValueError(f"Unsupported format: {format_name}")
    return dst.stat().st_size


def compress(src: Path, target: int, custom_output: str | None, keep_format: bool) -> tuple[Path, int]:
    img = Image.open(src)
    img = ImageOps.exif_transpose(img)

    dst = output_path(src, custom_output)
    dst.parent.mkdir(parents=True, exist_ok=True)

    ext = src.suffix.lower()
    fmt = img.format or "PNG"
    if ext in {".jpg", ".jpeg"}:
        fmt = "JPEG"
    elif ext == ".webp":
        fmt = "WEBP"
    elif ext == ".png":
        fmt = "PNG"

    candidates: list[tuple[Image.Image, str, int | None]] = []
    if keep_format:
        candidates.append((img, fmt, 90))
        if fmt == "PNG":
            candidates.append((img.convert("P", palette=Image.Palette.ADAPTIVE, colors=256), "PNG", None))
            candidates.append((img.convert("P", palette=Image.Palette.ADAPTIVE, colors=128), "PNG", None))
    else:
        candidates.append((img, fmt, 90))
        if fmt != "JPEG":
            candidates.append((img, "JPEG", 88))
        if fmt != "WEBP":
            candidates.append((img, "WEBP", 85))
        candidates.append((img.convert("P", palette=Image.Palette.ADAPTIVE, colors=256), "PNG", None))
        candidates.append((img.convert("P", palette=Image.Palette.ADAPTIVE, colors=128), "PNG", None))

    best_path = dst
    best_size = None

    for current_img, current_fmt, quality in candidates:
        trial = dst.with_name(f"{dst.stem}.{current_fmt.lower()}{dst.suffix}")
        size = try_save(current_img, src, trial, current_fmt, quality)
        if best_size is None or size < best_size:
            best_size = size
            best_path = trial
        if size <= target:
            if trial != dst:
                if dst.exists():
                    dst.unlink()
                trial.replace(dst)
                best_path = dst
                best_size = size
            return dst, size

    if best_path != dst:
        if dst.exists():
            dst.unlink()
        best_path.replace(dst)
        best_path = dst

    if best_size is None:
        raise RuntimeError("Compression failed")

    if best_size <= target:
        return best_path, best_size

    # Reduce dimensions gradually if format-only attempts did not meet the target.
    working = img.copy()
    width, height = working.size
    for scale in (0.9, 0.8, 0.7, 0.6):
        resized = working.resize((max(1, int(width * scale)), max(1, int(height * scale))), Image.Resampling.LANCZOS)
        for current_fmt, quality in (("JPEG", 86), ("WEBP", 82), ("PNG", None)):
            trial = dst.with_name(f"{dst.stem}.{current_fmt.lower()}{dst.suffix}")
            size = try_save(resized, src, trial, current_fmt, quality)
            if size <= target:
                if dst.exists():
                    dst.unlink()
                trial.replace(dst)
                return dst, size
            if size < best_size:
                best_size = size
                if best_path != dst and best_path.exists():
                    best_path.unlink()
                best_path = trial

    if best_path != dst:
        if dst.exists():
            dst.unlink()
        best_path.replace(dst)
        best_path = dst
    return best_path, best_size


def main() -> int:
    parser = argparse.ArgumentParser(description="Compress an image to a target size.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("--target-size", default="2MB", help="Target size like 2MB, 800KB, or 1500000")
    parser.add_argument("--output", help="Custom output path")
    parser.add_argument("--keep-format", action="store_true", help="Avoid format fallback when possible")
    args = parser.parse_args()

    src = Path(args.input)
    if not src.exists():
        print(f"Input not found: {src}", file=sys.stderr)
        return 1

    target = parse_size(args.target_size)
    dst, size = compress(src, target, args.output, args.keep_format)
    print(dst)
    print(format_size(size))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
