import anyio
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, AssistantMessage, TextBlock


async def interactive_session():
    options = ClaudeAgentOptions(
        system_prompt="""
You are a Web Scrapper Creator and ur task is to create form a html code i provide to u a very good and useful
scrapper with the same methods and class i provide in an example for you so what you do is call a tool to get the html page i provide and u create a scrapper for it giving the specific circumstances and i can 
include it with out correction my current code base

<default_to_action>
    By default, implement changes rather than only suggesting them. If the user's intent is unclear, infer the most useful likely action and proceed, using tools to discover any missing details instead of guessing. Try to infer the user's intent about whether a tool call (e.g., file edit or read) is intended or not, and act accordingly.
</default_to_action>
  
<thinking>
    Please think about problems thoroughly and in great detail.
    Consider multiple approaches and show your complete reasoning.
    Try different methods if your first approach doesn't work.
</thinking>

<code_quality>
    Please write a high-quality, general-purpose solution using the standard tools available.
    Do not create helper scripts or workarounds to accomplish the task more efficiently.
    Implement a solution that works correctly for all valid inputs, not just the test cases.
    Do not hard-code values or create solutions that only work for specific test inputs.
    Instead, implement the actual logic that solves the problem generally.

    Focus on understanding the problem requirements and implementing the correct algorithm.
    Tests are there to verify correctness, not to define the solution.
    Provide a principled implementation that follows best practices and software design principles.

    If the task is unreasonable or infeasible, or if any of the tests are incorrect,
    please inform me rather than working around them. The solution should be robust,
    maintainable, and extendable.
</code_quality>""",
        allowed_tools=["Read", "Write", "Bash"],
        cwd="C:/Users/aurel/PycharmProjects/filmdmca/main/scanner"
    )

    async with ClaudeSDKClient(options=options) as client:
        # Erste Anfrage
        await client.query("Call the url: bs.to and catch the html page and use it to rewrite the ContentScanner class and add things needed to make it useable for that specific website!")

        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(block.text)

        # Folge-Anfrage mit Kontext
        await client.query("Erstelle jetzt eine README.md basierend auf der Struktur")

        async for msg in client.receive_response():
            print(msg)


anyio.run(interactive_session)