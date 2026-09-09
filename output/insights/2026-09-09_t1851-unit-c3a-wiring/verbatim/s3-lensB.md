## 総括

plan はそのままでは実装へ渡せない。案 a は current v2 の受理集合を明確に広げ、D1660 の単調縮小方針と衝突するため、案 b が安全側である。  
負例 11 件のうち、competing marker、planned `retry_ordinal=None`、値域 receipt の 3 面は、実体を名指しした kill test になっておらず、変異が生存しうる。  
C3a は unlanded checkpoint なら死んだ gate ではないが、v5 result は D2 前には ratified/holdout freeze へ到達不能であり、単独 land は不可。  
whole-file SHA-256 pin 0 件は検算できた一方、AST・公開 API・consumer key-set の pin 列挙には抜けがある。pytest、campaign、性能測定は実行していない。

## 所見 B-1 — 案 a は受理集合を広げる

**real、[実測]**

現 consumer は completed session の `probe_before.competing=True` と marker の共存を拒否する。`orchestrator/campaign/s8b_holdout_admission.py:6577-6582,6733-6741`。一方、launcher は registry reserve を probe より先に実施するため、v2 marker が必要になる。`orchestrator/campaign/s8b_floor_attempt_launcher.py:569-584,981-997`。

案 a は、現在拒否される「current v2、pre-probe competing、marker あり」を新たに受理するため widen である。plan 自身も受理集合変更と認識している。`out-s2-plan.md:12-16`。

D1660 の直接対象は旧世代 token だが、「受理集合は狭まる方向にしか動かない」という明示方針には逆行する。`docs/decisions.md:50849-50858`。旧 token の再入口ではないため形式上まったく同じ対象ではないが、新たなユーザー裁定なしに許された変更とは読めない。

成果物影響: current v2 の live inspector が従来拒否した proof chain を受理する。

推奨: 案 a は採らず案 b を選ぶ。案 a を残すなら、単なる「v2 marker」ではなく launcher reservation 由来を区別できる権威を示した上で、D1660 との関係を裁定へ返す。

## 所見 B-2 — 案 b は artifact 受理集合を広げない

**refuted、[実測]**

二段化は probe を先に行い、非 competing の場合だけ marker を発行して registry reserve へ進める案である。これなら既存 consumer の行列、すなわち competing は marker なし、非 competing は marker ありを保存できる。`s8b_holdout_admission.py:6733-6741`。

artifact の受理集合は保存される。代わりに、launcher API の呼出可能形は continuation/capability を要求する分だけ狭まる。現在 production caller は 0 件なので、既存 production artifact を新たに拒否する変更でもない。`contract-v3.1.md:455-459`。

成果物影響: proof-chain consumer の規則を変えずに production 配線を可能にする。

推奨: 案 b を優先し、API 二段化後も certified wrapper が registry や recorder を caller へ露出しないことを維持する。

## 所見 B-3 — competing marker の負例は実体を束縛していない

**real、[実測]**

負例は「新設する admission の対になる正例・負例の片方が赤」としか書かれておらず、test node、呼ぶ consumer、依存先が不明である。`out-s2-plan.md:325`。

現存する近い検査も端から端ではない。

- holdout 側正例は synthetic `_inspection_case` と root patch を使う。`orchestrator/tests/test_s8b_holdout_admission.py:3998-4006`
- launcher 側 competing 正例は `_owned_post_probe` と `_PRODUCTION_DEPENDENCIES` を monkeypatch する。`orchestrator/tests/test_s8b_floor_attempt_launcher.py:1977-2007`

したがって、実 inspector を広く「current v2 marker なら全部許可」に変異しても、別 helper や stubbed fixture に置いた対だけが赤緑を示し、実変異が生存しうる。

成果物影響: 案 a/b の境界を間違えた実装でも、負例台帳上は kill 済みと誤記できる。

推奨: 選択案ごとに `launch_floor_attempt()` が作った durable state を実際の `inspect_floor_holdout_admission_evidence()` へ渡す正例・負例を名指しする。両関数と registry/marker 権威を stub しないことを条件にする。

## 所見 B-4 — planned `None` を拒否し続ける変異が生存する

**real、[実測]**

plan の具体名つき node は retry 側の `test_campaign_retry_binds_v2_measurement_ordinal` だけである。`out-s2-plan.md:300-312`。負例側は planned と retry をまとめて「対になる正例・負例」としか書いていない。`:326`。

