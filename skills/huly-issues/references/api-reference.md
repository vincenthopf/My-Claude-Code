# Huly API Reference

Detailed API documentation for advanced usage and troubleshooting.

## Architecture Overview

Huly uses a hybrid architecture:
- **REST API**: Authentication, search, backups
- **WebSocket/Client API**: Document CRUD operations (issues, projects, comments)

The CLI wraps both APIs transparently.

## Data Models

### Issue (`tracker:class:Issue`)

```typescript
interface Issue {
  _id: string;                    // Unique ID
  _class: 'tracker:class:Issue';  // Class identifier
  space: string;                  // Project space ID
  number: number;                 // Issue number within project
  title: string;                  // Required
  description?: string;           // Markdown content
  status: IssueStatus;            // Required
  priority?: IssuePriority;
  assignee?: string;              // User reference
  labels?: string[];
  estimation?: number;            // Hours
  remainingTime?: number;         // Hours
  dueDate?: number;               // Timestamp
  modifiedOn: number;             // Last modified timestamp
  modifiedBy: string;             // User who modified
}

type IssueStatus = 'Backlog' | 'Todo' | 'In Progress' | 'Done' | 'Canceled';
type IssuePriority = 'No priority' | 'Low' | 'Medium' | 'High' | 'Urgent';
```

### Project (`tracker:class:Project`)

```typescript
interface Project {
  _id: string;
  _class: 'tracker:class:Project';
  title: string;                  // Required
  identifier: string;             // Required, max 5 uppercase chars (e.g., "PROJ")
  description?: string;
  private?: boolean;              // Default: false
  autoJoin?: boolean;             // Default: true
  defaultIssueStatus?: string;    // Default status for new issues
  owners?: string[];              // User references
  members?: string[];             // User references
}
```

### Activity Message (Comments)

```typescript
interface ActivityMessage {
  _id: string;
  _class: 'activity:class:ActivityMessage';
  attachedTo: string;             // Parent object ID
  attachedToClass: string;        // Parent class (e.g., 'tracker:class:Issue')
  collection: string;             // Collection name (e.g., 'comments')
  message: string;                // Comment text
  modifiedOn: number;
  modifiedBy: string;
}
```

## Client API Methods

### Connection

```typescript
import { connect } from '@hcengineering/api-client';

const client = await connect('http://huly.local', {
  email: 'user@example.com',
  password: 'password',
  workspace: 'my-workspace'
});

// Always close when done
await client.close();
```

### Query Documents

```typescript
// Find all matching documents
const issues = await client.findAll(
  'tracker:class:Issue',
  { status: 'In Progress' },       // Query filter
  {
    limit: 50,                     // Max results
    sort: { modifiedOn: -1 },      // Sort descending
    // lookup: { ... },            // Join related docs
    // projection: { ... }         // Select fields
  }
);

// Find single document
const issue = await client.findOne('tracker:class:Issue', { _id: issueId });
```

### Create Documents

```typescript
const issueId = await client.createDoc(
  'tracker:class:Issue',           // Class
  projectSpaceId,                  // Space (project ID)
  {
    title: 'New issue',
    status: 'Todo',
    priority: 'High',
    description: 'Description here'
  }
);
```

### Update Documents

```typescript
await client.updateDoc(
  'tracker:class:Issue',
  spaceId,
  issueId,
  {
    status: 'Done',
    priority: 'Low'
  }
);
```

### Delete Documents

```typescript
await client.removeDoc('tracker:class:Issue', spaceId, issueId);
```

### Collections (Comments/Attachments)

```typescript
// Add comment to issue
await client.addCollection(
  'activity:class:ActivityMessage',  // Class to create
  issueSpace,                        // Space
  issueId,                           // Parent ID (attachedTo)
  'tracker:class:Issue',             // Parent class (attachedToClass)
  'comments',                        // Collection name
  { message: 'My comment' }          // Attributes
);

// Get comments on issue
const comments = await client.findAll(
  'activity:class:ActivityMessage',
  { attachedTo: issueId }
);

// Update comment
await client.updateCollection(
  'activity:class:ActivityMessage',
  space, commentId,
  issueId, 'tracker:class:Issue', 'comments',
  { message: 'Updated comment' }
);

// Delete comment
await client.removeCollection(
  'activity:class:ActivityMessage',
  space, commentId,
  issueId, 'tracker:class:Issue', 'comments'
);
```

## REST API Endpoints

### Authentication (Port 3000)

```bash
# Login
curl -X POST http://huly.local:3000/api/v1/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "pass"}'
# Response: { "token": "eyJ...", "workspaces": [...] }

# Verify token
curl -X GET http://huly.local:3000/api/v1/verify \
  -H "Authorization: Bearer TOKEN"
```

### Full-text Search (Port 4702)

```bash
curl -X POST http://huly.local:4702/api/v1/search \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "workspace": "workspace-id",
    "query": "search text",
    "classes": ["tracker:class:Issue"],
    "limit": 20,
    "from": 0
  }'
# Response: { "hits": [...], "total": 42 }
```

## Error Handling

Common errors and solutions:

| Error | Cause | Solution |
|-------|-------|----------|
| `Missing configuration` | .env not set | Copy .env.example to .env |
| `Connection refused` | Huly not running | Start Huly services |
| `Authentication failed` | Wrong credentials | Check email/password |
| `Project not found` | Invalid identifier | Use `projects` command to list |
| `Issue not found` | Wrong ID format | Use PROJ-123 format |

## Query Operators

Advanced query filters:

```typescript
// Exact match
{ status: 'Done' }

// Multiple values (OR)
{ status: { $in: ['Done', 'Canceled'] } }

// Not equal
{ status: { $ne: 'Backlog' } }

// Greater than
{ estimation: { $gt: 4 } }

// Less than or equal
{ modifiedOn: { $lte: Date.now() } }

// Exists
{ assignee: { $exists: true } }
```
