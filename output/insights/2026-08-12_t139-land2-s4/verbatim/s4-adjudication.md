# 段 4 裁定 — [T-139] land 2 session 4

親が段 2 プランと段 3 の 2 レンズの所見を real / refuted、採用 / 不採用、scope 内 / 外に裁定する。

## 裁定の核 — 本 wave は Q4 scope を**実装しない**。新事実つきでユーザー再裁定へ返す。

`DW-S04` は「承認済み裁定を止めてよいのは裁定時点で未見の新事実がある場合だけ」とし、
「止めるときも親が不採用にせず、新事実付きのユーザー再裁定待ちへ戻す」と定める。
下記 N1〜N3 はいずれも Q4 裁定 (2026-08-12 12:38) の時点で**どの控えにも記録が無かった**事実であり、
Q4 の scope をそのまま実装すると Q1/Q2 または絶対規律 2 に抵触する。

**ただし本 wave は land する。** Q4 の禁止は「**解除 decision だけを先に land しない**」であって、
「解除 decision を含まない land をしない」ではない。解除 decision と投入経路を**両方とも**
land しなければ、D308 が警告する「止める文が canonical に無く、通す gate も未実装」の窓は開かない。
現土台 (session 1・2 の実装) と記録・裁定パッケージだけを land する。

## 未見の新事実 (N1〜N3)

### N1 — 束縛検査が**恒真**になる (段 2・段 3 の 3 子が独立に到達)

`a12` (weak null の型 I 誤りを較正する事前 simulation) は **pilot 1 本目の投入より前に完走**を
要求し、未完了なら `design_not_feasible` である (追補 A `a12`、逐語)。実装も実行結果も 0 件。
したがって `submit_pilot` の受理集合は**空**であり、次の 4 実装が同じ観測結果になる。

1. canonical release が無いので拒否する正しい実装
2. `a09` / `a12` が無いので拒否する正しい実装
3. binding を一度も検査せず常に拒否する実装
4. どの入力も読まず `raise` する実装

**帰結:** 負例テスト (`missing_a09` / `missing_a12` / duplicate marker / direct qsub) は
検査が発火した証拠にならない。「束縛検査を land した」と書けない。
D292 の理由欄が禁じた「未実装・未検証の gate の合格条件を凍結し、実装が条件に合わないとき
**条件側を緩める圧力**が生まれる」形そのものである。

**親の判断:** これは規律 2 の面である。恒真な防壁を「機械執行した」と記録することは、
正しさシグナルの後付け (規律 3) にも当たる。**採用 = real、本 wave では実装しない。**

なお `a12` の**合格条件自体は承認済み文書で完全に固定されている** (固定入力の実在と digest 一致を
親が実測。`throughput.tsv` sha256 = `755cfa7e…` 一致、`α₁ = 0.025`、B = 1,000,000 × 60 セル、
seed、counter-mode PRNG、判定式 `U_{Jk} ≤ α₁`)。よって「中身を見ずに凍結」ではない。
**閂は条件の未確定ではなく、正例を作る計算が未実行であること**である。
その計算は約 60 億 draw 規模で、それ自体が計算ノード job 1 本分であり Q4 の scope に入らない。

### N2 — Q4 の scope と Q1/Q2 の見送りが**内部で衝突する** (レンズ A が発見、親が追認)

PBS driver は `a09` の schedule を消費し、intent / binding / collector record はその
`schedule_sha256` を持つ。しかし —

- 追補 A `a09` が凍結しているのは**意味的な導出規則まで** (逐語 seed
  `7df15572…`、`key(j, w, p)` の式、preimage の byte grammar、tie-break)。
- **canonical TSV・header・157 行・並び順という serialization は `record-items-v2.md` §10 の
  「承認済み文書から一意には導けない閉包」8 件のうちの第 4 番**である。

したがって driver が canonical schedule digest を名乗るには**閉包 4 を採用する必要があり**、
それは Q1/Q2 が「機構を新設しない」と見送った当の対象である。
採用しなければ、同じ意味的 schedule から実装依存の異なる digest が出る。

**親の判断:** real。**親が一存で解けない** — Q4 と Q1/Q2 のどちらを優先するかはユーザーの
裁定事項である。裁定パッケージ R2 として返す。

### N3 — `collector` の実行 site が現行規律下で不成立 (レンズ A)

段 2 は collector を「login-side のみ」と置くが、Pegasus では `tools/pegasus/` の未登録実行体を
login node で拒否し、`local-ok` の新設には実測が要る (`docs/pegasus-runbook.md`)。
既存 collector も `unknown` / `compute-only` である。

**親の判断:** real。scope 内で解けるが、N1・N2 が閉じるまで着手しても捨てになる。

## 所見の裁定表

