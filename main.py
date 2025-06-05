class Agent:
    def __init__(self, name):
        self.name = name
        self.memory = []

    def receive(self, message):
        print(f"{self.name} received: {message}")
        self.memory.append(message)

    def send(self, other_agent, message):
        print(f"{self.name} sends to {other_agent.name}: {message}")
        other_agent.receive(message)


class AnnabanAI(Agent):
    def think(self):
        return "Hello from AnnabanAI! Ready to collaborate."


class GeminiRelay(Agent):
    def think(self):
        return "GeminiRelay here. Standing by for commands."


def main():
    annaban = AnnabanAI("AnnabanAI")
    gemini = GeminiRelay("GeminiRelay")

    # Simulate interaction
    annaban.send(gemini, annaban.think())
    gemini.send(annaban, gemini.think())


if __name__ == "__main__":
    main()
