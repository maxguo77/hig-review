#!/usr/bin/env python3
"""
Deterministic helpers for UI-image review.
==========================================

The visual review itself is done by the model (it reads the image). These
helpers provide the things eyeballing can't do reliably:

  dims <image> [--scale N] [--platform P]
        -> pixel size, aspect, orientation, and — only when the size matches a
           known full-device screenshot — a device/scale/point-size + safe-area
           note. Window/region or non-standard captures are reported as such
           (no bogus device guess). Pass --scale to enable px↔pt anyway, and
           --platform to tailor the safe-area note.

  sample <image> X Y [X2 Y2 ...] [--norm] [--contrast] [--box R]
        -> the actual sRGB hex/rgb at each pixel (PNG only). Use this to ground
           a contrast check in real colors instead of eyeballing. With exactly
           two points + --contrast it also prints the WCAG ratio — and warns when
           the two colors are nearly identical (you likely sampled background
           twice and missed the text). --box R samples a (2R+1)² window per point
           (reporting avg/darkest/lightest) and, with --contrast, auto-picks the
           glyph stroke as the luminance extreme furthest from point 2's
           background — so thin/anti-aliased text doesn't need pixel-perfect aim.

  contrast <c1> <c2> [--large]
        -> WCAG contrast ratio + AA/AAA pass/fail. HIG gives no fixed value, so
           WCAG AA (4.5:1 body / 3:1 large) is the pragmatic stand-in
           (see general-review-mode.md). Prefer feeding it colors from `sample` or
           from values the design states; mark eyeballed inputs as estimates.

Colors accept "#RGB", "#RRGGBB", or "r,g,b". Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import struct
import sys
import zlib

# Known device screenshot sizes (portrait px) -> (label, scale, pt_w, pt_h).
# Matched in either orientation with a small tolerance.
KNOWN_DEVICES = {
    (1170, 2532): ("iPhone 12/13/14", 3, 390, 844),
    (1179, 2556): ("iPhone 14/15/16 Pro", 3, 393, 852),
    (1206, 2622): ("iPhone 16 Pro", 3, 402, 874),
    (1290, 2796): ("iPhone 14/15 Pro Max / Plus", 3, 430, 932),
    (1284, 2778): ("iPhone 12/13 Pro Max", 3, 428, 926),
    (1125, 2436): ("iPhone X/XS/11 Pro", 3, 375, 812),
    (1080, 2340): ("iPhone 12/13 mini", 3, 360, 780),
    (750, 1334): ("iPhone 6/7/8/SE2/SE3", 2, 375, 667),
    (1242, 2208): ("iPhone 6+/7+/8+", 3, 414, 736),
    (2048, 2732): ("iPad Pro 12.9\"", 2, 1024, 1366),
    (1668, 2388): ("iPad Pro 11\"", 2, 834, 1194),
    (1640, 2360): ("iPad Air 10.9\"", 2, 820, 1180),
    (1620, 2160): ("iPad 10.2\"", 2, 810, 1080),
    (1488, 2266): ("iPad mini 8.3\"", 2, 744, 1133),
    (396, 484): ("Apple Watch 45mm", 2, 198, 242),
    (410, 502): ("Apple Watch 49mm Ultra", 2, 205, 251),
    (368, 448): ("Apple Watch 44mm", 2, 184, 224),
}

TOL = 8  # px tolerance when matching known sizes


# --------------------------- image dimensions ---------------------------- #

def _png_size(d: bytes):
    if d[:8] == b"\x89PNG\r\n\x1a\n" and d[12:16] == b"IHDR":
        w, h = struct.unpack(">II", d[16:24])
        return w, h
    return None


def _gif_size(d: bytes):
    if d[:6] in (b"GIF87a", b"GIF89a"):
        w, h = struct.unpack("<HH", d[6:10])
        return w, h
    return None


def _jpeg_size(d: bytes):
    if d[:2] != b"\xff\xd8":
        return None
    i, n = 2, len(d)
    while i < n - 9:
        if d[i] != 0xFF:
            i += 1
            continue
        marker = d[i + 1]
        if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                      0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            h, w = struct.unpack(">HH", d[i + 5:i + 9])
            return w, h
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        seg_len = struct.unpack(">H", d[i + 2:i + 4])[0]
        i += 2 + seg_len
    return None


def _webp_size(d: bytes):
    if d[:4] != b"RIFF" or d[8:12] != b"WEBP":
        return None
    fmt = d[12:16]
    if fmt == b"VP8 ":
        return (struct.unpack("<H", d[26:28])[0] & 0x3FFF,
                struct.unpack("<H", d[28:30])[0] & 0x3FFF)
    if fmt == b"VP8L":
        b0, b1, b2, b3 = d[21], d[22], d[23], d[24]
        w = ((b1 & 0x3F) << 8 | b0) + 1
        h = ((b3 & 0x0F) << 10 | b2 << 2 | (b1 & 0xC0) >> 6) + 1
        return w, h
    if fmt == b"VP8X":
        w = (d[24] | d[25] << 8 | d[26] << 16) + 1
        h = (d[27] | d[28] << 8 | d[29] << 16) + 1
        return w, h
    return None


def image_size(path: str):
    with open(path, "rb") as f:
        d = f.read(64)
    for fn in (_png_size, _gif_size, _jpeg_size, _webp_size):
        try:
            r = fn(d)
        except Exception:
            r = None
        if r:
            return r
    raise ValueError("Unsupported or unreadable image (need PNG/JPEG/GIF/WebP).")


def match_device(w: int, h: int):
    """Return device info ONLY if size matches a known full-device screenshot."""
    pw, ph = min(w, h), max(w, h)
    orientation = "portrait" if h >= w else "landscape"
    for (kw, kh), (label, scale, ptw, pth) in KNOWN_DEVICES.items():
        if abs(pw - kw) <= TOL and abs(ph - kh) <= TOL:
            pt = [ptw, pth] if orientation == "portrait" else [pth, ptw]
            return {"matched": True, "device": label, "scale": scale,
                    "pt_size": pt, "orientation": orientation}
    return {"matched": False, "orientation": orientation}


def capture_hint(w: int, h: int) -> str:
    """Best-guess hint about what an UNMATCHED image probably is."""
    aspect = min(w, h) / max(w, h)
    if max(w, h) <= 512:
        return "small canvas (could be watchOS, an icon, or a cropped region)"
    if w >= h and max(w, h) >= 1280:
        return "landscape — likely a macOS window, a region crop, or tvOS/desktop"
    if 0.55 <= aspect <= 0.85:
        return "tablet-ish aspect, but not an exact iPad size — likely a window/region crop"
    if aspect < 0.55:
        return "tall aspect — phone-like, but not an exact device size"
    return "non-standard size — likely a window or region crop"


def safe_area_note(matched: dict, platform: str | None) -> str:
    if matched.get("matched"):
        dev = matched["device"]
        if "iPhone" in dev:
            return ("Top safe area (notch/Dynamic Island) + bottom home indicator "
                    "— keep content/controls clear of both.")
        if "iPad" in dev:
            return "Respect top status bar + multitasking; generous layout margins."
        if "Watch" in dev:
            return "Tiny canvas — large tap targets, minimal chrome, top time area."
    p = (platform or "").lower()
    if p == "macos":
        return ("macOS window — no device safe areas; check title bar/toolbar, "
                "resizable layout, and standard window controls instead.")
    if p in ("web", "数据大屏", "dashboard"):
        return "Web/dashboard — no Apple safe areas; judge by viewport & responsive layout."
    if p:
        return f"Platform '{platform}' — verify that platform's safe areas before judging edges."
    return ("Unknown capture — if it's a full-device screenshot tell me the device; "
            "if it's a window/region crop, device safe-areas don't apply.")


def cmd_dims(args) -> int:
    try:
        w, h = image_size(args.image)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    m = match_device(w, h)
    scale = m.get("scale") or args.scale
    info = {"width_px": w, "height_px": h, "orientation": m["orientation"],
            "aspect": round(min(w, h) / max(w, h), 4),
            "device": m.get("device") if m["matched"] else None,
            "matched_full_device": m["matched"],
            "scale": scale,
            "pt_size": m.get("pt_size"),
            "safe_area": safe_area_note(m, args.platform)}
    if not m["matched"]:
        info["capture_hint"] = capture_hint(w, h)
    if scale:
        info["tap_target_44pt_px"] = 44 * scale
        info["note_px_to_pt"] = f"divide px by {scale} to get points (@{scale}x)"
    if args.json:
        print(json.dumps(info, ensure_ascii=False, indent=2))
    else:
        print(f"{w}×{h}px  {info['orientation']}  aspect {info['aspect']}")
        if m["matched"]:
            print(f"device       : {m['device']}  (@{m['scale']}x, "
                  f"{m['pt_size'][0]}×{m['pt_size'][1]}pt)")
        else:
            print(f"device       : no full-device match — {info['capture_hint']}")
            if args.platform:
                print(f"platform     : {args.platform} (from --platform)")
        if scale:
            print(f"px↔pt        : {info['note_px_to_pt']}; 44pt target = {info['tap_target_44pt_px']}px")
        elif not m["matched"]:
            print("px↔pt        : unknown scale — pass --scale N (e.g. 2 for Retina) to enable")
        print(f"safe area    : {info['safe_area']}")
    return 0


# ----------------------------- PNG sampling ------------------------------ #

_CHANNELS = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}


def _paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    return b if pb <= pc else c


def _decode_png(path: str, max_row: int | None = None):
    """Minimal PNG decoder: 8/16-bit, color types 0/2/3/4/6, non-interlaced.
    Returns (width, height, get_pixel) where get_pixel(x, y) -> (r, g, b)."""
    with open(path, "rb") as f:
        data = f.read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG (pixel sampling supports PNG only)")
    idat = bytearray()
    plte = None
    w = h = bd = ct = interlace = 0
    pos = 8
    while pos < len(data):
        ln = struct.unpack(">I", data[pos:pos + 4])[0]
        ctype = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + ln]
        pos += 12 + ln  # length + type + data + crc
        if ctype == b"IHDR":
            w, h, bd, ct, _comp, _filt, interlace = struct.unpack(">IIBBBBB", body)
        elif ctype == b"PLTE":
            plte = body
        elif ctype == b"IDAT":
            idat += body
        elif ctype == b"IEND":
            break
    if interlace:
        raise ValueError("interlaced PNG not supported (re-export non-interlaced)")
    if ct not in _CHANNELS:
        raise ValueError(f"unsupported PNG color type {ct}")
    channels = _CHANNELS[ct]
    if bd not in (8, 16):
        raise ValueError(f"unsupported PNG bit depth {bd} (need 8 or 16)")
    sample_bytes = bd // 8
    bpp = channels * sample_bytes
    stride = w * bpp
    raw = zlib.decompress(bytes(idat))
    rows_needed = h if max_row is None else min(h, max_row + 1)

    recon = bytearray()
    prev = bytearray(stride)
    p = 0
    for _ in range(rows_needed):
        ft = raw[p]; p += 1
        line = bytearray(raw[p:p + stride]); p += stride
        if ft == 1:
            for i in range(bpp, stride):
                line[i] = (line[i] + line[i - bpp]) & 255
        elif ft == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 255
        elif ft == 3:
            for i in range(stride):
                a = line[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 255
        elif ft == 4:
            for i in range(stride):
                a = line[i - bpp] if i >= bpp else 0
                c = prev[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + _paeth(a, prev[i], c)) & 255
        recon += line
        prev = line

    def get_pixel(x, y):
        off = y * stride + x * bpp
        hi = sample_bytes - 1  # high byte for 16-bit, 0 for 8-bit
        if ct in (2, 6):
            return (recon[off + hi], recon[off + sample_bytes + hi],
                    recon[off + 2 * sample_bytes + hi])
        if ct in (0, 4):
            v = recon[off + hi]
            return (v, v, v)
        if ct == 3:  # palette index (bd==8)
            idx = recon[off]
            return (plte[idx * 3], plte[idx * 3 + 1], plte[idx * 3 + 2])
        raise ValueError("unhandled color type")

    return w, h, get_pixel


def _hex(rgb) -> str:
    return "#%02X%02X%02X" % rgb


def _window_pixels(get_pixel, cx, cy, w, h, r):
    """Every in-bounds RGB in the (2r+1)² window centred on (cx, cy)."""
    out = []
    for yy in range(cy - r, cy + r + 1):
        if not (0 <= yy < h):
            continue
        for xx in range(cx - r, cx + r + 1):
            if 0 <= xx < w:
                out.append(get_pixel(xx, yy))
    return out


def _avg_rgb(pixels):
    n = len(pixels)
    return tuple(int(round(sum(p[i] for p in pixels) / n)) for i in range(3))


def _near_identical(c1, c2, tol=8):
    """True if two colors are within `tol` on every channel — i.e. you probably
    sampled the same region twice (missed the foreground element)."""
    return max(abs(a - b) for a, b in zip(c1, c2)) <= tol


def cmd_sample(args) -> int:
    coords = args.coords
    if len(coords) < 2 or len(coords) % 2 != 0:
        print("ERROR: provide coordinate pairs: X Y [X2 Y2 ...]", file=sys.stderr)
        return 2
    try:
        w0, h0 = image_size(args.image)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    r = max(0, int(getattr(args, "box", 0) or 0))
    pts = []
    for i in range(0, len(coords), 2):
        x, y = coords[i], coords[i + 1]
        if args.norm:
            x, y = int(round(x * (w0 - 1))), int(round(y * (h0 - 1)))
        else:
            x, y = int(x), int(y)
        if not (0 <= x < w0 and 0 <= y < h0):
            print(f"ERROR: point ({x},{y}) out of bounds {w0}×{h0}", file=sys.stderr)
            return 1
        pts.append((x, y))
    try:
        max_row = min(h0 - 1, max(y for _, y in pts) + r)
        w, h, get_pixel = _decode_png(args.image, max_row=max_row)
    except Exception as e:
        print(f"ERROR: {e}\n(For JPEG/HEIC, state colors from the design or "
              f"convert: sips -s format png in.jpg --out out.png)", file=sys.stderr)
        return 1

    samples = []
    for (x, y) in pts:
        if r == 0:
            rgb = get_pixel(x, y)
            samples.append({"x": x, "y": y, "r": 0, "hex": _hex(rgb), "rgb": list(rgb)})
        else:
            win = _window_pixels(get_pixel, x, y, w, h, r)
            darkest = min(win, key=relative_luminance)
            lightest = max(win, key=relative_luminance)
            avg = _avg_rgb(win)
            samples.append({
                "x": x, "y": y, "r": r, "n": len(win),
                "hex": _hex(avg), "rgb": list(avg),
                "darkest": {"hex": _hex(darkest), "rgb": list(darkest)},
                "lightest": {"hex": _hex(lightest), "rgb": list(lightest)},
            })

    result = {"image": args.image, "size": [w, h], "samples": samples}

    if args.contrast and len(samples) == 2:
        if r == 0:
            fg, bg = tuple(samples[0]["rgb"]), tuple(samples[1]["rgb"])
            if _near_identical(fg, bg):
                result["warning"] = ("两点颜色几乎相同(各通道差≤8)——可能两点都采在背景上、"
                                     "未命中文字/前景。换坐标，或加 --box R 取邻域极值重采。")
        else:
            # Box mode: point 2's window = background; in point 1's window the glyph
            # stroke is the luminance extreme furthest from the background — works for
            # light-on-dark and dark-on-light alike, no manual coordinate hunting.
            bg = tuple(samples[1]["rgb"])
            bg_l = relative_luminance(bg)
            d = tuple(samples[0]["darkest"]["rgb"])
            l = tuple(samples[0]["lightest"]["rgb"])
            fg = d if abs(relative_luminance(d) - bg_l) >= abs(relative_luminance(l) - bg_l) else l
            if _near_identical(fg, bg):
                result["warning"] = ("第1点窗口里最极端的像素仍≈背景——文字可能不在窗口内/采偏。"
                                     "确认坐标落在字形上，或加大 --box R。")
        ratio = contrast_ratio(fg, bg)
        result["contrast"] = {"ratio": round(ratio, 2), "fg": _hex(fg), "bg": _hex(bg),
                              "AA_normal": ratio >= 4.5, "AA_large": ratio >= 3.0,
                              "picked": "box-extreme" if r else "points"}
    elif args.contrast:
        result["warning"] = "--contrast 需要正好 2 个点（前景、背景各一）。"

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for s in samples:
            if s["r"] == 0:
                print(f"({s['x']},{s['y']}): {s['hex']}  rgb{tuple(s['rgb'])}")
            else:
                print(f"({s['x']},{s['y']}) ±{s['r']}px[{s['n']}]: avg {s['hex']}  "
                      f"darkest {s['darkest']['hex']}  lightest {s['lightest']['hex']}")
        if "contrast" in result:
            c = result["contrast"]
            print(f"contrast: {c['ratio']}:1  fg {c['fg']} / bg {c['bg']} ({c['picked']})  "
                  f"AA normal {c['AA_normal']} / large {c['AA_large']}")
        if "warning" in result:
            print(f"⚠ {result['warning']}")
    return 0


# ------------------------------- contrast -------------------------------- #

def parse_color(s: str):
    s = s.strip()
    if s.startswith("#"):
        s = s[1:]
        if len(s) == 3:
            s = "".join(c * 2 for c in s)
        if len(s) != 6:
            raise ValueError(f"bad hex color: #{s}")
        return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))
    parts = [p.strip() for p in s.replace(";", ",").split(",")]
    if len(parts) != 3:
        raise ValueError(f"bad color: {s!r} (use #RRGGBB or r,g,b)")
    rgb = tuple(int(float(p)) for p in parts)
    if any(not 0 <= c <= 255 for c in rgb):
        raise ValueError(f"rgb out of range: {rgb}")
    return rgb


def relative_luminance(rgb) -> float:
    def lin(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(x) for x in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(c1, c2) -> float:
    l1, l2 = relative_luminance(c1), relative_luminance(c2)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def cmd_contrast(args) -> int:
    try:
        c1, c2 = parse_color(args.color1), parse_color(args.color2)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    ratio = contrast_ratio(c1, c2)
    aa_normal, aa_large = ratio >= 4.5, ratio >= 3.0
    aaa_normal, aaa_large = ratio >= 7.0, ratio >= 4.5
    result = {
        "color1": list(c1), "color2": list(c2), "ratio": round(ratio, 2),
        "AA": {"normal_text": aa_normal, "large_text": aa_large},
        "AAA": {"normal_text": aaa_normal, "large_text": aaa_large},
        "note": "WCAG AA stand-in for HIG contrast intent (no fixed HIG value).",
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        tgt = "large text" if args.large else "normal/body text"
        verdict = aa_large if args.large else aa_normal
        print(f"contrast ratio: {result['ratio']}:1")
        print(f"AA  ({tgt}): {'PASS' if verdict else 'FAIL'} "
              f"(need {'3.0' if args.large else '4.5'}:1)")
        print(f"AA  normal {aa_normal} / large {aa_large}  |  AAA normal {aaa_normal} / large {aaa_large}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Deterministic UI-image helpers.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    # --json is added per-subcommand so it can appear after the arguments
    # (the natural place), which a single top-level flag would not allow.
    def add_json(p):
        p.add_argument("--json", action="store_true", help="machine-readable output")

    d = sub.add_parser("dims", help="image size + device/scale/safe-area")
    d.add_argument("image")
    d.add_argument("--scale", type=int, default=None, help="force @Nx scale for px↔pt")
    d.add_argument("--platform", default=None, help="tailor safe-area note (macos/web/…)")
    add_json(d)

    s = sub.add_parser("sample", help="real sRGB color at pixel coords (PNG only)")
    s.add_argument("image")
    s.add_argument("coords", type=float, nargs="+", help="X Y [X2 Y2 ...]")
    s.add_argument("--norm", action="store_true", help="coords are 0–1 fractions")
    s.add_argument("--contrast", action="store_true", help="if 2 points, print WCAG ratio")
    s.add_argument("--box", type=int, default=0, metavar="R",
                   help="sample a (2R+1)² window per point (reports avg/darkest/lightest); "
                        "with --contrast picks the glyph stroke = luma extreme vs point 2's bg")
    add_json(s)

    c = sub.add_parser("contrast", help="WCAG contrast ratio between two colors")
    c.add_argument("color1")
    c.add_argument("color2")
    c.add_argument("--large", action="store_true", help="evaluate as large text (≥18pt/14pt bold)")
    add_json(c)

    args = ap.parse_args()
    return {"dims": cmd_dims, "sample": cmd_sample, "contrast": cmd_contrast}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
