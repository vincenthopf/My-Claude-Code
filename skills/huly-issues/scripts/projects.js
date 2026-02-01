#!/usr/bin/env node
// List projects - compact output
import { getClient, closeClient } from './lib/client.js';

try {
  const c = await getClient();
  const projects = await c.findAll('tracker:class:Project', {});

  if (projects.length === 0) {
    console.log('(none)');
  } else {
    projects.forEach(p => console.log(`${p.identifier}: ${p.title}`));
  }
  await closeClient();
} catch (e) {
  console.error(`ERR: ${e.message}`);
  process.exit(1);
}
