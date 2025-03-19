import os
import subprocess
import json
import shutil
from datetime import datetime
from pathlib import Path
import argparse

# Function to execute shell commands and return the result
def execute_shell_command(command, working_dir=None):
    """
    Executes a shell command and returns the standard output and error output.
    
    Args:
    - command (str): The shell command to execute.
    - working_dir (str, optional): Directory in which to run the command. Defaults to None.
    
    Returns:
    - tuple: A tuple containing the standard output and standard error output.
    """
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=working_dir)
        return result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return e.stdout, e.stderr

# Function to get commit hashes from the git history
def get_commit_hashes(repo_path, max_commits):
    """
    Fetches the commit hashes from the git history in the specified repository.
    
    Args:
    - repo_path (str): The path to the Git repository.
    - max_commits (int): The maximum number of commits to retrieve.
    
    Returns:
    - list: A list of commit hashes.
    """
    command = f"git log --reverse --format='%H' -n {max_commits}"
    output, error = execute_shell_command(command, repo_path)
    if error:
        raise Exception(f"Error fetching commit hashes: {error}")
    return output.splitlines()

# Function to get commit metadata (date and message)
def get_commit_metadata(repo_path, commit_hash):
    """
    Fetches the metadata (date and message) for a specific commit.
    
    Args:
    - repo_path (str): The path to the Git repository.
    - commit_hash (str): The commit hash for which to fetch the metadata.
    
    Returns:
    - tuple: A tuple containing the commit date and commit message.
    """
    command = f"git show -s --format='%ci %s' {commit_hash}"
    output, error = execute_shell_command(command, repo_path)
    if error:
        raise Exception(f"Error fetching commit metadata for {commit_hash}: {error}")
    
    # Parse the commit output: "YYYY-MM-DD HH:MM:SS commit message"
    commit_date, commit_message = output.split(" ", 1)
    return commit_date, commit_message.strip()

# Function to run the count words script on the README.md file for a specific commit
def count_words_in_readme(commit_hash, script_path, repo_path):
    """
    Runs the given counting script on the README.md file in the repository at a specific commit.
    
    Args:
    - commit_hash (str): The commit hash to checkout.
    - script_path (str): The path to the counting script.
    - repo_path (str): The path to the Git repository.
    
    Returns:
    - str: The output of the counting script.
    """
    # Ensure the script is run with the correct absolute path
    script_path = os.path.abspath(script_path)
    # Run the counting script directly on the current repo state (i.e., in the context of the commit)
    command = f"bash {script_path}"
    output, error = execute_shell_command(command, repo_path)
    if error:
        raise Exception(f"Error running counting script on commit {commit_hash}: {error}")
    return output.strip()

# Main function to execute the process of collecting commit history and word counts
def run_on_commit_history(script, repo, max_commits):
    """
    Runs the word-counting script on the specified number of commits in the given Git repository.
    
    Args:
    - script (str): The path to the counting script.
    - repo (str): The path to the Git repository.
    - max_commits (int): The number of commits to process.
    """
    repo_path = Path(repo)  # Convert repo path to a Path object
    artefacts_path = Path('artefacts')  # Path for storing the artefacts

    # Ensure the artefacts directory exists, remove it if it already exists
    if artefacts_path.exists():
        shutil.rmtree(artefacts_path)
    artefacts_path.mkdir(parents=True)  # Create the artefacts directory

    # Fetch the commit hashes for the specified number of commits
    commit_hashes = get_commit_hashes(repo_path, max_commits)

    # Metadata structure to store commit details
    metadata = {
        "created": datetime.now().strftime("%Y-%m-%d"),
        "commits": {}
    }

    # Process each commit hash
    for commit_hash in commit_hashes:
        # Get commit metadata (date and message)
        commit_date, commit_message = get_commit_metadata(repo_path, commit_hash)
        print(f"Processing commit {commit_hash} - {commit_message} ({commit_date})")

        # Run the word-counting script on the commit's README.md
        try:
            count_output = count_words_in_readme(commit_hash, script, repo_path)
            errors = None  # No errors if the script runs successfully
        except Exception as e:
            count_output = "cat: README.md: No such file or directory"  # Error message
            errors = str(e)

        # Store commit metadata (including any errors encountered)
        metadata["commits"][commit_hash] = {
            "date": commit_date,
            "message": commit_message,
            "errors": errors
        }

        # Create a .txt file for the commit's word count output
        commit_file_path = artefacts_path / f"{commit_hash}.txt"
        with open(commit_file_path, 'w') as f:
            f.write(count_output)

    # Save the metadata to a JSON file
    metadata_file_path = artefacts_path / "metadata.json"
    with open(metadata_file_path, 'w') as f:
        json.dump(metadata, f, indent=4)

    print("Process complete. Artefacts saved to 'artefacts' directory.")

# Command-line argument parsing
if __name__ == "__main__":
    # Create an argument parser
    parser = argparse.ArgumentParser(description='Run a script on Git commit history.')
    
    # Define the arguments the script will accept
    parser.add_argument('--script', type=str, required=True, help='Path to the counting script (e.g., count-words-in-readme.sh)')
    parser.add_argument('--repo', type=str, required=True, help='Path to the Git repository')
    parser.add_argument('--max-commits', type=int, required=True, help='Number of commits to process')

    # Parse the command-line arguments
    args = parser.parse_args()

    # Run the main function with the parsed arguments
    run_on_commit_history(args.script, args.repo, args.max_commits)
