#!/usr/bin/env node
// List issues with optional filters
// Usage: node issues-list.js [--status X] [--project X] [--limit N]
import { getClient, closeClient } from './lib/client.js';

const args = process.argv.slice(2);
const getArg = (flag) => {
  const i = args.indexOf(flag);
  return i !== -1 && args[i + 1] ? args[i + 1] : null;
};

const status = getArg('--status');
const project = getArg('--project');
const limit = parseInt(getArg('--limit') || '30');

try {
  const c = await getClient();
  const query = {};

  // Get projects for formatting
  const projects = await c.findAll('tracker:class:Project', {});
  const projMap = new Map(projects.map(p => [p._id, p]));

  if (status) query.status = status;
  if (project) {
    const proj = projects.find(p => p.identifier === project.toUpperCase());
    if (proj) query.space = proj._id;
  }

  const issues = await c.findAll('tracker:class:Issue', query, {
    limit,
    sort: { modifiedOn: -1 }
  });

  // Helper to extract short name from refs like "tracker:status:Backlog" -> "Backlog"
  const shortName = (ref) => ref ? ref.split(':').pop() : '';

  if (issues.length === 0) {
    console.log('(none)');
  } else {
    issues.forEach(i => {
      const p = projMap.get(i.space);
      const id = p ? `${p.identifier}-${i.number}` : i._id.slice(0, 8);
      const status = shortName(i.status);
      const pri = i.priority ? ` (${shortName(i.priority)[0]})` : '';
      const who = i.assignee ? ` @${i.assignee}` : '';
      console.log(`${id}: [${status}] ${i.title}${pri}${who}`);
    });
  }
  await closeClient();
} catch (e) {
  console.error(`ERR: ${e.message}`);
  process.exit(1);
}
