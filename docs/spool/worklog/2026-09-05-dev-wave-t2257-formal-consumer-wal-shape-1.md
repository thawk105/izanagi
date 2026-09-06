---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-05
wave: dev-wave-t2257-formal-consumer-wal-shape
seq: 1
title: [T-2257] 8c formal consumer の `_wal_trigger()` を production の `stage` + `payload` 形状へ直し、旧形状は FC05C で拒否する (コード + テスト、branch worktree-dev-wave-t2257-formal-consumer-wal-shape、実装面の差分 6 file、変異 14/15 KILLED + 等価 1 SURVIVED)
---

## 本文

- ユーザー依頼は「`reflux_formal_consumer.py` の `_wal_trigger()` (root の `kind`/`trigger_binding` を要求) が production producer の書く
  `stage` + `payload` 形状の WAL record を読めない食い違いを consumer 側で直す。`wal.py` は触らない (t1851-unit-a の未着地差分を
  確認し、producer 側の変更が要れば止める)。正例は production producer が実際に書いた record の逐語、負例は旧形状。Codex author
  (D95)。規律 2 を緩めない。provisioning の裁定や P6 本体には触れない」。
- **結果:** consumer 側だけで閉じた。`wal.py` / `trigger_gate_binding.py` / `reflux_result_evidence.py` は 1 byte も変えていない
  (t1851-unit-a の `wal.py` は main と差分ゼロ、producer 変更は不要と確認)。設計判断は {{D:formal-consumer-production-wal-trigger-shape}}、
  一次資料は `output/insights/2026-09-05_t2257-formal-consumer-wal-shape/README.md`。
- **brief 前の実測:** output/campaigns の trigger campaign 7 本の `wal.jsonl` に `trigger_binding` record は 0 件で、保存済みの
  production record は無い。正例は producer 関数 `wal.log_trigger_binding()` を実走して得た (record は insight の verbatim へ逐語保存、
  同じ bytes を test の literal に持つ)。ledger 側 `trigger_binding` の production producer は未実装で、値は契約由来 (DW-O13 の限界)。
- **段 3 相談 2 本の real 所見で裁定を補強:** payload の key 集合を閉じる、outer envelope の key 集合を閉じる (root と payload の
  attempt 併存 = root shadow を拒否)、source 付き正例 (mask 18) と source だけ違う負例、FC06 test の追随、`_rewrite_wal` の root 注入
  禁止、焦点走は `run_tests.py` 経由 (`test_reflux_*` は pytest-only allowlist)、fixture builder test の exact key 検査。
- **段 5 (Codex author 1 単位) → 焦点走 1 回目 679 緑 / 4 赤:** 赤は `test_reflux_result_evidence.py` の golden 4 定数
  (fixture の result record bytes を値で pin)。plan・2 レンズ・親の pin 閉包がそろって落とした値 pin (F39 再発)。fix1 で独立再計算に
  より更新。**親の erratum:** fix1 で P-3 の literal を brief の `ts` へ書き換えさせたが、refs の逐語は別の走の `ts` で、段 5 の子が
  正しかった。fix2 で refs の bytes へ戻した (F1 の near-miss 追記)。
- **焦点走 2 回目 683 緑 → 段 6 レビュー 2 本:** A は NO-GO (canonical-list 経路は `wal.parse_line()` を通らず outer 値の型が未検査)、
  B は GO。fix3 で `variant`/`env_tag`/`ts` の型契約を consumer 内に敷き、負例 3 本 (N-11〜N-13) を追加。焦点再レビュー GO。
  焦点走 3 は同 worktree の provenance 監査 job と並行投入して rc=16 (非帰属)、3b は queue-wait-timeout の rc=16、
  D612 上書きを付けた 3c で 686 緑。
- **変異 (probe → 本走、dispatch):** probe 1 回目は runner script に D612 上書きを書き忘れ、baseline 段が既定 900 秒の queue 待ちで
  rc=16 になり変異が 1 件も走らなかった (非帰属 infra、丸 2 日の遅延)。上書きを足した probe 2 回目で観測 node を集め、本走は
  15/15 一致 (14 KILLED、等価 M12 のみ SURVIVED、MISMATCH 0、baseline 緑)。冗長 gate は出なかった。
- **受入全走** は本記録 commit の後に投入し、結果は受入 receipt と land 報告に残す (記録 commit を tested tip の内側へ置くため)。
- **据え置き:** consumer の terminal record 検査 (`_validate_wal_outcomes` の `terminal.get("kind")`) は同族の食い違いで、production の
  terminal は `stage` が `commit` / `abort` (`model.py`)。修理後も本番 projection は FC05C を通った後 FC07 で止まる。
  {{T:formal-consumer-terminal-stage-shape}} として起票。
- 新規テスト 18 本は `acceptance_duration_ledger.json` へ未登録。台帳の読み込みは fail-soft で受入は止まらないが、焦点走の dispatch は
  JUnit XML を残さないため、この wave では登録できない。
- 段 8 の改善候補: (a) pin 閉包は baseline / golden の hash 値そのものを `git grep` する、(b) 実装子に渡す逐語は artifact そのものと
  照合し brief の引用を根拠にしない、(c) 同一 worktree からの dispatch は provenance 監査も含めて直列にする、(d) 変異 harness の
  runner script にも D612 上書きの export を定型として入れる。いずれも memory へ。
- 工数: codex 子 9 本 (plan 1、lens 2、author 1、review 2、fix 3、焦点再レビュー 1 のうち fix3 と再レビューを含む)、いずれも rc=0。
  計算ノード: 焦点走 4 (うち 2 が rc=16 の非帰属)、provenance 監査 2、変異 dispatch 2 走 (32 job)、受入全走は記録 commit 後。

## 次の一手差分

### 完了

- [T-2257] `_wal_trigger()` を production 形状へ直し、旧形状・非 exact 形状は FC05C で拒否する。terminal 側は別 carry。
  remaining: none
  base: 13583a3224d7dfa52a8a8842336b0792c706580e140ccbace8be073360fba064

### 新規

- {{T:formal-consumer-terminal-stage-shape}} **P2・新規**: 8c formal consumer の `_validate_wal_outcomes()`
  (`reflux_formal_consumer.py` の `terminal.get("kind")`) が root `kind` を要求するが、production の terminal record は
  `stage` が `commit` / `abort` (`orchestrator/campaign/model.py`) で outer に `kind` を持たない。T-2257 で trigger 側を直した後も
  本番 projection は FC07 で止まる。consumer 側で `stage` を読む形へ直し、fixture の terminal record も production 形状へ揃える。
  読み手の修理だけ。実装は Codex author (D95)。
