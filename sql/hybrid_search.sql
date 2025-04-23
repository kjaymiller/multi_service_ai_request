-- Add a generated column that creates a tsvector from title and description
 ALTER TABLE ContentItem
 ADD COLUMN meta_search_vector tsvector
 GENERATED ALWAYS AS (
     to_tsvector('english',
         COALESCE(meta->>'title', '') || ' ' ||
         COALESCE(meta->>'description', '')
     )
 ) STORED;

 -- Create a GIN index on the tsvector column for fast searching
 CREATE INDEX meta_search_idx ON ContentItem USING GIN (meta_search_vector);

 -- Add a generated column that creates a tsvector from content_snippet
 ALTER TABLE QuoteEmbeddings
 ADD COLUMN snippet_search_vector tsvector
 GENERATED ALWAYS AS (
     to_tsvector('english', COALESCE(content_snippet, ''))
 ) STORED;

 -- Create a GIN index on the tsvector column for fast searching
 CREATE INDEX snippet_search_idx ON QuoteEmbeddings USING GIN (snippet_search_vector);


CREATE OR REPLACE FUNCTION hybrid_search(
     search_text TEXT,
     search_vector VECTOR,
     text_weight FLOAT DEFAULT 0.5,
     vector_weight FLOAT DEFAULT 0.5,
     limit_results INTEGER DEFAULT 20
 ) RETURNS TABLE (
     content_item_id INTEGER,
     content_snippet TEXT,
     title TEXT,
     hybrid_score FLOAT
 ) AS $$
 BEGIN
     RETURN QUERY
     WITH search_query AS (
         SELECT plainto_tsquery('english', search_text) AS text_query
     )
     SELECT
         q.content_item_id,
         q.content_snippet,
         c.meta->>'title' AS title,
         (
             text_weight * GREATEST(
                 ts_rank(q.snippet_search_vector, sq.text_query),
                 ts_rank(c.meta_search_vector, sq.text_query)
             ) +
             vector_weight * (1.0 - (q.embedding <=> search_vector))
         ) AS hybrid_score
     FROM
         QuoteEmbeddings q
     JOIN
         ContentItem c ON q.content_item_id = c.id,
         search_query sq
     WHERE
         (q.snippet_search_vector @@ sq.text_query OR
          c.meta_search_vector @@ sq.text_query OR
          q.embedding <=> search_vector < 0.3)
     ORDER BY
         hybrid_score DESC
     LIMIT limit_results;
 END;
 $$ LANGUAGE plpgsql;
