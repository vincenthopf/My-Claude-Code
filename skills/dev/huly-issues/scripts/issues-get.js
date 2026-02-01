#!/usr/bin/env node
// Get issue details by ID (PROJ-123)
// Usage: node issues-get.js PROJ-123
import { getClient, closeClient, parseIssueId, timeAgo } from './lib/client.js';

const id = process.argv[2];
if (!id) {
  console.error('Usage: node issues-get.js PROJ-123');
  process.exit(1);
}

try {
  const c = await getClient();
  const parsed = parseIssueId(id);
  let issue, project;

  if (parsed) {
    const projects = await c.findAll('tracker:class:Project', { identifier: parsed.project });
    if (projects.length === 0) {
      console.error(`ERR: Project ${parsed.project} not found`);
      process.exit(1);
    }
    project = projects[0];
    issue = await c.findOne('tracker:class:Issue', { space: project._id, number: parsed.number });
  } else {
    issue = await c.findOne('tracker:class:Issue', { _id: id });
    if (issue) {
      const projs = await c.findAll('tracker:class:Project', { _id: issue.space });
      project = projs[0];
    }
  }

  if (!issue) {
    console.error(`ERR: Issue ${id} not found`);
    process.exit(1);
  }

  // Get comments
  const comments = await c.findAll('activity:class:ActivityMessage', { attachedTo: issue._id });

  // Helper to extract short name from refs like "tracker:status:Backlog" -> "Backlog"
  const shortName = (ref) => ref ? ref.split(':').pop() : '';

  // Output
  const issueId = project ? `${project.identifier}-${issue.number}` : id;
  const status = shortName(issue.status);
  const priority = issue.priority ? shortName(issue.priority).replace('Priority', '') : '';
  console.log(`${issueId}: ${issue.title}`);
  console.log(`Status: ${status}${priority ? ` | Pri: ${priority}` : ''}${issue.assignee ? ` | @${issue.assignee}` : ''}`);
  if (issue.estimation) console.log(`Est: ${issue.estimation}h`);
  if (issue.dueDate) console.log(`Due: ${new Date(issue.dueDate).toISOString().split('T')[0]}`);
  console.log('---');
  console.log(issue.description || '(no description)');

  if (comments.length > 0) {
    console.log(`\nComments (${comments.length}):`);
    comments.slice(-5).forEach(c => {
      console.log(`  @${c.modifiedBy || '?'} (${timeAgo(c.modifiedOn)}): ${(c.message || c.text || '').slice(0, 100)}`);
    });
    if (comments.length > 5) console.log(`  ... and ${comments.length - 5} more`);
  }

  await closeClient();
} catch (e) {
  console.error(`ERR: ${e.message}`);
  process.exit(1);
}
