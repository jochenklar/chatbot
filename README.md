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

Create a `config.py` file, which looks like this:

```python
LLM_API = 'OpenAI'  # or 'Ollama'
LLM_ARGS = {
    'model': 'gpt-4.1-mini',
    'model_kwargs': {
        "stream": True
    }
}

SYSTEM_PROMPT = '''
You are a helpful assistant who answers questions about small puppies.
'''

CONTEXT_PATH = 'context.json'

STREAM = True

STARTERS = [
    {
        'label': '',
        'message': ''
    },
        {
        'label': '',
        'message': ''
    },
]
```

If you have an `OPENAI_API_KEY` put it in a `.env` file, since chainlit automatically reads it from there:

```
OPENAI_API_KEY=supersecret
```

Usage
-----

```bash
chainlit run app.py
```
