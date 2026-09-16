# 段 4 裁定 — [T-2639]

親が段 2 プランと段 3 レンズ A / B を裁定し、プラン v2 と変異事前登録を確定する。

## 1. 所見の裁定

### 採用する (real)

| # | 出所 | 所見 | 裁定 |
|---|---|---|---|
| A1 | レンズ A | `test_spool_fallback_has_one_decisive_layer` は層が 1 つなら誤った証拠でも通る [恒真ゲート] | **採用。** 一般不変条件「decisive は常に一層」は作らず、各 case で layer・outcome・verdict・path・四要素・matched commit を**具体値で**照合する |
| A2 | レンズ A | `test_spool_fallback_does_not_call_regular_decision` は全 spool を無条件 `indeterminate` にしても通る [テスト代表性] | **採用。** 実体を名指しする正例 (`_spool_exact_positive_decision` が実 `_find_exact_state` 経由で `landed` を返す) を対にする |
| A3 | レンズ A | probe テストは exact 解決済みだけだと probe が呼ばれず発火しない | **採用。** 候補 0 の未解決 fragment で probe 実行を確認し、probe 結果を変えても verdict が不変であることを検査する |
| A4 | レンズ A | batch 異常テストは main tip を不一致にしないと分岐へ到達しない。注入応答が消費された assert が要る | **採用。** 到達証明の assert を必須にし、空入力・余剰行・終端 LF 欠落・`ambiguous`・`dangling`・引用符・先頭 `-` を case に足す |
| A5 | レンズ A | `:` を含む実在 path は 1 件でなく **1,653 件** | **採用。** 段 2 プランの「実在例あり」は正しいが件数を訂正する |
| B1 | レンズ B + 親 | S1/S2 後も `exact-state-not-proven` (6 / 7 件) と `exact-object-seen-at-another-path` (17 件) が残り rc=2 のまま | **採用。受入条件に明記する。** 「rc を 0 にする」を成功条件にしない |
| B2 | レンズ B | 「情報を運ぶ」は consumer 不変更では届かない。`check_branch_rescue.py` は unit evidence を捨て、集約 reason と `report_sha256` しか返さない (`:1557-1568`) | **採用。scope に S4 を追加する** (下記) |
| B3 | レンズ B | 「decisive は常に一層」という新一般不変条件、identity 二重索引、`_find_object_any_path` の batch 化は不要な複雑化 | **採用。いずれも実装しない** |
| C1 | 段 2 + 両レンズ | 親 brief の誤り — M2 の 121 倍は局所値 (端から端では約 20 倍、mode 再確認を含まない)、M2b は「18 種類の状態」であって merge commit 18 個ではなく包含関係は未証明、M3 は blob 一致のみで四要素の正例実測として不足、I7 の「非 blob (tree / symlink)」は誤りで symlink は blob (差は mode)、M6 の「rc=2 が削除 gate を止める」は §2 が rc を使わない事実と矛盾 | **全件採用。**親 brief を訂正した上で段 5 へ渡す |

### 採用するが scope 外 (裁定パッケージへ返す)

| # | 出所 | 所見 | 裁定 |
|---|---|---|---|
| X1 | レンズ A | 候補上限超過でも正例を優先して `landed` を返す現行方針と、D922 点 4 の逐語「上限超過は indeterminate」が衝突する [ドリフト] | **real。だが scope 外。** D922 を書いた [T-1239] wave 自身が `test_history_match_at_candidate_33_wins_before_65_plus_truncation` で現行挙動を逐語固定している。既存挙動は変えない。裁定パッケージへ |
| X2 | レンズ B | 「main 側の改版で価値が取り込まれた」を D922 の枠内で機械判定できない。rc=2 を消すにはこの設計択一が要る | **real。scope 外。** 証拠契約の変更であり AI が単独で決めない。裁定パッケージへ |
| X3 | 親 | `docs/unreachable-object-ledger.md:84` の rc=2 の定義は「timeout、上限超過、root 移動、期限算出不能、台帳 parse 不能などで技術的に不完全」であり **`indeterminate` verdict を挙げていない**。一方 D1231 の却下項は「`indeterminate` があっても rc=0」を却下している。実装は `complete = (verdict != indeterminate)` (`check_branch_rescue.py:1568`) | **real。scope 外。** 正本どうしの読みが割れる。**実装は現行のまま変えない。** 逐語を並べて裁定パッケージへ |
| X4 | 段 2 + レンズ B | 削除 spool fragment の exact 証明対象 (required の不在 / old blob の過去存在) | **real。scope 外。** 段 2 の除外判断を支持する |
| X5 | レンズ B | 親子 timeout の終了余裕 — rescue の子 deadline と外側 subprocess timeout が同値で、子の理由 JSON より先に kill されうる | **real。scope 外。** S3 の測定には織り込むが、予算分割の再設計はしない |

### 却下する (refuted)

| # | 所見 | 却下理由 |
|---|---|---|
| R1 | 「S1 は無益」 | 10.92 秒 → 0.09 秒 の実測がある。端から端では約 20 倍だが、それでも timeout の主因を外す |
| R2 | 「S2 は判定を甘くする」 | D922(a) の既存証拠を spool へ適用するだけで、新種の証拠を足さない。正例専用で `not-landed` へ届かない |
| R3 | P2 の代案「identity 索引」 | 最終条件を保つなら新しい正例を増やさず、保たないなら証拠条件を変える。どちらでも採らない。re-home では wave も SHA も変わる実例があり identity 索引だけでも解決しない |

## 2. プラン v2 (確定 scope)

