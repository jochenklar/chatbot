import importlib

import chainlit as cl
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from .config import settings


class Adapter:

    async def on_chat_start(self):
        pass

    async def on_chat_end(self):
        pass

    async def on_chat_resume(self, thread):
        pass

    async def on_message(self, message):
        raise NotImplementedError

    @staticmethod
    def init_adapter():
        adapter_module_name, adapter_class_name = settings.ADAPTER.rsplit(".", 1)
        adapter_module = importlib.import_module(adapter_module_name)
        adapter_class = getattr(adapter_module, adapter_class_name)
        return adapter_class()


class LangChainAdapter(Adapter):

    def init_prompt(self):
        return ChatPromptTemplate.from_messages(
            [
                ("system", "{system_prompt}"),
                ("system", "{context}"),
                MessagesPlaceholder(variable_name="history"),
                ("user", "{content}")
            ]
        )

    def init_llm(self):
        raise NotImplementedError

    def init_chain(self):
        return self.init_prompt() | self.init_llm()

    def get_context(self):
        return ""

    async def on_chat_start(self):
        cl.user_session.set("chain", self.init_chain())

    async def on_message(self, message):
        chain = cl.user_session.get("chain")
        history = cl.user_session.get("history", [])
        context = self.get_context()

        inputs = {
            "system_prompt": settings.SYSTEM_PROMPT,
            "context": context,
            "history": history,
            "content": message.content
        }

        response_content = await self.run_chain(chain, inputs)

        # add messages to history
        cl.user_session.set("history", [
            *history,
            HumanMessage(content=message.content),
            AIMessage(content=response_content)
        ])

    async def run_chain(self, chain, inputs):
        response_content = ""
        if settings.STREAM_RESPONSE:
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

        return response_content

    def set_starters(self):
        try:
            return [cl.Starter(**starter) for starter in settings.STARTERS]
        except AttributeError:
            return None


class OpenAILangChainAdapter(LangChainAdapter):

    def init_llm(self):
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(**settings.LLM)


class OllamaLangChainAdapter(LangChainAdapter):

    @property
    def init_llm(self):
        from langchain_ollama import ChatOllama
        return ChatOllama(**settings.LLM)


adapter = Adapter.init_adapter()
