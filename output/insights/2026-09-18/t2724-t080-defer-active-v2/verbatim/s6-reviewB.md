## 所見 (RB-1 …)

対象は `7a763575f`。指定資料・13 file の差分・現物を読取り、親ログを照合した。編集・pytest 実行はしていない。

**RB-1 — must-fix：接続 fixture は build seam で停止し、委譲の正負境界に到達していない。**

両木の接続系 8 node は、`test_s8b_ratified_freeze.py:_make_emitter_build` の `compiler_input_rel = "fixture.txt"` による `FileNotFoundError`。固定 ccbench 用の seam を、実 ccbench clone にそのまま適用している。

**放置時の影響：接続正例と主要な委譲負例が赤のままになり、active-valid 到達・land 条件を証明できない。**

変更してよい範囲は同 test helper の入力 path 指定と接続 fixture からの引渡し。固定 fixture の既定値は維持し、接続側は **fixture が checkout した pin に存在する regular file** を指定する。実 submodule に `fixture.txt` を追加する修正、pin の変更、検証 API の stub 化は禁止。

**RB-2 — must-fix：再 launch は既存の同一 object 契約を壊す。親の走査だけの案にも二つの未解決点がある。**

`C/s8b_oracle_driver.py:run_block` の campaign-start 前の再 launch が、既存 `test_v2_floor_disk_swap_after_launch_uses_same_validated_object` を両木で赤にしている。

親案でも、単に `launch_validate` を `search_repository` に置き換えるだけでは不十分。

- scanner は floor result の bytes も読む。floor result は `_active_chain_exempt_exact` の免除対象ではない。poisoned bytes への交換で既存 hit が消えると、保持 report との完全一致が拒否する。
- tracked receipt を削除すると、列挙集合の digest が同じでも scanner の `is_file()` 検査が失敗する。走査を先に置く限り `[missing]` の epoch refusal には到達しない。

**放置時の影響：既存 disk-swap 正例が赤のまま、または fixture 修復後に `[missing]` が別理由で赤になる。**

修正対象は `C/s8b_oracle_driver.py:run_block` と、親が指定した限定的な再走査処理。receipt 層2の委譲が存在しない `never-issued` 経路へ、新たな鮮度条件を一律に課さないこと。既存 test の `completed`・同一 object assertion は維持する。

`[missing]` は **実装側の順序を直す**。既存 receipt 履歴・存在・bytes の再解決を利用し、receipt 自体の epoch drift を走査失敗より先に帰属させる。履歴に変化がない late-hit は鮮度検査の拒否として残す。`inspect_receipt_history` の正常な中間状態も `invalid` なので、それを完成済み resolution として直接比較してはいけない。既存の解決回数 pin、epoch refusal、late-hit の拒否理由を維持する。

**RB-3 — must-fix：floor E2E の digest oracle が、残存 chain record を入力に含めていない。**

`T/test_s8b_floor_campaign.py:test_real_seal_protocol_to_floor_official_core_e2e` は、`expected_clean_digest` に `frozen_paths` の hash だけを渡す。一方、production の `clean_scan_digest` は chain record の path と bytes hash も含める。親の原因判定は現物と一致する。

**放置時の影響：修正前45赤のうち1件が chain 有り木で残り、両木焦点緑に到達しない。**

変更可能なのは **期待 digest の入力構成**。preflight 用 `expected_allowlist` と、digest 用の namespace 全体の記録を分ける。clone に残る chain record を独立に列挙・hash 化して後者へ加える。

`allowlist == expected_allowlist`、clean scan の呼出し回数2、両 digest の完全一致は変更しない。production の `clean_scan_digest` や `_assert_freeze_allowlist` の返値から期待値を作ると自己照合になるため不可。g1 を S に追加して消す修正も不可。

**RB-4 — must-fix：consumer 回帰には、もう一つの行番号 pin の追随漏れがある。**

`focus-nochain-2.log` の唯一の赤は
`test_define_sink_cross_product_classifies_t2155_production_sinks_exactly`。

`T/test_ccbench_spawn_sites.py:3460` の `1775` が残り、`classifications[s8b_sink]` が `KeyError`。現 commit の同じ `pipeline.evaluate` sink は **1790行**。更新済みの1788→1803は別の `evaluate_fn` sink で、そちらは正しい。

**放置時の影響：接続系を直しても consumer 回帰・通常受入に赤が残る。**

修正可能なのは当該 sink の位置 pin。`Counter({"covered": 38})`、kind、scope、失敗集合の期待値は変更しない。追加修正後は最終位置を再確認する。

**RB-5 — must-fix：非層2拒否の新負例は、狙った単一理由を固定していない。**

`T/test_s8b_oracle_driver.py:test_t080_active_v2_preserves_nonlayer2_receipt_refusal` は「非空」「層2理由なし」「二つの結果の集合一致」だけを要求する。別の非層2拒否や複数理由でも通るため、R trailer だけの負例とは証明できない。

**放置時の影響：fixture の別障害を正しい拒否と誤認し、m2a に対する検出力の帰属を誤る。**

