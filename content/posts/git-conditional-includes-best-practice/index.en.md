+++
date = '2026-07-24T18:00:00+09:00'
draft = false
title = 'Wrong Git Account Again? Conditional Includes & Multi-Account Isolation for GitHub CLI / AI Agents'
seo_description = "Solve Git multi-identity management and GitHub CLI (gh) account switching issues. Learn how to fix erroneous commits, use Git conditional includes, and deploy a transparent Shell wrapper for seamless, automated account isolation across terminals and AI agents."
tags = ["Git", "GitHub", "dev-tools", "Claude Code", "best-practices"]
categories = ["tech"]
cover = 'git_identity.png'
images = ['git_identity.png']
nolastmod = true
+++

### Background

As a developer constantly jumping across multiple projects, I frequently run into a headache-inducing issue: committing code in a company repository with my personal email, or mistakenly using my work email in a personal repo. Seeing a personal avatar show up in the commit history of a corporate project is always embarrassing.

Recently, I made this mistake again and had already pushed it to the remote repository. This time, I decided to fix the root cause once and for all so this careless error never happens again.

As usual, I turned to Gemini for guidance.

### Emergency Fix: Handling Pushed Commits with Wrong Author Details

{{< ask >}}

I made an incorrect commit in Git with the wrong username and email configured, and I've already pushed it. How can I fix this?

{{< /ask >}}

{{< gemini >}}

Sure, this is a very common yet tricky issue in Git because you have already `push`ed the incorrect commit to the remote repository. Rewriting publicly shared history requires caution, especially when collaborating with teammates.

Don't worry—this is completely solvable. Here are two approaches:

1. **Option 1: Fix only the latest commit** (the simplest and most common scenario)
2. **Option 2: Fix multiple historical commits** (the more complex scenario)

Before proceeding, **please read this important note**:

> [!WARNING]
> The following operations will **rewrite remote repository history**. If you work in a team, **make sure to coordinate with your colleagues first**. A force push will diverge their local branch history from the remote, requiring them to run extra commands to sync back up.

#### Option 1: Fix Only the Latest Commit

If only the **very last commit you just pushed** is incorrect, this is the simplest scenario.

##### Step 1: Update the author info on the latest commit

In your local repository, use `git commit --amend` to modify the last commit.
We can use the `GIT_COMMITTER_NAME` and `GIT_COMMITTER_EMAIL` environment variables to temporarily override the committer settings.

```Bash
# --amend opens editor for the last commit message, but we won't change the message
# --author directly updates the author information
# --no-edit keeps the previous commit message without opening an editor
GIT_COMMITTER_NAME="Your Correct Username" GIT_COMMITTER_EMAIL="your_correct_email@example.com" git commit --amend --author="Your Correct Username <your_correct_email@example.com>" --no-edit
```

After running this, your local latest commit is fixed.

##### Step 2: Force push to the remote repository

Because you modified your local history, it has diverged from the remote repository. You cannot run a standard `git push`; you must force push.

It is recommended to use `--force-with-lease`, which is safer than `--force` because it verifies that no one else has updated the remote branch since your last fetch.

```Bash
git push --force-with-lease
```

Done! The author info on the latest commit on the remote repository is now corrected.

#### Option 2: Fix Multiple Historical Commits

If there are multiple past commits with the wrong email, or the entire repository history contains the wrong address, you can fix it using the following method:

##### Method A: Recommended Standard Tool (`git-filter-repo`)

Git has officially deprecated legacy `git filter-branch` and recommends **`git-filter-repo`** as the official standard tool for rewriting history (it is dramatically faster and safer).

1. Install `git-filter-repo` (e.g., via Homebrew on macOS):
   ```Bash
   brew install git-filter-repo
   ```

2. Run the following command in the repository root to bulk-replace the old email and username with the correct ones:
   ```Bash
   git filter-repo --email-callback '
   return b"your_correct_email@example.com" if email == b"wrong_old_email@example.com" else email
   ' --name-callback '
   return b"Your Correct Username" if email == b"wrong_old_email@example.com" else name
   ' --force
   ```

3. After history is rewritten, force push to the remote:
   ```Bash
   git push --force-with-lease
   ```

