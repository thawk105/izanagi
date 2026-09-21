---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-21
wave: dev-wave-mocc-xp-pin-candidate
seq: 1
title: mocc の X/P 計装を pin 候補へ載せる前段 — 計装 patch はそのまま commit すると D297 が拒否し、include 1 行と型 2 箇所の修正で D297 を通ると実測した (docs-only、Codex 利用枠切れで実装は次 wave、branch worktree-dev-wave-mocc-xp-pin-candidate)
---

## 本文

- 依頼 (ユーザー直接起動の `/dev-wave`): T-2294 (D1686) の X/P 計装を現行 pin e9e477ca の G2 read-from witness hook 系統の submodule branch へ統合し、正例・負例と D1603 の材料 3 点を揃える。
  push・gitlink / `CCBENCH_FULL_SHA` 更新・再承認の提示・探索開始は scope 外。記録 = `output/insights/2026-09-21/mocc-xp-pin-candidate/README.md`。
- 段 1 の実測 (login、repo 外 scratch): 計装 patch は hook branch 先端 = 現行 pin に厳密適用で当たるが、**そのまま commit すると D297 検査が rc=1 で拒否** (`#if TRACE` 内の `#include <set>` が include 行の不一致になる)。
  `#include <set>` の 1 行を除き `std::multiset` 2 箇所を trace.hh が供給する `std::unordered_multiset` に替えた版は GCC 11.4 / 12.3 で pass (TRACE=0 の前処理)、負例 4 本も厳密適用で当たり、verifier の proof-surface gate も真 (e9e477ca は偽)。
  TRACE=1 の build と実行は測っていない。設計判断は {{D:mocc-xp-candidate-keeps-d297-include-rule}}。
- **Codex の利用枠が切れた。** 段 2 plan (14:22〜14:32、受理) の直後、段 3 相談 2 本 (14:32:57 / 14:32:59 投入) が起動直後に失敗した (launcher log 上 6 秒 / 5 秒、launcher rc=2、codex の exit code 1、出力 0 byte)。
  `turn.failed` の本文は「You’ve hit your usage limit. … try again at Sep 26th, 2026 7:35 PM.」(時間帯の表記なし)。
- D95 決定 (3) (Codex 不可用時は親が代筆しない) に従い、段 4 で「実装しない」と裁定し `4→7→8→9` の docs-only で閉じた。repo の実装面 (commit 対象) は書いていない。repo 外の probe script と scratch 上の測定用の置換は親が行った。
  既定は Codex 復帰後の次 wave で進めることで、復帰前に進めるなら D105 の waiver (ユーザー裁定) が要る。本 wave は waiver を求めていない。従量経路 (credits 購入・API キー) には切り替えていない。
- **本 wave の記録は Codex の敵対検査を受けていない** (段 3・段 6 の Codex 子が走っていない)。代わりに独立 context の Claude (opus、読み取りのみ) で insight と fragment の事実照合を 1 本行い、must-fix 5・should 8・nit 11 を全件反映した (Codex レビューの代替とは扱わない)。
  段 2 plan は次 wave の段 2 成果物として流用し、段 3 を当ててから確定する。
- plan の指摘で brief を 3 点訂正した: 「現行 pin の mocc 結果は常に indeterminate」は広すぎる (e9e477ca + T-2294 patch の診断実走は certified の正例を持つ、ただし NON_ADMISSIBLE の診断 build)。p4 の D297 pass は TRACE=0 前処理の証拠で TRACE=1 build の証拠ではない。p4 script の冒頭コメントは処理本文と食い違う。
- 変異 matrix は免除 (実装面の差分ゼロ)。受入全走は本 wave の記録 commit を含む tip で land 前に 1 回投入する (結果は land の受領証)。記録前に local main `47368e7d5` を ff-only で取り込み (provenance 全史監査 rc=0、12,364 件、新規違反なし)、記録 commit の直前に `f646e7e85` へ再度 ff-only した。
- 工数: Codex 子 3 本 (plan 1 = 受理、consult 2 = 起動直後に枠切れ)、Claude の照合子 1 本 (opus、79 tool 呼び出し、約 13 分)、login の probe 10 本 (うち D297 検査器の実走 7 回、p6 の再実行を含む)。

## 次の一手差分

### 更新

- [T-2295] **P2**: `I` 面 — 現行 pin e9e477ca の `cc/` と `include/` に、verifier が I emitter と認識する文字列を含む file は 0 件 (2026-09-21 の文字列検索、別表記の不在までは証明しない)。
  X/P を pin 候補へ載せても閉じない — mocc は write-intent shadow の新設計が要り、silo の `izanagi-trace-t152` は現行 pin の祖先でない (`output/insights/2026-09-21/mocc-xp-pin-candidate/README.md` §5)。
  certification gate は I を要求しないので、I の不在は X/P を載せた系列の gate の妨げにならない。
  base: 5b542686bbef38eb397f6be2013f23e06e85d56eba42fe631bf7c70f59b8e39c

### 新規

- {{T:mocc-xp-pin-candidate-commit}} **P2・新規**: Codex の利用枠の復帰後 (表示「Sep 26th, 2026 7:35 PM」、時間帯の表記なし) に fresh wave で、mocc の X/P 計装を e9e477ca の単一の子 commit として hook 系統の submodule branch に載せ、D1603 の材料 3 点を揃える。
  入力 = `output/insights/2026-09-21/mocc-xp-pin-candidate/README.md` §3・§4・§7 (候補 bytes の目標 = blob `e393efbf…`、D297 は GCC 2 版 pass 済み、段 2 plan を流用して段 3 から)。
  完了 = C の commit・bundle・主 checkout の submodule git dir への fetch、C 上の正例・負例の compute 1 走、C に対する D297 (GCC 2 版 + clang)、波及表の点検。
  push・gitlink と承認定数の更新・再承認の提示 (D2114 項 3 の見送り台帳経路)・探索開始は含めない。