変更可能なのは新 test の assertion 強化。既存 f28 と同様に `receipt.user_commit_trailer` の単一理由を固定し、公開 gate にも同じ完全な拒否集合を要求する。fixture の別拒否を期待集合へ追加して通してはいけない。

**RB-6 — should：新接続 test の実 root reader 分類が登録簿に反映されていない。**

新接続8 nodeと draft 負例は、builder 経由で実親 repo の source・output・履歴と実 ccbench を読む。しかし新 test 名は `conftest.py` の resource 登録簿にも独立 golden にもない。fork decorator は process 分離であり、resource lock の代替ではない。

**放置時の影響：並列受入で実 root writer と競合でき、焦点緑だけでは再現性を保証できない。**

既存の resource 登録簿と golden に、実アクセスに対応する reader 分類を追随させる。新 floor helper 消費 test の親 repo 読取りも併せて確認する。新しい台帳・lock 機構は不要。ログ上の serialization 緑を、未登録アクセスが存在しない証拠にしてはいけない。

**RB-7 — should：memo の縮約自体は正しいが、負例に旧件数と不足する選択対照が残る。**

`T/test_real_repo_serialization.py:test_receipt_memo_consumer_inventory_and_optouts_are_complete` の合成負例は、8/8へ変更後も `node_count=35` を渡している。集合検査が壊れても件数で落ち得るため、狙った集合差分の検出を独立に示さない。

また lazy test の非 consumer 対照は `test_example.py::test_unrelated` のまま。今回外した元 consumer だけを選ぶ対照はない。

**放置時の影響：memo の再混入や不要な prewarm を、意図した負例で確実に検出したと主張できない。**

既存 test 内で、件数を正しい値に保って集合だけを壊す。既存 barrier test に元 consumer の選択を与え、不発火を要求する。残存 consumer の起動条件や worker 禁止を弱めない。

**RB-8 — should：5分上限への寄与を算定できる node duration が指定ログにない。**

指定3ログに call/setup/teardown の個別 duration 行はない。接続 fixture と新 clone 3ケースの所要は分離できない。

**放置時の影響：焦点走だけで既に300秒超の状況で、通常受入5分以内という判断ができない。**

既存の計測手段で修復後の所要を確認する。必要なら test fixture の base 構築を共有し、ケースごとの独立 clone・root に束縛した実 token 再取得・各 assertion を維持する。parameter 数の削減や検査省略はしない。

## 接続正例の判定

**構造は実機構へ接続しているが、実測では未達。**

- `active_v2_base=True` は最初の basis commit 前に、既存g1・budget input・predictions・selector journalを除去する。これは接続 fixture 限定で、45 node用の S を広げていない。
- receipt 接続分岐は既存 ccbench pin を利用し、`_prepare_emitter_base`／`_make_fixed_ccbench` を再実行しない。
- fixture 自身の seed commit を selector の `pre_oracle_head` に使う。既存 predictions による no-op と、外国の祖先参照を避けている。
- `load_ratified_freeze`・`launch_validate`・`verify_receipt` を stub していない。
- 正例は `state == "active-valid"` に加え、`refusals == ()` と observation の存在を要求する。

ただし両木とも emitter の build 中に停止している。B-1 の既知障害を避ける構造は確認できても、その後の C→G→A→X、最終 load／launch／receipt 接続が成功するとはまだ言えない。

負例の品質判定は次のとおり。

| test 群 | 判定 |
|---|---|
| `unactivated_chain_hit_is_invalid` | Gへcheckoutし、official pathへ実hitを追加。単一の層2理由を要求する。現在は構築前段で赤 |
| `failed_launch_preserves_receipt_refusal` | 実 launch の `closure-hit-mismatch` を固定。その後の gate は二系統の拒否の存在を要求するが、余分な拒否を禁止していない |
| `active_v2_preserves_nonlayer2_receipt_refusal` | 狙った trailer 理由を固定していない。RB-5 |
| `campaign_start_rechecks_receipt[changed|missing]` | prepare到達、単一epoch理由、evaluate未実行、WALなしを要求。mutation は実 bytes／削除。`missing` はRB-2 |
| `campaign_start_rejects_late_hit` | gate前からある同名pathの内容を交換し、列挙driftによる代役拒否を避ける。v2理由の存在検査は完全集合より弱い |
| `v1_gate_does_not_delegate_with_active_v2` | v1指定で層2理由を要求する。ただし `any(...)` なので他理由の併発は許す |
| `layer2_delegation_rejects_*` | 正常 token の委譲成功を先に確認。outer HEAD、同HEAD・同列挙の別root、namespace外追加、非exact型、世代bytes変更を分離している |
| `delegated_scan_keeps_frozen_document_bindings[...]` | 正常tokenを保ち、入力docの1束縛だけ変更。exactな `MigrationError.reason` を要求 |
| `launch_token_retains_immutable_scan_and_root` | resolve済みroot、列挙digest、nested mappingの変更拒否、hitのtuple化、historical型の不受理を確認 |

後半の分離 test に、検証本体を代役へ差し替える箇所は認めなかった。ただし正式な変異 kill 結果は今回の親ログにはない。

