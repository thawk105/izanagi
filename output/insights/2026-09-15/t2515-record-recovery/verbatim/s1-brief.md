# 段 1 brief — [T-2515] 未着地の研究記録だけを回収する

- 研究前進: B-4 の rr95/rr5 較正を止めた**認証経路の 3 週間故障**は、main のどの台帳にも残っていない。
  一次資料 (docs/failures.md) にこの型が無いと、同型のドリフトを次に引く手段が無い。進む主張は
  「認証経路を長期間走らせないこと自体が検知の穴である」で、完了判定は failures 台帳と insights に
  ドリフト年表 (2026-08-06 最後の成功 → 2026-08-20 3.10 構文投入 → 2026-09-01 関門義務化) と
  子 13 本の逐語が現れ、受入・land を通ること。**新しい測定はしない。**
- scope: `output/insights/2026-09-10/t2515-rr95-rr5-calibration/` へ当時の子逐語 13 本を
  `original-verbatim/` として足し、同 README へ**追記のみ**で年表と検知穴を残す。
  spool fragment を failures / worklog へ書く。この wave 自身の記録は
  `output/insights/2026-09-15/t2515-record-recovery/`。
- scope 外 (依頼が明示): 新しい gate・検査・一般化、仮想リスク向けの台帳追加、コード変更、
  再測定、branch 削除。**実装面の差分はゼロ** (docs / insights のみ)。
- 確定済みユーザー裁定 (逐語 = job dir の rulings-verbatim.md):
  - **D1936 項 6**: 「未land worktree-dev-wave-t2515-calib-rr95-rr5 の
    certify-materialize-backoff-patch は本裁定と食い違う範囲を採用しない」→ spool decisions seq=4 の
    1 本目は**回収しない**。
  - **D1936 項 43**: t1259 fixture 案は承認済みで T-2579 が実装・着地 → seq=4 の 2 本目も**回収しない**。
  - **D1936 項 46 / 項 47**: 旧 fragment の新規 T 2 件は裁定済み → **転載しない**。
  - **D1986 項 1**: rr5 の却下記録は却下のまま残す → 「rr95/rr5 が取れた」と読める書き方をしない。
  - **D1941**: 新規資料は日付配下。既存資料は bytes を変えずに置き、旧名索引を保つ。
- 不変条件: 既着地 bytes を 1 byte も変えない (job-evidence 7 file、mutation 成果物、
  `recovery-verbatim/`)。既存 README は**追記のみ**で、当時の記述を書き換えない (規律 7)。
  accepted 較正の取得を主張しない。規律 2 を緩めない — 関門を通すための記述を入れない。
- 成果物の形: (1) `original-verbatim/` 13 file = branch blob の逐語コピー、
  (2) 既存 README への追記 1 節、(3) spool failures 1 本・worklog 1 本、
  (4) 本 wave の insights 1 dir。
- (P1) **親の provisional 裁定・攻撃対象**: 旧 spool の failures 3 件のうち、
  待ち手偽成功は**新規 F ではなく F355 への 2026-09-10 再発追記**にする (F817 は 2026-09-03 に
  F355 へ supersede 済み)。残る 2 件 (3 週間故障 / 字面検索による既存 F 見落とし) は新規 F。
  F934 には「988706 / 988708 で関門が初めて実走した」supersede 追記を入れる。
- (P2) **親の provisional 裁定・攻撃対象**: spool decisions seq=1 の 2 本
  (rratio exact 5 値 / 関門の python3.10 起動) は**回収しない**。記述する設計は main に着地済みで、
  後者は D1936 項 6 が関門ごと撤去したため現行 main と食い違う。
- 既存被覆の実測 (純増だけ書く): docs/failures.md に T-2515 は 0 件。主題検索 (3 週間 / 988653 /
  condition-gate.stderr / intelpython) でも該当 F は無い。worklog entry 1429 は先行**回収** wave の
  もので、T-2515 wave 自身の entry は無い。insights の job-evidence 7 file は blob 一致で着地済み。
- 変更面アンカー: `output/insights/2026-09-10/t2515-rr95-rr5-calibration/README.md` 末尾へ節追加。
  同 dir 直下へ `original-verbatim/` 新設。`docs/spool/failures/` `docs/spool/worklog/` へ新 fragment。
- 受入・実測環境: Pegasus login (計測なし)。全走は `tools/run_tests.py` 経由、
  受入は `tools/dev_wave_wait.py acceptance --lease-optional`。
- 並列分割: docs-only のため実装子なし (D95 の実装面ゼロ)。段 2 plan 1 本、段 3 敵対 2 本 (read-only)。
  段 6 の review 子は (P1)(P2) の裁定が割れた場合だけ起こす。
