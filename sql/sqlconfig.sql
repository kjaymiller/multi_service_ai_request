CREATE EXTENSION IF NOT EXISTS vector;
--
-- Table 2: ContentSource
CREATE TABLE ContentSource (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    chunk_size INTEGER NOT NULL,
    input_url TEXT
);

-- Table 1: ContentItem
CREATE TABLE ContentItem (
    id SERIAL PRIMARY KEY,
    source_id INTEGER NOT NULL,
    meta JSONB NOT NULL,
    CONSTRAINT fk_source
      FOREIGN KEY(source_id) 
	  REFERENCES ContentSource(id)
      ON DELETE CASCADE
);

-- Table 3: QuoteEmbeddings
CREATE TABLE QuoteEmbeddings (
    id SERIAL PRIMARY KEY,
    content_item_id INTEGER NOT NULL,
    content_snippet TEXT NOT NULL,
    embedding vector NOT NULL,
    CONSTRAINT fk_content_item
      FOREIGN KEY(content_item_id) 
	  REFERENCES ContentItem(id)
      ON DELETE CASCADE
);
