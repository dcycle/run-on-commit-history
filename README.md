# Git Commit History Word Count Script
----

```markdown
# Git Commit History Word Count Script

./scripts/run-on-commit-history.sh script processes the commit history of a Git repository, checks out each commit, and runs a specified script (e.g., `count-words-in-readme.sh`) to count the words in the `README.md` file. It then stores the output in individual `.txt` files and creates a `metadata.json` file with commit information.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Usage](#usage)
- [Output](#output)
- [License](#license)

## Prerequisites

Before running the script, ensure you have the following installed:

- **Python 3.x**: Make sure Python 3.x is installed. You can verify by running:
  
  ```bash
  python --version
  ```

  If not installed, download and install it from [python.org](https://www.python.org/downloads/).

- **Git**: The script interacts with a Git repository. Verify Git is installed by running:

  ```bash
  git --version
  ```

  If not installed, download and install it from [git-scm.com](https://git-scm.com/downloads).

- **Bash**: The script assumes a Unix-like environment (Linux or macOS) with Bash available. Ensure you have a Bash shell installed.

- **`count-words-in-readme.sh` script**: This script is used to count the words in the `README.md` file. Make sure this script is available and executable. Example content for `count-words-in-readme.sh`:

  ```bash
  cat README.md | wc
  ```

  Ensure it is executable:

  ```bash
  chmod +x count-words-in-readme.sh
  ```

## Setup

1. Clone the Git repository you want to analyze or ensure it is already available locally.

   ```bash
   git clone <repository_url> ./workspace
   ```

   Replace `<repository_url>` with the actual URL of your Git repository.

2. Make sure the `./scripts/count-words-in-readme.sh` script is available at the specified path, and is executable.

   ```bash
   chmod +x ./scripts/count-words-in-readme.sh
   ```

## Usage

1. **Clone the repository** for the script.

   If you haven't already, clone the repository for the script to your local machine:

   ```bash
   git clone <script_repository_url> ./script
   cd ./script
   ```

   Replace `<script_repository_url>` with the repository where the script resides.

2. **Execute the script** using the following command:

   ```bash

    ./scripts/run-on-commit-history.sh  --script=./count-words-in-readme.sh --repo=./workspace --max-commits=3

   ```

   - `--script`: Path to the `count-words-in-readme.sh` script.
   - `--repo`: Path to your Git repository.
   - `--max-commits`: The maximum number of commits to process from the repository history (e.g., `3`).

### Example:

If you have a `README.md` in your repository located at `./workspace` and the `count-words-in-readme.sh` script is in the same directory as `run_on_commit_history.py`, you would run:

```bash
./scripts/run-on-commit-history.sh  --script=./count-words-in-readme.sh --repo=./srv/snamy/dp/de/starterkit-node/ --max-commits=3
```

## Output

After running the script, the following output will be generated:

1. **Artefacts Directory**: A directory called `artefacts` will be created in the same directory as the script.

2. **Metadata File (`metadata.json`)**: This file contains the metadata for each commit, including:
   - Commit hash
   - Commit date
   - Commit message
   - Any errors encountered (e.g., if `README.md` is missing)

   Example content of `metadata.json`:
   
   ```json
   {
       "created": "2025-03-19",
       "commits": {
           "4ef357d": {
               "date": "2024-10-29",
               "message": "commit xyz"
           },
           "5299ec9": {
               "date": "2024-10-24",
               "message": "something was done here"
           },
           "468fa73": {
               "date": "2024-10-22",
               "message": "some commit",
               "errors": "cat: README.md: No such file or directory"
           }
       }
   }
   ```

3. **Commit `.txt` Files**: Each processed commit will have a corresponding `.txt` file containing the output of the word-counting script.

   Example file names and contents:
   
   - `4ef357d.txt`:
     ```
     cat: README.md: No such file or directory
     ```

   - `5299ec9.txt`:
     ```
     120    900   9789
     ```

   - `468fa73.txt`:
     ```
     165    1223   13675
     ```

   If a commit does not contain a `README.md` file, an error message will be logged in the `.txt` file (e.g., `cat: README.md: No such file or directory`).


```
