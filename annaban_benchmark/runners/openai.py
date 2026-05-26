from .base import BaseRunner


class OpenAIRunner(BaseRunner):
    def __init__(self):
        super().__init__("gpt")
