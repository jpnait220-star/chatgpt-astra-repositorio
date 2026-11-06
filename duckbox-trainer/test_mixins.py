from pathlib import Path
import os,subprocess
B=Path(__file__).parent;T=B/'tools';out=B/'build/mixin-test';out.mkdir(exist_ok=True)
service=out/'META-INF/services';service.mkdir(parents=True,exist_ok=True)
for n in ['IMixinService','IGlobalPropertyService']:(service/('org.spongepowered.asm.service.'+n)).write_text('DuckBoxMixinService\n')
cp=os.pathsep.join(map(str,[B/'dist/MouseTweaks-BETA17-sem-nohitdelay-mundo.jar',out,B/'dist/DuckBoxTrainer-1.21.4-0.3.28-alpha.jar',T/'mixin.jar',*T.glob('asm/*.jar'),*T.glob('libraries/**/*.jar')]))
subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-proc:none','-cp',cp,'-d',str(out),str(B/'tests/DuckBoxMixinService.java'),str(B/'tests/MixinTest.java')],check=True)
subprocess.run(['java','-Xverify:all','-cp',cp,'MixinTest',str(T/'minecraft-intermediary.jar'),str(B/'dist/DuckBoxTrainer-1.21.4-0.3.28-alpha.jar')],check=True)

subprocess.run(['java','-Xverify:all','-cp',cp,'MixinTest',str(T/'minecraft-intermediary.jar'),str(B/'dist/DuckBoxTrainer-1.21.4-0.3.28-alpha.jar'),'client'],check=True)

subprocess.run(['java','-Xverify:all','-cp',cp,'MixinTest',str(T/'minecraft-intermediary.jar'),str(B/'dist/DuckBoxTrainer-1.21.4-0.3.28-alpha.jar'),'client',str(B/'dist/MouseTweaks-BETA17-sem-nohitdelay-mundo.jar')],check=True)
