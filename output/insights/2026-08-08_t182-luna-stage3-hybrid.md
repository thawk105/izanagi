# 段 3 敵対相談の sol/luna 混成化と model 単一権威の機械 pin (2026-08-08)

wave = `dev-wave-t182-luna-stage3` / branch = `worktree-dev-wave-t182-luna-stage3`
逐語一式 = `2026-08-08_t182-luna-stage3-hybrid-verbatim/`

## 何をしたか

dev-wave 段 3 (敵対相談) の codex model を、sol 一色から **sol 1 本 + luna 1 本の混成**へ変えた。
あわせて model 指定の所在を 1 か所へ集約し、drift を機械検出できるようにした。

**採用根拠はユーザー裁定である。** [T-182] の被覆率 (11 件中 10 件 = 91%、token −31.6%) は
同 ID 自身が「循環・非盲検・事前登録なし・n=1 のため policy 根拠にしない」と記録しており、
本 wave もこれを採用根拠にしていない。[T-184] (証拠に基づく既定 policy 採用) と
[T-189] (妥当な比較実験の設計) は supersede も carve-out もせず、open のまま据え置く。

## 経緯 — 全 luna から混成へ

ユーザーの初回裁定は「段 3 を luna@max に置き換えてほしい」だった。段 3 の敵対レビュー 2 本は
これに **NO-GO** を返した。主要な論拠は次の 2 点である。

1. D207 が「検出力を下げる変更は規律 2 (正しさゲートを緩める変異を許さない) の対象」と明記しており、
   この repository の自己解釈では段 3 は正しさゲートの一部である。
2. 91% は「11 件中 1 件の見落とし」であり、全レンズを luna にすると sol にしか出せない所見を落とす。

さらに親が一次資料を読み直したところ、**親自身の前提が誤っていた** (下記 erratum 1)。
これらを新事実としてユーザーへ再提示した結果、**混成**が選ばれた。
混成なら sol レンズが 1 本残るため段 3 全体の検出力低下は限定され、段 3 の token は約 16% 減る。

## 親の erratum 3 件

1. **「luna は sol が出さなかった所見を 2 件出した」は誤り。** 一次資料
   `2026-07-29_t182-model-routing-shadow-pilot.md` の「shadow-only の所見 2 件」は
   **luna 1 件 + mini 1 件**であり、luna のその 1 件も**別の sol run (レンズ A の所見 9) が
   独立に到達**していた。sol を 2 本走らせる現行構成に対する luna の純増所見は **0 件**である。
2. **段 4 裁定の「sol の検出集合を 1 件も失わない」は誤り** (段 6 レビュー R2 が指摘)。
   T-182 の比較はレンズ B の同一 prompt に対するものであり、luna を割り当てたレンズでは
   sol が出したはずの所見を落としうる。**無損失は主張しない。**
3. **変異 M5 の事前登録が過剰決定だった。** 期待 4 node に対し実際は 9 node が赤になり MISMATCH。
   `DW-M02` に従い初回結果を消さず erratum として残し、単一理由の M7 へ再照準した (M7 は KILLED)。

## 確定した設計 — model の単一権威

model の権威は `docs/dev-wave/operations.md` の `DW-O01` にある次の 1 行だけである。

```
`<model>`: 段 3 のみ 2 本で `gpt-5.6-sol`→`gpt-5.6-luna`、他段 `gpt-5.6-sol`。
```

`DW-O01` は条件 dispatch 01 が「codex subprocess を起動する直前」に必ず読む節であり、
権威が起動直前の必読集合に入る。`DW-S02` / `DW-S03` / dispatcher からは model 名を削除し、
`DW-O01` の起動雛形は `-m <model>` の placeholder にした。

### 期待値照合ではなく「不在」を検査する

段 3 レンズ A が、期待値照合方式の decoy 攻撃を構成した — 正しい slug を 1 つ残したまま
同じ節へ別の slug を足せば `values == [expected]` で通る。同型の fail-open は D223 で
一度実害を出している。そこで pin を**「model slug がそこに存在しないこと」**の検査にした。
権威行だけが例外で、その行自体は exact 1 件で固定する。decoy を置く場所自体が違反になる。

pin は 7 本ある。

- `DW-O01` 可視本文に権威 literal が exact 1 件
- `DW-O01` 可視本文に `-m <model>` が exact 1 件
- `DW-O01` 節が一意 (上と別 finding)
- `DW-O01` 内の権威行**以外**に slug 無し
- `DW-O01` **外**の `operations.md` に slug 無し
- `workers.md` 全体 (見出し含む) に slug 無し
- `.claude/commands/dev-wave.md` に slug 無し

