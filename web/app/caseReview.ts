export function reviewCase(comparison: [string, number, number][]) {
 const funding=comparison.find(([label])=>label==='Funding carry');
 const cost=comparison.find(([label])=>label==='Execution cost');
 const net=comparison.find(([label])=>label==='Net P&L');
 if(!funding||!cost||!net||[...funding.slice(1),...cost.slice(1),...net.slice(1)].some(n=>typeof n!=='number'||!Number.isFinite(n)))return null;
 return {
  fundingError:Math.abs(funding[2]-funding[1]),
  zeroFundingError:Math.abs(funding[2]),
  costError:Math.abs(cost[2]-cost[1]),
  costDifference:cost[2]-cost[1],
  paperNet:net[2],
  noTradeNet:0,
 };
}
