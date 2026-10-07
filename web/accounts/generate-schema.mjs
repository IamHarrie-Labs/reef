import {getAuthTables} from 'better-auth/db';
import {passkey} from '@better-auth/passkey';
import {writeFileSync} from 'node:fs';
// Generate from the installed, lockfile-pinned authentication schema without connecting to a database.
const tables=getAuthTables({plugins:[passkey()],rateLimit:{storage:'database'}});
const quote=name=>'"'+name.replaceAll('"','""')+'"';
const sql=['-- Generated from Better Auth and @better-auth/passkey 1.7.7. Review before applying.'];
for(const [key,table] of Object.entries(tables).sort(([,a],[,b])=>(a.order||10)-(b.order||10))){
 const columns=['"id" text PRIMARY KEY'];
 for(const [field,definition] of Object.entries(table.fields)){
  const name=definition.fieldName||field;
  const type=definition.type==='date'?'timestamptz':definition.type==='boolean'?'boolean':definition.type==='number'?(definition.bigint?'bigint':'double precision'):'text';
  let column=`${quote(name)} ${type}${definition.required?' NOT NULL':''}${definition.unique?' UNIQUE':''}`;
  if(definition.references)column+=` REFERENCES ${quote(tables[definition.references.model]?.modelName||definition.references.model)}(${quote(definition.references.field)}) ON DELETE CASCADE`;
  columns.push(column);
 }
 sql.push(`CREATE TABLE IF NOT EXISTS ${quote(table.modelName||key)} (\n ${columns.join(',\n ')}\n);`);
 for(const [field,definition] of Object.entries(table.fields))if(definition.index)sql.push(`CREATE INDEX IF NOT EXISTS ${quote(`${key}_${field}_idx`)} ON ${quote(table.modelName||key)}(${quote(definition.fieldName||field)});`);
}
sql.push('CREATE UNIQUE INDEX IF NOT EXISTS "passkey_credential_unique" ON "passkey"("credentialID");');
writeFileSync(new URL('./auth-schema.sql',import.meta.url),sql.join('\n\n')+'\n');
