chatbot
=======

This is a small demo application, which implements a chatbot based on [Chainlit](https://chainlit.io/).


Setup
-----

Install the prerequisites, preferebly in a virtual environment:

```bash
pip install .[openai]
pip install .[ollama]  # alternatively
```

Create a `config.yaml` file, which looks like this:

```yaml
adapter: 'chatbot.adapter.OpenAILangChainAdapter'
llm:
    model: 'gpt-4.1-mini'
    model_kwargs:
        stream: true
system_prompt: >
    You are a helpful assistant who answers questions about small puppies.
stream_response: true
starters:
    - label:
      message:
    - label:
      message:   
```

If you want to use Ollama use the following adapter:

```yaml
adapter: 'chatbot.adapter.OllamaLangChainAdapter'
```


Usage
-----

```bash
chainlit run chatbot/app.py
```
