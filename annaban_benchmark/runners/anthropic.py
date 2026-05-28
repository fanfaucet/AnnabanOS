from .base import BaseRunner


class AnthropicRunner(BaseRunner):
    def __init__(self):
        super().__init__("claude")
