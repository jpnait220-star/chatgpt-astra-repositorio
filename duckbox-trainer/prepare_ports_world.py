"""Convert the supplied template's item formats for each native Minecraft port.
Older versions need real NBT/component conversion, not a renamed world-version tag.
"""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import sys,shutil,json,io,zlib,struct,uuid,hashlib
B=Path(__file__).parent
sys.path.insert(0,str(B/'tools/python'))
import nbtlib as n
ATTRS={'max_health','attack_damage','attack_speed','armor','armor_toughness','movement_speed','knockback_resistance','attack_knockback','follow_range','flying_speed','luck','scale','step_height','gravity','safe_fall_distance','fall_damage_multiplier','jump_strength','burning_time','explosion_knockback_resistance','oxygen_bonus','water_movement_efficiency','movement_efficiency'}
def old_attr(value):
 if value.startswith('minecraft:') and value.split(':')[1] in ATTRS:return value.replace('minecraft:','minecraft:generic.')
 return value
def uuid_ints(raw):
 u=uuid.UUID(raw);return n.IntArray([int.from_bytes(u.bytes[i:i+4],'big',signed=True) for i in range(0,16,4)])
def modifier_uuid(raw):
 h=bytearray(hashlib.md5(raw.encode()).digest());h[6]=(h[6]&15)|48;h[8]=(h[8]&63)|128
 return uuid_ints(str(uuid.UUID(bytes=bytes(h))))
def from_json(value):
 if isinstance(value,dict):return n.Compound({k:from_json(v) for k,v in value.items()})
 if isinstance(value,list):return n.List([from_json(v) for v in value])
 if isinstance(value,bool):return n.Byte(int(value))
 if isinstance(value,int):return n.Int(value)
 if isinstance(value,float):return n.Double(value)
 return n.String(value)
def old_item(raw):
 if not raw:return n.Compound()
 raw=json.loads(json.dumps(raw))
 tag=n.Compound();out=n.Compound({'id':n.String(raw['id']),'Count':n.Byte(raw.get('count',1))})
 for key,value in raw.get('components',{}).items():
  key=key.removeprefix('minecraft:')
  if key=='unbreakable':tag['Unbreakable']=n.Byte(1)
  elif key=='damage':tag['Damage']=n.Int(value)
  elif key=='custom_name':tag.setdefault('display',n.Compound())['Name']=n.String(value if isinstance(value,str) else json.dumps(value,ensure_ascii=False))
  elif key=='lore':tag.setdefault('display',n.Compound())['Lore']=n.List[n.String]([v if isinstance(v,str) else json.dumps(v,ensure_ascii=False) for v in value])
  elif key in ['enchantments','stored_enchantments']:
   levels=value.get('levels',value);tag['Enchantments' if key=='enchantments' else 'StoredEnchantments']=n.List[n.Compound]([n.Compound({'id':n.String(k),'lvl':n.Short(v)}) for k,v in levels.items() if isinstance(v,int)])
  elif key=='attribute_modifiers':
   mods=value.get('modifiers',[]) if isinstance(value,dict) else value
   result=[]
   for m in mods:
    obj=n.Compound({'AttributeName':n.String(old_attr(m['type'])),'Name':n.String(m['id']),'UUID':modifier_uuid(m['id']),'Amount':n.Double(m['amount']),'Operation':n.Int({'add_value':0,'add_multiplied_base':1,'add_multiplied_total':2}[m['operation']])})
    if m.get('slot','any')!='any':obj['Slot']=n.String(m['slot'])
    result.append(obj)
   tag['AttributeModifiers']=n.List[n.Compound](result)
  elif key=='profile':
   profile=n.Compound()
   if 'name' in value:profile['Name']=n.String(value['name'])
   if 'id' in value:profile['Id']=uuid_ints(value['id']) if isinstance(value['id'],str) else n.IntArray(value['id'])
   properties=n.Compound()
   for p in value.get('properties',[]):
    entry=n.Compound({'Value':n.String(p['value'])})
    if 'signature' in p:entry['Signature']=n.String(p['signature'])
    properties.setdefault(p['name'],n.List[n.Compound]()).append(entry)
   if properties:profile['Properties']=properties
   tag['SkullOwner']=profile
  elif key=='custom_data':tag.update(from_json(value))
  elif key=='block_entity_data':tag['BlockEntityTag']=from_json(value)
  elif key=='potion_contents':
   if 'potion' in value:tag['Potion']=n.String(value['potion'])
   if 'custom_color' in value:tag['CustomPotionColor']=n.Int(value['custom_color'])
  elif key=='fireworks':
   tag['Fireworks']=n.Compound({'Flight':n.Byte(value.get('flight_duration',1))})
  elif key in ['max_stack_size','enchantment_glint_override','item_model','repair_cost']:pass
  else:raise ValueError('Component requires conversion: '+key)
 if tag:out['tag']=tag
 return out

