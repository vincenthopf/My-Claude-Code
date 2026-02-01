#!/usr/bin/env node
// Update issue
// Usage: node issues-update.js PROJ-123 [--status Done] [--priority High] [--title "New title"]
import { getClient, closeClient, parseIssueId } from './lib/client.js';

const id = process.argv[2];
const args = process.argv.slice(3);
const getArg = (flag) => {
  const i = args.indexOf(flag);
  return i !== -1 && args[i + 1] ? args[i + 1] : null;
};

if (!id) {
  console.error('Usage: node issues-update.js PROJ-123 --status Done');
  process.exit(1);
}

const status = getArg('--status');
const priority = getArg('--priority');
const title = getArg('--title');
const description = getArg('--description');

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

  // Map friendly names to Huly refs
  const statusMap = {
    'backlog': 'tracker:status:Backlog',
    'todo': 'tracker:status:Todo',
    'in progress': 'tracker:status:InProgress',
    'inprogress': 'tracker:status:InProgress',
    'done': 'tracker:status:Done',
    'canceled': 'tracker:status:Canceled',
    'cancelled': 'tracker:status:Canceled'
  };
  const priorityMap = {
    'no priority': 'tracker:string:NoPriorityPriority',
    'nopriority': 'tracker:string:NoPriorityPriority',
    'low': 'tracker:string:LowPriority',
    'medium': 'tracker:string:MediumPriority',
    'high': 'tracker:string:HighPriority',
    'urgent': 'tracker:string:UrgentPriority'
  };

  const ops = {};
  if (status) ops.status = statusMap[status.toLowerCase()] || status;
  if (priority) ops.priority = priorityMap[priority.toLowerCase()] || priority;
  if (title) ops.title = title;
  if (description) ops.description = description;

  if (Object.keys(ops).length === 0) {
    console.error('ERR: No updates specified');
    process.exit(1);
  }

  await c.updateDoc('tracker:class:Issue', issue.space, issue._id, ops);
  console.log(`OK: ${id} updated`);
  await closeClient();
} catch (e) {
  console.error(`ERR: ${e.message}`);
  process.exit(1);
}
