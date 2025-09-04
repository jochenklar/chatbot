import chainlit as cl

from chatbot.adapter import adapter


@cl.on_chat_start
async def on_chat_start():
    await adapter.on_chat_start()


@cl.on_chat_end
async def on_chat_end():
    await adapter.on_chat_end()


@cl.on_chat_resume
async def on_chat_resume(thread):
    await adapter.on_chat_resume(thread)


@cl.on_message
async def on_message(message):
    await adapter.on_message(message)


@cl.set_starters
def set_starters():
    return adapter.set_starters()
