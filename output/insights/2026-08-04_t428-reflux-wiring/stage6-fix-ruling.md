# [T-428] 段 6 fix 裁定 — レビュー 2 本 (rev1 = 正しさ境界 6 所見、rev2 = 閉包・回帰 7 所見) の裁定と fix 分割

日付: 2026-08-04。全 13 所見 real、refuted 0。snapshot = HEAD 8bfcf0d +
s6-snapshot-uncommitted.patch (job dir 退避)。fix は所有素集合の 3 単位並列 (DW-S06-B、
段 5 契約全文継承)。

## 裁定と割当

| 所見 | 裁定・fix 方針 | 単位 |
|---|---|---|
| r1-1 (predicate↔binding の分離) | real・採用。source-bound binding 確定時に materialize 済み SOURCE_REL の hole 行を読み、`emit_predicate(TriggerGateIR(binding.mask))` と byte-exact 照合する (P module 仕様にあった producer 検査の実装漏れ)。交差負例 (predicate A × binding B) を pipeline / sink 双方へ | F1 |
| r1-2 (proposal→機械 sweep 偽装 downgrade) | real・採用。(i) admission は campaign ID を lock canonical preimage から再計算し basename と照合、(ii) 機械 sweep 免除は「全 build receipt が非 coder-authored」を必須条件に加える (coder-authored receipt が 1 つでもあれば proposal 級)。変換直接負例を追加 | F1 |
| r1-3 (auditor 自由形式 evidence の raw 反射) | real・採用。auditor の violations/nits を閉じた code 列挙 + 固定 field へ制限し、任意文字列を WAL payload / critic へ流さない。raw 値入り reject の負例 | F2 |
| r1-4 (binding→start 間の crash 窓) | real・採用。replay/validator は「末尾 orphan binding (対応 start なし・以後に record なし)」を許容し、startup が証拠付き recovery-abort tombstone へ収束させる。fault injection 境界テスト | F1 |
| r1-5 (planner axis 未検査、M-C3 過大表示) | real・採用。loader/sink で planner.axis == coder.axis == MARKER_ID + enum 検査。テスト名と実保証を一致させ M-C3 を再照準 | F2 |
| r1-6 = r2-2 (dry-pass / fixture main が admission 必須 digest と衝突) | real・採用。dry-pass / no-build は admitted-campaign consumer (critic digest) を呼ばない専用経路に分離。fixture main は provenance funnel へ統合。mock なしの fresh-layout CLI テスト | F2 |
| r2-1 (test_autonomous_trial_completeness 取り残し) | real・採用。同ファイルを consumer 閉包に追加し fixture (旧新 ID・binding・commitment・provenance) を更新 | F3 |
| r2-3 (epoch テスト自己矛盾・8c 被覆不足) | real・採用。direct 旧 ID 集合の是正 + 8c A/B/C 全 workload の旧新 ID と旧 root 非書込の表形式固定 | F1 (test_campaign) / F3 (trial 側) |
| r2-4 (provenance 集合比較が attempt 多重度を消す) | real・採用。provenance entry に build_attempt_id を持たせ per-attempt 対応を検査。M-B9 を attempt 欠落変異へ再登録 | F1 |
| r2-5 (commitment 式が裁定逐語と不一致) | real・採用 (実装側を正とする)。裁定 §1 A5/B10 の式 `sha256(canonical(binding) ∥ nonce)` は「nonce を canonical JSON の field として含めた canonical bytes の sha256」へ**erratum** (本ファイルが erratum の記録。意味は同等 = nonce が preimage に入り辞書攻撃を封じる)。独立 literal golden vector テストを追加し自己参照を断つ | F3 (+ 親: 本 erratum) |
| r2-6 (直前性の過大主張) | real・採用。validator を `binding_index == start_index - 1` (orphan 許容と両立) へ強化し、interposition 変異を追加 | F1 |
| r2-7 (四面 parity が形だけ) | real・採用 (テスト先行)。bit 順・極性・kUnset の semantic literal を 4 面から抽出して一致を pin するテスト。manifest 本文の変更が必要になった場合のみ pin 再 render + 親レビューの追加 cycle を報告 | F3 |
| r2 付随 (M-B9 / P+1 弱い、record_diff_reject legacy payload テスト不在) | real・採用。P+1 を public drive_iteration 経由の end-to-end へ拡張、legacy payload key 固定テスト追加 | F2/F3 |

## fix 単位の所有 (素集合)

- **F1 (binding 連鎖・WAL・admission)**: pipeline.py、wal.py、artifact_admission.py、
  test_campaign.py、test_artifact_admission.py
