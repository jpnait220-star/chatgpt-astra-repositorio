"""Package each native port without overwriting previously published release names."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import hashlib,json,shutil,re,subprocess
B=Path(__file__).parent;R=Path('/workspace/duckbox-publish')
manifest=json.loads((B/'publication.json').read_text())
for v in ['1.21.1','1.21.11','1.20.1']:
 root=Path('/workspace/duckbox-trainer-'+v);D=root/'dist';name='DuckBoxTrainer-'+v+'-0.3.30-alpha';jar=D/(name+'.jar')
 validation='DuckBoxTrainer0.3.30-alpha / Minecraft'+v+'\nBibliotecas nativas; testes sem janela grafica. Nao e partida grafica nem garantia de FPS/naturalidade.\n'
 for log in ['build.log','mixins-test.log','combat-test.log','mesh-test.log']:
  text=(root/log).read_text();assert not any(marker in text for marker in ['Traceback','Exception in thread','AssertionError','error:']),log+v
  assert not re.search(r'\[[^\]]*/ERROR\]',text),log+v
  assert ('COMPILED' if log=='build.log' else 'PASS') in text
  validation+='\n'+log+'\n'+text
 assert 'PASS PORT SERVER SMOKE' in (root/'combat-test.log').read_text()
 assert 'PASS ACTUAL WOVEN CRITICAL' in (root/'combat-test.log').read_text()
 with ZipFile(jar) as z:
  assert z.testzip() is None
  meta=json.loads(z.read('fabric.mod.json'));assert meta['version']=='0.3.30-alpha' and meta['depends']['minecraft']==v
  for n in z.namelist():
   if n.endswith('.class'):
    assert n.startswith('dev/duckbox/')
    assert int.from_bytes(z.read(n)[6:8],'big') <= (61 if v=='1.20.1' else 65)
 (D/'VALIDACAO.txt').write_text(validation)
 folders=['src','tests','art'];paths=[p for folder in folders for p in (root/folder).rglob('*') if p.is_file()]
 paths += [root/n for n in ['bootstrap.py','build.py','test_mixins.py','test_combat.py','test_meshes.py','README.md','LICENSE','CREDITOS-COSMETICOS.txt','world-conversion.json']]
 source=D/(name+'-fontes.zip')
 with ZipFile(source,'w',ZIP_DEFLATED) as z:
  for p in paths:z.write(p,p.relative_to(root).as_posix())
 pack=D/(name+'.zip')
 with ZipFile(pack,'w',ZIP_DEFLATED) as z:
  z.write(jar,'mods/'+jar.name)
  for p in (D/'DuckBoxTreino').rglob('*'):
   if p.is_file():z.write(p,'saves/DuckBoxTreino/'+p.relative_to(D/'DuckBoxTreino').as_posix())
  for n,out in [('README.md','LEIA-ME.md'),('LICENSE','LICENSE.txt'),('CREDITOS-COSMETICOS.txt','CREDITOS-COSMETICOS.txt')]:z.write(root/n,out)
  z.write(D/'VALIDACAO.txt','VALIDACAO.txt');z.write(source,'fontes/'+source.name)
 files=[jar,pack,source];sums=D/(name+'-SHA256SUMS.txt');sums.write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n' for p in files));files.append(sums)
 for p in files:
  assert subprocess.run(['git','cat-file','-e','HEAD:downloads/'+p.name],cwd=R,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode!=0,'Immutable release already published'
  shutil.copyfile(p,R/'downloads'/p.name);manifest[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
 for p in paths:
  dest=R/('duckbox-trainer-'+v)/p.relative_to(root);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
 print('PACKAGED',v,pack.stat().st_size,'bytes',flush=True)
(B/'publication-all.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('READY',len(manifest),'public release files')
