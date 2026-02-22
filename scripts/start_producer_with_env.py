from dotenv import load_dotenv
from pathlib import Path
import sys
import os


def main():
    env_path = Path('.') / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)

    # ensure repo root on sys.path for imports
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

    import rabbitmq_producer

    rabbitmq_producer.publish_all()


if __name__ == '__main__':
    main()
