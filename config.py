import os
import sys
from typing import Dict
from dotenv import load_dotenv, set_key

REQUIRED_ENV_VARS = ["GITLAB_URL", "GITLAB_TOKEN", "GITLAB_USERS", "GITLAB_MY_USERNAME"]

def setup_env(env_path: str):
    print(f"--- Configuring Environment ({env_path}) ---")
    for var in REQUIRED_ENV_VARS:
        current = os.getenv(var, "")
        prompt = f"Enter {var} [{current}]: " if current else f"Enter {var}: "
        value = input(prompt).strip()
        if value:
            set_key(env_path, var, value)
    print("Environment configured successfully.")

def load_env_config() -> Dict[str, str | list[str]]:
    if getattr(sys, 'frozen', False):
        env_path = os.path.join(os.path.dirname(sys.executable), ".env")
    else:
        env_path = os.path.join(os.path.dirname(__file__), ".env")

    if not os.path.exists(env_path):
        with open(env_path, "w") as f:
            pass

    load_dotenv(env_path)
    
    missing = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
    if missing:
        print(f"Missing environment variables: {', '.join(missing)}")
        setup_env(env_path)
        load_dotenv(env_path)

    return {
        "GITLAB_URL": os.getenv("GITLAB_URL", ""),
        "GITLAB_TOKEN": os.getenv("GITLAB_TOKEN", ""),
        "GITLAB_USERS": os.getenv("GITLAB_USERS", "").split(","),
        "GITLAB_MY_USERNAME": os.getenv("GITLAB_MY_USERNAME", ""),
    }
