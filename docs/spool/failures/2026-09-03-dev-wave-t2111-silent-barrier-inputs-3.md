---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-03
wave: dev-wave-t2111-silent-barrier-inputs
seq: 3
---

## 新規

### {{F:mutation-container-submodule-and-resume-trap}}. 変異 harness の使い捨て worktree が submodule 未初期化で baseline を赤にし、`--resume` がその赤を回復しないため再開が空転した [手順漏れ]

- 事象: `tools/mutation_worktree.py` が作る使い捨て container は submodule を再帰初期化しない。
  復帰した snapshot 検査が `submodule is not initialized: external/ccbench/third_party/shirakami` で
  21 件落ち、baseline が `PARSE_ERROR` になって本走が始まらなかった。container の submodule を
  初期化してから `--resume` しても、harness は記録済みの赤 baseline を再走せず
  (`baseline=0 run(s)`)、同じ位置で止まり続けた。2 回の再開が空転した。
- 根本原因: container 生成が `DW-O08` の再帰初期化を含まないこと。加えて `--resume` の意味論が
  「baseline は完了済みとして再走しない」であり、baseline の赤が環境要因でも回復経路が無いこと。
  `--resume` は `--attempt-out` に**既存 file** を要求し、通常の再投入 (`--out` と `--attempt-out` を
  新 path にする、`DW-O19`) と要求が逆向きになる点も、再開を 1 回余分に失敗させた。
- 恒久対応: memory `mutation-container-needs-submodule-init` — container は起動前に
  `python3 tools/dev_wave_submodule_init.py --worktree <container>/repo` で再帰初期化し、
  baseline が赤で終わった run は `--resume` せず、初期化済みの固定 commit checkout に対して
  `tools/mutation_harness.py --repo .` を**新しい `--out`** で走らせ直す。
  **`docs/dev-wave/` へ書けなかった。** `DW-O19` は 998/1000 bytes、`DW-M05` へ 4 行足すと
  L1.5 unique footprint が 9922 > 9696 bytes で `check_docs` が赤になる (実測)。
  共有契約が新しい運用知見を吸収できない状態にあることを併せて記録する。
- 再発検知: 変異走の baseline が `PARSE_ERROR` または `submodule is not initialized` を含んだら
  実装差分へ帰属せず container の初期化状態を先に見る (同 memory の How to apply)。

## 再発

### F273

- **再発: 2026-09-04** — 受入全走を 2 回投入し、いずれも `test_codex_worker_launch.py` の
  1 件だけが落ちた。**落ちた node は 2 回で異なる** (`test_sigterm_ignoring_child_is_killed` →
  `test_limit_stop_is_never_accepted`)。中身は前者が `actual rc timeout != expected rc 1`
  (`communicate(timeout=10)` 超過、`loadavg=45.9` / `bnode082`)、後者が `assert -9 == 0`
  (`max_wall="11"` の watchdog が子を SIGKILL)。いずれも launcher の壁時計上限である。
  同エントリの再発検知手順を実行した — 並行 launcher は **8 本** (F273 の 2 回目と同水準)、
  同 file の単独走は **211 passed / rc=0 / 8.87 秒**で緑。前者の単独再走も 7.44 秒で緑。
  本 wave の差分は `orchestrator/tests/test_codex_reasoning_ab.py` 1 本だけで production は
  無変更のため、同 file への到達経路が無い。**差分へ帰属させない。**
  受入 lease が他 wave の codex 子を排除しない構造は同エントリの記載どおり未解決で、
  本 wave では機構を新設しない。
