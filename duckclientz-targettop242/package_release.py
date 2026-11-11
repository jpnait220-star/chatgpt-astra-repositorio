from pathlib import Path
import zipfile,json,hashlib,shutil
R=Path(__file__).resolve().parent;D=R/'dist';report=json.loads((R/'build-report.json').read_text())
readme=D/'DuckClientZ-beta.2.42-LEIA-ME.md';shutil.copy2(R/'LEIA-ME.md',readme)
combined=D/'DuckClientZ-beta.2.42-4-versoes.zip'
with zipfile.ZipFile(combined,'w',zipfile.ZIP_DEFLATED) as z:
 for row in report.values():z.write(D/row['file'],row['file'])
 z.write(readme,'LEIA-ME.md')
source=D/'DuckClientZ-beta.2.42-targetlight-fontes.zip'
with zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED) as z:
 for p in [R/'build_targettop.py',R/'sign_release.py',R/'package_release.py',R/'build-report.json',R/'LEIA-ME.md',R/'.gitignore',*R.glob('src/**/*.java'),*R.glob('stubs/**/*.java'),*R.glob('tests/**/*.java')]:z.write(p,p.relative_to(R))
files=[D/row['file'] for row in report.values()]+[combined,source,readme,D/'DuckClientZ-update242.json']
(D/'DuckClientZ-beta.2.42-SHA256SUMS.txt').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n' for p in files))
print('Packaged 2.42 for all four games, source, README, signed updater and hashes.')
