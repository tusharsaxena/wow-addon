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

    def test_bare_wrapper_name_passes(self):
        # bin/ka0s-bounded puts the bare name on the plugin's PATH entry, so specs may drop the path.
        for cmd in ("ka0s-bounded lua tests/run.lua", "ka0s-bounded lua5.1 tests/perf.lua",
                    "ka0s-bounded luacheck .", "ka0s-bounded lizard -l lua .",
                    "ka0s-bounded tests/_kit/run-automated-tests.sh --no-bundle",
                    "/opt/p/bin/ka0s-bounded lua tests/run.lua"):
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

    # ── command position only (ATS-22): prose in heredocs and quotes is not a run ──
    def test_heredoc_body_is_not_a_run(self):
        for cmd in ("cat > notes.md <<'EOF'\nThe lizard gate passed.\nlizard -l lua .\nluacheck .\nEOF",
                    "cat > a.md <<EOF\nlua tests/run.lua\nEOF\ngit add a.md",
                    "python3 - <<'PY'\nimport os\nos.system('echo lizard')\nPY",
                    "git commit -F - <<'MSG'\nWA-ATS-01: lizard in prose\n\nrun-automated-tests.sh too\nMSG",
                    "cat <<-EOF > f\n\tlizard .\n\tEOF"):
            self.assertEqual(self.denied(cmd), [], cmd)

    def test_quoted_prose_is_not_a_run(self):
        for cmd in ('git commit -m "x; lizard is fine"', 'echo "(lua tests/run.lua)"',
                    "echo 'a && luacheck . | tail'", 'printf "%s\\n" "run: lizard -l lua ."',
                    "grep -n 'lua tests/run.lua; lizard' docs/x.md"):
            self.assertEqual(self.denied(cmd), [], cmd)

    def test_bare_runs_are_still_refused_next_to_prose(self):
        for cmd in ("lizard -l lua .",
                    "cat > f <<'EOF'\nprose\nEOF\nlizard -l lua .",
                    "cat > f <<EOF; luacheck .\nbody\nEOF",
                    'echo "done: $(lizard -l lua .)"',
                    "echo `luacheck .`",
                    "bash <<'EOF'\nlizard -l lua .\nEOF",
                    "{ luacheck .; }", "if lua tests/run.lua; then echo ok; fi",
                    "lua tests/run.lua > out.txt 2>&1 &"):
            self.assertTrue(self.denied(cmd), cmd)


class BinWrapper(unittest.TestCase):
    """bin/ka0s-bounded: the POSIX exec wrapper that puts the runner on the plugin's PATH entry."""
    PATH = os.path.join(os.path.dirname(HERE), "bin", "ka0s-bounded")

    def test_is_an_executable_lf_posix_script(self):
        self.assertTrue(os.path.isfile(self.PATH))
        self.assertTrue(os.access(self.PATH, os.X_OK))
        with open(self.PATH, "rb") as f:
            body = f.read()
        self.assertTrue(body.startswith(b"#!/bin/sh\n"))
        self.assertNotIn(b"\r", body)
        self.assertEqual(subprocess.run(["sh", "-n", self.PATH]).returncode, 0)

    def test_tracked_as_executable(self):
        p = subprocess.run(["git", "ls-files", "-s", "--", "bin/ka0s-bounded"], cwd=os.path.dirname(HERE),
                           capture_output=True, text=True)
        if p.returncode != 0 or not p.stdout:
            self.skipTest("not in a git checkout, or not yet staged")
        self.assertTrue(p.stdout.startswith("100755 "), p.stdout)

    def run_wrapper(self, *args):
        env = dict(os.environ, XDG_CACHE_HOME=tempfile.mkdtemp(), KA0S_KIT_CGROUP="off")
        env.pop("KA0S_BOUNDED_DEPTH", None)
        return subprocess.run([self.PATH, *args], capture_output=True, text=True, env=env, timeout=60)

    def test_runs_a_command_through_the_runner(self):
        p = self.run_wrapper("true")
        self.assertEqual(p.returncode, 0, p.stderr)
        p = self.run_wrapper("sh", "-c", "echo $KA0S_BOUNDED_DEPTH; exit 3")
        self.assertEqual((p.returncode, p.stdout.strip()), (3, "1"))  # exit code and runner env pass through

    def test_no_arguments_is_the_runners_usage_error(self):
        p = self.run_wrapper()
        self.assertEqual(p.returncode, 2)
        self.assertIn("usage: ka0s-bounded", p.stderr)


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

    def test_heredoc_prose_passes_and_a_bare_lizard_run_is_denied(self):
        p, _ = self.run_hook("cat > ANALYSIS.md <<'EOF'\nlizard -l lua . reported no function above 15\nEOF",
                             repo())
        self.assertEqual((p.returncode, p.stdout), (0, ""))
        p, _ = self.run_hook("lizard -l lua .", repo())
        self.assertEqual(json.loads(p.stdout)["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_fails_open_on_garbage(self):
        env = dict(os.environ, CLAUDE_PLUGIN_ROOT=os.path.dirname(HERE), HOME=tempfile.mkdtemp())
        p = subprocess.run(["bash", os.path.join(HERE, "bounded-runs-hook.sh")], input="not json lua",
                           capture_output=True, text=True, env=env, timeout=30)
        self.assertEqual((p.returncode, p.stdout), (0, ""))


if __name__ == "__main__":
    unittest.main()