def kit_json(raw,version):
 if raw is None:return None
 if version=='1.20.1':return {'snbt':old_item(raw).snbt()}
 raw=json.loads(json.dumps(raw));c=raw.get('components',{})
 if version=='1.21.1':
  for m in c.get('minecraft:attribute_modifiers',{}).get('modifiers',[]):m['type']=old_attr(m['type'])
 elif version=='1.21.11':
  for key in ['minecraft:enchantments','minecraft:stored_enchantments']:
   if key in c and isinstance(c[key],dict) and 'levels' in c[key]:c[key]=c[key]['levels']
  if 'minecraft:attribute_modifiers' in c and isinstance(c['minecraft:attribute_modifiers'],dict):c['minecraft:attribute_modifiers']=c['minecraft:attribute_modifiers']['modifiers']
  for key in ['minecraft:custom_name','minecraft:item_name']:
   if key in c and isinstance(c[key],str):c[key]=json.loads(c[key])
  if 'minecraft:lore' in c:c['minecraft:lore']=[json.loads(v) if isinstance(v,str) else v for v in c['minecraft:lore']]
 return raw

# Supported visual substitutes for blocks introduced after1.20.1.
REPLACEMENTS={'short_grass':'grass','tuff_bricks':'deepslate_bricks','chiseled_tuff_bricks':'chiseled_deepslate','polished_tuff':'polished_deepslate','chiseled_tuff':'chiseled_deepslate','copper_bulb':'copper_block','trial_spawner':'spawner','vault':'chiseled_polished_blackstone','crafter':'crafting_table','heavy_core':'polished_blackstone','pale_oak_planks':'birch_planks'}
for suffix in ['stairs','slab','wall']:
 for start,end in [('tuff_brick','deepslate_brick'),('polished_tuff','polished_deepslate'),('tuff','cobbled_deepslate')]:REPLACEMENTS[start+'_'+suffix]=end+'_'+suffix

def convert_nbt(obj,version,counts):
 if isinstance(obj,n.Compound):
  if 'components' in obj and 'id' in obj and str(obj['id']).startswith(('minecraft:','duckbox:')) and ('count' in obj or 'Count' in obj):
   raw=json.loads(json.dumps(obj.unpack(),default=lambda o:o.tolist()))
   if version=='1.20.1':
    slot=obj.get('Slot');item=old_item(raw);obj.clear();obj.update(item)
    if slot is not None:obj['Slot']=slot
    counts['items']+=1
   elif version=='1.21.1':
    attrs=obj['components'].get('minecraft:attribute_modifiers',{}).get('modifiers',[])
    for modifier in attrs:
     modifier['type']=n.String(old_attr(str(modifier['type'])))
  if version=='1.20.1':
   if 'Name' in obj and str(obj['Name']).startswith('minecraft:'):
    key=str(obj['Name']).split(':')[1]
    if key in REPLACEMENTS:obj['Name']=n.String('minecraft:'+REPLACEMENTS[key]);counts['block_substitutions']+=1
   # Chests store profile role outside the post1.20.5 component system.
   if 'components' in obj and 'minecraft:custom_data' in obj['components']:
    marker=obj['components']['minecraft:custom_data']
    if 'duckbox_chest_profile' in marker:obj['duckbox_visual_role']=n.Int(marker['duckbox_chest_profile'])
  for key,value in list(obj.items()):
   if key=='DataVersion' and version in ['1.20.1','1.21.1']:obj[key]=n.Int(3465 if version=='1.20.1' else 3955)
   else:convert_nbt(value,version,counts)
 elif isinstance(obj,n.List):
  for value in obj:convert_nbt(value,version,counts)

