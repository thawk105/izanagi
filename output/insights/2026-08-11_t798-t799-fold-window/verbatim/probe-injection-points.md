# probe の注入点 (逐語)

`authority: none` / `default_effect: no-state-change`。
実行可能な probe は repo 外 (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t798-t799-fold-window/probe/`)
に置き、ここには**何をどこへ注入したか**の逐語だけを残す ([T-317] 裁定)。

## 1. [T-798] の crash 注入 — fixture 側の `tools/check_docs.py`

本番 `_fold_main_locked` は窓の先頭で `_validate_generated_docs` を呼び、そこから
`tools/check_docs.py` を `cwd=repository.main` の subprocess として起動する
(`tools/dev_wave_land.py:1795-1816`)。したがってこの script の `getppid()` は land process である。
fixture の `check_docs.py` を次にすると、**land 本体を一切改変せずに窓の内側で SIGKILL できる。**

```python
import os
import signal
import sys
WORKLOG_ROTATE_BYTES = 100000


def main() -> int:
    with open(os.path.join("..", "check_docs_invoked"), "w") as handle:
        handle.write("invoked\n")
    os.kill(os.getppid(), signal.SIGKILL)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

注入点が窓の内側である根拠 (`tools/dev_wave_land.py`):

```
1871         fold_paths = _fold_plan_paths(plan)
1872         fold.apply_fold(repository.main, plan)      ← ここで state を unlink する
1873         _validate_generated_docs(repository)        ← crash 注入点 (窓の内側)
...
1911         commit = _git(repository.main, "commit", ...)   ← 窓の出口
```

`apply_fold` の state unlink は `tools/spool_fold.py:2357` (`state_path.unlink()`) で、
GC の直後・return の直前にある。

**注意 (fixture 設計の落とし穴):** `tools/spool_fold.py:1806-1832` の `_load_rotate_limit` は
`tools/check_docs.py` を **land process 内で `exec_module`** する。最初に書いた stub が
module 直下で `raise SystemExit(0)` していたため、`except Exception` を素通りして
**land process が出力ゼロ・rc=0 で静かに消えた**。実物と同じく `if __name__ == "__main__":` で
囲って解決した。この形自体は付随所見として `package.md` の Q4 に起票候補として載せている。

## 2. [T-799] の残存 state 生成 — 本番 `apply_fold` に書かせる

state を手で捏造せず、本番の write path に書かせる。plan 構築後に fragment 本体を 1 行増やすと、
`apply_fold` は state を書いた**後**に GC 照合で `TransactionError` を投げるので、
canonical 未適用・state 残存の形が残る。その後 fragment を戻せば tree は清浄になる。

```python
def leave_active_state(main_wt: Path, fragment: Path) -> str:
    plan = FOLD.plan_fold(main_wt, fold_date="2026-08-11")
    original = fragment.read_bytes()
    fragment.write_bytes(original + "\n- 後から足した 1 行\n".encode("utf-8"))
    try:
        FOLD.apply_fold(main_wt, plan)
    except FOLD.TransactionError as exc:
        reason = str(exc)
    else:
        reason = "(apply_fold が成功してしまった)"
    fragment.write_bytes(original)
    return reason
```

順序の根拠 (`tools/spool_fold.py`):

```
2292-2293   state_data = json.dumps(_plan_state(plan) ...)   ← state を先に書く
2293        _atomic_write(state_path, state_data)
2298-2311   target 状態の確定 (before/after/第三状態)         ← ここは通る
2315-2325   GC target の content 照合                        ← ここで raise する
2333-2341   canonical の書込み                              ← 到達しない
```

実測した停止理由: `docs/spool/worklog/2026-08-02-wave-a-1.md: GC target content が transaction と不一致`

## 3. fixture が本番のどこを実体で使っているか

```python
REPO_ROOT = Path(os.environ["IZANAGI_REPO"]).resolve()
sys.path.insert(0, str(REPO_ROOT / "orchestrator" / "tests"))
import test_dev_wave_land as LANDTEST      # LANDTEST.LAND  = tools/dev_wave_land.py の実体
import test_spool_fold as FOLDTEST         # FOLDTEST.spool_fold = tools/spool_fold.py の実体
```

`tools/spool_fold.py` は standalone CLI の測定用に fixture repo の `tools/` へ **bytes ごと複製**した
(`main()` が `Path(__file__).resolve().parents[1]` を repo とみなすため)。改変はしていない。
