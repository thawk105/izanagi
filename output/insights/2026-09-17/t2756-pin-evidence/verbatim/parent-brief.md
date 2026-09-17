# 親 brief (段 1) — [T-2756] mocc 第 2 例に向けた ccbench pin 更新項の再承認材料 3 点 (docs-only)

- wave: dev-wave-t2756-pin-evidence / branch worktree-dev-wave-t2756-pin-evidence / worktree /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2756-pin-evidence
- 基準: local main 38353207f719acb0871cfe3d9bbe3a02490282bb (= origin/main、乖離 0)。submodule gitlink = 511c9538e4e8efa54b45cda62e72389ed3b706ec (不動)

## 研究前進
論文の増分主張「指定した二つの CC 実装 (Silo / MOCC) で合成・評価手順を実証した」(D2114 項 2) に向け、certified な mocc 経路の必要条件である pin 前進 (D1373 関門の通過、D2104 項 13 / D1603 の再承認手続き) を**ユーザーが裁定できる材料**を揃える。完了判定 = insight に D1603 の材料 3 点が揃い、見送り台帳 (`docs/phase3.md` の [T-167] 行) からその insight が参照される。本 wave は pin を動かさず、性能・正しさの測定も行わない。

## scope (本題の材料提示だけ)
1. 候補 full OID の確定: mocc 単独 = `e9e477ca1b55348ab4530de0b1cf663ce4555290` (submodule の hook branch `izanagi-t1943-mocc-g2-readfrom-witness` の先端)。
2. `tools/check_trace0_preprocess_identity.py` の実走 (old=511c9538…, new=e9e477ca…) の結果 (report JSON を verbatim へ保存) と、checker の保証範囲の明記。
3. 承認済み定数・事前登録・identity・凍結への波及表 (骨格 = `output/insights/2026-09-17/cross-protocol-scope-release/README.md` §5 の 13 行) を、pin を束縛する全 file の閉包 (親の実測: full 40 桁 79 file / 7 桁を含む 134 file、台帳・archive・insights 除く) に拡張し層別に分類する。
成果物 = `output/insights/2026-09-17/t2756-pin-evidence/README.md` + `verbatim/` (checker report・閉包一覧・子の逐語) + `docs/phase3.md` [T-167] 行への 1 行追記 (insight への参照) + spool worklog fragment。decisions fragment は新しい設計判断が生じた場合だけ。

## 確定済みユーザー裁定 (覆さない)
D2114 項 3 (pin 前進は未承認、材料が揃ったら見送り台帳の再承認として別途提示、初回候補は mocc 単独)、D2104 項 13 (非 silo between-run 実測は保留)、D1603 (材料 3 点が揃ってから裁定)、D297 (保証名 = 「選定した macro context における TRACE=0 正規化 preprocess 出力の同一性、および include 活性の同一性」、翻訳単位の同一性を名乗らない、複数 compiler、admission toolchain と同一とは主張しない)、D986 (checker の 3 穴は塞ぐ)、D722/D723 (mocc 実供給 define・commit tree 走査・submodule 限界)、規律 2 (正しさゲートを緩めない)、規律 7 (過去の certified 判定は旧 pin で保持)。

## 不変条件
- superproject の gitlink・`orchestrator/campaign/pin.py`・`orchestrator/campaign/s8b_approved.py`・凍結物・事前登録は 1 byte も動かさない。
- checker を改変しない。checker が拒否しても「前進可能」とは判定しない。合格しても「前進可能」と判定するのは本 wave ではなくユーザー (再承認)。
- gate・検査・台帳・一般化の新設なし (仮想リスク向けは scope 外)。
- 実装面差分ゼロ → 変異 matrix 免除 (DW-S04)。受入全走は免除しない。

## 段 1 で実測した事実 (brief の前提)
- 候補 e9e477ca は現 pin 511c9538 の**直系子孫** (`merge-base --is-ancestor 511c… e9e4…` rc=0、merge-base = 511c9538)。4 commit: ef9328a3 (trace v2 hook、2026-08-21) → 058d0c4e (include comment 1 行、T-1506) → ae6880f7 (T-1943 witness) → e9e477ca (TRACE=0 include identity 保全)。全 commit が `cc/mocc/transaction.cc` だけを変更 (diff-tree raw: M 1 path、+141 行)。前 wave の「非祖先」表記は「候補が現 pin の祖先ではない」の意味であり、checker の祖先性 gate (old ⊑ new) は通る形。
- 過去の checker 実走は区間別: 511c→058d0c4e (T-1506、16 context 一致、archive 872)、058d0c4e→e9e477ca (T-1943、16 context 一致、archive 1079)。**pin 前進の命題そのもの (511c→e9e477 直接) は未実施**。checker はその後 D986 (2026-08-26) と t1642 文言 (2026-09-16) で改版。
- context 行列 = `SILO_SPACE.enumerate()` 8 genome × `_context_overlays()` 2 = 16。`EVOLVE_BLOCK_SOURCE_PROTOCOLS` に `cc/mocc/transaction.cc: 'mocc'` 登録済み (D722 の実供給 define 経路)。`PROVEN_REPO_ABSENT_MACROS = {MQLOCK}`。
- login node (pegasus02) の compiler: `/usr/bin/g++` 11.4.0、`/usr/bin/g++-12`、`/usr/bin/clang++` 14.0.0。g++-13 は無い。
- worktree 側 submodule は primary の module store を origin とし、候補 object を持つ (`cat-file -t` = commit)。

