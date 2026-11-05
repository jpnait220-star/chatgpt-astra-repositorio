from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import hashlib,json,os,subprocess,sys
B=Path(__file__).parent;T=B/'tools';out=B/'build/mouse-patch';out.mkdir(parents=True,exist_ok=True)
original=Path(sys.argv[1]);dest=B/'dist/MouseTweaks-BETA17-sem-nohitdelay-mundo.jar'
asm=os.pathsep.join(map(str,T.glob('asm/*.jar')))
subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-proc:none','-cp',asm,'-d',str(out),str(B/'tests/PatchMouse.java'),str(B/'tests/mousebridge/com/duckunified/duckbox/HitDelayScope.java')],check=True)
with ZipFile(original) as src:
 entries={n:src.read(n) for n in src.namelist() if not n.endswith('/')}
assert not any(n.upper().endswith(('.SF','.RSA','.DSA')) for n in entries),'Signed archive: do not modify signatures'
local='com/duckunified/mixin/LocalAttackDelayMixin.class'
(out/'original.class').write_bytes(entries[local])
subprocess.run(['java','-cp',os.pathsep.join([str(out),asm]),'PatchMouse',str(out/'original.class'),str(out/'patched.class')],check=True)
meta=json.loads(entries['fabric.mod.json']);meta['version']='1.0.0-beta.17-client-hitdelay-only';meta['description']='MouseTweaks BETA17: removida a camada que altera forca de ataque e imunidade em mundos. Demais funcoes preservadas; no trainer, hit-delay local so no Insta Kill.'
meta['entrypoints']['client'].remove('com.duckunified.combat.CombatClient')
meta['mixins'].remove('internal/duckunified-combat.mixins.json')
removed=[n for n in entries if n.startswith('com/duckunified/combat/') or n=='internal/duckunified-combat.mixins.json']
result={n:d for n,d in entries.items() if n not in removed}
result['fabric.mod.json']=(json.dumps(meta,indent=2,ensure_ascii=False)+'\n').encode()
result[local]=(out/'patched.class').read_bytes()
bridge='com/duckunified/duckbox/HitDelayScope.class';result[bridge]=(out/bridge).read_bytes()
result['DUCKBOX-PATCH-LEIA-ME.txt']=('Removidos AttackStrengthMixin/DamageWindowMixin e menu F10+C da camada Combat.\nNo Hit Delay local e demais funcoes originais preservados. Durante DuckBox,\na ponte permite o hitdelay local somente no Insta Kill; fora dele, as opcoes\noriginais do MouseTweaks continuam valendo. Substitua o MouseTweaks antigo.\nNao e necessario apagar o mundo ou as configs.\n').encode()
with ZipFile(dest,'w',ZIP_DEFLATED) as z:
 for n,d in result.items():z.writestr(n,d)
assert all(result[n]==d for n,d in entries.items() if n not in removed and n not in ['fabric.mod.json',local])
with ZipFile(dest) as z:assert z.testzip() is None
report={'input_sha256':hashlib.sha256(original.read_bytes()).hexdigest(),'output_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'removed':removed,'changed':['fabric.mod.json',local],'added':[bridge,'DUCKBOX-PATCH-LEIA-ME.txt'],'preserved_identical':len(entries)-len(removed)-2}
(B/'dist/MouseTweaks-BETA17-PATCH-VALIDACAO.json').write_text(json.dumps(report,indent=2)+'\n')
print('PATCHED',dest.name,'preserved',report['preserved_identical'],'original entries byte-for-byte; removed',len(removed),'world-combat entries')
