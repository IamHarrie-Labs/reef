import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {executePlan,research,resolveQuestion,validatePlan} from './core.mjs';
import worker from '../worker/index.js';
const snapshot=JSON.parse(fs.readFileSync(new URL('../web_export.json',import.meta.url)));
const context={pairs:['QQQ/TQQQ'],size:25000,hold:30,stress:null};

test('comparison uses the Python cells unchanged',()=>{
 const plan=resolveQuestion(snapshot,'Compare QQQ/TQQQ with SMH/SOXL at $25k for 30 days',context);
 const result=executePlan(snapshot,plan);assert.equal(result.cards.length,2);
 for(const card of result.cards)assert.deepEqual(card.cell,snapshot.pairs.find(p=>p.pair===card.pair).grid['25000']['30']);
});
test('follow-ups preserve both instruments and the selected stress',async()=>{
 const first=await research(snapshot,{question:'Compare QQQ/TQQQ with SMH/SOXL',context});
 const stressed=await research(snapshot,{question:'What if funding reverses?',context:first.context});
 assert.deepEqual(stressed.context.pairs,first.context.pairs);assert.equal(stressed.context.stress,'funding_reversal');
 const shorter=await research(snapshot,{question:'Now use a 7-day hold',context:stressed.context});
 assert.equal(shorter.context.hold,7);assert.equal(shorter.context.stress,'funding_reversal');
 for(const card of shorter.result.cards)assert.equal(card.stress.value,card.cell.stress.funding_reversal);
 assert.match(shorter.result.disclosures.join(' '),/stressed confidence interval and verdict have not been computed/);
 const base=resolveQuestion(snapshot,'Remove the stress test',shorter.context);assert.equal(base.stress,null);
});
test('ranking persists across changes to the holding period',async()=>{
 const rank=await research(snapshot,{question:'Rank the strongest setups',context});
 const shorter=resolveQuestion(snapshot,'Now use a 7-day hold',rank.context);assert.equal(shorter.intent,'rank');
 const supported=resolveQuestion(snapshot,'Show supported setups',context);assert.equal(supported.onlySupported,true);
 const all=resolveQuestion(snapshot,'Rank all setups',{...context,onlySupported:true});assert.equal(all.onlySupported,false);
});
test('non-grid sizes and holds are explicitly disclosed',()=>{
 const plan=resolveQuestion(snapshot,'QQQ/TQQQ at $23k for 11 days',context),result=executePlan(snapshot,plan);
 assert.ok(snapshot.sizes.includes(plan.size));assert.ok(snapshot.holds.includes(plan.hold));assert.match(result.disclosures[0],/requested \$23,000 for 11 days/);
});
test('common instrument names resolve without changing pair identity',()=>{
 assert.deepEqual(resolveQuestion(snapshot,'Compare gold against Tether Gold',context).pairs,['XAU/XAUT']);
 assert.deepEqual(resolveQuestion(snapshot,'Nvidia against NVDL for one week',context).pairs,['NVDA/NVDL']);
 assert.equal(resolveQuestion(snapshot,'Nvidia against NVDL for one week',context).hold,7);
});
test('unsupported instruments, horizons, sizes and shocks fail honestly',()=>{
 for(const question of ['Compare ABC/XYZ with QQQ/TQQQ','QQQ/TQQQ at $-25k','QQQ/TQQQ for -7 days','QQQ/TQQQ for 2 hours','Funding falls 30%','Funding increases 50%','Costs fall 50%','Risk halves','Predict tomorrow’s yield','Place an order now'])assert.throws(()=>resolveQuestion(snapshot,question,context),{name:'Error'});
});
test('AI cannot substitute another pair or stress, or add schema fields',()=>{
 const matched=resolveQuestion(snapshot,'What if funding reverses?',context);
 for(const plan of [{intent:'inspect',pairs:['SMH/SOXL'],stress:'funding_reversal'},{intent:'inspect',pairs:matched.pairs,stress:'half_funding'},{intent:'inspect',pairs:matched.pairs,stress:matched.stress,price:42}])assert.throws(()=>validatePlan(plan,snapshot,matched));
});
test('verified AI planning and explanation use the resolved result',async()=>{
 let calls=0;const fetcher=async(_url,request)=>{const input=JSON.parse(request.body);assert.equal(input.enable_thinking,false);calls++;
  if(calls===1){const resolved=JSON.parse(input.messages.at(-1).content).resolved_scenario;return {ok:true,json:async()=>({choices:[{message:{content:JSON.stringify({intent:'requirements',pairs:resolved.pairs,stress:resolved.stress})}}]})}}
  const supplied=JSON.parse(input.messages.at(-1).content);assert.equal(supplied.result.cards[0].pair,'QQQ/TQQQ');
  return {ok:true,json:async()=>({choices:[{message:{content:JSON.stringify({finding:'The result depends on the recorded carry.',tradeoff:'The hedge leaves residual price risk.',next_check:'Refresh captured depth before relying on the estimate.'})}}]})};
 };
 const response=await research(snapshot,{question:'What is the binding constraint?',context},{BITGET_QWEN_API_KEY:'test-only'},fetcher);
 assert.equal(calls,2);assert.equal(response.planner,'qwen3.8-max');assert.ok(response.commentary);
});
test('numeric AI prose is discarded without losing deterministic evidence',async()=>{
 const fetcher=async()=>({ok:true,json:async()=>({choices:[{message:{content:'{"finding":"Guaranteed 99% return","tradeoff":"None","next_check":"Buy"}'}}]})});
 const response=await research(snapshot,{question:'Why this pair?',context},{BITGET_QWEN_API_KEY:'test-only'},fetcher);
 assert.equal(response.commentary,null);assert.equal(response.planner,'Reef scenario matcher');assert.equal(response.result.cards[0].pair,'QQQ/TQQQ');
});
test('unavailable Qwen does not prevent research',async()=>{
 const response=await research(snapshot,{question:'What if funding halves?',context},{BITGET_QWEN_API_KEY:'test-only'},async()=>{throw Error('Offline')});
 assert.equal(response.context.stress,'half_funding');assert.equal(response.commentary,null);assert.equal(response.result.cards[0].stress.value,response.result.cards[0].cell.stress.half_funding);
});
test('stress explanations cannot imply recomputed support or confidence intervals',async()=>{
 let calls=0;const fetcher=async(_url,request)=>{calls++;const input=JSON.parse(request.body);const matched=JSON.parse(input.messages.at(-1).content);const content=calls===1?{intent:'inspect',pairs:matched.resolved_scenario.pairs,stress:'funding_reversal'}:{finding:'Funding reverses the estimated carry.',tradeoff:'The first pair loses its base support.',next_check:'Verify stressed confidence intervals.'};return {ok:true,json:async()=>({choices:[{message:{content:JSON.stringify(content)}}]})}};
 const reply=await research(snapshot,{question:'What if funding reverses?',context},{BITGET_QWEN_API_KEY:'test-only'},fetcher);
 assert.equal(reply.commentary,null);assert.equal(reply.result.cards[0].cell.verdict,snapshot.pairs.find(p=>p.pair==='QQQ/TQQQ').grid['25000']['30'].verdict);
});
test('Worker research route uses the same recorded results and enforces snapshot identity',async()=>{
 const env={ASSETS:{fetch:async()=>new Response(JSON.stringify(snapshot))}};
 const body={question:'Compare QQQ/TQQQ with SMH/SOXL',context,snapshot_utc:snapshot.generated_utc};
 const response=await worker.fetch(new Request('https://reef.invalid/api/research',{method:'POST',body:JSON.stringify(body)}),env);
 assert.equal(response.status,200);assert.equal((await response.json()).result.cards.length,2);
 const stale=await worker.fetch(new Request('https://reef.invalid/api/research',{method:'POST',body:JSON.stringify({...body,snapshot_utc:'1900-01-01'})}),env);assert.equal(stale.status,409);
});
