#!/usr/bin/env node
// Delete issue
// Usage: node issues-delete.js PROJ-123
import { getClient, closeClient, parseIssueId } from './lib/client.js';

const id = process.argv[2];
if (!id) {
  console.error('Usage: node issues-delete.js PROJ-123');
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

  await c.removeDoc('tracker:class:Issue', issue.space, issue._id);
  console.log(`OK: ${id} deleted`);
  await closeClient();
} catch (e) {
  console.error(`ERR: ${e.message}`);
  process.exit(1);
}
