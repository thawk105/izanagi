# [T-1851] 単位 C2 — 実行失敗の構造化と 2 量の分離

branch `worktree-dev-wave-t1851-unit-c2`、base `0cb90c592`
(継承 tip `ebbae72ba` + local main 固定 SHA `cc9bba523` の merge)。
**land しない (D1341)。** 6 単位が揃うまで branch 上の checkpoint に留める。

---

## 1. 何をしたか

契約 `contract-v3.1.md` の 3 節・9 節が「C2 が持つ」と射程外に切った 4 点のうち、
**1〜3 を実装した。4 点目は達成していない** (5 節に理由と実測を書く)。

実行失敗の数え方を、runner が書く**自然文の note を正規表現で読む**方式から、
rep 証跡の**構造化 field** から導く方式へ替えた。契約 3 節が
「自然文を信頼経路に残さない」と決めた確定裁定に従う。

- rep 証跡に 7 番目の key `execution_failure` (exact `bool`) を足した。
- runner の**両公開面**を同じ形にした。床値 campaign が実際に呼ぶのは
  `measure_point()` で、launcher が使うのは `capture_measure_point()` である。
  片方だけ直すと、経路によって契約 3 節の等値束縛が成立したりしなかったりする。
- campaign の `_EXEC_FAIL_RE` と `_count_exec_failures` を唯一の呼び手ごと除去した。
- 中央 verifier (`s8b_floor_stats`) も `exec_failures` を独立に再導出し、
  top-level の申告値との等値を要求する。resume gate も同じ検査を通す。

## 2. 敵対検査が暴いた破れ 2 件 (どちらも実装で閉じた)

### 2.1 terminal の本数式が 2 量を再結合していた

契約 v3.1 の 1.4 節と 2 節は opened の不変条件を
`len(throughputs) + nonfinite_count + exec_failures == reps_expected` と固定していた。
**この式は `exec_failures` を「欠格 rep すべての代理」に使っており、契約 3 節が
禁じた再結合そのものだった。**

- 非 zero 戻り値だけの rep を持つ**正当な session を拒否する**。
- 逆に、偽の `execution_failure=True` を申告すれば**通ってしまう**。

4 分類 (qualified / 非有限 / 実行例外 / その他の証跡不備) を互いに素に数える形へ作り直し、
`exec_failures <= rep_integrity_failures` を要求する。契約は
`contract-v3.1-erratum-1.md` で追記訂正した (規律 7 に従い本文は改変しない)。

### 2.2 「実行失敗 rep を完備と数えない」保証が発火していなかった

campaign の射影にある `complete` 述語から `execution_failure is False` の連言を外しても、
**どのテストも赤にならなかった。** rc=0 のまま実行に失敗した rep が qualified throughput へ
混ざりうる状態だった。

**これは段 3・段 6 の敵対レンズ 4 本と静的読解では見つからず、変異を実際に走らせて初めて出た。**
他の連言をすべて通す単一理由の負例を置いて閉じた。

## 3. 診断 counter が 1 つの入力 class で変わる (ユーザー裁定へ返す)

`FORMULA_ID` の据え置き可否を実装時 gate として検査したところ、
**producer が実際に出しうる 1 つの outcome class で値が変わる**ことが判った。
「subprocess は rc=0 で終了したが、その後の stdout 解析で例外を捕捉した rep」である。

| 量 | 改訂前 | 改訂後 |
|---|---:|---:|
| `exec_failures` | 1 | 1 (変わらない) |
| qualified throughputs | 同一 | 同一 (変わらない) |
| session の有効性 | — | 変わらない |
| session median | — | 変わらない |
| `rep_integrity_failures` | 0 | **1 (変わる)** |

旧実装は rc=0 と counter 完備だけでこの rep を complete と数えていた
(throughput が `None` でも complete)。**受理集合が狭まる向きの訂正である。**

`s8b_floor_stats` の docstring は「式には診断も含む。式を変えるときは `FORMULA_ID` を改版する」
と書き、改版すると `output/s8b-freeze/floor_protocol.json` の bytes が変わって
`FROZEN_MANIFEST` の pin に届く。**`FORMULA_ID` は変更していない。改版要否はユーザー裁定へ返す**
(`ruling-package.md` 裁定 1)。

producer の全 outcome class の直積 341 通りで、**変わらない量と変わる量の両方を exact に固定した。**

## 4. 成果物への波及 1 件

`floor_pair_driver` は runner の証跡をそのまま `floor-pair-window/v3` へ保存し、
その bytes が `finalize_floor()` の `artifact_sha256` に入る。
**7 key 化で実行時にこの成果物の digest が変わる。**

ところが同 consumer の test fake は 3 key しか作っておらず、同じ窓 schema が
旧 3 key と新 7 key の両方を受理していた。fake を実 producer の形へ揃え、
窓 record の key 集合と型を exact に固定した (`artifact_sha256` の値は焼き込んでいない)。

**この波及は段 1 の親の表にも段 2 の plan にも無く、段 6 のレビュー B が出した。**

## 5. 4 点目を達成していない理由 (実測)

契約 9 節は「`launch_floor_attempt()` の production 呼び手は 0 件。実値域は C2 が供給する」と書く。
**本 wave はこれを満たしていない。「実環境の値域を供給した」とは書かない。**

- `launch_floor_attempt()` の production 呼び手は **0 件**。
- launcher module の import 元は repo 全体で **1 件、自分の test file だけ**。
- campaign から `attempt_registry` への参照は **0 件**。
- **実 campaign の値域を記録した成果物は repo に 0 件** (親が `output/` 全体を走査)。
  記録済みの実値を launcher の gate へ通す近道は存在しない。
