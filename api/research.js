const fs=require('node:fs');
const path=require('node:path');
const bundled=JSON.parse(fs.readFileSync(path.join(process.cwd(),'web','web_export.json'),'utf8'));
const counts=new Map();
let cached=null,cachedAt=0;
module.exports=async(req,res)=>{
 res.setHeader('Cache-Control','no-store');
 if(req.method!=='POST')return res.status(405).json({error:'Method not allowed.'});
 const key=String(req.headers['x-forwarded-for']||req.socket?.remoteAddress||'unknown').split(',')[0],now=Date.now();
 const recent=(counts.get(key)||[]).filter(t=>now-t<60000);recent.push(now);counts.set(key,recent);
 if(counts.size>2000)for(const [k,v] of counts)if(v.at(-1)<now-60000)counts.delete(k);
 if(recent.length>12)return res.status(429).json({error:'Too many research turns. Wait a minute and retry.'});
 let body;try{body=typeof req.body==='string'?JSON.parse(req.body):req.body;if(!body||JSON.stringify(body).length>14000)throw Error()}catch{return res.status(400).json({error:'Invalid research request.'})}
 let snapshot=bundled;
 if(body.snapshot_utc!==bundled.generated_utc){
  if(!cached||now-cachedAt>60000){try{const r=await fetch('https://raw.githubusercontent.com/IamHarrie-Labs/reef/main/web/web_export.json',{signal:AbortSignal.timeout(4000)});if(r.ok){cached=await r.json();cachedAt=now}}catch{}}
  if(cached?.generated_utc===body.snapshot_utc)snapshot=cached;
  else return res.status(409).json({error:'The desk snapshot changed. Start a new notebook with the latest evidence.'});
 }
 try{const {research}=await import('../web/research/core.mjs');return res.status(200).json(await research(snapshot,body,process.env))}catch(error){return res.status(error.status||500).json({error:error.status?error.message:'Research is temporarily unavailable. Your notebook is retained.'})}
};