- **F2 (driver・dry-pass・開示)**: p3_s4_loop_trigger_gating.py、auditor_gate.py、
  p3_s4_loop.py、p3_autonomous_workload_trial.py、test_p3_s4_loop_trigger_gating.py、
  test_p3_autonomous_workload_trial.py、test_p3_s4_loop.py
- **F3 (consumer テスト閉包・golden)**: test_autonomous_trial_completeness.py、
  test_codex_agents.py、test_trigger_gate_binding.py、test_layer3_report.py
- 親: 本 erratum、s4-ruling への erratum 注記はしない (裁定原文は凍結、本ファイルが正)

## fix 後の義務

fix 統合後: 焦点再レビュー 1 本 (closed/partial/regressed 表、DW-O16 上限 3 巡)、
変異 spec の anchor 再検証 (DW-M07) → 変異 matrix 本走 (M-B9/M-C3/P+1 は再登録形)、
受入全走 + provenance 監査 (queue 回復後)。

## 2 巡目裁定 (焦点再レビュー closed 8 / partial 3 / regressed 2 を受けて)

- r1-2a (偽装の再構成可能性): **主張縮小で closed**。receipt は認証でなく内部整合
  (build_admission 既定義)。artifact 全面再構成の敵対者への暗号学的防御は本 wave の主張外
  とし、新 D fragment の非主張境界へ admission 分類を追記 (親)。増分防壁 (coder receipt
  条件) は維持
- r1-2b (全 post-policy への ID gate = 過剰拒否・I5 違反): **G1**。gate を trigger
  proposal 駆動 campaign だけへ縮退し、壊れた正例 (layer3/t126/completeness/sort/backoff
  critic roundtrip/M-B9 producer) を回復
- r2-1 (completeness fixture の非 canonical lock): **G1**。canonical writer で書き直す
- r2-3 (direct 旧 ID 誤り・8c 表到達不能): **G1**。pre-T428 config から実 ID を再計算して固定
- r1-1 (byte-exact/sink 照合): **G2**。strip 契約 (indent 合法・内容 byte-exact) を正と確定。
  sink (_quarantine_and_audit) に predicate == emit_predicate(IR(binding.mask)) の相互照合を
  追加し、空白変異負例 (行内二重空白・末尾ごみ) を追加
- r1-3 (未知 key 名の例外反射): **G2**。_strict_keys の例外を固定文言化 (key 名を含めない)。
  manifest の auditor 出力 schema を consumer と同じ閉形へ (producer/consumer 契約一致)。
  adapter 再 render + pin は親
- 3 巡目は最終 (DW-O16)。残余が出たら親が変異裏取りで real/refuted を裁定して閉じる

## 3 巡目 (最終) 裁定 — focal round-3 (closed 9 / partial 1 / regressed 3) と H1 (実走赤 13 件) の閉鎖

focal round-3 は H1 統合前の HEAD (a3359df) を対象に走ったため、residual の大半は H1 が被覆:
- r1-6/r2-2 regressed (no-build reject が admitted digest を呼ぶ、共有 driver 漏出含む) →
  H1 items 4/6 + p3_s4_loop.py:842 の修正で closed (battery 再実走で実証する)
- r1-2 regressed (layer3 正例 fixture 未回復) → H1 item 7 (canonical identity fixture) で closed
- r1-3 residual (c) (coder event の asdict が raw wire を report へ) → H1 item 13
  (閉じた射影へ変更、raw は replay 用 artifact のみ) で closed

H1 未被覆の 2 点の親裁定 (DW-O16 の 3 巡上限に達したため、これ以上の fix round は開かない):
- r1-3 residual (a) duplicate-key parser の raw key 名反射 (s8b_prediction_runner.py:224):
  real だが **scope 外** — 同ファイルへの wave 差分ゼロ (git log 実測)。既存の開示パターンで
  あり、本 wave の閉鎖対象 (trigger 経路の新設開示) ではない。**起票 (W8)**
- r1-3 residual (b) manifest の nits.items が required/one-of を欠き consumer の
  exact-one-key より緩い: real だが **nit/backlog (W9)** — 不一致は拒否側 (fail-closed) に
  倒れ、certified 値・受理集合・proof 参照を変える経路が無い (DW-G05 の成果物影響 1 行を
  書けないため must-fix にしない)。producer schema の閉形化は pin cycle を伴う小変更として
  次回へ

H1 の 13 件の帰属内訳: 実装欠陥 3 (no-build digest ×2、raw wire 射影 1)、wave 由来テスト
欠陥 10 (旧 schema fixture・path 縫い目・binding 転送・commitment 欠落)。
以後の検証は実測 (battery 再実走・変異 matrix・受入全走) で行う。
