## 変更面

- `orchestrator/campaign/p3_b4_launcher.py` — **新規**。production B-4 識別子の鋳造、admission 検証、閉じた pair、driver 継続を所有する唯一の起動器。
- `orchestrator/campaign/p3_b4_closed_critic.py` — **既存**。production factory に起動器識別子を要求し、旧 receipt-only CLI を閉じ、projection 閉包へ起動器を追加。
- `orchestrator/campaign/p3_s4_loop.py` — **既存**。`default_cfg`、`main`、`drive_iteration`、`run_one_iteration` に起動器認可を追加。
- `orchestrator/campaign/p3_s4_loop_sort.py` — **既存**。sort driver の同じ 4 境界に認可を追加。
- `orchestrator/campaign/p3_s4_loop_trigger_gating.py` — **既存**。trigger driver の 4 境界と `_run_one_iteration_resolved` に認可を追加。
- `orchestrator/tests/test_p3_b4_closed_critic.py` — **既存**。実 production factory、起動順、projection、旧 CLI、test-only 流用の負例。
- `orchestrator/tests/test_p3_s4_loop.py` — **既存**。base の marker 鋳造、直接 API、実 `main` の負例と golden 維持。
- `orchestrator/tests/test_p3_s4_loop_sort.py` — **既存**。sort の同型負例と golden 維持。
- `orchestrator/tests/test_p3_s4_loop_trigger_gating.py` — **既存**。trigger の同型負例、内部 resolved 関数の迂回、8 golden の維持。
- `docs/phase3-b4-reflux-ablation-preregistration.md` — **既存**。§7.2 の「marker は自己申告」「直接 API は開いている」を、閉じた範囲と残存限界に更新。

`CampaignConfig`、`ident.py`、WAL schema、proposal schema、critic role file は変更しない。

## 設計

現状認識は親の実測どおりだった。production の `create_b4_closed_critic_pair` 呼び手は現 `main()` 以外になく、base の `run_one_iteration` は `orchestrator/campaign/p3_s4_loop.py:1066-1182` で B-4 を見ていない。

### 封印と B-4 識別子

新 module の予定 `p3_b4_launcher.py:35-150` に次を置く。

- `_B4_IDENTIFIER_SEAL` と `_B4_TEST_IDENTIFIER_SEAL`。
- exact class の `B4LaunchIdentifier`。driver kind、admission record の SHA-256 と検証 HEAD、`production` / `test-only` を保持する。
- production 鋳造関数は module-private とし、`verify_b4_admission_record` が返した `VerifiedB4AdmissionRecord` から、起動器内部だけで呼ぶ。識別子は戻り値や標準出力へ出さない。
- 公開する試験口は `create_b4_launch_identifier_for_test()` だけとし、必ず test seal と `evidence_class="test-only"` を持たせる。
- `require_b4_config_identifier` は sealed production/test-only の双方を認め、テストが marked cfg を構築できるようにする。
- `require_b4_formal_identifier` は production seal だけを認め、factory、`main`、`drive_iteration`、`run_one_iteration` で使う。

対応する既存 idiom は `_PAIR_SEAL` / `_PRODUCTION_PAIR_SEAL` の定義 `p3_b4_closed_critic.py:132-133`、controller の exact seal 検査 `:771-797`、pair の production certification 検査 `:1070-1115`、production/test factory の分離 `:1186-1320` である。同型で実装できる。

同一 process が private global を差し替える攻撃には耐えない点も既存と同じであり、`p3_b4_closed_critic.py:160-163` の非保証を拡張して主張しない。D1042 の署名、一回性、process 間 token 化は入れない。

### marker の鋳造

3 driver の `default_cfg`、現在の `p3_s4_loop.py:892-915`、sort `:249-284`、trigger `:548-579` に内部 keyword-only 引数 `_b4_launch_identifier=None` を加える。

- `b4_reflux_ablation=False` かつ識別子なしは現在と完全に同じ処理。
- `b4_reflux_ablation=True` は sealed identifier がない限り marker を挿入しない。
- test-only identifier は cfg 構築まで許すが、formal factory / driver では拒否する。
- opaque identifier 自体は `search_config` に入れない。identity に残す bytes は現在の `B4_PROTOCOL_KEY` / `B4_PROTOCOL_VALUE`、`p3_s4_loop.py:116-118` のままとする。

これにより公開の `default_cfg(b4_reflux_ablation=True)` は識別子を自作できなくなる。marker 文字列を手で入れた `CampaignConfig` も、最下層の実行関門が production identifier 不在として拒否する。

### 起動経路

新起動器の continuation 経路は予定 `p3_b4_launcher.py:150-300` に次の順序で固定する。

