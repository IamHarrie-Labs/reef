import {useEffect,useRef,useState} from 'react';
import {ArrowRight,Download,RefreshCw,MessageSquare,Info} from 'lucide-react';
import type {FormEvent} from 'react';

type Context={pairs:string[];size:number;hold:number;stress:string|null};
type Cell={verdict:string;gross_bp:number;cost_bp:number;net_bp:number;sharpe:number;ci_lo:number|null;ci_hi:number|null;risk_bp:number;requires?:{binding:string;bp_per_day_now:number;bp_per_day_needed:number;min_hold_days:number|null}};
type Card={pair:string;size:number;hold:number;cell:Cell|null;history_days:number;direction:string;stress:{key:string;label:string;value:number|null;unit:string}|null};
type Reply={schema:string;question:string;snapshot_utc:string;model_version:string;context:Context;planner:string;interpreter:string|null;commentary:{finding:string;tradeoff:string;next_check:string}|null;note:string;result:{title:string;cards:Card[];leading:{pair:string;metric:string}|null;disclosures:string[]}};
type Notebook={snapshot_utc:string;context:Context;turns:Reply[]};
const STORAGE='reef-research-notebook-1';
const value=(n:number|null|undefined,decimals=1)=>n===null||n===undefined?'Unavailable':n.toFixed(decimals);
const verdict=(s:string)=>s==='SUPPORTED'?'Supported':s==='UNPROVEN'?'Unproven':'Unfavourable';

function ResearchResult({reply}:{reply:Reply}){
 const {result}=reply;
 return <div className="research-result"><h3>{result.title}</h3>
 {!result.cards.length?<p className="research-empty">Try the same scenario without the Supported filter, or change the holding period.</p>:<div className="table-scroll"><table className="research-comparison"><caption>Same reference size and holding period across all pairs. Base estimates and stress results are labelled separately.</caption><thead><tr><th>Recorded evidence</th>{result.cards.map(card=><th key={card.pair}>{card.pair}<small>{card.direction}</small></th>)}</tr></thead><tbody>
 <tr><th>Base verdict</th>{result.cards.map(card=><td key={card.pair}>{card.cell?<span className={`badge ${card.cell.verdict.toLowerCase()}`}>{verdict(card.cell.verdict)}</span>:'Book cannot support this size'}</td>)}</tr>
 {([['Gross carry · bp','gross_bp'],['Execution cost · bp','cost_bp'],['Net over hold · bp','net_bp'],['Residual risk · bp','risk_bp'],['Modelled Sharpe proxy','sharpe']] as const).map(([label,key])=><tr key={key}><th>{label}</th>{result.cards.map(card=><td key={card.pair}>{value(card.cell?.[key],key==='sharpe'?2:1)}</td>)}</tr>)}
 <tr><th>Funding-only 95% interval</th>{result.cards.map(card=><td key={card.pair}>{card.cell?.ci_lo!=null&&card.cell?.ci_hi!=null?`${value(card.cell.ci_lo,2)} to ${value(card.cell.ci_hi,2)}`:'Unavailable'}</td>)}</tr>
 <tr><th>Binding constraint</th>{result.cards.map(card=><td key={card.pair}>{card.cell?.requires?.binding||'Unavailable'}</td>)}</tr>
 <tr><th>Carry needed · bp/day</th>{result.cards.map(card=><td key={card.pair}>{value(card.cell?.requires?.bp_per_day_needed,2)}<small>Base estimate · other assumptions fixed</small></td>)}</tr>
 <tr><th>Shortest qualifying hold</th>{result.cards.map(card=><td key={card.pair}>{card.cell?.requires?card.cell.requires.min_hold_days?`${card.cell.requires.min_hold_days} days`:'None within the tested year':'Unavailable'}</td>)}</tr>
 {result.cards.some(card=>card.stress)&&<tr className="research-stress-row"><th>{result.cards[0]?.stress?.label}<small>Stress point estimate only</small></th>{result.cards.map(card=><td key={card.pair}>{value(card.stress?.value,card.stress?.unit==='Sharpe proxy'?2:1)}<small>{card.stress?.unit}</small></td>)}</tr>}
 </tbody></table></div>}
 {result.leading&&<p className="research-leading"><strong>{result.leading.pair}</strong> has the highest {result.leading.metric.toLowerCase()} among these recorded scenarios. Read the constraints before drawing a conclusion.</p>}
 {reply.commentary?<div className="research-interpretation"><span className="eyebrow">{reply.interpreter} · interpretation</span>{Object.entries(reply.commentary).map(([label,text])=><p key={label}><strong>{label==='finding'?'Finding':label==='tradeoff'?'Trade-off':'Next check'}</strong>{text}</p>)}</div>:<p className="research-fallback"><Info size={14}/>{reply.note}</p>}
 <details className="research-sources"><summary>Evidence sources and assumptions</summary><p>Snapshot {reply.snapshot_utc} · model {reply.model_version} · task resolved by {reply.planner}. Financial figures are copied from the Python export. Browser notebook turns are not Bitcoin-anchored.</p><ul>{result.disclosures.map(text=><li key={text}>{text}</li>)}</ul><p>Instrument data: Bitget captured books, funding and hourly prices. This comparison does not establish that the instruments are economically interchangeable.</p></details>
 </div>
}

