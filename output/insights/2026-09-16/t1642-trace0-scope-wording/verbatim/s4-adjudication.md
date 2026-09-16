# 段 4 裁定 — [T-1642] TRACE=0 検査の射程文言を「必要条件の一つ」へ統一する

基準: local main 9d52ef1459fdae5bc97050155b28fce0601d259f。
入力: s1/brief.md, s1/anchors.md, s2/plan.md, s3/lens-a.md, s3/lens-b.md。

## 1. 所見の裁定

| # | 所見 | 判定 | 採否 | 根拠 |
|---|---|---|---|---|
| A-1 | 親の「不在の実測」が検索語の件数と意味判定を混同 | real | 採用 (記録側) | `docs/pegasus-runbook.md` の `checker` は別 tool。件数は「当該 checker の保証範囲を述べる記述」に限定して書き直す |
| A-2 | `tools/pegasus/mocc_trace_pilot.sh:357` と `:426` の `Certifies the TRACE=0 preprocess identity gate.` が artifact classification manifest へ出力される live な成果物文言 | real | **採用 — 編集対象 A7 として追加** | 実測: 生成側 2 箇所のみ (`write_artifact_classification_manifest` の共通枝と `t1943_g2` 枝)。validate 側 (`:510-545`) は schema・trace_mode・enum・entry key 集合だけを見て `reason` の literal を見ない。repo 全体で `Certifies the TRACE=0` は上記 2 行のみ、test に literal pin 0 件 |
| A-3 | `output/insights/2026-08-11/t816-fn2-trace-v2/README.md:38` の「規律 1 (TRACE=0 側の等価性)」見出し下に pass を置く実例 | real | **不採用 (対応不要)** | 同 README `:120-121` が「checker の保証も『翻訳単位の同一性』ではなく『選定した macro context における…』に限定して名乗る」と既に明記。レンズ A 自身も「完全除去を証明したという断言の発見とは扱わない」と認定。過去 insight は当時の記録で、規律 7 により遡及改変しない。裁定パッケージへ 1 項目として返す |
| A-4 | A2〜A5 の非編集論法は本文に耐える | real | 採用 (非編集を維持) | `:38-41` は限定保証名、`:62-63` は失敗の説明、`:421-425`/`:539-541` は局所例外の説明。いずれも「通れば規律 1 が満たされる」と読ませる文ではない |
| A-5 | A1/A6 はコメントで成果物に出ないため、将来の執筆者に届かない | real | 採用 | A7 の追加でこの穴が実質塞がる (manifest は成果物 JSON)。加えて本 wave の insight に統一文言を載せる |
| A-6 | 別防壁・D774 への越境はない | real | 採用 (scope 外維持) | D780 決定 2・3 に従う |
| B-1 | A1 は D297 の compiler 依存留保を具体化していない | real | 採用 (1 文追加) | D297 は「複数 compiler で走らせ admission toolchain と同一であるとは主張しない」と留保する。docstring の読者が D297 全文を読む保証はない |
| B-2 | A6 の英訳に強弱のずれはない | real | 採用 (段 2 案を維持) | `proves` の目的語が D297 guarantee に限定され、`does not prove that removal` が付く |
| B-3 | 親の pin 一覧に漏れ (checker bytes は pilot `:1751` が SHA 採取、pilot bytes は `submit_mocc_trace.sh:319` が採取、過去 receipt `output/insights/2026-08-26_mocc-trace-pair-receipt.json:90,123` に現 checker SHA が literal で記録) | real | 採用 (記録側) | 過去成果物は変更しない。再計測もしない (測定は当時の道具で得た事実であり、現行コードとの差だけでは無効にならない = 規律 7)。将来の実行が新 bytes に対応する束縛を生成する |
| B-4 | 予定編集で壊れる固定行番号 pin は確認できず | real | 採用 | ただし「未知の派生 digest を含む全 pin の不在証明ではない」という留保ごと記録する |
| B-5 | AST 比較は文言の妥当性を検査しない | real | 採用 | 承認済み文案との全 bytes 比較を主検査、AST 比較を補助とする |
| B-6 | 焦点走 4 file に追加漏れなし (間接経路 2 段を確認) | real | 採用 | `test_check_trace0_preprocess_identity.py`, `test_mocc_trace_job_contract.py`, `test_mocc_trace_pair.py`, `test_hooks.py` |
| B-7 | 実行ロジックの変異 matrix を新設する意味はない | real | 採用 (下記 3 節の形で) | |

## 2. プラン v2 (実装する内容)

編集は 2 file・3 アンカーに限る。**checker の受理集合・拒否条件・report の JSON 構造を 1 bit も変えない。**

- **A1** `tools/check_trace0_preprocess_identity.py:3` — module docstring を置換する。既存 1 行を保ち、
  D780 決定 1 の逐語と、解釈の禁止、D297 の compiler 留保を続ける。
- **A6** `tools/pegasus/mocc_trace_pilot.sh:1742-1743` — 既存 2 行の英語コメントを保ち、
  D780 決定 1 を英語で言い換えた 2 行を続ける。
- **A7** 同 `:357` と `:426` — `reason` 文字列 `Certifies the TRACE=0 preprocess identity gate.` を、
  完全除去に対して必要条件の一つでしかないと読める形へ置き換える。**2 箇所は同一文字列にする。**
- **非編集**: A2 (`GUARANTEE` 定数)、A3 (`CheckError` docstring)、A4 (`:421`)、A5 (`:539`)、
  checker report の schema・field 集合、過去の insight・receipt・台帳。

## 3. 変異事前登録 (DW-M01)

**登録する変異はゼロ。免除ではなく「登録可能な変異が存在しない」ことの記録である。**

DW-S04 の免除条件 (実装面の差分ゼロ) には当たらない — 本 wave は `tools/` 配下 2 file を変更する。
しかし DW-M01 は「同じ入力を拒否する層が前後にも内側にも無く赤理由が一つに絞れる」変異だけを
登録することを求める。本 wave の差分は文言だけであり、その文言を守る実効 gate は repo に存在しない
(manifest の validate は `reason` の literal を見ず、test も文言を pin しない)。
文言を「十分条件」へ書き換える変異を作っても、殺す gate が無いので SURVIVED にしかならない。
その gate を新設することは D780 決定 1 (文言の統一) と依頼の scope 外である。
この判断は段 6 の敵対レビュー 2 本に検査させる。

## 4. 受入と検査

- 焦点走 4 file (B-6)。
- 受入全走 `python3 tools/dev_wave_wait.py acceptance -- python3 tools/run_tests.py`。
- 非緩和の確認: 承認済み文案との全 bytes 比較を主検査、module docstring を除く AST 一致を補助検査。
  どちらも一回限りの確認であり、repo へ新しい検査 file を足さない。

## 5. 裁定パッケージ (ユーザーへ返す・本 wave では実装しない)

1. **過去 insight の見出しと結果の引用**: `output/insights/2026-08-11/t816-fn2-trace-v2/README.md` は
   §3.1「規律 1 (TRACE=0 側の等価性)」の見出し直下に checker の 3 本 pass を置く。同文書 §5 が保証を
   限定して名乗るので断言ではないが、見出しと結果だけを引用すると射程を過大に読める。
   レンズ A は日付つきの追記訂正を推奨した。親は「過去の判定は追記でのみ訂正する」(規律 7) の
   範囲内だが D780 決定 1 が求める「成果物側の文言の統一」の対象外と裁定し、実装しない。
   ユーザーが追記を求めるなら次 wave で 1 行追記として閉じられる。
