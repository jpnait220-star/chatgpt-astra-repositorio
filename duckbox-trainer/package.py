from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import hashlib,json,shutil,subprocess,re
B=Path(__file__).parent;R=Path('/workspace/duckbox-publish');D=B/'dist';name='DuckBoxTrainer-1.21.4-0.3.23-alpha';jar=D/(name+'.jar')
assert jar.exists()
with ZipFile(jar) as z:
 assert z.testzip() is None
 meta=json.loads(z.read('fabric.mod.json'));assert meta['version']=='0.3.23-alpha' and meta['depends']['minecraft']=='1.21.4'
 classes=[n for n in z.namelist() if n.endswith('.class')];assert classes and all(n.startswith('dev/duckbox/') for n in classes)
validation='Duck Box Trainer0.3.23-alpha / Minecraft1.21.4\nSem execucao grafica de combate ou garantia de naturalidade/FPS.\nTestes usam bibliotecas/registries/bytecode Minecraft reais, sem substitutos de entidades.\nInclui TestServer vanilla sem janela: dano/locomocao, buffs/pop/resistencia, offhand,2macas, kit135HP, bau e mapa; guard pre-totem, torre real de la preta, limite de teia, armadilha60ticks e golpes nos pes; meshes/UVs dos4cosmeticos em coletor de vertices sem GPU. Nao e partida grafica nem testa todas dificuldades.\n\n'
for log in ['build.log','test.log','mixins-test.log','combat-test.log','mouse-patch.log','assets-test.log']:
 s=(B/log).read_text();assert not re.search(r'\[[^\]]*/ERROR\]',s),log;assert 'Traceback' not in s and 'Exception in thread' not in s and 'error:' not in s,log
 assert ({'build.log':'COMPILED','mouse-patch.log':'PATCHED'}.get(log,'PASS')) in s
 validation+=log+'\n'+s+'\n'
(D/'VALIDACAO.txt').write_text(validation)
paths=[p for folder in ['src','tests'] for p in (B/folder).rglob('*') if p.is_file()]+[B/n for n in ['README.md','LICENSE','CREDITOS-COSMETICOS.txt','.gitignore','bootstrap.py','build.py','make_map.py','test.py','test_mixins.py','test_combat.py','test_assets.py','patch_mouse.py','package.py']]
source=D/(name+'-fontes.zip')
with ZipFile(source,'w',ZIP_DEFLATED) as z:
 for p in paths:z.write(p,p.relative_to(B).as_posix())
pack=D/(name+'.zip')
with ZipFile(pack,'w',ZIP_DEFLATED) as z:
 z.write(jar,'mods/'+jar.name)
 z.write(D/'MouseTweaks-BETA17-sem-nohitdelay-mundo.jar','opcional/MouseTweaks-BETA17-sem-nohitdelay-mundo.jar')
 z.write(D/'MouseTweaks-BETA17-PATCH-VALIDACAO.json','opcional/MouseTweaks-BETA17-PATCH-VALIDACAO.json')
 for p in (D/'DuckBoxTreino').rglob('*'):
  if p.is_file():z.write(p,'saves/DuckBoxTreino/'+p.relative_to(D/'DuckBoxTreino').as_posix())
 z.write(B/'README.md','LEIA-ME.md');z.write(B/'CREDITOS-COSMETICOS.txt','CREDITOS-COSMETICOS.txt');z.write(B/'LICENSE','LICENSE.txt');z.write(D/'VALIDACAO.txt','VALIDACAO.txt');z.write(source,'fontes/'+source.name)
for p in [pack,source]:
 with ZipFile(p) as z:assert z.testzip() is None
files=[jar,pack,source,D/'MouseTweaks-BETA17-sem-nohitdelay-mundo.jar',D/'MouseTweaks-BETA17-PATCH-VALIDACAO.json'];sums=D/(name+'-SHA256SUMS.txt');sums.write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n' for p in files));files.append(sums)
manifest={}
for p in files:
 target=R/'downloads'/p.name;target.parent.mkdir(exist_ok=True)
 exists=subprocess.run(['git','cat-file','-e','HEAD:downloads/'+p.name],cwd=R,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0
 if exists:
  assert p.name.startswith('MouseTweaks-') and subprocess.check_output(['git','show','HEAD:downloads/'+p.name],cwd=R)==p.read_bytes(),'Published immutable name already exists: '+p.name
 shutil.copyfile(p,target);manifest[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
for p in paths:
 target=R/'duckbox-trainer'/p.relative_to(B);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
(B/'publication.json').write_text(json.dumps(manifest,indent=2)+'\n');print('PACKAGED',pack.name,pack.stat().st_size,'bytes;',len(classes),'mod classes;',len(files),'publication files')