現実装は `_campaign_plaintext()` で `retry_ordinal` を必ず非負整数に限定し、planned の `None` を拒否する。`orchestrator/campaign/s8b_terminal_evidence.py:760-768`。既存 fixture も `kind="retry"` かつ `slot_id[4]` を使う。`orchestrator/tests/test_s8b_terminal_evidence.py:144-165`。

よって「retry は `slot_id[3]` に直すが、planned `None` は引き続き拒否する」変異は、名指し済み retry node を通過できる。

成果物影響: planned session の sealed terminal が構築不能なまま C3a を完成扱いできる。

推奨: planned の `None` を同じ terminal evidence 実体へ通す正例と、planned の非 null を拒否する負例を別 node として名指しする。retry 側は measurement ordinal と recovery ordinal が異なる fixture にする。

## 所見 B-5 — 値域 receipt の fake 混入変異には production の変異対象がない

**real、[実測]**

plan は `test_gate_input_receipt_requires_default_production_path` を挙げる。`out-s2-plan.md:264,323`。しかし C3b はコードを所有せず、receipt は実 campaign 後に作る非 pytest 成果物とされている。`:142,235-239,312`。production receipt builder または validator の変更計画はない。

このままでは test-only helper を検査するか、まだ存在しない固定 artifact を検査するしかなく、実際に作成された receipt への fake 混入変異を殺せない。

成果物影響: pytest の kill 実績と、C3b receipt の真正性が対応しない。

推奨: この項をコード変異 kill と数えない。C3b の実 receipt と実 artifact の path、SHA-256、件数、値を直接突合した非 pytest evidence として扱う。

## 所見 B-6 — C3a checkpoint は死んだ gate ではないが、単独 land は不可

**refuted、[実測]**

D1114 が禁じるのは production caller 0 件の機構を先行 land すること。`docs/decisions.md:37608-37621`。C3a 後は default campaign が launcher を呼び、v5 proof を production self-check へ渡す計画なので、発火 path 自体は生じる。`out-s2-plan.md:82-86`。実行入口も `tools/pegasus/submit_floor.sh` と名指し済み。`s1-brief.md:44-48`。

さらに branch は全単位が揃うまで land しない checkpoint と明記されている。`s1-brief.md:3-4`。したがって、C3a だけが一時的に branch 上にあること自体は D1114/D1341 違反ではない。

ただし、C3a を単独 land すれば **real** な違反になる。D1194 は writer-only land を恒真な保証として却下し、D1341 は配線と前向き proof-chain 束縛の同時 land を要求する。`docs/decisions.md:39827-39845,42839-42855`。

成果物影響: C3a は「実装 checkpoint」であって「実 campaign で発火確認済み」または「land-ready」とは名乗れない。

推奨: C3a/C3b を別 checkpoint にしても、同じ最終 land 集合に残す。C3b receipt 完了前に C3a を完成・着地扱いしない。

## 所見 B-7 — producer v5 と freeze consumer v4 の一時的不整合は実在する

**real、[実測]**

`PRODUCTION_RESULT_SCHEMA` の追加だけでは、ratified consumer は v5 を読まない。

- ratified は `result_keys_for_mode()` の schema 引数を省略して v4 keys を要求する。`orchestrator/campaign/s8b_ratified_freeze.py:2352-2375`
- 続いて `document["schema"] == RESULT_SCHEMA`、すなわち v4 を要求する。`:2393-2409`
- 実際の holdout freeze も schema 引数なしの v4 exact keys と `RESULT_SCHEMA` を要求する。`orchestrator/campaign/s8b_holdout_freeze.py:1431-1442`

一方、`s8b_floor_stats.py` は artifact schema から v4/v5 を分岐し、v5 では `attempt_registry` の exact proof と独立 inspector 値を要求する。`orchestrator/campaign/s8b_floor_stats.py:753-819,1155-1193`。

成果物影響: C3a/C3b の v5 result は自己検査できるが、D2 前には holdout/ratified freeze の入力になれない。

推奨: 二重 alias は unlanded checkpoint 内では維持可能。ただし D2 consumer/fixture を同じ最終 land 集合へ含め、C3 単独で certified 到達を主張しない。

## 所見 B-8 — `s8b_holdout_admission.py` が v4 result を黙って読む、は誤り

**refuted、[実測]**

