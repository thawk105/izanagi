判定は **NO-GO** です。静的検査のみで、ファイル変更と pytest 実行はしていません。

### 1. blocker — P1 と A3 はどちらも、未コミット作業ツリーを current authority に昇格させる

根拠:

- legacy は固定 HEAD の exact `100644` blob から index 化されます。`orchestrator/campaign/s8b_floor_campaign.py:686-713,810-817`
- versioned entry は `iterdir()` と `read_bytes()` だけです。HEAD への存在、Git mode、tracked 状態を一切検査しません。`s8b_floor_campaign.py:819-869`
- 既存テスト自身が、未コミット file を `write_bytes()` してそのまま index に受理させています。`orchestrator/tests/test_s8b_protocol_builder.py:1119-1136`
- `certified_writer_admission` は同じ作業ツリー file を再読し、同じ作業ツリー由来 record の SHA と照合するだけです。由来を Git に戻していません。`orchestrator/campaign/certified_writer_admission.py:201-218`
- `ccbench_pin` は index では 40 桁 hex しか要求されません。Git object の実在は不要です。`s8b_floor_campaign.py:722-739`

具体的な受理差は次です。

| repository 状態 | 現 resolver | P1 | A3 |
|---|---:|---:|---:|
| legacy のみ | legacy | legacy | 拒否 |
| legacy + 未コミット HEAD-pin record 1 件 | 拒否 | versioned を受理 | versioned を受理 |
| legacy + 未コミット非 HEAD-pin record 1 件 | 拒否 | 拒否 | versioned を受理 |
| legacy + HEAD-pin record + 別 pin record | 拒否 | HEAD-pin を受理 | 拒否 |

したがって、P1 は現行受理集合の厳密な拡大です。A3 は正常状態を拒否する一方、以前拒否していた任意 pin の singleton file を受理するため、単なる厳格化ではありません。両案は包含関係になく、P1 は多重 record、A3 は任意 pin に弱い設計です。

さらに issuer は file を作った後の検査失敗でも削除しません。`s8b_floor_campaign.py:925-933,994-1059`。そのため通常の発行途中や失敗残骸さえ、P1/A3 の resolver が current として選び得ます。

影響:

- floor submission の受理集合が、committed authority から「同一 UID が置いた canonical file」まで広がります。
- trial claim は `ccbench_pin` と `protocol_sha256` を記録します。`s8b_holdout_admission.py:868-887`
- result と材料レポートにも同じ値が入ります。`s8b_floor_campaign.py:5110-5120,5169-5179`
- planned holdout の HEAD blob 再照合が入れば最終計測前に拒否できますが、submission 受理、build、claim、run directory 作成までの状態変更は先行し得ます。
- certified 選択の現在値は直ちには変わりませんが、その入力となる protocol authority の由来が Git から作業ツリーへ後退します。

最低限、resolver 用 index は固定 HEAD の versioned `100644` blobだけを authority とし、issuer の未コミット post-write 検査は別 API に分離すべきです。未追跡、削除、dirty 差分も fail-closed にする必要があります。

### 2. blocker — certified 側の consumer 閉包が欠けている

親の 3 点以外に、少なくとも次があります。

1. `s8b_holdout_freeze` の public `generate-v2-candidate`

   - legacy を直接読みます。`orchestrator/campaign/s8b_holdout_freeze.py:1280-1309`
   - official result の `protocol_sha256` がその legacy hash と一致することを要求します。`:1316-1341`
   - 生成 candidate にも legacy path/hash を書きます。`:1647-1651`
   - public CLI から到達可能です。`:1748-1814`

   versioned protocol で official result が生成されると、その SHA は legacy と異なるため、`:1335-1336` で必ず拒否されます。逆に legacy result を通せば、candidate は legacy を指し続けます。

2. downstream verdict と ratified verifier

   - verdict は freeze 内の `floor_protocol.path/sha256` を実際に読みます。`orchestrator/campaign/s8b_verdict.py:953-969`
   - ratified verifier も generation record の動的 path を捕捉して検証します。`orchestrator/campaign/s8b_ratified_freeze.py:2943-3042`

