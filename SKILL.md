---
name: openclaw-image-compress
description: Compress image files to a target size for OpenClaw workflows, defaulting to under 2MB. Use when the user asks to shrink,压缩, optimize, or resize PNG/JPG/JPEG/WebP images, or when they specify a custom maximum size.
---

# OpenClaw Image Compress

Compress a raster image to a size limit.

Default behavior:
- Target `2MB` when the user does not specify a size.
- Support custom targets like `800KB`, `1.5MB`, or `1500000`.
- Write a new file with `-compressed` in the name.

## Workflow

1. Parse the requested target size.
2. Run `scripts/compress_image.py` with that target.
3. Return the compressed file path and final size.

## Usage

```bash
python scripts/compress_image.py input.png
python scripts/compress_image.py input.jpg --target-size 800KB
python scripts/compress_image.py input.png --target-size 1.5MB --output output.png
```

## Rules

- Prefer preserving the original format and dimensions first.
- If needed to meet the size limit, reduce dimensions before falling back to a smaller raster format.
- Keep the implementation simple and deterministic.
