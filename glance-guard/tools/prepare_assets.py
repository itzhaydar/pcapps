"""Build-time only network access. Runtime never downloads anything."""
from pathlib import Path
import hashlib
import urllib.request
import zipfile
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parent.parent
URL="https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"

def main():
    assets=ROOT / "assets"; assets.mkdir(exist_ok=True)
    target=assets / "face_landmarker.task"
    if not target.exists():
        temporary=target.with_suffix(".download")
        try:
            with urllib.request.urlopen(URL,timeout=120) as source, temporary.open("wb") as destination:
                while chunk:=source.read(1024*1024):
                    destination.write(chunk)
            # The official versioned task is a ZIP model bundle; reject HTML/error responses.
            if temporary.stat().st_size < 1_000_000 or not zipfile.is_zipfile(temporary):
                raise RuntimeError("Invalid face model download")
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
    if not zipfile.is_zipfile(target):
        raise RuntimeError("Invalid face model; delete it and retry")
    digest=hashlib.sha256(target.read_bytes()).hexdigest()
    (assets / "face_landmarker.sha256").write_text(digest+"  face_landmarker.task\n")
    image=Image.new("RGBA",(256,256),(16,23,36,255))
    draw=ImageDraw.Draw(image)
    draw.rounded_rectangle((25,25,231,231),radius=50,fill=(35,66,75),outline=(142,232,194),width=9)
    draw.ellipse((58,88,198,168),outline=(142,232,194),width=12)
    draw.ellipse((108,108,148,148),fill=(142,232,194))
    image.save(assets / "icon.ico",sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])
    print("Prepared offline model and application icon. Model SHA-256:",digest)

if __name__ == "__main__":
    main()
