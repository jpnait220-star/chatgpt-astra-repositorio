from pathlib import Path
import zipfile,json,subprocess,hashlib,os,shutil
ROOT=Path(__file__).resolve().parent
TOOLS=Path('/workspace/duckclientz/tools')
FABRIC=Path('/workspace/duckclientz/tools/fabric-loader-0.16.10.jar')
VERSION='1.5.28-beta.2.41'
build=ROOT/'build';classes=build/'classes';classes.mkdir(parents=True,exist_ok=True)
asm=os.pathsep.join(str(TOOLS/x) for x in ['asm-9.7.1.jar','asm-tree-9.7.1.jar','asm-util-9.7.1.jar','asm-analysis-9.7.1.jar'])
subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-proc:none','-cp',asm,'-d',str(classes),str(ROOT/'src/Migration241Patch.java')],check=True)
common=build/'common';common.mkdir(exist_ok=True)
subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-proc:none','-source','17','-target','17','-cp',str(FABRIC)+os.pathsep+str(TOOLS/'gson.jar'),'-d',str(common),str(ROOT/'src/com/duckswords/connect/ServiceRoute241.java')],check=True)
dist=ROOT/'dist';dist.mkdir(exist_ok=True);report={}
allowed={'fabric.mod.json','com/duckswords/social/CosmeticSharing.class','com/duckswords/update/ClientUpdater229.class','com/duckswords/modules/CosmeticsOnline.class'}
for game in ['1.20.1','1.21.1','1.21.4','1.21.11']:
 source=ROOT/'originals'/f'DuckClientZ-{game}-1.5.28-beta.2.40.jar'
 patches=build/game/'patch';patches.mkdir(parents=True,exist_ok=True)
 subprocess.run(['java','-cp',str(classes)+os.pathsep+asm,'Migration241Patch',str(source),str(patches)],check=True)
 with zipfile.ZipFile(source) as z:
  original={n:z.read(n) for n in z.namelist()};metadata=json.loads(original['fabric.mod.json']);assert metadata['version']=='1.5.28-beta.2.40' and metadata['id']=='duckswords'
 replacements={p.relative_to(folder).as_posix():p.read_bytes() for folder in [patches,common] for p in folder.rglob('*.class')}
 metadata['version']=VERSION;replacements['fabric.mod.json']=(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n').encode()
 merged=original|replacements;target=dist/f'DuckClientZ-{game}-{VERSION}.jar'
 with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
  for name,data in merged.items():z.writestr(name,data)
 with zipfile.ZipFile(target) as z:
  assert z.testzip() is None
  changed=[name for name in original if original[name]!=z.read(name)]
  assert set(changed)==allowed,changed
  assert 'https://raw.githubusercontent.com' .encode() in z.read('com/duckswords/update/ClientUpdater229.class')
  assert b'https://duck-connect.vercel.app/updates' not in z.read('com/duckswords/update/ClientUpdater229.class')
  added=[name for name in z.namelist() if name not in original]
  assert added and all(n.startswith('com/duckswords/connect/ServiceRoute241') and n.endswith('.class') for n in added)
 report[game]={'file':target.name,'version':VERSION,'base':source.name,'base_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'size':target.stat().st_size,'changed_existing':changed,'added':added,'preserved_entries':len(original)-len(changed)}
 print('PRESERVED',game,report[game]['preserved_entries'],'entries; updated only metadata + three network/UI classes.')
(ROOT/'build-report.json').write_text(json.dumps(report,indent=2)+'\n')
