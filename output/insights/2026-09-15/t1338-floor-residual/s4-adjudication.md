# 段 4 裁定 — [T-1338] 床値依存の残件

基底 local main `0600887d92538b3f34d894f9674d202d0a29a578` (段 4 直前に再照合。wave 開始後の
main 進行は 0 commit)。

## 裁定 0 — 本 wave は実装しない (4→7→8→9)

段 2 (プラン) と段 3 の 2 レンズが独立に同じ結論へ到達した。**T-1338 に、実装可能で授権された
残作業は存在しない。** 依頼が名指しした 3 述語は D1985 で撤去済み、台帳が言う残件 R1〜R3 は
いずれも撤去授権が確認できない現用経路である。実装面差分ゼロのため `DW-S04` により変異 matrix を
免除する。**受入全走は免除しない。**

## 裁定 1 — 親 brief の断定を 5 点訂正する (所見はすべて real、採用)

| # | 所見 | 出所 | 裁定 |
|---|---|---|---|
| J1 | D811 の却下選択肢が禁じるのは「床値を空のまま `floor-null` の拒否だけを個別に解く」案に限られる。R2・R3 へ拡張できない | 段 2、段 3-A1 | **real・採用。** brief (P1-a)(P1-d) を訂正する。R1 の残置根拠は **D1985 の「残すもの」**に置く |
| J2 | D501 決定 7 の留保 (条件 3 は逐語凍結、再裁定が要る) は **D510 (2026-08-18 ユーザー裁定) が既に解決済み**。現行 `s8b_verdict` は床値を選択条件の値比較に使わない | 段 3-A2 | **real・採用。** 親が一次資料で裏取りした (D510 決定 1 が「最終判定から対象別 between-run floor との比較を撤去」「消える保証 4 件 (床値超・scale adequacy・oracle の一意最大・両構成の eligibility)」を名指し)。brief の「確定済みユーザー裁定」から D501 決定 7 の留保を外す |
| J3 | R3 のアンカー `s8b_oracle_report.py:2548` は assertion 1 行であり、「解決経路」全体は :2547–2560 (consumer 引渡しまで含めれば :2563) | 段 2、段 3-A、段 3-B | **real・採用。** 撤去単位としては両者が別物であり、成果物影響も異なる |
| J4 | 「R1〜R3 の撤去はいずれも受理集合を広げる」は未立証。局所述語の削除・経路の破損・最終受理集合の拡大は別物 | 段 2、段 3-A5、段 3-B | **real・採用。** R1 は manifest 側 (`s8b_oracle_manifest.py:603–606`) にも独立した null 拒否が残る。R2 は loader 呼出しだけ消すと limits 供給が壊れる (受理拡大ではなく実行破壊)。R3 は撤去範囲自体が一意でない |
| J5 | 床値系列 (D1758〜D2013) の存続だけでは古い撤去要求の失効を証明できない。D1985 自身が床値系列と共存しながら 3 述語を撤去している | 段 2、段 3-A3 | **real・採用。** 本 wave の根拠は「具体的な残置文 (D1985)・現用 consumer の実在・追加授権の不在」に置き直す |

## 裁定 2 — 不在の主張の範囲を訂正する (段 3-B、すべて real・採用)

親 brief の件数は `orchestrator/` 配下の Python に限った測定だった。repo 全体の件数として
読める書き方をしていた点を訂正する。

| 対象 | 親 brief の記述 | 訂正後 (段 3-B 実測) |
|---|---|---|
| `perf_sha_by_cell` | 「0 件」 | tracked file に **6 行** (`docs/decisions.md:59973`、前 wave の裁定・逐語記録)。**production の残存は 0 件** |
| `floor_budget_snapshot_sha256` | 「負例テスト 1 件だけ」 | tracked file に **17 行** (docs/archive 4、Python 負例 1、insight md 8、insight JSON 4)。**JSON の実 key としての一致は 0 件** (再帰走査で確認)。`output/s8b-freeze` の JSON 12 件と `output/s8b-freeze-budget-approvals` の 1 件にも不在 |
| `expected_perf_sha256` の production 供給元 | 「0 件」 | **維持。** `pipeline.evaluate` の production caller 5 箇所 (`loop.py:782`、`screening_driver.py:639`、`s1_direct_comparison.py:1233`、`s8b_oracle_driver.py:1783`、`qualification/t126_driver.py:543`) のいずれも具体的期待値を供給しない。`**kwargs` 転送 (`pipeline.py:2723–2725`) も入口 `evaluate_options` に旧期待値が無い。**動的呼出しまで排除する全称証明ではない** |
| approved spec | 「live な成果物は存在せず official は fail-closed」 | **成果物不在は維持** (`APPROVED_SPEC_SHA256 = None`、`git ls-tree -r HEAD -- output/s8b-oracle-spec/reviewed_spec.json` の **stdout 空**を親が確認)。ただし「official は必ず `no-approved-spec` を返す」は広すぎる。別の前提条件が先に拒否しうる |

