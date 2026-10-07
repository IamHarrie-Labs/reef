// Clean-path routing (/desk/evidence) on top of the History API.
export const ROUTE_EVENT='reef-route';
export const currentRoute=()=>(window.location.pathname.replace(/\/+$/,'')||'/')+window.location.search;
export const routeParams=()=>new URLSearchParams(window.location.search);
export function navigate(to:string,replace=false){if(replace)window.history.replaceState(null,'',to);else window.history.pushState(null,'',to);window.dispatchEvent(new Event(ROUTE_EVENT))}
export function onRoute(fn:()=>void){window.addEventListener(ROUTE_EVENT,fn);window.addEventListener('popstate',fn);return()=>{window.removeEventListener(ROUTE_EVENT,fn);window.removeEventListener('popstate',fn)}}
export function installRouter(){
  // Links shared before the move used #/desk; keep them working.
  if(window.location.hash.startsWith('#/'))window.history.replaceState(null,'',window.location.hash.slice(1)||'/');
  document.addEventListener('click',event=>{
    if(event.defaultPrevented||event.button!==0||event.metaKey||event.ctrlKey||event.shiftKey||event.altKey)return;
    const link=(event.target as Element|null)?.closest?.('a');
    if(!link||link.target||link.hasAttribute('download'))return;
    const href=link.getAttribute('href');
    if(!href||!href.startsWith('/')||href.startsWith('//')||href.startsWith('/api/'))return;
    event.preventDefault();
    if(href!==window.location.pathname+window.location.search)navigate(href);
  });
}
