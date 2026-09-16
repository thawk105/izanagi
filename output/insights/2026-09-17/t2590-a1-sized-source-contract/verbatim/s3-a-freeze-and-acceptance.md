## 凍結 bytes と pilot 成果物

静的検査と読み取り専用の digest 計算を行った。実装・pytest・実 build は行っていない。以下では `D`＝`orchestrator/campaign/paper_story_a1_paired.py`、`S`＝同ディレクトリの `paper_story_a1_source.py`、`J`＝`tools/pegasus/paper_story_a1_paired.sh` と略記する。`brief`・`plan`・`草稿`は射影された各文書を指す。

**refuted — 指定された分岐置換が pilot の履歴 binding を壊すという反例は見つからない。**

公開済み `receipt.json:226` と `result.json:278` の `source_binding` は読み取り比較で同一、`files` は9件だった。v1 契約の patch・policy・preregistration・amendment の4 digest、および公開 binding が持つ契約・patch・amendment の3 digestは一致した。

| 検査箇所 | pilot 入力についての検算 |
|---|---|
| `S:32` `binding_matches` | 現行は3 digestのみ照合。plan の既定 pilot 選択を維持すれば同じ判定になる。module の現在SHAは照合しない。 |
| `D:4836` binding検証 | pilot の期待 path集合が不変なら、追加される表のループは v1 の照合だけ発火する。 |
| `D:2230` source閉包 | terminal は5＋4＝9件、non-certifying は10＋4＝14件。pilot の末尾4件と順序を保持する計画。 |
| `D:5219` consumer | 公開 binding はv1を含むため、現行条件も提案の `any(...)` も真。取得する admission と後続判定は同じ。 |
| `D:5002` configure argv長 | amended時は `10 + len(define_tokens) + 4`。関数を変更しない計画なので長さ・位置・FETCHCONTENT条件は同じ。 |

**成果物への影響：** 計画どおりの実装なら、公開 pilot binding に対する上記判定は維持できる。凍結済みファイルを編集する提案も見つからない。

**unverifiable — 「再検証結果が1 bitも変わらない」は、未実装の現在には確定できない。**

また履歴 binding 検証と、現在checkoutとの照合は別である。`D:7519` はHEAD・blob OID・working SHAを照合するため、変更後checkoutを過去束の生成元として扱えば拒否される。plan:378–382 はこの区別を正しく記載している。

**成果物への影響：** 履歴検証の互換性を、変更後checkoutでの再materialize・再発行の成功まで拡張して記録してはいけない。

## 受理集合の変化

**real — 「sized amended sourceが増えるだけ」ではない。**

`brief:35` と `plan:160` の「受理形を増やさない」は、`_trace0_commands_match` 単体の述語を変更しない意味なら正しい。しかし study付きconsumer全体の集合は変わる。

| 入力 | 現行 → 計画後 |
|---|---|
| sizedの契約なし terminal binding（5件） | binding検証では受理可能 → 期待9件と不一致で拒否 |
| sizedの契約なし non-certifying binding（10件） | binding検証では受理可能 → 期待14件と不一致で拒否 |
| sizedのv2契約・追補を含むbinding | 余分なpathとして拒否 → digest等が整合すれば受理 |
| sizedのamended configure | 新bindingが拒否される → admissionと4 tokenを要求する既存経路へ接続 |
| hydrate未指定のsized submit | 当該source条件では止めない → submit時点で拒否 |

根拠は `D:2243`、`D:3409`、`D:4847`、`D:5219`、`D:5319`。現行のsized測定自体は `D:7127` で拒否されるため、「従来のsized本走が成功していた」という意味ではない。

**成果物への影響：** sizedの部分的な受理集合は拡大と縮小の双方がある。この差を記録しないと、変更の範囲を過少申告する。

**refuted — 両契約／契約なしbindingが、正規のpilot・sized consumerを抜ける穴。**

`D:4847` は、bindingが自己申告した集合ではなく呼出し側の期待 `relative_paths` と完全一致を要求する。正規経路では `D:4870`・`D:4880` がpolicyから閉包を作り、arm検証も `D:5319` でpolicy付き検証へ到達する。したがって、両契約入りは余分なpath、契約なしは不足pathとして拒否される。

ただし `_validate_source_binding_for_paths` に人為的に「両方入り／どちらもなし」の期待集合を渡せば、提案ループ自体は一契約性を保証しない。これはhelper単体の性質であり、確認した本番呼出しにはその集合を作る経路がない。

