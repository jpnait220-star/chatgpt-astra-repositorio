const {contextBridge,ipcRenderer}=require('electron');
contextBridge.exposeInMainWorld('lastZoneDesktop',{isDesktop:true,getConfig:()=>ipcRenderer.invoke('get-config'),connectServer:value=>ipcRenderer.invoke('connect-server',value)});
const keys=['lz','lz-controls','lz-quality','lz-music','lz-effects','lz-mix-version'];let previous='';function save(){try{const preferences={};for(const key of keys){const value=window.localStorage.getItem(key);if(value!==null)preferences[key]=value}const serialized=JSON.stringify(preferences);if(serialized!==previous){previous=serialized;ipcRenderer.send('preferences',preferences)}}catch{}}
window.addEventListener('DOMContentLoaded',()=>{setInterval(save,1500)});window.addEventListener('beforeunload',save);
