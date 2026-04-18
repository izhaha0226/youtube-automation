from __future__ import annotations

import os
from pathlib import Path

import httpx
from PIL import Image, ImageDraw, ImageFont

from app.core.config import settings
from app.core.llm import llm
from app.core.logging import get_logger
from app.core.paths import workspace_dir
from app.core.prompts import load_prompt, render
from app.modules.thumbnail.video_frame import capture_candidates
from app.schemas import ThumbnailInput, ThumbnailOutput

log = get_logger(__name__)

THUMB_W, THUMB_H = 1280, 720

YELLOW = (253, 211, 36)
BLUE = (58, 134, 255)
BLACK = (10, 10, 16)
WHITE = (255, 255, 255)

IMAGE_MODEL_PRIORITY = [
    "fal-ai/nano-banana-2",
    "fal-ai/flux-pro/v1.1-ultra",
    "fal-ai/flux/dev",
]


def generate_thumbnail(
    run_id: str,
    payload: ThumbnailInput,
    *,
    source_video: str | None = None,
    ab_colors: bool = True,
) -> ThumbnailOutput:
    out_dir = workspace_dir(run_id, "thumbnails")

    # 1) LLM design doc
    system = (
        "You design premium high-CTR Korean YouTube thumbnails for 리치고 (economy/real-estate). "
        "Follow the high-view copy playbook. Output JSON only."
    )
    user = render(
        load_prompt("thumbnail_prompt"),
        title=payload.title,
        thumbnail_candidates=payload.thumbnail_text,
        style=payload.style,
    )
    design = llm(temperature=0.6).generate_json(system=system, user=user)

    # 2) Background layer — prefer video frames, fallback to AI
    drafts: list[str] = []
    if source_video:
        frames = capture_candidates(source_video, out_dir / "frames", count=3)
        drafts = frames or []

    if not drafts:
        drafts = _ai_generate(
            prompt=design.get("image_prompt") or payload.title,
            negative=design.get("negative_prompt", ""),
            out_dir=out_dir,
            n=2,
        )
    if not drafts:
        drafts = [_fallback_bg(out_dir)]

    # 3) Auxiliary elements (chart + icon) — optional, best effort
    chart_layer = _aux_generate(
        "minimalist crashing red downward stock chart line graph, transparent background, editorial, sharp, isolated PNG",
        out_dir,
        "chart",
    )
    icon_layer = _aux_generate(
        "single small korean apartment building silhouette icon, flat, bold yellow outline, transparent background, isolated PNG",
        out_dir,
        "icon",
    )

    # 4) Compose final(s)
    text_overlay = design.get("text_overlay") or payload.thumbnail_text
    accent_word = design.get("accent_word")

    final_path = out_dir / "final.png"
    _compose(
        base_path=drafts[0],
        profile_path=payload.profile_image,
        text=text_overlay,
        out_path=final_path,
        accent_word=accent_word if isinstance(accent_word, str) else None,
        accent_color=YELLOW,
        chart_layer=chart_layer,
        icon_layer=icon_layer,
    )

    alt_paths: list[str] = []
    if ab_colors:
        alt = out_dir / "final_blue.png"
        _compose(
            base_path=drafts[0],
            profile_path=payload.profile_image,
            text=text_overlay,
            out_path=alt,
            accent_word=accent_word if isinstance(accent_word, str) else None,
            accent_color=BLUE,
            chart_layer=chart_layer,
            icon_layer=icon_layer,
        )
        alt_paths.append(str(alt))

    log.info(
        "thumbnail.done",
        final=str(final_path),
        alt=alt_paths,
        template=design.get("template_used"),
    )
    return ThumbnailOutput(
        draft_images=drafts + alt_paths,
        final_image=str(final_path),
        overlay_used=bool(payload.profile_image),
        save_path=str(out_dir),
    )


# ---------- Fal.ai generation ----------


def _ai_generate(prompt: str, negative: str, out_dir: Path, n: int = 2) -> list[str]:
    if not settings.fal_key:
        return []
    os.environ["FAL_KEY"] = settings.fal_key
    import fal_client

    enriched = (
        prompt
        + " 16:9 horizontal 1280x720, wide cinematic composition, YouTube thumbnail format,"
        " clean right third for portrait overlay."
    )

    out: list[str] = []
    for model in IMAGE_MODEL_PRIORITY:
        try:
            for i in range(n):
                args: dict = {"prompt": enriched, "num_images": 1}
                if "flux" in model:
                    args["image_size"] = {"width": THUMB_W, "height": THUMB_H}
                    args["enable_safety_checker"] = True
                if negative and "flux" in model:
                    args["negative_prompt"] = negative

                res = fal_client.subscribe(model, arguments=args)
                imgs = res.get("images") or []
                if not imgs:
                    continue
                url = imgs[0].get("url")
                if not url:
                    continue
                data = httpx.get(url, timeout=60).content
                p = out_dir / f"draft_{i}.png"
                p.write_bytes(data)
                out.append(str(p))
            if out:
                log.info("thumb.ai.model", model=model, count=len(out))
                return out
        except Exception as e:
            log.warning("thumb.ai.error", model=model, error=str(e))
            continue
    return out


