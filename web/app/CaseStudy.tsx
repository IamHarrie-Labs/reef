import {Download,ShieldCheck} from 'lucide-react';
import {useEffect,useState} from 'react';

export type CaseEvidence={key:string;selection:string;earlier_ineligible_records:number;prediction:{evidence:{pair:string;size:number;hold_days:number;verdict:string}};prediction_anchor:{bitcoin_header:{height:number}};timeline:Record<string,number>;comparison:[string,number,number][];limits:string[]};

const time=(ms:number)=>new Date(ms).toISOString().replace('T',' ').replace('Z',' UTC');
export function CaseStudy({bundle:supplied}:{bundle?:CaseEvidence|null}){
 const [portable,setPortable]=useState<CaseEvidence|null>(null);
 useEffect(()=>{if(supplied)return;const controller=new AbortController();fetch(`${import.meta.env.BASE_URL}case-studies/reef-case-1790265456123-AAPL-AAPU-1.json`,{signal:controller.signal}).then(r=>{if(!r.ok)throw Error();return r.json()}).then(b=>{if(!controller.signal.aborted&&b.key==='1790265456123:AAPL/AAPU:1')setPortable(b)}).catch(()=>{});return()=>controller.abort()},[supplied]);
 const bundle=supplied||portable;
 if(!bundle)return null;
 const ev=bundle.prediction.evidence;
 const filename=`reef-case-${bundle.key.replaceAll(':','-').replaceAll('/','-')}.json`;
 return <section className="shadow-desk case-study" aria-label="Verifiable case study"><div className="panel-top"><div><span className="eyebrow">ONE RECORD · FROM PREDICTION TO OUTCOME</span><h2>{ev.pair} · ${ev.size.toLocaleString()} · {ev.hold_days}-day hold</h2></div><a className="outline-button" href={`${import.meta.env.BASE_URL}case-studies/${filename}`} download={filename}><Download size={16}/> Download proof bundle</a></div>
 <p className="case-intro">{bundle.selection} Earlier ineligible records: {bundle.earlier_ineligible_records}. Frozen verdict: <strong>{ev.verdict.toLowerCase()}</strong>.</p>
 <ol className="case-timeline">{[['Prediction recorded','recorded_ms'],[`Prediction in Bitcoin block ${bundle.prediction_anchor.bitcoin_header.height}`,'bitcoin_ms'],['Holding period ended','maturity_ms'],['Hypothetical exit recorded','exit_ms'],['Outcome in Bitcoin','outcome_bitcoin_ms']].map(([label,key])=><li key={key}><span>{label}</span><time>{time(bundle.timeline[key])}</time></li>)}</ol>
 <div className="table-scroll"><table><thead><tr><th>Basis points of reference notional</th><th>Frozen estimate</th><th>Observed in paper execution</th></tr></thead><tbody>{bundle.comparison.map(([label,predicted,observed])=><tr key={label}><td>{label}</td><td>{predicted.toFixed(2)} bp</td><td>{observed.toFixed(2)} bp</td></tr>)}</tbody></table></div>
 <p className="ledger-note"><ShieldCheck size={14}/> The bundle includes both records, funding history, settlement marks, Merkle paths, original OpenTimestamps proofs and Bitcoin headers. Its verifier recomputes the result and checks proof inclusion and timing.</p>
 <details className="case-limits"><summary>How to verify, and what the proof does not establish</summary><p>Save the bundle, install <code>requirements-proof.txt</code> from the repository, then run <code>python src/case_study.py --verify PATH_TO_BUNDLE --online</code>. Online verification checks the block hashes at their stated heights with two public explorers. Offline verification checks the included headers only.</p><ul>{bundle.limits.map(limit=><li key={limit}>{limit}</li>)}</ul></details>
 </section>
}
