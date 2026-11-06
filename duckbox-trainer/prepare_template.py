"""Bundle the user's built map, omitting personal player data and stale locks."""
from pathlib import Path,PurePosixPath
from zipfile import ZipFile,ZIP_DEFLATED
import sys,io,json,shutil
B=Path(__file__).parent
sys.path.insert(0,str(B/'tools/python'))
import nbtlib
source=Path(sys.argv[1]) if len(sys.argv)>1 else None
if source is None:raise SystemExit('Usage: python prepare_template.py DuckBoxTreino.zip')
root=B/'dist/DuckBoxTreino'
if root.exists():shutil.rmtree(root)
root.mkdir(parents=True)
with ZipFile(source) as archive:
 for item in archive.infolist():
  p=PurePosixPath(item.filename)
  if not p.parts or p.parts[0]!='DuckBoxTreino' or '..' in p.parts or item.is_dir():continue
  parts=p.parts[1:]
  if not parts or parts[0] in ['playerdata','advancements','stats'] or parts[-1] in ['session.lock','level.dat_old']:continue
  dest=root.joinpath(*parts);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(archive.read(item))
config=json.loads((root/'duckbox-training.json').read_text())
config['options'].update(customMap=True,autoBuildOnJoin=False,initialized=True,built=True)
config['backups']={}
(root/'duckbox-training.json').write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n')
level=nbtlib.load(root/'level.dat');data=level['Data'];data.pop('Player',None)
data['LevelName']=nbtlib.String('Mundo de Duckzin')
data['allowCommands']=nbtlib.Byte(1)
data['GameType']=nbtlib.Int(2)
# The upload declares three external datapacks but contains none of their files.
# Do not leave broken enabled-pack references that prevent the built-in world loading.
if 'DataPacks' in data:
 data['DataPacks']['Enabled']=nbtlib.List[nbtlib.String]([n for n in data['DataPacks']['Enabled'] if not str(n).startswith('file/') or (root/'datapacks'/str(n)[5:]).exists()])
for field,key in [('SpawnX','spawnX'),('SpawnY','spawnY'),('SpawnZ','spawnZ')]:data[field]=nbtlib.Int(int(config['options'].get(key,{'spawnX':-146,'spawnY':65,'spawnZ':93}[key])))
data['GameRules']['spawnRadius']=nbtlib.String('0')
level.save(root/'level.dat',gzipped=True)
(root/'LEIA-ME.txt').write_text('Mundo de Duckzin: mapa e perfis enviados pelo autor, preservados. Use Fabric1.21.4, FabricAPI e DuckBoxTrainer. O gerador automatico da arena foi desativado neste mapa.\n')
out=B/'src/main/resources/assets/duckbox/world/duckzin.zip';out.parent.mkdir(parents=True,exist_ok=True)
with ZipFile(out,'w',ZIP_DEFLATED) as z:
 for p in sorted(root.rglob('*')):
  if p.is_file():z.write(p,p.relative_to(root).as_posix())
print('PREPARED USER WORLD',out.stat().st_size,'bytes;',len(list(root.rglob('*.mca'))),'region files; no personal player data')
