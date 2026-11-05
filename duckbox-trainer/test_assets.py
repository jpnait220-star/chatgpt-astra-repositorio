"""Verify the corrected user pack and stable panel identifiers without changing PNG pixels."""
from pathlib import Path
from zipfile import ZipFile
import hashlib,struct,sys,json
B=Path(__file__).parent
assert len(sys.argv)==2,'Usage: python test_assets.py corrected-pack.zip'
with ZipFile(sys.argv[1]) as original, ZipFile(B/'dist/DuckBoxTrainer-1.21.4-0.3.25-alpha.jar') as mod:
 mapping={n:Path(n).stem for n in original.namelist() if n.startswith(('Icones/','Kits/')) and n.endswith('.png')}
 for row in range(1,3):
  for col in range(1,4):mapping[f'START_3x2/start_linha{row}_coluna{col}.png']=f'start_{(row-1)*3+col}_'+('top_' if row==1 else 'bottom_')+['left','center','right'][col-1]
 mapping['START_3x2/start_completo.png']='start_sheet'
 assert len(mapping)==24
 for src,name in mapping.items():
  expected=original.read(src)
  assert mod.read(f'assets/duckbox/textures/map_panels/{name}.png')==expected,src
  model=json.loads(mod.read(f'assets/duckbox/items/painel_{name}.json'))
  assert model['model']['model']['texture']==f'duckbox:textures/map_panels/{name}.png',name
  width,height=struct.unpack('>II',expected[16:24]);assert width<=1536 and height<=1536
 print('PASS CORRECTED MAP ASSETS:24 PNGs byte-identical to uploaded pack; all24 item models use their own texture; stable panel IDs')
