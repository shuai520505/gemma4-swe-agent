"""Bounded, opt-in verification of an Agent-owned Python assertion reproducer.

Runs only through the organizer's sandbox skill executor. A SUPPORTED verdict
means an unchanged source tree passed this particular executed assertion script,
never semantic correctness, Issue coverage, or Native Resolved. No host callback,
tool wrapping, hidden tests, model calls, package installs, or submit hook.
"""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time

MAX_FILES = 30000
MAX_SOURCE_BYTES = 64 * 1024 * 1024
MAX_CHECK_BYTES = 64 * 1024
REPORT_PREFIX = "MEER_CHILD_REPORT="


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def git(root, *args):
    p = subprocess.run(["git", "-C", str(root), *args], capture_output=True,
                       timeout=5, check=True)
    return p.stdout


def tree_identity(root):
    """Hash tracked regular files, not just the files the model says it edited.

    Untracked files (including diagnostics) also invalidate evidence. Excludes
    only Git/cache/build artifacts; protected tests are read as normal public
    workspace data, never overlaid evaluator tests. Symlinks fail closed.
    """
    names = set(git(root, "ls-files", "-z").decode().split("\0"))
    names.update(git(root, "ls-files", "--others", "--exclude-standard", "-z").decode().split("\0"))
    names.discard("")
    # Official skill executor creates a fresh .adk_exec_<id>.py each call.
    names = {n for n in names if not (n.startswith(".adk_exec_") and n.endswith(".py"))
             and not set(Path(n).parts).intersection({'__pycache__', '.pytest_cache'})}
    if len(names) > MAX_FILES:
        raise ValueError("Source file budget exceeded")
    rows = {}; size = 0
    for name in sorted(names):
        p = root / name
        if p.is_symlink() or not p.resolve().is_relative_to(root):
            raise ValueError("Source symlink or path escape")
        # Deleted tracked source files are still part of the identity.
        if not p.exists():
            rows[name] = None
            continue
        if not p.is_file():
            raise ValueError("Non-regular source file")
        size += p.stat().st_size
        if size > MAX_SOURCE_BYTES:
            raise ValueError("Source byte budget exceeded")
        rows[name] = sha(p.read_bytes())
    return sha(json.dumps(rows, sort_keys=True).encode()), len(rows), size


class InstrumentAssertions(ast.NodeTransformer):
    """Count evaluated, non-constant asserts; never alter a file on disk."""
    def visit_Assert(self, node):
        self.generic_visit(node)
        dynamic = any(isinstance(n, (ast.Name, ast.Call, ast.Attribute, ast.Subscript))
                      for n in ast.walk(node.test))
        node.test = ast.copy_location(ast.Call(
            func=ast.Name(id="__meer_observe_assert__", ctx=ast.Load()),
            args=[node.test, ast.Constant(node.lineno), ast.Constant(dynamic)],
            keywords=[]), node.test)
        return node


def child(check, workspace):
    counts = dict(executed_assertions=0, nonconstant_assertions=0,
                  failed_assertions=0, exception_type=None)
    def observe(value, line, nonconstant):
        counts['executed_assertions'] += 1
        counts['nonconstant_assertions'] += int(nonconstant)
        passed = bool(value)
        counts['failed_assertions'] += int(not passed)
        return passed
    exit_code = 0
    try:
        os.chdir(workspace)
        sys.path.insert(0, str(workspace))
        source = check.read_text(encoding='utf-8')
        code = compile(ast.fix_missing_locations(InstrumentAssertions().visit(ast.parse(source))),
                       str(check), 'exec', optimize=0)
        exec(code, dict(__name__='__main__', __file__=str(check),
                        __meer_observe_assert__=observe))
    except BaseException as exc:
        counts['exception_type'] = type(exc).__name__
        exit_code = 1
    print(REPORT_PREFIX + json.dumps(counts), flush=True)
    return exit_code


def kill_group(process):
    if os.name == 'posix':
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    elif process.poll() is None:
        process.kill()
    process.wait(timeout=5)


