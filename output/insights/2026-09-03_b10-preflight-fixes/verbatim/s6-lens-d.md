## 所見 1 — nonce 分離で再開と独立 `perf` 相が実効不能になる

深刻度: must-fix

根拠:

- `orchestrator/campaign/b10_backoff_shape_sweep.py:3389-3391` は cache root を submission nonce ごとに分離する。
- fresh な単一 `verify-perf` job では、correctness の `run_campaign(... cache_root=cache_root)` (`:3449-3464`) と性能 binary の `_perf_binary(... **build_kwargs)` (`:3502-3505`) が同じ root を使うため、意図どおりである。
- 一方、submitter と driver は独立 `verify` / `perf` 相を引き続き受理する (`tools/pegasus/submit_b10_backoff_shape.sh:61-70`, `b10_backoff_shape_sweep.py:3340-3352`)。
- 独立 `perf`、または途中終了後の新 nonce による `verify-perf` 再投入では、既存 WAL の correctness SHA (`:3474-3476`) と新 cache で再 build した SHA が cross-job 比較になる。裁定 E4 により、その bytes 一致は成立しない。
- 不一致は停止ではなく cell の `missing` へ変換され (`:3526-3539`)、create-only record として固定される (`:3581-3584`)。一度 `verify` が commit 済みなら、後続 `verify-perf` もその variant を skip するため同じ問題になる。
- `--phase build` の成果物も別 nonce の `verify-perf` から参照されず、warm-up cache としては利用不能になる。
- 追加テストは fresh な同一 file の SHA helper (`orchestrator/tests/test_b10_backoff_shape_sweep.py:802-807`) と cache 式の AST (`:810-824`) だけで、独立相・中断再開を覆わない。

成果物影響: 独立 `perf` または再投入で balanced/read-heavy の create-only block record が `missing=true` に固定され、135-cell report は受理できても選択・判定が indeterminate になる。

## 所見 2 — 歴史 45 digest gate の接続をテストしていない

深刻度: must-fix

根拠:

- production adapter は最後に `_require_legacy_record_digests(content_digests)` を呼ぶ (`orchestrator/campaign/b10_backoff_shape_sweep.py:2611-2693`, 特に `:2689`)。
- しかしテストは定数集合を同じ helper へ直接渡し (`orchestrator/tests/test_b10_backoff_shape_sweep.py:1373-1392`)、adapter については誤った campaign ID と空 records だけを渡して入口で落としている (`:1393-1399`)。
- したがって `:2689` の adapter 内 call だけを削除する M6 変異は、helper 本体を残したまま全テストを通過できる。有限 45 件への閉包が実際の report admission に接続されていることを検査していない。

成果物影響: digest call が脱落しても改変した `correctness_certified` / `median_tps` を持つ歴史 record が report に入り、judgement と選択値を変更できる。

## 所見 3 — 270 枠の「完了数」を campaign 別に開示していない

深刻度: must-fix

根拠:

- campaign ごとの disclosure object にあるのは raw `verify_done` 数と tag 数であり、campaign が寄与した `completed_logical_slots` は無い (`orchestrator/campaign/b10_backoff_shape_sweep.py:2865-2875`)。
- 完了数は全 campaign をまとめた後に `min(observed, limit)` で算出される (`:2917-2977`)。
- Markdown も総完了数 `:3143-3146` に対し、campaign ID の行では raw `verify_done` だけを表示する (`:3150-3158`)。
- 具体例は追加テスト自身にある。performance 6、legacy 1、unknown 1 の入力では raw は 8 (`orchestrator/tests/test_b10_backoff_shape_sweep.py:1562-1568`) だが完了枠は 6 (`:1573-1579`)。レポート上、名指しされた campaign は「8」、総完了数は「6」となり、その campaign の完了寄与 6 は明示されない。

成果物影響: 完了 197 等の総数を、どの campaign が何件構成したか成果物から直接監査できず、§6 (4-b) の campaign 名付き内訳を満たさない。

## 所見 4 — 270 枠の写像に必要な `variant_id` が 135-cell admission で未検査

深刻度: should-fix

根拠:

