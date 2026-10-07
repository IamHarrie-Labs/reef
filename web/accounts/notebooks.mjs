import {randomUUID} from 'node:crypto';

export function validateNotebook(data) {
  if (!data || typeof data.snapshot_utc !== 'string' || data.snapshot_utc.length > 80 || !Array.isArray(data.turns) || data.turns.length > 200) throw Object.assign(new Error('Invalid notebook.'), {status:400});
  const c=data.context;
  if (!c || !Array.isArray(c.pairs) || c.pairs.length>50 || c.pairs.some(p=>typeof p!=='string'||p.length>100) || !Number.isFinite(c.size) || c.size<=0 || !Number.isFinite(c.hold) || c.hold<=0 || !(c.stress===null||typeof c.stress==='string')) throw Object.assign(new Error('Invalid scenario.'),{status:400});
  if (data.turns.some(t=>t?.schema!=='reef-research-1'||typeof t.question!=='string'||t.question.length>700||typeof t.snapshot_utc!=='string'||!Array.isArray(t.result?.cards))) throw Object.assign(new Error('Invalid research record.'),{status:400});
  if (Buffer.byteLength(JSON.stringify(data))>2_000_000) throw Object.assign(new Error('This notebook is too large. Export it and start another notebook.'),{status:413});
  return {snapshot_utc:data.snapshot_utc,context:data.context,turns:data.turns};
}

export async function notebookRequest(pool,userId,method,body={},id=null) {
  if (!userId) throw Object.assign(new Error('Sign in to access saved notebooks.'),{status:401});
  if (id&&!/^[\da-f-]{36}$/i.test(id)) throw Object.assign(new Error('Invalid notebook identifier.'),{status:400});
  if (method==='GET') {
    const result=id?await pool.query('SELECT id,title,version,data,updated_at FROM reef_notebook WHERE id=$1 AND user_id=$2 AND deleted_at IS NULL',[id,userId]):await pool.query(`SELECT id,title,version,updated_at FROM reef_notebook WHERE user_id=$1 AND deleted_at IS ${body.trash?'NOT ':''}NULL ORDER BY updated_at DESC`,[userId]);
    if(id&&!result.rows.length)throw Object.assign(new Error('Notebook not found.'),{status:404});
    return id?result.rows[0]:{notebooks:result.rows};
  }
  if(method==='PATCH') {
    if(!id)throw Object.assign(new Error('Choose a notebook.'),{status:400});
    const result=await pool.query('UPDATE reef_notebook SET deleted_at=NULL,updated_at=now(),version=version+1 WHERE id=$1 AND user_id=$2 AND deleted_at IS NOT NULL RETURNING id',[id,userId]);
    if(!result.rows.length)throw Object.assign(new Error('Notebook not found.'),{status:404});
    return {restored:true};
  }
  if(method==='DELETE') {
    if(!id)throw Object.assign(new Error('Choose a notebook.'),{status:400});
    const result=await pool.query('UPDATE reef_notebook SET deleted_at=now(),updated_at=now(),version=version+1 WHERE id=$1 AND user_id=$2 AND deleted_at IS NULL RETURNING id',[id,userId]);
    if(!result.rows.length)throw Object.assign(new Error('Notebook not found.'),{status:404});
    return {deleted:true};
  }
  if(method!=='PUT')throw Object.assign(new Error('Method not allowed.'),{status:405});
  const title=typeof body.title==='string'?body.title.trim():'';
  if(!title||title.length>100)throw Object.assign(new Error('Use a notebook name of 1 to 100 characters.'),{status:400});
  const data=validateNotebook(body.data);
  if(!id){
    const newId=randomUUID();
    const result=await pool.query('INSERT INTO reef_notebook (id,user_id,title,data) VALUES ($1,$2,$3,$4) RETURNING id,title,version,updated_at',[newId,userId,title,JSON.stringify(data)]);
    return result.rows[0];
  }
  if(!Number.isInteger(body.version)||body.version<1)throw Object.assign(new Error('Missing notebook version.'),{status:400});
  const result=await pool.query('UPDATE reef_notebook SET title=$3,data=$4,version=version+1,updated_at=now() WHERE id=$1 AND user_id=$2 AND version=$5 AND deleted_at IS NULL RETURNING id,title,version,updated_at',[id,userId,title,JSON.stringify(data),body.version]);
  if(!result.rows.length)throw Object.assign(new Error('This notebook changed on another device. Open the latest version or save this draft as a new notebook.'),{status:409});
  return result.rows[0];
}
