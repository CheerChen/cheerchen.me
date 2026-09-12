#!/usr/bin/env python3
"""Check front matter consistency and image references in Hugo content.

Runs two checks:
1. Front matter: tags/categories/date/cover/images/draft must be identical
   across all language versions (index.zh.md, index.ja.md, index.en.md)
   of the same post bundle.
2. Image references: no bare ![](file.png) for bundle-relative files;
   all shortcode src files must exist in the bundle.

Usage:
    python3 scripts/check-content.py
    python3 scripts/check-content.py --frontmatter   # only front matter check
    python3 scripts/check-content.py --images        # only image check
"""
import argparse
import re
import sys
import tomllib
from pathlib import Path

CONTENT_DIR = Path("content/posts")
SHARED_FIELDS = ["tags", "categories", "date", "cover", "images", "draft"]
BUNDLE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".mp4", ".webm", ".mov"}
BARE_IMG_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
FIGURE_RE = re.compile(r"{{<\s*(figure|vfigure)\s+([^>]+)>}}")
SHORTCODE_SRC_RE = re.compile(r'src="([^"]+)"')


def extract_front_matter(filepath: Path) -> dict | None:
    """Extract TOML front matter from a Hugo content file (+++ delimited)."""
    text = filepath.read_text(encoding="utf-8")
    if not text.startswith("+++"):
        return None
    end = text.find("+++", 3)
    if end == -1:
        return None
    toml_text = text[3:end].strip()
    return tomllib.loads(toml_text)


def check_front_matter() -> list[str]:
    """Check that all language versions of a post have consistent front matter."""
    errors: list[str] = []
    for bundle in sorted(CONTENT_DIR.iterdir()):
        if not bundle.is_dir():
            continue
        md_files = sorted(bundle.glob("index.*.md"))
        if len(md_files) < 2:
            continue
        front_matters: dict[str, dict] = {}
        for f in md_files:
            lang = f.stem.replace("index.", "")
            fm = extract_front_matter(f)
            if fm is None:
                errors.append(f"{f.name}: could not parse front matter")
                continue
            front_matters[lang] = fm
        if len(front_matters) < 2:
            continue
        ref_lang = list(front_matters.keys())[0]
        ref = front_matters[ref_lang]
        for lang, fm in front_matters.items():
            if lang == ref_lang:
                continue
            for field in SHARED_FIELDS:
                if field in ref or field in fm:
                    ref_val = ref.get(field)
                    cur_val = fm.get(field)
                    if ref_val != cur_val:
                        errors.append(
                            f"{bundle.name}: '{field}' mismatch — "
                            f"{ref_lang}={ref_val!r} vs {lang}={cur_val!r}"
                        )
    return errors


def check_images() -> list[str]:
    """Check image references in Hugo content files."""
    errors: list[str] = []
    for md in sorted(CONTENT_DIR.rglob("index.*.md")):
        text = md.read_text(encoding="utf-8")
        bundle_dir = md.parent
        # Check for bare ![](file.png) that should use shortcodes
        for match in BARE_IMG_RE.finditer(text):
            _alt, src = match.groups()
            if src.startswith(("http", "/")):
                continue
            ext = Path(src).suffix.lower()
            if ext in BUNDLE_EXTS:
                errors.append(
                    f'{md}: bare ![]({src}) — use {{{{< figure src="{src}" ... >}}}} shortcode instead'
                )
        # Check shortcode src references exist in bundle
        for match in FIGURE_RE.finditer(text):
            shortcode = match.group(1)
            attrs = match.group(2)
            src_match = SHORTCODE_SRC_RE.search(attrs)
            if not src_match:
                errors.append(f"{md}: {shortcode} shortcode missing src attribute")
                continue
            src = src_match.group(1)
            if src.startswith(("http", "/")):
                continue
            if not (bundle_dir / src).exists():
                errors.append(f'{md}: {shortcode} src="{src}" — file not found in bundle')
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Check Hugo content")
    parser.add_argument("--frontmatter", action="store_true", help="Only run front matter check")
    parser.add_argument("--images", action="store_true", help="Only run image reference check")
    args = parser.parse_args()

    run_fm = not args.images
    run_img = not args.frontmatter

    all_errors: list[str] = []
    if run_fm:
        fm_errors = check_front_matter()
        if fm_errors:
            print("❌ Front matter inconsistencies:\n")
            for e in fm_errors:
                print(f"  {e}")
            all_errors.extend(fm_errors)
        else:
            print("✅ Front matter is consistent across language versions.")

    if run_img:
        img_errors = check_images()
        if img_errors:
            print("\n❌ Image reference issues:\n")
            for e in img_errors:
                print(f"  {e}")
            all_errors.extend(img_errors)
        else:
            print("✅ All image references are valid.")

    if all_errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
