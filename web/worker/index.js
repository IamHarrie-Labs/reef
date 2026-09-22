const json=(value,status=200)=>new Response(JSON.stringify(value),{status,headers:{'content-type':'application/json; charset=utf-8','cache-control':'no-store'}});

async function investigate(request,env){
  if(request.method!=='POST')return json({error:'Method not allowed.'},405);
  let body;
  try{body=await request.json()}catch{return json({error:'Invalid request.'},400)}
  const snapshot=await (await env.ASSETS.fetch(new URL('/web_export.json',request.url))).json();
  const pair=snapshot.pairs.find(p=>p.pair===body.pair);
  const cell=pair?.grid[String(body.size)]?.[String(body.hold)];
  if(!pair||!cell)return json({error:'That recorded scenario is unavailable.'},404);
  const evidence={pair:pair.pair,verdict:cell.verdict,gross_annual_pct:pair.edge.annual_pct,gross_bp:cell.gross_bp,cost_bp:cell.cost_bp,net_bp:cell.net_bp,net_annual_pct:cell.annual_pct,risk_bp:cell.risk_bp,sharpe:cell.sharpe,ci:[cell.ci_lo,cell.ci_hi],breakeven_days:cell.breakeven_days,history_days:pair.edge.history_days};
  try{
    const upstream=await fetch(`${env.BITGET_QWEN_BASE_URL||'https://hackathon.bitgetops.com/v1'}/chat/completions`,{method:'POST',headers:{'content-type':'application/json',authorization:`Bearer ${env.BITGET_QWEN_API_KEY}`},body:JSON.stringify({model:env.BITGET_QWEN_MODEL||'qwen3.8-max',temperature:.2,max_tokens:180,messages:[{role:'system',content:'You are Reef’s evidence interpreter. Explain why the verdict follows in two short plain-English sentences. Use no digits, quantities, prices, percentages, performance claims, recommendations, or new facts. The deterministic interface already displays every number. State uncertainty clearly.'},{role:'user',content:JSON.stringify({question:String(body.question||''),evidence})}]})});
    if(!upstream.ok)return json({error:'The AI explanation is temporarily unavailable.'},502);
    const result=await upstream.json();
    const commentary=result.choices?.[0]?.message?.content?.trim();
    if(!commentary||/\d/.test(commentary))return json({error:'The AI response did not pass Reef’s evidence guard.'},502);
    return json({commentary,model:env.BITGET_QWEN_MODEL||'qwen3.8-max',evidence});
  }catch{return json({error:'The AI explanation timed out. Reef’s calculated evidence is still available.'},504)}
}

export default {async fetch(request,env){const url=new URL(request.url);if(url.pathname==='/api/investigate')return investigate(request,env);return env.ASSETS.fetch(request)}};
