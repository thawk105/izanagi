指定資料を読んだ静的レビューです。実装・試験・実 trace の再実測は行っていません。

以下、`plan` は [s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-v3-existence/codex/s2-plan.md)、`brief` は [s1-brief.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-v3-existence/s1-brief.md)、コードの短縮名は `orchestrator/verifier/` 配下、試験は `orchestrator/tests/test_verifier.py` を指します。

### B1 — must-fix：cycle の優先順位変更は撤回する

**根拠:** plan:43,180,247、`model.py:551`、`docs/decisions.md:71524`。D2224 は cycle を従来どおり non-serializable として返すと明記しています。依頼逐語には、この優先順位を変更する指示はありません。設計 §6.1 の genesis 誤用も、cycle の control ではなく integrity の試験です（設計 README:252）。

存在違反を cycle より前に判定する必要はありません。現行の `certified` は `serializable and integrity.clean()` なので、新件数を `clean()` に足せば非認定になります。

**修正案:** `VerifyResult.verdict` を変更しない。brief の完了条件(a)を「非巡回の存在違反 fixture は indeterminate」と明確化する。cycle 併存例は non-serializable・非認定・存在件数正を期待し、優先順位変更を殺す変異は削除する。

**放置時の成果物への影響:** 認定集合は変わらない一方、既に検出した cycle の verdict が non-serializable から indeterminate に変わる。

### B2 — must-fix：P1 は設計から導ける同値条件ではない

**根拠:** brief:22,38、plan:11,253、設計 README:83、単位4記録 README:117、`docs/decisions.md:71537`。

設計は「**初期に無く、かつ**最初の committed write が INSERT」と述べています。brief はこれを「最初の write が I **なら**初期不存在」に強めています。また、書込みがない key の genesis 読みを初期存在とする規則も追加しています。plan は推定と認めていますが、brief の「§3.3 の規則で決める」という表現とは一致しません。

同じ W/R 列から、初期存在 key への不正な最初の I と、初期不存在 key への正常な I は区別できません。未書込み key の genesis 読みでも同様です。

**修正案:** 親裁定で「段1は完全な committed trace と W op の意味に基づく初期存在の推定契約を採用する」と明示し、「初期ロード集合を検証した」とは書かない。この契約を採らないなら、指定入力だけで完了とはできません。単位7の一覧や新 gate を黙って追加する修正は不要です。

**放置時の成果物への影響:** 推定契約上の certified が、実際の初期キー集合との整合まで証明した certified と誤解される。

### B3 — must-fix：完了条件(c)には実装後の API 実測が必要

**根拠:** brief:8–12,25–26、plan:243、`core.py:56`, `core.py:68`, `model.py:77`, `model.py:490`, `model.py:560`。

静的には、印以外に **v3 を一律に止める条件はありません**。ただし認定には、非空・非巡回・各 integrity 正常・X/P の source assessment 充足が必要です。commit witness は指定した場合に一致が必要で、現コードは未指定を一律拒否してはいません。I の proof surface は認定必須条件ではありません。

親の「違反0件」は実装の呼出し漏れを検出できません。実 trace は D がなく、INSERT 対象表への R もないため、存在検査が丸ごと無効でも同じ結果になり得ます。

**修正案:** 実装後の checkout から、指定 trace に公開 `verify_trace_dir` を実行し、実 source context・外部 commit 数を渡して `certified=True` を確認する。probe 内の再実装規則、field の差替え、synthetic proof source で代用しない。使用 commit・引数・結果を既存の成果記録に残せば十分です。repo 外 probe は結合確認として使えますが、repo 内の正負例・変異の代替にはできません。

**放置時の成果物への影響:** 実装後の認定到達が未確認のまま、完了条件(c)だけが達成済みになる。

### B4 — should：指定版を読む規則の正例が足りない

**根拠:** plan:23–33,169–178、`dsg.py:659`。

計画は「指定された版の存在を見る」と正しく定めていますが、試験表には「後で DELETE された key の古い live 版を読む」正例がありません。最新 op だけで読む実装でも、多くの予定例を通過します。

**修正案:** 既存の valid-histories 群へ次の対を追加する。

- `I@v1 → D@v2`、別取引が `R(v1)`：存在違反0、非巡回になる構成で certified。
- 同じ R を `R(v2)` に変更：存在違反1、indeterminate。

読み手の commit が D より後でも、既存 DSG が読み手を D より前へ直列化できる構成にする。新しい時刻規則は足さない。

**放置時の成果物への影響:** 最新状態と指定版を取り違えた実装が、正常な履歴を余分に非認定にする可能性が残る。

### B5 — should：変異は入口と各条件へ分け、等価正例を別枠にする

**根拠:** plan:212–225、単位4記録 README:80–97。

全件0になる欠陥は、予定されている**独立した件数期待**が実装されれば検出できます。経路一致だけでは、全経路が同時に0になる欠陥を検出できません。

変異候補には次の修正が必要です。

- compact 入口の呼出し削除に加え、object 入口の呼出し削除を入れる。
- P3 全削除だけでなく、I・U・D の条件削除を個別に照準する。全削除の kill は各条件の検出力を証明しない。
- 「tid順**または**txid順」は別変異として確定する。
- B1 の優先順位変異を削除し、B4 の「指定版を最新 op に置換」を入れる。
- 同版異種 op の任意選択は、I/D をどちらへ潰すか明記する。I 選択でも D 選択でも結果が変わる対照が必要。

