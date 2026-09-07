## 総括

段 5 の実装を完了しました。commit は作成していません。`docs/` と counterfactual patch は未変更です。

凍結対象の SHA-256 は維持されています。

- 事前登録: `ee7617f57bf6816fd8bfb42b5830926be1174ebcca617ed122c3fbca62f127a6`
- patch C: `794b7b48dd19e30560dddc27f4408d67923d801241046df53257a8aefe82a396`

## 変更した file と、その中身 (file:line)

- [t2187_adaptive_const_probe.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265-itt-author/tools/pegasus/probes/t2187_adaptive_const_probe.py:81)
  - 反実仮想事前登録 hash helper、ASCII decimal uint64 seed parser、policy 2 必須検査を追加。
  - policy 2 の genome だけ任意 seed を使用。policy 0/1 は既定 seed を維持。
  - exact 条件でのみ hash を付与し、top-level、全 row、journal に束縛を記録。policy 2 row に seed を記録。

- [t2187_adaptive_const_probe.pbs](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265-itt-author/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:87)
  - `IZANAGI_T2187_STEP_POLICY_SEED` の検査と policy 2 必須判定を追加。
  - performance argv に非空時だけ一度渡し、certify argv は変更していません。

- [backoff_counterfactual_analysis.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265-itt-author/orchestrator/campaign/backoff_counterfactual_analysis.py:478)
  - 明示 path 専用の `analyze_counterfactual()` を新設。
  - artifact/schema/axis/hash/seed/genome/binary/trace を fail closed 検査。
  - 次窓 ITT、run 等重み、cluster SD、90/95% CI、TOST、4 種の副次層を実装。
  - zero commit、片腕欠落、12 cluster 不足は run を除外せず inconclusive。
  - CLI、glob、最新 artifact 選択、`median_tps` 比較はありません。

- [test_t2187_adaptive_const_probe.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265-itt-author/orchestrator/tests/test_t2187_adaptive_const_probe.py:1448)
  - seed 境界・書式・policy 別 genome、hash 付与範囲、journal、PBS 配線を追加。

- [test_dynamic_backoff_transitions.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265-itt-author/orchestrator/tests/test_dynamic_backoff_transitions.py:1326)
  - 既定列を保持し、別 seed の割当列を独立 LCG 計算と照合。
  - policy 0 から別 seed と LCG state が前処理後に消える検査を強化。

- [test_backoff_counterfactual_analysis.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265-itt-author/orchestrator/tests/test_backoff_counterfactual_analysis.py:160)
  - 対応づけ、最後の割当、等重み、分散、CI、境界、禁止除外、欠測、順序不変性を合成 artifact で検査。

- [test_ccbench_spawn_sites.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265-itt-author/orchestrator/tests/test_ccbench_spawn_sites.py:922)
  - deferred ledger の driver 行番号を実体の `3013` / `3382` へ追随。

- [patches/README.md](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265-itt-author/patches/README.md:289)
  - stale な `pending` 説明を exact 範囲と実 SHA-256 の契約へ更新。

## 実走したテスト (nodeid と範囲。実走していないならそう書く)

pytest nodeid は実走していません。

`tools/run_tests.py` で新解析 test 単体、および指定された4 test fileを試行しましたが、両方とも `qstat -Q preflight rc=1`、`rc=16`、`child_started=false` で終了しました。

補助検査として、pytest 外の純粋 API probeで以下を確認しました。

- 新解析の5合成ケース
- seed/parser/genome/hash/journal/PBS文字列契約
- 入力順不変性
- `git diff --check`

## 赤の内訳と帰属

- test assertion の赤: 観測なし
- runner infrastructure: 2回とも Pegasus dispatch preflight 失敗
- 帰属: queue 照会基盤。test child は起動していないため、実装の緑・赤は未確定です。

## 所有外 caller・共有 fixture・consumer test への波及 (静的列挙)

- PBS performance branch → driver の新 seed argv。
- `Genome` → source digest / buildcache。可変 seed の波及は policy 2 のみ。
- journal consumer は policy 2 row から seed、全 counterfactual row から hash を復元可能。
- certify branch、認証 exact 2 cell、既存 trace validator、grid validatorは不変。
- 新解析 module は PBS・Pegasus 登録簿から未接続で、公開面は `__all__ = ["analyze_counterfactual"]` のみ。
- deferred gate 台帳の2 build sink pinを実 lineへ更新。
- 射影外の caller は探索していません。

## 現行の受理・拒否挙動と、変えた点

従来の5/11/12-field cell、policy 0/1、seed を持たない既存 argv、certify argvは維持しました。

変更点は以下です。

- policy 2 を含む走行は明示 seed 必須。
- seed は ASCII 10進の `0..2**64-1` のみ受理。
- policy 0/1 に seed を渡しても genome は変化しない。
- counterfactual hash は exact 3腕・exact 診断軸だけに付与。
- `"pending"` は driver から生成不能。
- 解析入力の契約違反・重複 seed・hash 不一致は拒否。
- zero commit、片腕欠落、12 cluster 未満は選択的除外せず inconclusive。

## 残る不確実性

正式な4 test fileと制約 meta-testは、Pegasus dispatch 基盤障害のため未実走です。実 artifact や C++ 別 seed binaryによる end-to-end 実測も行っていません。