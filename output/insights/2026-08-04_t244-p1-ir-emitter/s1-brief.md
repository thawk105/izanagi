# 段 1 brief — [T-244] D121 P1: 固定 5-bit IR と全 32 mask 監査済み emitter

## scope (ユーザー command 引数で確定)

T-244 本体のうち **D121 決定 (7) の前提条件 P1 だけ**を、**新規 leaf に閉じて**実装する。
P3 (origin ledger) と P5 (provider/session/token) の面には触らない (P3 は並行 wave
`wave-t244-p3-origin-ledger` が所有)。

**作るもの:** ① 新規 leaf `orchestrator/campaign/reflux_ir.py` — 固定 5-bit IR の値型・
正準 wire 形の parser (非正準入力は全拒否)・正準 emitter (mask → C++ 述語 1 行)。
② 独立 golden 台帳 `orchestrator/tests/reflux_ir_expected_goldens.py` (D82 / `s1_expected_goldens.py`
と同型 — production から import せず、実行時導出もしない)。③ テスト
`orchestrator/tests/test_reflux_ir.py`。④ spool fragment (worklog / decisions) と insights 逐語。

**触らないもの:** `axis_trigger_gating.py`、`s8a_trigger_sweep.py` (どちらも sha256 が
freeze に pin 済み)、既存 loop の受理経路 (**wiring しない**)、P3 / P5 の面。

## 確定済みユーザー裁定

- D121 決定 (1) 軸 (i) 主軸 + (iv) 併用、決定 (3) 強制と開示の分離、決定 (4) exact-mask no-good cut、
  決定 (7) 前提条件 10 件と P1 の定義
- worklog (153) の U1〜U5 (U2 = 「実装が無いゆえの非適用」は FAIL とする改訂は別 wave 所有)
- 本 wave の射程はユーザー引数そのもの

## 段 1 前提実測 (実施済み)

| # | 測ったこと | 結果 |
|---|---|---|
| A | `axis_trigger_gating.py` の bytes pin | sha256 `47507d9b…c04c` が `known_axes_freeze.json` / `measurement_freeze.json` に一致 → **no-touch** |
| B | 既存の独立 emitter の実在 | `s8a_trigger_sweep.py:215 predicate_for()` が 2026-07-11 に本 leaf と独立に書かれている |
| C | 凍結 anchor の被覆 | freeze の `gate_predicate` 6 record が `predicate_for` と **byte 一致**。相異なる mask は 3 点 (4=g_rt, 8=g_rl, 31=ident_all) |
| D | campaign 記録の被覆 | provenance の `implementation` が **9/32 mask** を覆う (0,1,4,5,8,9,12,13,31)。残 23 点は artifact 無し |
| E | 32 mask の相異性 | 述語文字列は **32/32 が相異なる** (正準性の必要条件が成立) |
| F | 既存 gate との整合 | 32 mask 全部が `check_syntax_contract` を通り、全て 1 物理行・末尾空白なし |
| G | 新規 leaf 追加の副作用 | stub を実編集で置いて `test_s8b_repo_scan_invariant` + `test_frozen_artifacts` = **3 passed**、stub 削除で clean 復元 (DW-O19) |
| H | 受入環境 | pegasus02 (login) から `run_tests.py` が gen_S へ同期 dispatch (request `883125.nqsv`、20 秒) |

## 純増検出力 (既存被覆との差、DW-S01)

既存 `test_s8a_trigger_sweep.py` は **EFF3 = 3 要因 (8 点) の構造検査だけ**で、byte-literal golden を
持たない。`s1_expected_goldens.py` は 3 mask の述語 literal を持つが、**freeze 文書の検査**であって
emitter と照合したことは一度もない。純増は次の 4 点である。

1. **32 mask 全点の byte-literal golden** (現状 0 点)
2. **既存独立実装 `predicate_for` との全 32 点 差分照合** (現状なし)
3. **IR parser の拒否面** (現状ゼロ — production parser は任意 1 行 C++ を受理する)
4. **round-trip 恒等** emit → parse → mask (現状なし)

## 不変条件

- `axis_trigger_gating.py` / `s8a_trigger_sweep.py` の bytes を変えない
- **既存の受理集合を変えない** → D96 手続の対象外 (一次対象は `s8b_selector_output.py`)。
  将来 production を IR へ閉じる wiring は受理集合の縮小であり、その時点で D96 が要る旨を記録する
- 独立 golden を production から実行時に導出しない (導出すると恒真、P1 の警告そのもの)
- **「P1 を満たした」と名乗らない。** 本 wave は P1 の機械部品だけであり、候補表現の閉包は未実施

## 親の provisional 裁定 (攻撃対象)

- **(P1)** 正準 wire 形 = `GATEABLE_REASONS` 定義順 LSB-first の **長さ 5 の '0'/'1' 文字列**。
  空白・符号・prefix・大文字・長さ違い・int・JSON は全拒否 (順序と空白の side channel を消す)
- **(P2)** leaf は `predicate_for` を**呼ばず独自実装**する。テストで全 32 点を差分照合する
  (呼ぶと独立性が消え、pin 済みファイルへの依存も増える)
- **(P3)** 独立 golden = 32 行の literal 表。凍結 freeze (3 mask) と campaign provenance (9 mask) を
  上位 anchor として重ね、どの層が何点を覆うかをテストに明記する
- **(P4)** 「監査済み」の主張範囲 = 「32 mask すべてで literal golden と既存独立実装に byte 一致、
  うち 9 点は記録済み artifact、うち 3 点は凍結 bytes にも一致」まで。これを超えて主張しない

## 成果物影響 (DW-G05)

- **実装しない場合:** D121 P1 は未充足のまま。U2 裁定 (「実装が無いゆえの非適用」= FAIL) により
  cap-lift は FAIL 固定で、D114 の上限 1 が解除できない → 8c 正式系列 H1/H2 (複数世代) が走れず、
  certified 選択の材料が 1 世代分に留まる。台帳側は decisions D121 決定 (7) の P1 行が未充足のまま
- **誤って実装した場合:** emitter が 1 mask でも別 bytes を出すと、提案 mask と build される variant が
  食い違い fitness の帰属が汚染される (D39 決定 7 と同型) → certified 選択の値が誤る
- **恒真な監査を書いた場合:** 「32 mask 監査済み」が台帳に載り、将来の cap-lift 裁定が偽の
  前提充足を根拠にする。これは謳うだけで発火しない保証 (規律 6 の監査発火条件) そのもの

## 敵対検証子の要否 (DW-C00)

**省かない。** 本 wave の中心成果は「正しさ防壁の部品」と「その監査が恒真でないこと」の主張であり、
台帳へ載る主張が将来の cap-lift 裁定の入力になる。設計択一も割れる (wire 形・独立性の担保法・
「監査済み」の射程)。よって段 2・3 と段 6 の review 子を置く。

## 並列分割方針

leaf・golden 台帳・テストは相互依存するため **実装は単一所有 (codex author 1 本)**。
段 3 の敵対相談と段 6 のレビューは **2 レンズ並列**。
