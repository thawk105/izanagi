---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-t2810-g1-launch-validation
seq: 1
title: [T-2810] 凍結 v2 g1 の launch validator を official 成果物の現物形へ整合した — journal allowlist に reservation-preflight と binding 2 key を足し、段階 6 lineage を「各 artifact の一意・非 merge 導入 i について C ≤ i ≤ G」+「G 自身が追加した世代文書の導入 == {G}」へ改め、実 repo の historical reverify は段階 8 (未発効候補の scan hit) まで到達、live は policy 照合で拒否のまま (コード + テスト + docs、branch worktree-dev-wave-t2810-g1-launch-validation)
---

## 本文

- ユーザー依頼 (2026-09-20、dev-wave 引数の逐語は insight `verbatim/T-2810-origin.md`) の範囲で 1 wave。一次資料は
  `output/insights/2026-09-20/t2810-g1-launch-validation/README.md` (新事実・裁定・受理集合の変化・実測・変異台帳・scope 外・逐語)、設計判断は
  {{D:g1-launch-validator-current-shape}}。専用 handoff は repo 外 job dir、wave artifact dir は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2810-g1-launch-validation/`。
- 起点 local main `482f19b88` → 編集前に 2 回 ff-only で `800178b39` (main はその後も進み、受入の post-claim merge で揃えた)。開始 gate (fresh、外部 handoff) rc=0。
  同課題の稼働 wave は `git worktree list` + ListAgents で 0 件。DW-O09 pin 閉包 = 変更 4 file の sha256 pin 0 件、B-10 freeze-tree pin は候補 path を含まず不変。
- **brief 前の前提実測で新事実 4 件** (insight §2): N1 = 着手時 main の live P3 (g1) は T-2304 の pin 前進 (policy epoch `db6bc9ea…`、D2184) で
  journal 検査より手前の段階 4 `manifest-invalid` で止まる (一次資料 §5 の `journal-state-invalid` は pin 前進前の観測)。N2 = `campaign-start` も binding 2 key
  で allowlist と不一致。N3 = journal + 段階 6 を一時変異 (DW-O19、復元済み) すると policy 照合なしの正規経路 `reverify_published_freeze` が段階 4〜7 を通過し
  段階 8 の full scan で未発効候補 `output/s8b-freeze-candidates/holdout_freeze.v2.g1.json` の未申告 hit (`closure-hit-mismatch`) で止まる。N4 = 現物は
  cert C = result 導入 = X1' = G^ なので α は「C ≤ i ≤ G」の形が要る。
- 段 2 plan (codex) と段 3 相談 2 本 (sol = 正しさ境界、luna = 裁定整合・scope) は must-fix 0 の実装変更・should 5 (A-1 reservation の件数・順序、A-2 旧 checkout への
  一般化を書かない、B-1 上限は重複検査、B-2 受理集合の一般化を明示、B-3 効能の限定) をすべて採用。δ 案 (`frozen_at_head` 束縛) は不採用 (理由は D)。
- 段 5 author (Codex、20 分): production +99/−10、test +309/−3 (新規 test 17 関数 / 63 ケース + helper 5 関数)、oracle test +7/−5 → 統合 commit `dc5b0f39b`。
  段 6 レビュー 2 本 (A: 正しさ境界・fixture と実物の 1 文字照合、B: 過剰・削除) は **must-fix 0 / GO ×2** (should 1 = RA-1 M12 の集計別枠、nit 5)。
  fix1 (docstring、`0d943f9cb`)。焦点走 1 (統合 commit、10 file、計算ノード 249.8 s) = 974 passed / 13 skipped / **1 failed** (既存
  `test_generation_two_rejected_before_artifact_io`、`generation_number` だけを射影する fixture と世代文書 {G} 検査の衝突、本差分に帰属) → 段 4 追補 1 (世代文書 path を
  G 自身の追加 path から引く) → fix2 (`083a45ee9`)。焦点走 2 (fix2、17 file = 焦点走 1 の 10 + DW-O26 の consumer 7、245.6 s) = **1876 passed / 13 skipped / 0 failed**。
  held 診断走 (`IZANAGI_RUN_GROWTH_HELD_TESTS`、held 6 + tmp repo 2 + 1、80.8 s) = 9 passed。焦点再レビュー 1 本 = GO、regressed 0、新所見 0。
- **実 repo 実測 (統合 commit 後・fix2 後の 2 回、無変異、login node、insight §5):** loader = generation 1 / sha `7e1114…`。`reverify_published_freeze` =
  `closure-hit-mismatch` (rr80 未申告 = 候補 path) — **段階 4〜7 を通過して段階 8 に到達** (成功ではない)。`launch_validate` = `manifest-invalid` (policy)。
  runbook §2 P3 (g1 path) = `allowed: false`、拒否 2 件 exact (更新後 `_ACTIVATED_G1_REFUSALS` と集合一致)、v1 path = 既知 4 件 exact (不変)。
  `assert_g1_floor_selection_identity` = None。
- 変異 matrix (M0 等価 + 負例 14、独立 clone @`083a45ee9`、計算ノード dispatch、runner = 3 test file): probe (全件 SURVIVED 登録、20:33〜23:15) で観測 node を集め
  (M1 53 / M2 26 / M3 3 / M4 12 / M5 2 / M6 24 / M7 2 / M8 2 / M9〜M11 各 1 / M12 2 / M13 1 / M14 59、段 6 レビュー A の帰属表と一致)、final (23:15〜02:55、1 走 268〜944 s
  = 計算ノード混雑) で **baseline PASSED・M0 SURVIVED・14/14 KILLED・期待 node 完全一致 15/15・MISMATCH 0**。M12 (世代文書 {G} 検査の削除) は
  段階 7 が別 cause で拒否するので受理集合の kill でなく「拒否段階 / cause の契約」の別枠、M13 (上限) は helper 単体試験だけが殺す重複検査、M4 の受理集合の証拠は
  `both` 4 node (RA-1)。詳細は insight §6.2。
- 検査: provenance range 監査 (`800178b39..HEAD`、記録 commit 1 の tip) 4 件違反なし、`check_docs` 違反なし、`git diff --check` 緑、`spool_fold.py --dry-run` rc=0、
  三軸走査の hit は既知の official 成果物 4 file × 2 holdout のみ。受入: 記録 commit の tip で待ち手経由の全走 (3 shard) を門番 loop から投入する。結果は本 fragment には
  書かず受領証 (job dir) と land の記録が持つ。child-green でなければ land しない。
- **限界・言わないこと:** 本 wave の効能は「validator の互換性修復」と「新 main の historical reverify が段階 8 に到達」まで。historical は候補 hit で失敗のまま、
  live は policy 拒否のまま、P3 の全 gate 受理 (`allowed: true`) は未達。W-4 / W-5 / certified / 測定値・認証結果は更新しない。旧 pin 固定 checkout への修正の
  移植は未実施・未確認。独立 fixture の成功は launch core の証拠で loader 込みの chain 成功ではない (loader 成功は実 repo で別に実測)。binding は記録内の
  整合情報で PBS job の外部認証ではなく、DAG の記録順は実時間順を保証しない。fixture の journal は key 文法と型契約だけが現物と一致する。
- 事故: 親が author 子の進捗確認で他 worktree へ `cd` を含む Bash を打ち追跡 cwd が移った (F100 再発、`EnterWorktree(path)` で即復帰、実害なし)。
- 工数: codex 子 9 本 (plan 1、consult 2、author 1、fix 2、review 2、focus 1)。計算ノード job: 焦点走 2 + held 診断走 1 + 変異 (probe 16 走 + final 16 走、独立 clone) + 受入。wave 全体 18:58〜 (受入・land は別記)。

## 次の一手差分

### 完了

- [T-2810] launch validator の journal allowlist と段階 6 lineage を official 成果物の現物形へ整合し、runbook §2 P3 を g1 / v1 path で再実測、`_ACTIVATED_G1_REFUSALS` を pin 前進後の live 真値へ更新した。journal 修正後に別の不整合 2 件 (live の policy 照合 = T-2812 系、historical の未発効候補 scan hit) が残ることを記録して止めた。
  remaining: none
  base: 8a435faac3d9c6de268112a84e109b35badb93fff25a99037a62fd143829b8ac

### 新規

- {{T:g1-candidate-doc-scan-hit}} **P1・裁定済み (第 27 回 /rulings、2026-09-21 00:5x JST「推奨通り」、一次控え `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-09-21-rulings-full27-verdicts.md` 項 5、台帳の D は記録 wave `rulings-all-20260921` の fold 後) → 削除 commit の実装手番 (AI、本 wave の land 後に別 commit)**: 凍結 v2 g1 の historical launch validation (`reverify_published_freeze`) は段階 8 の full scan で未発効候補 `output/s8b-freeze-candidates/holdout_freeze.v2.g1.json` (X2 で main に載った、世代文書と同 bytes) が rr80 の未申告 hit になり `closure-hit-mismatch` で止まる (exact exemption は V1・世代文書・approval・pointer の 4 path だけで、候補 path は走査除外ではない、insight §8)。裁定 = (a) 候補 file だけを削除する commit (scan 除外は不変、B-10 freeze-tree pin の対象外、G/A/X・floor_source bytes 不変、削除後に load / reverify を再実測。根拠 = 候補 path の役割が批准済み世代 (D2180) へ移って終了、D2077 を削除許可としては引かない)。帰結の記録: `V2_CANDIDATE_REL` の create-only 存在拒否が消え再生成で hit が復活しうる、held 真値 (`_ACTIVATED_G1_REFUSALS`) の候補を含む hit 列挙が変わるので再実測、候補 bytes と来歴は X2 の履歴 blob と世代文書で保持。
