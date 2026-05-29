from __future__ import annotations

from pathlib import Path

from collections import deque

from PIL import Image, ImageFilter, ImageOps


ROOT = Path(__file__).resolve().parent.parent
SOURCE = Path("/Users/wb_lujiahao/Desktop/1.jpg")
ASSET_DIR = ROOT / "desktop_pet" / "assets"


def main() -> None:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    base = Image.open(SOURCE).convert("RGBA")

    cropped = _crop_subject(base)
    transparent = _remove_white_background(cropped)
    fitted = _fit_square_canvas(transparent, 220)
    fitted.save(ASSET_DIR / "pet_idle.png")

    for name in ("pet_peek.png", "pet_sleep.png", "pet_blink.png"):
        fitted.save(ASSET_DIR / name)

    react = _react_variant(fitted)
    react.save(ASSET_DIR / "pet_react.png")


def _crop_subject(image: Image.Image) -> Image.Image:
    gray = ImageOps.grayscale(image)
    inverted = ImageOps.invert(gray)
    bbox = inverted.point(lambda x: 255 if x > 12 else 0).getbbox()
    if not bbox:
        return image
    left, top, right, bottom = bbox
    margin = 18
    left = max(0, left - margin)
    top = max(0, top - margin)
    right = min(image.width, right + margin)
    bottom = min(image.height, bottom + margin)
    return image.crop((left, top, right, bottom))


def _remove_white_background(image: Image.Image) -> Image.Image:
    rgba = image.copy()
    source = rgba.convert("RGB")
    pixels = source.load()
    width, height = rgba.size

    border_samples = []
    for x in range(width):
        border_samples.append(pixels[x, 0])
        border_samples.append(pixels[x, height - 1])
    for y in range(height):
        border_samples.append(pixels[0, y])
        border_samples.append(pixels[width - 1, y])
    bg = tuple(sum(pixel[i] for pixel in border_samples) // len(border_samples) for i in range(3))

    visited = bytearray(width * height)
    background = bytearray(width * height)
    queue = deque()

    def index(x: int, y: int) -> int:
        return y * width + x

    def is_background_like(x: int, y: int) -> bool:
        r, g, b = pixels[x, y]
        distance = abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2])
        # Keep dark pencil outlines and saturated purple/yellow toy colors opaque.
        saturation = max(r, g, b) - min(r, g, b)
        brightness = (r + g + b) / 3
        return distance < 72 and saturation < 34 and brightness > 205

    for x in range(width):
        for y in (0, height - 1):
            if is_background_like(x, y):
                queue.append((x, y))
                visited[index(x, y)] = 1
    for y in range(height):
        for x in (0, width - 1):
            if is_background_like(x, y) and not visited[index(x, y)]:
                queue.append((x, y))
                visited[index(x, y)] = 1

    while queue:
        x, y = queue.popleft()
        background[index(x, y)] = 255
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if nx < 0 or ny < 0 or nx >= width or ny >= height:
                continue
            i = index(nx, ny)
            if visited[i] or not is_background_like(nx, ny):
                continue
            visited[i] = 1
            queue.append((nx, ny))

    alpha = Image.new("L", (width, height), 255)
    alpha_pixels = alpha.load()
    for y in range(height):
        for x in range(width):
            if background[index(x, y)]:
                alpha_pixels[x, y] = 0

    alpha = alpha.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(radius=0.55))
    rgba.putalpha(alpha)
    return rgba


def _fit_square_canvas(image: Image.Image, canvas_size: int) -> Image.Image:
    subject = image.copy()
    bbox = subject.getbbox()
    if bbox:
        subject = subject.crop(bbox)

    max_side = int(canvas_size * 0.86)
    subject.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)

    canvas = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    x = (canvas_size - subject.width) // 2
    y = int(canvas_size * 0.06)
    canvas.alpha_composite(subject, (x, y))
    return canvas


def _react_variant(image: Image.Image) -> Image.Image:
    variant = image.copy()
    overlay = Image.new("RGBA", variant.size, (0, 0, 0, 0))
    for offset in (-2, 2):
        blush = Image.new("RGBA", variant.size, (0, 0, 0, 0))
        for y in range(variant.height):
            for x in range(variant.width):
                if (x - variant.width * 0.36 - offset) ** 2 + (y - variant.height * 0.47) ** 2 < 11 ** 2:
                    blush.putpixel((x, y), (255, 180, 190, 22))
                if (x - variant.width * 0.64 - offset) ** 2 + (y - variant.height * 0.47) ** 2 < 11 ** 2:
                    blush.putpixel((x, y), (255, 180, 190, 22))
        overlay = Image.alpha_composite(overlay, blush)
    return Image.alpha_composite(variant, overlay)


if __name__ == "__main__":
    main()
