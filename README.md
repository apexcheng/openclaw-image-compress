# OpenClaw Image Compress

A small OpenClaw-ready skill for compressing raster images to a size limit.

## What it does

- Defaults to compressing images under `2MB`
- Supports custom targets like `800KB`, `1.5MB`, or `1500000`
- Keeps the original file and writes a new `-compressed` copy

## Skill files

- `SKILL.md` - skill instructions and trigger guidance
- `scripts/compress_image.py` - the compression script
- `agents/openai.yaml` - UI metadata for Codex/OpenClaw

## Usage

```bash
python scripts/compress_image.py input.png
python scripts/compress_image.py input.jpg --target-size 800KB
python scripts/compress_image.py input.png --target-size 1.5MB --output output.png
```

## Notes

- The script tries to preserve format and dimensions first.
- If needed, it falls back to other raster formats or smaller dimensions to meet the target size.
- The default target is `2MB` when no size is provided.
