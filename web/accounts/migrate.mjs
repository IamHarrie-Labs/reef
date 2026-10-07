import pg from 'pg';
import {readFile} from 'node:fs/promises';
if(!process.env.REEF_DATABASE_URL)throw Error('Set REEF_DATABASE_URL in the server environment before migrating.');
const pool=new pg.Pool({connectionString:process.env.REEF_DATABASE_URL,connectionTimeoutMillis:10000});
const client=await pool.connect();
try{
 await client.query('BEGIN');
 for(const file of ['auth-schema.sql','schema.sql'])await client.query(await readFile(new URL(file,import.meta.url),'utf8'));
 await client.query('COMMIT');
 console.log('Reef account and notebook tables are ready.');
}catch(error){await client.query('ROLLBACK');throw error}finally{client.release();await pool.end()}
