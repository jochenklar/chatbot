import importlib
from pathlib import Path

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
                ("system", settings.SYSTEM_TEMPLATE),
                ("system", settings.CONTEXT_TEMPLATE),
                MessagesPlaceholder(variable_name="history"),
                ("user", settings.USER_TEMPLATE)
            ]
        )

    def init_llm(self):
        raise NotImplementedError

    def init_chain(self):
        return self.init_prompt() | self.init_llm()

    def update_history(self, history, message_content, response_content):
        history.append(HumanMessage(content=message_content))
        history.append(AIMessage(content=response_content))
        cl.user_session.set("history", history)

    async def on_chat_start(self):
        cl.user_session.set("chain", self.init_chain())

    async def on_message(self, message):
        history = cl.user_session.get("history", [])
        context = await self.fetch_context(message)

        inputs = {
            "context": context,
            "history": history,
            "content": message.content
        }

        response_content = await self.run_chain(inputs)

        self.update_history(history, message.content, response_content)

    async def fetch_context(self, message):
        context = cl.user_session.get("context", "")

        if not context and hasattr(settings, "CONTEXT_PATH"):
            context = "\n\n".join([
                file_path.read_text()
                for file_path in Path(settings.CONTEXT_PATH).rglob("*")
            ])
            cl.user_session.set("context", context)

        return context

    async def run_chain(self, inputs):
        chain = cl.user_session.get("chain")

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

    def init_llm(self):
        from langchain_ollama import ChatOllama
        return ChatOllama(**settings.LLM)


adapter = Adapter.init_adapter()
