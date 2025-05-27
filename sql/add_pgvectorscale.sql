CREATE EXTENSION IF NOT EXISTS vectorscale CASCADE;
CREATE INDEX document_embedding_idx ON document_embedding
USING diskann (embedding vector_cosine_ops);