def verify(workspace, check, seconds=10, state_dir=None):
    begin = time.perf_counter()
    report = dict(schema='MEER_EVIDENCE_V1', verdict='UNKNOWN',
                  semantic_correctness='UNKNOWN', native_resolved=None,
                  new_evidence=False, subprocess_invocations=0,
                  executed_assertions=None, nonconstant_assertions=None,
                  failed_assertions=None, timed_out=False,
                  source_unchanged_during_check=None,
                  scope='OPT_IN_ASSERTION_REPRODUCER_ONLY',
                  global_submit_gate=False, global_tool_gate=False)
    try:
        workspace = Path(workspace).resolve(strict=True)
        requested = Path(check)
        if requested.is_symlink():
            raise ValueError('Symlink reproducer refused')
        check = requested.resolve(strict=True)
        # Reproducer must be Agent-owned scratch outside the repository. This
        # helper never rewrites repository tests/config or trusted evaluator files.
        if check.is_relative_to(workspace) or not check.is_file():
            raise ValueError('Use an Agent-owned scratch reproducer outside the repository')
        if check.stat().st_size > MAX_CHECK_BYTES or check.suffix != '.py':
            raise ValueError('Invalid reproducer size or extension')
        if not 0 < seconds <= 15:
            raise ValueError('Per-check time must be in (0, 15] seconds')
        before, count, size = tree_identity(workspace)
        check_sha = sha(check.read_bytes())
        report.update(source_sha256=before, source_files=count, source_bytes=size,
                      check_sha256=check_sha, check_timeout_seconds=seconds)
        key = sha((before + check_sha).encode())
        if state_dir is None:
            state_dir = Path(tempfile.gettempdir()) / ('meer-' + sha(str(workspace).encode())[:16])
        state_dir = Path(state_dir)
        if state_dir.is_symlink():
            raise ValueError('Symlink state directory refused')
        state_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        receipt = state_dir / 'receipt.json'
        if receipt.is_symlink():
            raise ValueError('Symlink receipt refused')
        if receipt.exists():
            prior = json.loads(receipt.read_bytes())
            if prior.get('key') == key:
                report.update(verdict='OBSERVED', reason='REPEATED_UNCHANGED_CHECK_NOT_EXECUTED',
                              prior_verdict=prior.get('verdict'), evidence_fresh=False)
                return report
        with tempfile.TemporaryFile() as log:
            p = subprocess.Popen([sys.executable, str(Path(__file__).resolve()),
                                  '--child', '--workspace', str(workspace), '--check', str(check)],
                                 cwd=workspace, stdout=log, stderr=subprocess.STDOUT,
                                 start_new_session=os.name == 'posix')
            report['subprocess_invocations'] = 1
            try:
                p.wait(timeout=seconds)
            except subprocess.TimeoutExpired:
                report.update(timed_out=True, reason='LOCAL_VERIFICATION_TIMEOUT')
            finally:
                kill_group(p)
            log.seek(0, os.SEEK_END)
            output_size = log.tell()
            log.seek(max(0, output_size - 65536))
            output = log.read().decode('utf-8', errors='replace')
        after, _, _ = tree_identity(workspace)
        unchanged = before == after and check_sha == sha(check.read_bytes())
        report.update(source_unchanged_during_check=unchanged,
                      new_evidence=True, child_exit_code=p.returncode,
                      captured_output_bytes=output_size)
        # Last line must be our own report; a model-written log is not accepted as
        # an input receipt. Agent-owned code is still untrusted (see limitations).
        rows = [x[len(REPORT_PREFIX):] for x in output.splitlines() if x.startswith(REPORT_PREFIX)]
        stats = json.loads(rows[-1]) if rows else {}
        for name in ('executed_assertions', 'nonconstant_assertions', 'failed_assertions', 'exception_type'):
            report[name] = stats.get(name)
        if report['timed_out']:
            pass
        elif not unchanged:
            report['reason'] = 'SOURCE_OR_CHECK_CHANGED_DURING_VERIFICATION'
        elif p.returncode != 0 or stats.get('failed_assertions', 0) > 0:
            report.update(verdict='CONTRADICTED', reason='LOCAL_CHECK_FAILED')
        elif stats.get('nonconstant_assertions', 0) <= 0:
            report['reason'] = 'NO_EXECUTED_NONCONSTANT_ASSERTION'
        else:
            report.update(verdict='SUPPORTED', reason='THIS_ASSERTION_CHECK_PASSED', evidence_fresh=True)
        # Scratch receipt is a convenience cache, not a security attestation.
        data=json.dumps(dict(key=key, verdict=report['verdict']))
        fd, temporary = tempfile.mkstemp(dir=state_dir)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(data)
            os.replace(temporary, receipt)
        finally:
            Path(temporary).unlink(missing_ok=True)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        report.update(verdict='UNKNOWN', reason='EVIDENCE_UNAVAILABLE', error_type=type(exc).__name__)
    finally:
        report['wall_seconds'] = time.perf_counter() - begin
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--workspace', default='/workspace')
    p.add_argument('--check', required=True)
    p.add_argument('--seconds', type=float, default=10)
    p.add_argument('--child', action='store_true', help=argparse.SUPPRESS)
    args = p.parse_args()
    if args.child:
        return child(Path(args.check), Path(args.workspace))
    print(json.dumps(verify(args.workspace, args.check, args.seconds), sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
