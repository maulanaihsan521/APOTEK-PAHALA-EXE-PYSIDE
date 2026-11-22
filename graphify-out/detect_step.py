import json
from pathlib import Path

from graphify.detect import detect
from graphify.paths import out_path
from graphify.watch import _read_build_excludes, _read_build_gitignore

INPUT_PATH = Path(Path("graphify-out/.graphify_root").read_text(encoding="utf-8-sig").strip())
result = detect(
    Path(INPUT_PATH),
    extra_excludes=_read_build_excludes(out_path()),
    gitignore=_read_build_gitignore(out_path()),
)
Path("graphify-out/.graphify_detect.json").write_text(
    json.dumps(result, ensure_ascii=False), encoding="utf-8"
)
print(f'Detected {result["total_files"]} files, ~{result.get("total_words", 0):,} words')
for key, files in result.get("files", {}).items():
    if files:
        print(f"  {key}: {len(files)}")
if result.get("skipped_sensitive"):
    print(f'Skipped sensitive: {len(result["skipped_sensitive"])}')
    for name in result["skipped_sensitive"][:20]:
        print("   ", name)