def region(path,version,counts):
 data=path.read_bytes();out=bytearray(data[:8192]);sector=2
 for i in range(1024):
  record=int.from_bytes(data[i*4:i*4+4],'big');offset=record>>8
  if not offset:continue
  start=offset*4096;length=int.from_bytes(data[start:start+4],'big');mode=data[start+4]
  if mode!=2:raise ValueError('Unexpected chunk compression '+str(mode))
  chunk=n.File.parse(io.BytesIO(zlib.decompress(data[start+5:start+4+length])))
  convert_nbt(chunk,version,counts);buffer=io.BytesIO();chunk.write(buffer);encoded=zlib.compress(buffer.getvalue())
  payload=struct.pack('>I',len(encoded)+1)+b'\x02'+encoded;sectors=(len(payload)+4095)//4096
  if sectors>255:raise ValueError('Large chunk')
  out[i*4:i*4+4]=((sector<<8)|sectors).to_bytes(4,'big');out.extend(payload);out.extend(bytes(sectors*4096-len(payload)));sector+=sectors;counts['chunks']+=1
 path.write_bytes(out)

def prepare(version):
 root=Path('/workspace/duckbox-trainer-'+version);dest=root/'dist/DuckBoxTreino';shutil.rmtree(dest,ignore_errors=True);shutil.copytree(B/'dist/DuckBoxTreino',dest)
 config=json.loads((dest/'duckbox-training.json').read_text())
 for profile in config['kitProfiles'].values():profile['inventory']=[kit_json(v,version) for v in profile['inventory']]
 for key in ['kit','inventory']:
  if key in config and isinstance(config[key],list):config[key]=[kit_json(v,version) for v in config[key]]
 (dest/'duckbox-training.json').write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n')
 counts={'chunks':0,'items':0,'block_substitutions':0}
 if version in ['1.20.1','1.21.1']:
  for p in dest.rglob('*.mca'):region(p,version,counts)
  for persistent in (dest/'data').glob('*.dat'):
   saved=n.load(persistent);convert_nbt(saved,version,counts)
   if version=='1.20.1' and persistent.name=='random_sequences.dat' and 'sequences' in saved.get('data',{}):saved['data']=saved['data']['sequences']
   saved.save(persistent,gzipped=True)
  level=n.load(dest/'level.dat');convert_nbt(level,version,counts);data=level['Data'];data['Version']=n.Compound({'Id':n.Int(3465 if version=='1.20.1' else 3955),'Name':n.String(version),'Series':n.String('main'),'Snapshot':n.Byte(0)})
  #1.20.1 world feature flag names and format are compatible with enabled vanilla.
  data['enabled_features']=n.List[n.String](['minecraft:vanilla']);level.save(dest/'level.dat',gzipped=True)
 (dest/'LEIA-ME.txt').write_text('Mundo de Duckzin paraMinecraft '+version+'. Mapa enviado pelo autor; giro baixo padrao. Dados de jogadores removidos.\n')
 out=root/'src/main/resources/assets/duckbox/world/duckzin.zip'
 with ZipFile(out,'w',ZIP_DEFLATED) as z:
  for p in sorted(dest.rglob('*')):
   if p.is_file():z.write(p,p.relative_to(dest).as_posix())
 (root/'world-conversion.json').write_text(json.dumps({'minecraft':version,**counts},indent=2)+'\n')
 print('PREPARED',version,counts,flush=True)
if __name__=='__main__':
 for version in sys.argv[1:] or ['1.21.1','1.21.11','1.20.1']:prepare(version)
