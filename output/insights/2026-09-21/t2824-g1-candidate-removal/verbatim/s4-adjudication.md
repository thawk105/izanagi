# 段 4 裁定 — [T-2824] (2026-09-21 08:50 JST、base 5efd69367)

段 2・3 は省略 (設計択一なし: D2194 項 5 が択 (a) と不変条件を確定済み、実装面は test 定数 1 個の追随だけ)。所見は段 1 の自己実測のみ。
段 4 直前の裁定 inbox 再走査: rulings-inbox の 2026-09-21 控え (第 27 回) 以後に本対象へ触れる控えなし (段 4 直前に ls で確認)。

## 裁定

- (P1) provisional のまま維持: 削除後の historical reverify の到達点は実測で決める。成功しても「記録 contract での historical 再検証が通った」までで、
  certified 昇格・live admission の代替・W-4/W-5 開始許可とは書かない。別段階で拒否されたら、その段階・reason を記録して止める (本 wave で直さない)。
- (P2) provisional のまま維持: held 真値は削除後の live P3 (g1 path) の実測 refusals と集合 exact 一致の値にする。prefix / any / 部分一致へ落とさない。
  変化が候補 path の除去以外に及んだら (例: live policy 拒否文の変化) 、その差を段 4 追補で再裁定する。
- N1 (v1 path の中身も変わる): runbook §1.1 の判定規則 (件数・種別) は不変で本文を直さない。W-3 の状態文「候補の hit 4 / 4」「(ii) 候補 hit で止まる」だけを実測値で更新する。
- held node の実行: 本依頼 (held 真値を現在値へ更新) を 6 node の診断走・変異走に限ったユーザー明示指示と扱い、`IZANAGI_RUN_GROWTH_HELD_TESTS=explicit-user-command` を
  その走だけに立てる (T-2810 と同じ運用)。hold 台帳・growth_test_holds は変えない。
- fixture 補助 3 箇所・`V2_CANDIDATE_REL`・create-only 拒否・scan 除外・`_active_chain_exempt_exact`・B-10 pin には触れない (brief の不変条件)。

## plan v2

1. 親: 削除 commit (diff = `output/s8b-freeze-candidates/holdout_freeze.v2.g1.json` の D 1 件だけ、`AI-Agent: product=claude; ...; role=author; scope=record`)。
2. 親: 削除後の 5 経路 (loader / reverify / launch_validate / P3 g1 / P3 v1) を login で再実測 → evidence/after-*.json。
3. Codex author 1 本: `orchestrator/tests/test_s8b_oracle_driver.py` の `_ACTIVATED_G1_REFUSALS` を親が渡す実測 refusals と exact 一致させ、直上 comment の
   「historical reverify は段階 8 の未発効候補 hit まで到達する」を実測の到達点へ直す。他 file・他行は触らない。
4. 焦点走 (計算ノード dispatch): held 6 node (held env あり) + 候補 path を参照する fixture test 群 (floor_campaign の replay / clean-scan、oracle_driver の visible output、
   holdout_freeze の create-only 群) + driftguards。
5. 段 6: 独立 read-only 敵対レビュー 2 本 (A = 弱体化・規律 2、B = 記録の限定・帰結)。変異 matrix (下記)。受入 (dev_wave_wait acceptance)。
6. 段 7: insight (新規 `output/insights/2026-09-21/t2824-g1-candidate-removal/`)、runbook W-3 状態文、phase3 checkpoint、worklog / failures? (なし) fragment。

## 変異の事前登録 (DW-M01、実装前)

対象 commit = Codex 統合後の tip (fix があれば fix 最終 commit で再検証、DW-M07)。runner = `tools/run_tests.py --force-dispatch`、対象 = held 6 node (env あり)。

| id | 位置 | 置換 | 期待 | 数え方 |
|---|---|---|---|---|
| M0 | `_ACTIVATED_G1_REFUSALS` 直上 comment 1 行 | 等価な文言変更 | SURVIVED | harness の SURVIVED 検出の正例 |
| M1 | `_ACTIVATED_G1_REFUSALS` の第 1 要素 | 削除前の値 (rr80 / rr20 とも hit 4 件 = 候補 path を含む) へ戻す | KILLED、期待 node = held 6 node の完全集合 (probe で確定) | **diagnostic sensitivity pin (DW-M08 別枠)**。held 真値は production の受理集合を変えない構造化シグナルの exact pin なので、受理集合の kill には数えない。示すのは「更新後の真値が削除後の実 repo と実際に照合されている (恒真でない)」ことだけ |

単一理由性: M1 で held node が赤になる理由は refusals 集合の exact 不一致だけ (他 assertion は変異の前後で不変)。production の変異は登録しない
(実装面の差分が test 定数だけで、production の受理集合を変える変更が無い — 受理集合の kill を主張しない)。
