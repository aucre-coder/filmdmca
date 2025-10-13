from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient

website = "bsto"
url = "C:/Users/aurel/PycharmProjects/filmdmca/main/" + website + "/scanner"

async def callback():
        options = ClaudeAgentOptions(
            system_prompt="Verify the VideoLinkExtractor is working properly with the website https://bs.to <thinking> Please think about problems thoroughly and in great detail. Consider multiple approaches and show your complete reasoning.Try different methods if your first approach doesn't work. </thinking>",
        allowed_tools = [
            "Read",
            "Bash",
            "Edit"
        ],
        permission_mode='acceptEdits',
            cwd=url
        )
        async with ClaudeSDKClient(options=options) as client:
            await client.query(
                """Only change or edit the VideolinkExtractor File!! Nothing else!! """)

            async for message in client.receive_response():
                print(message)