`s8b_holdout_admission.py` は top-level result schema の consumer ではない。ここでの exact key 検査は、current/legacy generation に応じた attempt-ledger row の schema と key setである。`orchestrator/campaign/s8b_holdout_admission.py:6755-6774`。

この inspector が作った receipt を `s8b_floor_stats.py` が result 検証へ使う。したがって「holdout admission が v4 のまま producer v5 を黙って受理する」という不整合はない。実際の v4 固定 consumer は `s8b_holdout_freeze.py` であり、そこで hard reject される。

成果物影響: 不整合は silent acceptance ではなく fail-closed な到達不能として現れる。

推奨: consumer 表では `s8b_holdout_admission.py` と `s8b_holdout_freeze.py` を分けて記載する。

## 所見 B-9 — pin 閉包の列挙に抜けがある

**real、[実測]**

path 名の単純検索ではなく、AST・signature・exact set を読むと少なくとも次が未列挙である。

- live verifier 内の比較を AST で 1 件に pin し、caller を campaign、holdout freeze、ratified freeze の exact 3 file に固定する。`orchestrator/tests/test_s8b_floor_stats.py:1603-1629`
- certified launcher が registry/recorder を公開せず、固定 sealed recorder を使うことを signature と source で pin する。`orchestrator/tests/test_s8b_floor_attempt_launcher.py:2221-2230`
- holdout inspector の公開 signature 12 引数を exact pin する。`orchestrator/tests/test_s8b_holdout_admission.py:3727-3742`
- ratified fixture の result key setを schema 省略時の v4 contract に pin する。`orchestrator/tests/test_s8b_ratified_freeze.py:1468-1472`
- campaign が `RESULT_SCHEMA` を contract の同一 object として re-export することを pin する。`orchestrator/tests/test_s8b_floor_contract.py:164-180`

成果物影響: 特に案 b の launcher API 変更と D2 の consumer 更新が、未列挙の既存 test に波及する。

推奨: pin 閉包へ上記を追加し、C3a では期待値を保存、D2 で v5 化が必要な consumer fixture だけを所有させる。

## 所見 B-10 — whole-file SHA-256 pin 0 件という限定主張は支持される

**refuted、[実測]**

候補 11 file の現在の SHA-256 を計算し、その literal を `rg -F --hidden -g '!.git/**'` で repo 全体へ検索したが hit は 0 件だった。例として campaign は `27232bfb...5a87`、launcher は `12f0dc30...e5c`、contract は `3e380355...73d` で、いずれも参照なし。

したがって「独立した literal whole-file hash pin は 0 件」は検算できた。ただしこれは AST、signature、caller set、nodeid pin がないことを意味しない。

成果物影響: whole-file hash の更新は不要だが、B-9 の semantic pin は regression 対象に残る。

推奨: plan の「whole-file hash 0」は維持し、「pin 閉包の全列挙」という見出しだけを限定表現へ直す。

## 所見 B-11 — 1 campaign の min/max を母集合へ一般化できない

**real、[推測]**

plan は実 campaign 後に exact type、key set、列挙値、min/max、件数を記録するとしている。`out-s2-plan.md:241-254`。これはその run の観測値を証明できるが、launcher が将来受理しうる全入力値域や、未発火の competing/failure/retry 分岐の値域は証明しない。

1 回の campaign を母集合とみなせるのは、主張対象をその 1 run に限定する場合、または事前定義された有限集合をその run が欠落なく全列挙したことを独立に示せる静的 field に限られる。timestamp、throughput、failure、probe 出力、実際に未使用だった retry slot には一般化できない。

成果物影響: `gate-input-values.json` の min/max を validator の許容 bound や実環境全体の値域として読むと過大主張になる。

推奨: 下記の限界文言を receipt と README の双方へ載せる。

## 受理集合の向きの判定

| 案 | artifact consumer の受理集合 | launcher API の受理集合 | D1660 |
|---|---|---|---|
| a: current v2 の launcher-consumed competing marker を許可 | **広がる** | おおむね維持 | 旧 token そのものではないが、単調縮小方針と衝突。新裁定なしでは不可 |
| b: probe 後に marker を発行する二段 API | **維持** | continuation を要求する分だけ狭まる | 衝突なし |

推奨判定は **b**。

## 恒真化の危険がある負例

危険があるのは少なくとも次の 3 件。

1. competing marker の「対になる正例・負例」  
   実 consumer と launcher を名指しせず、既存の近似 test も別々の stubbed/synthetic 経路である。