def _aux_generate(prompt: str, out_dir: Path, name: str) -> str | None:
    if not settings.fal_key:
        return None
    os.environ["FAL_KEY"] = settings.fal_key
    import fal_client

    try:
        res = fal_client.subscribe(
            "fal-ai/nano-banana-2",
            arguments={
                "prompt": prompt + " transparent background, isolated, 512x512 square",
                "num_images": 1,
            },
        )
        imgs = res.get("images") or []
        if not imgs:
            return None
        url = imgs[0].get("url")
        if not url:
            return None
        data = httpx.get(url, timeout=60).content
        p = out_dir / f"aux_{name}.png"
        p.write_bytes(data)
        return str(p)
    except Exception as e:
        log.info("thumb.aux.skip", name=name, error=str(e))
        return None


def _fallback_bg(out_dir: Path) -> str:
    img = Image.new("RGB", (THUMB_W, THUMB_H), (14, 30, 58))
    p = out_dir / "draft_fallback.png"
    img.save(p)
    return str(p)


# ---------- Composition ----------


def _compose(
    base_path: str,
    profile_path: str | None,
    text: str,
    out_path: Path,
    accent_word: str | None,
    accent_color: tuple[int, int, int],
    chart_layer: str | None = None,
    icon_layer: str | None = None,
) -> None:
    base = Image.open(base_path).convert("RGBA").resize((THUMB_W, THUMB_H))

    # Chart (top-left)
    if chart_layer and Path(chart_layer).exists():
        base = _paste_aux(base, chart_layer, (30, 30), max_size=(460, 320), opacity=0.92)

    # Icon (left mid)
    if icon_layer and Path(icon_layer).exists():
        base = _paste_aux(base, icon_layer, (70, 280), max_size=(170, 170), opacity=1.0)

    # Profile PNG (right side, alpha preserved)
    if profile_path and Path(profile_path).exists():
        base = _paste_profile_raw(base, profile_path)

    # Vignette
    base = _vignette(base)

    # Two-line headline, line-1 tilted -3°
    lines = _split_lines(text)
    base = _draw_headline_blocks(
        base, lines=lines, accent_word=accent_word, accent_color=accent_color
    )

    base.convert("RGB").save(out_path)


def _paste_aux(base, aux_path, pos, max_size, opacity=1.0) -> Image.Image:
    aux = Image.open(aux_path).convert("RGBA")
    aux.thumbnail(max_size)
    if opacity < 1.0:
        r, g, b, a = aux.split()
        a = a.point(lambda v: int(v * opacity))
        aux = Image.merge("RGBA", (r, g, b, a))
    canvas = base.copy()
    canvas.alpha_composite(aux, pos)
    return canvas


def _paste_profile_raw(base: Image.Image, profile_path: str) -> Image.Image:
    prof = Image.open(profile_path).convert("RGBA")
    target_h = int(THUMB_H * 0.98)
    ratio = target_h / prof.height
    target_w = int(prof.width * ratio)
    prof = prof.resize((target_w, target_h))

    alpha = prof.split()[-1]
    shadow = Image.new("RGBA", prof.size, (0, 0, 0, 0))
    sh_layer = Image.new("RGBA", prof.size, (0, 0, 0, 140))
    shadow.paste(sh_layer, (0, 0), alpha)

    px = THUMB_W - target_w + 60
    py = THUMB_H - target_h + 10
    canvas = base.copy()
    canvas.alpha_composite(shadow, (px + 10, py + 14))
    canvas.alpha_composite(prof, (px, py))
    return canvas


def _vignette(img: Image.Image) -> Image.Image:
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for y in range(int(img.height * 0.50), img.height):
        a = int(((y - img.height * 0.50) / (img.height * 0.50)) * 220)
        d.line([(0, y), (img.width, y)], fill=(0, 0, 0, a))
    return Image.alpha_composite(img, overlay)


