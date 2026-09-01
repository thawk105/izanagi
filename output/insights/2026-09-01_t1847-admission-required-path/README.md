# [T-1847] 受理記録の置き場所を driver ごとの要求 path 1 本に固定する

- wave: `dev-wave-t1784-admission-single-path`
- branch: `worktree-dev-wave-t1784-admission-single-path`
- 実装 anchor commit: `549ebfc9ee6cac8b4ec9aabd13aa521b1cb317fb`
- base main: `24014bdb259d971571f22b54a8f10a49352b825f`
- 裁定: D1050 (2026-08-26 ユーザー裁定)。設計判断は本 wave の decisions fragment。

## 何をしたか

B-4 pre-run admission record の検証器 `verify_b4_admission_record` に、
**解決後の repository-relative path が `driver_kind` に対応する要求 path と一致すること**を
要求する関門を 1 箇所だけ足した。内容が完全に正しい record でも、要求 path 以外に置かれていれば
受理しない。これにより「同じ record を複数の path に置いて実走後に都合のよい方を選ぶ」経路が閉じる。

関門の位置は `driver_kind` の閉集合検査より後、record bytes の読み込み・HEAD blob 照合・
schema 検査・文書 binding 検査より前である。前後どちらへずらしても既存の拒否署名が壊れるか
新関門の失敗署名が不安定になる。

## 依頼引数の前提が既裁定に覆されていた

依頼は主目的 (1) として「§5 残り 9 欄の型検査 (D1000)」を挙げていたが、
**D1332 (2026-09-01 00:09 JST land、ユーザー裁定) が「見送る」と決着済み**だった。
再訪条件「記入時の型の誤りが実際に 1 件観測されたとき」は成立していない。実装せず scope 外とした。
依頼文は archive worklog (990) の T-1784 本文をそのまま運んでおり、その本文が 2026-08-26 以降
更新されていなかった。

## 変異の実測

`mutation/` に spec と ledger を置く。runner は焦点 8 file、`--runner-mode dispatch`。

|変異|内容|期待|結果|失敗 node 数|
|---|---|---|---|---|
|M1|関門の条件付き `raise` を除去 (過小拒否側)|KILLED|KILLED|**1**|
|M2|関門の比較 `!=` を `==` へ反転 (過剰拒否側)|KILLED|KILLED|86|

- baseline PASSED、`matching` 2/2、MISMATCH 0、SURVIVED 0、TIMEOUT 0。
- **M1 の失敗 node は厳密に 1 件** (`test_verifier_enforces_driver_required_path`) で、
  関門の単一理由性が実測で確定した。前段の path 解決も後段の HEAD blob / schema / 文書 binding /
  projection も、正例と同一 bytes・同一 HEAD の record を通すため、落ちる理由は path 一致だけである。
- **M2 は 86 node へ波及するので過剰決定**であり、単独変異による単一理由性の証拠からは外す。
  受理集合を狭める wave が DW-M01 で要求する「承認外の過剰拒否」の検出力を示す広域対照として記録する。

### 事前登録の訂正 (erratum)

段 4 で親が登録した M2 は「mapping の `base` の値を `admission.json` へ差し替える」だったが、
段 6 レビュー A が「正例 fixture は要求 path に record を置くので、mapping を変異させると
enforcement テストの正例も落ちる」と指摘した。期待 node が不完全だったため、
DW-M07 の本走前 anchor 再検証に従って方向の違う 2 件へ差し替え、
全件 SURVIVED 期待の probe (`mutation/mutation-probe-spec.json`) で観測 node を集めてから
完全集合を持つ本走 spec を登録した。**初回登録は消さず本節に残す。**

## 実測した検査

|走|対象|結果|
|---|---|---|
|変更前 baseline|焦点 3 file|122 passed / rc=0 (request 963064.nqsv)|
|変更後|焦点 5 file|161 passed / rc=0 (request 963452 前の走)|
|変更後|焦点 8 file|643 passed / rc=0 (request 963452.nqsv)|

8 file への拡張は段 6 レビュー B の指摘による。shared fixture を経由する間接 consumer
(`test_p3_s4_loop.py` と sort / trigger 版) は参照検索でしか見つからない。

## この変更が閉じないこと (module docstring に逐語で書いた)

- 要求 path にある record の**内容**が正しいことは証明しない。
- この module の mapping が**事前登録された正本**であることは証明しない。
- driver をまたいで単一 path であることは証明しない。
- mapping や要求 path の record を書き換える commit は防がない。
- Git の外で先に結果を知ってから record を commit する経路は塞がない。

## ユーザーへ返す所見 (scope 外・実装せず)

`orchestrator/campaign/p3_b4_raw_record_producer.py` は admission sidecar の
`admission_record_repository_path` を driver の要求 path と照合せず、key の存在しか見ない。
他欄を保ったまま path だけ旧値へ変えた sidecar でも `protocol_ok` を満たせる。
certified 経路は sidecar bytes 全体を検証済み record から再構築した値と byte 比較するため閉じている。
本 wave の変更が作った欠陥ではない (変更前は要求 path 自体が無く、照合対象が存在しなかった)。
worklog fragment の新規項として裁定へ返した。

