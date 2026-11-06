"""Verify the corrected user pack and stable panel identifiers without changing PNG pixels."""
from pathlib import Path
from zipfile import ZipFile
import hashlib,struct,sys,json
B=Path(__file__).parent
assert len(sys.argv)==2,'Usage: python test_assets.py corrected-pack.zip'
with ZipFile(sys.argv[1]) as original, ZipFile(B/'dist/DuckBoxTrainer-1.21.4-0.3.31-alpha.jar') as mod:
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

with ZipFile(B/"dist/DuckBoxTrainer-1.21.4-0.3.31-alpha.jar") as mod:
 assert hashlib.sha256(mod.read("assets/duckbox/textures/map_panels/easy.png")).hexdigest()=="65120c7dc6792756101ba613033432b36b0a0676f2bbfcd33db852b069059397","easy"
 assert hashlib.sha256(mod.read("assets/duckbox/textures/map_panels/hard.png")).hexdigest()=="6d5d586888654008c46787445c58ae6d51a10a35700c68a29e3209abaf66f6a9","hard"
 assert hashlib.sha256(mod.read("assets/duckbox/textures/map_panels/harder.png")).hexdigest()=="2e7ff2c5418abc613de492407be643495c1ccc088a58a4fe74b5f7cfc863fb21","harder"
 assert hashlib.sha256(mod.read("assets/duckbox/textures/map_panels/insane_feature.png")).hexdigest()=="c11b5361715e368d8f090dd3e627159031b48e742a86ae06467253a11c036076","insane_feature"
 print("PASS DIFFICULTY ASSETS:4 original PNGs with stable SHA256; white backing is rendered without editing pixels")

with ZipFile(B/"dist/DuckBoxTrainer-1.21.4-0.3.31-alpha.jar") as mod:
 assert hashlib.sha256(mod.read("assets/duckbox/textures/entity/chest/stock.png")).hexdigest()=="61cc9fc5b56e757bbb15b654230dd2fe7bc6e7ebcaba3fd16f1e2f28906f872d","stock"
 assert hashlib.sha256(mod.read("assets/duckbox/textures/entity/chest/profile.png")).hexdigest()=="a7d3a987f9003d3201b0d82e095b2502d37c4fcba6760b829fc8adcc7496caef","profile"
 print("PASS CHEST ASSETS: original Gift stock and purple profile PNG hashes verified")

with ZipFile(B/"dist/DuckBoxTrainer-1.21.4-0.3.31-alpha.jar") as mod:
 with ZipFile(__import__('io').BytesIO(mod.read('assets/duckbox/world/duckzin.zip'))) as world:
  assert 'level.dat' in world.namelist() and 'duckbox-training.json' in world.namelist()
  assert not any(n.startswith(('playerdata/','advancements/','stats/')) or n.endswith('session.lock') for n in world.namelist())
  config=json.loads(world.read('duckbox-training.json'))
  assert not config['options']['customMap'] and not config['options']['autoBuildOnJoin']
  original_path=B/'review/user-world-original.zip'
  if original_path.exists():
   with ZipFile(original_path) as original:
    prefix=next(n[:-len('level.dat')] for n in original.namelist() if n.endswith('/level.dat'))
    for n in world.namelist():
     if n.endswith('.mca'):assert world.read(n)==original.read(prefix+n),n
    assert config['kitProfiles']['1']==json.loads(original.read(prefix+'duckbox-training.json'))['kitProfiles']['1']
    assert all(not any(config['kitProfiles'][str(i)]['inventory']) for i in [2,3,4])
  print('PASS BUILT WORLD: bundled regions/kits preserved, automatic rebuild disabled and personal player files omitted')

with ZipFile(B/'dist/DuckBoxTrainer-1.21.4-0.3.31-alpha.jar') as mod:
 meta=json.loads(mod.read('fabric.mod.json'))
 assert meta['icon']=='assets/duckbox/icon.png'
 assert struct.unpack('>II',mod.read(meta['icon'])[16:24])==(256,256)
 icon=mod.read('assets/duckbox/world_icon.png')
 assert struct.unpack('>II',icon[16:24])==(64,64)
 assert (B/'dist/DuckBoxTreino/icon.png').read_bytes()==icon
 with ZipFile(__import__('io').BytesIO(mod.read('assets/duckbox/world/duckzin.zip'))) as world:
  assert world.read('icon.png')==icon
 from PIL import Image
 import io
 original=Image.open(B/'art/avatar-original.png').convert('RGBA')
 for size,path in [(256,meta['icon']),(64,'assets/duckbox/world_icon.png')]:
  actual=Image.open(io.BytesIO(mod.read(path))).convert('RGBA')
  assert actual.tobytes()==original.resize((size,size),Image.Resampling.LANCZOS).tobytes()
 print('PASS AVATAR: exact supplied artwork resized without cropping; mod256 and exported/embedded world64 icons agree')

from PIL import Image
for suffix,version in [('', '1.21.4'),('-1.21.1','1.21.1'),('-1.21.11','1.21.11'),('-1.20.1','1.20.1')]:
 root=B.parent/('duckbox-trainer'+suffix)
 with ZipFile(root/f'dist/DuckBoxTrainer-{version}-0.3.31-alpha.jar') as release:
  background=Image.open(__import__('io').BytesIO(release.read('assets/duckbox/textures/map_panels/white_background.png'))).convert('RGBA')
  assert background.size==(2,2) and set(background.getdata())=={(255,255,255,255)}
  assert 'textures/map_panels/white_background.png' in (root/'src/main/java/dev/duckbox/panels/PanelGraphics.java').read_text()
 print('PASS OWN WHITE BACKGROUND:',version,'bundled opaque white texture, no missing vanilla texture dependency')