2. planned `retry_ordinal=None` の「対になる正例・負例」  
   名指しされた node は retry measurement ordinal だけであり、planned を拒否し続ける変異が生存する。

3. fake/injected 値域 receipt の pytest 負例  
   production receipt を生成・検証するコードが変更計画に存在せず、test-only 実体を検査する恒真化が可能。

さらに「row count/head/generation を変える」に対し node 名が `prefix_head_mismatch` だけなのも曖昧である。実装段では 3 field を個別に変異させ、同じ live recapture 比較へ届くことを確認する必要がある。

## 死んだ gate の判定

**現在の unlanded checkpoint としては refuted。** C3a 後には production caller と発火 script が存在するため、機構そのものは死んでいない。

ただし次は不可である。

- C3a だけを land する
- C3b 実測前に「実環境で発火確認済み」と書く
- D2 前に「certified consumer へ到達する」と書く

このいずれかを行えば D1114、D1194、D1341 に対する **real** な違反になる。

## consumer 不整合の判定

一時的不整合は **real** だが、silent acceptance ではない。

- `s8b_floor_stats.py`: v4/v5 を schema 別 exact keys で読み、v5 proof を live replay と照合する
- `s8b_ratified_freeze.py`: v4 exact keys と `RESULT_SCHEMA` を要求し、v5 を拒否する
- `s8b_holdout_admission.py`: result consumer ではなく attempt-ledger consumer
- 実際の holdout result consumer である `s8b_holdout_freeze.py`: v4 を要求し、v5 を拒否する

よって `PRODUCTION_RESULT_SCHEMA` 二重化は C3 checkpoint では成立するが、D2 を伴わない land には耐えない。

## pin 閉包の抜け

追加すべき既存 pin は次のとおり。

- `test_s8b_floor_stats.py:1603-1629` — AST 比較数と live verifier caller exact set
- `test_s8b_floor_attempt_launcher.py:2221-2230` — certified API と固定 recorder
- `test_s8b_holdout_admission.py:3727-3742` — inspector 公開 signature と保証境界
- `test_s8b_ratified_freeze.py:1468-1472` — default v4 result key set
- `test_s8b_floor_contract.py:164-180` — campaign の schema alias re-export identity

literal whole-file SHA-256 pin は検算上 0 件である。

## 値域 receipt が主張できる条件と限界の文言案

主張条件は次のすべてである。

- Pegasus compute node 上の fresh default production campaign である
- fake registry、injected `measure_fn`、test seam を使用していない
- commit、job ID、env tag、mode、protocol/freeze digest、run path を固定している
- launcher invocation、registry row、terminal evidence、result v5 proof、live inspector proof が全件対応する
- receipt の各値を出所 artifact の canonical bytes と SHA-256 から再導出できる
- 件数と欠落の有無を示し、未発火分岐を値域へ含めない

限界文言案:

> 本 receipt は、記載した commit、Pegasus job、環境 tag、mode、protocol および freeze による fresh default production campaign 1 回で、実際に観測された入力値だけを記録する。列挙値と min/max はこの run の観測集合および標本極値であり、launcher または consumer が受理しうる全値域、未発火分岐、他環境、他 mode、他 commit、将来 campaign の母集合または許容 bound を示さない。静的な有限集合について完全性を主張する場合は、事前定義された対象集合と本 run の全件対応が別途示された項目に限る。

## 親 brief の不変条件 4 件の判定

| 不変条件 | 欠陥判定 | 根拠 |
|---|---|---|
| 凍結 23 件と `FORMULA_ID` を変えない | **refuted、[実測]** | plan は全 23 件 byte 不変、`FORMULA_ID` 据置を明記。`out-s2-plan.md:144-176,335-336` |
| 正しさ gate を緩めず、fake/injected を実値域にしない | **real、[実測]** | 案 a は現受理集合を広げる。fake receipt の kill も production 実体を持たない。`:12-16,264,323` |
| launcher の perf 述語の新しい直接 call を作らない | **refuted、[実測]** | 既存 launcher gate を使い、新 direct call を作らないと明記。`:177,337` |
| `attempt_registry_core.py` に禁止構文を書かない | **refuted、[実測]** | core は変更対象外で、`aborted=False` と `OriginSealed(False, ...)` を明示的に禁止。`:180,338` |

したがって、不変条件 1、3、4 は plan 上守られる。不変条件 2 だけは、案 b の選択と具体的な端から端の正例・負例を入れるまで未充足である。