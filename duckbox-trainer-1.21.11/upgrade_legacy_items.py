from pathlib import Path
from zipfile import ZipFile
import subprocess,os
B=Path(__file__).parent;T=B/'tools';out=B/'build/item-migration';out.mkdir(parents=True,exist_ok=True)
cp=os.pathsep.join(map(str,[B/'build/named.jar',T/'minecraft-named.jar',T/'fabric-loader.jar',*T.glob('named/*.jar'),*T.glob('libraries/**/*.jar')]))
subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-proc:none','-cp',cp,'-d',str(out),str(B/'tests/UpgradeLegacyItems.java')],check=True)
with ZipFile(out/'named.jar','w') as z:z.write(out/'UpgradeLegacyItems.class','UpgradeLegacyItems.class')
(out/'runtime.jar').unlink(missing_ok=True)
subprocess.run(['java','-jar',str(T/'remapper.jar'),str(out/'named.jar'),str(out/'runtime.jar'),str(T/'yarn.tiny'),'named','intermediary',str(T/'minecraft-named.jar'),str(B/'build/named.jar')],check=True)
cp=os.pathsep.join(map(str,[out/'runtime.jar',B/'dist/DuckBoxTrainer-1.21.11-0.3.31-alpha.jar',T/'minecraft-intermediary.jar',T/'fabric-loader.jar',*T.glob('fabric-*.jar'),*T.glob('libraries/**/*.jar')]))
subprocess.run(['java','-Xmx1600m','-cp',cp,'UpgradeLegacyItems',str(B/'src/main/resources/duckbox/legacy-stock-items.json'),str(B/'item-upgrades.json')],check=True,timeout=120)