## 裁定 3 — 「本 wave は凍結 bytes を変えない」は維持、「撤去しても影響先なし」への拡張は却下 (段 3-B、real・採用)

実装なしのため本 wave が変える凍結 bytes は無い。しかし **仮に R3 を撤去した場合**の pin 閉包は
空ではない。次 wave のために記録する。

- **file 全体 SHA-256**: `s8b_oracle_report.py` は `generator_versions` の対象
  (`s8b_oracle_manifest.py:67`、:458–496 が source bytes を照合)。現 hash は
  `30fe2b1bcad143f5a85ca32250744522d6049f4c71e9b853618e3af2dd0091c7`。
- **行番号**: `orchestrator/tests/test_ccbench_spawn_sites.py:2959–2964` が
  `s8b_oracle_driver.py` の `run_block` 評価行 **1783** を `_BuildSink` の literal で pin する
  (親が現物で確認)。R1・R2 呼出しを行ごと消せば参照がずれる。**前 wave が実際に赤にした型**である。
- **正規表現・文字列アンカー**: `test_s8b_budget.py:72` の `match="null"`、
  `test_s8b_oracle_driver.py:1609` の prefix と :2330–2331 の literal。
- **派生 digest**: `test_s8b_oracle_manifest.py:92–93` の golden spec に report hash が埋まり、
  :63–65 の `PIN_GATE_SPEC_SHA256` へ波及する。再生成 manifest では
  `generator_versions` → `manifest_id` → manifest digest → budget ledger 束縛
  (`s8b_oracle_driver.py:1581–1586`) まで鎖が続く。**既存の凍結 JSON が source 編集だけで
  書き換わる意味ではない。**

## 裁定 4 — refuted 所見 2 件

| # | 所見 | 裁定 |
|---|---|---|
| J6 | R1〜R3 を残すこと自体が D496 決定 1 (凍結した過去値を比較の基礎にしない) に違反する | **refuted。** R1 は floor/budget の存在条件、R2 は freeze の budget を今回の資源上限へ射影、R3 は批准床値の選択規則と公開証拠の再検証であり、いずれも過去 throughput との比較ではない。D510 と現行 verdict が反証する |
| J7 | 実装なしで返すこと自体が絶対規律 2 に反する (緩んだ門の放置) | **refuted。** 新たな anomaly 受理も verifier の迂回も立証されていない。消えた保証は D510 と D1985 が明示的に承認した変更である。**受理集合の拡大一般と、anomaly を見逃す正しさ検証の弱体化は同義ではない** |

## 裁定 5 — D811 の「門が守っていた性質」の射程を明記する (段 3-A6、real・採用)

`s8b_oracle_driver.py:524` の条件は `freeze.get("floor") is None` だけを見る。**床値が official
由来であること・正値であること・pair 内部整合・性能差が床値を超えることは検査しない。**
したがって D811 の「門が守っていた性質」は、

- 「null を拒む性質」と読むなら現に実装されている。
- 「正しい official 床値を保証する性質」と読むなら、この 1 条件だけでは達成されない。

本 wave はこの区別を記録するだけで、どちらの読みも採らない (どちらを採るかは裁定事項)。
null 条件自体は恒真ではない。ただし実行経路では manifest 側の別拒否と重複する。

## 裁定 6 — T-1338 の扱いは「内容を訂正した裁定待ち」とする (段 3-A8、採用)

**閉じない。** scope 外だった事実は、不要と裁定された事実ではない。次の一手の carry 本文を、
測定した事実へ書き換える (完了扱いにはしない)。**撤去要求そのものの取下げはユーザー裁定へ返す。**

## 変異事前登録 (DW-M01)

**実装面差分ゼロのため変異 matrix を免除する** (`DW-S04`)。登録する変異は無い。
恒真な登録を避ける `DW-M01` / F28 の趣旨にも従う — 本 wave は production の述語を 1 つも
足さないため、殺すべき新設 gate が存在しない。**受入全走は免除せず段 7 の記録前に実走する。**

## 成果物と段の経路

`4→7→8→9`。段 5・6 を飛ばす。成果物は本 wave の insight 一式と `docs/spool/` の fragment
(worklog・decisions・failures)。実装面の差分は 0 byte。
