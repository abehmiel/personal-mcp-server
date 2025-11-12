# Usage Examples and Practical Workflows

This guide provides practical, real-world examples of using your personal MCP server with Claude Desktop. Learn through concrete examples and discover effective workflows.

## Table of Contents

1. [Quick Start Examples](#quick-start-examples)
2. [Indexing Codebases](#indexing-codebases)
3. [Managing Personal Notes](#managing-personal-notes)
4. [Research and Documentation](#research-and-documentation)
5. [Multi-Collection Workflows](#multi-collection-workflows)
6. [Advanced Search Techniques](#advanced-search-techniques)
7. [Common Workflows](#common-workflows)
8. [Best Practices](#best-practices)

---

## Quick Start Examples

### Example 1: Your First Document

**Add a simple document:**

```
Hi Claude! Can you add this document to a collection called "test":

"Python is a high-level, interpreted programming language known for its
simplicity and readability. It supports multiple programming paradigms
including procedural, object-oriented, and functional programming."
```

**Claude's response:**
```
I'll add that document to the "test" collection for you.

[Claude uses add_documents tool]

✅ Successfully added 1 document to the "test" collection.
```

**Search for it:**

```
Search my "test" collection for information about programming paradigms.
```

**Claude's response:**
```
[Claude uses search_documents tool]

I found relevant information about programming paradigms in your collection:

The document mentions that Python supports multiple programming paradigms
including procedural, object-oriented, and functional programming...
```

### Example 2: Check What You Have

**List all collections:**

```
What collections do I have?
```

**Claude's response:**
```
[Claude uses list_collections tool]

You have 1 collection:
- test (1 document)
```

### Example 3: Clean Up

**Delete a collection:**

```
Delete the "test" collection.
```

**Claude's response:**
```
[Claude uses delete_collection tool]

✅ Successfully deleted the "test" collection.
```

---

## Indexing Codebases

### Example: Index a Python Project

**Scenario:** You have a Python project and want Claude to help you understand and work with it.

**Step 1: Prepare your documents**

First, extract relevant code. You might:
- Copy-paste key modules
- Export files as text
- Use a script to concatenate files

**Step 2: Add to a collection**

```
Claude, I want to index my Python project. Let me add some key files
to a collection called "my-python-project".

First, here's my main.py file:
```python
def main():
    """Main entry point for the application."""
    config = load_config()
    app = Application(config)
    app.run()

if __name__ == "__main__":
    main()
```

Can you add that?
```

**Step 3: Add more files**

```
Now add this utils.py file to the same collection:
```python
def load_config():
    """Load configuration from config.yaml."""
    with open('config.yaml', 'r') as f:
        return yaml.safe_load(f)

def validate_input(data):
    """Validate user input data."""
    if not isinstance(data, dict):
        raise ValueError("Input must be a dictionary")
    return data
```
```

**Step 4: Add metadata for organization**

```
Add this database.py file with metadata indicating it's the database layer:
```python
class Database:
    """Database connection handler."""
    def __init__(self, connection_string):
        self.conn = create_connection(connection_string)

    def query(self, sql):
        """Execute a SQL query."""
        return self.conn.execute(sql)
```

Please include metadata: {"type": "database", "layer": "data"}
```

**Step 5: Use your indexed code**

```
Search my "my-python-project" collection for examples of how to load configuration.
```

**Result:** Claude finds and explains the `load_config()` function.

### Example: Index Documentation

```
Claude, I want to add my project's README to the "my-python-project" collection:

# My Awesome Project

This project provides a web API for data processing...

[Installation]
pip install -r requirements.txt

[Usage]
python main.py --config config.yaml

[API Endpoints]
- POST /api/process - Process data
- GET /api/status - Check status
```

**Later, ask:**

```
How do I install and run my project? Check the "my-python-project" collection.
```

**Claude retrieves and explains the installation and usage sections.**

---

## Managing Personal Notes

### Example: Journal Entries

**Create a notes collection:**

```
Add these journal entries to a collection called "journal":

Entry 1: "Today I learned about Python decorators. They're functions that
modify other functions. The @property decorator is particularly useful for
creating getters and setters. Example: @property can make a method accessible
like an attribute."

Entry 2: "Discovered that list comprehensions are faster than loops for
creating lists in Python. Syntax: [expression for item in iterable if condition].
Need to use these more in my code."

Entry 3: "Studied async/await in Python. The asyncio library enables
concurrent programming. Key insight: await pauses execution until the
awaited coroutine completes, but doesn't block the event loop."
```

**Search your notes:**

```
Search my "journal" for notes about Python performance.
```

**Result:** Claude finds Entry 2 about list comprehensions and performance.

```
What did I learn about decorators? Check my journal.
```

**Result:** Claude retrieves Entry 1 with decorator information.

### Example: Meeting Notes

```
Add this meeting note to my "work-notes" collection:

Meeting: Q4 Planning - November 11, 2025

Attendees: Sarah, Mike, Jen, Me

Key Decisions:
- Launch new feature by December 15
- Hire 2 engineers in Q1
- Migrate to microservices architecture

Action Items:
- Me: Draft technical spec by Nov 18
- Sarah: Finalize budget by Nov 20
- Mike: Start recruiting process

Follow-up: Next meeting November 25 to review progress.

Metadata: {"type": "meeting", "date": "2025-11-11", "project": "Q4-planning"}
```

**Later, retrieve:**

```
What were my action items from the Q4 planning meeting?
```

**Claude searches and extracts your action items.**

---

## Research and Documentation

### Example: Research Collection

**Build a research knowledge base:**

```
I'm researching machine learning. Add these key concepts to a collection
called "ml-research":

Document 1: "Supervised Learning: Algorithm learns from labeled training
data. Examples include classification (predicting categories) and regression
(predicting continuous values). Common algorithms: Linear Regression,
Decision Trees, Random Forests, Neural Networks."

Document 2: "Unsupervised Learning: Algorithm finds patterns in unlabeled
data. Types include clustering (grouping similar items) and dimensionality
reduction (simplifying data). Examples: K-Means, PCA, Autoencoders."

Document 3: "Neural Networks: Composed of layers of interconnected nodes
(neurons). Each connection has a weight. Training adjusts weights via
backpropagation. Deep learning uses many layers (deep neural networks)."

Document 4: "Overfitting: Model performs well on training data but poorly
on new data. Solutions include regularization, dropout, more training data,
and simpler models."
```

**Ask conceptual questions:**

```
What's the difference between supervised and unsupervised learning?
Check my "ml-research" collection.
```

**Result:** Claude finds and compares Documents 1 and 2.

```
How do I prevent overfitting in neural networks?
```

**Result:** Claude retrieves Document 4 and explains overfitting solutions.

### Example: Tutorial Collection

```
I'm learning web development. Add this to "web-dev-tutorials":

HTML Basics:
- <html> is the root element
- <head> contains metadata
- <body> contains visible content
- Semantic tags: <article>, <nav>, <section>, <header>, <footer>

CSS Flexbox:
- display: flex; makes element a flex container
- justify-content: aligns items horizontally
- align-items: aligns items vertically
- flex-direction: controls layout direction (row/column)

JavaScript Promises:
- Promise represents eventual completion/failure of async operation
- States: pending, fulfilled, rejected
- .then() handles success, .catch() handles errors
- async/await provides cleaner syntax

React Hooks:
- useState: adds state to functional components
- useEffect: performs side effects
- Custom hooks: reusable stateful logic
```

**Query your tutorials:**

```
How do I align items with CSS Flexbox? Check my tutorials.
```

---

## Multi-Collection Workflows

### Example: Separate Work and Personal

```
# Work collection
Add to "work-code":
[Python code for work project]

# Personal collection
Add to "personal-projects":
[Python code for hobby project]

# Notes collection
Add to "learning":
[Tutorial notes and resources]
```

**Then search specifically:**

```
Search my "work-code" for authentication examples.
```

```
Search my "personal-projects" for game logic.
```

### Example: Organize by Topic

```
Collections:
- "python-basics" - Fundamental Python concepts
- "python-advanced" - Advanced topics (decorators, metaclasses, etc.)
- "python-data" - Data science and analysis
- "python-web" - Web development with Flask/Django
```

**Benefit:** Focused searches, better organization, clearer context.

### Example: Time-Based Collections

```
Collections:
- "notes-2025-q1" - Q1 notes
- "notes-2025-q2" - Q2 notes
- "notes-2025-q3" - Q3 notes
```

**Benefit:** Archive old notes, maintain current context.

---

## Advanced Search Techniques

### Technique 1: Semantic Search

RAG understands meaning, not just keywords:

```
# Query: "How to handle errors"
# Finds: Documents about exceptions, try/catch, error handling,
#        debugging, validation - even without exact phrase
```

**Example:**

```
Search "ml-research" for ways to improve model accuracy.
```

**Finds:**
- Documents about overfitting (accuracy improvement technique)
- Regularization methods
- Data augmentation
- Even though query doesn't mention these terms specifically

### Technique 2: Specific Queries

More specific = better results:

```
# Less specific
"Python"  # Too broad, many matches

# More specific
"Python error handling best practices"  # Focused results

# Very specific
"How to handle FileNotFoundError in Python with context managers"  # Precise match
```

### Technique 3: Multiple Searches

Combine searches for comprehensive understanding:

```
# First search
Search "my-python-project" for database connection code.

# Second search (based on first result)
Search "my-python-project" for where database errors are handled.

# Third search (synthesis)
Search "my-python-project" for examples of database transactions.
```

### Technique 4: Collection Comparison

```
# Compare approaches across collections
Search "work-code" for authentication implementation.
Search "open-source-examples" for authentication implementation.

# Claude, compare these two approaches...
```

---

## Common Workflows

### Workflow 1: Daily Journaling

**Morning:**
```
Add to my "daily-journal":
"November 11, 2025 - Goals for today:
- Complete RAG implementation
- Write documentation
- Review pull requests
Focus area: Stay organized, take breaks."
```

**Evening:**
```
Add to my "daily-journal":
"November 11, 2025 - Accomplishments:
- ✅ Completed RAG implementation
- ✅ Wrote comprehensive docs
- ⚠️ Only reviewed 2 of 5 PRs
Learning: Documentation takes longer than expected.
Tomorrow: Focus on PR reviews first."
```

**Weekly review:**
```
Search my "daily-journal" for accomplishments this week.
```

### Workflow 2: Project Knowledge Base

**Setup phase:**
```
1. Create collection: "project-x"
2. Add README and architecture docs
3. Add key code files
4. Add meeting notes and decisions
```

**Development phase:**
```
# When coding
"Search 'project-x' for examples of API endpoint implementation."

# When onboarding
"Search 'project-x' for authentication flow documentation."

# When debugging
"Search 'project-x' for error handling patterns."
```

**Maintenance phase:**
```
# Update docs as you go
"Add this updated API documentation to 'project-x'..."
```

### Workflow 3: Learning and Research

**Collect information:**
```
# Add articles, tutorials, notes
"Add to 'learning-rust':
Summary of Rust ownership rules from tutorial..."
```

**Study:**
```
# Quiz yourself
"What are Rust's ownership rules? Check my learning-rust collection."

# Connect concepts
"How does Rust's ownership relate to memory safety? Search learning-rust."
```

**Apply:**
```
# Use knowledge in practice
"Give me an example of using ownership in Rust. Check my notes."
```

### Workflow 4: Content Creation

**Research phase:**
```
# Collect sources
Add research notes to "blog-post-rag" collection
```

**Writing phase:**
```
# Reference your research
"What did I learn about vector embeddings? Check blog-post-rag."
"Find my notes on similarity search implementation."
```

**Review phase:**
```
# Check coverage
"What topics have I covered in my blog-post-rag collection?"
```

---

## Best Practices

### Organizing Collections

**DO:**
- ✅ Create separate collections by topic/project
- ✅ Use descriptive collection names
- ✅ Add metadata for filtering (future feature)
- ✅ Keep collections focused and coherent

**DON'T:**
- ❌ Put everything in one giant collection
- ❌ Use vague names like "stuff" or "misc"
- ❌ Mix unrelated topics in one collection
- ❌ Create too many tiny collections (overhead)

### Writing Effective Documents

**DO:**
- ✅ Include context and background
- ✅ Use clear, descriptive language
- ✅ Add dates and sources when relevant
- ✅ Keep documents focused on one topic

**DON'T:**
- ❌ Add extremely short snippets without context
- ❌ Use ambiguous references ("it", "that", "this")
- ❌ Include only code without explanation
- ❌ Mix multiple unrelated concepts

### Crafting Good Search Queries

**DO:**
- ✅ Be specific about what you're looking for
- ✅ Use natural language (RAG understands meaning)
- ✅ Include context in your query
- ✅ Iterate if results aren't relevant

**DON'T:**
- ❌ Use only single keywords
- ❌ Expect exact keyword matches
- ❌ Give up after one search (try rephrasing)
- ❌ Search wrong collection

### Maintaining Your Knowledge Base

**Regular maintenance:**
1. **Review collections monthly**
   - Archive old/irrelevant content
   - Update outdated information
   - Consolidate similar documents

2. **Update as you learn**
   - Add new insights immediately
   - Correct mistakes when discovered
   - Expand thin documentation

3. **Organize proactively**
   - Split large collections when needed
   - Merge sparse collections
   - Rename for clarity

### Performance Tips

1. **Batch additions:**
   ```
   # Instead of one at a time
   Add documents 1, 2, 3, 4, 5 together
   ```

2. **Appropriate collection size:**
   - Small: < 1,000 docs (instant search)
   - Medium: 1,000-10,000 docs (fast search)
   - Large: 10,000+ docs (still fast, but consider splitting by topic)

3. **Descriptive metadata:**
   - Helps with future filtering features
   - Organizes your knowledge
   - Provides context for searches

---

## Real-World Use Cases

### Use Case 1: Software Developer

**Collections:**
- `current-project-backend` - Backend codebase
- `current-project-frontend` - Frontend codebase
- `api-docs` - API documentation
- `team-decisions` - Architecture decisions and meeting notes
- `learning` - Tutorials and new tech research

**Daily workflow:**
```
Morning: Review yesterday's decisions
"What did we decide about the database schema? Check team-decisions."

Coding: Reference patterns
"Show me examples of error handling in our backend. Search current-project-backend."

Learning: Study new tech
"What are the benefits of GraphQL? Check my learning collection."
```

### Use Case 2: Writer/Researcher

**Collections:**
- `research-notes` - Article summaries and key points
- `quotes` - Interesting quotes with sources
- `outlines` - Article/book outlines
- `drafts` - Work in progress
- `published` - Finished pieces

**Workflow:**
```
Research: Collect information
"Add this article summary to research-notes..."

Writing: Reference research
"What are the main arguments for X? Search research-notes."

Editing: Check consistency
"Did I already cover this point? Search drafts."
```

### Use Case 3: Student

**Collections:**
- `cs101-notes` - Computer Science 101
- `math201-notes` - Calculus II
- `physics150-notes` - Physics
- `study-resources` - Textbook summaries, practice problems
- `project-ideas` - Ideas for projects

**Workflow:**
```
Studying: Review concepts
"Explain Big O notation. Check my cs101-notes."

Homework: Find examples
"Show me an example of integration by parts. Search math201-notes."

Projects: Explore ideas
"What project ideas do I have for machine learning? Check project-ideas."
```

---

## Tips for Success

1. **Start small:** Begin with one collection, expand as needed
2. **Be consistent:** Develop naming conventions and stick to them
3. **Add context:** More context = better search results
4. **Experiment:** Try different queries to see what works
5. **Iterate:** Refine your organization over time
6. **Use regularly:** The more you use it, the more valuable it becomes
7. **Keep current:** Update docs as your knowledge evolves

---

## Next Steps

- **Try the examples** - Start with simple documents and searches
- **Develop your workflow** - Find what works for your use case
- **Explore features** - Experiment with different collection structures
- **Share feedback** - Contribute to improving the project

---

**Remember:** The MCP server is your personal knowledge companion. The more you use it, the more powerful it becomes as you build up your indexed knowledge base.

**Document Version:** 1.0
**Last Updated:** 2025-11-11
