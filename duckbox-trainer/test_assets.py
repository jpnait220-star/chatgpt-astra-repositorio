"""Verify the corrected user pack and stable panel identifiers without changing PNG pixels."""
from pathlib import Path
from zipfile import ZipFile
import hashlib,struct,sys,json
B=Path(__file__).parent
assert len(sys.argv)==2,'Usage: python test_assets.py corrected-pack.zip'
with ZipFile(sys.argv[1]) as original, ZipFile(B/'dist/DuckBoxTrainer-1.21.4-0.3.27-alpha.jar') as mod:
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

with ZipFile(B/"dist/DuckBoxTrainer-1.21.4-0.3.27-alpha.jar") as mod:
 assert hashlib.sha256(mod.read("assets/duckbox/textures/map_panels/easy.png")).hexdigest()=="65120c7dc6792756101ba613033432b36b0a0676f2bbfcd33db852b069059397","easy"
 assert hashlib.sha256(mod.read("assets/duckbox/textures/map_panels/hard.png")).hexdigest()=="6d5d586888654008c46787445c58ae6d51a10a35700c68a29e3209abaf66f6a9","hard"
 assert hashlib.sha256(mod.read("assets/duckbox/textures/map_panels/harder.png")).hexdigest()=="2e7ff2c5418abc613de492407be643495c1ccc088a58a4fe74b5f7cfc863fb21","harder"
 assert hashlib.sha256(mod.read("assets/duckbox/textures/map_panels/insane_feature.png")).hexdigest()=="c11b5361715e368d8f090dd3e627159031b48e742a86ae06467253a11c036076","insane_feature"
 print("PASS DIFFICULTY ASSETS:4 original PNGs with stable SHA256; white backing is rendered without editing pixels")

with ZipFile(B/"dist/DuckBoxTrainer-1.21.4-0.3.27-alpha.jar") as mod:
 assert hashlib.sha256(mod.read("assets/duckbox/textures/entity/chest/stock.png")).hexdigest()=="f73faa3d2d66e19c3304628edb02dc307f14836d9ada538223932e352694bf2d","stock"
 assert hashlib.sha256(mod.read("assets/duckbox/textures/entity/chest/profile.png")).hexdigest()=="a7d3a987f9003d3201b0d82e095b2502d37c4fcba6760b829fc8adcc7496caef","profile"
 print("PASS CHEST ASSETS: original Pokemon stock and purple profile PNG hashes verified")
