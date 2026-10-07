import {test} from 'node:test';
import {strict as assert} from 'node:assert';
import {holdReturn,verdictReason} from '../app/researchPresentation.ts';

test('holding-period percentage preserves sign, units and small nonzero returns',()=>{
 assert.equal(holdReturn(122.6),'+1.226%');
 assert.equal(holdReturn(-362.6),'-3.626%');
 assert.equal(holdReturn(0),'0.000%');
 assert.equal(holdReturn(81),'+0.810%');
 assert.equal(holdReturn(0.01),'+0.0001%');
});
test('a positive but unfavourable estimate is not described as costs exceeding funding',()=>{
 assert.match(verdictReason({verdict:'UNFAVOURABLE',net_bp:30,gross_bp:90,requires:{binding:'cost'}}),/risk-adjusted threshold/);
 assert.match(verdictReason({verdict:'UNFAVOURABLE',net_bp:30,gross_bp:90,requires:{binding:'risk'}}),/residual risk/);
 assert.match(verdictReason({verdict:'UNFAVOURABLE',net_bp:-30,gross_bp:90}),/costs exceed/);
 assert.match(verdictReason({verdict:'UNFAVOURABLE',net_bp:0,gross_bp:90}),/no net carry/);
});
test('uncertainty and unavailable execution remain distinct from a negative return',()=>{
 assert.match(verdictReason({verdict:'UNPROVEN',net_bp:30,gross_bp:90}),/interval still crosses zero/);
 assert.match(verdictReason(null),/cannot fill this size/);
 assert.match(verdictReason({verdict:'SUPPORTED',net_bp:30,gross_bp:90}),/excludes zero/);
});