1. `verify_b4_admission_record`、現 `p3_b4_admission_record.py:627-730`。
2. 検証結果に束縛した production identifier を非公開鋳造。
3. identifier を渡した各 driver の `default_cfg` から on/off cfg を構築。
4. 実 `create_b4_closed_critic_pair`、現 `p3_b4_closed_critic.py:1186-1268`。factory 側も識別子、driver kind、再検証した admission record との一致を再確認する。
5. pair の両 controller を invoke し、現 `assert_b4_certified_arm_pair`、`:1810-1890` を通す。
6. 選択 arm の terminal receipt を提示した後、stdin の固定 JSON handshake で proposal path を受け取る。
7. registry に保持した実 driver の `main` を、`--b4-reflux-ablation`、固定 arm、proposal、receipt、build authority と、非公開 identifier 付きで呼ぶ。

proposal は新 receipt の SHA-256 を含む必要があるため、factory より前に固定内容として受け取れない。現 gate は base `p3_s4_loop.py:1380-1396`、sort `p3_s4_loop_sort.py:380-400`、trigger `p3_s4_loop_trigger_gating.py:854-876` にある。stdin handshake は receipt 後も同じ launcher process を維持し、identifier を外へ渡さないためのものとする。proposal bytes の固定や、critic 決定との因果束縛は追加しない。

bootstrap は現 `b4_bootstrap` / receipt 禁止 `p3_s4_loop.py:1197-1233` のため pair を作れない。起動器に明示的な `bootstrap` subcommand を置き、admission 検証、identifier 鋳造、実 driver `main` の順で receipt なしの初回だけを走らせる。直接 driver CLI からの bootstrap は同じ production identifier 不在で拒否する。

### 認可の受け渡し

- base: `main` `p3_s4_loop.py:1534-1770` → `drive_iteration` `:1423-1531` → `run_one_iteration` `:1066-1182`。
- sort: `main` `p3_s4_loop_sort.py:540-685` → `drive_iteration` `:423-517` → `run_one_iteration` `:299-354`。
- trigger: `main` `p3_s4_loop_trigger_gating.py:1072-1227` → `drive_iteration` `:899-1053` → `_run_one_iteration_resolved` `:692-790`。公開 `run_one_iteration` `:793-829` にも独立関門を置く。

各境界で exact message を変える。上位関門だけを除去しても下位の別メッセージになるため、変異検査が過剰決定されない。

## 手順

1. `p3_b4_launcher.py:1-300` に identifier、検証器、driver registry、bootstrap / continuation を追加する。単独で壊しうる既存検査は、動的に新 module を読む `test_campaign_import_invariant.py:1001-1043`、`test_ccbench_spawn_sites.py:303-315`、`test_p3_exploration_namespace.py:123-149`。
2. `p3_b4_closed_critic.py:77-106,610-668,1186-1320,1893-2000` を変更する。production/test factory に対応 seal を要求し、旧 config factory / receipt-only `main` を除去または hard-fail 化する。既存 `test_p3_b4_closed_critic.py:307-1206,1554-1639,2212-2307,2590-2725` が影響する。
3. base の `default_cfg` `p3_s4_loop.py:892-915` と `run_one_iteration` / `drive_iteration` / `main` `:1066-1182,1423-1531,1534-1770` に identifier を通す。既存 B-4 tests `test_p3_s4_loop.py:2475-2845` は test-only identifier fixture へ移行する。
4. sort の対応面 `p3_s4_loop_sort.py:249-354,423-517,540-685` を同型化する。`test_p3_s4_loop_sort.py:854-1058` が単独で壊れうる。
5. trigger の対応面 `p3_s4_loop_trigger_gating.py:548-579,692-829,899-1053,1072-1227` を同型化する。特に `drive_iteration` が公開関数を通らず `_run_one_iteration_resolved` を呼ぶ `:1011-1018` を見落とさない。`test_p3_s4_loop_trigger_gating.py:2677-2915` が影響する。
6. `test_p3_b4_closed_critic.py:1554-1617` の projection exact set に launcher を追加し、同 file `:2190-2725` に launcher の順序検査、actual factory の負例、production caller AST census を置く。
7. 3 driver test の既存 golden を保持しつつ、下記の actual entity 負例を追加する。ordering test で factory と driver を stub する場合、それは順序だけの証拠と明記し、負例の代用にしない。
8. `docs/phase3-b4-reflux-ablation-preregistration.md:277-315` を更新する。直接 API と marker 自己申告の 2 項を閉じた面へ移し、proposal 因果束縛、PATH、pair 完全性、file-drawer、same-process 書換えは残す。

## 負例一覧