## provisional 裁定 (攻撃対象)
- (P1) 候補は e9e477ca 単独で確定してよい。根拠: D2114 項 3 の指名、直系子孫、diff 1 file、T-1943 で checker 通過済みの先端。TicToc・旧候補 c9c1a9c は積まない。
- (P2) checker 実走の形: `python3 tools/check_trace0_preprocess_identity.py --repo <worktree>/external/ccbench --old 511c9538… --new e9e477ca… --cxx <compiler> --expect-paths cc/mocc/transaction.cc` を g++ 11.4 / g++-12 / clang++ 14 の 3 本で走らせる。login node で git と `-E -P` だけを使う軽い処理であり runbook の「重い処理」に当たらない。3 本とも rc=0 のときだけ材料 (2) を「合格」と書く。どれか rc≠0 なら「拒否」と書き、原因を構造化して載せる (前進可能とは書かない)。
- (P3) 保証範囲の逐語 = D297 の保証名 + 「16 context は Silo の genome 空間 (BACK_OFF / NO_WAIT_LOCKING_IN_VALIDATION / NO_WAIT_OF_TICTOC / WAL) × GLOBAL_VALUE_DEFINE overlay であり、mocc TU に対する実効 define map は 4 種・正規化 digest は 2 種 (T-1506 実測)。mocc 固有の macro 空間は列挙していない」+ mocc trace.hh 1 行特例 (`#if TRACE` 初期枝内の `#include "../../include/trace.hh"` 1 行の追加だけ) + header 差分は保証外 (今回の diff に header は無い) + compiler 依存 + D986 で塞いだ 3 穴 + D723 の submodule 限界 + 「この検査だけで trace の完全除去を証明したと解釈しない」(checker docstring)。
- (P4) 波及表の分類軸 = {A 定数 (新系列で更新が要る)、B 事前登録 (erratum または新登録、旧登録は旧 pin で保持)、C identity / lock / evidence (新系列は新 ID、旧は保持)、D 凍結物 (保持、再凍結の要否)、E 歴史記録・figure provenance・paper-story 結果 (保持、書き換えない)、F テスト pin / fixture (定数更新に追随して更新、機械的)、G 一致検査 (pin 不一致で拒否する consumer)}。134 file を全数分類し、結論は「pin 前進は既存の certified 判定を無効化しない (規律 7)。新 pin で継続する系列だけが A〜C・F の更新を要する」。
- (P5) 見送り台帳への提示形 = `docs/phase3.md` [T-167] 行の末尾に「【2026-09-17 追記: 材料 3 点 = <insight path>。再承認は未提示】」を 1 行足すだけ。再承認の裁定文・承認語は書かない。

## 模擬 / 実の差
checker は実走 (模擬なし)。閉包は `git grep` の実測 (pin の 4 形: full 40 桁、7 桁 `511c953`、8 桁 `511c9538`、describe 形 `g511c9538`)。子は read-only で pytest 非実走 (静的検査)、親が実測する。

## 並列分割
docs-only → Codex author なし。段 2 plan 1 本 (read-only、閉包の分類案を file:line で)、段 3 consult 2 レンズ (A: 正しさ境界 — 保証範囲の言い過ぎ / 言い足りなさ、候補確定の根拠、P2 の実行形; B: 波及表の完全性と分類誤り、規律 7 との整合、見送り台帳への提示形)、段 5 親が checker 実走 + insight 執筆、段 6 review 2 レンズ (同じ 2 軸で成果物を攻撃)。

## 純増 (既存被覆との差)
既存: §4 候補観測、§5 骨格 13 行、T-1506 / T-1943 の区間別 checker 結果。純増: 直接区間 511c→e9e477 の checker 結果 (3 compiler)、134 file の全数分類、保証範囲の逐語、見送り台帳からの参照。
