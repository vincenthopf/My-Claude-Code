// Shared Huly client connection
// This module is imported by other scripts - keeps connection logic DRY

import pkg from '@hcengineering/api-client';
const { connect } = pkg;
import { config } from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { existsSync } from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const envPath = join(__dirname, '..', '..', '.env');

if (existsSync(envPath)) {
  config({ path: envPath });
}

export const HULY_URL = process.env.HULY_URL || 'http://huly.local';
export const HULY_EMAIL = process.env.HULY_EMAIL;
export const HULY_PASSWORD = process.env.HULY_PASSWORD;
export const HULY_WORKSPACE = process.env.HULY_WORKSPACE;

let clientInstance = null;

export async function getClient() {
  if (clientInstance) return clientInstance;

  if (!HULY_EMAIL || !HULY_PASSWORD || !HULY_WORKSPACE) {
    console.error('ERR: Set HULY_EMAIL, HULY_PASSWORD, HULY_WORKSPACE in .env');
    process.exit(1);
  }

  clientInstance = await connect(HULY_URL, {
    email: HULY_EMAIL,
    password: HULY_PASSWORD,
    workspace: HULY_WORKSPACE
  });
  return clientInstance;
}

export async function closeClient() {
  if (clientInstance) {
    await clientInstance.close();
    clientInstance = null;
  }
}

// Parse issue ID (PROJ-123) to {project, number}
export function parseIssueId(id) {
  const match = id.match(/^([A-Z]+)-(\d+)$/i);
  if (!match) return null;
  return { project: match[1].toUpperCase(), number: parseInt(match[2]) };
}

// Compact time format
export function timeAgo(ts) {
  const s = Math.floor((Date.now() - ts) / 1000);
  if (s < 60) return `${s}s`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h`;
  return `${Math.floor(h / 24)}d`;
}
