from pathlib import Path
import struct,gzip,json,time
B=Path(__file__).parent;root=B/'dist/DuckBoxTreino';root.mkdir(parents=True,exist_ok=True)
class Long(int):pass
class Byte(int):pass
class Float(float):pass
def string(s):b=s.encode();return struct.pack('>H',len(b))+b
def kind(x):return 1 if isinstance(x,Byte) else 4 if isinstance(x,Long) else 3 if isinstance(x,int) else 5 if isinstance(x,Float) else 6 if isinstance(x,float) else 8 if isinstance(x,str) else 10 if isinstance(x,dict) else 9

def payload(x):
 t=kind(x)
 if t in [1,3,4,5,6]:return struct.pack({1:'>b',3:'>i',4:'>q',5:'>f',6:'>d'}[t],x)
 if t==8:return string(x)
 if t==10:return b''.join(bytes([kind(v)])+string(k)+payload(v) for k,v in x.items())+b'\0'
 return bytes([kind(x[0]) if x else 0])+struct.pack('>i',len(x))+b''.join(payload(v) for v in x)
dimensions={'minecraft:overworld':{'type':'minecraft:overworld','generator':{'type':'minecraft:flat','settings':{'biome':'minecraft:plains','lakes':Byte(0),'features':Byte(0),'structure_overrides':[],'layers':[{'height':1,'block':'minecraft:bedrock'},{'height':126,'block':'minecraft:stone'},{'height':1,'block':'minecraft:smooth_stone'}]}}},'minecraft:the_nether':{'type':'minecraft:the_nether','generator':{'type':'minecraft:noise','settings':'minecraft:nether','biome_source':{'type':'minecraft:multi_noise','preset':'minecraft:nether'}}},'minecraft:the_end':{'type':'minecraft:the_end','generator':{'type':'minecraft:noise','settings':'minecraft:end','biome_source':{'type':'minecraft:the_end'}}}}
data={'DataVersion':4189,'version':19133,'Version':{'Id':4189,'Name':'1.21.4','Snapshot':Byte(0),'Series':'main'},'LevelName':'DuckBoxTreino','GameType':1,'allowCommands':Byte(1),'initialized':Byte(1),'hardcore':Byte(0),'Difficulty':Byte(2),'DifficultyLocked':Byte(0),'SpawnX':-32,'SpawnY':79,'SpawnZ':120,'SpawnAngle':Float(180),'Time':Long(0),'DayTime':Long(6000),'LastPlayed':Long(int(time.time()*1000)),'rainTime':0,'thunderTime':0,'clearWeatherTime':1000000,'raining':Byte(0),'thundering':Byte(0),'GameRules':{'doMobSpawning':'false','doDaylightCycle':'false','doWeatherCycle':'false','spawnRadius':'0','keepInventory':'true'},'DataPacks':{'Enabled':['vanilla'],'Disabled':[]},'WorldGenSettings':{'seed':Long(271828),'generate_features':Byte(0),'bonus_chest':Byte(0),'dimensions':dimensions},'BorderCenterX':0.0,'BorderCenterZ':0.0,'BorderSize':59999968.0}
(root/'level.dat').write_bytes(gzip.compress(b'\x0a\x00\x00'+payload({'Data':data})))
(root/'LEIA-ME.txt').write_text('DuckBoxTreino 1.21.4. Instale Fabric + Fabric API + DuckBoxTrainer. Apenas a arena e construida na primeira entrada. Aguarde a montagem. O mundo e um template plano, sem construcoes importadas de terceiros.\n')
(root/'duckbox-training.json').write_text(json.dumps({'arenaRevision':3,'arenaPositionRevision':1,'options':{'x':-5,'y':78,'z':111,'size':13,'initialized':True,'built':False,'autoBuildOnJoin':True,'customMap':False,'dimension':'minecraft:overworld'},'backups':{}},indent=2)+'\n')
print('MAP',root)
