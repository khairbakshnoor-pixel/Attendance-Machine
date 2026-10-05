"""Create a source-only showcase delivery without databases, models or secrets."""
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    "package.json", "package-lock.json", "tsconfig.json", "vite.config.ts",
    "vercel.json", "index.html", ".gitignore", ".vercelignore", "web/.env.example",
]


def main():
    target = ROOT / "facetrack-website.zip"
    files = [ROOT / name for name in FILES]
    files += sorted((ROOT / "web/src").glob("*"))
    files += sorted((ROOT / "public").glob("*"))
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            if path.is_file():
                archive.write(path, path.relative_to(ROOT))
        archive.write(ROOT / "WEBSITE.md", "README.md")
    with zipfile.ZipFile(target) as archive:
        assert archive.testzip() is None
        names = archive.namelist()
        assert all(not name.endswith((".db", ".onnx", ".env")) for name in names)
    print(f"Created {target.name}: {len(names)} source files, {target.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
