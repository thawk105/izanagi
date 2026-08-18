---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-18
wave: dev-wave-t902-holdout-scan-cost
seq: 1
title: holdout live scan の regex 係数を削った — 「ファイル数比例を外す」は出力契約と両立しないと実測で確定した (コード + テスト、branch worktree-dev-wave-t902-holdout-scan-cost、変異 matrix = baseline PASSED・9/9 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- **依頼文が引いていた裁定は上書き済みだった。** 引数は 2026-08-12 **第 4 束**の
  「ファイル数比例の live scan は保留対象そのもの。除去または保留の形を [T-917] と調整」を
  逐語で持っていたが、同 8-12 **第 6 束**の [T-915] が
  「holdout live scan は測定の公正 = **保留対象外**。保留も除去もせず、ファイル数比例をやめる
  最適化として T-902 実装側が扱う」と上書きし、2026-08-15 棚卸しでも確定していた。
  F31 に従い本文優先で後者を採った。[T-917] は 2026-08-12 land 済みで二重着手はない。
- **[T-902] を阻んでいた閂は実在しなかった。** `freeze_verification_hold.HELD = True` により
  `verify_document` は `_verify_source` を評価しない。現行 generator の sha256
  `4bd0bc63…` は凍結記録 `1910fff3…` と**既に不一致のまま全検査が緑**であり、
  「実装を 1 byte 変えると freeze 再発行が要る」は成立しない。
- **裁定文が求めた「ファイル数比例をやめる」は出力契約と両立しない。** `skipped_binary_count` は
  全 file の binary/UTF-8 判定を要し、regex hit は任意位置にありうるので短絡できず、
  `exempt_exact` の免除判定は全 bytes の SHA-256 を要する。段 2 プランと段 3 の 2 レンズが
  独立に同じ結論へ達した。**本 wave の到達点は係数削減である**と成功条件を書き換えた。
  未達として改善を捨てることはしない。
- **律速は Python ではなく lustre のメタデータ遅延だった。** `os.stat` 163.0 us/file、
  open+read+close 345.6 us/file。`pathlib` と raw `os.open` の差は 10 us 未満。
  `is_file()` は warm でも 171.6 us/file (合計 2.324s) でページキャッシュでも消えない。
- **親の provisional 裁定 A (`is_file()` を `os.fstat` へ畳む) を段 2・段 3 が独立に反証した。**
  実測 2.3 秒 (18%) の価値があるが、directory / symlink 先の特殊 file / FIFO / Unix socket /
  device / dangling symlink / 削除 race / stat 権限不足 / NUL 入り path の 9 系統で、
  例外の型・文言・「そもそも open しない」現行挙動を保存できない。性能を理由に厳密等価性を
  緩めないため不採用とした。{{D:holdout-scan-coefficient-only}}
- **新しい regex parser を書く案を、追加効果 0.71 秒 (約 5%) を理由に却下した。** 段 3 レンズ A の
  「既存 `_derive_required_literal` を 1 要素 mapping で軸ごとに再利用する」案を採り、
  新しい false negative 面をゼロにした。親が最初に書いた「metachar 直前までを prefix とする」
  規則は量指定子が literal 末尾に掛かると false negative を出し、40 万試行の fuzz で
  **prefilter 適用 78 件中 5 件の反例**が出ていた。B' はこの規則を導入しない。
- **段 6 は 2 レンズとも NO-GO。両レンズが独立に同じ 1 件を指摘した** — 出力に存在しない
  `per_axis_paths` の順序を守るため `texts` 全走査を 2 系統追加し、新テストがそれを設計契約として
  固定していた。実費は 18.23 ms と些少だが、ファイル数比例の走査をテストで凍結する形そのものが
  test-time regression の既裁定に反するため、集合演算へ単純化し当該変異を登録から外した。
- **親自身の所見 2 件は実測で自壊した。** (1)「等価性 fixture の text 変更で検出力が消えた」は
  レンズ D が反証し、親の実測 (共通 literal は軸 literal に包含され、除去しても観測差が出ない
  等価変異) とも整合した。(2)「共通 literal 走査の除去で約 0.6 秒浮く」は実測 **0.030 秒**で、
  見積もりが 20 倍外れていた。測らずに裁定していれば無意味な変更を実装子へ投げていた。
- **親 brief の凍結 pin の記述を 1 件訂正した。** 「live bytes を束縛する pin は無い」は不正確で、
  正しくは generator source の pin は hold 中で評価されない一方、
  `output/s8b-freeze/holdout_freeze.json` の raw bytes は `s8b_ratified_freeze.load_legacy_freeze` が
  **hold と無関係に無条件で** pin している。結論 (generator を編集してよい) は変わらない。
- **codex 認証が wave 中に失効した** (13:01 JST、`401 Unauthorized ... token_revoked`)。
  consult luna は 371 秒・34 model call・出力 13,874 token を消費した後に死に、
  consult sol は同じ 401 を 3 回受けながら既存 session で耐えて回復後に完走した。
  並行 wave からは「枠切れ (数秒・token ゼロの即死)」と周知されたが、
  **本 wave の失敗はその型ではなく認証失効**である。再投入は別 artifact-root で行った。
  F172 の再発として記録した。
- **エージェント工数**: codex 子 8 本 (plan 1・consult 3 (1 本不受理)・author 1・review 2・fix 1)。
  plan / consult は `reasoning=max`、author / review / fix は `high`。
- 正本 = `output/insights/2026-08-18_t902-holdout-scan-coefficient/README.md`

## 次の一手差分

### 完了

- [T-902] `s8b_holdout_freeze.search_repository` の regex 係数を削った。軸ごとの prefilter
  (既存 `_derive_required_literal` を 1 要素 mapping で再利用) と、`texts` identity に束縛した
  call-local memo により、regex 走査を 9 本から相異なる 5 本へ減らした。
  出力は実 repo で完全 slow path と canonical bytes 等値を 4 試行確認
  (sha256 `63c482d2fc63a8edadcd2a944f9fa81f903ff85a8bff1922a3e3a5e2dfef153a`、wave 前と同一値)。
  削減は最小同士 12.791s → 9.086s (29.0%)、中央同士 14.31s → 11.18s (21.9%)。
  焦点走 120 passed / 2 skipped、変異 matrix baseline PASSED・KILLED 9/9・MISMATCH 0。
  **「ファイル数比例の撤廃」は出力契約と両立しないため係数削減で終端する。**
  残る比例項の扱い ((a) 未保留 node の恒久保留 / (b) 読取経路の置換 / (c) 現状維持) は
  {{T:holdout-scan-remaining-proportionality}} が保持する。
  remaining: none
  base: 6f07db077ab3be4750901cf43761c0fdfe8c6aeb8af19fead8b7f1c186a4be5d

### 新規

- {{T:holdout-scan-remaining-proportionality}} **P2・新規**: holdout live scan に残る
  ファイル数比例項の扱いを裁定する。`search_repository` は全 file の列挙・open・read・decode を
  維持するため、係数削減後も lustre のメタデータ遅延 (stat 163 us/file、
  open+read+close 346 us/file) に比例する。選択肢は
  (a) `test_s8c_preregistration_invariant.py::test_wave_files_do_not_contaminate_production_holdout_scan`
  (call 14.57 秒、未保留) の恒久保留 — **ユーザー明示命令が要る**、
  (b) `is_file()` の独立 stat を open 後の `os.fstat` へ畳む (実測 2.3 秒 = 18%。ただし
  FIFO / device を現在は開かない挙動と例外の型・文言を保存できないため、厳密等価性との取引)、
  (c) `git grep` 系への読取経路置換 (集合が既に不一致 — in-memory 524 件に対し worktree grep
  519 件、`ycsb_` は 955 件に対し 944 件。binary / UTF-8 / untracked / submodule の意味論を
  別途証明する必要があり別 wave)、(d) 現状維持。いずれも受理集合か保留 registry に触るため
  親では決められない。
