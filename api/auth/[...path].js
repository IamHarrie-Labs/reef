module.exports=async(req,res)=>{const {nodeHandler}=await import('../../web/accounts/server.mjs');return nodeHandler(req,res,'auth')};