## 45 node の解消表 (chain 有り木、解消 / 残存 / 新規)

対照45 nodeと `focus-chain-1.log` の FAILED 集合の交差は、floor E2Eの1件だけ。親の **44解消／1残存** という集計は一致する。

| 経路 | 対照赤 | 解消 | 残存 |
|---|---:|---:|---:|
| T-080 output copy／構築 | 10 | 10 | 0 |
| floor clone 2経路 | 5 | 4 | 1 |
| memo依存の切離し | 29 | 29 | 0 |
| g7 | 1 | 1 | 0 |
| 合計 | 45 | 44 | 1 |

新規赤は接続系8件と既存disk-swap退行1件の計9件。したがって「45件が全部緑」は否。

切離し実装は以下の点で裁定に沿う。

- S は official namespace 全体と candidate exact file。g1 は残す。
- copy の ancestor 集合は除外後の集合から作る。独立期待集合との差分、candidate sibling の残存、bytes一致を検査する。
- floor両clone経路に削除helperが入る。source HEAD、gitlink commit、S削除commitを分離し、残存treeのmode/OIDも確認する。
- 削除契約testは S空時のHEAD不変、S非空時のexact削除集合、実行可能な無関係fileの保持を検査する。
- scan負例3ケースは指定されたofficial／candidate pathに置く。無害bytes受理→実 `conjunction_hits` 確認→clean scan拒否の順で、別gateの拒否を成功扱いにしていない。
- draft負例も S外の実hitを確認してから実 `_draft_reconstruct_holdout` の拒否を要求する。
- g7の既存exact refusal集合は変更されていない。

T-2776の完了には、残存赤の解消と正式な変異実証がまだ必要。

## 焦点走の赤の帰属と fix 指示

| 親ログ | 結果 | 帰属 |
|---|---|---|
| `focus-nochain-1.log` | 1086 passed / 9 failed / 11 skipped | 接続fixture 8、再launch退行1 |
| `focus-chain-1.log` | 1085 passed / 10 failed / 11 skipped | 上記9＋floor期待digest1 |
| `focus-nochain-2.log` | 1574 passed / 1 failed / 25 skipped | `pipeline.evaluate` の位置pin漏れ |

修正対象はRB-1〜4のfile・関数に限定できる。接続8件は原因共通だが、fixture修正後にはじめて各 assertion を評価できる。そこで出る拒否を、現在の緑予測に織り込んではいけない。

memo登録簿は、conftest・独立golden・AST導出が8関数／8 nodeへ追随し、opt-out 2関数／3 nodeを維持している。B-2のliteral二本も残存consumerへ変更済み。`test_run_tests_task_run.py` は登録集合から代表を選ぶので直接変更は不要で、今回の赤にも含まれない。

直接constructor 7箇所の新field追加は確認できる。`replace` 派生はfieldを継承する。consumerログの唯一の赤はRB-4であり、constructor、serialization、reportに新たな失敗は報告されていない。productionの凍結artifactや固定hashを変更する差分もない。ただし指定ログを受入全走や全pinの網羅証拠とは扱わない。

時間は、焦点走がchain無し **465.05秒**、chain有り **447.52秒**。通常受入と同一条件ではないが、既に300秒を超える。chain無し焦点走のreceipt prewarmだけで **40.61秒**、consumer回帰の計算ノード走で **44.84秒**を使っている。29 nodeの切離しによってprewarm費用が消えた、という解釈は誤り。

新fixture個別の寄与はログ欠落により算定不能。さらに現在の接続8件は早期失敗の時間なので、修復後の正常構築時間の上限にもならない。

## 報告と実体の不一致

author報告の「実装済み・未達」「pytest未実走」は正確であり、実行環境の制約を怠慢とは評価しない。

- 列挙された主要変更・新test名は差分に存在する。nodeidの名前違いは認めなかった。
- 直接constructor 7箇所、B-2のliteral二本、1788→1803の追随は実体と一致する。
- **報告漏れはもう一つのsink pin**。1775の残存はconsumer実測で赤になった。段3の「追加の数値pinは見つからなかった」という探索結果も訂正が必要。
- resource分類は報告でも未確認とされている。実体では新readerの登録が未追加であり、「consumer波及完了」とは扱えない。
- `[missing]` の問題提起は正しい。ただし「列挙digestが変わる」のではなく、tracked欠落pathの読み取り前検査で停止する問題。
- authorのreport test直接呼出し失敗は、親consumerログでは再現する赤として報告されていない。現在の未解決赤に重複計上しない。
- 「未commit」と実装commitの存在は、親がcommitを担当した作業分担で説明でき、矛盾ではない。

## 総括

親の失敗件数と44／45解消の判定は妥当。ただし修正案は、走査時のfloor再読とreceipt削除時の拒否順序を解決していない。consumer回帰の追加pin漏れ、非層2負例の単一理由性も修正が必要。

接続正例、両木焦点緑、chain無し通常受入、変異実証、5分以内の受入は、現証拠では達成していない。

NO-GO
