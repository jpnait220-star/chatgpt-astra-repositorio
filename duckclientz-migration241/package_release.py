from pathlib import Path
import json,zipfile,hashlib,shutil
R=Path(__file__).resolve().parent;D=R/'dist';report=json.loads((R/'build-report.json').read_text())
(D/'DuckClientZ-beta.2.41-LEIA-ME.md').write_text((R/'LEIA-ME.md').read_text())
combined=D/'DuckClientZ-beta.2.41-4-versoes.zip'
with zipfile.ZipFile(combined,'w',zipfile.ZIP_DEFLATED) as z:
 for e in report.values():z.write(D/e['file'],e['file'])
 z.write(R/'LEIA-ME.md','LEIA-ME.md')
source=D/'DuckClientZ-beta.2.41-migracao-fontes.zip'
with zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED) as z:
 for p in [R/'build_migration.py',R/'sign_release.py',R/'package_release.py',R/'LEIA-ME.md',R/'inspection.json',R/'build-report.json',R/'.gitignore',*R.glob('src/**/*.java'),*R.glob('tests/**/*.java')]:z.write(p,p.relative_to(R))
# Service configuration starts with no endpoint; activation is a separate signed revision.
shutil.copy2(D/'DuckClientZ-service241-pending.json',D/'DuckClientZ-service.json')
files=[D/e['file'] for e in report.values()]+[combined,source,D/'DuckClientZ-beta.2.41-LEIA-ME.md',D/'DuckClientZ-service.json',D/'DuckClientZ-update241-draft.json']
(D/'DuckClientZ-beta.2.41-SHA256SUMS.txt').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n' for p in files))
print('Packaged four mods, combined ZIP, source ZIP, signed pending config and draft updater. Live update channel not changed.')