3. official preflight

   - fixed set は legacy path のままです。`s8b_floor_campaign.py:259-264`
   - supplied versioned SHA と legacy bytes を比較し、allowlistにも legacy pathとversioned SHAの組を入れます。`:3607-3635,3700-3707`
   - official は今日 CLI で拒否中ですが、解禁時には guaranteed break です。`:5727-5745,6740-6747`

再現の筋道:

1. versioned protocol で official result を得る。
2. `generate-v2-candidate` を実行する。
3. producer は legacy SHA を計算し、versioned SHA を持つ result を拒否する。
4. v2 candidate、ratification、verdict、certified 選択へ進めない。

影響:

- 現在の certified 値は誤って更新されず、fail-closed のままです。
- しかし新しい certified 選択、材料レポート、試行台帳の生成経路は永久に開きません。
- legacy result を使った場合だけ進める状態が残り、resolver の current と certified chain の参照先が分裂します。

`FLOOR_PROTOCOL_REL` の全用途を一括して歴史錨定と扱った分類が誤りです。producer は official run が実際に使った committed protocol path/hash を manifestやresultの証拠鎖から取得すべきで、current resolverを後から再実行するのも不適切です。

### 3. major — shell を直しても、public pilot CLI が caller-selected path のまま残る

根拠:

- CLI は `--protocol PATH` を必須引数として公開しています。`s8b_floor_campaign.py:6550-6557`
- `main()` はその path を直接 `load_protocol()` します。`:6749-6765`
- resolver を呼ぶ検査はありません。
- 既存テストも任意 path を渡す public API として固定しています。`orchestrator/tests/test_s8b_floor_campaign.py:3705-3724,8575-8613`

再現:

1. current versioned artifact と byte-exact な copy を任意 path に置く。
2. shell wrapperを通さず `--mode pilot --protocol <copy>` を実行する。
3. core の current contract検査と、予定される holdout document一致検査は通る。
4. campaign resultには SHAしか残らず、callerが選んだ入力 pathは証拠鎖に残りません。

異なる documentなら後段で拒否されますが、campaign claimやrun作成などが holdout authority 検査より先にあります。`s8b_floor_campaign.py:5684-5770,6043-6067`

影響:

- resultの数値が byte-exact copyで変わらなくても、「callerにpathを選ばせない」というD460の受理境界は閉じません。
- wrapper外の実行では、trial claimとレポートのSHAがどの sanctioned pathから来たかを復元できません。
- shell用に pathだけを出力するCLIを足す設計も、scan後の差し替え窓を残します。

production driver自身がresolver recordを内部取得し、pathだけでなくcommitted bytes/SHAを使用する必要があります。

### 4. blocker — 「T-1255 の手段記述は失効した」は親だけでは裁定できない

根拠:

- 最新裁定は「`freeze_protocol` の tty 判定を明示フラグとAI provenanceへ置換し、そのうえで凍結」と明記しています。`docs/archive/worklog-phase3-0817-611.md:565-573`
- sourceも現在なお `freeze_protocol` を「実凍結」、`reseal_protocol` を「AI reseal」と別の操作として定義しています。`s8b_floor_campaign.py:1070-1072,1237-1285`
- 親 brief はこの明示手段を実装しないとしています。`brief.md:57-58`

`freeze_protocol` の出力先が既存である事実は、「裁定が誤っている」証拠にはなりますが、「reseal_protocolだけで裁定を履行した」と親が決定できる根拠にはなりません。むしろ裁定文の「create-onlyなので旧 protocolを退ける手順を含める」は、その衝突を認識した指示です。

影響:

- artifactのbytesは期待どおりでも、誰がどの承認経路で凍結したかという要求済みprovenanceが欠落します。
- worklogやdecisionが「T-1255完了」と記録すると、実装とユーザー裁定が食い違います。
- 数値より、凍結成果物の権威参照が誤ります。

段4で「reseal_protocolをT-1255の正規履行とみなすか」「freeze_protocolも改修または統合するか」をユーザーへ再裁定させる必要があります。

### 5. major — 「旧 protocolを退ける」はP1では不成立、A3では脆い停止状態になる

P1の再選択経路:

