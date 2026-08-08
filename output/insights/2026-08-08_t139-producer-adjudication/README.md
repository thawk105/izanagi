# [T-139] producer 実装 — 逐語 (dev-wave 2026-08-08)

```text
authority: none
default_effect: no-state-change
```

本ディレクトリは dev-wave `[T-139] producer 実装` の逐語成果物である。可変状態の正本は
worklog 末尾、採用済み判断の正本は decisions であり、ここには凍結した逐語を置く。
**本文書は可変状態の正本ではない。**

## 結論 (先に読むこと)

- **producer は実装しなかった。コードとテストは 1 行も land していない。**
  段 2 の起草子と段 3 の敵対レンズ 2 本が独立に NO-GO を返した (blocker 計 15 件、重複統合後 11 件)。
  親は全件を real と裁定した (refuted 0 件)。
- **決め手は「入力が存在しない」こと。** PBS 測定本体は追補 A の `a01`〜`a09` (時間予算・待機・
  driver 引数・arm identity・schedule seed) に依存する。これ無しに前置・sink・registry だけを land すると、
  台帳だけが「producer 実装済み」へ進む。worklog (305) の [T-139] 次の一手が記録する順序
  (「追補 A → producer 実装 → pilot」) とも一致する。
- **凍結事前登録 core に内部矛盾が見つかった (新事実)。** §14 の閉集合の表は `a01`〜`a13` を
  列挙するのに、§15 の投入 gate と「通る正例」は `a01`〜`a12` を基準にする。exact-key なので
  2 つの集合は**互いに素**であり、どちらを実装しても他方を満たす追補 A が拒否される。
  `a13` は primary 系列の有意水準であり、`a12` 読みでは pilot の後に有意水準を選べる状態が残る。
  **これは 2026-08-07 の裁定時点で未見であり、親が片方を選ぶと受理集合が動くため、ユーザー裁定へ返す。**
- **ユーザー裁定 4 問へ分解した。** 正本は `package.md` (凍結。裁定後も書き換えない)。
- **親の誤りが 3 件ある。** うち 1 件は「実装被覆 0」で、D229 決定 (7) が既に訂正済みの見積りを
  親が再導入したものである (§訂正 = `s4-adjudication.md` §0)。

## ファイル

| file | 内容 |
|---|---|
| `README.md` | 本文書 |
| `brief.md` | 段 1 brief (凍結。書き換えない。誤りは `s4-adjudication.md` §0 を正とする) |
| `s2-plan.md` | 段 2 プラン起草 (codex read-only, reasoning=max) — NO-GO、file:line 粒度の実装案付き |
| `s3-lensA.md` | 段 3 敵対レンズ A = 正しさ境界と権威境界 — NO-GO、blocker 7 + must-fix 4 + nit 1 |
| `s3-lensB.md` | 段 3 敵対レンズ B = 手続き整合と実効性 — NO-GO、blocker 8 + must-fix 2 |
| `s4-adjudication.md` | 段 4 裁定 (real/refuted、親の誤り 3 件の訂正、実装しない理由) |
| `record-items.md` | **段 A 記録項目 (受領証 closed schema) の案** — 裁定 gate 提出用 |
| `package.md` | **ユーザー裁定パッケージ (4 問)** |

## 1. 敵対検証が実装前に止めたもの

段 3 の 2 レンズが計 21 件の所見を返し、親は全件 real と裁定した。統合後の主なもの:

- **認可を置く sink の位置が誤っていた。** 段 2 の案は `qsub` を行う関数にだけ binding を必須化し、
  **受領証を実際に書く関数は無認可**のままだった。T-609 が否定した「呼び手側の認可」の再現である。
  T-643 (i) の「認可の第一境界は producer 側」に照らすと、必須引数は受領証を永続化する関数に要る。
- **追補 A の study-wide な一回限り束縛が無い。** 各投入時点の祖先検査だけでは、pilot 1 の後に
  別の追補 A2 を commit して pilot 2 をそれに束縛でき、各投入は自己整合する。
  事前登録は「pilot 1 本目より前」に固定することを要求している。
- **失敗投入を raw に残す authority と collector が無い。** 事前登録 §13 の否定検査 1
  (失敗投入を台帳と raw の双方から落とす) が閉じない。qsub 前の durable intent と、
  job 側 preflight reject の回収経路が同じ実装単位に要る。
- **受領証から trace-enabled / trace-disabled の分離を再計算できない。** 絶対規律 1 に不足する。
  性能 arm の `trace_enabled` と、correctness 証拠の独立 build identity、両者の非同一性制約が要る。
- **preflight の source authority が未定義。** helper 1 枚を commit blob から実行しても、
  import される resolver が live worktree なら束縛されない。T-609 で実際に起きた欠陥の同型である。
- **段 A 帰属の変異 6 件のうち 4 系統で単一理由帰属が不成立。** JSON schema の
  `additionalProperties:false` と runtime の exact-key 再検査が二重の層になっており、
  片方を無効化しても他方が拒否する (`DW-M01` / D190)。実装時に実効 gate へ再照準が要る。
- **a03 (環境復帰の指標と許容範囲) の恒真化は静的検査では防げない。** 「`allocation_observation` と
  名乗りながら定数を返す実装」「有限だが実現値を必ず含む範囲」は raw observation からの再計算を要する。

## 2. 訂正 (親 brief の誤りを本ディレクトリが正とする)

詳細は `s4-adjudication.md` §0。要点だけ:

- **訂正 1 (実装被覆)。** brief の「実装被覆 0」は誤り。D229 決定 (7) が「0/9 は過大」と既に訂正しており、
  `orchestrator/qualification/` の試行台帳・系列 FSM・投入束縛・原子公開・identity が
  記録項目の要求に構造的に対応する。正しい主張は「**T-139 固有の public API が 0 件**」である。
- **訂正 2 (成果物影響表)。** brief §4 の 6 行は、追補 A・PBS 測定本体・publisher 結線・validator caller が
  揃った**後**の効果である。現時点では pilot 経路自体が存在しない。
- **訂正 3 (`verify_receipt` の検出力)。** 検出できるのは「producer が書いた 2 つの文書の食い違い」であり、
  実測 checkout の混入ではない。事前登録 §15 の非保証、および T-643 (ii) の「完全な偽造検出は見送り」と一致する。

## 3. 本書が主張しないこと

- 段 2 の実装案が正しい、とは主張しない。両レンズが NO-GO を返しており、採用していない。
- `record-items.md` の記録項目が承認された、とは主張しない。**単独の裁定 gate の提出物**である。
- 投入 gate を機械的に実装した、とは主張しない。resolver も受領証 producer も投入 script も存在しない。
- 実装差分がゼロのため、**変異 matrix は射程外**である。
