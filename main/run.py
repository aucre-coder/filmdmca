import asyncio
from main.data.Config import Config
from main.scanner.DisneyContentScannerCaller import DisneyContentScannerCaller


async def main():
    API_KEY = "faf01faf639d2a53896fed98347fd391"

    if API_KEY == "DEIN_TMDB_API_KEY_HIER":
        print("FEHLER: TMDb API Key fehlt!")
        print("Kostenlos: https://www.themoviedb.org/settings/api")
        return

    config = Config(TMDB_API_KEY=API_KEY)
    scanner = DisneyContentScannerCaller(config)

    try:
        # Initialize async components
        await scanner.initialize()

        # Run the scanner
        await scanner.run(num_pages=5)
    finally:
        # Always cleanup resources
        await scanner.cleanup()


if __name__ == '__main__':
    asyncio.run(main())