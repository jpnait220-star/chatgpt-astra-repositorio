from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import subprocess,os,json,hashlib
B=Path(__file__).parent;T=B/'tools';out=B/'build';out.mkdir(exist_ok=True)
subprocess.run(['python',str(B/'bootstrap.py')],check=True)
cp=[T/'minecraft-named.jar',T/'fabric-loader.jar',*T.glob('named/*.jar'),*T.glob('libraries/**/*.jar'),T/'mixin.jar']
if not cp[1].exists():
 import urllib.request
 cp[1]=T/'fabric-loader.jar'
 if not cp[1].exists():urllib.request.urlretrieve('https://maven.fabricmc.net/net/fabricmc/fabric-loader/0.16.10/fabric-loader-0.16.10.jar',cp[1])
sources=list((B/'src/main/java').rglob('*.java'));classes=out/'classes';classes.mkdir(exist_ok=True)
subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-Xmaxerrs','1000','-proc:none','-source','21','-target','21','-cp',os.pathsep.join(map(str,cp)),'-d',str(classes),*map(str,sources)],check=True)
with ZipFile(out/'named.jar','w',ZIP_DEFLATED) as z:
 for folder in [classes,B/'src/main/resources']:
  for p in folder.rglob('*'):
   if p.is_file():z.write(p,p.relative_to(folder).as_posix())
final=B/'dist/DuckBoxTrainer-1.21.1-0.3.31-alpha.jar';final.parent.mkdir(exist_ok=True);final.unlink(missing_ok=True)
subprocess.run(['java','-jar',str(T/'remapper.jar'),str(out/'named.jar'),str(final),str(T/'yarn.tiny'),'named','intermediary',str(T/'minecraft-named.jar')],check=True)
with ZipFile(final) as z:assert z.testzip() is None
print('COMPILED',final.name,final.stat().st_size,hashlib.sha256(final.read_bytes()).hexdigest())
