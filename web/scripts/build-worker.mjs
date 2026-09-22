import {copyFileSync,mkdirSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
const root=fileURLToPath(new URL('..',import.meta.url));
mkdirSync(`${root}/dist/server`,{recursive:true});
copyFileSync(`${root}/worker/index.js`,`${root}/dist/server/index.js`);
