"""Original supersampled mouse artwork. Build asset only; no runtime Pillow dependency."""
from pathlib import Path
from PIL import Image, ImageDraw
OUT=Path(__file__).resolve().parents[1]/'assets'
S=4
for selected in ('left','right','middle'):
 for active in (False,True):
  im=Image.new('RGBA',(160*S,170*S));d=ImageDraw.Draw(im)
  def box(rect,fill,r=20,outline=None,width=1):
   d.rounded_rectangle(tuple(int(v*S) for v in rect),radius=r*S,fill=fill,outline=outline,width=width*S)
  # Halo, shadow, softly tapered shell and independent button panels.
  if active:
   for pad,alpha in ((10,10),(7,18),(4,26)):
    box((30-pad,9-pad,130+pad,157+pad),(255,214,88,alpha),50)
  box((31,13,129,161),'#080b10',48)
  box((29,7,131,155),'#475267',48)
  box((31,9,129,153),'#181e2a',46)
  box((34,13,126,149),'#222b3a',43)
  # Distinct sculpted lobes meet above the palm area.
  for side,rect in [('left',(37,16,77,78)),('right',(83,16,123,78))]:
   fill=('#ffdf74' if active else '#75623a') if selected==side else '#303b4e'
   box(rect,fill,20, '#ffe5a2' if selected==side else '#414d62')
  d.line((36*S,82*S,124*S,82*S),fill='#111722',width=3*S)
  box((73,31,87,60),'#ffdf74' if selected=='middle' else '#0c111a',6,
      '#fff0b6' if selected=='middle' else '#65738b')
  for y in (37,43,49,55):d.line((77*S,y*S,83*S,y*S),fill='#9d803c' if selected=='middle' else '#455166',width=S)
  box((64,128,96,132),'#ffdc5e' if active else '#5b667b',2)
  im.resize((160,170),Image.Resampling.LANCZOS).save(OUT/f'mouse-{selected}-{int(active)}.png')