検出正規表現は `gpt-<数字>` 系一般を拾う。`gpt-5.4-mini` や `gpt-6-*` のような
別 family での迂回も塞ぐ。

## byte 予算 — 設計を 2 度変えさせた制約

`docs/dev-wave/` 4 file の合計上限は 25,200 bytes で、wave 開始時の余裕は **4 bytes** だった。
model 名を 1 つ足すだけで超える。上限引き上げと安全義務 prose の削除は禁じ手である
(`check_docs.py` 冒頭が手段目的の逆転を明示的に禁じている)。

当初は dispatcher (`.claude/commands/dev-wave.md`、別予算) へ権威を置いた。しかし wave 途中で
local main を取り込んだところ、**別 wave が同 file を 9,457 / 9,500 まで使っていた** (その wave も
「本文編集は予算不足で裁定へ返す」としている)。そこで権威を `DW-O01` へ移した。
結果的にこれはレビュー R2 の BLOCKER (権威が起動直前の必読集合に無い) を同時に閉じた。

reference 側の byte は、`DW-S02` の「read-only 固有のテスト帰属は `DW-O05` に従う。」1 文を
外して捻出した。同義務は段 2 preflight の dispatch 表 (`check_docs.py` の
`_pairs(_OPERATIONS, ..., "DW-O05")` で機械強制) と条件 05 で二重に保証されており、
prose を外しても義務は失われない。

最終: dev-wave reference **25,180 / 25,200**、dispatcher **9,457 / 9,500**。

## 実測 (すべて親、計算ノード)

| 項目 | 値 |
|---|---|
| 段 1 生死確認 | `codex exec -m gpt-5.6-luna -c model_reasoning_effort="max" -s read-only` = rc 0、CLI reported 13,017 token |
| `tools/check_docs.py` | 違反なし |
| `orchestrator/tests/test_check_docs.py` | 325 passed |
| 受入全走 1 回目 (実装 tip `03f1487b`) | **7373 passed / 20 skipped** (1174.40s、job `895950.nqsv`) |
| 受入全走 2 回目 (`dd17b571`) | 7372 passed / **1 failed** / 20 skipped (1161.74s、job `895953.nqsv`) — 赤はフレーク (下記) |
| フレークの単独再走 | `test_codex_worker_launch.py` = 64 passed (再現せず) |
| 受入全走 3 回目 (**land 対象 tip** `9a99fede`) | **7373 passed / 20 skipped・赤ゼロ** (1210.04s、job `895995.nqsv`) |
| 変異 spec1 | 6 件中 5 KILLED / 1 MISMATCH (M5)、SURVIVED 0 |
| 変異 spec2 | M7 KILLED (期待 2 node と完全一致)、SURVIVED 0 |
| `tools/check_ai_provenance.py` | 新規違反なし |

## この pin が保証しないこと

- **実際の起動 model を縛らない。** pin は文書契約だけを守る。`-m` の実引数を権威行と
  機械照合する層は存在しない。
- **served model を attest できない** (F56)。receipt の model は要求 slug の echo である。
  記録できるのは `requested_model` までで、`served_model` は unknown である。
- 本 wave 自身の段 2 / 3 / 5 / 6 は**すべて `gpt-5.6-sol`** で走った (混成契約が未 land のため)。
  本 wave の敵対所見を luna の成果として読んではならない。

## 段 3 / 段 6 レビューの規模

| 段 | レンズ | 結果 |
|---|---|---|
| 段 3 敵対相談 | A = 整合・実効性、B = 正しさ境界 | BLOCKER 3 + 4、両者 NO-GO、refuted 0 |
| 段 6 敵対レビュー | R1 = pin の実効性、R2 = 裁定準拠・受理集合 | BLOCKER 4 + 5、両者 NO-GO、refuted 0 |

fix は 3 巡 (`s6fix` = pin 強化、`s6fix2` = 権威の `DW-O01` 移設、`s6fix3` = 冗長 gate の期待値修正)。

## rollback (policy-only)

`DW-O01` の権威行を `` `<model>`: 全段 `gpt-5.6-sol`。 `` へ戻し、`check_docs.py` の
権威 literal 定数を同じ文字列へ更新し、`orchestrator/tests/test_check_docs.py` の
`_build_min_repo()` fixture と権威系 negative を追随させ、`check_docs` と当該テストを再走する。
**射程は将来の規範 model だけである。** 既に luna 名義で行ったレビュー、そこから派生した裁定・
実装・成果物は戻らない。canonical 台帳は append-only なので、取り消しは後続 decision の
supersede で表現する。発火条件は (a) 段 3 の見落としに起因する欠陥が land した実例が出たとき、
(b) [T-189] の妥当な A/B が非劣性を否定したとき、(c) ユーザーの指示。
