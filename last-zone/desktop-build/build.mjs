import {packager} from '@electron/packager';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import os from 'node:os';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const platform=process.argv[2]||'win32';
const paths=await packager({dir:path.join(root,'desktop-app'),name:'LAST ZONE',platform,arch:'x64',electronVersion:'45.3.2',out:path.join(root,'desktop-dist'),overwrite:true,asar:true,icon:path.join(root,'desktop-app','icon'),prune:true,download:{cacheRoot:path.join(os.tmpdir(),'last-zone-electron-cache')},appCopyright:'Last Zone — protótipo independente',win32metadata:{CompanyName:'Last Zone',FileDescription:'Last Zone Desktop',ProductName:'LAST ZONE'}});
console.log(JSON.stringify({platform,outputs:paths}));
