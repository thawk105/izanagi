# [T-1048] 段 4 裁定 — plan v2 と変異事前登録

2026-08-13 19:04 JST。段 3 の 2 レンズ (sol = 過剰拒否と層の取り残し、luna = 迂回経路) の所見を裁定する。
逐語 = `verbatim/consult-a2.md`、`verbatim/consult-b.md`、`verbatim/plan.md`。

## 0. 裁定 inbox の再走査 (DW-S04)

wave 開始 (17:15) 後に増えた控えは `2026-08-13-t244-8c-multigeneration-human-loop-parity.md` (18:00 裁定) の
1 件。`2026-08-13-rulings11-12rulings.md` (16:56) と併せて **本 wave に関係する項はゼロ**。巻き戻しなし。

## 1. 所見の裁定

| # | 所見 | 判定 | 採否 |
|---|---|---|---|
| A2-1 | `axis_trigger_gating.py` が凍結 JSON 3 本から source SHA で間接 pin されている | **real** | 事実は採用、must-fix は**却下** (下記 1.1) |
| B-1 | prologue の型差し替えで block/epilogue を逐語一致させたまま gate を常時 false にできる | **real** | **scope 外** — 起票 (下記 1.2) |
| A2-2 | 宣言と BEGIN の間へ `return;` を挿入すると hole も gated call も実行されない | **real** | **scope 外** — 起票 |
| A2-3 | epilogue 直後へ `#if ... else { backoff(); } #endif` を置くと、preprocess 後に `if...else` が結合して常時 backoff になる | **real** | **scope 外** — 起票。**「R2 を閉じた」の記載方法を変える根拠として採用** |
| B-6 | brief の「S8b / S-1 extime は quarantine 非経由」は誤り | **real** | **採用** — 純増検出力を訂正 (下記 1.3) |
| A2-6 | deleted/modified/gap は 1 つの gate への異なる入力にすぎず、独立変異にならない | **real** | **採用 (must-fix)** — 変異登録を 1 件へ集約 |
| B-5 | 既存 frame/hole 負例を新検査の kill 証拠にしてはいけない | **real** | **採用** — canonical block + bad epilogue を直接渡す case を登録 |
| B-7 / A2-7 | `END + E + E` の直結重複拒否 | **real (両者一致で nit)** | **不採用 — 検査を落とす** (下記 1.4) |
| B-3 | `FileNotFoundError` の早期 return が新検査を迂回する | **real** | **scope 外** — 起票 |
| B-4 / A2-4 | 非認証 diagnostic build と S8b resume は admission 外 | **real** | **scope 外** — [T-1050] で起票済み。重複起票しない |
| A2-5 | 現行 producer に byte 過剰拒否は再現しなかった | **real** | **採用 (nit)** — 正例の固定方針に反映 |
| B-2 / A2-2 | P1 の一般化が未記載前提に依存 | **real** | **採用** — P1 の根拠を差し替える |

### 1.1 A2-1 (凍結 JSON の間接 pin) — 事実は採用、編集場所の変更は却下

**実測 (親):** `output/s1-freeze/known_axes_freeze.json:46`、`output/s1-freeze/measurement_freeze.json:41`、
`output/s8b-freeze/holdout_freeze.json` が `orchestrator/campaign/axis_trigger_gating.py` の sha256 を
`47507d9b936efeaa463f839a59d5afd7c2a7a8d36427a46ad61579bf4b50c04c` として pin している。
現行実測値は `72371560f750fa5712e3da9aeeeb9699e5a3dbb187a6617539e1dff979155b09` で、
**本 wave の着手前 (main 48b2caab) から既に不一致**である。`s1_known_axes_freeze.verify_document:854-857`
が不一致を `FreezeError` にする。

**裁定:** 定数の置き場所は `axis_trigger_gating.py` のままとする。理由は 2 つ。

1. 既存の凍結チェーン検証 (実装 bytes 完全一致を含む) は**ユーザー裁定で保留中**であり
   (`freeze-verification-hold`、2026-08-12 rulings 第 4 束)、対象外と明記されているのは
   正しさゲート・規律 1・防壁の自己完全性である。本 wave が足すのは正しさゲート側で、
   保留対象は pin 照合の側である。
2. D48 は軸定数の正本を `axis_trigger_gating.py` 1 本と定めている。admission 側へ逃がすと
   軸定数の正本が二分され、D48 必須条件 5 に反する。

