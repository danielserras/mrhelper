import sys
import argparse
from app import MRHelper
from config import load_env_config, setup_env
import os

def print_help():
    print("""
MrHelper - GitLab Merge Request Monitor
Usage: python main.py [command]

Commands:
  run        Start the TUI (default)
  config     Update environment configuration
  help       Show this help message

Key Controls (in app):
  Q: Quit
  U: Update
  V: View MR in browser
  T: Toggle Full Title
  R: Mark as reviewed
    """)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    subparsers.add_parser("run", help="Start the application")
    subparsers.add_parser("config", help="Update environment configuration")
    subparsers.add_parser("help", help="Show this help message")

    args = parser.parse_args()

    # Determine env path logic
    if getattr(sys, 'frozen', False):
        env_path = os.path.join(os.path.dirname(sys.executable), ".env")
    else:
        env_path = os.path.join(os.path.dirname(__file__), ".env")

    if args.command == "config":
        setup_env(env_path)
    elif args.command == "help":
        print_help()
    else:
        # Default to 'run'
        config = load_env_config()
        MRHelper(
            config.get("GITLAB_URL"), 
            config.get("GITLAB_TOKEN"), 
            config.get("GITLAB_USERS"),
            config.get("GITLAB_MY_USERNAME")
        ).run()
