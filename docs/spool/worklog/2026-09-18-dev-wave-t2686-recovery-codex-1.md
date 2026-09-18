---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-18
wave: dev-wave-t2686-recovery-codex
seq: 1
title: [T-2686] exact-state union walk実装を回収し、観測対象の混同を修正して同一判定の対測定を完了した（コード＋docs、branch dev-wave-t2686-recovery-codex）
---

## 本文

- ユーザー指定の元tip6ac18eb40を、着手main b2037abfa基点の専用Codex worktreeへ回収。
  既存赤3件はwalk観測がdiff --name-onlyを混入させたため。隔離authorが7 selectorを修正し、
  productionと既存assertは維持。判定条件・期限・limit+1正例を維持する採用判断は{{D:exact-state-union-walk}}。
- 独立レビュー2本＋driver修正後の焦点レビュー2本。初回authorは総括見出し欠落で未受理となり、
  実装残差を保存して実コードを独立監査した（F43）。観測対象と状態語の取り違えはF992へ再発追記。
- 計算node bnode050の旧/新/旧/新で、固定target559bcbc29…・同main56be58448、
  timing除外payloadがbyte一致、Git子process数は両対244→161。所要は40.001→25.789秒と
  38.196→26.065秒。変化するload/未証明の専有性があるため一般高速化率や実装単独の因果効果とはしない。
  判定は全走indeterminate/one-or-more-states-unproven。8秒以内の達成は主張しない。
- driverは正常な非決定的patch-id merge省略と実timeoutを区別した。全raw/canonical fieldを保ち、
  実raw4正例/16負例を親が確認、修正後に別4走を取得。初回driver rc1は遡及して成功にしない。
- 焦点4fileは373 passed/52.10秒。正式変異はbaseline green、raw status16 KILLED/等価1 SURVIVED、
  失敗node完全集合一致、MISMATCH0。候補順・本数・方式等の契約感度を正しさのkillへ合算しない。
  m04は非lexicalを保証した既存nodeへ分離。共有木snapshot不一致の初回wrapper125を保持し、
  同一anchorの独立cloneでwrapper0/復元/teardownまで再確認した。
- 全史provenanceは新規違反なし、既知56を別記。初回HEAD変化による監査赤、QUEでの正規取消し、
  probeのMISMATCHも保全。raw・逐語・source hash・分類は
  output/insights/2026-09-18/t2686-exact-state-union-walk/ にある。
- 初回全受入は25185 passed/69 skipped。その間にlandしたT-2691を取り込み、checker/rescue両fileの
  焦点244 passed/7.33秒を確認。旧s4の条件どおり、記録後の統合tipへ最終全受入を再投入する。
- dev-wave改善候補1件を専用handoffへ記録した。共有木snapshot検査と独立clone再走の保証範囲を
  既存DW-O19/DW-M05で明確にする記述候補で、採用・改善実装・次wave・新gate/台帳機構は追加しない。
  最終受入・landの結果は固定tipに束縛した受領証へ保存する。pushは行わない。

## 次の一手差分

### 完了

- [T-2686] exact-state候補供給のunion化を回収し、同一判定・process減の対測定と変異検証を完了した。
  remaining: none
  base: 569cbef7b0cbee675a7bc2ed4954878c163e221e5d43f1cc3f022dea4aafb8fd
