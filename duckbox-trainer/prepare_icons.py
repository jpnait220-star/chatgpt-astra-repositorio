"""Encode the author's supplied PNG at the sizes required by Fabric and Minecraft."""
from pathlib import Path
import sys,shutil,json
from PIL import Image
B=Path(__file__).parent
if len(sys.argv)!=2:raise SystemExit('Usage: python prepare_icons.py avatar-original.png')
source=Path(sys.argv[1]);image=Image.open(source).convert('RGBA')
if image.width!=image.height:raise SystemExit('Provide the square original to preserve the entire avatar without cropping.')
art=B/'art';art.mkdir(exist_ok=True)
if source.resolve()!=(art/'avatar-original.png').resolve():shutil.copyfile(source,art/'avatar-original.png')
resources=B/'src/main/resources/assets/duckbox'
image.resize((256,256),Image.Resampling.LANCZOS).save(resources/'icon.png')
image.resize((64,64),Image.Resampling.LANCZOS).save(resources/'world_icon.png')
meta=B/'src/main/resources/fabric.mod.json';data=json.loads(meta.read_text());data['icon']='assets/duckbox/icon.png';meta.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
print('ENCODED supplied avatar as256x256mod icon and64x64world icon; original preserved')
