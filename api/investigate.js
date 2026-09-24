const fs=require('node:fs');
const path=require('node:path');

const bundled=JSON.parse(fs.readFileSync(path.join(process.cwd(),'web','web_export.json'),'utf8'));
const LIVE='https://raw.githubusercontent.com/IamHarrie-Labs/reef/main/web/web_export.json';
let cache={at:0,data:null};
// The desk page reads the hourly live export; explain the same snapshot the visitor is looking at.
async function currentSnapshot(){
  if(cache.data&&Date.now()-cache.at<300000)return cache.data;
  try{const r=await fetch(LIVE,{signal:AbortSignal.timeout(4000)});if(r.ok){const d=await r.json();if(d.model_version==='2.0'&&Array.isArray(d.pairs)&&String(d.generated_utc)>=String(bundled.generated_utc)){cache={at:Date.now(),data:d};return d}}}catch{}
  return bundled;
}
const requests=new Map();
function clientKey(req){return String(req.headers['x-forwarded-for']||req.socket?.remoteAddress||'unknown').split(',')[0].trim()}
// Best-effort, per-instance limit: serverless instances do not share this map, so it
// slows casual abuse of the Qwen key rather than enforcing a global quota.
function limited(req){const key=clientKey(req),now=Date.now(),recent=(requests.get(key)||[]).filter(t=>now-t<60000);recent.push(now);requests.set(key,recent);return recent.length>12}
function safeJson(text){return JSON.parse(String(text||'').trim().replace(/^```json\s*/i,'').replace(/```$/,'').trim())}
function fallback(e){return {finding:e.verdict==='UNPROVEN'?'The carry survives estimated costs, but the uncertainty range still includes a losing outcome.':e.verdict==='SUPPORTED'?'The tested carry survives costs and the stated evidence threshold.':'The apparent carry does not survive the tested costs and residual risk.',binding_constraint:e.ci?.[0]<=0?'The uncertainty range is the binding constraint.':e.net_bp<=0?'Execution cost is the binding constraint.':'Residual spread risk remains the binding constraint.',invalidation:'A material change in funding, liquidity, or spread behaviour could change this result.',next_check:'Refresh the funding window and executable depth before relying on the result.'}}

module.exports=async function handler(req,res){
  res.setHeader('Cache-Control','no-store');
  if(req.method!=='POST')return res.status(405).json({error:'Method not allowed.'});
  if(limited(req))return res.status(429).json({error:'Too many investigations. Wait a moment and try again.'});
  let body;try{body=typeof req.body==='string'?JSON.parse(req.body):req.body}catch{return res.status(400).json({error:'The request could not be read.'})}
  if(!body||typeof body.question!=='string'||body.question.length<3||body.question.length>500)return res.status(400).json({error:'Ask a question between three and five hundred characters.'});
  const snapshot=await currentSnapshot();
  if(typeof body.pair!=='string'||!snapshot.sizes.map(String).includes(String(body.size))||!snapshot.holds.map(String).includes(String(body.hold)))return res.status(400).json({error:'Choose a recorded pair, size and holding period.'});
  const pair=snapshot.pairs.find(item=>item.pair===body?.pair);
  const cell=pair?.grid[String(body?.size)]?.[String(body?.hold)];
  if(!pair||!cell)return res.status(404).json({error:'That recorded scenario is unavailable.'});
  const evidence={pair:pair.pair,verdict:cell.verdict,gross_annual_pct:pair.edge.annual_pct,gross_bp:cell.gross_bp,cost_bp:cell.cost_bp,net_bp:cell.net_bp,net_annual_pct:cell.annual_pct,risk_bp:cell.risk_bp,sharpe:cell.sharpe,ci:[cell.ci_lo,cell.ci_hi],breakeven_days:cell.breakeven_days,history_days:pair.edge.history_days,validation_start:pair.edge.validation_start,validation_end:pair.edge.validation_end,stress:cell.stress};
  try{
    if(!process.env.BITGET_QWEN_API_KEY)return res.status(503).json({error:'AI commentary is not configured. Reef’s calculated evidence remains available.'});
    const upstream=await fetch(`${process.env.BITGET_QWEN_BASE_URL||'https://hackathon.bitgetops.com/v1'}/chat/completions`,{method:'POST',headers:{'content-type':'application/json',authorization:`Bearer ${process.env.BITGET_QWEN_API_KEY}`},body:JSON.stringify({model:process.env.BITGET_QWEN_MODEL||'qwen3.8-max',temperature:.1,max_tokens:220,messages:[{role:'system',content:'You are Reef’s evidence interpreter. Return only valid JSON with exactly four string fields: finding, binding_constraint, invalidation, next_check. Each field must be one short plain-English sentence. Use no digits, quantities, prices, percentages, performance claims, trade recommendations, or facts absent from the evidence. Explain only what the frozen evidence means. State uncertainty plainly.'},{role:'user',content:JSON.stringify({question:body.question,evidence})}]}),signal:AbortSignal.timeout(75000)});
    if(!upstream.ok)return res.status(502).json({error:'The AI explanation is temporarily unavailable.'});
    const result=await upstream.json();
    let commentary;try{commentary=safeJson(result.choices?.[0]?.message?.content)}catch{return res.status(502).json({error:'The AI response could not be verified.'})}
    const keys=['finding','binding_constraint','invalidation','next_check'];
    if(Object.keys(commentary).sort().join('|')!==keys.slice().sort().join('|')||keys.some(k=>typeof commentary[k]!=='string'||!commentary[k].trim()||/\d/.test(commentary[k])))return res.status(502).json({error:'The AI response did not pass Reef’s evidence guard.'});
    return res.status(200).json({commentary,model:process.env.BITGET_QWEN_MODEL||'qwen3.8-max',evidence});
  }catch{return res.status(200).json({commentary:fallback(evidence),model:'Reef evidence fallback',evidence,notice:'Qwen timed out; deterministic interpretation shown.'})}
};