**成果物への影響：** 正規pilot・sized経路の受理集合に混入は生じない。「全v3 bindingに必ず一契約」という一般保証にはしてはいけない。

**refuted — sizedのattempt非固定がpilotを緩める。**

planは `D:3411`・`D:7127` のpilot attempt照合と、`D:2636` のpilot attempt-0004条件を明示的に残す。binding検証自体は現行でもattemptを検査しない。

**成果物への影響：** pilotの新規submit／measureは引き続きattempt-0004限定。sizedのsource契約非固定を、再投入制限の解除と解釈する根拠はない。

## D1323 の閉じ

**refuted — 親statusのsubmodule無視、または元checkoutのuntrackedだけで、不定な測定sourceが通る。**

具体的に次の反例候補を追った。

- 親側 `ignore=all` でtracked変更を隠す：`D:2402–2420` がsubmoduleを直接検査する。jobも `J:361–369` に同じ検査がある。
- 元checkoutへuntrackedファイルを置く：これは凍結policyの `untracked_files_ignored: true` に従い受理される。しかし `S:75–77` はpinから別worktreeを作るため、そのファイルを実測sourceへコピーしない。
- materialized rootへ指定patch以外のsource差分を入れる：`S:58–66` がroot・HEAD・期待materializationを検査し、`pipeline.py:1096–1104` がtrace/perf境界で呼ぶ。既存tree比較は `.git` を除くtreeを列挙する（`s8b_expected_materialization.py:62,242,448`）。

**成果物への影響：** この3経路から、出所不定なCCBench sourceをsized測定へ通す反例は構成できなかった。untrackedを無条件拒否へ変える必要はない。

**unverifiable — P5の「閉じ」は、現時点では実測済みではない。**

既存機構の存在は現物で確認できるが、sizedはまだ `D:7127` で止まる。さらに `D:5373` が検査するのはconsumer実行環境の元checkoutであり、過去の実測treeを再検査するものではない。過去sourceについてはbinding/admissionの整合検査である。

閉じの記録には、既存5境界の呼出し、sizedで渡される同一context、実際に観測した受理・拒否、stubで置き換えた部分を区別して残すべきである。plan:238–268 の試験計画はその方向にある。

**成果物への影響：** 今すぐT-2081を「sizedで実証済み」と閉じると、台帳の完了根拠が実装・試験より先行する。

## hydrate 入力の出所

**refuted — 外部dirがpinなしなので、その内容が無検査でsizedへ入る。pilotと同一の経路である。**

外部dirの指定文字列自体にはcommit pinがない。しかし `J:1361–1371` のコピー後、`S:85` が既存 `_verify_pristine_floor_dependency_sources` を呼ぶ。

同関数は共有policyからpinを取得し（`s8b_floor_campaign.py:2617`付近）、各依存のGit top-levelとHEADを確認し、pin不一致を拒否する。同時に `tracked_only=False` が既定なので、untracked・ignored・submoduleを含むstatusを検査する（同:2718–2781）。元dirの名前や存在だけで受理する経路ではない。

**成果物への影響：** sizedがpilotと同じ依存供給経路を利用できるようになる。計画に依存pin・clean条件を緩める差はなく、D1323違反の新しい面は確認できない。

## 追補 README と code の乖離

**refuted — 草稿1〜5項に、対応する機構が存在しない。**

草稿:28–39 は、元checkout検査、隔離worktree＋指定patch、build直前validate、同一sourceの引渡し、consumerのbinding/admission検査に対応する。特に `D:7137–7150` と `D:7183–7184` は、条件関門とcampaignへ同じcontextのrootを渡している。

ただし5項は「consumerが過去treeのbytesを独立証明する」という意味には読めない。現物の `artifact_standalone_proof` はfalseである（公開receipt:227、`D:4866`）。

**成果物への影響：** 現行の文言を束縛・整合検査として読む限り、未実装の独立証明を約束してはいない。

**real — 草稿の保証範囲には明示すべき限界がある。**

草稿:35 の「指定patch以外の差分は拒否する」は、既存tree比較の対象内という限定が必要である。同比較は `.git` を除外する。また草稿:45–47 の出所説明は、元checkoutのuntrackedを拒否する意味ではない。凍結sized policy:20 は明示的に無視を登録している。

