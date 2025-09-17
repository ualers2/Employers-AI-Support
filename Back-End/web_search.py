from agents import Agent, Runner, SQLiteSession
import os

# Create agent
agent = Agent(
    name="Assistant",
    instructions="Reply very concisely.",
    tools=
)

# Create a session instance with a session ID
session = SQLiteSession("conversation_123", os.path.join(os.path.dirname(__file__), 'conv.db'))

# Also works with synchronous runner
result = Runner.run_sync(
    agent,
    "What's the population?",
    session=session
)
print(result.final_output)  # "Approximately 39 million"