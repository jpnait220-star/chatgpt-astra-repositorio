"""Check the original uploaded PNG bytes against the mod JAR without editing images."""
from pathlib import Path
from zipfile import ZipFile
import hashlib,struct,sys
B=Path(__file__).parent
jar=B/'dist/DuckBoxTrainer-1.21.4-0.3.23-alpha.jar'
assert len(sys.argv)==3, 'Usage: python test_assets.py kits.zip textures.zip'
count=0
with ZipFile(jar) as mod:
 for archive in sys.argv[1:]:
  with ZipFile(archive) as original:
   for name in original.namelist():
    if not name.endswith('.png'):continue
    expected=original.read(name)
    actual=mod.read('assets/duckbox/textures/map_panels/'+Path(name).name)
    assert hashlib.sha256(expected).digest()==hashlib.sha256(actual).digest(),name
    width,height=struct.unpack('>II',expected[16:24])
    assert width<=1536 and height<=1254,(name,width,height)
    count+=1
 assert count==19,count
print('PASS ORIGINAL MAP ASSETS:',count,'PNGs byte-identical to both uploaded ZIPs; dimensions at most1536x1254; no pixel edits')
