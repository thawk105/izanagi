# 段 1 brief — 消えたブランチの未 land 作業を検出する監査を land する

## scope

`tools/audit_dangling_commits.py` (新規) と、`.claude/commands/cleanup-branches.md` §1 からの
呼び出し 1 行、および whole-file SHA-256 pin の独立 2 箇所更新を、**現行 main
(`94db52ef`) の上に Codex `role=author` で新規実装して land する。**

## 確定済みユーザー裁定

- 2026-08-05 「1,2,4 推奨通り。3 は取り込む価値がありそうなら取り込み」
  (一次資料: `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-05-cleanup-branches-dangling-commit-gap.md`)。
  裁定事項 1 = 起票者推奨 (a) の「§1 に 2 段判定つきの到達不能検査を足す」。
  実体は tools/ 側のスクリプトに置き §1 から呼ぶ形 ((a)+(b) の合成) とする。
- 裁定 3 (`rescue-t213` の取り込み) は前セッションが「取り込まない」と結論済み。本 wave の scope 外。
- 裁定 4 (`worktree-wave-t409-impl-trigger-grammar` 削除) は権限分類器に拒否済み。本 wave の scope 外。

## 前提の実測 (DW-S01: 承認済み裁定の前提を実測する)

1. **`e8d0c44c` は land できない。** `check_ai_provenance.py` の full-history 監査は
   D95 導入 commit 以降を恒久的に検査する。実装面 path を持ち Codex `role=author` を欠く
   `e8d0c44c` を main へ入れると main が恒久的に赤になる。よって同 commit は**参照案としてのみ使い、
   history には入れない**。新 branch `worktree-dev-wave-cleanup-dangling-audit` を main から作った。
   参照差分は `reference-impl-e8d0c44c.diff` に退避済み。
2. **main には未 land。** `94db52ef` に `tools/audit_dangling_commits.py` は無い。
3. **既存被覆 (性質での検索)。** 「到達不能 commit として未 land 作業が失われる」vector を
   検出する経路は repo に無い。`tools/codex_reasoning_ab.py` が `git fsck --unreachable` を
   使うが、目的は A/B 実験用 repo の健全性判定であり、掃除経路からは呼ばれない。
   `cleanup-branches` §1 は現存ブランチだけを棚卸しする。**純増検出力 = 「ブランチごと消えた
   未 land 作業」を単発実行で検出できるようになること。**
4. **入口の byte 予算。** `.claude/commands/cleanup-branches.md` は現在 3,959 bytes、
   `tools/check_docs.py:170` の上限は 4,000。ただし負例テスト
   `test_cleanup_command_invalid_backtick_info_is_rejected` が **+17 bytes** 追記して
   「違反ちょうど 1 件」を要求するため、**実効上限は 3,983**。空きは 24 bytes しかない。
5. **pin 閉包 (DW-O09)。** `.claude/commands/cleanup-branches.md` の whole-file SHA-256 は
   `tools/check_docs.py:330` (`CLEANUP_COMMAND_SHA256`) と
   `orchestrator/tests/test_check_docs.py:179` (`_EXPECTED_CLEANUP_COMMAND_SHA256`) の
   独立 2 箇所に pin される。`test_check_docs.py:4033` が本物のファイルから hexdigest を
   再計算して両者と照合する。durable manifest / FROZEN_MANIFEST / review ledger 側の pin は無い。
   producer は無い (DW-O10 不成立)。
6. **設計は 3 段判定でなければならない (前セッションの実測)。** 「到達不能 かつ 変更ファイルが
   main に不在」の 2 段では、稼働中 wave の tip を誤検出して実 repo で 30 件鳴った。
   「**他のどのブランチ先端にも無い**」を足すと 0 件になり positive control は鳴り続ける。
   本 wave はこの 3 段目を必須の不変条件として引き継ぐ。

## 不変条件

- **I1. 誤検出ゼロ性。** 現行 repo の実走で報告 0 件であること。稼働中 wave の tip・
  過去 rotation の古い版・fold 済み fragment を鳴らしてはならない。
- **I2. 見逃さないこと (positive control)。** 「未 land commit を持つブランチを消した」合成 repo で
  必ず鳴ること。この control は変異 matrix で恒真でないことを機械的に示す。
- **I3. 安全義務を削らない。** 入口の byte 予算捻出のために §2 の削除条件、§3 の F26/F51 手順、
  §5 の push 引き渡しを削除・弱化しない。削るのは重複記述だけとする。
- **I4. 負例テストの期待値を緩めない。** 入口は 3,983 bytes 以下に収める。
- **I5. 読み取り専用。** 監査スクリプトは repo を変更しない (`git fsck` と `git rev-list` 等の
  読み取りのみ。branch 作成・削除・gc をしない)。

## 成果物の形

- `tools/audit_dangling_commits.py` — 3 段判定の監査。既定で `docs/spool/`・`docs/archive/`
  を除外 (fold が消費する経路)。rc は「報告 0 件で 0」。
- `orchestrator/tests/test_audit_dangling_commits.py` — positive control 1 + negative control 4。
- `.claude/commands/cleanup-branches.md` §1 に呼び出し 1 行 (≤ 3,983 bytes)。
- `tools/check_docs.py` と `orchestrator/tests/test_check_docs.py` の SHA-256 pin 更新。
- docs: `docs/spool/` の worklog / failures fragment (親が docs-only で書く)。

## 成果物影響 (DW-G05)

実装しない場合、certified 選択・レポート・台帳の**値と受理集合は変わらない**。変わるのは
「ブランチごと消えた未 land 作業に気づけるか」だけである。よって本 wave は台帳の
恒久対応 (F114 予定) を成立させるためのものであり、研究成果物の数値には影響しない。
`tools/check_docs.py` の pin 更新は whole-file hash の通常更新で、受理の意味論を広げない。

## 親の provisional 裁定 (攻撃対象)

- **(P1) 軽量版で走る。** DW-C00 の 3 条件を評価した: 設計択一は裁定済みで割れていない、
  正しさ防壁 (verifier / oracle gate / proof chain) に触らない、受理集合の変更は
  whole-file SHA pin の通常更新のみ。よって段 2・3 を省く。ただし実装面があるため
  段 5 の Codex 実装子と fix 子は省略不可。
- **(P2) 段 6 のレビュー子は 1 本残す。** 新規検出器であり、過去に誤検出 30 件を出した実績が
  あるため。焦点は I1/I2 と「positive control が恒真でないこと」。
- **(P3) 参照案の扱い。** `e8d0c44c` の差分を Codex に**参照として**渡すが、Codex が現行 main 上で
  自分の実装を書き、乖離は理由付きで報告させる。親は実装面を直接編集しない。

## 並列分割方針

実装面は 1 ファイル群 (tools + tests + 入口 + pin) で結合が強いため、段 5 は Codex 実装子 1 本。
段 6 はレビュー 1 本 + 変異 matrix (親)。docs fragment は親が並行して用意する。

## 受入・実測の環境

- 対象テストと `check_docs.py` は worktree
  `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-submodule-recurrence`
  (branch `worktree-dev-wave-cleanup-dangling-audit`) の repo root で走らせる (DW-O18)。
- `check_ai_provenance.py` の履歴監査は D105 決定 (2) により計算ノードへ自動 dispatch される。
