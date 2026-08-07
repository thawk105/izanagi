# [T-139] 本走前置 — 段 4 裁定 (2026-08-07)

```text
authority: none
default_effect: no-state-change
```

段 2 プラン (`s2-plan.md`) と段 3 の敵対 2 レンズ (`s3-lensA.md` / `s3-lensB.md`) はいずれも NO-GO を
返した。親は以下のとおり real / refuted を裁定し、プラン v2 を確定する。逐語は
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-prereg-freeze/` に置き、本 wave の記録 commit で
本ディレクトリへ写す。

## 0. 親の誤りの訂正

- **brief の「`package.md` = 確定済みユーザー裁定 11 件の正本」は不正確だった** (段 2・レンズ B、real)。
  `package.md` は裁定**前**に書かれた凍結パッケージであり、本文は今も「11 件未裁定」「κ 未定」と書いている。
  確定結果の正本は `docs/worklog.md` のエントリ (299) / (300) と、land 後の本 wave の新 D である。
  `package.md` は後から書き換えない。凍結事前登録にこの書き分けを明記する。
- **brief が新 D 番号を `D232` と直書きしたのは race-stale だった** (両レンズ、real)。
  以後 slug (`{{D:...}}`) で扱い、番号を成果物へ焼かない。
- **base digest について親が「段 2 の値と不一致」と両レンズへ伝えたのは、親の計算誤りだった。**
  `tools/spool_fold.py` の `_extract_latest_active` / `_task_item_digest` を実際に呼んで再計算した結果、
  段 2 の値 `dc41c0b8…` と一致した。両レンズはこの誤情報に基づき「値を信用するな」と判定しており、
  その判定理由は誤りである。ただし**land 直前に再計算する**という運用規律は正しいので採る
  (並行 wave が [T-139] 項を先に更新すれば digest は変わる)。

## 1. 採用する所見 (real・scope 内)

| # | 所見 | 出所 | 対応 |
|---|---|---|---|
| R1 | brief の (P2)「paired cluster 設計一般」の例外は広すぎる | A1 / B5 / 段 2 | **(P2) を撤回。** 例外は [T-139] の RF 3-arm study に限定する (`DW-G03` — 族一般化には独立 2 例が要る) |
| R2 | 例外条文に trace 分離の再確認がない | A1 | 例外条件に「性能 3 arm はすべて trace-disabled、correctness 検証は別 build・別 run」を明記 |
| R3 | 状態表に穴 — `N>0 ∧ G>0 ∧ H≤0` がどの `qualification_status` にも入らず exact-one が破れる | A3 | **軸 2 を first-match の順序表へ組み替え**、`degradation_below_kappa` を新設して網羅性を閉じる |
| R4 | gate の 5 前提に自己申告根と時間逆転がある (receipt を admission 前提にしている) | A2 / A5 | 署名を 3 段 (`resolve` → `submit` → `verify_receipt`) に分け、receipt 照合を投入**後**へ移す |
| R5 | 「第 2 の完結版」が推論内容を書き換えうる | A5 | **core 1 本 + 閉集合の追補**構成へ変更。追補が変更してよい field を core が閉集合で列挙する |
| R6 | study identity が producer の自由選択になる | A1 / A2 | 例外の適用対象を canonical core path で定義し、producer が別 blob を core と申告できないようにする |
| R7 | base digest は land 直前に再計算する | A5 / B4 | 運用規律として採用 |
| R8 | 確定値の根拠を `package.md` に取るのは誤り | B6 / 段 2 | 凍結事前登録に根拠の書き分けを明記 |
| R9 | 本 wave の gate は文書層だけで、producer / validator / consumer / qsub / receipt には未実装 | B3 | 成果物へ明記し、「投入 gate を実装した」と書かない |
| R10 | `【U#】` marker は `check_docs` が検出しない | A5 / B4 | 親が commit 前に静的走査し、結果を記録する。新 checker は scope 外 |
| R11 | wave commit を 1 本にすると段記録まで混ざる | B6 | **substantive commit** (roadmap / D fragment / 凍結事前登録 / README) と **record commit** (worklog fragment・逐語) に分ける |

