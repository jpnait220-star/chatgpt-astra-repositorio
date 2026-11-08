from pathlib import Path
import zipfile,hashlib,json
root=Path(__file__).resolve().parent
version='1.0.2'
dist=root/'dist';dist.mkdir(exist_ok=True)
files={}
for p in (root/'src').rglob('*'):
    if p.is_file():files[str(p.relative_to(root/'src')).replace('\\','/')]=p.read_bytes()
files['LEIA-ME.md']=(root/'LEIA-ME.md').read_bytes()
files['preview-pastas.png']=(root/'preview-pastas.png').read_bytes()
for p in (root/'tests').glob('*.ps1'):files['tests/'+p.name]=p.read_bytes()
# Windows batch launchers: explicit CRLF. PowerShell scripts retain their UTF-8 BOM.
for name in list(files):
    if name.endswith('.cmd'):files[name]=files[name].decode('utf-8').replace('\r\n','\n').replace('\n','\r\n').encode('ascii')
files['ARQUIVOS-SHA256.txt']=''.join(hashlib.sha256(data).hexdigest()+'  '+name+'\n' for name,data in sorted(files.items())).encode('utf-8')
archive=dist/f'DuckPC-Windows11-{version}.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for name,data in sorted(files.items()):z.writestr(f'DuckPC-{version}/{name}',data)
(dist/f'DuckPC-Windows11-{version}-SHA256.txt').write_text(hashlib.sha256(archive.read_bytes()).hexdigest()+'  '+archive.name+'\n')
manifest={'version':version,'platform':'Windows 11 / Windows PowerShell 5.1 / .NET WinForms','tests':'50 checks: 36 core/file checks and 14 profile orchestration checks with Windows registry mocked; Windows UI/native behavior requires local validation','network_at_runtime':False,'automatic_startup':False,'admin_required_for_own_actions':False,'package':archive.name,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest()}
(dist/f'DuckPC-Windows11-{version}-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(archive.name,archive.stat().st_size,'bytes')
