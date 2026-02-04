# Google Engineering Practices - Code Review Summary

Distilled from Google's public engineering practices documentation.

## The Standard of Code Review

The primary purpose of code review is to ensure the codebase improves over time. All tools and processes serve this goal.

### Key Principle
**A change that improves the overall code health of the system should be approved, even if it isn't perfect.**

No code is perfect. The question is: does this change make the code better than it was?

### Mentoring
Code review is an opportunity for teaching. Share knowledge about language features, design patterns, and codebase conventions. Frame suggestions as learning opportunities, not criticisms.

## What to Look For

### Design
- Does this change belong in this codebase?
- Does it integrate well with the rest of the system?
- Is now the right time to add this functionality?

### Functionality
- Does the code do what the author intended?
- Is what the author intended good for users of this code?
- Think about edge cases, concurrency issues, race conditions.

### Complexity
- Is the code more complex than necessary?
- Could a simpler solution work?
- Will other developers understand this code when they need to modify it?

**Over-engineering**: solving problems that don't exist yet, or making code more generic than needed.

### Tests
- Are the tests correct and sensible?
- Do they test the behavior being implemented?
- Will they fail when the code is broken?
- Will they produce false positives?

### Naming
- Did the developer choose clear names?
- Is a name long enough to communicate what it does, but not so long it's hard to read?

### Comments
- Are comments clear and useful?
- Do they explain *why*, not *what*?
- Are there TODO comments that should be tickets instead?

### Style
- Follow the style guide for the language.
- Don't block on personal style preferences not in the guide.
- If something isn't in the style guide, accept the author's approach.

### Documentation
- If the change affects how users build, test, or interact with the code, update relevant documentation.

### Every Line
- Look at every line of code you've been assigned to review.
- Some things can be scanned (data files, generated code), but human-written code should be examined.

### Context
- Look at the change in context. Is a 4-line function getting added to a 500-line file that's already doing too much?
- Consider the broader impact.

### Good Things
- Tell the developer when they've done something well. Positive reinforcement encourages good practices.

## How to Write Code Review Comments

### Courtesy
- Be kind and respectful.
- Comment on the code, not the developer.
- Never say "you" in a negative context.

### Explain Why
- Share your reasoning. "This is confusing" is less helpful than "I found this confusing because the variable name suggests X but it contains Y."

### Balance Direction
- Point out problems AND help with solutions.
- Don't write the solution for them, but give enough guidance.

### Accept Explanations
- If the developer explains something and it makes sense, consider if the code itself should be clearer.
- "This is explained in the comment below" → maybe the comment should be above, or the code restructured.

## Speed of Code Reviews

### Why Speed Matters
- Slow reviews frustrate developers
- Slow reviews cause code to get stale
- Slow reviews discourage refactoring
- Developers start routing around slow reviewers

### How Fast
- **Maximum**: one business day for initial response
- **Better**: within a few hours
- **Ideal**: immediately when it arrives

### When to Deprioritize
- Focused work should not be interrupted for review
- Between tasks, check for pending reviews

### Large Changes
- If a change is too big to review quickly, ask the author to split it into smaller changes.
- If it can't be split, schedule time to review thoroughly but communicate timeline.

## How to Handle Reviewer Comments

### Think Before Responding
- If you don't understand a comment, ask for clarification.
- If you disagree, explain your reasoning politely.
- Remember: the reviewer is trying to help.

### Fix or Explain
- Every comment should be addressed with either:
  - A code change, or
  - An explanation of why no change is needed

### Don't Take It Personally
- Code review is about the code, not about you.
- Even if a comment seems harsh, assume good intent.

## Resolving Conflicts

### Seek Understanding First
- Make sure you understand each other's perspective.
- Often disagreements stem from miscommunication.

### Escalate Rarely
- Most disputes can be resolved through discussion.
- Escalate only when there's a clear impasse affecting code quality.

### When You're the Reviewer
- Don't approve code you think is problematic.
- But also don't block on personal preference.
- Ask: "Will this harm users or maintainability?" If not, consider approving.

### When You're the Author
- If the reviewer insists on something you disagree with, try it their way.
- You might learn something. Or you'll have evidence for why it doesn't work.

## Emergency Situations

### What Qualifies
- Production is down
- Major security vulnerability
- Legal compliance deadline

### What Changes
- Review can be less thorough
- Post-merge review is acceptable
- But: still don't skip review entirely, just expedite it

### What Doesn't Change
- Code should still be correct
- Tests should still exist
- Security concerns still matter