**同時に守る制約:** **凍結 JSON を再 pin しない** (同裁定の「凍結 bytes は書き換えない」)。
本 wave は既存の不一致を不一致のまま維持し、新たな赤を作らない。受入全走で確認する。
既存不一致そのものは起票する。

### 1.2 B-1 / A2-2 / A2-3 (gate 意味論の迂回) — scope 外・起票

3 件はいずれも「凍結領域を広げても gate の**意味論**は固定できない」ことの実証である。
ユーザーの scope は「post-END の `if (izanagi_gate_pass)` まで」と明示され、かつ
「scope 外の発見は worklog の次の一手へ起票し、本 wave の差分へ帰属させない」と指示されている。
したがって**実装しない**。ただし記録義務を負う:

- R2 の閉鎖主張は **「END 行末と gated call の間での `izanagi_gate_pass` 再代入」に限定して書く。**
  「R2 を閉じた」と無限定に書かない。
- 残存限界として R1・R3 に加えて次を明記する。
  - **R4**: prologue での `izanagi_gate_pass` の再宣言 (型差し替えによる代入・真理値の無効化)。
  - **R5**: 宣言と BEGIN の間の制御流変更 (`return;` 等) による hole/gated call の非到達化。
  - **R6**: epilogue 直後への dangling `else` 付加による常時 backoff 化。

### 1.3 B-6 (純増検出力の訂正)

brief の「S8b oracle / floor / S-1 extime calibration は quarantine 非経由」は**誤りだった**。
親の実測: `s1_verify_extime_calibration.py:341-347` と `s1_direct_comparison.py:593-602`
(`prepare_cell`、S8b floor / oracle が共有) はいずれも `p3_s4_loop.quarantine` を呼び
`passed` を検査する。

**訂正後の純増検出力:** build gateway が、quarantine の実行有無と独立に、**compiler が読む直前の
source そのもの**に対して epilogue の逐語隣接を要求するようになる。quarantine が覆わないのは
(i) 実装文字列を挿入しない pristine / characterization 経路、(ii) diff の baseline 側に既に
混入している改変、の 2 つで、純増はこの 2 つに限る。**quarantine も admission も通らない
非認証 build は純増の対象外**である (そこは元から admission 外)。

### 1.4 B-7 / A2-7 (E+E 直結重複拒否) — 落とす

sol は「限定を明記して採用」、luna は「落とすか明記」で、**両者とも nit と評価**した。親は落とす。

- DW-G05 の成果物影響が書けない。`E + E` が生む「backoff 二重実行」は、**受理する**
  `E + #if ... else { backoff(); } #endif` (A2-3) や `E + 無条件 backoff` (B-7) と同じ結果であり、
  片方だけを拒否する理由を成果物の値の差として書けない。DW-G05 は「書けない must-fix は nit/backlog」とする。
- 受理言語を最小に保つ方が記録が正直になる。落としたうえで、受理言語に
  **「epilogue より後の bytes は凍結しない」を明示**する。

## 2. provisional 裁定 (P1)〜(P5) の確定

| 裁定 | 確定 | 根拠の変更 |
|---|---|---|
| P1 凍結は epilogue 側だけ | **採用。ただし根拠を差し替える** | 旧根拠「hole が無条件代入だから prologue 凍結は不要」は B-1 / A2-2 により **refuted**。新根拠は「ユーザー裁定の scope が post-END までであり、prologue 側は R4/R5 として起票する」 |
| P2 exact adjacency | **採用** | 両レンズ一致。`ends[0].end()` を唯一の開始位置にする |
| P3 三分岐の維持 | **採用** | stock/non-trigger を新たに止めない。ENOENT 早期 return の是非は起票 (B-3) |
| P4 後続空行を凍結しない | **採用。ただし「これで R2 が閉じる」という根拠は撤回** | A2-3 の dangling else により、`#endif` までの凍結は意味論を閉じない |
| P5 R1 を閉じない | **採用** | 残存限界を R4/R5/R6 まで拡張して記録する |

## 3. plan v2 (段 2 プランからの差分)

段 2 プランを次の 5 点だけ変更し、他は全採用する。

1. **`E + E` 直結重複検査を削除する** (1.4)。負例 `duplicated-adjacent` も登録しない。
2. 受理言語に **「epilogue より後の bytes は凍結しない」** を明記する。
3. `_require_materialized_trigger_axis_predicate` の docstring の残存限界へ **R4 / R5 / R6 を追加**する。
4. 変異は下記 §4 の 3 件に集約する (A2-6 / B-5)。
5. **凍結 JSON (`known_axes_freeze.json` 等) を一切変更しない。**

