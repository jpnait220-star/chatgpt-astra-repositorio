from pathlib import Path
import os,subprocess,shutil
B=Path(__file__).parent;T=B/'tools';out=B/'build/combat-tests'
world=out/'worlds-low-web';shutil.rmtree(world,ignore_errors=True)
cp=os.pathsep.join(map(str,[B/'build/web-woven.jar',B/'build/critical-woven.jar',out/'runtime.jar',B/'dist/DuckBoxTrainer-1.21.11-0.3.31-alpha.jar',T/'minecraft-intermediary.jar',T/'fabric-loader.jar',*T.glob('fabric-*.jar'),*T.glob('libraries/**/*.jar'),T/'mixin.jar']))
subprocess.run(['java','-Xmx1800m','-Xverify:all','-Dduckbox.lowtraps=true','-cp',cp,'CombatServerTest',str(world),str(B/'src/main/resources/assets/duckbox/world/duckzin.zip')],cwd=out,check=True,timeout=180)