- **S1** — `_find_exact_state` の候補走査を tagged batch 化する。
  `--batch-check=%(objectname) %(objecttype) %(objectsize) %(rest)`、入力
  `<full-commit-oid>:<path> <連番>`。成功行にも連番で順序検査を効かせる。chunk の全行を検証してから
  一致を受理する。OID/type が一致した候補だけ **同じ commit** を `_tree_entry` で再取得し
  `_entry_matches` を必ず通す。空白・LF・CR・TAB を含む path と `required.missing` / tree / gitlink /
  非通常 mode は既存 `ls-tree` 経路へ退避する。`:` で分解しない。
- **S2** — spool fragment で fold receipt が不一致のとき、**通常 blob (mode 100644 / 100755) に限り**
  exact-state 探索へ正例専用 fallback する。`_spool_exact_positive_decision` は `state.change` /
  `state.old` / `any_path` を受け取らない。receipt parse error・blob 上限・fragment 解析エラーを
  exact の成功で覆い隠さない。削除 fragment は対象外。
- **S3** — 定数は段 6 の実測後に親が決める。到達可能範囲は landed CLI が 300 秒以下 (`:1945-1951`)、
  候補数 1〜100000 (`:1979`)、rescue 全体予算 1〜900 秒 (`:2094`)。
- **S4 (追加)** — `check_branch_rescue.py` の `_landed_assessment` が返す dict に、**未証明 unit の
  説明**を運ぶ。最小形は次のとおり。
  - 未証明 unit ごとに `commit` / `path` / `change` / `required_state` / `decision.reason`
  - 各 unit の決定的証拠層の `outcome` / `reason` / `candidate_count` / `candidate_limit`
  - `reason` 別の件数表
  - 子 JSON を得られなかった場合 (timeout 等) は、その欠落を明記し「全 unit を説明できた」と
    書かない
  - **件数上限を設け、超過時は truncated を明記する** (無制限に出力を膨らませない)
  - `complete` / `conclusive` / `verdict` / rc は 1 bit も変えない。
  - 成果物影響: 到達不能 object 台帳への記帳判断材料が、`report_sha256` だけでなく
    「どの commit のどの path がなぜ未証明か」を含むようになる。

## 3. 不変条件 (段 5・6 で破ってはならない)

I1〜I7 は親 brief のまま。ただし I7 を訂正する — **symlink の object type は blob であり、
通常ファイルとの差は mode である。** 非 blob は tree / gitlink を指す。

追加。

- **I8** S4 は `complete` / `conclusive` / `verdict` / rc / `decision_inputs` の既存 field の値を
  変えない。追加 field だけを足す。
- **I9** X1〜X5 の挙動を変えない。

## 4. 受入条件 (この wave の成功判定)

1. 変異 matrix が baseline 緑、登録全件 KILLED、SURVIVED 0、MISMATCH 0、期待 node 完全一致。
2. 受入全走が緑。
3. **`worktree-dev-wave-t2515-calib-rr95-rr5` と `worktree-dev-wave-prov-incremental-audit` の 2 本で、
   変更前後の verdict が同一** (どちらも `indeterminate`) であり、**所要と git 子 process 数が減る**。
   実測値を worklog に書く。
4. **着地済み wave の spool fragment が `landed` になる正例**と、**未着地 wave の spool fragment が
   `indeterminate` のまま (`not-landed` ではない) 負例**が、実 repo を読むテストで固定される。
5. rescue の出力に未証明 unit の理由が載り、`indeterminate` の commit について
   「どの path がなぜ未証明か」が JSON から読める。
6. **rc が 0 になることは成功条件ではない。** B1 のとおり残余は残る。残余の件数と理由を worklog に
   書く。

## 5. 変異事前登録 (DW-M01)

spec schema は `izanagi-dev-wave-mutation-spec/v1`。実例は
`output/insights/2026-08-27/t1825-rescue-gate/mutation-final-spec.json`。

先行 wave [T-1239] の錨のうち、本 wave が書き換える経路を通る 4 件を**再登録**する。

| id | 変異 | 期待する赤 |
|---|---|---|
| N01 | S2: receipt 不在の spool を `indeterminate` → `not-landed` (旧 M1 の錨) | 未着地 spool の負例が `not-landed` になる |
| N02 | S1: mode 再確認を落とし、OID/type 一致だけで受理 (旧 M5) | mode だけ違う候補の負例が `landed` になる |
| N03 | S1: batch の行検証を落とし、順序違いをそのまま採用 | 順序違い注入の負例が `landed` または誤 commit を証拠にする |
| N04 | S1: 打ち切り・parse 失敗を `indeterminate` でなく「候補なし」へ丸める (旧 M6) | 異常応答の負例が `indeterminate` にならない |
| N05 | S2: `_spool_exact_positive_decision` を `_regular_decision` へ差し替え | 未着地 spool の負例が `not-landed` になる |
| N06 | S2: exact の成功が receipt parse error を覆う | 壊れた registry の負例が `landed` になる |
| N07 | S1: `:` を含む path を `split(":")` で分解 | `:` を含む path の正例が証明できなくなる |
| N08 | S4: 未証明 unit の説明を出さない | S4 の正例が赤 |
| N09 | S4: 子 JSON を得られなかったときも「全 unit を説明できた」と書く | 欠落明記の負例が赤 |

**単一理由性 (F820)。** 各変異は実装後に、同じ入力を拒否する層が前後にも内側にも無いことを確認する。
確認できない変異は登録せず実効 gate へ再照準する。

## 6. 依頼が指した 4 commit の OID は回収できなかった

`/cleanup-branches` の当該実行は docs のみで insight dir を残しておらず、
`docs/archive/worklog-phase3-0915-1506.md` にも OID の記載が無い。
`docs/unreachable-object-ledger.md` は entry 0 件である。よって受入条件 3 は、**再現可能な固定 corpus**
(上記 2 branch と spool の正例・負例) に置き換える。この置換は insight に明記する。
