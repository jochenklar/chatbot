import logging
import sys
from pathlib import Path

import chainlit as cl
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

logger = logging.getLogger(__name__)

try:
    import config
except ModuleNotFoundError:
    logger.error("config.py not found")
    sys.exit(1)

context = []
for file_path in Path("context").iterdir():
    logger.info("Loading %s", file_path)
    context.append(file_path.read_text())


@cl.on_chat_start
async def on_chat_start():
    if config.LLM_API == "OpenAI":
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(**config.LLM_ARGS)
    elif config.LLM_API == "Ollama":
        from langchain_ollama import ChatOllama
        llm = ChatOllama(**config.LLM_ARGS)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "{system_prompt}"),
            ("system", "{context}"),
            MessagesPlaceholder(variable_name="history"),
            ("user", "{content}")
        ]
    )

    chain = prompt | llm

    cl.user_session.set("chain", chain)


@cl.on_message
async def on_message(message):
    chain = cl.user_session.get("chain")
    history = cl.user_session.get("history", [])

    inputs = {
        "system_prompt": config.SYSTEM_PROMPT,
        "context": "\n\n".join(context),
        "history": history,
        "content": message.content
    }

    response_content = ""
    if config.STREAM_RESPONSE:
        response_message = cl.Message(content="")
        await response_message.send()

        async for chunk in chain.astream(inputs):
            if isinstance(chunk, AIMessageChunk):
                response_content += chunk.content
                response_message.content = response_content
                await response_message.update()
    else:
        response = await chain.ainvoke(inputs)
        response_content = response.content
        await cl.Message(content=response_content).send()

    # add messages to history
    cl.user_session.set("history", [
        *history,
        HumanMessage(content=message.content),
        AIMessage(content=response_content)
    ])


@cl.set_starters
async def set_starters():
    return [cl.Starter(**starter) for starter in config.STARTERS]