- current record validator は host・binding・格子等を検査するが、`variant_id` を検査しない (`orchestrator/campaign/b10_backoff_shape_sweep.py:2444-2513`)。
- 現に `_prior_block_record` fixture は `variant_id` を持たず (`orchestrator/tests/test_b10_backoff_shape_sweep.py:351-389`)、既存の正例で受理される (`:1347-1354`)。
- 135 gate は `(workload, block_id, point)` だけを見る (`b10_backoff_shape_sweep.py:2540-2559`)。
- 270 枠の WAL 写像は同じ record の `variant_id` に依存し、欠落・空値を黙って除外する (`:2853-2863`, `:2900-2906`)。

具体的な壊れる入力: balanced/read-heavy の 45 record が正しい格子・host・binding を持つが `variant_id` を欠く場合、135 gate は通る一方、実在する全 `verify_done` が unmapped になり、完了枠が過少計上される。

成果物影響: 135 records が揃っていても `verification_slot_completeness.completed_logical_slots` が実 WAL より小さくなり、レポートと台帳の 270/完了/未完了値が変わる。

## 所見 5 — scheduler 壁時計テストは failure branch を動かしていない

深刻度: should-fix

根拠:

- scheduler 実測値の production gate は `tools/pegasus/b10_backoff_shape_campaign.sh:284-285`。
- テストは条件の 1 行だけを正規表現で抜き、等しい 2 値で成功することだけを確認する (`orchestrator/tests/test_b10_backoff_shape_sweep.py:2268-2282`)。後続の `|| { write_failure ...; exit 2; }` は実行対象外で、異なる 2 値の拒否も試していない。
- RHS を `+ 1` に書き換えれば正規表現が一致しなくなるため、その限定変異は赤になる。ただしこれは値の拒否経路ではなく source 形状による赤である。例えば failure branch を `|| true` にしても、このテストは通る。

成果物影響: scheduler 実測値と契約値の不一致拒否が将来切断されても検出できず、短い allocation を正規 request として受理して未完了 records を生む可能性がある。

## 所見 6 — 許可外の既存テスト期待値が変更されている

深刻度: nit

根拠:

許可された現行 policy SHA と壁時計 meta-test 以外にも、次の既存期待値が変更されている。

- `orchestrator/tests/test_b10_backoff_shape_sweep.py:1131-1132` — `FORMAL_PHASES` の既存 exact tuple。
- 同 `:2186-2197` — Python invocation 一覧、phase 文字列、dependency 条件。
- 同 `:2284-2285` — 壁時計テスト内の phase 期待値。
- 同 `:2334-2353` — 既存 probe dry-run を probe/report 2 回・receipt 2 件へ変更。
- `orchestrator/tests/test_ccbench_spawn_sites.py:827-840,2597-2603` — 既存 ledger と exact assert の行番号。
- skip、assert 反転、意味的な緩和は見つからなかった。歴史 SHA は `orchestrator/tests/pegasus_policy_expected_goldens.py:8-9` のままである。

成果物影響: 直接の成果物影響は無い。この所見は親裁定の「既存期待値を変えない」制約への形式違反だけなので nit。

## 壁時計 4 consumer の追跡

4 consumer はすべて単一値 `tools/pegasus/policy.json:12` へ接続されている。

- submitter receipt producer: `tools/pegasus/submit_b10_backoff_shape.sh:200-221` → test `test_b10_backoff_shape_sweep.py:2254-2265`。式を `+ 1` にすると equality が赤。
- job receipt validator: `tools/pegasus/b10_backoff_shape_campaign.sh:191-194` → test `:2254-2264`。式を `+ 1` にすると equality が赤。
- driver receipt validator: `b10_backoff_shape_sweep.py:550-555,879-885` → test `:2266`。式を `+ 1` にすると赤。
- scheduler observed limit: job script `:284-285` → test `:2268-2282`。`+ 1` は正規表現不一致で赤だが、所見 5 のとおり拒否挙動そのものは未検査。

PBS 指示行は job script `:5` を test `:2247-2252` が独立に `hours * 3600 + minutes * 60 + seconds` で秒換算している。production 側に共通換算器は無く、同一換算器による恒真ではない。

## report と cache の確認済み事項

report 配線は以下の全層で一致している。

- driver phase 集合: `b10_backoff_shape_sweep.py:107-108,3340-3352,3610-3622`
- job script phase 正規表現・workload 拒否: `b10_backoff_shape_campaign.sh:24-30`
- submitter phase 受理・workload 拒否: `submit_b10_backoff_shape.sh:61-70`
- job receipt の phase/workload 検査: `b10_backoff_shape_campaign.sh:166-182`
- driver receipt 検査: `b10_backoff_shape_sweep.py:516-555`
- report の dependency build 省略: `b10_backoff_shape_campaign.sh:308-354`
- report だけが writer を呼ぶ: `b10_backoff_shape_sweep.py:3404-3431`
- workload 相から report writer は除去済み。

