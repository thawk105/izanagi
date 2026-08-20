---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: dev-wave-t1442-c06-reachability
seq: 1
title: _evaluate_c06のreachability検査をC03/C05/C07と同型のidiomへ強化した (コード+テスト、branch worktree-dev-wave-t1442-c06-reachability、変異matrix = baseline PASSED・3/3 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- 一次資料は `docs/worklog.md` entry 754 ([T-1421] C06 machine_checkable 昇格 wave) の起票文と
  D599。D599 は reachability 検査の3弱点 ((a) supervisor 不在時の無条件 skip、(b) 呼び出し名の
  文字列一致だけで import 束縛を検証しない、(c) `_ledger_lock`/`_check_limit_state` の存在のみ
  検査) を「本 wave では修正せず後続 wave へ送る」としており、本 wave がその後続にあたる。
  設計は {{D:c06-reachability-explorer-alignment}}。
- 段1 brief で同ファイル内の姉妹評価器 (`_evaluate_c03`/`_evaluate_c05`/`_evaluate_c07`) を
  比較調査し、3弱点それぞれに対応する既存の強い idiom (`_ReachabilityExplorer`+`_declared_call`、
  producer 不在時の明示 UNSATISFIED、per-function `required_calls` dict、契約 `reachable_from`
  整合検査) を特定した。command 引数は弱点(a)(b)の2点のみ言及していたが、一次資料には(c)も
  含まれていたため F31 に従い本文優先で3点とも scope に含めた。
- 段2 codex plan・段3 敵対相談2レンズ (sol=正しさ境界、luna=整合・scope) が独立に、plan の
  新設テストが誤った reason_code 文字列 (`"budget-consumer-undefined"`、正しくは
  `"budget-consumer-contract-undefined"`) を使っていることを発見した (このまま実装すると
  新設3ケースが無条件に失敗する)。段5実装で修正済み。
- レンズlunaが独立に発見: `_evaluate_c12` (行2313-2327付近) がC06現行と全く同じ
  `_reachable_calls` 名前一致弱点を持つ。両レンズとも「C06のみが本waveのscope、C12は次task
  候補」と結論した。{{T:c12-reachability-name-only-weakness}}として記録する。
- 段6敵対レビュー2本のうちreviewA (実装差分の正確性) はmust-fixゼロ、英語コメント1箇所の
  nitのみ (fixで日本語化)。reviewB (回帰・mutation準備) が2件のreal/must-fixを発見:
  `required_calls`検査の呼び出し欠落と`_c06_reachable_from_verdict`のfail-open化を、
  現テスト集合が独立検出できない。fixで検出テストを2本追加して解消した (対応表:
  reason_codeバグ=closed、共有fixture副作用=refuted、英語コメント=closed、
  required_calls検出力=closed、reachable_from検出力=closed。単一fix unitのため並列統合の
  焦点再レビューは省略、親が直接diff全文とtest実走で検証した)。
- 新設テスト5本すべてを、旧コード (統合commit前のHEAD) に対して個別にA/B実測した
  (`git diff>patch`で本番fileの差分退避→`git checkout --`でHEADへ戻す→対象テスト実行→
  `git apply`で復元、を3回)。いずれも旧コードで`EVIDENCE_UNDEFINED`(誤)、新コードで
  `UNSATISFIED`(正)になることを確認し、旧弱点(a)(b)(c)が実在すること・新設テストが実際に
  検出層として機能することを実測で裏付けた。
- 変異事前登録 (DW-M01) を段4で読み忘れ、段6 fix完了後・mutation_harness.py投入直前に発覚した
  (`docs/dev-wave/mutation.md`を通常の直線フローで見落とした2例目、1例目は[T-1142])。
  遡及登録では、各変異の置換対象一意性・構文正当性をスクリプト検証したうえ、実ファイルへ
  apply/revertして`tools/run_tests.py`で単一理由性を個別に実測してからspec化した (机上予測に
  依らない)。mutation_harness.pyが固定commit HEADを要求すると判明したため、段6の統合commit
  (`cfba6e66`、AI-Agent 5行、`check_ai_provenance.py --message-file`事前検査・commit後
  full-history監査とも新規違反なし) を先に作成し、そのHEADに対して本走した。
  結果: baseline PASSED (192 passed)、M01 (`_c06_reachable_from_verdict`のfail-open化) =
  KILLED (`test_c06_rejects_broken_reachable_from_contract`のみ、期待一致)、M02
  (`required_calls`から`_check_limit_state`を除去) = KILLED
  (`test_c06_rejects_budget_without_limit_check`のみ、期待一致)、M03 (Explorer/declared_call
  部分を旧ad hoc名前一致へ戻す、supervisor不在の明示returnは維持) = KILLED
  (`test_c06_rejects_name_only_supervisor_decoy`のみ、期待一致)。3/3 matches_expectation=true。
  spec は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1442-c06-reachability/mutation-spec.json`
  (sha256 `56153f4f1db549b2755f4013c623458fd480143c23937103f6fc7bfe5e10ada1`)、結果は同
  ディレクトリ `mutation-out.json` (repo_head=`cfba6e66dc5a059f4db8719333370d353143dd47`)。
- 検証中の技術的発見 (decisions・残る限界に格上げしない補足): P1.2 (supervisor/`run_trial`不在の
  明示 return) は、P1.1 (Explorer化) 実装後は実質的に冗長であることが分かった —
  supervisor不在・run_trial不在のいずれも、Explorerが空グラフを返しその後の
  `required_targets`膜membership検査が自然に失敗するため、明示returnを外しても
  (Explorer呼び出し自体は素通りさせても) 同じ結果になる。ただし明示returnは意図を明確にする
  防御的コードとして残す価値があり、変更しなかった。
- 実 repo 現行状態への判定結果は不変であることを確認した (`test_repository_candidate_uses_real_s8c_budget_module`
  が変更後も緑、`s8c_budget.py`の`_check_limit_state`/`_ledger_lock`実呼び出しを
  `:474,556,572,604`で確認済み)。`nc_c06_one_arm_reservation_removed`も引き続きUNSATISFIED。

## 次の一手差分

### 完了

- [T-1442] `_evaluate_c06`のreachability検査をC03/C05/C07と同型のidiomへ強化した。
  remaining: none
  base: 9741130fb5bd108e75abcb7143d0f8c77ac36894af20f443bd7cb52396aa6ec8

### 新規

- {{T:c12-reachability-name-only-weakness}} **P2・新規**: `_evaluate_c12`が使うhelper
  (`s8c_preregistration_evidence.py`行2313-2327付近) がC06現行 (改修前) と同じ
  `_reachable_calls`名前一致弱点 (import束縛を検証しない) を持つ。[T-1442]waveで
  `_evaluate_c06`向けに`_ReachabilityExplorer`+`_declared_call`への置換パターンが確立された
  ため、同型の強化を`_evaluate_c12`へ適用できる。段3 lensB・段6 reviewB (T-1442) が独立に
  発見・確認した。