*(Note: If your current development environment is restricted and cannot install extra Python tools, you can also fall back to Git's built-in `git filter-branch --env-filter ...` command.)*

{{< /gemini >}}

### Root Solution: Automatically Switch Identities with Git Conditional Includes

Fixing the immediate error is good, but we need a fundamental solution to prevent this recurring headache.

> I want Git to automatically select the right identity across broad directory scopes. How can I achieve that?

{{< gemini >}}

Automatically switching Git identities (username and email) based on different project directories (such as "work" vs. "personal") is an excellent practice! It effectively prevents the awkwardness of committing personal emails into company repositories.

Git provides an elegant built-in solution called **"Conditional Includes" (`includeIf`)**. This feature was introduced in Git 2.13 and has long since become a standard capability.

How it works: you define a condition in your global `~/.gitconfig`. When the path of your Git repository matches this condition, Git loads an extra, dedicated configuration file that overrides the identity settings in your global configuration.

Here is a step-by-step setup guide using a typical "work" vs. "personal" scenario.

#### Scenario Assumption

Suppose your directory structure looks like this:

- All **work** projects live in `~/dev/work/`.
- All **personal** projects live in `~/dev/personal/`.

#### Step 1: Create Separate Configuration Files for Each Identity

First, create dedicated configuration files for each identity. These files can live anywhere in your home directory, but placing them alongside `~/.gitconfig` prefixed with `.gitconfig-` makes them easy to manage.

1. **Create the work identity config `~/.gitconfig-work`**  
Run the following command in your terminal, or create and edit the file directly:

```Bash
# Write the following to ~/.gitconfig-work
cat > ~/.gitconfig-work << EOF
[user]
    name = Your Work Username
    email = <your-work-email>
EOF
```

2. **Create the personal identity config `~/.gitconfig-personal`**  
Similarly, create a file for your personal identity:

```Bash
# Write the following to ~/.gitconfig-personal
cat > ~/.gitconfig-personal << EOF
[user]
    name = Your Personal Username
    email = <your-personal-email>
EOF
```

Now you have two separate identity configurations.

#### Step 2: Update Your Main `~/.gitconfig`

Next, edit your global `~/.gitconfig` to tell Git when to load those identity files.

1. **Set a default identity**  
In `~/.gitconfig`, specify your most frequently used identity or a fallback default. Git uses this when a project path matches no special condition. Leaving it empty is also valid.

```TOML
[user]
```

_If your `~/.gitconfig` already has a `[user]` section, ensure it reflects your intended default._

2. **Add `includeIf` conditions**  
At the end of `~/.gitconfig`, add the `[includeIf]` directives:

```TOML
# When repo path is under ~/dev/work/, load work config
[includeIf "gitdir:~/dev/work/"]
path = ~/.gitconfig-work

# When repo path is under ~/dev/personal/, load personal config
[includeIf "gitdir:~/dev/personal/"]
path = ~/.gitconfig-personal
```

> [!NOTE]  
> The path following `gitdir:` must end with a trailing slash `/` to match directories rather than files of the same name. `~/` is recognized by Git as your home directory.

#### How to Verify the Setup

Verification is simple:

1. **Enter a Git repository under your work folder**:

```Bash
cd ~/dev/work/some-work-repo
```

2. **Check the active `user.email`**:

```Bash
git config user.email
```

The output should be your **work email** (`<your-work-email>`).

3. **Enter a Git repository under your personal folder**:

```Bash
cd ~/dev/personal/some-personal-repo
```

4. **Check the active `user.email` again**:

```Bash
git config user.email
```

The output should be your **personal email** (`<your-personal-email>`).

With this setup, you solve the multi-identity issue once and for all. As long as projects live in their designated parent directories, Git picks the right identity automatically.

> [!NOTE]  
> This setting applies only to **future commits** and will not alter any existing commit history. To update older commits, you still need methods like `git rebase` or `git commit --amend` discussed earlier.

{{< /gemini >}}

### Advanced Setup: Integrating SSH Key Management

> Now my SSH config only has authorization for my github.com-personal account.
>
> In individual Git repositories, I also have local `[user]` settings (some do, some don't).
>
> How can I migrate this step by step into clean "Conditional Includes"?

{{< gemini >}}

#### Refactoring SSH Configuration (`~/.ssh/config`)

To isolate work and personal assets cleanly, define **explicit, symmetric** Host aliases in `~/.ssh/config` bound to their corresponding keys:

```text
Host github.com-work
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_ed25519_work
  IdentitiesOnly yes

Host github.com-personal
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_ed25519_personal
  IdentitiesOnly yes
```

The advantage here is that work and personal keys are fully symmetric and independent, eliminating reliance on a global fallback while keeping the structure straightforward.

---

#### Updating Git Identity Files: Symmetric URL Rewriting

Next, configure **"symmetric bidirectional URL rewriting"** inside your respective Git identity configs.

1. **Update the work identity config (`~/.gitconfig-work`)**:

```TOML
[user]
    name = Your Work Username
    email = <your-work-email>

# Under work directory, automatically rewrite standard git@github.com: to github.com-work
[url "git@github.com-work:"]
    insteadOf = git@github.com:
```

2. **Update the personal identity config (`~/.gitconfig-personal`)**:

```TOML
[user]
    name = Your Personal Username
    email = <your-personal-email>

# Under personal directory, automatically rewrite standard git@github.com: to github.com-personal
[url "git@github.com-personal:"]
    insteadOf = git@github.com:
```

This `url...insteadOf` rule is incredibly powerful: whether in work or personal directories, you can clone repositories using standard GitHub URLs like `git clone git@github.com:org/repo.git`. Git rewrites it on the fly to `github.com-work` or `github.com-personal` based on the active path, automatically routing to the right SSH key.

---

#### Clean Up: Removing Legacy Per-Repository Configurations

The final step is to purge existing per-repository `[user]` settings and let the automated system take over.

1. **Remove local `user` configurations**:

```bash
# --local affects only the .git/config file inside the current project
git config --local --unset-all user.name
git config --local --unset-all user.email
```

After this, the repository no longer carries local overrides.

2. **(Recommended) Normalize remote URLs**:

With `url...insteadOf` in place, you no longer need hardcoded `github.com-personal` URLs in your remotes. Switching back to standard addresses makes repos portable:

```Bash
# Check current remote url
git remote -v
# output: origin  git@github.com-personal:CheerChen/konakore.git (fetch)
# ...

# Update to standard URL
git remote set-url origin git@github.com:CheerChen/konakore.git

# Verify update
git remote -v
# output: origin  git@github.com:CheerChen/konakore.git (fetch)
# ...
```

3. **Final Verification**:

Inside the project directory, run:

```Bash
# Check which email Git will use
git config user.email

# Test if push/pull still works with the correct SSH key
git fetch
```

Repeat this cleanup across your other repositories. All Git actions will adapt to the parent folder automatically with zero manual switching needed.

{{< /gemini >}}

---

### Modern Upgrade: Zero-Friction Isolation in the Era of `gh` and AI Agents

After sorting out Git conditional includes and SSH keys, I thought the problem was solved permanently. However, as I started using the GitHub CLI (`gh`) extensively from the command line, alongside AI coding agents like Claude Code and Devin to execute tasks, a new issue quickly popped up:

While in a personal project directory, I asked an AI agent to open a PR. To my dismay, `gh` defaulted to my corporate GitHub account and opened the PR under my company identity!

My initial instinct was to add instructions to the agent's prompt guidelines (such as `CLAUDE.md` or `AGENTS.md`):

```markdown
## gh multi-account auto-select

When running any gh command, manually specify the token based on current working directory:
- `~/dev/personal/` -> GH_TOKEN="$(gh auth token --user personal-user)" gh <command>
- `~/dev/work/`     -> GH_TOKEN="$(gh auth token --user work-user)" gh <command>
```

I assumed this would be foolproof. But after using it for a while, three major pain points surfaced:

1. **Useless for humans in the terminal**: When I manually type `gh pr create` or `gh repo view` in my shell, prompt instructions do nothing. The CLI still used whatever default account was active, resulting in frequent mistakes.
2. **Wastes agent context window**: Forcing token-injection rules into system prompts wastes context tokens and distracts the model from core coding problems.
3. **Maintenance nightmare across multiple tools**: Claude Code (`CLAUDE.md`), Devin (`AGENTS.md`), Codex, Cursor (`.cursorrules`)—every agent has its own configuration. Repeating and syncing these rules across every CLI tool and agent config is tedious and error-prone.

Realizing that relying on prompt instructions is fragile and high-maintenance, I consulted Gemini again:

> Prompt rules for agents are painful to maintain and eat context tokens, and they don't fix manual terminal usage. Is there a way to auto-switch gh accounts based on directory at the Shell level?

{{< gemini >}}

This is a classic modern pain point!

Git's `includeIf` is scoped strictly within Git itself and only affects `git` commands. GitHub CLI (`gh`), however, is an independent tool that maintains a single active account per host (such as `github.com`). When you run `gh auth status`, only one account has `Active account: true`.

The best engineering principle here: **Do not test LLMs with prompts, and do not test humans with memory. Intercept physically at the Shell environment layer.**

We can achieve seamless isolation using a transparent Shell wrapper for `gh`.

#### Writing the Transparent `gh` Wrapper Script

Place an executable named `gh` in a directory prioritized in your `PATH` (such as `~/bin/gh`), having it inject the appropriate `GH_TOKEN` into the real `/opt/homebrew/bin/gh` based on the current working directory (`$PWD`):

```bash
#!/bin/bash
# Automatically select GitHub account token based on current working directory
# Directory mapping:
#   ~/dev/personal/  -> personal account
#   ~/dev/work/      -> work account

# Absolute path to real Homebrew-installed gh binary
REAL_GH="/opt/homebrew/bin/gh"

case "$PWD/" in
  *"$HOME/dev/work/"*)
    TARGET_USER="work-user"
    ;;
  *"$HOME/dev/personal/"*)
    TARGET_USER="personal-user"
    ;;
  *)
    TARGET_USER=""
    ;;
esac

if [ -n "$TARGET_USER" ]; then
  TOKEN="$("$REAL_GH" auth token --user "$TARGET_USER" 2>/dev/null)"
  if [ -n "$TOKEN" ]; then
    export GH_TOKEN="$TOKEN"
  fi
fi

exec "$REAL_GH" "$@"
```

Make the script executable: `chmod +x ~/bin/gh`.

#### Verification and Results Comparison

Once configured, verify behavior across directories to observe the difference between native `gh` and the wrapper:

1. **Verify personal directory (terminal and agents alike)**:
   ```bash
   cd ~/dev/personal/my-repo
   gh api user --jq .login
   # Native gh: returns default active account (e.g. work-user, risking wrong account)
   # With Wrapper: returns personal-user (automatically matches personal token)
   ```

2. **Verify work directory (terminal and agents alike)**:
   ```bash
   cd ~/dev/work/company-repo
   gh api user --jq .login
   # Native gh: returns default active account
   # With Wrapper: returns work-user (automatically matches work token)
   ```

3. **Verify AI Agent subshell execution (non-interactive subshell)**:
   ```bash
   zsh -c "cd ~/dev/personal/my-repo && gh api user --jq .login"
   # Output: personal-user
   ```

Now, whether typing `gh` manually in the terminal or letting an AI agent run child processes in the background, the system intercepts calls via this wrapper based on directory—achieving frictionless bidirectional isolation.

{{< /gemini >}}

### Crucial Details: Subshell and Zsh Startup Priorities

When implementing this shell wrapper in practice, two subtleties regarding shell environment variable inheritance are critical. Overlooking them can result in the wrapper working in your interactive terminal while background AI agents silently bypass it:

#### 1. Non-Interactive Subshells Require `~/.zshenv`

When AI coding agents like Claude Code or Devin run shell commands via child processes (e.g. `exec("gh ...")`), they spawn **non-interactive subshells**.

Under Zsh:
- **`~/.zshrc`**: Loaded only in interactive shells (e.g., standard interactive terminal windows).
- **`~/.zshenv`**: Always loaded on any shell startup, including non-interactive subshells.

If you export your `PATH` only in `~/.zshrc`, interactive terminals intercept calls properly, but background agents bypass the wrapper and run the default `/opt/homebrew/bin/gh`.

Therefore, make sure `~/bin` is prepended inside `~/.zshenv`:

```zsh
# Prepend PATH in ~/.zshenv so subshells and agents use the wrapper
export PATH="$HOME/bin:$HOME/.local/bin:$PATH"
```

#### 2. Resetting PATH Preemption from `brew shellenv`

If your `~/.zshrc` executes `eval "$(/opt/homebrew/bin/brew shellenv)"`, Homebrew will prepend `/opt/homebrew/bin` to the front of `PATH`.

Be sure to re-prepend `~/bin` to `PATH` after `brew shellenv` runs:

```zsh
# ~/.zshrc
eval "$(/opt/homebrew/bin/brew shellenv)"

# Ensure ~/bin stays ahead of /opt/homebrew/bin
export PATH="$HOME/bin:$HOME/.local/bin:$PATH"
```

### Summary

With this end-to-end setup, we not only fixed past commit mistakes but also established an automated multi-identity system:

- **Emergency Fix Layer**: Use `git commit --amend` or the standard tool `git-filter-repo` to rapidly clean up pushed commit history.
- **Git Commit / SSH Identity Layer**: Use `includeIf` and `insteadOf` in `~/.gitconfig` to automatically match commit emails and SSH keys based on project path.
- **GitHub CLI / AI Agent Layer**: Use the `~/bin/gh` transparent wrapper combined with `~/.zshenv` environment interception to physically isolate accounts for both command-line terminals and AI agents like Claude Code and Devin.

Offloading account switching to shell-level mechanics ensures that as long as projects are in the right directory, every manual commit, PR creation, or automated API call from an agent uses the correct identity—with no confusion or accidental cross-account leakage.
