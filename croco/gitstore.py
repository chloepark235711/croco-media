"""Compare-and-swap style git store.

Every state change is a commit pushed with a plain (non-force) push. If another
worker pushed first the push is rejected, we re-sync to the remote tip and
re-evaluate the transaction function. That gives atomic, race-free updates
without a server (used for episode state and the private budget ledger).
"""
import os
import random
import subprocess
import time


class Conflict(Exception):
    pass


class GitStore:
    def __init__(self, workdir, remote, branch="main", retries=10,
                 author=("croco-bot", "croco-bot@users.noreply.github.com"), allowed=None):
        self.workdir, self.remote, self.branch = workdir, remote, branch
        self.retries, self.author = retries, author
        self.allowed = allowed  # tuple of path prefixes this worker may write; None = any

    def _git(self, *args, check=True):
        env = dict(os.environ, GIT_TERMINAL_PROMPT="0",
                   GIT_AUTHOR_NAME=self.author[0], GIT_AUTHOR_EMAIL=self.author[1],
                   GIT_COMMITTER_NAME=self.author[0], GIT_COMMITTER_EMAIL=self.author[1])
        return subprocess.run(["git", "-C", self.workdir, *args], env=env, check=check,
                              capture_output=True, text=True)

    def sync(self):
        if not os.path.isdir(os.path.join(self.workdir, ".git")):
            os.makedirs(self.workdir, exist_ok=True)
            subprocess.run(["git", "clone", "-q", "--branch", self.branch, self.remote,
                            self.workdir], check=True, capture_output=True, text=True)
        else:
            self._git("fetch", "-q", "origin", self.branch)
            self._git("reset", "-q", "--hard", f"origin/{self.branch}")
            self._git("clean", "-qfd")

    def transact(self, fn, message):
        """fn(workdir) -> list of changed relative paths, or falsy to abort.
        Returns commit sha, or None if fn made no change."""
        for attempt in range(self.retries):
            self.sync()
            changed = fn(self.workdir)
            if not changed:
                return None
            if self.allowed is not None:
                dirty = [l[3:] for l in self._git("status", "--porcelain").stdout.splitlines()]
                for c in list(changed) + dirty:
                    if not c.startswith(self.allowed):
                        self._git("reset", "-q", "--hard", f"origin/{self.branch}")
                        raise PermissionError(f"write outside allowed paths refused: {c}")
            self._git("add", "--", *changed)
            self._git("commit", "-q", "-m", message)
            r = self._git("push", "-q", "origin", f"HEAD:{self.branch}", check=False)
            if r.returncode == 0:
                return self._git("rev-parse", "HEAD").stdout.strip()
            time.sleep(random.uniform(0.05, 0.3) * (attempt + 1))
        raise Conflict(f"could not push after {self.retries} attempts")

    def bot_touched(self, prefix):
        """True if the bot identity ever authored/committed a change under prefix."""
        out = self._git("log", "--format=%ae%n%ce", "--", prefix, check=False).stdout.split()
        return self.author[1] in out
