import json
import logging
import sys

import chainlit as cl
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

logger = logging.getLogger(__name__)

try:
    import config
except ModuleNotFoundError:
    logger.error("config.py not found")
    sys.exit(1)


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

    with open(config.CONTEXT_PATH) as fp:
        context = json.load(fp)

    cl.user_session.set("chain", chain)
    cl.user_session.set("context", context)


@cl.on_message
async def on_message(message):
    chain = cl.user_session.get("chain")
    history = cl.user_session.get("history", [])
    context = cl.user_session.get("context", {})

    inputs = {
        "system_prompt": config.SYSTEM_PROMPT,
        "context": context,
        "history": history,
        "content": message.content
    }

    response_content = ""
    if config.STREAM:
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