## 逐語

`verbatim/` に段 1 brief、段 2 プラン、段 3 の 2 レンズ、段 4 裁定、段 5 実装子報告、
段 6 の 2 レビューを置く。実装子は sandbox の scheduler socket 制約で pytest を実走できず
(rc=16)、緑を 1 件も主張していない。テストの実測はすべて親が計算ノードで行った。

## 受入を止めている host session pin 問題 (別 wave 所有)

本 wave の受入全走は、変更と無関係な決定的赤で止まった (詳細は上記「停止理由」ではなく本節)。
ユーザー指示により codex 2 レンズと相談して方針を決めたので、その結論を残す。
**実装は並行セッションが一本化して所有しており、本 wave は当該 file を 1 行も触っていない。**

逐語は `verbatim/host-pin-facts.md` (親の実測)、`verbatim/s3b-hostpin-sol.md`、
`verbatim/s3b-hostpin-luna.md`。

### 事実

`orchestrator/tests/test_codex_reasoning_ab.py:128` が `/home/SFC/tanab/.codex/sessions` を
絶対 path で pin し、`tools/codex_reasoning_ab.py:196-208` が 2026-07-29 の 5 session を
id と sha256 で pin する。**5 件ともホストから消えている** (`~/.codex/sessions/2026/` は 08 と 09 のみ)。
repo 内に写しは無い。赤は 21 error (fixture) + 5 failed (直接読み 4 + 間接解決 1) の 26 件。

赤化の時間窓は **2026-08-20 より後〜2026-09-01** (D585 が 08-20 に `benchmark_snapshots` を
使う node を実走している)。気づかれず居座った期間の上限は約 12 日。

### 相談で確定した拘束 (いずれも既裁定)

- **D315**: `_find_rollout` の `len(matches) != 1` の 5 行と rc を**不変に保つ**と凍結済み。
  いま赤を出しているのがその行である。**resolver を緩める修正は正しさゲートの弱体化**にあたる。
  同一性の錨は `ROLLOUT_SHA256` で、5 呼出はいずれも直後に `_verify_rollout_sha` を走らせる。
- **D1285 / D1245**: 歴史 pin を新しい session の値へ張り替えない (歴史記録の改変)。
- **D1154**: 環境の偶発的な件数・根の実在を可用性の代理に pin しない。
  現行ガードの `_HISTORICAL_SESSIONS.is_dir()` はまさにこの反パターンで、
  08/09 があるため真になり skip が発火しない。
- **D314 / D700 / D701**: 解除先が実際に到達可能でないテストは既に問題化されている。
  **正確な skip は緊急隔離としては妥当だが、恒久完了として扱うと抵触する。**

### 結論

- **緊急隔離**: 修正層は test 側の availability 判定に限る。可用の定義は
  (i) identity 一致の rollout がちょうど 1 件解決、(ii) bytes が pin された SHA と一致、
  (iii) 読取りと JSON/identity 検査が成功、の連言。
  **skip してよいのは exact zero-match だけで、duplicate・SHA 不一致・破損は赤に残す。**
  `_find_rollout` は full scan fallback で SHA 再検査なしに file を返しうる
  (`tools/codex_reasoning_ab.py:612-637`) ので、probe は戻り path へ
  `_verify_rollout_sha` を明示適用する。probe 自身の自己検査 node を常時実行で置き、
  「probe が壊れて常に missing を返す」変異を検出可能にする。
  受入結果には missing label と skip 数を明示し、「全被覆 green」と報告しない。
- **恒久解は正確な skip ではない。** 赤い 26 node の mutation・snapshot・replay 被覆は
  他 node が代替しておらず、恒久 skip は被覆を暗黙に消す (規律 2 に触れる)。
  一般的な性質は既存の合成入力 helper で常時実行 node へ移し
  (`:7154-7231`、`:3741-3838,4250-4390`、`:1142-1196`、`:8494-8572`、`:8951-9251`)、
  復元不能な「2026-07-29 の exact bytes 一致」だけを裁定対象として撤去するか
  historical audit と明記する。
- **族一般化はしない。** 射影範囲で独立した欠陥例は 1 件だけで、DW-G03 の独立 2 例は成立しない。
- **変更単位は独立 wave。** 本 wave (B-4 admission record) へ混ぜない。

### hold が取れない理由 (D1160 では解消しない)

D1160 は `evidence_id` の placeholder 表記を許し「F 番号は land 時の fold でしか生まれない」
循環を解くが、`flaky_test_holds.py:115` の `green_observation` 非空と `:135-139` の
`green_run_count >= 1` は別 field の別 validator として残る。
**この 26 件は一度も緑になっておらず、正直に埋められる緑の観測が無い。**
緑の観測を捏造すれば登録は通るが、それは規律 2 が禁じる方向そのものである。