1. **`default_cfg(..., b4_reflux_ablation=True)` の自作**

   - 呼び方: 3 driver の実 `default_cfg` を identifier なしで呼ぶ。
   - どこで落ちるか: base `p3_s4_loop.py:892-904`、sort `p3_s4_loop_sort.py:249-272`、trigger `p3_s4_loop_trigger_gating.py:548-567` の marker 挿入直前。
   - 例外: `B4LauncherAuthorizationError("B-4 marker creation requires a sealed launcher identifier")`。
   - 検査: 各 driver test file の B-4 節。
   - 検査除去変異を殺すテスト: `test_b4_default_cfg_rejects_unsealed_marker_creation`、sort / trigger の同名 test。

2. **marked cfg で `run_one_iteration` を直接呼ぶ**

   - 呼び方: test helper で marker だけ持つ cfg を作り、identifier なしで実関数を呼ぶ。trigger は公開関数と `_run_one_iteration_resolved` の両方を検査する。
   - どこで落ちるか: base `p3_s4_loop.py:1066`、sort `p3_s4_loop_sort.py:299`、trigger `p3_s4_loop_trigger_gating.py:692,793` の先頭。`layout.ensure`、quarantine、WAL より前。
   - 例外: `B4LauncherAuthorizationError("B-4 run_one_iteration requires a production launcher identifier")`。
   - 検査: それぞれの driver test file。
   - 検査除去変異を殺すテスト: `test_b4_marked_run_one_iteration_direct_call_requires_launcher`、trigger の `test_b4_resolved_iteration_cannot_bypass_launcher`。

3. **`drive_iteration` の直接呼び**

   - 呼び方: marked cfg、receipt または bootstrap state を与えるが identifier は渡さない。
   - どこで落ちるか: base `p3_s4_loop.py:1423`、sort `p3_s4_loop_sort.py:423`、trigger `p3_s4_loop_trigger_gating.py:899` の先頭。
   - 例外: `B4LauncherAuthorizationError("B-4 drive_iteration requires a production launcher identifier")`。
   - 検査: 各 driver test file。
   - 検査除去変異を殺すテスト: `test_b4_drive_iteration_direct_call_requires_launcher`。下層の別メッセージでは合格しない exact match とする。

4. **3 driver の実 `main(["--b4-reflux-ablation", ...])` を直接呼ぶ**

   - 呼び方: 有効な `--run-iteration` 形を与えるが hidden identifier は渡さない。
   - どこで落ちるか: base `p3_s4_loop.py:1566`、sort `p3_s4_loop_sort.py:569`、trigger `p3_s4_loop_trigger_gating.py:1108` の parse 直後。
   - 例外: `B4LauncherAuthorizationError("B-4 driver main requires a production launcher identifier")`。
   - 検査: `test_p3_s4_loop.py`、sort、trigger の各 test file。実 `main` を呼び、build helper が未到達であることも spy で確認する。
   - 検査除去変異を殺すテスト: `test_b4_driver_main_rejects_direct_cli_without_launcher` の各 node。main 関門を外すと `default_cfg` の異なる message へ進むため赤になる。

5. **production factory の直接使用**

   - 呼び方: 実 `create_b4_closed_critic_pair` に marked cfg を渡すが production identifier を渡さない。
   - どこで落ちるか: `p3_b4_closed_critic.py:1186-1197`、admission record 読取や artifact root 作成より前。
   - 例外: `B4LauncherAuthorizationError("B-4 production pair factory requires a production launcher identifier")`。
   - 検査: `test_p3_b4_closed_critic.py`。factory 自体は stub にしない。
   - 検査除去変異を殺すテスト: `test_real_production_pair_factory_requires_launcher_identifier`。

6. **test-only 鋳造口の formal 流用**

   - 呼び方: 実 `create_b4_launch_identifier_for_test()` で得た値を production factory または実 driver `main` に渡す。
   - どこで落ちるか: 新 `p3_b4_launcher.py:90-150` の formal verifier。factory と各 driver の最上位境界から呼ぶ。
   - 例外: `B4LauncherAuthorizationError("test-only B-4 launcher identifier cannot authorize a formal sample")`。
   - 検査: factory は `test_p3_b4_closed_critic.py`、driver は各 driver test file。
   - 検査除去変異を殺すテスト: `test_test_only_identifier_cannot_enter_production_factory` と各 `test_b4_driver_main_rejects_test_only_identifier`。

7. **旧 `p3_b4_closed_critic.main()` の receipt-only 起動**

   - 呼び方: 現在の CLI 引数 `--driver`、`--artifact-root`、`--admission-record` で直接呼ぶ。
   - どこで落ちるか: `p3_b4_closed_critic.py:1941`。
   - 例外: `B4LauncherAuthorizationError("B-4 production runs require orchestrator.campaign.p3_b4_launcher")`。
   - 検査: `test_p3_b4_closed_critic.py`。
   - 検査除去変異を殺すテスト: `test_legacy_closed_critic_cli_cannot_mint_a_b4_identifier`。

