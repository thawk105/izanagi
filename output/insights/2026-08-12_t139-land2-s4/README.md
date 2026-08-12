# 2026-08-12 [T-139] land 2 session 4 — Q4 scope が Q1/Q2 と衝突すると実測し、実装ゼロで land した

wave `dev-wave-t139-manifest-land2-s4` / branch `worktree-dev-wave-t139-manifest-w2`。
**実装面差分ゼロ。ただし land した** (Q6 (a) により本 session が最終)。

## この session が何をしたか

指示は 2026-08-12 第 2 束の裁定 Q4 —「投入の実務経路 (`submit_pilot`・PBS driver・collector)
+ D292 を上書きする解除 decision + 束縛検査だけを 1 session・同一 land で組む」— の実行だった。

段 2 のプラン起草と段 3 の敵対 2 レンズが**独立に NO-GO** を返し、親は段 4 で
**Q4 scope を実装しない**と裁定した。根拠は裁定時点で未見だった事実 3 件 (N1〜N3) である。

**land はした。** Q4 の禁止は「解除 decision **だけ**を先に land しない」であり、
解除 decision と投入経路の**双方を land しない**選択は、D308 が警告する
「止める文が canonical に無く、通す gate も未実装」の窓を開かない。
session 1・2 の緑の土台と記録・裁定パッケージが main へ入った。

| file | 内容 |
|---|---|
| `verbatim/s1-brief.md` | 段 1 brief — 実測 8 件、不変条件、provisional 裁定 (P1)〜(P6)。**(P5) と F5 は後に誤りと判明** |
| `verbatim/s2-plan.md` | 段 2 プラン起草 (codex, reasoning=max) — **NO-GO**、blocker B1〜B4 |
| `verbatim/s3-sol.md` | 段 3 レンズ A「scope の空洞化と孤児 gate」— **NO-GO**、blocker B1〜B5 |
| `verbatim/s3-luna.md` | 段 3 レンズ B「正しさ防壁の回避経路」— **NO-GO**、blocker B1〜B9 |
| `verbatim/s4-adjudication.md` | 段 4 裁定 — real/refuted 13 件、訂正 3 件、裁定パッケージ R1〜R5 |
| `package.md` | 裁定パッケージ R1〜R5 (ユーザー手番) |

## 中核の発見 — 束縛検査が恒真になる (3 子が独立に到達)

`a12` (weak null の型 I 誤りを較正する事前 simulation) は **pilot 1 本目の投入より前に完走**を
要求する (追補 A `a12`)。実装も実行結果も 0 件。したがって `submit_pilot` の受理集合は**空**で、
次の 4 実装が観測上まったく区別できない。

1. canonical release が無いので拒否する正しい実装
2. `a09` / `a12` が無いので拒否する正しい実装
3. binding を一度も検査せず常に拒否する実装
4. どの入力も読まず `raise` する実装

負例テストは検査が発火した証拠にならない。これは D292 の理由欄が禁じた
「未実装・未検証の gate の合格条件を凍結し、実装が条件に合わないとき**条件側を緩める圧力**が
生まれる」形そのものであり、絶対規律 2 の面である。

**`a12` の合格条件自体は承認済み文書で完全に固定されている** (親が実測: 固定入力
`output/env/pegasus/t139-positive-control-probe/0_892042.nqsv/throughput.tsv` は実在し
sha256 = `755cfa7ea7c22ac763f404769103fd2ff0c49763c79369ac826db6a32b71c4f2` が仕様と一致、
`α₁ = 0.025`、B = 1,000,000 × 60 セル、seed、counter-mode PRNG、判定式 `U_{Jk} ≤ α₁`)。
**閂は条件の未確定ではなく、正例を作る計算が未実行であること**である。
その計算は約 60 億 draw 規模で、それ自体が計算ノード job 1 本分である。

## Q4 と Q1/Q2 の内部衝突 (N2)

PBS driver は `a09` の schedule を消費し、intent / binding / collector record がその
`schedule_sha256` を持つ。しかし承認範囲は**節の粒度で割れている**。

| 対象 | 承認状態 |
|---|---|
| `a09` の**導出規則** (逐語 seed `7df15572…`、`key(j, w, p)` の式、preimage の byte grammar、tie-break) | 追補 A で**承認済み** |
| schedule 表の**serialization** (canonical TSV・header・157 行・並び順) | `record-items-v2.md` §10 の**未承認閉包 第 4 番** |

driver が canonical schedule digest を名乗るには閉包 4 の採用が要り、それは Q1/Q2 が
「機構を新設しない」と見送った当の対象である。採用しなければ、同じ意味的 schedule から
実装依存の異なる digest が出る。**親が一存で解けない設計択一**であり R2 として返した。

## 親 brief の誤り 3 件 (本 README が正本)

1. **(P5) を撤回。** 「粗い provenance は粗い provenance 標準の decision が既に認めた水準」と
   書いたが、同 decision は canonical `docs/decisions.md` に存在しない
   (未 land branch `worktree-rulings-20260812-coarse-provenance` 上にある)。
   親自身が段 1 で grep 実測してそう brief に書きながら、同じ brief の別節でそれを
   proof chain の根拠に使った。**自己矛盾**である。
2. **段 3 へ渡した実測 F5 を訂正。** 「`a09` の schedule は承認済み文書で完全に凍結されている」は
   **導出規則については真、serialization については偽**。上表が反例。
3. **(P4)(iii) を訂正。** 「投入は `submit_pilot` 経由でしか起こせない」は機械保証できない。
   保証境界は「直接 qsub された job は driver preflight を越えず、valid run record・試行台帳・
   材料 report・certified 選択へ**一切昇格しない**」まで。

## land したもの / しなかったもの

**land した:** session 1・2 の実装 (`erratum.py` / `blobref.py` / `approval_payload.py` /
`addendum_envelope.py` / Git trust root 部分集合 + test 3 file)、本 session の記録と裁定パッケージ、
先行 session の未 land fragment 7 件。

**land しなかった:** 解除 decision、`submit_pilot`、PBS driver、collector、束縛検査、
`report.py` への `report_scope` additive field。
