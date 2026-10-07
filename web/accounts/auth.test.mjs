import {test} from 'node:test';
import assert from 'node:assert/strict';
import {configured,assertOrigin,handle} from './server.mjs';
test('accounts remain disabled without durable storage, a secret and a fixed origin',()=>{assert.equal(configured({}),false);assert.equal(configured({REEF_DATABASE_URL:'postgres://test',BETTER_AUTH_SECRET:'short',BETTER_AUTH_URL:'https://reef.example'}),false);assert.equal(configured({REEF_DATABASE_URL:'postgres://test',BETTER_AUTH_SECRET:'x'.repeat(32),BETTER_AUTH_URL:'https://reef.example'}),true)});
test('same-origin mutation policy rejects unrelated and missing origins',()=>{const env={BETTER_AUTH_URL:'https://reef.example'};assert.doesNotThrow(()=>assertOrigin('https://reef.example',env));assert.throws(()=>assertOrigin('https://other.example',env),e=>e.status===403);assert.throws(()=>assertOrigin(null,env),e=>e.status===403)});
test('unconfigured account discovery does not contact a database or advertise saving',async()=>{const response=await handle(new Request('http://localhost:5177/api/accounts'),'accounts');assert.deepEqual(await response.json(),{enabled:false,recovery:false,user:null})});
