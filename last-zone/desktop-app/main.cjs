const {app,BrowserWindow,Menu,ipcMain,dialog}=require('electron');
const fs=require('node:fs'),path=require('node:path');
const {createLocalServer,normalizeServerURL,cleanPreferences,healthCheck}=require('./local-server.cjs');
let window=null,local=null,config={serverURL:'',preferences:{}},file='',closing=false,prompting=false,saveTimer=null;
function persist(){try{fs.mkdirSync(path.dirname(file),{recursive:true});fs.writeFileSync(file+'.tmp',JSON.stringify(config,null,2));fs.renameSync(file+'.tmp',file)}catch{}}
if(!app.requestSingleInstanceLock()){app.quit()}else{
 app.on('second-instance',()=>{if(window){if(window.isMinimized())window.restore();window.focus()}});
 app.whenReady().then(async()=>{file=path.join(app.getPath('userData'),'settings.json');try{const saved=JSON.parse(fs.readFileSync(file,'utf8'));config={serverURL:saved.serverURL?normalizeServerURL(saved.serverURL):'',preferences:cleanPreferences(saved.preferences)}}catch{}
 Menu.setApplicationMenu(null);local=createLocalServer({gameFile:path.join(__dirname,'game.html'),getConfig:()=>config});const origin=await local.start();
 window=new BrowserWindow({title:'LAST ZONE',width:1366,height:820,minWidth:960,minHeight:640,backgroundColor:'#10232a',icon:path.join(__dirname,'icon.png'),webPreferences:{preload:path.join(__dirname,'preload.cjs'),nodeIntegration:false,contextIsolation:true,sandbox:true,webSecurity:true,backgroundThrottling:false}});
 window.webContents.setIgnoreMenuShortcuts(true);window.webContents.setWindowOpenHandler(()=>({action:'deny'}));window.webContents.on('will-navigate',(event,url)=>{try{if(new URL(url).origin!==origin)event.preventDefault()}catch{event.preventDefault()}});
 window.on('close',async event=>{if(closing)return;event.preventDefault();if(prompting)return;prompting=true;const result=await dialog.showMessageBox(window,{type:'question',buttons:['Continuar jogando','Sair'],defaultId:0,cancelId:0,message:'Sair do Last Zone?',detail:'Se você é o anfitrião, a sala será encerrada para o amigo.'});prompting=false;if(result.response===1){closing=true;persist();window.destroy();app.quit()}});
 window.webContents.on('render-process-gone',async(_event,details)=>{if(closing)return;const result=await dialog.showMessageBox(window,{type:'warning',buttons:['Reabrir no modo leve','Fechar'],message:'O processo gráfico foi interrompido.',detail:'Motivo: '+details.reason});if(result.response===0){config.preferences['lz-quality']='0';persist();await window.loadURL(origin+'/?quality=low')}else{closing=true;window.destroy();app.quit()}});
 ipcMain.handle('get-config',event=>{if(event.sender!==window.webContents)throw Error('Origem inválida');return {serverURL:config.serverURL}});
 ipcMain.handle('connect-server',async(event,value)=>{if(event.sender!==window.webContents)throw Error('Origem inválida');const url=normalizeServerURL(value);if(new URL(url).port===new URL(origin).port&&['127.0.0.1','localhost','0.0.0.0','[::1]'].includes(new URL(url).hostname))throw Error('Use o endereço do servidor público, não o endereço local do aplicativo.');const result=await healthCheck(url);config.serverURL=url;persist();return result});
 ipcMain.on('preferences',(event,value)=>{if(event.sender!==window.webContents)return;config.preferences=cleanPreferences(value);clearTimeout(saveTimer);saveTimer=setTimeout(persist,200)});
 await window.loadURL(origin);
 }).catch(async err=>{await dialog.showErrorBox('LAST ZONE',String(err.message));app.exit(1)});
 app.on('window-all-closed',()=>app.quit());app.on('before-quit',()=>{persist();local?.stop().catch(()=>{})});
}
