#!/usr/bin/env python3
"""Build with Java 21; downloaded dependencies are provided by the server, not bundled."""
from pathlib import Path
import urllib.request, subprocess, zipfile, shutil, hashlib
ROOT=Path(__file__).resolve().parent
TOOLS=ROOT/'tools'; TOOLS.mkdir(exist_ok=True)
urls={
'paper-api.jar':'https://repo.papermc.io/repository/maven-public/io/papermc/paper/paper-api/1.21.1-R0.1-SNAPSHOT/paper-api-1.21.1-R0.1-20250328.161643-128.jar',
'TAB.jar':'https://github.com/NEZNAMY/TAB/releases/download/6.2.1/TAB.v6.2.1.-.Paper.1.20.5.-.1.21.4.jar',
'luckperms-api.jar':'https://repo.maven.apache.org/maven2/net/luckperms/api/5.4/api-5.4.jar',
}
for name,artifact,version in [('adventure-api','net/kyori/adventure-api','4.17.0'),('adventure-key','net/kyori/adventure-key','4.17.0'),('examination-api','net/kyori/examination-api','1.3.0'),('examination-string','net/kyori/examination-string','1.3.0'),('annotations','org/jetbrains/annotations','24.1.0'),('snakeyaml','org/yaml/snakeyaml','2.2'),('guava','com/google/guava/guava','33.2.1-jre'),('bungeecord-chat','net/md-5/bungeecord-chat','1.20-R0.2')]:
    urls[name+'.jar']=f'https://repo.maven.apache.org/maven2/{artifact}/{version}/{name}-{version}.jar'
for name,url in urls.items():
    target=TOOLS/name
    if not target.exists():
        print('Downloading',name,flush=True); urllib.request.urlretrieve(url,target)
classpath=':'.join(str(TOOLS/n) for n in urls)
classes=ROOT/'build/classes'; shutil.rmtree(classes,ignore_errors=True); classes.mkdir(parents=True)
subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-source','21','-target','21','-encoding','UTF-8','-cp',classpath,'-d',str(classes),*[str(p) for p in (ROOT/'src/main/java').rglob('*.java')]],check=True)
for p in (ROOT/'src/main/resources').rglob('*'):
    if p.is_file(): shutil.copy2(p,classes/p.relative_to(ROOT/'src/main/resources'))
dist=ROOT/'dist';dist.mkdir(exist_ok=True)
jar=dist/'DuckHideNick-Paper-1.21-1.0.2.jar'
with zipfile.ZipFile(jar,'w',zipfile.ZIP_DEFLATED) as z:
    for p in classes.rglob('*'):
        if p.is_file():z.write(p,p.relative_to(classes))
print('Built',jar.name,hashlib.sha256(jar.read_bytes()).hexdigest())
if (ROOT/'src/test/java').exists():
    tests=ROOT/'build/tests';tests.mkdir(exist_ok=True)
    subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-source','21','-target','21','-encoding','UTF-8','-cp',str(classes)+':'+classpath,'-d',str(tests),*[str(p) for p in (ROOT/'src/test/java').rglob('*.java')]],check=True)
    subprocess.run(['java','-ea','-cp',str(tests)+':'+str(classes)+':'+classpath,'dev.duckzin.hidenick.PluginTests'],check=True)
