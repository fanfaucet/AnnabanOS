from .base import BaseRunner


class OllamaRunner(BaseRunner):
    def __init__(self):
        super().__init__("ollama")
