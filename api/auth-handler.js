module.exports=async(req,res)=>{
 const url=new URL(req.url,'https://getreef.xyz');
 const path=req.query?.authPath||url.searchParams.get('authPath');
 if(typeof path==='string'){
  url.pathname=`/api/auth/${path}`;
  url.searchParams.delete('authPath');
  req.url=url.pathname+url.search;
 }
 const {nodeHandler}=await import('../web/accounts/server.mjs');
 return nodeHandler(req,res,'auth');
};