READMEが既に「tracked-clean」と書いているため、`untracked_files_ignored` の語がないことだけならnit。ただしD1323の閉じの説明として使うなら、「元checkoutのuntrackedは既登録どおり無視し、pinから隔離生成する」という既存挙動を添えるのが正確である。

**成果物への影響：** codeの受理集合は変わらないが、READMEと閉じの記録が保証する範囲を実装以上に広げるのを防ぐ。検査追加は不要。

## 裁定との整合

**refuted — 固定2契約表・v2 JSON・追補README・直接回帰testが、それだけで禁止された汎用化／台帳／gateになる。**

plan:62 は登録APIや第三studyへの拡張機構を設けないと限定する。v2と追補は、凍結v1を保存しながらsizedのsource条件を束縛する名指し変更である。既存検査のsizedへの接続と、その回帰testは独立した新gateではない。

D1973の却下理由も実装禁止ではなく、「証明書とpolicy凍結とは別単位で扱う」である（`docs/decisions.md:59541–59543`）。

**成果物への影響：** この限定を守れば、追加の認可状態や汎用の受理規則を作らずにsizedを接続できる。

**real — 「台帳」候補として区別すべきなのはbrief:41の変異台帳である。**

これは文言上は追加記録に当たる。ただしbrief:15にユーザー指定の変異事前登録があり、その実施記録に限るなら、付随的な台帳新設とは区別できる。運用時のsource受理台帳へ発展させる根拠はない。

**成果物への影響：** author検証記録を越えて永続の受理状態・運用参照先を作れば、D1986のscope外になる。

**real — plan:16の「D1986項5の逐語がB-4と取り違え」は、現在の射影資料と一致しない。**

`rulings-verbatim.md:64–74` は既にA-1の項5で、`docs/decisions.md:60073–60081` と整合する。このplanの指摘に基づく訂正は不要である。

**成果物への影響：** 放置すると、正しい裁定資料に対して不要な訂正履歴・参照変更を作る。

## brief の実測値と一般化

**refuted — `0ba074…` が履歴bindingのlive pinである。**

公開receipt:245–247の値はmoduleの歴史SHA。`S:34–38` の固定照合対象にmoduleはなく、`D:4850–4859` はその形式を確認するだけである。ただし現在checkout照合の `D:7540` では比較対象になる。

**成果物への影響：** 履歴binding内のSHAを現在値へ書き換える必要はない。書き換えれば成果物間の束縛を変えてしまう。

**real — 「pilot attempt 1〜3はinfra失敗」は分類が粗い。**

attempt-0001・0002のbench前停止は、attempt-0002記録:33,121,138–151で裏付けられる。一方attempt-0003は、依存供給不足とsourceの意味不整合を条件関門が拒否したものだ（`output/insights/2026-09-09/t2397-a1-pilot-attempt-0003/README.md:149–164`）。単なるscheduler／輸送障害ではない。

**成果物への影響：** attempt非固定の根拠として「bench前の停止」と「再投入してよい原因」を混同すると、将来の失敗分類・再投入記録を誤らせる。source契約からattempt pinを外すこととは分けて記録すべきである。

**refuted — ident/walのsized登録が未実装。**

`orchestrator/campaign/ident.py:48–52` と `orchestrator/campaign/wal.py:122–126` に、対象sized IDとbalanced5 pairing designの組が存在する。

**成果物への影響：** 本waveでidentity集合を拡張する必要はない。

**unverifiable — baselineの「462 passed」は本相談では再検証していない。**

brief末尾の親実測記録として扱う。今回確認できたのは静的経路と読み取り計算であり、計画後の回帰成功ではない。

**成果物への影響：** 親baselineを変更後の受入結果へ転用すると、未検証の実装を完了扱いにする。

## 総括

**計画の主要経路を壊すpilot互換性違反・両契約混入・新たなhydrate無検査経路は見つからなかった。** 固定2契約への対称化は維持できる。

修正すべき点は、①sizedの受理集合には縮小もあると明記する、②T-2081の静的根拠と実測済みの閉じを分ける、③READMEの保証範囲を既存検査に合わせる、④planの古い裁定訂正指示とpilot失敗の分類を直す、の4点である。

実装後のpilot判定同一性とsized接続の成功は未検証。新gate・bytes検査・運用台帳の追加、本走投入・認可は提案しない。