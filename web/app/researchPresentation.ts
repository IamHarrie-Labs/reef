type Estimate = {net_bp:number;gross_bp:number;verdict:string;requires?:{binding:string}|null};

/** Display the exported basis-point result as a percentage of reference notional. */
export function holdReturn(basisPoints:number){
 return new Intl.NumberFormat('en-US',{style:'percent',minimumFractionDigits:3,maximumFractionDigits:4,signDisplay:'exceptZero'}).format(basisPoints/10000);
}

export function verdictReason(cell:Estimate|null|undefined){
 if(!cell)return 'The captured order book cannot fill this size. Try a smaller reference size.';
 if(cell.verdict==='SUPPORTED')return 'The risk-adjusted estimate clears the model’s threshold, and its funding-only interval excludes zero.';
 if(cell.verdict==='UNPROVEN')return 'The point estimate clears the threshold, but its funding-only interval still crosses zero.';
 if(cell.net_bp===0)return 'Estimated funding income only offsets execution costs, leaving no net carry.';
 if(cell.net_bp<=0)return cell.gross_bp>0?'Execution costs exceed the estimated funding income.':'Estimated funding income does not cover the trade’s execution costs.';
 if(cell.requires?.binding==='risk')return 'The remaining carry is too small relative to the estimated residual risk.';
 return 'After execution costs, the remaining carry does not clear the model’s risk-adjusted threshold.';
}
