import os
import sys
import yaml
import subprocess
import argparse

def parse_env_vars(env_vars_str):
    """
    Parse environment variables from a string and return a dictionary.
    """
    env_vars = {}
    for line in env_vars_str.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith('-'):
            line = line[1:].strip()  # Remove leading hyphen and any surrounding whitespace
        key, value = map(str.strip, line.split(':', 1))
        if key:
            env_vars[key] = value
    return env_vars

def simplify_path(path):
    """
    Simplify a given file path, resolving '.' and '..' components.
    """
    if not path:
        raise ValueError("No path provided.")
    
    components = path.split('/')
    stack = []
    
    for component in components:
        if component in ("", "."):
            continue
        elif component == "..":
            if stack:
                stack.pop()
        else:
            stack.append(component)
    
    return "/" if not stack else "/".join(stack)

def remove_path_prefix(full_path, prefix):
    """
    Remove a prefix from a file path and return the modified path.
    """
    full_path = full_path.lstrip('./')
    prefix = prefix.lstrip('./')
    
    return f"./{full_path[len(prefix)+1:]}" if full_path.startswith(prefix) else full_path

def main():
    parser = argparse.ArgumentParser(description="Run evaluations based on changed files.")
    parser.add_argument('--env-vars', type=str, help='Environment variables in key:value format')
    parser.add_argument('--working-directory', type=str, required=True, help='Working directory')
    parser.add_argument('--config-path', type=str, required=True, help='Path to the config file')
    parser.add_argument('--changed-files', type=str, help='List of changed files')
    
    args = parser.parse_args()

    # Set environment variables
    if args.env_vars:
        env_vars = parse_env_vars(args.env_vars)
        for key, value in env_vars.items():
            print(f"Setting env var: {key}={value}")
            os.environ[key] = value

    # Prepare working directory
    working_directory = args.working_directory
    if not working_directory.startswith('./'):
        working_directory = f"./{working_directory}"

    # Load config
    with open(args.config_path, 'r') as f:
        config_content = yaml.safe_load(f)
    
    prompts_path = simplify_path(f"{working_directory}/{config_content['prompts']['promptsPath']}")
    
    print(f"Prompts path: {prompts_path}")
    print(f"Working directory: {working_directory}")

    # Evaluate changed files
    if args.changed_files:
        changed_files = args.changed_files.split()
        for file in changed_files:
            if file.startswith(prompts_path):
                file = remove_path_prefix(file, working_directory)
                result = subprocess.run(['npx', '@ellmo-ai/ts-sdk', 'eval', '--path', file])
                
                if result.returncode != 0:
                    print(f"Check failed for {file}")
                    sys.exit(1)

if __name__ == "__main__":
    main()
