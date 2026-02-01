#!/usr/bin/env node
// Test authentication - outputs workspace info or error
import { getClient, closeClient, HULY_WORKSPACE } from './lib/client.js';

try {
  await getClient();
  console.log(`OK: ${HULY_WORKSPACE}`);
  await closeClient();
} catch (e) {
  console.error(`ERR: ${e.message}`);
  process.exit(1);
}