def _split_lines(text: str) -> list[str]:
    lines = [ln.strip() for ln in text.replace("\r", "").split("\n") if ln.strip()]
    if len(lines) == 1 and len(lines[0]) > 10:
        s = lines[0]
        mid = _mid_break(s)
        lines = [s[:mid].strip(), s[mid:].strip()]
    return lines[:2] or [text.strip()]


def _draw_headline_blocks(
    img: Image.Image,
    lines: list[str],
    accent_word: str | None,
    accent_color: tuple[int, int, int],
) -> Image.Image:
    target_w = int(THUMB_W * 0.88)
    font1 = _fit_font(lines[0] if lines else "", target_w, start=220)
    font2 = _fit_font(lines[1] if len(lines) > 1 else "", target_w, start=180)

    line1_rot = None
    if lines:
        line1_img = _render_block(
            text=lines[0],
            font=font1,
            bg=accent_color,
            fg=BLACK,
            accent_word=None,
            accent_color=None,
            pad_x=40,
            pad_y=18,
        )
        line1_rot = line1_img.rotate(-3, resample=Image.BICUBIC, expand=True)

    line2_img = None
    if len(lines) > 1:
        line2_img = _render_block(
            text=lines[1],
            font=font2,
            bg=BLACK,
            fg=WHITE,
            accent_word=accent_word,
            accent_color=accent_color,
            pad_x=36,
            pad_y=16,
        )

    canvas = img.copy()
    bottom_margin = 28

    if line2_img is not None:
        y2 = THUMB_H - bottom_margin - line2_img.height
        x2 = (THUMB_W - line2_img.width) // 2
        canvas.alpha_composite(line2_img, (x2, y2))
        y_anchor = y2
    else:
        y_anchor = THUMB_H - bottom_margin

    if line1_rot is not None:
        y1 = y_anchor - line1_rot.height + 10
        x1 = (THUMB_W - line1_rot.width) // 2
        canvas.alpha_composite(line1_rot, (x1, max(0, y1)))

    return canvas


def _render_block(
    text: str,
    font: ImageFont.FreeTypeFont,
    bg: tuple[int, int, int],
    fg: tuple[int, int, int],
    accent_word: str | None,
    accent_color: tuple[int, int, int] | None,
    pad_x: int,
    pad_y: int,
) -> Image.Image:
    m = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    tw = _text_w(m, text, font)
    th = _text_h(m, text, font)
    block = Image.new("RGBA", (tw + pad_x * 2, th + pad_y * 2 + 10), bg + (255,))
    d = ImageDraw.Draw(block)
    x = pad_x
    y = pad_y - int(th * 0.05)
    if accent_word and accent_color and accent_word in text:
        before, _, after = text.partition(accent_word)
        d.text((x, y), before, font=font, fill=fg)
        x += _text_w(d, before, font)
        d.text((x, y), accent_word, font=font, fill=accent_color)
        x += _text_w(d, accent_word, font)
        d.text((x, y), after, font=font, fill=fg)
    else:
        d.text((x, y), text, font=font, fill=fg)
    return block


# ---------- Font & metrics ----------


def _fit_font(text: str, target_w: int, start: int = 220, floor: int = 80):
    if not text:
        return _font(start)
    m = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    size = start
    while size > floor:
        f = _font(size)
        bbox = m.textbbox((0, 0), text, font=f)
        if (bbox[2] - bbox[0]) <= target_w:
            return f
        size -= 6
    return _font(floor)


def _text_w(draw, text, font) -> int:
    if not text:
        return 0
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]


def _text_h(draw, text, font) -> int:
    if not text:
        return 0
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[3] - bbox[1]


def _mid_break(s: str) -> int:
    mid = len(s) // 2
    for offset in range(0, 6):
        for d in (0, 1, -1):
            i = mid + offset * d
            if 0 < i < len(s) and s[i] == " ":
                return i
    return mid


def _font(size: int) -> ImageFont.FreeTypeFont:
    candidates = [
        _data_font("Paperlogy-9Black.ttf"),
        _data_font("Paperlogy-8ExtraBold.ttf"),
        _data_font("Pretendard-Black.otf"),
        _data_font("Pretendard-ExtraBold.otf"),
        _data_font("Pretendard-Bold.otf"),
        str(Path.home() / "Library/Fonts/Pretendard-Black.otf"),
        str(Path.home() / "Library/Fonts/Pretendard-ExtraBold.otf"),
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    ]
    for c in candidates:
        try:
            if Path(c).exists():
                return ImageFont.truetype(c, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _data_font(name: str) -> str:
    return str(settings.data_dir / "fonts" / name)
