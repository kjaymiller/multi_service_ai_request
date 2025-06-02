# Multi-Service AI Coach

A RAG (Retrieval-Augmented Generation) application that allows you to query personal content from multiple sources using vector embeddings and AI-powered responses.

## Overview

This application enables you to:

1. Ingest content from multiple sources
   - [kjaymiller.com/blog](https://kjaymiller.com/blog/)
   - [kjaymiller.com/microblog](https://kjaymiller.com/microblog/)
   - [kjaymiller.com/notes](https://kjaymiller.com/notes/)
   - [Conduit](https://relay.fm/conduit)
2. Store content with vector embeddings in a PostgreSQL database
3. Query your content using hybrid search (keyword + semantic vector similarity)
4. Generate AI-powered responses based on your personal content

## Requirements

- Python 3.8+
- PostgreSQL with `vector` and `pgvectorscale` extension installed
- Environment variables:
  - `POSTGRES_SERVICE_URI` - PostgreSQL connection string

## Installation

1. Clone the repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up your PostgreSQL database:

```bash
psql -d your_database -f sql/sqlconfig.sql
psql -d your_database -f sql/hybrid_search.sql
psql -d your_database -f sql/sources.sql  # Modify this file with your own sources
```

## Usage

### Ingesting Content

The application supports ingesting content from various sources:

```bash
# Ingest a single item
python -m ingest.api item /path/to/file.md --source blog

# Bulk ingest blogs
python -m ingest.api blog /path/to/blog/directory

# Bulk ingest microblogs
python -m ingest.api microblog /path/to/microblog/directory

# Bulk ingest Conduit transcripts
python -m ingest.api conduit /path/to/conduit/directory
```

Content files should be in Markdown format with frontmatter metadata.

### Querying Content

Query your content using the CLI:

```bash
# Simple content search (returns relevant content snippets)
python -m cli.app query "your search query"

# AI-powered response based on your content
python -m cli.app ai "your question about your content"

# Custom system message for the AI
python -m cli.app ai "your question" --system "Your custom system prompt"
```

## Project Structure

- `cli/` - Command-line interface for queries and AI responses
  - `app.py` - CLI commands implementation
  - `db.py` - Database interaction for queries
- `ingest/` - Content ingestion functionality
  - `api.py` - API for content ingestion
- `sql/` - SQL scripts for database setup
  - `sqlconfig.sql` - Database schema
  - `hybrid_search.sql` - Hybrid search function
  - `sources.sql` - Content source configuration

## Architecture

1. **Content Sources** - Define various sources of content in the ContentSource table
2. **Content Items** - Store individual pieces of content with metadata
3. **Embeddings** - Content is split into chunks and embedded using HuggingFace embeddings
4. **Hybrid Search** - Combines keyword search and vector similarity for optimal retrieval
5. **AI Response** - Uses Claude to generate responses based on retrieved content

## Customization

- Modify `sql/sources.sql` to configure your own content sources
- Adjust chunk sizes per source type depending on content length
- Customize the system message in `cli/app.py` to change AI behavior
- Change your LLM with another Langchain supported ChatModel

## Contribution

While contributions are accepted, I do not intend on making this a product intended for adaptation by others. If you fork and run into issues, please file an issue but I can't promise my response my response will resolve the problem.

## License

This project is [MIT licensed](/LICENSE)

This project is based on the [Conduit FastAPI RAG](https://github.com/kjaymiller/conduit-transcripts-fastapi) application.
