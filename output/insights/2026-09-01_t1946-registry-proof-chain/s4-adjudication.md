# 段 4 裁定 — T-1946 / D1194 (旧 D1112) 択 (b)

親裁定。base 11b44e2d1。段 2 plan 1 本、段 3 敵対相談 2 本 (レンズ A / レンズ B)、
親の独立実測 8 件を材料とする。

## 裁定 — 本 wave は実装しない。設計を凍結して裁定パッケージを返す

DW-S04 の「実装しない」裁定にあたる。段 5・6 を飛ばし `4→7→8→9` とする。
実装面の差分がゼロなので変異 matrix は DW-S04 の免除に該当する。**受入全走は免除しない。**

### 根拠 (3 つの着地済み裁定が順序を定めている)

1. **D1114** — 「発火する path を名指しできない gate は、部分実装でも land しない」。
   発火条件は (a) 発火条件を満たす既存 artifact path も計測 ID も名指しできない、かつ
   (b) **独立した敵対検査が**「先行 land すると production 呼び手 0 件の死んだ gate になる」と
   判定した、の両方。理由節に「検査だけ land すると既存 campaign が止まる」と明記がある。
   - (a) 成立。現行 schema は v4 のみで proof field は無く、tracked repo に qualifying artifact は 0 件。
   - (b) 成立。**レンズ A・レンズ B が独立に成立と判定した。** 親も同じ実測に到達している。
   - D1114 は「設計を凍結して裁定へ返す」と結論の形まで指定している。本裁定はそれに従う。

2. **D1193 + D1279** — 「予算の置き場所は新しい設計判断なので、**設計に入る時点で改めて諮る**」
   (D1193)、「先回りして決めない。実装が設計段階に入るまで発火しない」(D1279)。
   **本 wave が設計段階である。** 設計案 (段 2 plan) が出た結果、レンズ B が
   「plan は freeze-wide の単一 `row_count` / `chain_head` を proof identity に採ることで、
   台帳と予算が同じ freeze-wide chain にある設計を暗黙に固定している」と判定した
   (`s8b_attempt_profile.py:378-382`、`attempt_registry_core.py:1019,1120-1129`)。
   これは D1279 が発火する条件そのものであり、諮らずに進めれば留保を破る。

3. **D1194** — 択 (b) は裁定済みで再裁定しない。**本裁定は D1194 を覆さない。**
   目標の設計 (新規成果物への前向き束縛) はそのまま維持し、land の順序だけを D1114 に従わせる。

### 実測 (production 呼び手 0 件) — 3 者独立確認

`launch_floor_attempt()` の production 呼び手は 0 件、launcher module の production import 元も
0 件。呼び手は `orchestrator/tests/test_s8b_floor_attempt_launcher.py` だけ
(public 1 件 `:664`、test-only helper 5 件 `:317,393,436,486,626`、alias import `:20`)。
親・レンズ A・レンズ B が別々に AST / 動的 import / 文字列解決まで含めて確認し、追加経路なし。

したがって現状、production の床値 campaign は attempt registry を一度も作らない。
plan どおり検査側だけを入れると、fresh は `s8b_floor_campaign.py:7702-7724`、
resume は `:7557-7571` で result 組立前に停止し、publish に到達しない。
レンズ B の追加実測として、現在の production CLI は pilot のみ
(`tools/pegasus/floor_campaign.sh:1226-1230`) で official は
`s8b_floor_campaign.py:453-463,8368-8375` で既に拒否される。つまり止まるのは
「唯一生きている pilot campaign」であり、将来 official を開いても同じ位置で止まる。

## 所見の real / refuted と採否

| # | 出所 | 所見 | 判定 | 採否 |
|---|---|---|---|---|
| 1 | A-1 / B-1 | D1114 の両条件が成立し単独 land は禁止 | **real / blocker** | 採用。本裁定の根拠 |
| 2 | B-2 | live tail の完全一致比較は、後続の正当な append で既発行 v5 を無効化する | **real / blocker** | 採用。設計制約として記録。比較すべきは「現 registry の先頭 N 行が記録 head に一致」であって現 tail との一致ではない |
| 3 | B-3 | plan が D1193/D1279 の留保 (予算の置き場所) を暗黙に固定している | **real / blocker** | 採用。ユーザー裁定へ返す本体 |
| 4 | A-2 | s8c 最終 inspector (`s8c_result_judge.py:2103` `verify_floor_bytes`) が live gate を通らない | **real** | scope 外。親が独立確認済み。ただし s8c は certification の消費側で、certification 自体は ratified 経路で起きる。消費時点の台帳生存再確認は D1194 の要求より強い性質なので、別裁定として返す |
| 5 | A-3 | 変異事前登録の候補 5 件に帰属が成立しない | **real / must-fix** | 採用。実装 wave への制約として記録 |
| 6 | B-4 | pure verifier の v5 正例 2 件が plan の閉包から欠落 (`test_end_to_end_golden_floor_values_and_tamper_detection`、`test_verify_floor_artifact_binaries_positive_and_negative`) | **real / must-fix** | 採用。実装 wave への制約として記録 |
| 7 | B-5 | "sole connection owner" docstring が read-only inspector と矛盾する | **real / must-fix** | 採用。実装時は同じ commit で docstring を「adapter/mutation の唯一所有者」へ限定し、read-only verifier ownership を明記する |
| 8 | A-4 | 一部の負例は proof-chain 束縛ではなく部品検査の負例である | **real / nit** | 採用。束縛の負例と部品の負例を分けて登録する |
| 9 | A-5 | 規律 2 の問いは「既存 v4 input の受理面」に限定すべき | **real / nit** | 採用。brief の不変条件 1 の表現を訂正 |

