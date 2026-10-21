// Publishable code/UI dependencies only. Business data stays in TableGit.
const fs=require('fs'),path=require('path');
const mapping={'assets/lri-tablegit.js':'runtime/tablegit.js','assets/insight-executive.css':'runtime/insight.css','assets/lri-shell.js':'runtime/lri-shell.js','assets/lri-shell.config.json':'runtime/lri-shell.config.json','assets/lri-translation-runtime.js':'runtime/lri-translation-runtime.js','assets/lri-translation-core.js':'runtime/lri-translation-core.js','assets/lri-browser-translator.js':'runtime/lri-browser-translator.js'};
const inputRoot=process.argv[2];if(!inputRoot)throw Error('Pass the shared asset repository root');
for(const [source,target]of Object.entries(mapping)){
 let text=fs.readFileSync(path.join(inputRoot,source),'utf8');if(source==='assets/lri-shell.js')text=text.replace("const repoRootUrl = new URL('../', assetUrl);","const repoRootUrl = new URL('../../../', assetUrl);");
 if(source==='assets/lri-tablegit.js')text=text.replace('async function readJson(url, options = {}) {', 'async function readJson(url, options = {}) {\n    if (globalThis.LRICloudTableRead && new URL(url, location.href).pathname.startsWith(\'/__mcpgit/tables/\')) return globalThis.LRICloudTableRead(url, options);');
 const destination=path.join(inputRoot,'business_insight/cloud_core',target);fs.mkdirSync(path.dirname(destination),{recursive:true});fs.writeFileSync(destination,text);
}
