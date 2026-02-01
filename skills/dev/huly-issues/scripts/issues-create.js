#!/usr/bin/env node
// Create issue
// Usage: node issues-create.js --project PROJ --title "Title" [--status Todo] [--priority High] [--description "..."]
import { getClient, closeClient } from './lib/client.js';
import corePkg from '@hcengineering/core';
const { generateId } = corePkg;

const args = process.argv.slice(2);
const getArg = (flag) => {
  const i = args.indexOf(flag);
  return i !== -1 && args[i + 1] ? args[i + 1] : null;
};

const project = getArg('--project');
const title = getArg('--title');
const priority = getArg('--priority') || 'NoPriority';
const description = getArg('--description') || '';

if (!project || !title) {
  console.error('Usage: node issues-create.js --project PROJ --title "Title" [--priority High]');
  process.exit(1);
}

try {
  const c = await getClient();

  const projects = await c.findAll('tracker:class:Project', { identifier: project.toUpperCase() });
  if (projects.length === 0) {
    console.error(`ERR: Project ${project} not found`);
    process.exit(1);
  }
  const proj = projects[0];

  // Generate unique issue ID
  const issueId = generateId();

  // Increment project sequence for issue number
  const incResult = await c.updateDoc(
    'tracker:class:Project',
    'core:space:Space',
    proj._id,
    { $inc: { sequence: 1 } },
    true
  );
  const sequence = incResult.object.sequence;

  // Create issue using addCollection
  await c.addCollection(
    'tracker:class:Issue',
    proj._id,
    proj._id,
    proj._class,
    'issues',
    {
      title,
      description,
      status: proj.defaultIssueStatus,
      number: sequence,
      kind: 'tracker:taskTypes:Issue',
      identifier: `${proj.identifier}-${sequence}`,
      priority: `tracker:string:${priority}Priority`,
      assignee: null,
      component: null,
      estimation: 0,
      remainingTime: 0,
      reportedTime: 0,
      reports: 0,
      subIssues: 0,
      parents: [],
      childInfo: [],
      dueDate: null,
      rank: ''
    },
    issueId
  );

  console.log(`OK: ${proj.identifier}-${sequence}`);
  await closeClient();
} catch (e) {
  console.error(`ERR: ${e.message}`);
  process.exit(1);
}
