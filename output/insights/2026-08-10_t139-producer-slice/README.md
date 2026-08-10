# [T-139] producer 実装 wave — 逐語と変異台帳 (2026-08-10)

branch `worktree-dev-wave-t139-producer-slice`。可変状態の正本は `docs/worklog.md` 末尾である。
本ディレクトリは凍結記録であり、後から書き換えない。

## 結論

**依頼された vertical slice (受領証 → validator → 投入 script) は通していない。**
段 3 の敵対レンズ 2 本と段 6 のレビュー 2 本 + 焦点再レビューがすべて NO-GO を返し、
親は所見を全件 real と裁定した (refuted 0 件)。段 4 で scope を
「承認 payload (docs) + 参照束縛の純関数 2 本」へ縮小した。

**pilot は依然として投入不可。**投入 gate は実装していない。

## 塞いだもの / 塞げなかったもの

| 区分 | 内容 |
|---|---|
| 実装した | 凍結 blob 読取 (環境無害化・commit 型 / regular blob mode・size 上限・shallow/replace/grafts の fail-closed)、erratum の 2 operation 適用と `erratum_id` 別 validator registry、追補 A envelope parser (fence 認識つき exact-13)、承認 payload の canonical 固定 |
| 実装していない | `resolve_effective_preregistration` / `PreregBinding` / `submit_pilot` / `verify_receipt`、approval manifest、受領証 schema、alpha 予約台帳、PBS 測定本体・driver・collector・durable intent、correctness verifier の配線、end-to-end 正例 |
| 閉じられなかった穴 | 合成 digest の trust root は caller supplied のまま (manifest 待ち) / resolver 経由の fail-closed 変異は resolver 不在のため定義不能 / correctness verifier の即時 gate は pilot と同じ単位に要る |

## ユーザー裁定へ返した 4 問

1. **Q-A** 承認済み 2 文書の矛盾 — 追補 A `a04` は preflight の `a03` 不成立を
   `post_performance_failure` へ写すが、record-items は同 reason に marker か
   性能 run raw の実在を要求する。preflight で落ちた attempt はどちらも持たない。
   **受領証 schema の digest 固定はこの裁定待ち。**
2. **Q-B** core §7 の較正義務が未達のまま段階 2 が発効している。
   承認済みの第 2 erratum を誰がいつ起草するか。それまで pilot を機械的に止めるか。
3. **Q-C** `a13` の原子予約台帳の canonicality をどこに置くか
   (固定 Git ref は clone 間の二重予約を防げないと敵対検証が示した)。
4. **Q-D** 残りを 2 波に割るか 3 波に割るか。

詳細は `verbatim/s4-adjudication.md` と `verbatim/s1-brief-addendum.md`。

## 実測値 (親が一次資料から独立に算出。段 2 の申告と全件一致)

```text
凍結 core (F 時点、450 行)  ac939af4de87dff0cd3964e37cef975d57919a709d57f4e9523c8b6a9fcd60e9
erratum op1 対象行 (404)    6e87b981b2d3550ea56278a50f9544a86bab575d18de3ea7f3984abdeca5681e
erratum op2 対象行 (424)    b5e2c7b290c1c21aff84f4b520468df551c9d0e4bd76d2102ace3208b3e1b7d1
対象トークンの出現件数      2 件 (404 / 424 行のみ)
2 operation 適用後の合成    d1782b04ceb7cd56a3d10e2e6efb4eb7f90e6a89506a74bba727d34a5f79de82
承認済み追補 A (再発行版)   f7db96ce8ecb12359fedf56baea24939c629d4d16a1ec167c183425ea198cfec
判定写像                    bf5b6783b5a1a0b6c495618fe5292a968e44712d857cf84bdc436dcf027f6025
erratum                     a1abc60ef8e3f4346f61fbdd8282c295f353ca272062af02a856e3c5de9dd6d3
record-items                1957026c83db3486a39508a9aae07fd03ff5ac84d4edfc0d24b7051758f78fd3
旧版追補 A (非承認)         1f5612587ffeacd39285a28fb1b2e35df6e904689ec30bcc4877e85223146bdd
```

実追補 A の `## fields` 節は 871 行、fence 行 76、fence 内の見出し様の行 0 件、
素朴な `### ` 見出し 13 件。したがって fence 認識の新設は承認済み文書の解釈を変えていない。

## 変異

| ledger | 内容 |
|---|---|
| `mutation-ledger.json` | 初回本走。19 変異、baseline PASSED、**16 KILLED / 3 MISMATCH / SURVIVED 0** |
| `mutation-ledger-erratum.json` | 期待 node を実測へ合わせた再走。3 変異、baseline PASSED、**3 KILLED (期待一致)** |

MISMATCH 3 件 (M11 / P1 / P2) はいずれも期待 node が発火したうえで
もう 1 node も同じ単一理由で落ちた過剰決定であり、生存ではない。
初回 spec と初回 ledger は変更していない。

親の事前登録 9 件のうち 3 件は検出力の過大計上だった (段 6 レンズが指摘)。
要素数検査の削除は他層が同じ入力を拒否するため冗長 gate として単独変異の証拠から外し、
行束縛だけを壊す変異を新設し、resolver 不在で定義できない変異は代用を作らず未登録にした。

## 受入

`7876 passed / 20 skipped / rc=0` (495.47 秒、計算ノード)。
測った tip は最新 main を取り込んだ merge commit である。

## 逐語

`verbatim/` に段 1〜段 6 の全成果物を置く。
段 3 のレンズ 2 本、段 6 のレビュー 2 本、焦点再レビューはいずれも **NO-GO** を返した。
段 6 の fix 子が `closed` と申告した 4 件を焦点再レビューが `partial` へ覆した記録も含む。
