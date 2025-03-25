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

def get_commit_hashes(repo_path, max_commits):
    """
    Fetches the commit hashes from the git history in the specified repository.

    Args:
    - repo_path (str): The path to the Git repository.
    - max_commits (int): The maximum number of commits to retrieve.

    Returns:
    - list: A list of commit hashes.
    """
    # Fetch the commit hashes from the repository
    command = f"git log --reverse --format='%H' -n {max_commits}"
    output, error = execute_shell_command(command, repo_path)
    if error:
        raise Exception(f"Error fetching commit hashes: {error}")

    # Return the commit hashes as a list
    return output.splitlines()

def select_commits(repo_path, select_count):
    """
    Selects a given number of commits (first, last, and evenly spaced middle commits)
     from the git history.

    Args:
    - repo_path (str): The path to the Git repository.
    - select_count (int): The number of commits to select (including first and last).

    Returns:
    - list: A list of selected commit hashes along with their numbers.
    """
    # Get the total number of commits in the repository
    command = "git rev-list --count HEAD"
    output, error = execute_shell_command(command, repo_path)
    if error:
        raise Exception(f"Error fetching total commit count: {error}")

    max_commits = int(output.strip())

    # If fewer commits are requested than available, adjust the selection count
    if select_count > max_commits:
        raise ValueError("Number of selected commits cannot be greater than total commits.")

    # Fetch all commit hashes from the repository
    commit_hashes = get_commit_hashes(repo_path, max_commits)

    # The list to store selected commit hashes
    selected_commits = []

    # Always select the first commit
    selected_commits.append((1, commit_hashes[0]))  # (commit number, commit hash)

    # Always select the last commit
    selected_commits.append((max_commits, commit_hashes[-1]))  # (commit number, commit hash)

    # For the middle commits, we need to select evenly spaced commits
    if select_count > 2:
        middle_commit_count = select_count - 2  # We already have first and last commits

        # Calculate the step size for evenly spaced middle commits
        step_size = (max_commits - 1) // (select_count - 1)  # This ensures equal spacing

        # Select middle commits based on the step size
        for i in range(1, middle_commit_count + 1):
            middle_commit_position = i * step_size
            middle_commit_position = min(middle_commit_position, max_commits - 1)  # Ensure within bounds
            selected_commits.append((middle_commit_position + 1, commit_hashes[middle_commit_position]))  # (commit number, commit hash)

    # Sort selected commits in ascending order (commit 1 first, commit 2 second, etc.)
    selected_commits = sorted(selected_commits, key=lambda x: x[0])
    return selected_commits

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

    In this method we are first trying to get current branch of repo.
    Next we are switching to commit hash. Changes are made
    to README.md in the in this commit hash are present if we switched to that
    particular commit hash. Count the words in README.md file and revert back
    to current branch which we got earlier.

    Args:
    - commit_hash (str): The commit hash to checkout.
    - script_path (str): The path to the counting script.
    - repo_path (str): The path to the Git repository.

    Returns:
    - str: The output of the counting script.
    """
    # Ensure the script is run with the correct absolute path
    script_path = os.path.abspath(script_path)

    # Get the current branch before checking out to the commit hash
    command = "git rev-parse --abbrev-ref HEAD"
    current_branch, error = execute_shell_command(command, repo_path)
    if error:
        raise Exception(f"Error retrieving current branch: {error}")

    # Checkout to the specified commit hash
    command = f"git switch --detach {commit_hash} --quiet"
    output, error = execute_shell_command(command, repo_path)
    if error:
        raise Exception(f"Error checking out commit {commit_hash}: {error}")

    # Run the counting script directly on the current repo state (i.e., in the context of the commit)
    command = f"bash {script_path}"
    countoutput, error = execute_shell_command(command, repo_path)
    if error:
        checkout_from_detached_commit(current_branch, repo_path)
        if error:
            raise Exception(f"Error reverting back to original branch {current_branch.strip()}: {error}")
        raise Exception(f"Error running counting script on commit {commit_hash}: {error}")

    checkout_from_detached_commit(current_branch, repo_path)
    return countoutput.strip()

# Function to checkout to a current branch from detached HEAD state
def checkout_from_detached_commit(current_branch, repo_path):
    """
    Checks out a current branch from a detached HEAD state.

    Args:
    - current_branch (str): The branch of a  the Git repository.
    - commit_hash (str): The commit hash to checkout.
    """
    # Revert back to the original branch
    command = f"git checkout {current_branch.strip()} --quiet"
    output, error = execute_shell_command(command, repo_path)
    if error:
        raise Exception(f"Error reverting back to original branch {current_branch.strip()}: {error}")

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
    # Create the artefacts directory
    artefacts_path.mkdir(parents=True)

    # Dynamically get the total number of commits and decide how many to select
    total_commits_command = "git rev-list --count HEAD"
    output, error = execute_shell_command(total_commits_command, repo_path)
    if error:
        raise Exception(f"Error fetching total commit count: {error}")

    total_commits = int(output.strip())
    print(f"Total commits in the repository: {total_commits}")

    # Select the commits
    selected_commits = select_commits(repo_path, max_commits)

    # Metadata structure to store commit details
    metadata = {
        "created": datetime.now().strftime("%Y-%m-%d"),
        "commits": {}
    }

    # Process each commit hash
    for commit_number, commit_hash in selected_commits:
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

    print("**** Process complete. Artefacts saved to 'artefacts' directory. ***")

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
