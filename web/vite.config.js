import {defineConfig} from 'vite';
import react from '@vitejs/plugin-react';
import {existsSync,readFileSync} from 'node:fs';

const envPath=new URL('../.env',import.meta.url);
const env=existsSync(envPath)?Object.fromEntries(readFileSync(envPath,'utf8').split(/\r?\n/).filter(x=>x&&!x.startsWith('#')&&x.includes('=')).map(x=>{const i=x.indexOf('=');return [x.slice(0,i).trim(),x.slice(i+1).trim()]})):{};
const evidence=()=>JSON.parse(readFileSync(new URL('./web_export.json',import.meta.url),'utf8'));

async function explain(body){
  const pair=evidence().pairs.find(p=>p.pair===body.pair);
  const cell=pair?.grid[String(body.size)]?.[String(body.hold)];
  if(!pair||!cell)throw Error('That recorded scenario is unavailable.');
  if(!env.BITGET_QWEN_API_KEY)throw Error('Qwen is not configured.');
  const facts={pair:pair.pair,verdict:cell.verdict,gross_annual_pct:pair.edge.annual_pct,gross_bp:cell.gross_bp,cost_bp:cell.cost_bp,net_bp:cell.net_bp,net_annual_pct:cell.annual_pct,risk_bp:cell.risk_bp,sharpe:cell.sharpe,ci:[cell.ci_lo,cell.ci_hi],breakeven_days:cell.breakeven_days,history_days:pair.edge.history_days,validation_start:pair.edge.validation_start,validation_end:pair.edge.validation_end,stress:cell.stress};
  const response=await fetch(`${env.BITGET_QWEN_BASE_URL||'https://hackathon.bitgetops.com/v1'}/chat/completions`,{method:'POST',headers:{'Content-Type':'application/json',Authorization:`Bearer ${env.BITGET_QWEN_API_KEY}`},body:JSON.stringify({model:env.BITGET_QWEN_MODEL||'qwen3.8-max',temperature:.1,max_tokens:220,messages:[{role:'system',content:'Return only valid JSON with exactly four short string fields: finding, binding_constraint, invalidation, next_check. Use no digits, quantities, prices, percentages, recommendations, or facts absent from the frozen evidence.'},{role:'user',content:JSON.stringify({question:body.question,evidence:facts})}]})});
  if(!response.ok)throw Error(`Qwen returned ${response.status}.`);
  const data=await response.json();let commentary;try{commentary=JSON.parse(data.choices?.[0]?.message?.content?.replace(/^```json\s*/i,'').replace(/```$/,'').trim())}catch{throw Error('Qwen’s response could not be verified.')}
  const keys=['finding','binding_constraint','invalidation','next_check'];if(keys.some(k=>typeof commentary[k]!=='string'||/\d/.test(commentary[k])))throw Error('Qwen’s response did not pass the evidence guard.');
  return {commentary,model:env.BITGET_QWEN_MODEL||'qwen3.8-max',evidence:facts};
}

export default defineConfig({base:'./',build:{outDir:'dist/client',emptyOutDir:true},plugins:[react(),{name:'reef-evidence',configureServer(server){server.middlewares.use('/web_export.json',(_req,res)=>{res.setHeader('Content-Type','application/json');res.end(JSON.stringify(evidence()))});server.middlewares.use('/api/investigate',async(req,res)=>{if(req.method!=='POST'){res.statusCode=405;return res.end()}let raw='';req.on('data',c=>raw+=c);req.on('end',async()=>{try{const result=await explain(JSON.parse(raw));res.setHeader('Content-Type','application/json');res.end(JSON.stringify(result))}catch(error){res.statusCode=502;res.setHeader('Content-Type','application/json');res.end(JSON.stringify({error:error.message}))}})})},generateBundle(){this.emitFile({type:'asset',fileName:'web_export.json',source:readFileSync(new URL('./web_export.json',import.meta.url))})}}]});
