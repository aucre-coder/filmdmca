import os
import anyio
from claude_agent_sdk import query, ClaudeAgentOptions, ClaudeSDKClient, create_sdk_mcp_server, tool
from playwright.sync_api import sync_playwright

from agent.videolinkagent import  callback

BASE_DIR_SCANNER = "C:/Users/aurel/PycharmProjects/filmdmca/main/bsto/scanner/scanner"
BASE_DIR_EXTRACTOR = "C:/Users/aurel/PycharmProjects/filmdmca/main/bsto/scanner/extractor"


@tool("addContentScanner", "Write or update the BSTO ContentScanner.py in scanner/scanner/", {"scanner": str})
async def add_content_scanner(args):
    """Write or update the BSTO ContentScanner.py"""
    filepath = os.path.join(BASE_DIR_SCANNER, "ContentScanner.py")
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(args['scanner'])
    return {
        "content": [
            {"type": "text", "text": f"✓ Scanner written to: {filepath}"}
        ]
    }


@tool("addDisneyContentScannerCaller", "Write or update DisneyContentScannerCaller.py in scanner/scanner/", {"caller": str})
async def add_content_scanner_caller(args):
    """Write or update DisneyContentScannerCaller.py"""
    filepath = os.path.join(BASE_DIR_SCANNER, "DisneyContentScannerCaller.py")
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(args['caller'])
    return {
        "content": [
            {"type": "text", "text": f"✓ Caller written to: {filepath}"}
        ]
    }


@tool("addVideoLinkExtractor", "Write VideoLinkExtractor.py to extractor directory", {"extractor": str})
async def add_video_link_extractor(args):
    """Write VideoLinkExtractor.py"""
    filepath = os.path.join(BASE_DIR_EXTRACTOR, "VideoLinkExtractor.py")
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(args['extractor'])
    return {
        "content": [
            {"type": "text", "text": f"✓ Video extractor written to: {filepath}"}
        ]
    }


@tool("addMovieInfoExtractor", "Write MovieInfoExtractor.py to extractor directory", {"extractor": str})
async def add_movie_info_extractor(args):
    """Write MovieInfoExtractor.py"""
    filepath = os.path.join(BASE_DIR_EXTRACTOR, "MovieInfoExtractor.py")
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(args['extractor'])
    return {
        "content": [
            {"type": "text", "text": f"✓ Movie info extractor written to: {filepath}"}
        ]
    }


@tool("addMetadataExtractor", "Write MetadataExtractor.py to extractor directory", {"extractor": str})
async def add_metadata_extractor(args):
    """Write MetadataExtractor.py"""
    filepath = os.path.join(BASE_DIR_EXTRACTOR, "MetadataExtractor.py")
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(args['extractor'])
    return {
        "content": [
            {"type": "text", "text": f"✓ Metadata extractor written to: {filepath}"}
        ]
    }




server = create_sdk_mcp_server(
    name="tools",
    version="1.0.0",
    tools=[ add_metadata_extractor, add_movie_info_extractor,
           add_video_link_extractor, add_content_scanner_caller, add_content_scanner]
)


async def interactive_session():

    options = ClaudeAgentOptions(
        system_prompt="""You are a Web Scraper Creator. Your task is to create a scraper from HTML code.CRITICAL - USE THESE CUSTOM TOOLS:✓ mcp__tools__addContentScanner - Write ContentScanner.py to scanner/scanner/✓ mcp__tools__addVideoLinkExtractor - Write VideoLinkExtractor.py to scanner/extractor/✓ mcp__tools__addMetadataExtractor - Write MetadataExtractor.py to scanner/extractor/✓ mcp__tools__addMovieInfoExtractor - Write MovieInfoExtractor.py to scanner/extractor/✓ mcp__tools__addContentScannerCaller - Write DisneyContentScannerCaller.py✓ mcp__tools__get_html - Fetch HTML from URL using PlaywrightNEVER use standard file tools like Write, Edit, or bash for file operations.ALWAYS use the provided MCP tools to write code files.<code_quality>Write production-ready code without comments, documentation, or test files.Follow the existing architecture pattern from the filmpalast scanner.</code_quality>""",
        allowed_tools=[
            "Read",
            "Bash",
            "Write",
            "mcp__tools__addMetadataExtractor",
            "mcp__tools__addMovieInfoExtractor",
            "mcp__tools__addVideoLinkExtractor",
            "mcp__tools__addDisneyContentScannerCaller",
            "mcp__tools__addContentScanner"
        ],
        mcp_servers={"tools": server},
        permission_mode='acceptEdits',
        cwd="C:/Users/aurel/PycharmProjects/filmdmca/main/filmpalast/scanner"
    )

    async with ClaudeSDKClient(options=options) as client:
        await client.query("""Call get_html tool with URL "https://bs.to" to fetch the HTML.Then analyze the HTML structure and create a complete BSTO scanner using the MCP tools:1. Call addMetadataExtractor with metadata extraction code2. Call addVideoLinkExtractor with video link extraction code  3. Call addMovieInfoExtractor with series info extraction code4. Call addContentScanner with the main scanner orchestration code Base your implementation on the filmpalast scanner structure but adapt it for bs.to's HTML. Create the DisneyContentScannerCaller!!! The goal is to find all series at once!! """)

        async for message in client.receive_response():
            print(message)

async def main():
    await interactive_session()
    await callback()


if __name__ == "__main__":
    anyio.run(main)