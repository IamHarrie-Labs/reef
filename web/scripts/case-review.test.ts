import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {reviewCase} from '../app/caseReview.ts';
test('case baseline errors use the same fixed position and absolute funding error',()=>{
 const result=reviewCase([['Funding carry',-2,1],['Execution cost',4,7],['Net P&L',-6,-20]]);
 assert.deepEqual(result,{fundingError:3,zeroFundingError:1,costError:3,costDifference:3,paperNet:-20,noTradeNet:0});
});
test('missing or invalid observations cannot produce a case comparison',()=>{
 assert.equal(reviewCase([]),null);
 assert.equal(reviewCase([['Funding carry',0,NaN],['Execution cost',4,7],['Net P&L',-6,-20]]),null);
});
test('public case and repository case retain identical committed evidence',()=>{
 const bundle=JSON.parse(fs.readFileSync(new URL('../../data/case_study.json',import.meta.url),'utf8'));
 const publicBundle=JSON.parse(fs.readFileSync(new URL('../public/case-studies/reef-case-1790265456123-AAPL-AAPU-1.json',import.meta.url),'utf8'));
 assert.deepEqual(bundle,publicBundle);
 const result=reviewCase(bundle.comparison)!;
 assert.ok(result.fundingError<result.zeroFundingError);
 assert.ok(result.costDifference>0);
 assert.ok(result.paperNet<0);
});
