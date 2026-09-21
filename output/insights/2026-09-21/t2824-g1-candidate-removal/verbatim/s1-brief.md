# 段 1 brief — [T-2824] 未発効候補 holdout_freeze.v2.g1.json の削除 commit (2026-09-21 08:40 JST、base 5efd69367)

- 研究前進: 凍結 v2 g1 床値 chain の historical reverify (reverify_published_freeze) を段階 8 の未申告 hit (候補 path) から先へ進め、runbook W-3 の残手番 (ii) を閉じる。主経路 (CC 自動合成) からは遠い (D2194 項 5 自身の評価)。完了判定 = 候補 1 file だけの削除 commit + 5 経路の再実測 + held 真値 `_ACTIVATED_G1_REFUSALS` の現在値化 + 帰結の insight 記録。
- 確定裁定: D2194 項 5 = 択 (a)。根拠は「候補 path の役割が批准済み世代 (D2180) へ移って終了」。D2077 を削除許可として引かない。控え rulings-inbox 2026-09-21 項 5、一次資料 t2810 insight §5・§8 (2)。T-2810 は land 済み (main に 131bbc9e2 ほか)。
- scope: (1) 削除 commit (diff = 候補 1 file の D だけ、親、output/ の記録変更で Codex author 不要)、(2) held 真値の追随 (test 1 file の frozenset 定数と直上 comment、Codex author)、(3) insight + runbook W-3 の状態文 + phase3 checkpoint + worklog fragment (親、docs)。
- 不変条件: scan 除外・`_active_chain_exempt_exact`・`V2_CANDIDATE_REL` 定数・create-only 拒否 (`_write_v2_candidate_create_only`) のコード不変。G/A/X・floor_source の bytes 不変。B-10 freeze-tree pin (`output/s1-freeze` + `output/s8b-freeze` の固定名 rglob、`92099c87…`) の対象外で定数不変。live の policy 拒否 ([T-2812] 系) には触らない。規律 2 を緩めない (held 真値は実測値へ置き換えるだけで、prefix / any へ落とさない)。gate・台帳は足さない。
- 削除前の実測 (本 wave、login、evidence/): loader OK (世代 1、sha 7e1114…、G 32ba8cae4)、reverify = closure-hit-mismatch (rr80 未申告 = 候補 path、94.2 s)、live = manifest-invalid / binary-admission (0.23 s)、P3 g1 = rc=2 拒否 2 件 (T-2810 fix2 と集合 exact 一致)、P3 v1 = rc=2 既知 4 件 (T-2810 after-v1 と集合 exact 一致)。
- 新事実 N1: v1 path の既知 4 件のうち走査拒否 2 件も hit 列挙 (rr80 / rr20 各 4 件) に候補 path を含む。削除後は件数 4 のまま中身 (hit 3 件) が変わる見込み。runbook §1.1 は内訳を持たない (正本 = worklog・一次資料) ので本文の判定規則は不変、W-3 の「候補の hit 4 / 4」は状態文として更新。
- (P1) 親の provisional 裁定・攻撃対象: 削除後 historical reverify が段階 8 を越えた先 (成功 / 別段階で拒否) は未知。どちらでも実測値をそのまま記録し、成功しても certified 昇格や live admission の代替と書かない (規律 7、runbook §2 P3)。
- (P2) 同: held 真値の変化は hit 列挙から候補 path が消える (4→3 件) だけで、他文字列 (live の policy 拒否) は不変。実測で確認し、違えば段 4 で再裁定。
- held node 6 本 (driver 4 + driftguards 2、growth hold) は受入全走で走らない → 焦点走で `IZANAGI_RUN_GROWTH_HELD_TESTS` を立てて実走する (F10 再発型を避ける)。
- 候補 path を「あれば除く」fixture 補助 3 箇所 (floor_campaign `_remove_chain_artifacts_from_replay`、oracle_driver `_copy_git_visible_output` と sibling test) は削除後も成立 → 触らない。
- 成果物影響 (DW-G05): 放置時は historical reverify が段階 8 で止まり続け、削除後に held 真値を直さなければ held 焦点走が赤 (受入では見えない)。
- 分割: Codex author 1 本。段 2・3 は設計択一なし (裁定で方向確定) で省略。段 6 は held 真値 = 正しさ gate の期待値の変更なので独立 read-only 敵対レビュー 2 本 (弱体化でないか・記録の限定)。
- 環境: 実測は login (T-2810 と同条件)、焦点走は計算ノード dispatch、受入は tools/dev_wave_wait.py acceptance。
