# server.py
from fastmcp import FastMCP
import subprocess
from playwright.sync_api import sync_playwright

mcp = FastMCP("Dmca")


@mcp.tool
def add(a: int, b: int) -> int:
    """Add two numbers"""

    return a + 1000


@mcp.tool
def get_html(url: str) -> str:
    """
    Fetch the fully formatted HTML source code of a URL using Playwright.
    This includes all HTML after JavaScript has been executed.

    Args:
        url: The URL to fetch HTML from (must include https://)

    Returns:
        The complete HTML source code of the page
    """
    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(url, wait_until='networkidle')

        html = page.content()

        browser.close()

        return html


if __name__ == "__main__":
    mcp.run(show_banner=False)