from pathlib import Path
import zipfile,json,hashlib,shutil
R=Path(__file__).resolve().parent;D=R/'dist';report=json.loads((R/'build-report.json').read_text())
readme=D/'DuckClientZ-beta.2.47-LEIA-ME.md';shutil.copy2(R/'LEIA-ME.md',readme)
combined=D/'DuckClientZ-beta.2.47-4-versoes.zip'
with zipfile.ZipFile(combined,'w',zipfile.ZIP_DEFLATED) as z:
 for row in report.values():z.write(D/row['file'],row['file'])
 z.write(readme,'LEIA-ME.md')
source=D/'DuckClientZ-beta.2.47-rendertop-fontes.zip'
with zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED) as z:
 files=[R/'build_revision.py',R/'run_checks.py',R/'sign_release.py',R/'package_release.py',R/'build-report.json',R/'LEIA-ME.md',R/'.gitignore',*R.glob('src/**/*.java'),*R.glob('tests/**/*.java')]
 for p in files:z.write(p,p.relative_to(R))
files=[D/row['file'] for row in report.values()]+[combined,source,readme,D/'DuckClientZ-update247.json']
(D/'DuckClientZ-beta.2.47-SHA256SUMS.txt').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n' for p in files))
for p in [combined,source]:assert zipfile.ZipFile(p).testzip() is None
print('Packaged 2.47: four games, sources, README, signed updater and hashes.')
