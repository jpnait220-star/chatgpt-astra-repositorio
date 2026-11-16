"""Package an Electron win32 build and the matching server into release downloads."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import hashlib
import shutil
import struct

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'release-dist'
APP = ROOT / 'desktop-dist' / 'LAST ZONE-win32-x64'
OUT.mkdir(exist_ok=True)
pe = (APP / 'LAST ZONE.exe').read_bytes()
pe_offset = struct.unpack_from('<I', pe, 0x3c)[0]
assert pe[:2] == b'MZ' and pe[pe_offset:pe_offset+4] == b'PE\0\0'
assert struct.unpack_from('<H', pe, pe_offset+4)[0] == 0x8664
for name in ['COMECE-AQUI.txt', 'ALTARE-GUIA.txt', 'AUDIO-CREDITS.txt', 'VALIDACAO-DUO.txt']:
    shutil.copyfile(ROOT / name, APP / name)
with ZipFile(OUT / 'LastZone-v6-Windows.zip', 'w', ZIP_DEFLATED, compresslevel=1) as archive:
    for path in sorted(APP.rglob('*')):
        if path.is_file():
            archive.write(path, path.relative_to(APP.parent))
with ZipFile(OUT / 'LastZone-v6-Servidor.zip', 'w', ZIP_DEFLATED) as archive:
    for name in ['server.mjs', 'LAST ZONE Duo.html', 'package.json', 'server-config.json', 'ALTARE-GUIA.txt', 'AUDIO-CREDITS.txt', 'Dockerfile']:
        archive.write(ROOT / name, name)
shutil.copyfile(ROOT / 'LAST ZONE Duo.html', OUT / 'LastZone-v6.html')
shutil.copyfile(ROOT / 'ALTARE-GUIA.txt', OUT / 'Guia-Altare.txt')
for name in ['verdant-town.png', 'verdant-aerial.png']:
    if (ROOT / name).is_file():
        shutil.copyfile(ROOT / name, OUT / name)
for path in OUT.glob('*.zip'):
    with ZipFile(path) as archive:
        assert archive.testzip() is None, path.name
checksums = [f'{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}' for path in sorted(OUT.iterdir()) if path.name != 'SHA256SUMS.txt']
(OUT / 'SHA256SUMS.txt').write_text('\n'.join(checksums) + '\n')
print('\n'.join(checksums))