## 2. 裁定 — 「同じ変更単位」(D134 決定 (3)) の充足

レンズ B は「段 2 の決定 (7) は循環的な読み替えであり、下位の新決定で既存要件の意味を変更してはならない」
と指摘した (real)。親はこれを受け、**新 D で「変更単位」を再定義しない**。代わりに次の 2 つを同時に採る。

- **(α)** roadmap の限定例外・新 D の fragment・凍結事前登録を**同一の wave commit**に置く。
  `docs/spool/README.md` は未 fold fragment 自体を正本と定めており、canonical 台帳を wave が
  直接編集することは禁止されている。docs-only で到達できる最も強い「同一変更単位」はこれである。
- **(β)** roadmap の例外条文に**発効条件**を書く — 例外は、当該決定が canonical 台帳へ fold された
  land 以後にのみ効力を持つ。fold 前の中間状態 (roadmap だけが見え canonical D がない状態) では
  例外は発効しない。

(β) は最厳格解釈 (canonical D と roadmap が同一 Git commit) を満たすものではない。**満たせない。**
spool 方式そのものがそれを禁じているからである。(β) はその差を無害化する fail-closed であり、
親はこの残差をユーザーへ明示する (§4)。

## 3. 裁定 — 個別の択一

- **(P1) 置き場所 = `output/insights/2026-08-07_t139-mainrun-design/preregistration.md` (新規)。確定。**
  両レンズが refute せず、親が決定的な先例を実測した — 既存 T-139 probe の事前登録は
  `output/insights/2026-08-05_t139-alt-x-probe/preregistration.md` に置かれ、`authority: none` /
  `default_effect: no-state-change` と同じ枠に構造 field (`study_label`) を持ち、PBS が
  `<run_commit>:<path>` の blob として抽出し内容を検査している。本件はこの先例と同型である。
  草案 `preregistration-draft.md` は**書き換えない** (裁定前の記録)。
- **(P2) 撤回** (R1)。
- **(P3) gate の実施点** — 既存 `assert_prereg_ancestor` は祖先しか見ないので単独では不十分 (A2、real)。
  署名は本 wave で書くが、機械配線は producer 実装 wave の責務であることを明記する (R4 / R9)。
- **(P4) 撤回し §2 の (α) + (β) に置き換える** (R11 と併せて commit を 2 本に分ける)。

## 4. scope 外 — ユーザーへ返す裁定候補 (本 wave では実装しない)

1. **`docs/spool` 方式と「同一変更単位」要求の残差** (§2)。canonical D と roadmap を同一 Git commit に
   置くことは spool 規約下で不可能である。(β) の発効条件で無害化したが、要求そのものを緩めたと
   読むこともできる。ユーザーの確認を求める。
2. **producer 実装 wave の前提裁定 4 件** (レンズ B): (i) producer と qsub のどちらを第一の
   admission boundary にするか、(ii) receipt に commit / path / blob SHA のどこまでを必須記録にするか、
   (iii) validator が何を独立に再計算するか、(iv) consumer がどの未認証状態を拒否するか。
3. **U8 の残余数値** (候補数上限・累積 spending の数値) と **U11 の時間予算表**。いずれも
   本 wave では埋めない (捏造禁止)。core は追補で埋める field を閉集合で指定し、
   埋まるまで投入を deny する。

## 5. 変異事前登録 (`DW-M01`)

**実装差分がゼロのため、変異 matrix と受入全走の変異部分は射程外である** (D134 決定 (2) と同型)。
本 wave の検証は (a) `python3 tools/check_docs.py`、(b) `python3 tools/spool_fold.py --dry-run`、
(c) `【U[0-9]+】` および `{{` `}}` の静的全走査、(d) 受入全走 (`tools/run_tests.py`) で行う。
いずれも親が実走し、実走していない検査を緑と書かない。
