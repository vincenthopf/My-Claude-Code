#!/usr/bin/env node
// List comments on issue
// Usage: node comments-list.js PROJ-123
import { getClient, closeClient, parseIssueId, timeAgo } from './lib/client.js';

const id = process.argv[2];
if (!id) {
  console.error('Usage: node comments-list.js PROJ-123');
  process.exit(1);
}

try {
  const c = await getClient();
  const parsed = parseIssueId(id);
  let issue;

  if (parsed) {
    const projects = await c.findAll('tracker:class:Project', { identifier: parsed.project });
    if (projects.length === 0) {
      console.error(`ERR: Project ${parsed.project} not found`);
      process.exit(1);
    }
    issue = await c.findOne('tracker:class:Issue', { space: projects[0]._id, number: parsed.number });
  } else {
    issue = await c.findOne('tracker:class:Issue', { _id: id });
  }

  if (!issue) {
    console.error(`ERR: Issue ${id} not found`);
    process.exit(1);
  }

  const comments = await c.findAll('activity:class:ActivityMessage', { attachedTo: issue._id });

  if (comments.length === 0) {
    console.log('(none)');
  } else {
    comments.forEach(c => {
      console.log(`@${c.modifiedBy || '?'} (${timeAgo(c.modifiedOn)}): ${c.message || c.text || ''}`);
    });
  }

  await closeClient();
} catch (e) {
  console.error(`ERR: ${e.message}`);
  process.exit(1);
}