- 配線の見積りは 5 file / 350-550 行 (段 2 plan)。しかも 7-key schema が先に無いと組めない。

単位分割の扱いはユーザー裁定へ返す (`ruling-package.md` 裁定 2)。

## 6. 未解決として残す穴 (帰属つき)

`returncode=0` ∧ `execution_failure=False` ∧ `throughput=None` の rep は 4 分類のいずれにも
入らず、sealed terminal を作れない。**改訂前後で挙動が同じであり、本 wave に帰属しない**
(旧式でも同じ rep は拒否される)。閉じるには受理集合を動かすので、後続単位の裁定へ送る。

## 7. 最終状態の実測

- **受入全走 `child-green`: 22,404 passed / 68 skipped / 0 failed** (attempt 6、receipt 発行済み)。
  tested main `931fd8fc5`、tested tip `dd6e3beff`。
- **変異 12 件すべて KILLED、MISMATCH 0、SURVIVED 0。** 期待 node は完全集合で固定した。
  1 node の単一理由 kill が 7 件 (M1・M2・M5a・M5b・M6・M9・M10・M11)、
  残りも 2〜5 node に収まる。
  **M7 (key 集合を 6 へ戻す) は 148 node の過剰決定だったので、`DW-M03` に従い
  単独変異の証拠から外した。**
- **probe では M6 だけが SURVIVED した。** 段 3・段 6 の敵対レンズ 4 本が見逃した穴で、
  変異を実際に走らせて初めて出た。負例を置いて本走で KILLED になった。
- 親が独立に実走した緑: runner 2 file 70 件、算出 3 file 675 件、
  焦点走 22 file 3,082 件、対ドライバ 211 件、sink 台帳 44 件、campaign 494 件。
- 受入所要台帳: 20,284 件から **22,426 件**へ 2,142 件を add-only で追加
  (削除 0・既存値変更 0 を検算)。

### 受入 6 回の内訳と赤の帰属

| attempt | 結果 | 赤の帰属 |
|---|---|---|
| 1 | 22,320 passed / 24 赤 | 3 件は**帰属** (行番号 pin)、21 件は非帰属 (`git ls-files --others` の setup timeout) |
| 2 | 22,390 passed / 1 赤 | **帰属** (受入所要台帳の被覆率) |
| 3 | 22,371 passed / 20 赤 | 非帰属 (同じ setup timeout の再発) |
| 4 | 走行前に停止 | main が進み merge message の provenance が要求された |
| 5 | 22,401 passed / 3 赤 | 非帰属 (launcher の rc timeout) |
| 6 | **22,404 passed / 0 赤** | — |

**非帰属の判定は毎回 local main 単独走と branch 単独走の両方で行った。** いずれも
私の差分に含まれず、変更した module を import もしていない file で、単独走では全件緑だった。

## 8. 段 8 — 自己改善は予算に阻まれて 2 件とも落とした

候補は 3 件あり、**docs への収容は 0 件**である。

1. **`DW-O01` の予算見積りに wall-clock が無い。** 同節は「重い巡は call/token を見積もる」と
   しか書かず、本 wave の段 5 子 2 は **call 122/400 と余裕があるのに wall-clock 既定 3600 秒で
   SIGTERM され、483 行の実装を終えていながら報告 0 byte** で落ちた。
   **収容を試みたが `docs/dev-wave/**` の L1.5 層が上限 9,696 bytes に対して満杯だった。**
   4 節を意味等価に詰めても 30 bytes 足りない。D730 は
   「収容先が既存記述の削減で作れないと確かめられた場合にだけ上限を引き上げる」とし、
   例外の基準を「同型の実害が独立に 3 例以上」と定める。
   **wall-clock 超過の実測は本 wave の 1 例だけ**なので例外に当たらず、
   D730 の原則どおり「実施しない」へ落とした。**上限は引き上げていない。**
   事故の経緯は failures 台帳が持つのが正しい置き場所であり、そこへは収容した。
2. **子の実走指示に成長 hold の迂回禁止が無い。** 段 5 子 1 が
   `GrowthTestHoldBypassRefused` を迂回して走らせた。実測 1 例で、実害も出ていない
   (子は結果を正直に報告した)。同じ理由で落とした。親は投げ文へ手で書けば足りる。
3. **投入前の参照 path 実在検査を親が飛ばした。** `DW-O01` は既に規定しており、
   **規定の欠落ではなく親の不履行**である。docs 変更は要らない。failures 台帳へ記録した。

**予算に阻まれた 2 件のうち上限引き上げに至ったものは 0 件なので、D782 の報告義務には該当しない。**

## 9. 収録物

- `contract-v3.1-erratum-1.md` — 契約 v3.1 の 1.4 節・2 節への追記訂正
- `s1-brief.md` — 段 1 brief (実測アンカーと pin 閉包。親が 3 度自己訂正した経緯を含む)
- `s4-adjudication.md` — 段 4 裁定と変異事前登録
- `ruling-package.md` — ユーザーへ返す 2 件
- `mutation-probe-spec.json` / `mutation-probe-out.json` — 変異 probe (全件 SURVIVED 登録)
- `mutation-final-spec.json` / `mutation-final-out.json` — 本走 (exact node 集合)
- `verbatim/` — plan、敵対レンズ 4 本、実装子 3 本、fix 3 本の逐語
- `verbatim/prompts/` — 全子へ渡した prompt の逐語
