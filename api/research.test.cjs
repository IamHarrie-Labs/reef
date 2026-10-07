const {test,beforeEach,afterEach}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const handler=require('./research.js');
const snapshot=JSON.parse(fs.readFileSync('web/web_export.json'));
const originalFetch=global.fetch,originalKey=process.env.BITGET_QWEN_API_KEY;
beforeEach(()=>{delete process.env.BITGET_QWEN_API_KEY;global.fetch=async()=>{throw Error('Network is disabled in this test')}});
afterEach(()=>{global.fetch=originalFetch;if(originalKey===undefined)delete process.env.BITGET_QWEN_API_KEY;else process.env.BITGET_QWEN_API_KEY=originalKey});
async function invoke(body,method='POST'){
 const response={code:200,headers:{},setHeader(k,v){this.headers[k]=v},status(code){this.code=code;return this},json(payload){this.payload=payload;return this}};
 await handler({method,body,headers:{'x-forwarded-for':'unit-test'},socket:{}},response);return response;
}
const body=()=>({snapshot_utc:snapshot.generated_utc,question:'Compare QQQ/TQQQ with SMH/SOXL',context:{pairs:['QQQ/TQQQ'],size:25000,hold:30,stress:null}});
test('Vercel route serves reproducible comparisons without an upstream model',async()=>{
 const result=await invoke(body());assert.equal(result.code,200);assert.equal(result.payload.result.cards.length,2);assert.equal(result.payload.interpreter,null);assert.equal(result.headers['Cache-Control'],'no-store');
});
test('Vercel route refuses a different snapshot instead of mixing evidence',async()=>{
 const result=await invoke({...body(),snapshot_utc:'1900-01-01'});assert.equal(result.code,409);
});
test('Vercel route rejects malformed requests and unsupported methods',async()=>{
 assert.equal((await invoke('{bad')).code,400);assert.equal((await invoke({})).code,400);assert.equal((await invoke({question:'Compare QQQ/TQQQ'})).code,400);assert.equal((await invoke(body(),'GET')).code,405);
 assert.equal((await invoke({...body(),question:'Place an order now'})).code,400);
 assert.equal((await invoke({...body(),history:'x'.repeat(15000)})).code,400);
});