**等価変異の正例は1つ入れるべきです。** 例えば版 tuple の `sorted(vs)` を `sorted(vs, key=lambda v: (v[0], v[1]))` にする。これは SURVIVED が期待値です。brief:12 の「全部 kill」は「非等価の故障変異を全部 kill」に直す。

**放置時の成果物への影響:** kill 数を満たしても個別条件の抜けを見逃す、または正常な等価変異の生存を失敗扱いする。

### B6 — should：詳細の全件ソートと試験の総当たりを縮める

**根拠:** plan:56–64,83–97,184–193,235–241、brief:33,41–43。

共通検査＋薄い二 adapter は妥当です。P3 も同じ存在状態の局所検査であり、直ちに scope 外とは判断しません。同版異種 op も、parser が保持し既存 `version_dups` が拾わない実在の入力面です（`parse.py:428`、`dsg.py:364`）。任意選択による認定を避ける処理は残すべきです。

一方、以下は縮小できます。

- 構造化詳細は必要ですが、`read_index` を含む全詳細の追加ソートは必須ではありません。winner の txid 順と frame 内順を使う決定的な収集で足ります。
- 各意味例の全経路総当たりを避け、意味例は基本経路、各違反種を含む代表 fixture は全経路で確認する。
- overflow と実 worker 終了の既存試験へ存在違反 fixture を追加し、fallback harness を複製しない。
- 手動 legacy helper に workers=2 を渡すだけでは並列経路の証明になりません（試験:3418–3421）。
- 未書込み・自己版・順序・表分離はデータ表でまとめる。

**修正案・上限:** 追加＋削除合計で production **250行**、試験 **300行**、合計 **550行**を目安の上限とする。新規 test 関数は **8本以内**、意味 fixture は **20ケース以内**、代表 fixture の経路反復は別計数。これは静的見積りであり、超過時は削る検査ではなく増えた理由をレビューする。

**放置時の成果物への影響:** 認定集合は改善せず、変更面・試験時間・診断仕様の維持負担だけが増える。

### B7 — should：印の撤去後に死ぬ schema 判定と import が未列挙

**根拠:** `rg` で `orchestrator/`・`tools/` の Python を実検索した結果、印・旧 note の直接参照は次が全件です。

| 箇所 | 内容 |
|---|---|
| `model.py:487,506` | field、`clean()` 条件 |
| `core.py:64,66,67` | field 設定、旧 note の2行 |
| `test_verifier.py:3714` | 旧試験名 |
| `test_verifier.py:3726,3730,3755,3779` | field 参照 |
| `test_verifier.py:3729` | 旧 note の期待 |

これらに加え、`core.py:42,50` の `is_v3` は旧印分岐だけで使用され、`core.py:18` の `TxnV3` もその判定だけで使用されています。plan の削除表にはこの残骸がありません。

**修正案:** 新実装で使わなければ `is_v3` の両代入と `TxnV3` import も削除する。`result_to_dict_v3` の docstring（`core.py:202`）は「anomaly witnesses のみ拡張」から存在詳細も含む説明へ更新する。

repo 全体の検索には `docs/decisions.md:71524`、`docs/worklog.md:729,2008`、単位4 README:47,118 と過去の変異記録も出ます。これらは過去の判断・実測記録なので削除対象にせず、新成果記録で撤去を説明する。

**放置時の成果物への影響:** certified の判定は変わらないが、不要な schema 判定と古い出力契約の説明が残る。

### B8 — should：既存期待値の変更は U 正常例だけに限定する

**根拠:** `test_verifier.py:3698–3779`、plan:195–206。

既存 v3 試験で、印だけを理由に indeterminate を要求している箇所は次のとおりです。

| 既存期待 | 撤去後 |
|---|---|
| `3718` の U＋U版読み → `3725` | serializable verdict・certified へ変更可 |
| 同 U ケースの capability → `3737,3738` | certified・serializable verdict へ変更可 |
| I＋genesis 読み → 同じ assertions | indeterminate 維持、新違反へ帰属を置換 |
| D版読み → 同じ assertions | indeterminate 維持、新違反へ帰属を置換 |

他の indeterminate 期待は変更しません。X/I 違反（`3707`）、壊れた framing（`3773`）、空 trace（`3778`）には独立した非認定理由があります。`3494` の serial-tables 試験は D版を3表で読むため、純グラフ事実の `serializable=True` を維持しつつ、存在件数3・非認定を確認すべきです。

**修正案:** 上表を期待値変更の限定表として採用する。I/D 負例は件数と構造化理由を確認し、1行修正した正常対照を併置する。v2 の3例と既存 golden は維持する。「serializable」という語は verdict と純グラフ属性を区別して記述する。

**放置時の成果物への影響:** 一括した期待値変更により、存在違反や別の integrity 違反まで認定対象へ緩めるおそれがある。

## 総括

- 現 plan は B1〜B3 の修正前には承認できない。
- 印の撤去後、条件を満たす v3 が certified に届く静的経路はある。
- cycle 優先順位を変える必要はなく、D2224 の既存契約を維持する。
- P1 は初期集合の検証ではなく、段1の明示的な推定契約として裁定する。
- 共通存在検査、P3、同版異種 op の非認定処理は局所的に実装できる。
- 実 trace の違反0件は検出力の証拠にならず、repo 内の正負例・変異が必要。
- 旧印の直接参照に加え、`is_v3`・`TxnV3` の死んだ参照も撤去する。
- 実装後の API 実測と試験結果は未確認であり、親の検証で完了を確定する。