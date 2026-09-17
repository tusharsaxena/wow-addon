#!/usr/bin/env python3
"""Tests for scripts/bounded_runs.py -- run: python3 scripts/test_bounded_runs.py"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bounded_runs  # noqa: E402


def repo(kit_version=None):
    d = tempfile.mkdtemp()
    if kit_version is not None:
        os.makedirs(os.path.join(d, "tests", "_kit"))
        with open(os.path.join(d, "tests", "_kit", "framework.lua"), "w") as f:
            f.write("local Kit = {}\nKit.VERSION = %d\n" % kit_version)
    return d


class Matcher(unittest.TestCase):
    def setUp(self):
        self.old = repo(22)
        self.new = repo(23)

    def denied(self, command, cwd=None):
        return bounded_runs.check(command, cwd or self.old)

    # ── refused ──
    def test_plain_runs_are_refused(self):
        for cmd in ("lua tests/run.lua", "lua5.1 tests/run.lua -j auto", "lua tests/perf.lua",
                    "luacheck .", "lizard -l lua .", "tests/_kit/run-automated-tests.sh --no-bundle",
                    "bash tests/_kit/run-automated-tests.sh", "./tests/_kit/run-automated-tests.sh"):
            self.assertTrue(self.denied(cmd), cmd)

    def test_refused_inside_compound_commands(self):
        for cmd in ("cd KickCD && lua tests/run.lua > out.txt 2>&1",
                    "git status; luacheck . | tail -3",
                    "(cd x; lua tests/run.lua)",
                    "out=$(lua tests/run.lua --list)",
                    "FOO=1 env lua tests/run.lua",
                    "timeout 60 lua tests/run.lua"):  # a timeout alone is not a memory bound
            self.assertTrue(self.denied(cmd), cmd)

    def test_old_kit_lua_run_refused_through_cd(self):
        parent = os.path.dirname(self.old)
        name = os.path.basename(self.old)
        self.assertTrue(bounded_runs.check("cd %s && lua tests/run.lua" % name, parent))

    # ── allowed ──
    def test_wrapper_passes(self):
        for cmd in ("ka0s-bounded lua tests/run.lua",
                    "~/.claude/wow-addon/bin/ka0s-bounded luacheck .",
                    "cd X && /opt/p/scripts/ka0s-bounded tests/_kit/run-automated-tests.sh",
                    "KA0S_KIT_PROC_MB=4096 ka0s-bounded lua tests/run.lua"):
            self.assertEqual(self.denied(cmd), [], cmd)

    def test_bounded_by_hand_passes(self):
        self.assertEqual(self.denied("(ulimit -v 2097152; timeout 180 lua tests/run.lua > o 2>&1)"), [])

    def test_inline_opt_out_passes(self):
        self.assertEqual(self.denied("KA0S_BOUNDED_HOOK=off lua tests/run.lua"), [])

    def test_self_guarding_kit_passes_for_lua_only(self):
        self.assertEqual(self.denied("lua tests/run.lua", self.new), [])
        self.assertEqual(self.denied("lua %s/tests/perf.lua" % self.new, "/"), [])
        self.assertTrue(self.denied("luacheck .", self.new))

    def test_mentions_are_not_runs(self):
        for cmd in ("grep -n lua tests/run.lua", "git diff tests/run.lua", "cat tests/run.lua",
                    "luacheck --version", "lizard --help", "echo 'lua tests/run.lua'",
                    "sed -n 1,20p tests/_kit/run-automated-tests.sh", "lua -v",
                    "lua tools/gen-api-members.lua", "which luacheck lizard"):
            self.assertEqual(self.denied(cmd), [], cmd)


class HookScript(unittest.TestCase):
    def run_hook(self, command, cwd):
        payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}, "cwd": cwd})
        env = dict(os.environ, CLAUDE_PLUGIN_ROOT=os.path.dirname(HERE), HOME=tempfile.mkdtemp())
        p = subprocess.run(["bash", os.path.join(HERE, "bounded-runs-hook.sh")], input=payload,
                           capture_output=True, text=True, env=env, timeout=30)
        return p, env["HOME"]

    def test_denies_with_the_wrapper_path_and_installs_the_link(self):
        p, home = self.run_hook("lua tests/run.lua", repo(22))
        self.assertEqual(p.returncode, 0)
        out = json.loads(p.stdout)["hookSpecificOutput"]
        self.assertEqual(out["permissionDecision"], "deny")
        self.assertIn("ka0s-bounded", out["permissionDecisionReason"])
        link = os.path.join(home, ".claude", "wow-addon", "bin", "ka0s-bounded")
        self.assertTrue(os.path.islink(link))
        self.assertTrue(os.access(os.path.realpath(link), os.X_OK))

    def test_silent_on_ordinary_commands(self):
        p, _ = self.run_hook("git status", repo())
        self.assertEqual((p.returncode, p.stdout), (0, ""))

    def test_fails_open_on_garbage(self):
        env = dict(os.environ, CLAUDE_PLUGIN_ROOT=os.path.dirname(HERE), HOME=tempfile.mkdtemp())
        p = subprocess.run(["bash", os.path.join(HERE, "bounded-runs-hook.sh")], input="not json lua",
                           capture_output=True, text=True, env=env, timeout=30)
        self.assertEqual((p.returncode, p.stdout), (0, ""))


if __name__ == "__main__":
    unittest.main()
