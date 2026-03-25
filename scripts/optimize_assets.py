import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def _which(name: str) -> str | None:
    return shutil.which(name)


def _format_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.1f}{unit}" if unit != "B" else f"{n}{unit}"
        n /= 1024
    return f"{n:.1f}GB"


def _safe_replace(src: Path, dst: Path) -> None:
    tmp = dst.with_suffix(dst.suffix + ".tmp")
    if tmp.exists():
        tmp.unlink()
    shutil.move(str(src), str(tmp))
    if dst.exists():
        dst.unlink()
    shutil.move(str(tmp), str(dst))


def optimize_png(path: Path, *, dry_run: bool) -> tuple[int, int, str]:
    try:
        from PIL import Image
    except Exception:
        return (path.stat().st_size, path.stat().st_size, "Pillow not installed")

    before = path.stat().st_size
    if dry_run:
        return (before, before, "dry-run")

    try:
        with Image.open(path) as im:
            if im.format != "PNG":
                return (before, before, "skip")

            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tf:
                tmp_path = Path(tf.name)

            save_kwargs = {"optimize": True}
            if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
                save_kwargs["compress_level"] = 9
            else:
                save_kwargs["compress_level"] = 9

            im.save(tmp_path, format="PNG", **save_kwargs)

        after = tmp_path.stat().st_size
        if after < before:
            _safe_replace(tmp_path, path)
            return (before, after, "ok")
        tmp_path.unlink(missing_ok=True)
        return (before, before, "no-gain")
    except Exception as e:
        return (before, before, f"error: {e}")


def optimize_pngs_with_oxipng(root: Path, *, dry_run: bool) -> tuple[int, int, str]:
    oxipng = _which("oxipng")
    if not oxipng:
        return (0, 0, "oxipng not found")

    pngs = list(iter_files(root, {".png"}))
    before = sum(p.stat().st_size for p in pngs)
    if dry_run:
        return (before, before, "dry-run")

    cmd = [
        oxipng,
        "-o",
        "6",
        "--strip",
        "safe",
        "-r",
        str(root),
    ]
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if p.returncode != 0:
            after = sum(x.stat().st_size for x in pngs)
            return (before, after, p.stderr.strip()[-4000:])
        after = sum(x.stat().st_size for x in pngs)
        return (before, after, "ok")
    except Exception as e:
        after = sum(x.stat().st_size for x in pngs)
        return (before, after, str(e))


def _ffmpeg_encode_mp3(src: Path, dst: Path, bitrate_k: int) -> tuple[bool, str]:
    ffmpeg = _which("ffmpeg")
    if not ffmpeg:
        return (False, "ffmpeg not found")

    cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(src),
        "-vn",
        "-map_metadata",
        "0",
        "-ac",
        "2",
        "-ar",
        "44100",
        "-b:a",
        f"{bitrate_k}k",
        str(dst),
    ]

    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if p.returncode != 0:
            return (False, p.stderr.strip()[-4000:])
        return (True, "ok")
    except Exception as e:
        return (False, str(e))


def optimize_mp3(path: Path, *, bitrate_k: int, dry_run: bool) -> tuple[int, int, str]:
    before = path.stat().st_size
    if dry_run:
        return (before, before, "dry-run")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tf:
        tmp_path = Path(tf.name)

    ok, msg = _ffmpeg_encode_mp3(path, tmp_path, bitrate_k)
    if not ok:
        tmp_path.unlink(missing_ok=True)
        return (before, before, msg)

    after = tmp_path.stat().st_size
    if after < before:
        _safe_replace(tmp_path, path)
        return (before, after, "ok")

    tmp_path.unlink(missing_ok=True)
    return (before, before, "no-gain")


def iter_files(root: Path, exts: set[str]):
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in exts:
            yield p


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="assets")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--png", action="store_true")
    parser.add_argument("--audio", action="store_true")
    parser.add_argument("--music-bitrate", type=int, default=128)
    parser.add_argument("--sfx-bitrate", type=int, default=96)
    args = parser.parse_args(argv)

    root = Path(args.root)
    if not root.exists():
        print(f"Root not found: {root}")
        return 2

    do_png = args.png or (not args.png and not args.audio)
    do_audio = args.audio or (not args.png and not args.audio)

    total_before = 0
    total_after = 0

    if do_png:
        ox_b, ox_a, ox_status = optimize_pngs_with_oxipng(root, dry_run=args.dry_run)
        if ox_status == "ok" or ox_status == "dry-run":
            total_before += ox_b
            total_after += ox_a
            print(f"PNG oxipng {ox_status}: {_format_bytes(ox_b)} -> {_format_bytes(ox_a)}")
        else:
            for p in iter_files(root, {".png"}):
                b, a, status = optimize_png(p, dry_run=args.dry_run)
                total_before += b
                total_after += a
                if status not in ("no-gain", "skip"):
                    print(f"PNG {status}: {p} {_format_bytes(b)} -> {_format_bytes(a)}")

    if do_audio:
        for p in iter_files(root, {".mp3"}):
            rel = str(p).replace("\\", "/")
            if "/assets/music/" in f"/{rel}".lower().replace("\\", "/"):
                bitrate = args.music_bitrate
            elif "/assets/sounds/" in f"/{rel}".lower().replace("\\", "/"):
                bitrate = args.sfx_bitrate
            else:
                bitrate = args.music_bitrate

            b, a, status = optimize_mp3(p, bitrate_k=bitrate, dry_run=args.dry_run)
            total_before += b
            total_after += a
            if status not in ("no-gain",):
                print(f"MP3 {status}: {p} {_format_bytes(b)} -> {_format_bytes(a)}")

    print(f"Total: {_format_bytes(total_before)} -> {_format_bytes(total_after)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
