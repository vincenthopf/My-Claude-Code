#!/usr/bin/env node
// Full-text search for issues
// Usage: node search.js "query" [--limit N]
import { HULY_URL, HULY_WORKSPACE } from './lib/client.js';

const query = process.argv[2];
const limit = process.argv.includes('--limit')
  ? parseInt(process.argv[process.argv.indexOf('--limit') + 1])
  : 20;

if (!query) {
  console.error('Usage: node search.js "query" [--limit N]');
  process.exit(1);
}

try {
  const searchUrl = `${HULY_URL}:${process.env.HULY_SEARCH_PORT || 4702}/api/v1/search`;

  const response = await fetch(searchUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${process.env.HULY_TOKEN || ''}`
    },
    body: JSON.stringify({
      workspace: HULY_WORKSPACE,
      query,
      classes: ['tracker:class:Issue'],
      limit
    })
  });

  if (!response.ok) {
    console.error(`ERR: Search failed (${response.status})`);
    process.exit(1);
  }

  const data = await response.json();

  if (!data.hits || data.hits.length === 0) {
    console.log('(none)');
  } else {
    console.log(`Found ${data.total}:`);
    data.hits.forEach(h => {
      console.log(`  ${h._id.slice(0, 8)}: ${h.title || '?'} [${h._score.toFixed(1)}]`);
    });
  }
} catch (e) {
  console.error(`ERR: ${e.message}`);
  process.exit(1);
}