export function ResearchConversation({snapshotUtc,pair,size,hold,onRefresh,onResolved}:{snapshotUtc:string;pair:string;size:number;hold:number;onRefresh:()=>void;onResolved:(question:string,context:Context)=>void}){
 const initial=():Notebook=>{try{const saved=JSON.parse(localStorage.getItem(STORAGE)||'null');if(saved?.snapshot_utc&&Array.isArray(saved.turns)&&saved.turns.length<=12&&Array.isArray(saved.context?.pairs)&&saved.turns.every((turn:Reply)=>turn.schema==='reef-research-1'&&Array.isArray(turn.result?.cards)))return saved}catch{}return {snapshot_utc:snapshotUtc,context:{pairs:[pair],size,hold,stress:null},turns:[]}};
 const [notebook,setNotebook]=useState<Notebook>(initial),[question,setQuestion]=useState(''),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const [exportPreview,setExportPreview]=useState('');
 const abort=useRef<AbortController|null>(null),latest=useRef<HTMLDivElement>(null);
 const previousSelection=useRef({pair,size,hold});
 const stale=notebook.snapshot_utc!==snapshotUtc;
 useEffect(()=>{try{localStorage.setItem(STORAGE,JSON.stringify(notebook))}catch{}},[notebook]);
 useEffect(()=>()=>abort.current?.abort(),[]);
 useEffect(()=>{const previous=previousSelection.current;previousSelection.current={pair,size,hold};if(previous.pair===pair&&previous.size===size&&previous.hold===hold)return;if(abort.current){abort.current.abort();abort.current=null;setBusy(false);setError('The selected scenario changed. Ask again using the current context.')}if(!stale)setNotebook(n=>({...n,context:{...n.context,pairs:n.context.pairs[0]===pair?n.context.pairs:[pair],size,hold}}))},[pair,size,hold,stale]);
 function reset(){abort.current?.abort();abort.current=null;setBusy(false);setError('');setNotebook({snapshot_utc:snapshotUtc,context:{pairs:[pair],size,hold,stress:null},turns:[]})}
 async function ask(text:string){
  if(busy||stale)return;
  setError('');setBusy(true);setQuestion(text);
  const controller=new AbortController();abort.current=controller;const timeout=setTimeout(()=>controller.abort(),55000);
  try{const response=await fetch('/api/research',{method:'POST',headers:{'content-type':'application/json'},signal:controller.signal,body:JSON.stringify({question:text,context:notebook.context,snapshot_utc:notebook.snapshot_utc,history:notebook.turns.slice(-3).flatMap(turn=>[{role:'user',content:turn.question},{role:'assistant',content:JSON.stringify(turn.context)}])})});const reply=await response.json();if(!response.ok)throw Error(reply.error||'Research is unavailable. Retry this question.');if(reply.schema!=='reef-research-1'||reply.snapshot_utc!==notebook.snapshot_utc)throw Error('The response does not match this notebook’s frozen snapshot. Start a new notebook.');if(controller.signal.aborted)return;setNotebook(n=>({...n,context:reply.context,turns:[...n.turns,reply].slice(-12)}));setQuestion('');onResolved(text,reply.context);requestAnimationFrame(()=>latest.current?.scrollIntoView({behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'nearest'}))}
  catch(e){if(abort.current!==controller)return;setError(e instanceof Error&&e.name!=='AbortError'?e.message:'Research timed out. Your previous turns are retained; retry the question.')}
  finally{clearTimeout(timeout);if(abort.current===controller){setBusy(false);abort.current=null}}
 }
 function submit(e:FormEvent){e.preventDefault();void ask(question)}
 function download(){const report={...notebook,exported_utc:new Date().toISOString(),limits:['A research notebook, not an order or a forecast.','Notebook turns are not Bitcoin-anchored.','All comparisons use the stated frozen snapshot.']};const encoded=JSON.stringify(report,null,2);setExportPreview(encoded);const url=URL.createObjectURL(new Blob([encoded],{type:'application/json'}));const link=document.createElement('a');link.href=url;link.download='reef-research-notebook.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}
 const suggestions=notebook.turns.length?['What if funding reverses?','Now use a 7-day hold','What would need to change?','Remove the stress test']:['Compare QQQ/TQQQ with SMH/SOXL at $25k for 30 days','Rank the strongest setups at $25k for 30 days','Explain this setup’s constraint'];
 return <section className="research-notebook" aria-label="Research conversation"><header><div><span className="eyebrow">YOUR RESEARCH NOTEBOOK</span><h2>Ask. Compare. Challenge the assumption.</h2><p>Follow-up questions keep your instruments and scenario. Every turn uses one dated set of evidence.</p></div><div className="notebook-actions"><button className="outline-button" onClick={reset}><RefreshCw size={14}/> New notebook</button><button className="outline-button" onClick={download} disabled={!notebook.turns.length}><Download size={14}/> Export research</button></div></header>
 <div className="research-context" aria-label="Current research context"><span>{notebook.context.pairs.join(' · ')||'All tracked pairs'}</span><span>${notebook.context.size.toLocaleString()} reference</span><span>{notebook.context.hold}-day hold</span><span>{notebook.context.stress?notebook.context.stress.replaceAll('_',' '):'Base assumptions'}</span><small>Snapshot {notebook.snapshot_utc}</small></div>
 {stale&&<p className="query-message" role="status">This saved notebook uses an older snapshot. You can export it; start a new notebook to research the latest evidence.</p>}
 <div className="research-thread" aria-live="polite" aria-busy={busy}>{notebook.turns.map((reply,index)=><article className="research-turn" key={`${index}-${reply.question}`}><div className="research-question"><MessageSquare size={16}/><p>{reply.question}</p><small>Turn {index+1}</small></div><ResearchResult reply={reply}/></article>)}<div ref={latest}/>{busy&&<div className="research-loading" role="status"><p>Resolving your question and checking the recorded evidence…</p><div className="ai-skeleton"/><div className="ai-skeleton short"/></div>}</div>
 <form onSubmit={submit}><label className="sr-only" htmlFor="notebook-question">Research question or follow-up</label><input id="notebook-question" autoComplete="off" maxLength={700} value={question} onChange={e=>setQuestion(e.target.value)} placeholder={notebook.turns.length?'Change the size, compare another pair, or test an assumption…':'Compare QQQ/TQQQ and SMH/SOXL at $25k for 30 days'} disabled={busy||stale}/><button className="pill-button" disabled={busy||stale||question.trim().length<3} type="submit">{busy?'Investigating…':'Investigate'}<ArrowRight size={16}/></button></form>
 {error&&<div className="query-message" role="alert"><Info size={15}/><span>{error}</span><button className="outline-button" onClick={onRefresh}>Refresh evidence</button></div>}
 <div className="research-suggestions">{suggestions.map(text=><button key={text} disabled={busy||stale} onClick={()=>void ask(text)}>{text}<ArrowRight size={12}/></button>)}</div>
 <p className="research-privacy">Saved in this browser. Each submitted question and recent context are sent to the research service and, when available, Qwen. Up to twelve turns are retained. No account or orders.</p>
 {exportPreview&&<details className="research-export" open><summary>Dated research export</summary><p>Your JSON download was requested. If this browser blocks downloads, select and save the same content below.</p><pre tabIndex={0} aria-label="Exported notebook JSON">{exportPreview}</pre></details>}
 </section>
}