| # | 出所 | 所見 | 裁定 |
|---|---|---|---|
| 1 | plan B1 / sol 1 / luna B1・B5 | `a12` 不在で受理集合が空・束縛検査が恒真 | **real・採用**。N1 |
| 2 | sol 4 / sol B2 | canonical TSV 157 行は未承認閉包 4。親の実測 F5 は半分誤り | **real・採用**。N2。**親の F5 を訂正** |
| 3 | plan B3 / luna B3 | (P5) の「粗い provenance は既に認められた」は根拠なし | **real・採用**。**(P5) を撤回** |
| 4 | plan B4 / sol 9 / luna | (P4)(iii)「投入は `submit_pilot` 経由でしか起こせない」は機械保証できない | **real・採用**。保証境界は「直接 qsub された job は driver preflight を越えず、valid run record・試行台帳・材料 report・certified 選択へ一切昇格しない」まで。**(P4)(iii) を訂正** |
| 5 | sol 2 / N3 | 実務経路の全層 (submit CLI・admission・collector 実行 site) が scope から落ちている | **real・採用**。N3 |
| 6 | luna B7 | D308 の同一 land を執行する機械検査が無く、願望のまま | **real・採用**。裁定パッケージ R4 |
| 7 | luna B6 | release marker の exact grammar・PATH shadow・HEAD race・dirty worktree bytes が未閉鎖 | **real・採用**。実装時の必須要件として R1 へ添付 |
| 8 | luna B8 | qsub 後 crash / retry の状態機械が未確定。`submission.py:150` は単発 `os.write` で short-write 検査なし | **real**。`submission.py` の short-write は **T-126 側の既存欠陥**であり本 wave の scope 外。裁定パッケージ R5 で別タスク起票を推奨 |
| 9 | sol 3 | 「`a09` の独立再導出そのものが新機構」は誤り | **refuted**。ただし serialization は別 (所見 2) |
| 10 | sol 5 | 「3 成果物に値が入らないなら land 価値ゼロ」は誤り | **refuted**。(P1) は維持 |
| 11 | sol 7 / luna | 現時点で D291 report が二重権威になっている | **refuted** (production consumer 0 件) |
| 12 | sol 8 / luna B9 | `report_scope` の additive 追加は Q4 外の拡張で、誤読を機械的に防がない | **real・不採用 (実装しない)**。Q4 が名指していない層への拡張 |
| 13 | luna | `preregistration` docstring の `submit_pilot` が現行 bypass だという主張 | **refuted** (export 禁止テストが実在) |

## 訂正 (親 brief の誤り。worklog へ記録する)

- **(P5) を撤回。** `{{D:coarse-provenance-standard}}` は canonical `docs/decisions.md` に存在せず
  (親が段 1 で grep 実測して brief にそう書きながら)、同じ brief でそれを「既に認めた」根拠に使った。
  自己矛盾である。
- **段 3 へ渡した実測 F5 を訂正。** 「`a09` の schedule は承認済み文書で完全に凍結されている」は
  **導出規則については真、serialization については偽**。§10 閉包 4 が反例である。
  一般化「独立再導出は承認済み仕様の実装であって新設ではない」は導出規則に限って成立する。
- **(P4)(iii) を訂正。** 上記所見 4 の保証境界へ書き換える。

## 本 wave の scope (確定)

**実装面の差分 = 0。** 段 5・段 6 を飛ばし `4 → 7 → 8 → 9` とする。

land する内容:

1. **session 1・2 の実装** (`erratum.py` / `blobref.py` / `approval_payload.py` /
   `addendum_envelope.py` / Git trust root 部分集合 + test 3 file) — 既に branch 上にあり、
   s2 の受入で緑だったもの。本 session が現 main の上で受入全走を再走して certify する。
2. **記録** — worklog fragment (訂正 3 件を含む)、failures fragment、insights (逐語 + 裁定パッケージ)。
3. **裁定パッケージ R1〜R5** (下記)。
4. 未 land の先行 fragment 7 件 (w1 decisions 1 / w1 worklog 1 / land2 worklog 1 + failures 1 /
   land2-s2 worklog 1 + failures 1 / land2-s3 worklog 1 + failures 1) + 本 session 分。

land **しない**内容: 解除 decision、`submit_pilot`、PBS driver、collector、束縛検査、
`report_scope` の additive field。

## 変異事前登録 (`DW-M01`)

**免除。** `DW-S04` の免除条件「『実装しない』裁定済みかつ実装差分ゼロの wave の変異 matrix」に
該当する (D301 の連言)。**受入全走は免除しない** — 実 repo を読むテストがあるため、
記録 commit を含む最終 tip で実走し、結果を worklog へ書く。

## 裁定パッケージ (ユーザーへ返す。R1〜R5)

- **R1 — `a12` を誰がいつ実装・実走するか。** Q4 の「投入の実務経路」に `a12` producer・
  独立 verifier・実 pass artifact まで含むか。含まないなら、正例が構成できないため
  Q4 scope の束縛検査は land できない (N1)。
  親推奨 = **`a12` を独立の 1 wave として先に立てる** (計算ノード job 1 本分の規模であり、
  投入経路と同じ session に入れると両方が半端になる)。
- **R2 — `a09` の canonical serialization (§10 閉包 4) を採るか。** 採れば Q1/Q2 の
  「機構を新設しない」と衝突し、採らなければ driver は実装依存の digest しか出せない (N2)。
  親推奨 = **本 wave では判断しない。R1 の `a12` wave で `a09` の意味的 generator だけを先に作り、
  serialization は `operational-only` と明記して canonical `schedule_sha256` を名乗らない。**
- **R3 — 恒真な防壁を land してよいか。** 「受理集合が空の gate を、正例が作れるようになるまで
  先に land する」ことを認めるか。親推奨 = **認めない** (N1、D292 の理由欄と規律 2)。
- **R4 — D308 の同一 land を機械が執行するか。** 現状は規律であって検査が無い (所見 6)。
  親推奨 = **[T-508] の機械化移管枠 (Q5 の裁定) で扱う。** 本 wave では新設しない。
- **R5 — `orchestrator/qualification/submission.py:150` の単発 `os.write`** (short-write 検査なし、
  read-back なし) は T-126 側の既存欠陥である (所見 8)。親推奨 = **別タスクとして起票**。
  本 wave の scope 外。

## 次 session への引き渡し

R1〜R5 の裁定が出るまで、投入経路の実装は着手できない。R1 (a12) が最も上流である。
