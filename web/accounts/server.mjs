import {betterAuth} from 'better-auth';
import {passkey} from '@better-auth/passkey';
import {magicLink} from 'better-auth/plugins';
import pg from 'pg';
import {createHash,randomBytes,randomUUID} from 'node:crypto';
import {notebookRequest} from './notebooks.mjs';

let instance;
const hash=value=>createHash('sha256').update(value).digest('hex');
export function configured(env=process.env){return !!(env.REEF_DATABASE_URL&&env.BETTER_AUTH_SECRET?.length>=32&&env.BETTER_AUTH_URL)}
export function assertOrigin(origin,env=process.env){if(origin!==new URL(env.BETTER_AUTH_URL).origin)throw Object.assign(new Error('Request origin is not allowed.'),{status:403})}
const cookieName=()=>process.env.BETTER_AUTH_URL?.startsWith('https:')?'__Host-reef-signup':'reef-signup';
const cookieValue=headers=>headers.get('cookie')?.split(';').map(s=>s.trim()).find(s=>s.startsWith(`${cookieName()}=`))?.split('=')[1]||'';
export function services(){
 if(instance)return instance;
 if(!configured())throw Object.assign(new Error('Cloud accounts are not configured yet.'),{status:503});
 const origin=new URL(process.env.BETTER_AUTH_URL).origin;
 if(!origin.startsWith('https://')&&!/^http:\/\/(localhost|127\.0\.0\.1)(:|$)/.test(origin))throw Error('Account hosting requires HTTPS.');
 const pool=new pg.Pool({connectionString:process.env.REEF_DATABASE_URL,max:3,connectionTimeoutMillis:7000,idleTimeoutMillis:20000});
 const recovery=!!(process.env.RESEND_API_KEY&&process.env.REEF_EMAIL_FROM);
 async function email(to,url,subject){const r=await fetch('https://api.resend.com/emails',{method:'POST',headers:{Authorization:`Bearer ${process.env.RESEND_API_KEY}`,'Content-Type':'application/json'},body:JSON.stringify({from:process.env.REEF_EMAIL_FROM,to,subject,text:`${subject}\n\n${url}\n\nIf you did not request this, ignore this email.`}),signal:AbortSignal.timeout(10000)});if(!r.ok)throw Error('The email could not be sent.')}
 async function pending(context,headers){if(typeof context!=='string'||!/^[\da-f-]{36}$/i.test(context))throw Error('Start passkey signup again.');const binding=cookieValue(headers);if(!binding)throw Error('Start passkey signup in this browser.');const r=await pool.query('SELECT id,name FROM reef_signup WHERE id=$1 AND binding_hash=$2 AND expires_at>now() AND consumed_at IS NULL',[context,hash(binding)]);if(!r.rows[0])throw Error('Signup expired. Start again.');return r.rows[0]}
 const auth=betterAuth({appName:'Reef',baseURL:origin,secret:process.env.BETTER_AUTH_SECRET,database:pool,trustedOrigins:[origin],session:{expiresIn:60*60*24*21,freshAge:300},rateLimit:{enabled:true,storage:'database',window:60,max:30},user:{changeEmail:{enabled:recovery},deleteUser:{enabled:false}},...(recovery?{emailVerification:{sendVerificationEmail:async({user,url})=>email(user.email,url,'Verify your Reef recovery email')}}:{}),plugins:[passkey({rpID:new URL(origin).hostname,rpName:'Reef',origin,authenticatorSelection:{residentKey:'required',userVerification:'required'},registration:{requireSession:false,resolveUser:async({ctx,context})=>{const p=await pending(context,ctx.headers||ctx.request.headers);return{id:p.id,name:p.name,displayName:p.name}},afterVerification:async({ctx,context,verification,user})=>{
  if(!verification.registrationInfo?.userVerified)throw Error('Verify with your device PIN, fingerprint or face.');
  const headers=ctx.headers||ctx.request.headers;
  const session=await auth.api.getSession({headers});
  if(session){if(session.user.id!==user.id||Date.now()-new Date(session.session.createdAt).getTime()>300000)throw Error('Sign in again before adding another passkey.');return;}
  const p=await pending(context,headers);
  if(p.id!==user.id)throw Error('Signup does not match this passkey.');
  const consumed=await pool.query('UPDATE reef_signup SET consumed_at=now() WHERE id=$1 AND binding_hash=$2 AND consumed_at IS NULL AND expires_at>now() RETURNING id',[p.id,hash(cookieValue(headers))]);
  if(!consumed.rows.length)throw Error('This signup was already used.');
  const created=await ctx.context.internalAdapter.createUser({id:p.id,name:p.name,email:`${p.id}@accounts.reef.invalid`,emailVerified:false});return {userId:created.id};
 }},authentication:{afterVerification:async({verification})=>{if(!verification.authenticationInfo?.userVerified)throw Error('Verify with your device PIN, fingerprint or face.')}}}),...(recovery?[magicLink({disableSignUp:true,expiresIn:600,sendMagicLink:async({email:to,url})=>email(to,url,'Sign in to your Reef account')})]:[])]});
 instance={auth,pool,recovery,origin};return instance;
}
export async function handle(request,kind){
 const url=new URL(request.url);
 if(kind==='accounts'&&request.method==='GET'&&!configured())return Response.json({enabled:false,recovery:false,user:null});
 const {auth,pool,recovery,origin}=services();
 if(!['GET','HEAD'].includes(request.method))assertOrigin(request.headers.get('origin'));
 if(kind==='auth')return auth.handler(request);
 const session=await auth.api.getSession({headers:request.headers});
 if(kind==='accounts'){
  if(request.method==='GET')return Response.json({enabled:true,recovery,user:session?.user||null,accountOrigin:origin});
  if(request.method!=='POST')return Response.json({error:'Method not allowed.'},{status:405});
  const body=await request.json();
  if(url.searchParams.get('recovery')){
   if(!recovery)throw Object.assign(new Error('Email recovery is unavailable.'),{status:503});
   if(typeof body.email!=='string'||body.email.length>254)throw Object.assign(new Error('Enter your verified recovery email.'),{status:400});
   // Always invoke the auth endpoint to apply its persistent rate limit. Only verified identities receive email.
   const user=await pool.query('SELECT id FROM "user" WHERE email=$1 AND "emailVerified"=true',[body.email.trim().toLowerCase()]);
   const result=await auth.handler(new Request(`${origin}/api/auth/sign-in/magic-link`,{method:'POST',headers:request.headers,body:JSON.stringify({email:user.rows.length?body.email.trim().toLowerCase():`${randomUUID()}@accounts.reef.invalid`,callbackURL:`${origin}/desk`})}));
   if(result.status===429)return result;
   return Response.json({sent:true});
  }
  if(session)throw Object.assign(new Error('You are already signed in.'),{status:409});
  const name=typeof body.name==='string'?body.name.trim():'';
  if(name.length<2||name.length>80)throw Object.assign(new Error('Enter a name of 2 to 80 characters.'),{status:400});
  // A database-backed bucket bounds abandoned signups across function instances.
  const bucket=hash(`${request.headers.get('x-forwarded-for')||'unknown'}:${Math.floor(Date.now()/600000)}`);
  await pool.query("DELETE FROM reef_signup_limit WHERE created_at<now()-interval '1 day'");
  await pool.query('DELETE FROM reef_signup WHERE expires_at<now()');
  const quota=await pool.query('INSERT INTO reef_signup_limit (id,count) VALUES ($1,1) ON CONFLICT(id) DO UPDATE SET count=reef_signup_limit.count+1 RETURNING count',[bucket]);
  if(quota.rows[0].count>10)throw Object.assign(new Error('Please wait before creating another account.'),{status:429});
  const id=randomUUID(),binding=randomBytes(32).toString('hex');
  await pool.query('INSERT INTO reef_signup (id,name,binding_hash,expires_at) VALUES ($1,$2,$3,now()+interval \'10 minutes\')',[id,name,hash(binding)]);
  return Response.json({context:id},{headers:{'Set-Cookie':`${cookieName()}=${binding}; HttpOnly; Path=/; SameSite=Strict; Max-Age=600${origin.startsWith('https:')?'; Secure':''}`}});
 }
 if(kind==='notebooks'){
  const body=['PUT'].includes(request.method)?await request.json():{trash:url.searchParams.get('trash')==='1'};
  return Response.json(await notebookRequest(pool,session?.user.id,request.method,body,url.searchParams.get('id')));
 }
 return Response.json({error:'Not found.'},{status:404});
}
export async function nodeHandler(req,res,kind){
 res.setHeader('Cache-Control','no-store');
 try{const headers=new Headers();for(const [key,value] of Object.entries(req.headers))if(value)headers.set(key,Array.isArray(value)?value.join(','):value);const base=process.env.BETTER_AUTH_URL||'http://localhost:5177';const request=new Request(new URL(req.url,base),{method:req.method,headers,...(!['GET','HEAD'].includes(req.method)?{body:typeof req.body==='string'?req.body:JSON.stringify(req.body||{})}:{})});const response=await handle(request,kind);res.statusCode=response.status;for(const [k,v] of response.headers)if(k!=='set-cookie')res.setHeader(k,v);const cookies=response.headers.getSetCookie();if(cookies.length)res.setHeader('Set-Cookie',cookies);res.end(await response.text())}catch(error){res.statusCode=error.status||500;res.setHeader('Content-Type','application/json');res.end(JSON.stringify({error:error.status?error.message:'Account services are temporarily unavailable. Your local research is retained.'}))}
}