- versioned fileを作業ツリーから削除する、namespaceをsparse checkoutで欠落させる、またはartifactだけrollbackする。
- scannerはHEADのversioned blobを見ず、legacyだけを返します。`s8b_floor_campaign.py:819-821`
- P1 fallbackがlegacyを再選択します。
- HEAD gitlinkを旧 pin `d706...` へ戻し、versioned fileを残した場合も、legacyがHEAD-pin exactとなりP1が積極的に再選択します。

A3の停止経路:

- 現在のnamespaceは不在です。発行前にA3を有効にすると候補0件です。
- artifactだけrollback、codeだけcherry-pick、sparse checkout、legacy-only fixtureで同じ0件になります。
- `test_s8b_protocol_builder.py:312-342` と `certified_writer_fixtures.py:110-123` はlegacyだけのfixtureです。
- submodule未初期化だけは原因になりません。P1のgitlink取得はsubmodule内容でなくHEAD treeを読みます。`s8b_floor_campaign.py:904-922`

A3 resolver自身はlegacyを返しません。ただし、全変更のrollback、旧revisionの別worktree、direct CLI、未配線のholdout-freezeではsystemとしてlegacyが再利用されます。

影響:

- P1でlegacyが戻ると、trial claimの`ccbench_pin`、resultとreportの`protocol_sha256`が旧値へ戻ります。
- A3の0件状態ではfloor submissionの受理集合が空になり、新しいresult、report、試行台帳が生成されません。
- 「同一commit群」は実装中、部分rollback、fixture、別worktreeの状態を原子的にはしません。

### 6. minor — 発行後の結合状態で赤になる既存テストが追加で漏れている

artifact追加だけに限定すれば、段2の「実repo resolver系2件」という切り分けは反証できませんでした。しかし実waveは「shell配線、resolver変更、artifact発行」の結合状態です。その状態では次が追加で赤になります。

- `test_submit_floor_qsub_argv_does_not_inherit_ambient_confirmation` はlegacy argvを固定しています。`orchestrator/tests/test_pegasus_floor_tools.py:1349-1380`
- `test_floor_driver_failure_propagates_rc[rc-0/2/7]` はjob-resultのlegacy `protocol_path`を固定しています。`:2285-2335`
- `test_floor_driver_fd_setup_failure_does_not_mark_launch` の専用driverは新しいresolver subcommandを処理できず、対象のFD setupより前にmarker作成または終了します。`:2403-2457`
- `test_floor_job_result_writer_failure_preserves_driver_rc` も専用driverがresolver呼出しで先に終了し、本来検査するjob-result failureへ到達しません。`:2460-2499`
- 安全なconsumer閉包まで直すなら、legacy-only candidate fixtureを使う `test_v2_candidate_build_and_generate_synthetic_g1` も更新対象です。`test_s8b_holdout_freeze.py:1271-1305`、`s8b_v2_freeze_fixture.py:331-365`

影響:

- 単なる期待pathの差だけでなく、failure stage、launch marker、job-result作成有無が変わります。
- 期待値を一括置換すると、resolution失敗とdriver失敗を区別する検出力が落ちます。
- 成果物ではfailure receiptのstageと`protocol_path`参照が誤る可能性があります。

最終判定は **NO-GO** です。P1/A3を選ぶ前に、committed-only index、consumer閉包、T-1255再裁定を段4へ戻す必要があります。

## 総括

- P1は現行受理集合を単調に広げ、A3も未コミットsingletonを新たに受理するため、両案とも現状のscannerでは採用不能です。
- 最大の欠陥はpin選択規則ではなく、versioned recordの権威が固定HEAD blobでなく作業ツリーにあることです。
- shell、holdout admission、certified admissionの3点だけでは閉じず、direct CLI、v2 candidate producer、official preflightが残っています。
- P1ではlegacyが再選択され、A3では部分着地やrollbackで受理集合が空になります。
- T-1255は`freeze_protocol`改修を明示しており、親が手段だけ失効と断定するには再裁定が必要です。
- 既存テスト計画もversioned pathによるfailure-stage回帰とholdout-freeze producerを被覆していません。
- よって段4へは、両案ともそのまま不採用、committed-only authorityを前提に再設計、という結論を返します。