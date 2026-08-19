---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-19
wave: workload-policy-hint-impl
seq: 3
title: workload descriptor に人間の自由記述方針ヒントを追加し planner-v4 へ実配線した (コード + docs、branch worktree-workload-policy-hint-impl、変異 matrix = baseline PASSED・3/3 KILLED・SURVIVED 0・MISMATCH 0 (probe 1件 別記))
---

## 本文

- roadmap.md §1 協議改訂 (継承 branch、seq1/seq2 の fragment) の上に実装した。継承 fragment 2 件は
  本 wave へ re-home し (`wave:` を `workload-policy-hint-impl` へ書き換え、ファイル名も追随)、
  1 wave として fold されるようにした。設計判断は {{D:workload-policy-hint}} (継承 fragment)。
- **段2 codex plan の訂正**: 当初 brief は planner-v4 の実起動元を `p3_s4_loop.py` と想定したが、
  段2 codex plan が「実際の active caller は `p3_autonomous_workload_trial.py` (8c) であり
  `p3_s4_loop.py` は proposal を引数で受けるだけ」と指摘した。自分で裏取りし、8c 側の sealed
  arm/exact-key 機構に触れる設計 (B2) は規律5 に反すると判断し、`p3_s4_loop.py` に**実際に
  main() から呼ばれる** planner-v4 入力 JSON 射影の CLI 経路 (「B1-emit」、`--emit-planner-context`)
  を新設する方針へ確定した (段4 裁定)。
- **段5 実装で判明した pin 閉包の広がり**: `s8b_descriptor_schema.json` の bytes 変更が
  `schema_sha256` を変え、`autonomous_trial_completeness.py` の定数だけでなく
  `test_layer3_report.py`・`test_reflux_originless_compatibility.py` (巨大 baseline blob、
  hash-of-hash を含む派生 pin) にも波及した。grep によるリテラル一致検索では派生 hash
  (`role_file_sha256` 等、値そのものでなく計算結果を埋め込む pin) を見落とすことを実測で確認した
  (段8 改善候補へ記録)。
- **段6 敵対レビュー2レンズ**が独立に「hint 付き planner 入力が実 CLI から到達できない
  (既存テストは `default_cfg` の monkeypatch でしか実証していなかった)」を検出。fix で
  `--policy-hint` CLI 引数を追加し、`default_cfg` を monkeypatch しない実 CLI テストを追加した。
  焦点再レビューで全 real 所見 (7件) の closed を確認、regressed なし。
- **`.codex/role-adapters/planner-v4.json` の扱い**: `.claude/agents/planner-v4.md` の本文編集は
  `orchestrator/codex_roles/spec.py` の `render_adapter()` が本文を byte-exact に埋め込むため
  adapter 再生成が必須と判明。`.codex/` は codex sandbox で読取専用のため、既存 waiver 理由
  `codex-sandbox-readonly-dotcodex` (D105 決定1、2026-08-18 に別 wave で同一制約への裁定済み、
  恒久の正規経路) を再利用し、親が `expected_adapters()` の実出力をそのまま書き込んで代行した。
  同一 commit に含めた `review_ledger.py` の pin 更新 (Codex でも編集可能だったはずの1行) について
  provenance 上の疑問を自ら提起したが、段6 レンズB が `check_ai_provenance.py`/D105 を読み
  「waiver は commit 単位」と確認し refuted (是正不要)。
- 変異 matrix (`tools/mutation_harness.py --runner-mode dispatch --detached`)。baseline PASSED
  (1003 items)。M1 (型検査)・M3 (absent 早期return)・M4 (report field) の3件を正式登録し
  KILLED 完全一致。M2 (membership 判定) は `project_from_search_config` が9 test file から
  参照されるため完全 node set の手動確定が非現実的と判断し (DW-M01)、SURVIVED 期待の probe として
  走らせた — 結果は約140 node 規模の MISMATCH (cascade failure)。これは当該行が広く実効gate
  として機能していることの実測確認であり、正式な KILLED 登録はせず probe 所見として記録する。
- **{{T:workload-policy-hint-impl}} の完了記録は本 fold では出せない**: `spool_fold.py` の
  `TASK_HEAD_RE` は `完了`/`更新`/`carry` の対象 ID として `[T-NNN]` (既存の実番号) だけを受理し、
  同一 fold 内で新規登録した T の placeholder 記法を対象にできない (`check_docs.py` が
  「対象 ID が不正」で拒否することを実測確認)。本 wave の実装は完了しており (上記本文のとおり
  workload descriptor + planner-v4 配線 + layer3 記録のすべてを実装・レビュー・変異検証済み)、
  本 fragment の「### 新規」登録 (継承 fragment seq1) はそのまま残して fold に実番号を採らせ、
  実番号が判明した後 (本 wave の land 後) に別途の軽量 docs-only follow-up wave で「### 完了」
  (`[T-実番号]`) を出す必要がある ([T-699] の carry 完了と同型のパターン)。次セッションへの
  申し送り事項として worklog 本文に明記する。

## 次の一手差分