## 不変条件の維持

- ordinary branch では識別子検査を呼ばず、現在の `search_config` 構築を一字も変えない。base `p3_s4_loop.py:899-915`、sort `p3_s4_loop_sort.py:263-284`、trigger `p3_s4_loop_trigger_gating.py:558-579` が根拠となる。
- identifier は `search_config` や `CampaignConfig` に保存しない。`ident.canonical_preimage` が identity に含めるのは `search_config` の値だけである `ident.py:150-177`。
- base golden は `test_p3_s4_loop.py:2475-2494` の `2cd75697` / `9f43a5b8`、sort は `test_p3_s4_loop_sort.py:854-870` の `081dd46f`、trigger は同 test file `:112-134` の 8 件をそのまま exact assertion として残す。
- 新関門は既存処理より前に追加するだけで、base の quarantine から `run_campaign` への順序 `p3_s4_loop.py:1096-1170`、sort `p3_s4_loop_sort.py:311-342`、trigger `p3_s4_loop_trigger_gating.py:703-753` は動かさない。
- 既存 receipt 照合と一回消費 `p3_s4_loop.py:1210-1316`、proposal reject、verifier、build/verify/bench、WAL payload は変更しない。受理集合は増えない。
- `.claude/agents/critic.md`、proposal schema、WAL schema には触れない。

## 未決と推奨

### P3: 既存 `p3_b4_closed_critic.main()` は置き換える

親の「上位に置いて receipt 部品として残す」は修正を推奨する。現在の `main` は `p3_b4_closed_critic.py:1941-1985` で自ら marked cfg を作るため、外部から生かしたままでは第二の鋳造入口になる。

production factory と controller は部品として残すが、旧 CLI `main` は専用起動器への案内を伴う hard failure にする。receipt-only の実装本体を公開 production entry として残さない。これで production factory の production caller は新 launcher 1 件だけになり、AST census で exact に固定できる。

### P4: launcher を projection 閉包へ入れる

入れることを推奨する。新 launcher の bytes は「誰が marker を鋳造できるか」「factory と実 driver の接続」を決める実験装置そのものだからである。

変更点は `p3_b4_closed_critic.py:77-106` に launcher path 定数、`:610-663` の全 driver 共通 entries への追加。影響は以下。

- factory 作成時の期待値 `:1150-1159`
- invocation 中の live 再確認 `:870-873`
- receipt 再読時の current bytes 照合 `:1590-1591`
- admission expectation `:1883-1888`
- exact manifest test `test_p3_b4_closed_critic.py:1554-1617`

既存 receipt の projection hash は意図的に失効する。既存 admission record の expected projection も更新、commit されるまで formal run は fail-closed になる。literal hash pin はないため、golden campaign identity には影響しない。

### module 内容走査

新 module を自動発見する走査は存在する。

- import / namespace 全走査: `test_campaign_import_invariant.py:1001-1043`
- process 起動 exact census: `test_ccbench_spawn_sites.py:303-315,458-506`
- campaign root creator 発見: `test_p3_exploration_namespace.py:123-149`
- build CLI 内容走査: `test_p3_build_authority_cli.py:1189-1195`
- certified writer census: `test_campaign.py:5128-5165`
- build/materializer census: `test_s8b_floor_campaign.py:6088-6157`
- WAL commit / capability issuer census: `test_t1286_commit_receipt.py:657-702`
- その他の target-name 全走査: `test_s8b_oracle_manifest_contract.py:39-84`、`test_s8b_floor_stats.py:848-874`、`test_s8b_oracle_report.py:5488-5508`、`test_s8b_ratified_freeze.py:2375-2385`、`test_pegasus_dispatch_compute.py:2232-2245`、`test_t338_submission_gate_unit5.py:490-514`、`test_login_headroom.py:1625-1643`。

launcher は subprocess を起動せず、`run_campaign`、`CampaignLayout`、WAL writer、build API を直接呼ばず、実 driver `main` へ委譲する。そのため既存 allowlist の追記は不要である。追随編集が必要なのは projection exact set と、新たに置く B-4 factory caller census だけと見込む。

## 総括

production B-4 識別子は admission 検証後に専用 launcher 内だけで鋳造し、外へ渡さない。  
production factory、3 driver の `main`、`drive_iteration`、最下層 iteration の全境界で同じ sealed identifier を要求する。  
test-only 口は cfg fixture 作成には使えるが、formal sample では exact error で拒否する。  
P3 は旧 receipt-only CLI の閉鎖、P4 は launcher bytes の projection 採用を推奨する。  
実装、pytest、書込みは行っていない。今回の結論は指定資料と repository の静的確認だけに基づく。