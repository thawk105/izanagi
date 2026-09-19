# scan_sampler.py (逐語)

Codex author 作の login 側 sampler (job dir で実行、repo には入れない)。出力は ../sampler-meas-1.jsonl。

```python
"""Read-only Git scan sampler; run outside the measured worktree."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time


def process_counts(self_tag: str) -> tuple[int, int]:
    leaders = workers = 0
    for path in Path('/proc').glob('[0-9]*/cmdline'):
        try:
            command = path.read_bytes().replace(b'\0', b' ').decode(errors='replace')
        except (OSError, ProcessLookupError):
            continue
        leaders += int('dev_wave_wait.py' in command and ' acceptance' in command
                       and self_tag not in command and '--self-tag' not in command)
        workers += int('run_tests.py' in command)
    return leaders, workers


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('repo-root', 'worktree', 'out', 'stop-file'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--interval-seconds', type=float, required=True)
    parser.add_argument('--max-samples', type=int, required=True)
    parser.add_argument('--self-tag', required=True)
    args = parser.parse_args()
    if not args.repo_root.is_absolute() or not args.worktree.is_absolute():
        parser.error('--repo-root and --worktree must be absolute')
    if args.interval_seconds <= 0 or args.max_samples <= 0 or not args.self_tag:
        parser.error('interval, max-samples and self-tag must be positive/nonempty')
    worktree = args.worktree.resolve(strict=True)
    if args.out.resolve().is_relative_to(worktree):
        parser.error('--out must be outside the measured worktree')
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(args.repo_root))
    from tools.pegasus.probes import t1259_qsub_env_delivery_probe as probe

    scans = (
        ('head', ('rev-parse', '--verify', 'HEAD')),
        ('tracked', ('status', '--porcelain=v1', '--untracked-files=no',
                     '--ignore-submodules=none')),
        ('untracked', ('ls-files', '--others', '--exclude-standard', '-z')),
        ('detached', ('symbolic-ref', '-q', 'HEAD')),
    )
    for index in range(args.max_samples):
        if args.stop_file.exists():
            break
        started = time.monotonic()
        leaders, workers = process_counts(args.self_tag)
        sample = {
            'timestamp': datetime.now(timezone.utc).isoformat(), 'sample': index,
            'loadavg': [float(v) for v in Path('/proc/loadavg').read_text().split()[:3]],
            'leaders': leaders, 'workers': workers, 'git': {}, 'sha256': {},
        }
        for name, argv in scans:
            tick = time.monotonic()
            error = None
            try:
                if name == 'detached':
                    probe._repo_is_detached(worktree, git_timeout_seconds=600.0)
                else:
                    probe._run_git(worktree, *argv, git_timeout_seconds=600.0)
            except Exception as exc:
                error = {'type': type(exc).__name__, 'message': str(exc)}
            sample['git'][name] = {
                'argv': list(argv), 'wall_seconds': time.monotonic() - tick,
                'error': error,
            }
        sample['git_total_seconds'] = sum(v['wall_seconds'] for v in sample['git'].values())
        for relative in (probe.PROBE_RELATIVE_PATH, probe.PBS_RELATIVE_PATH,
                         probe.CAMPAIGN_RELATIVE_PATH):
            tick = time.monotonic()
            error = digest = None
            try:
                digest = probe._sha256_file(worktree / relative)
            except Exception as exc:
                error = {'type': type(exc).__name__, 'message': str(exc)}
            sample['sha256'][relative] = {
                'wall_seconds': time.monotonic() - tick, 'digest': digest, 'error': error,
            }
        sample['sha256_total_seconds'] = sum(v['wall_seconds'] for v in sample['sha256'].values())
        with args.out.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(sample, ensure_ascii=False) + '\n')
        deadline = started + args.interval_seconds
        while index + 1 < args.max_samples and time.monotonic() < deadline:
            if args.stop_file.exists():
                return
            time.sleep(min(0.5, max(0, deadline - time.monotonic())))


if __name__ == '__main__':
    main()

```
