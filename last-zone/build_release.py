"""Build both self-contained playable HTML and a source archive without network access."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import runpy
ROOT=Path(__file__).resolve().parent
runpy.run_path(str(ROOT/'enhance.py'))
s=(ROOT/'LAST ZONE Frontier.html').read_text()
lib=(ROOT/'three.min.js').read_text().replace('</script','<\\/script')
standalone=s.replace('<script src="./three.min.js"></script>','<script>'+lib+'</script>')
for name in ['LAST ZONE Frontier offline.html','LAST ZONE Island 2.html','LAST ZONE Duo.html']:
 (ROOT/name).write_text(standalone)
if (ROOT/'desktop-app').is_dir():
 (ROOT/'desktop-app/game.html').write_text(standalone)
with ZipFile(ROOT/'LAST-ZONE-Duo.zip','w',ZIP_DEFLATED) as archive:
 for name in ['LAST ZONE Duo.html','MULTIPLAYER.txt','server.mjs','Dockerfile','render.yaml','package.json','combat-ui.js','multiplayer.js','balance.js','expansion.js','controls.js','campaign.js','revamp-world.js','revamp-movement.js','revamp-ai.js','audio-assets.js','revamp-audio.js','verdant-world.js','aim-camera.js','test_health_200.py','test_verdant.py','AUDIO-CREDITS.txt','test_revamp.py','ALTARE-GUIA.txt','COMECE-AQUI.txt','server-config.json','test_native_proxy.cjs','test_desktop.py','test_expansion.py','test_duo.py','VALIDACAO-DUO.txt','duo-hud.png','LAST ZONE Island 2.html','LAST ZONE Frontier.html','three.min.js','LEIA-ME.txt','original.html','upgrade.js','visuals.js','animation.js','graphics.js','island.js','polish.js','enhance.py','build_release.py','test_game.py','test_island.py','island-town.png','island-trees.png','island-aerial.png','island-lobby.png']:
  if (ROOT/name).is_file():archive.write(ROOT/name,name)
 for path in (ROOT/'audio').glob('*'):
  if path.is_file():archive.write(path,path.relative_to(ROOT))
 for path in (ROOT/'desktop-app').glob('*'):
  if path.is_file():archive.write(path,path.relative_to(ROOT))
 for name in ['package.json','package-lock.json','build.mjs']:
  path=ROOT/'desktop-build'/name
  if path.is_file():archive.write(path,path.relative_to(ROOT))
print('Built: LAST ZONE Duo.html and LAST-ZONE-Duo.zip')
