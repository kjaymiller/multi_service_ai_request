import os
from typing import Optional
import typing_extensions
import typer
from langchain_anthropic import ChatAnthropic
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from db import similarity_search

app = typer.Typer()


def get_query(query: str):
    results = similarity_search(query)
    messages = [f"{title} - {content}" for content, title, score in results]
    return "\n\n".join(messages)


@app.command(name="query")
def _query(query: str):
    print(get_query(query))


@app.command(name="ai")
def ai(
    query: str,
    system_message: typing_extensions.Annotated[
        Optional[str],
        typer.Option("--system", help="Override the system with new system text"),
    ] = None,
):
    results = get_query(query)

    llm = ChatAnthropic(
        model="claude-3-7-sonnet-20250219",
        temperature=0,
        max_tokens=1024,
        timeout=None,
        max_retries=2,
    )

    if not system_message:
        system_message = """
            You are a helpful personal assistant that is tasked with helping me (Jay) recall information that I've written about.

            Given the query:{query} respond using quotes and samples from the returned content below.

            Content: {docs}

            - Provide narration and lead with a summary paragraph.
            - Speak directly to me
            - Format for readability and use markdown
            - Only use quotes mentioned. Don't use external references.
            - If there is no content - Say so and stop generating a response. Don't make things up.
            """

    system = ("system", system_message)
    prompt = ChatPromptTemplate.from_messages(
        [
            system,
            (
                "human",
                "{query}",
            ),
        ]
    )

    chain = prompt | llm | StrOutputParser()
    print("requesting response....")
    topic = {"query": query, "docs": results}

    for content in chain.stream(topic):
        print(content, end="")


if __name__ == "__main__":
    app()
