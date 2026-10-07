/** Shared lockup for navigation, mobile menus and the site footer. */
export function ReefMark({size=32}:{size?:number}){
 return <img className="reef-mark" src="/brand/reef-seal.svg" width={size} height={size} alt="" aria-hidden="true"/>;
}

export function ReefLogo(){
 return <a className="logo" href="/" aria-label="Reef home"><ReefMark/><span>Reef</span></a>;
}
