---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-12
wave: dev-wave-t860-test-red
seq: 1
title: 焦点走でだけ落ちる test_spool_fold の赤 4 件をテスト側で直した — 全走の赤 2 件は main 由来で別 wave 所有 (テストのみ、変異 5/5 KILLED、branch worktree-dev-wave-t860-test-red)
---

## 本文

- **ユーザー依頼は「テストが失敗するところあると思う。適切にテストされているところか、
  テストしているところを直してください」、裁定は「じゃぁテスト側を直して」だった。**
  裁定に従い production (`tools/spool_fold.py` / `tools/check_docs.py`) は 1 byte も変更していない。
- **赤は 2 種類あり、別々の帰属だった。**
  - 全走 (main `427da17c`、計算ノード、583.00s): **2 failed / 9123 passed / 20 skipped**。
    赤は `test_t793_report.py` の 2 node だけで、**main HEAD 自身が赤**である。
    peer 3 セッションが独立に同じ結論へ到達し `worktree-dev-wave-t827-slow-tests` の
    `292151a5` 等で修正済みだったので、**本 wave は当該 file を触らず重複実装を避けた。**
    本 wave の全走は「main 由来」帰属の独立 2 例目の実証になる。
  - 焦点走 `test_spool_fold.py`: **4 failed**。これが本 wave の獲物。
- **機序は「全走では他 module の import 副作用に隠れ、焦点走でだけ落ちる」型だった。**
  `_load_rotate_limit(repo)` は fold 対象 repo の `check_docs.py` を importlib で読むが、
  その `from dev_waves.launch_authority import ...` は**読み込む側 process の `sys.path`** で
  解決される。fixture repo の `tools/` は `sys.path` に無い。repo 外 probe で
  「`tools/` 無し → FAIL / 実 checkout の `tools/` 有り → OK」を実測した。
- **同型の 2 例目が既にある。** [T-813] が「`orchestrator/` が `sys.path` に入るかどうかが
  `test_reflux_ir.py` の module 直下 `sys.path.insert` の副作用に依存する」ことを実測している
  (正本 `output/insights/2026-08-11_t813-acceptance-sharding/` の M-6b)。peer [T-827] からの共有で判明した。
- **段 6 の敵対レビューが親 brief の主張 2 件を実測で覆した。**
  (a)「4 node は bytes 厳密 golden」は誤りで、N37 は `status`・fragment・path の**構造判定**であり
  `after_bytes` 比較を持たない。変異 M3 の実観測 (N37 が落ちない) が独立に裏付けた。正しくは
  **byte 厳密 3 + plan 構造 1** である。(b)「全走でも緑」という受入条件は既知 baseline (2 failed) と
  矛盾して非一意だったので、**「main 427da17c 由来の既知 2 node 以外に新規 failure なし」**へ改めた。
- **レビューの must-fix 1 件目は「中心契約を観測する node が 1 つも無い」だった。**
  context manager が fixture でなく実 checkout の `tools/` を掴む形へ書き換えても、両者の
  source bytes が同一である限り既存 4 node は緑のままだった。**親 brief が明示的に却下した形を
  受理できていた。** positive control を 1 node 追加して閉じた。
- **変異 matrix は round 3 で 5/5 KILLED、期待 node 完全一致、baseline PASSED。**
  erratum: **round 1 の M3 は MISMATCH**。real canonical の 3 node と登録したが実観測は
  synthetic を含む 8 node だった。`DW-M08` に従い初回を probe と明記し、実観測から完全集合を
  再導出して round 2 で一致させた。M4/M5 (context manager が実 checkout を掴む / 復元を落とす) が
  positive control の恒真性を否定した。
- **新旧両走 (`DW-M08`) は構造的に取れない。** 変更前の tree では baseline 自体が当該 4 node で
  赤になり harness が fail-closed で止まる。その事実が新旧差分の証拠である —
  **変更前は 4 node が入力によらず必ず落ちるので検出力ゼロ、変更後は production の byte offset
  変異 (M3) で 3 node が正しい理由で落ちる。**
- 材料と裁定パッケージ (R1/R2) は `output/insights/2026-08-12_t860-test-red/package.md`。
  レビュー・実装子の逐語と変異台帳 3 round も同ディレクトリに置いた。

## 次の一手差分

### 新規

- {{T:load-rotate-limit-import-provenance}} **P2・ユーザー裁定待ち**:
  `_load_rotate_limit` が fold 対象 repo の `check_docs.py` を読みながら依存 (`dev_waves`) を
  呼び出し側 process の `sys.path` で解決する結合をどうするか。選択肢 (a) 現状維持 (fail-closed)、
  (b) 対象 repo の `tools/` を import 文脈へ束縛、(c) `check_docs.py` を自己完結にする
  (bytes が変わるので pin 閉包の再確認が要る)。正本は
  `output/insights/2026-08-12_t860-test-red/package.md` の R1。
- {{T:focal-red-invisible-to-acceptance}} **P2・ユーザー裁定待ち**:
  「全走では緑・焦点走では赤」型を現行の受入が構造的に見逃す件。独立 2 例目 ([T-813] M-6b) が
  成立しており `DW-G03` の族一般化条件を満たしうる。選択肢 (a) 現状維持、(b) 段 6 受入へ変更 file の
  焦点走を 1 本追加、(c) `DW-O18` の焦点走規定を強化、(d) import 副作用を検査する meta-test。
  走行時間の増分を実測してから決める (恒久ルール「開発するほどテストが遅くなる構造を作らない」)。
  正本は同 package.md の R2。
