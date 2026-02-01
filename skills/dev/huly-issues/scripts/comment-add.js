#!/usr/bin/env node
// Add comment to issue
// Usage: node comment-add.js PROJ-123 "Comment text"
import { getClient, closeClient, parseIssueId } from './lib/client.js';

const id = process.argv[2];
const message = process.argv[3];

if (!id || !message) {
  console.error('Usage: node comment-add.js PROJ-123 "Comment text"');
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

  await c.addCollection(
    'activity:class:ActivityMessage',
    issue.space,
    issue._id,
    'tracker:class:Issue',
    'comments',
    { message }
  );

  console.log(`OK: Comment added to ${id}`);
  await closeClient();
} catch (e) {
  console.error(`ERR: ${e.message}`);
  process.exit(1);
}
