---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: worktree-t-397-sort-witness
seq: 1
title: '[T-397]/[T-410] sort 軸 permutation_violations へ framing_violation_details 同型の構造化 integrity witness を実装した (コード+テスト、branch worktree-T-397-sort-witness、変異matrix = baseline 409 passed・9/9 KILLED、受入待ち)'
---

## 本文

- [T-397] (「sort 軸の構造化 integrity witness を新設する」) と [T-410] (同一内容、
  `/rulings` 経由で別途 allocate) が同一 work item の二重登録と判明した。origin は
  `docs/archive/worklog-phase3-0804-148.md`(148) と `-152-153.md`(153)。本 wave で両方消化する。
- {{D:sort-witness-p1-narrowed}} のとおり D146 決定10 (byte-binding blocker のため実装しない) を
  再検証し、land を妨げる意味では解消済みと確定した。
- `TxnFramingViolation`/`framing_violation_details` と同型の `SortPermutationClass`/
  `SortPermutationViolation` を `orchestrator/verifier/parse.py` に新設し、
  `model.py`/`core.py`/`report.py` へ配線、`orchestrator/critic/digest.py` の LLM 可視面、
  `orchestrator/campaign/s5_permutation_coverage.py` の positive-control consumer まで
  一気通貫で結線した。段2 codex plan・段3 敵対相談2レンズ (正しさ境界/整合実効性)・段6 敵対
  レビュー2レンズ・fix はすべて Codex (gpt-5.6-luna, reasoning=max)。段6 レビュー real 所見2件
  (`_oracle_cross_check` の将来語彙耐性、critic denylist の `framing_violation_details` 漏れ =
  framing 軸の既存潜在バグを隣接 fix で解消) を fix 済み。
- 変異matrix (B-057、9件) は baseline 409 passed で、初回 probe で M2
  (`orchestrator/verifier/parse.py` の rcdptr-set-changed 分岐、`rcdptr_multiset_preserved`
  反転) が SURVIVED — `test_verifier.py` の実経路テストが `sample[2]` の `observation` 本体を
  検査していなかったテスト漏れと判明した ({{F:mutation-parse-observation-gap}})。1 行の assert
  追加で fix し、再走で 9/9 KILLED を確認した。
- 変異harness (`mutation_worktree.py`) が対象 file を一時書換えるため、
  `orchestrator/campaign/campaign_lock.py` の `CONTRACT_LOADER_RELATIVE_PATHS` に該当する変異
  (parse.py/report.py) を `test_critic.py` と同一 runner で走らせると
  `ratified_enforcement_source` autouse fixture が一律 contract-loader-drift 赤になり
  node 抽出が汚染されることを発見した ({{F:mutation-contract-loader-contamination}})。
  runner の test file 集合を bound-file 有無で2群に分けて解決した。
- commit は2本: 実装統合 (`3c993259`) とテスト漏れ fix (`e946168c`)。
  `check_ai_provenance.py --force-dispatch` (相対 path 起動必須、worktree 絶対 path は guard 拒否)
  はいずれも新規違反なし。

## 次の一手差分

### 完了

- [T-397] 二重登録と判明した [T-410] とあわせ、sort 軸の構造化 integrity witness を実装・変異
  matrix裏取りまで完了した。
  remaining: none
  base: 23eca0dfb0338270c915f9fc23a8c023790c58e7ccb319e3e79dc2fdafdeb1c5
- [T-410] [T-397] と同一 work item (二重登録)。同一 commit で消化した。
  remaining: none
  base: 20d3d15f357bc503f7ada20d5276ce69f4419aacb4d3cb327421ef53a215040a
