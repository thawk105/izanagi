# [T-810] 測定装置 slice 1 — insights package

依頼は「実測の実施」だったが、protocol §9 の 2 段承認関門と実装 0 byte により**実測は投入できない**。
本 wave は投入の前提となる**凍結された事前登録と非流入検査**を作った。
**キューへ T-810 の測定を 1 件も投入していない。**

## 構成

| file | 内容 |
|---|---|
| `brief.md` | 段 1 brief。scope・不変条件・親の provisional 裁定 (P1)(P2)(P3) |
| `s4-adjudication.md` | 段 4 裁定。所見 15 件の real/refuted、変異事前登録 16 件 |
| `verbatim/s2-plan.md` | 段 2 起草プラン |
| `verbatim/s3-lensA.md` | 段 3 敵対レンズ A (正しさ境界と非流入) — NO-GO、blocker 8 |
| `verbatim/s3-lensB.md` | 段 3 敵対レンズ B (事前登録の網羅性) — NO-GO、blocker 6 |
| `verbatim/s6-revA.md` | 段 6 敵対レビュー A (validator) — NO-GO、blocker 5 + must-fix 4 |
| `verbatim/s6-revB.md` | 段 6 敵対レビュー B (凍結) — NO-GO、blocker 4 + must-fix 3 |
| `verbatim/s6-focus.md` | 段 6 焦点再レビュー — NO-GO、closed 8 / partial 7 / regressed 1 |
| `mutation/mutation-spec.json` | 変異 16 件の事前登録 (結果に合わせて書き直していない) |
| `mutation/mutation-ledger.json` | 変異本走の台帳 |

## 成果物

| path | 役割 |
|---|---|
| `tools/pegasus/policies/t810_prereg_v1.json` | 凍結事前登録。N=13・R=10、状態別 effective N、golden vector、F 分位の binary64 hex 定数、benchmark argv、投入順 seed 手続き、`/authorization`、`/limitations` |
| `orchestrator/campaign/t810_preregistration.py` | 承認 receipt を必須にする loader。raw bytes への digest、深い不変射影、休眠封印、読込完了時の golden conformance |
| `orchestrator/campaign/t810_estimator_v1.py` | 参照 evaluator。`eval()` 不使用、backend 分岐なし |
| `orchestrator/campaign/t810_validator.py` | §6.3 の 5 検査を束ねる単一 fail-closed validator |
| `tools/pegasus/validate_t810.py` | pre / post を同一実装へ振り分ける CLI |

## 変異 matrix の結果

**16 件中 13 件が期待どおり** (KILLED 12 + 正例 SURVIVED 1)。

MISMATCH 3 件 (M3・M4・M6) は**すべて超過検出**である — 変異は KILLED され、
**期待 node は実測 node の部分集合**だった。原因は本 wave が新設した
「loader 完了時に golden conformance を実行する」結合で、凍結物と推定の破壊が後段へ波及する
(M3 = 48 node、M6 = 41 node、M4 = 3 node)。

**期待 node を実測へ合わせて書き直しての再走は行っていない。**事前登録を結果に合わせる事後調整に
なるためである。`DW-M03` に従い **M3 と M6 は過剰決定 (冗長 gate) として単独変異の証拠から外す**。
M4 は予測不足として記録する。

M1 は **wave 前の実コードに実在する形** (`git ls-files --others --exclude-standard`、
`orchestrator/campaign/s8b_ratified_freeze.py` ほか) と同型の変異であり、
新設した「gitignore を参照しない全走査」がその形を拒否することを確認した。KILLED。

M16 は正例で SURVIVED。過剰拒否が無いことの証拠であり、実際 fix 1 巡目では
この正例が過剰拒否 (validator 自身の `index.lock` churn) を捕まえた。

## 受入全走の実測値

| 走 | request | 秒 | 結果 | 備考 |
|---|---|---:|---|---|
| 1 走目 | `905180.nqsv` | 583 | **6 failed / 9201 passed / 20 skipped** | 4 件は本 wave の所有外波及、2 件は main 由来 |
| 2 走目 | — | 560 | **2 failed / 9205 passed / 20 skipped** | **残るのは main 由来の 2 件だけ** |

焦点走 (本 wave の 3 file) は **82 passed / rc=0**。

**land は本 wave の成果物ではなく main 側の赤で塞がれている。**
`orchestrator/tests/test_t793_report.py` の 2 件が、`docs/decisions.md` の `D305` に対して
期待値 `("D292",)` を literal 固定しているために落ちる。両ファイルを変更したのは
main の祖先 commit (`427da17c` / `c820722a`) だけで、本 wave の 8 commit は触れていない。
公表層 (T-793 / D291) の fail-closed な報告 gate であるため、
**本 wave は文脈なしに直さず起票して止めた。**

## この package が主張しないこと

- **§9.1 の充足。**(a) N-job barrier 系、(b) PBS wrapper、(c) runner policy、
  (d2) 測定ノード上の repo 不在、(f) 並走ガード機械化、(g) 予算 admission が未実装であり、
  人間の承認 ID も 2 つ未発行である。**本 slice の validator が rc=0 を返しても、
  それは投入の承認ではない** (休眠封印により結果型から投入経路へ到達できない)。
- **未記録 exec の不存在。**receipt の照合だけでは証明できない。
  (b) の単一 mediation 点まで閉じない。`/limitations` に宣言してある。
- **承認 receipt の外部権威性。**署名も trust root も無く caller が自己発行できる。
  `/limitations/approval_receipt_trust_root_absent` に宣言してある。
