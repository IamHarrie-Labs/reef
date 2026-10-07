// Exercise real PostgreSQL storage inside a rolled-back transaction.
// This checks persistence behavior, not WebAuthn enrollment or browser sessions.
import pg from 'pg';
import {randomUUID} from 'node:crypto';
import assert from 'node:assert/strict';
import {notebookRequest} from './notebooks.mjs';
if(!process.env.REEF_DATABASE_URL)throw Error('Set REEF_DATABASE_URL privately before running the database check.');
const pool=new pg.Pool({connectionString:process.env.REEF_DATABASE_URL,connectionTimeoutMillis:10000});
const client=await pool.connect();
try{
 await client.query('BEGIN');
 const required=['user','session','account','verification','passkey','rateLimit','reef_notebook','reef_signup','reef_signup_limit'];
 const tables=await client.query('SELECT tablename FROM pg_tables WHERE schemaname=current_schema() AND tablename=ANY($1)',[required]);
 assert.deepEqual(tables.rows.map(row=>row.tablename).sort(),required.toSorted(),'Run both reviewed database migrations before activating accounts.');
 const first=randomUUID(),second=randomUUID();
 for(const id of [first,second])await client.query('INSERT INTO "user" (id,name,email,"emailVerified","createdAt","updatedAt") VALUES ($1,$2,$3,false,now(),now())',[id,'Database check',`${id}@test.reef.invalid`]);
 const data={snapshot_utc:'database-check',context:{pairs:['QQQ/TQQQ'],size:25000,hold:30,stress:null},turns:[]};
 const notebook=await notebookRequest(client,first,'PUT',{title:'Rollback check',data});
 assert.deepEqual((await notebookRequest(client,first,'GET',{},notebook.id)).data,data);
 assert.equal((await notebookRequest(client,second,'GET')).notebooks.length,0);
 await assert.rejects(notebookRequest(client,second,'GET',{},notebook.id),e=>e.status===404);
 await assert.rejects(notebookRequest(client,second,'PUT',{title:'Other owner',data,version:1},notebook.id),e=>e.status===409);
 const updated=await notebookRequest(client,first,'PUT',{title:'Updated',data,version:1},notebook.id);
 assert.equal(updated.version,2);
 await assert.rejects(notebookRequest(client,first,'PUT',{title:'Old draft',data,version:1},notebook.id),e=>e.status===409);
 await assert.rejects(notebookRequest(client,second,'DELETE',{},notebook.id),e=>e.status===404);
 await notebookRequest(client,first,'DELETE',{},notebook.id);
 await assert.rejects(notebookRequest(client,first,'GET',{},notebook.id),e=>e.status===404);
 assert.equal((await notebookRequest(client,first,'GET',{trash:true})).notebooks.length,1);
 await assert.rejects(notebookRequest(client,second,'PATCH',{},notebook.id),e=>e.status===404);
 await notebookRequest(client,first,'PATCH',{},notebook.id);
 assert.equal((await notebookRequest(client,first,'GET',{},notebook.id)).title,'Updated');
 console.log('Real database checks passed: save/reopen, owner isolation, stale writes, trash and restore. All test writes rolled back. Passkey enrollment remains a separate browser check.');
}finally{await client.query('ROLLBACK');client.release();await pool.end()}