cache root は receipt path と一致検査された 32 hex nonce (`b10_backoff_shape_sweep.py:507-510,537-539`) ごとに `build-variants/b10-jobs/<nonce>` へ分かれる。同一の fresh `verify-perf` job 内では correctness/perf が同じ root を使う。別 nonce の 3 job 間の cache 競合は止まる。

新規テストに、3 本同時実行で結果が変わる共有書込みは見つからなかった。新しい report root は create-only で、2 本の report が競合すれば一方が失敗する。正式手番が report を 1 回だけ投入する限り決定的である。

## consumer test の参照関係

production 名と policy path/alias の参照を `orchestrator/tests/` から逆引きした完全な runnable test 一覧は次の 20 files。

- `orchestrator/tests/test_b10_backoff_shape_sweep.py`
- `orchestrator/tests/test_campaign.py`
- `orchestrator/tests/test_ccbench_spawn_sites.py`
- `orchestrator/tests/test_condition_meaning_gate.py`
- `orchestrator/tests/test_official_perf_closure.py`
- `orchestrator/tests/test_p3_build_authority_cli.py`
- `orchestrator/tests/test_hooks.py`
- `orchestrator/tests/test_backoff_extended_sweep.py`
- `orchestrator/tests/test_backoff_profile_pegasus.py`
- `orchestrator/tests/test_claude_transport.py`
- `orchestrator/tests/test_paper_story_a1_job_contract.py`
- `orchestrator/tests/test_pegasus_floor_tools.py`
- `orchestrator/tests/test_pegasus_policy_registry.py`
- `orchestrator/tests/test_pegasus_tools.py`
- `orchestrator/tests/test_s8b_floor_campaign.py`
- `orchestrator/tests/test_silo_ladder_rung1_driver.py`
- `orchestrator/tests/test_silo_ladder_rung1_evidence.py`
- `orchestrator/tests/test_ss2pl_lock_study.py`
- `orchestrator/tests/test_t126_pegasus_tools.py`
- `orchestrator/tests/test_t126_qualification_driver.py`

`certified_writer_fixtures.py:105-109` は runnable test ではなく、その consumer は `test_campaign.py:89`。

`tools/pegasus/policy.json` の bytes を exact pin する consumer は次の 2 files だけで、実装報告の列挙に漏れは無い。

- `test_silo_ladder_rung1_evidence.py:1265-1274`
- `test_t126_pegasus_tools.py:1461-1470`

現行 SHA は `b991c749...` に更新済み、歴史 SHA `b1c42e49...` は未変更である。

## 総括

must-fix:

- nonce cache 分離後、独立 `perf` と中断再開が cross-job SHA 不一致から create-only missing records を作る。
- 歴史 45 digest gate を adapter から外す M6 変異がテストで検出されない。
- 270 枠の完了数に campaign ID ごとの完了寄与が無く、§6 (4-b) の内訳を満たさない。

親が走らせるべき consumer test の完全な一覧:

- `test_b10_backoff_shape_sweep.py`
- `test_campaign.py`
- `test_ccbench_spawn_sites.py`
- `test_condition_meaning_gate.py`
- `test_official_perf_closure.py`
- `test_p3_build_authority_cli.py`
- `test_hooks.py`
- `test_backoff_extended_sweep.py`
- `test_backoff_profile_pegasus.py`
- `test_claude_transport.py`
- `test_paper_story_a1_job_contract.py`
- `test_pegasus_floor_tools.py`
- `test_pegasus_policy_registry.py`
- `test_pegasus_tools.py`
- `test_s8b_floor_campaign.py`
- `test_silo_ladder_rung1_driver.py`
- `test_silo_ladder_rung1_evidence.py`
- `test_ss2pl_lock_study.py`
- `test_t126_pegasus_tools.py`
- `test_t126_qualification_driver.py`

親裁定へ返すべき残件:

- R5 の nonce 分離下で、独立 `build` / `verify` / `perf` 相と cross-submission 再開を正式な受理面に残すか。現状のままなら fresh な単一 `verify-perf` 以外は安全に完遂できない。
- 次系列で再利用する歴史 campaign/binding の事前指定規則。
- R9 の設計文書訂正。
- 許可外の既存テスト期待値変更を戻す扱い。