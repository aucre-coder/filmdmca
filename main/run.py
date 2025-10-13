import asyncio
import importlib
from main.data.Config import Config


async def main():
    API_KEY = "faf01faf639d2a53896fed98347fd391"

    SCANNER_TYPE = "disney"

    SCANNER_MAP = {
        "disney": "main.bsto.scanner.scanner.DisneyContentScannerCaller.DisneyContentScannerCaller",
        "netflix": "main.bsto.scanner.scanner.NetflixScannerCaller.NetflixScannerCaller",
    }

    scanner_path = SCANNER_MAP.get(SCANNER_TYPE)
    if not scanner_path:
        raise ValueError(f"Unknown scanner type: {SCANNER_TYPE}")

    # Parse the full path
    module_path, class_name = scanner_path.rsplit('.', 1)
    module = importlib.import_module(module_path)
    ScannerClass = getattr(module, class_name)

    config = Config(TMDB_API_KEY=API_KEY,TMDB_BASE_URL="https://api.themoviedb.org/3",TARGET_SITE="https://bs.to")
    scanner = ScannerClass(config)

    try:
        await scanner.initialize()
        await scanner.run()
    finally:
        await scanner.cleanup()

if __name__ == '__main__':
    asyncio.run(main())