### gate の禁止 (署名) と通る正例 (DW-S04)

```
禁止: raw[ends[0].end() : ends[0].end() + len(FROZEN_TEMPLATE_EPILOGUE_BYTES)]
        != FROZEN_TEMPLATE_EPILOGUE_BYTES   ->  BuildAdmissionError

通る正例: FROZEN_TEMPLATE_BLOCK_BYTES + FROZEN_TEMPLATE_EPILOGUE_BYTES
          + b"\n#if ADD_ANALYSIS\n"          ->  受理
```

## 4. 変異事前登録 (DW-M01)

| ID | 層 | 変異 | 期待 | 単一理由性の確認 |
|---|---|---|---|---|
| MUT-1 | negative | `build_admission.py` の epilogue 隣接検査を削除する | canonical pristine block + 改変 epilogue の拒否テストが赤 | 入力の block は pristine なので `block == FROZEN_TEMPLATE_BLOCK_BYTES` の早期 return (現行 `build_admission.py:189-190`) に当たり、**他のどの層も拒否しない**。コードで確認済み |
| MUT-2 | positive (過剰拒否検出) | epilogue 検査を `raw[start:] != E` (末尾まで完全一致要求) へ**強める** | 「E の後の空行と `#if ADD_ANALYSIS` を受理する」正例テストが赤 | 受理集合を縮小する wave の必須正例 (DW-M01)。この入力を止める層は他に無い |
| MUT-3 | negative | `FROZEN_TEMPLATE_EPILOGUE_BYTES` を patch と食い違う逐語値へ差し替える | patch 整合テスト (`test_frozen_trigger_epilogue_matches_template_patch_bytes`) が赤。**期待 node の完全集合は fix 後に再導出する** (定数は受理判定にも使われるため複数 node が同時に赤くなる) | 定数の正本性を守る唯一の層。patch 側は不変条件で触らない |

### 4.1 段 6 レビュー B による期待 node の是正 (2026-08-13 19:4x JST 追記)

段 6 レンズ B が「MUT-1 は 3 node、MUT-2 は `test_build_admission.py` 内だけで**少なくとも** 37 node を
赤にする。単数の期待では DW-M08 の完全集合一致を満たさず `MISMATCH` になる」を must-fix で出した。
**採用する。** ただし「少なくとも」という留保が付く以上、静的列挙は完全集合の根拠にならない。
DW-M08 が明示的に許す probe 経路を採る — **1 巡目を probe と明記して回し、実測した失敗 node の
完全集合で再登録して本走する。** runner 範囲は `orchestrator/tests/test_build_admission.py` に固定し、
範囲と期待集合を対にする。1 巡目の生 ledger は erratum として残す。

**登録しないもの** (DW-M01 の単一理由性を満たさないため):

- BEGIN/END の順序検査 arm (後段の frame 比較が同じ入力を拒否する。T-897 の M4-prime と同型)。
- `deleted` / `modified` / `gap-before` を別々の変異として数えること
  (いずれも MUT-1 が消す同一分岐への異なる入力である。**負例テストとしては 3 入力とも持つ**)。

## 5. 起票 (worklog の次の一手へ。本 wave の差分へ帰属させない)

1. **trigger 骨格の prologue 再宣言 (R4) と BEGIN 前制御流 (R5)** — 凍結領域を宣言側へも広げるか。
   実証差分は `verbatim/consult-b.md` 所見 1、`verbatim/consult-a2.md` 所見 2。
2. **post-epilogue の dangling `else` (R6)** — 骨格に構文的 terminator を足す案は patch 不変条件と
   衝突するため、patch migration を伴う設計裁定が要る。実証差分は `verbatim/consult-a2.md` 所見 3。
3. **`axis_trigger_gating.py` の凍結 JSON 間接 pin が wave 前から不一致** — 凍結チェーン検証の
   保留裁定との関係を整理する (再 pin はしない)。
4. **admission の `FileNotFoundError` 早期 return** — axis 対象の ENOENT を拒否へ倒すか。
   過剰拒否の危険があるため単独裁定が要る。

[T-1050] (S8b binary ↔ admission receipt) は既に起票済みのため重複起票しない。
