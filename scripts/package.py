"""Build a dependency-free, reproducible unpacked-extension ZIP."""
from pathlib import Path
import zipfile
import json

root = Path(__file__).resolve().parents[1]
files = ['manifest.json', 'background.js', 'core.js', 'dashboard.html', 'dashboard.css', 'dashboard.js', 'motion.js', 'README.md', 'INSTALAR-NO-OPERA.txt']
files += [str(path.relative_to(root)) for path in sorted((root / 'icons').glob('*')) if path.is_file()]
version = json.loads((root / 'manifest.json').read_text())['version']
target = root / 'artifacts' / f'DuckCleans-{version}.zip'
target.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
    for filename in files:
        info = zipfile.ZipInfo(filename, date_time=(2026, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o644 << 16
        archive.writestr(info, (root / filename).read_bytes())
print(target)
