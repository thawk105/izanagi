---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t2117-legacy-bytes-removal
seq: 1
title: [T-2117] 復元不能な当時の bytes 一致の要求を撤去し、二経路 golden の照合を合成入力の常時実行 node へ戻した (コード + docs、branch worktree-dev-wave-t2117-legacy-bytes-removal、変異 matrix = 新旧両走・変更後 baseline PASSED / 5 KILLED・変更前 baseline PASSED / 5 SURVIVED・期待 node 完全一致)
---

## 本文

- ユーザー依頼は「復元不能な『当時の bytes 一致』要求だけを撤去し、恒久解を実装する。
  恒久 skip は採らない — 被覆を暗黙に消し絶対規律 2 に触れるためで、この裁定は動かさない。
  撤去するのは復元不能な当時の bytes 一致だけで、一般的な性質の検査は既存のまま残す。
  [T-2125] と同じ障害の重複修正にならないよう、段 1 で両者の対象を突き合わせること。
  本題の撤去と恒久解だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」。
- 一次資料は `output/insights/2026-09-16/t2117-legacy-bytes-removal/README.md`。
- **恒久解の第一段は着地済みだった。** D1382 第一段の 24 node 復帰は [T-2111] の
  `f1a2183ef` で main に入っており、台帳 ID `T-2117` の検索では 1 件も hit しない。
  段 1 で `git log --oneline -- <対象 file>` を引いて初めて分かった。
- **残差は 1 件だけだった。** `_require_pinned_rollouts` の production 呼び出しは
  `orchestrator/tests/test_codex_reasoning_ab.py:3573` の 1 箇所で、他 3 箇所は guard 自身の
  正例・負例である。恒久沈黙していたのは
  `test_m2_production_golden_requires_both_routes` の 1 node。
- **その 1 node が守っていた性質は、どの常時実行 node からも到達していなかった。**
  既存の結線検査 2 本は 3 回目の `_find_rollout` で打ち切り、合成 fixture
  `benchmark_snapshots` は `prepared_golden=` で golden 導出を迂回していた。
  **この読解は変更前の変異走 (5/5 SURVIVED) が実測で裏付けた。**
- **[T-2125] とは重複しない。** あちらは `orchestrator/campaign/artifact_admission.py` の
  `current-closure-unavailable` が主題で、対象 file が重ならない。
- **段 3 の 2 レンズが実装の罠を 2 つ先に潰した。** (a) route B へ渡るのは list ではなく
  generator で、観測のために実体化した列を実関数へ渡さないと route B が base のまま残り、
  正しい入力なのに偽の mismatch で落ちる。(b) 負例で差分の除去側まで変えると patch context
  不一致で比較へ到達する前に別の `ValidationError` が出て、「到達前の失敗」を
  「mismatch 検出」と取り違える。どちらも実装子の指示へ入れた。
- **親 brief の前提 2 つが一般化しすぎており、段 3 の両レンズが同じ箇所を指した。**
  「恒久沈黙は 1 件だけ」は `_require_pinned_rollouts` 経由に限る話であり、別 guard による
  沈黙を排除していない。「`benchmark_snapshots` を使わなければ登録簿の更新は要らない」は、
  function scope の `tmp_path` / `monkeypatch` だけを使う今回の構成に限る
  (consumer 閉包は登録済み node を seed とし他の共有 fixture も対象に含むため)。段 4 で限定した。
- **段 6 のレビュー 2 本は blocker・must-fix ゼロ。** レンズ A が事前登録 5 変異を
  1 件ずつ机上で当て、M1 (比較関数の恒真化) は負例だけが殺し正例は緑のまま、
  M2 (比較呼び出しの省略) は両方が赤という区別を予測した。**実測は予測と完全に一致した。**
  nit 2 件 (負例末尾の恒真 assert、一時 repo の commit が system git 設定に依存) は
  成果物の値・受理集合・参照を変えないので直していない。
- **変異は新旧両走で差分を示した (DW-M08)。** 変更後は baseline PASSED・5/5 KILLED、
  変更前 (`d97c423bd`) は baseline PASSED・5/5 SURVIVED で 1 node も落ちなかった。
  変更後の KILLED 件数だけでは「もともと別 node が殺していた」可能性を排除できない。
- **変異道具側で 2 件実測した。** (a) `tools/mutation_worktree.py` は作った使い捨て worktree の
  submodule を初期化せず、baseline が 27 errors の `PARSE_ERROR` になる (DW-C01 は全新規
  worktree の再帰初期化を定めるが wrapper 自身は行わない)。(b) 同 wrapper の `--resume` は
  baseline を再走せず前回の `PARSE_ERROR` を使うので壊れた baseline から回復できない。
  さらに共有木の事後検査が並行 churn で落ちた。container へ `tools/mutation_harness.py` を
  直接当てて解決した。
- **受入 1 走目は 24085 passed・3 error で赤だった。3 件とも非帰属と判定した。**
  2 件は `test_t1259_qsub_env_delivery_probe.py` の setup で
  `git ls-files --others --exclude-standard -z` が 30 秒 timeout、1 件は
  `test_s8c_preregistration_predicates.py::test_repository_candidate_uses_real_s8c_budget_module` の
  setup で `real-repo lock deadline exceeded` (parent write lock を READ 4 本が保持) である。
  いずれも本 wave の差分 (`test_codex_reasoning_ab.py` 1 file、新 node は共有 fixture も
  real-repo lock も使わない) から到達しない。同じ tip で 3 件を単独再走し 8 passed
  (parametrize 展開後) で再現しなかったため、DW-O18 に従い受入を 1 度だけ再走した。
- 設計判断は {{D:m2-golden-synthetic-restore}}。
- **実装子はテストを 1 件も走らせられなかった。** dispatch の `qstat -Q` が socket 作成制限で
  失敗し rc=16。子は `closed` と書かず「実装済み・未実走」と報告し、実測は親が行った。
- 工数: codex 子 6 本 (plan 1 = 7 call、consult 2 = 6 / 6 call、author 1 = 13 call、
  review 2 = 8 / 7 call)。全段 `gpt-6-astra` / `medium`。
  変異走は計算ノード job 12 本 (変更後 6・変更前 6) と、破棄した変更前 baseline 2 本。

## 次の一手差分

### 完了

- [T-2117] 復元不能な当時の bytes 一致の要求を撤去し、二経路 golden の照合を
  合成入力の常時実行 node へ戻した。正例と mismatch 負例の 2 node を常時実行にし、
  変異の新旧両走で検出力の差分を実測した。
  remaining: none
  base: ba3304c49d54809f68b2a3a7991736caba182f87260454b8a4849b5b0eb8056d