## 親自身の実測の訂正 (レンズが正しく指摘した)

- **F-P4 の過剰一般化を撤回する。** 「admission に registry 参照を足すと確実に meta-test が赤」は
  誤り。meta-test が検出するのは exact token `s8b_attempt_registry` であり、
  `attempt_registry_core` / `s8b_attempt_profile` / 新 inspector 名は該当しない。
  対象 2 file と positive control の実測自体は正しい。
  同様に「producer へ値を届けるには campaign 外から渡すしかない」も広すぎる。
  campaign は既存どおり admission の read-only inspector を呼べる。
- **F-SCHEMA の数え方を訂正する。** 「4 + 3 = 7 の述語」は不正確。schema を拒否する
  consumer 述語は stats / holdout / ratified の 3 件。`s8b_floor_campaign.py:163,6585` は
  必要な変更面ではあるが述語ではない。
- **F-CHAIN の推測を撤回する。** 「空 registry と genesis のみを chain head で区別できない可能性」は
  誤り。genesis は `attempt_registry_core.py:1497-1500` で chained row になり非 zero の
  event hash を持つ。zero になるのは chained row が 1 件も無い入力だけで、
  正規 reader は空自体を拒否する (`:986-1004`)。
- **F-ARTIFACT の限定を維持する。** tracked repo に 0 件は再現したが、
  repo 外・別 checkout・計算ノードまで一般化はできない。

## ユーザーへ返す裁定 (これが本 wave の成果物)

**設計と実測は完成している。足りないのは順序と、留保された 1 つの設計判断である。**

### 択一 1 — 実装の単位をどうするか

- **(A) 書き手配線 + proof chain 束縛を 1 つの wave で同時に land する。**
  D1114 が求める「到達可能な一体設計」。D1194 の目標をそのまま満たす。
  ただし配線には下記の択一 2 の答えが要る。**親の推奨はこれ。**
- (B) 本 wave の設計を凍結したまま、配線 wave を先に走らせ、束縛はその次に land する。
  D1114 が禁じるのは「片側だけの land」なので、配線が先なら束縛側は死んだ gate にならない。
  ただし配線だけ land した状態は D1194 の却下欄「書き手だけ land して束縛を後続へ送る」に当たる。
- (C) 束縛を諦める。D1194 が既に却下している。挙げるのは網羅のため。

### 択一 2 — D1193 が留保した予算の置き場所 (D1279 が「設計案が出た時点で諮る」と定めたもの)

台帳は protocol 世代ごとに分ける (D1193 で確定)。予算は凍結単位に残す (同)。
その両立には、世代を跨いで予算を数える権限をどこに置くかを決める必要がある。

- **(i) freeze 単位の予算専用 ledger を別に置き、世代別台帳から参照する。**
  台帳の分割と予算の集約が構造的に分かれる。proof identity は世代別台帳の側に付く。
  **親の推奨はこれ** — D1193 の 2 つの要求を、どちらも曲げずに満たす唯一の形に見える。
- (ii) 世代別台帳を横断して replay し、予算を毎回再計算する。
  別 ledger を作らずに済むが、世代が増えるほど replay 対象が増える。
- (iii) 予算も世代ごとにリセットする。**D1193 が明示的に却下済み** (規律 2 の面)。

### 択一 3 — proof identity の形 (レンズ B の blocker 2 に対する設計制約)

- **(I) 記録するのは `{row_count=N, chain_head_at_N}` とし、検証は「現 registry の先頭 N 行が
  その head を再現するか」で行う (prefix 証明)。** 後続の正当な append で既発行 v5 が壊れない。
  **親の推奨はこれ。**
- (II) 現 tail との完全一致。plan の初版。**採ってはならない** — 次の 1 件の正当な試行で、
  既に certified だった v5 freeze が oracle judge と verdict から参照不能になる。

### 択一 4 — s8c 最終層を射程に入れるか (所見 4)

- (甲) 入れない。s8c は certification の消費側であり、certification は ratified 経路で起きる。
  **親の推奨はこれ** — D1194 は「新規成果物への前向き束縛」を求めており、
  消費時点の台帳生存再確認はそれより強い性質である。
- (乙) 入れる。公式選択表の発行時点でも台帳の生存を要求する。

## 本 wave が land するもの

実装面の差分はゼロ。docs のみ:

- 上記の裁定を decisions fragment 1 件へ。
- 実測・所見・次の一手を worklog fragment 1 件へ。
- 段 2 plan と段 3 相談 2 本の逐語を insight へ (次 wave が同じ調査をやり直さないため。
  D1114 の却下欄「何も記録せず止める」への対応)。
