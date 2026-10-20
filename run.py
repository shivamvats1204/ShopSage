import argparse

from app.server import run

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='ShopSage — ERPNext enhancer assistant')
    parser.add_argument('--port', type=int, default=8890)
    args = parser.parse_args()
    run(args.port)
