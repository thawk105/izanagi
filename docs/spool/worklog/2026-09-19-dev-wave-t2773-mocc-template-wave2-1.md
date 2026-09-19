---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-19
wave: dev-wave-t2773-mocc-template-wave2
seq: 1
title: [T-2773] mocc の auditor-live 相当の機械実証 wave 2 を実走した — 温度述語 template (1 helper・1 hole・4 callsite・OFF 原文保存) を e9e477ca へ接続し、実 resolver の OFF = stock / ON-B 別 identity・計装 template 版の本文保存・DQ 13 対照・consumer 束縛 3 対照・auditor 定義 (read-only + 正しさ限定の射影) を 30 check all_pass の JSON に束縛、fresh auditor n=1 は A1' / A2' reject・B' pass で弁別 (コード + patch + テスト + docs、branch worktree-dev-wave-t2773-mocc-template-wave2、変異 matrix = baseline PASSED・16/16 KILLED 期待 node 完全一致・等価 M0 SURVIVED・MISMATCH 0)
---

## 本文

- ユーザー決定 (2026-09-19)「mocc 温度述語軸のオンボーディング段階 A を承認し、T-2773 wave 2 の機械実証を認可する。探索および pin 前進は認可しない」を起点に、D2134 項 8 の wave 2 を実装・実走した。段階 B (敵対レビュー) は段 6 のレビュー 2 本で兼ねた。**緑は探索・pin 前進・正式な軸採用のいずれも認可しない** (D2134 項 9、{{D:mocc-template-proof-wave2}})。引数の「wave 1 = t2780」は pilot discriminator ([T-2780]) で、D2134 項 8 の wave 1 は [T-2772] (entry 1666) — 両者 main に land 済みで前提は成立。
- 着手時 local main `657e1e5a7` (作成時 `a99425b66`、peer 通知を契機に ff-only) から fresh worktree、開始 gate rc=0。設計 §13 の未確定は e9e477ca 現物で確定 (`Epotemp::temp` = `uint64_t : 32`、`FLAGS_temp_threshold` = `uint64`、Options.cmake の universal 供給)。pin 閉包: 旧計装 patch の sha は 12 file (完全 sha) に出現 → 1 byte も変えず新 file で足す、auditor.md の sha は pin 3 箇所 (review_ledger / adapter json / originless baseline) → 同 wave で追随。
- 計画 1・敵対相談 2・author 1・レビュー 2・fix 1、いずれも `gpt-6-astra`。段 3 must-fix 2 件 (A: 計装 template 版の本文保存が機械 check に無い → `instrumentation_body_preserved` / B: auditor-live 機械要件 (1) の read-only 契約・入力射影が JSON に未接続 → `auditor_definition_read_only_and_projection`) を採用、refuted 6 件 (P3 型・brace・fallback、三比較、auditor 行番号、pin 3 箇所、cache route、鍵の偽陽性)。段 4 裁定 R1〜R21 (12 走 = template ON-B の正常系対照で broken 4 patch は再走しない、保証名の限定、束縛と all_pass の分離、PIN 分離、helper 名に izanagi を含めない、外側 guard 行を一意 witness)。
- author の未完 2 件: `.codex/role-adapters/auditor.json` (sandbox が `.codex/` を read-only mount、Errno 30) は T-1356 前例と同じく親が renderer 出力で置換し D105 waiver (reason=codex-sandbox-readonly-dotcodex、2026-08-18 承認の再利用) 付きの別 commit にした。`liveness-run.sh` (job dir) は author が job dir へ書けず親が計測操作 script として書いた — R20 / D95 決定 2 からの所有逸脱を記録する (repo には入れない)。生死確認 attempt 1 は親 script が GNU `patch --dry-run` (fuzz) で旧計装を template 適用後に当ててしまい rc=2、`git apply --check` (driver と同じ厳密適用) へ直した attempt 2 で rc=0。実装差分には帰属しない。
- compute (gen_S 11161.nqsv、Elapse 352 秒): 30 check all_pass。OFF = stock は実 resolver の正規化前処理 identity で一致 (`6454d9f3…`)、ON-B は別 (`41f52341…`)、論理行列 OFF 543 / ON-B 548 一致、計装保存の offset 19 + 35×6、DQ 13 / deny-only 4 / consumer 3 / auditor 7 項目、12 走 (W / U × hot 0 / cold 21 / default 10 × 1 / 4 thread) すべて certified & silent、verifier wall 最大 52.9 秒。**無 template と OFF の TRACE=0 `.text` は `ERR` の `__LINE__` (1193 → 1228) で 2 行差** — identity の正本は resolver なので設計どおりだが、binary 同一は主張しない。
- 段 6 レビュー: 両者 NO-GO must-fix 1 (per-key 入力由来対照の不足 = 親所見と同じ、M8 の DQ subtype 比較削除と tools の Bash 混入が素通り) → fix 1 巡 (test file 1 本、30 key の成立入力 → 1 箇所破壊対照、X 恒偽化対照を `false && (…)` へ)。B の 2 件目 (生死確認 attempt 1 と author 報告の矛盾) は refuted (上記 fuzz)。焦点走 1 = 658 passed / 2 skipped (deselect 2)、焦点走 2 = 660 passed / 2 skipped (deselect なし)。
- n=1 (fresh Claude `auditor` 子、Read/Grep/Glob、期待 verdict・fitness 非共有): A1' (validation の writer lock 削除、marker 外) = reject (型 13 + 8、hot での早期 lock による遮蔽を指摘)、A2' (`FLAGS_clocks_per_us` 依存) = reject (型 16 = 型 3 + 2)、B' (`!(temp < threshold)`) = pass (nit: stock と同値なので tie、marker の `#else` 枝は到達不能で冗長)。弁別成功。機械 `all_pass` には入れない。
- 変異 matrix (dispatch、HEAD 6861225c0、期待 node は dispatch 形の probe で実測): baseline PASSED、16/16 KILLED (期待 node 完全一致)、等価 M0 SURVIVED、MISMATCH / PARSE_ERROR / TIMEOUT 0。主 killer は新 test の意味検査 (軸契約・計装保存・束縛・gate 鍵・per-key 入力由来・auditor 項目)、sha 束縛だけの JSON consumer が単独 killer なのは JSON 自身の変異 2 件だけ。
- 受入全走は記録 commit を含む tip で land 前に 1 回 (結果は land の受領証)。段 8 自己改善は候補 4 件 (所有の逸脱 = DW-C01 で規定済み、patch fuzz の near miss と失敗 log の射影は親 memory、dispatch probe は DW-M07 どおり) で docs 変更ゼロ。
- 一次資料は `output/insights/2026-09-19/t2773-mocc-template-wave2/README.md` と同 `verbatim/`・`n1/`。専用 handoff は repo 外 job dir の `HANDOFF.md`。

## 次の一手差分

### 完了

- [T-2773] mocc の auditor-live 相当の機械実証 wave 2 (template 接続) を完了した。template・軸定数 module・計装 template 版・新 driver / JSON (30 check all_pass)・DQ / consumer 束縛の対照・auditor.md の mocc 節 + pin 3 箇所・gate test・n=1 の 3 候補が揃った。緑でも探索・pin 前進は認可しない ({{D:mocc-template-proof-wave2}})。
  remaining: none
  base: e70b63aee92d84ae753b144ecb1bcd96321945c5c8434627cd2c983cb56e611c
