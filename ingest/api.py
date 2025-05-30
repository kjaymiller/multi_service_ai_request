import datetime
import json
import logging
import os
import pathlib
from enum import Enum
from typing import Any, Dict

import frontmatter
import psycopg
import typer
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from psycopg.rows import dict_row

app = typer.Typer()

db_connection = psycopg.connect(
    os.getenv("POSTGRES_SERVICE_URI"),
    row_factory=dict_row,
)


class Source(Enum):
    conduit = "conduit"
    blog = "blog"
    microblog = "microblog"
    youtube = "youtube"
    guest_podcast = "guest_podcast"
    conference_talk = "conference_talk"
    notes_to_self = "notes_to_self"


chunk_size = {
    "conduit": 300,
    "blog": 500,
    "microblog": 0,
    "youtube": 300,
    "guest_podcast": 300,
    "conference_talk": 300,
    "notes_to_self": 300,
}


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return super(DateTimeEncoder, self).default(obj)


def create_content_item(source: Source, meta: Dict[str, Any]) -> int:
    logging.info("converting meta into JSON")
    meta = json.dumps(meta, cls=DateTimeEncoder)
    logging.info("creating new item record")
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            Insert into contentitem (source, meta) values (%s, %s::jsonb)
            RETURNING id;
            """,
            (source, meta),
        )
        record = cursor.fetchone()
    db_connection.commit()
    logging.info("created: new item %s" % record)
    return record["id"]


def generate_embeddings(chunk_size: int, content: str, content_item_id: int):
    embeddings = HuggingFaceEmbeddings()

    if chunk_size:
        logging.info("chunk_size > 0. splitting doc")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=20,
            separators=[".", "!", "?", "\n"],
            keep_separator="end",
        )

        docs = text_splitter.split_text(content)
        embed_docs = embeddings.embed_documents(docs)
        entries = [
            (content_item_id, text, embedding)
            for text, embedding in zip(docs, embed_docs)
        ]
        logging.info("inserting %d docs" % len(entries))
        with db_connection.cursor() as cursor:
            cursor.executemany(
                """
                INSERT into quoteembeddings (content_item_id, content_snippet, embedding)
                VALUES (%s, %s, %s)
                """,
                entries,
            )

    else:
        logging.info("chunk_size set to 0")
        docs = content
        embed_docs = embeddings.embed_documents(docs)
        entries = (content_item_id, docs, embed_docs[0])
        logging.info("inserting doc into DB")
        with db_connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT into quoteembeddings (content_item_id, content_snippet, embedding)
                VALUES (%s, %s, %s)
                """,
                entries,
            )

    db_connection.commit()
    logging.info("Done!")


def create_item(filepath: pathlib.Path, source: Source):
    post = frontmatter.load(filepath)
    meta, content = post.metadata, post.content
    content_item_id = create_content_item(source=source, meta=meta)
    generate_embeddings(
        content_item_id=content_item_id,
        chunk_size=chunk_size[source.value],
        content=content,
    )


@app.command(name="item")
def import_item(filepath: pathlib.Path, source: Source):
    create_item(filepath=filepath, source=source)


@app.command(name="microblog")
def bulk_microblog(microblog_path: pathlib.Path):
    source = Source.microblog

    for entry in microblog_path.iterdir():
        logging.info("adding %s" % entry)
        create_item(filepath=entry.absolute(), source=source)


@app.command(name="blog")
def bulk_blog(blog_path: pathlib.Path):
    source = Source.blog

    for entry in blog_path.glob("*.md"):
        logging.info("adding %s" % entry)
        create_item(filepath=entry.absolute(), source=source)


@app.command(name="conduit")
def bulk_conduit(blog_path: pathlib.Path):
    source = Source.conduit

    for entry in blog_path.iterdir():
        logging.info("adding %s" % entry)
        create_item(filepath=entry.absolute(), source=source)


@app.command(name="notes")
def bulk_notes(notes_path: pathlib.Path):
    """Bulk load notes to self section"""
    source = Source.notes_to_self

    for entry in notes_path.glob("*.md"):
        logging.info("adding %s" % entry)
        create_item(filepath=entry.absolute(), source=source)


if __name__ == "__main__":
    app()
