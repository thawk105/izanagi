## 変更した file

- [condition_meaning_gate.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2153-author/orchestrator/campaign/condition_meaning_gate.py:161)  
  8 macro の registry、新宣言型、factory、枝切り出し、二値観測、green schema を実装。旧 BACKOFF witness と CLI を固定した。
- [s3_lock_coverage.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2153-author/orchestrator/campaign/s3_lock_coverage.py:97)  
  runtime meaning の宣言を factory から取得するよう変更。
- [s5_permutation_coverage.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2153-author/orchestrator/campaign/s5_permutation_coverage.py:94)  
  permutation 2 macro を factory へ配線。
- [t152_write_intent_coverage.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2153-author/orchestrator/campaign/t152_write_intent_coverage.py:194)  
  write-intent 4 macro を factory へ配線。
- [screening_driver.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2153-author/orchestrator/campaign/screening_driver.py:176)  
  各 request の meaning 宣言を factory から取得。
- [test_condition_meaning_gate.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2153-author/orchestrator/tests/test_condition_meaning_gate.py:583)  
  実 patch 照合、8 正例、非識別・入れ子・重複・endif 欠落・旧型・未登録・schema の負例を追加。
- [test_s5_permutation_coverage.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2153-author/orchestrator/tests/test_s5_permutation_coverage.py:86)  
  S3/S5 の factory 配線と exact declaration 引き渡しを検査。
- [test_t152_write_intent_coverage.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2153-author/orchestrator/tests/test_t152_write_intent_coverage.py:880)  
  preflight が factory を使用することを固定。
- [test_screening_driver.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2153-author/orchestrator/tests/test_screening_driver.py:226)  
  screening の全 request が factory を経由することを固定。

## 実装の要点

- registry: [condition_meaning_gate.py:161](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2153-author/orchestrator/campaign/condition_meaning_gate.py:161) に macro、所有 path、開始指令だけを保持。
- factory: [condition_meaning_gate.py:784](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2153-author/orchestrator/campaign/condition_meaning_gate.py:784) で要求値 1、既定値 0 の対だけ宣言。その他は `None`。
- 切り出し: [condition_meaning_gate.py:2214](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2153-author/orchestrator/campaign/condition_meaning_gate.py:2214) で開始指令一意性、深さ 0、対応 `#endif` を検査。
- 観測: [condition_meaning_gate.py:2303](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2153-author/orchestrator/campaign/condition_meaning_gate.py:2303) で要求値と既定値を実コンパイラ前処理。同一観測は `compile-time-branch-selection-not-discriminating` で赤。
- 旧型固定: [condition_meaning_gate.py:449](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2153-author/orchestrator/campaign/condition_meaning_gate.py:449) と [condition_meaning_gate.py:3063](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2153-author/orchestrator/campaign/condition_meaning_gate.py:3063) を `BACKOFF_FIXED` 専用に固定。
- schema: [condition_meaning_gate.py:2777](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2153-author/orchestrator/campaign/condition_meaning_gate.py:2777) と [condition_meaning_gate.py:2871](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2153-author/orchestrator/campaign/condition_meaning_gate.py:2871) で source、指令、1/0 観測、argv、compiler identity を exact 検査。

## 走らせた検査

- `git diff --check`: 緑。
- production 5 module import: 緑。
- 変更した test 4 module import: `PYTHONPATH=orchestrator/tests` で緑。
- `python3 tools/check_codex_agents.py`: 緑。
- `python3 tools/check_docs.py`: 緑。
- `test_condition_meaning_gate.py` 全体、追加正負 nodeid、driver 3 file、`test_ccbench_spawn_sites.py`、`test_update_acceptance_duration_ledger.py`: 実装済み・未実走。

pytest は指定 runner で5回試行したが、すべて `qstat -Q` の `EACCTAUTH Unknown user-id` により child 起動前に rc=16。内訳は green 0、red 0、未起動。生成された試行 receipt は除去済み。

## 意図的な赤

無し。

## 波及の可能性

- `MEANING_SUPPORTED_MACROS` は 1 件から 9 件へ増えるが、旧型 constructor の全 caller は静的監査し、いずれも `BACKOFF_FIXED` 固定だった。
- registry 外の 13 macro と所有外 driver は従来どおり `unestablished`。
- 新規 test nodeid の acceptance duration 台帳追随は段 7 の親作業。台帳は編集していない。
- 新 proof kind の evidence を独自に exact 解釈する外部 consumer があれば追随が必要。repo 内に該当 reader は見つからなかった。

## 受理・拒否の挙動

変更前は対象 8 macro が常に `unestablished` だった。変更後は正しい 1/0 枝なら green、非識別、入れ子、開始指令重複、対応 `#endif` 欠落なら red になる。

registry 外、値対不一致、旧型への非 `BACKOFF_FIXED` 指定は受理されない。従来拒否されていた入力を新たに受理する変更はない。

## 総括

裁定 v2 の8 macroだけを compile-time 枝選択 witnessへ移した。  
旧 BACKOFF 復号器の受理面は固定した。  
許可された9ファイル以外は変更していない。  
pytest は基盤エラーにより実装済み・未実走であり、closed とは申告しない。