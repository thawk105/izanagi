## 変更面

| file:line | 現状 | 変更後 |
|---|---|---|
| `tools/dev_wave_wait.py:231` | outer receipt は `dev-wave-acceptance-receipt/v3`。 | `v4` へ上げる。v3 fallback は設けない。 |
| `tools/dev_wave_wait.py:290,1951-2013` | `_red_gate_blob_sha` は revision を受け取るが、対象 path は `_RED_CHECKER_PATH` に固定。 | `path` を keyword-only 引数にし、checker 呼出しでは `_RED_CHECKER_PATH` を明示する。flake がある場合だけ同じ関数で `tested_main:tools/run_tests.py` と `tested_tip:tools/run_tests.py` を解決し、blob SHA の等値を要求する。SHA を receipt へ保存せず、識別子も増やさない。 |
| `tools/dev_wave_wait.py:400-406` | `_RedCheckResult` は `red_nodeids` だけを持つ。 | `flake_nodeids: tuple[str, ...]` を追加する。 |
| `tools/dev_wave_wait.py:2720-2822` | JSON 読取、root schema、collection、node の検査が I/O 関数内に埋め込まれ、node は非帰属 3 field だけを許す。 | 純粋関数 `_red_check_payload_nodeids(payload, *, tested_main, tested_tip, log_sha256)` を切り出す。実 producer を `json.loads` した object をそのまま渡し、`(red_nodeids, flake_nodeids)` を返す test seam とする。I/O、Git、時刻には触れない。 |
| `tools/dev_wave_wait.py:2762-2822` | `classification == "non-attributable"`、3 field、`rerun_rc` は int なら値を問わない。 | 非帰属は field 集合が exactly `{"classification","nodeid","rerun_rc"}`、分類が `non-attributable`、空でない文字列 nodeid、`type(rerun_rc) is int and rerun_rc == 1`。flake は exactly `{"classification","main_rerun_rc","nodeid","rerun_rc","wave_rerun_rc"}`、分類が `flake`、3 rc 全て `type(...) is int and ... == 0`。attributable、bool、欠落、余分 field、他の rc は全て `_StageFailure("acceptance-red-check")`。 |
| `tools/dev_wave_wait.py:2802-2822` | 1 集合だけを sorted・unique 検査する。 | 2 集合を別々に sorted・unique 検査し、相互に素であることも検査する。flake が非空なら、その後に runner blob 等値 gate を通してから `_RedCheckResult` を返す。 |
| `tools/dev_wave_wait.py:2493-2643` | `non-attributable-only` は `red_nodeids` が非空のときだけ成立。診断は `red_nodeid_count` だけ。 | `red_nodeids ∪ flake_nodeids` が非空なら成立する。診断へ `flake_nodeid_count` を追加し、両方空、red check 不在、child rc 不一致を区別する。outer receipt へ `flake_nodeids` を追加し、child-green では両集合を `[]` にする。 |
| `tools/dev_wave_wait.py:3177-3215` | red check 結果を outer receipt へ渡す。 | 呼出し形は維持し、flake 集合と runner gate 済みの `_RedCheckResult` を渡す。red-only と child-green では runner main/tip 比較を起動しない。 |
| `tools/dev_wave_land.py:70-96` | schema v3、exact field 集合に `red_nodeids` だけ。 | schema v4、exact field 集合へ `flake_nodeids` を追加する。 |
| `tools/dev_wave_land.py:141-170` | `LandResult` と JSON は `acceptance_red_nodeids` だけ。 | `acceptance_flake_nodeids: tuple[str, ...] | None` を追加し、`as_json()` では `None` または list として出す。 |
| `tools/dev_wave_land.py:258-263` | `_AcceptanceVerification` は red 集合だけ。 | `flake_nodeids` を追加し、2 集合を最後まで分離する。 |
| `tools/dev_wave_land.py:608-690` | child-green は red が空、非帰属経路は red が非空・sorted・unique なら受理。 | child-green は red と flake がともに空。非帰属経路は両方が list、各々 sorted・unique・全要素が空でない文字列、相互に素、和集合が非空であることを要求する。checker rc/status/hash の既存条件は緩めない。 |
| `tools/dev_wave_land.py:691-748` | tip の runner は `cat-file -e` で存在確認だけ。checker は非帰属経路で main/tip blob 等値を検査。 | 既存の tip 存在確認は全経路で維持する。flake 非空時だけ main/tip の runner を `rev-parse` し、checker blob 検査と同じ `receipt_git_results` の失敗処理へ加える。Git 失敗は retryable、SHA 不正・不一致は通常の acceptance reject。red-only と child-green の受理集合は変えない。 |
| `tools/dev_wave_land.py:749-765` | verification から red 集合だけを結果へ伝搬。 | red と flake を `_AcceptanceVerification` → `_with_acceptance_verification` → `LandResult` → JSON の全閉包で伝搬する。 |
| `tools/dev_wave_land.py:562-589,3391-3429` | `_release_authority_digest` も共有 exact parser を通る。 | 関数固有の新 field 検査は足さず、v4 exact field 集合を共有する。pre-land と post-land 再読の両 call siteが同じ v4 receipt digest を受理することを実 receipt テストで pin する。 |
| `tools/check_acceptance_reds.py:940-1000,1340-1410,1500-1610` | 既に非帰属 3 field、flake 5 field、attributable 5 fieldを生成し、再走 rc を `{0,1}` に限定。 | 変更しない。rc exact pin は破損 receipt と将来 drift への防御深度であり、現 producer の受理集合を狭めるものではない。 |
| `orchestrator/tests/test_dev_wave_wait.py:606-819,1734-1777,2397-2560,3150-3335,3480-3562,8211-8235` | fixture、schema pin、red-only 検査。 | v4、2 集合、exact node 述語、runner gate、診断 fieldを更新し、正負テストを追加する。 |
| `orchestrator/tests/test_dev_wave_land.py:216-267,424-446,690-1240` | v3 相当 fixtureと red-only land。 | 全 fixtureへ `flake_nodeids` を追加し、flake-only、mixed、runner 不一致、release-authority、結果 JSONを検査する。 |
| `orchestrator/tests/test_dev_wave_land.py:3739-3777,6071-6080,6558-6576` | `LandResult` の exact equality、既定 JSON、64 KiB 境界が現 field 数を前提とする。 | 空 tupleまたは `None` の `acceptance_flake_nodeids` を期待値へ追加し、compact JSON の境界用 fillerを再計算する。 |
| `orchestrator/tests/test_check_acceptance_reds.py:460-646` | 実 producer は3分類の exact dictを既に検査するが、waiter consumerへ渡していない。 | 実際に書かれた3分類の JSONを純粋 consumer 述語へそのまま渡す。root field集合と node field集合はテスト内の独立 literalで固定する。 |
| `docs/pegasus-runbook.md:833-843,878-882` | 経路(ii)は非帰属だけを説明し、台帳指示は `red_nodeids` だけ。 | flake 観測分類、別集合、runner blob gate、残余、台帳への両集合記録を明記する。 |
| `docs/spool/decisions/...:new` | D371/D389 は現行本文のまま。 | 新 D fragmentで両 D の部分改訂、v4、残余受容、P7を記録する。既存本文は書き換えない。 |
| `docs/spool/worklog/...:new` | T-1302 は active。 | 新 Dへの参照とユーザー裁定を記録し、実装・受入完了時に T-1302 を `完了` にする。 |

grep で確認した outer schema 閉包は次の通りです。

- 生きた schema v3 literal は実装・テストで4 hitです。producer 1件、runtime consumer 1件、wait test pin 2件です。
- canonical docsには D393 の歴史記述が1 hitあります。既存 D は変更せず、新 Dからv4移行を記録します。
- runtime consumer は `tools/dev_wave_land.py` 1 file、入口2関数、call site 3箇所です。`_verify_acceptance_receipt` が1箇所、`_release_authority_digest` がpre-landとpost-land再読の2箇所です。
- land test fixtureは schema文字列を定数から得るためliteral grepには出ませんが、exact field集合へ `flake_nodeids` を足さない限り全fixture由来receiptが拒否されます。
- 既発行のv3 receiptは意図的に全て拒否されます。再利用やfallbackは行わず、新waiterで受入を撮り直します。

P7 の具体例は次です。

- 正例: tested main `A` と tested tip `B` が異なるcommitでも、差分が `wave.txt` だけで `A:tools/run_tests.py` と `B:tools/run_tests.py` が同じblob `X`、checker nodeがflake形で3 rc全て0なら、waiterとlandの両方を通します。
- 負例: tip側 `tools/run_tests.py` を1 byte変更してblobが `X != Y` になった場合、同じflake payloadでもwaiterはouter receipt発行前に `_StageFailure`、crafted v4 receiptをlandへ直接渡してもmainを動かさずrejectします。

## 実装順序

1. `tools/dev_wave_wait.py` に純粋 payload 述語と `_RedCheckResult.flake_nodeids` を入れます。ここで2 node形、整列、一意、相互排他を確定します。
2. `_red_gate_blob_sha` をpath指定可能にし、既存checker束縛を同値に保ったまま、flake限定runner gateを追加します。
3. waiterのverdict、診断、outer receiptを2集合対応にし、schemaをv4へ上げます。
4. 同じ差分単位でlandのschema、exact parser、verdict、runner gate、結果伝搬をv4対応にします。producerだけ、またはconsumerだけが先行した状態でcommitしません。
5. checker実 producerの3分類を純粋 consumerへ通す相互pinを先に追加し、その後にwaiterとlandの攻撃テスト、実process end-to-endを追加します。
6. 親がrunbook、decisions fragment、worklog fragmentを追加します。実装子はコードとテストだけを扱います。
7. 親が `python3 tools/run_tests.py` 経由で3 test fileを実測し、`check_codex_agents.py`、`check_docs.py`、commit後のprovenance検査を行います。このread-only段では緑を主張しません。

## テスト計画

### `orchestrator/tests/test_dev_wave_wait.py`

| test名 | 主張 | 偽緑にならない理由 |
|---|---|---|
| `test_success_receipt_binds_tip_argv_rc_fingerprints_holder_waiter_and_scheduler` | exact root field集合に `flake_nodeids` があり、schemaがliteral v4、child-greenでは両集合が空。 | field集合とversionを独立literalで比較するため、producer定数から期待値を生成しない。 |
| `test_red_check_payload_accepts_exact_supported_node_shapes` | 非帰属とflakeを混在させ、別々のliteral tupleへ分類する。 | consumer本体を直接呼び、補助fixtureの分類結果とは比較しない。 |
| `test_red_check_payload_rejects_non_exact_node_shapes` | 欠落、余分field、attributable、空nodeid、bool、非帰属rc 0/2、flake各rc非0を全て `_StageFailure` にする。 | 1 fieldずつ壊す攻撃表で、単なる正常系dict比較ではない。 |
| `test_red_check_payload_rejects_unsorted_duplicate_or_overlapping_sets` | 各集合の非整列・重複と集合間重複を拒否する。 | producerのsort helperを使わず、壊れた順序をliteralで渡す。 |
| `test_non_attributable_only_publishes_receipt_with_real_child_rc` | red-onlyは従来どおり通り、`flake_nodeids == []`、runner blob lookupは起動しない。 | `_run_acceptance` の全event列をdrainするため、余分なgate発火も検出する。 |
| `test_red_checker_different_commits_same_checker_blob_is_accepted` | main/tipが異なってもred-onlyならrunner等値を新要求しない。 | fake Gitの予定外runner queryが即失敗するため、P7の範囲拡大を検出する。 |
| `test_flake_only_publishes_v4_receipt_with_separate_nodeids` | runner blob同一のflake-onlyがouter v4を発行し、redは空、flakeだけが残る。 | checker receiptからouter publishまで実際のwaiter制御経路を通す。 |
| `test_flake_runner_blob_mismatch_rejects_before_outer_receipt` | main/tip runner blob不一致でstage 70、final receiptなし、lease cleanup。 | mismatchをGit応答で実在させ、述語のmonkeypatchで結果を作らない。 |
| `test_acceptance_receipt_consistency_detail` | 和集合空を拒否し、診断にred/flake両countが出る。 | detail JSONをexact literalで比較する。 |
| `test_real_waiter_process_accepts_merged_tip_with_same_waiter_bytes` | real waiter processがschema v4 receiptを出す。 | private helperだけでなく別processが書いた実fileを読む。 |

### `orchestrator/tests/test_dev_wave_land.py`

| test名 | 主張 | 偽緑にならない理由 |
|---|---|---|
| `test_land_accepts_receipt_bound_to_wave_tip_and_emits_digest` | child-green結果にred/flakeの空tupleと空listが出る。 | 実Git fixtureをlandし、結果objectとJSONの両方を見る。 |
| `test_land_rejects_tampered_acceptance_receipt` | `flake_nodeids` 欠落とv3をexact parserが拒否する。 | 実receipt bytesを改変し、main HEAD不変まで確認する。 |
| `test_land_rejects_verdict_field_inconsistency` | child-greenのflake非空、両集合空、flake非整列・重複・非文字列、red/flake重複を拒否。 | 各mutation後にlandを実行し、parser helperのboolだけを検査しない。 |
| `test_land_accepts_non_attributable_receipt_and_emits_red_nodeids` | red-onlyを維持し、flake結果は空。 | v4 exact parserから結果JSONまで通す。 |
| `test_land_accepts_flake_receipt_with_equal_runner_blobs_and_emits_flake_nodeids` | runner同一のflake-onlyを受理し、`acceptance_flake_nodeids` だけへ出す。 | main/tipの実Git blobをland自身に再計算させる。 |
| `test_land_accepts_mixed_red_and_flake_nodeids_without_merging_sets` | mixed集合を別々に保持し、和集合だけでverdict成立を判断する。 | 出力期待値を2つの独立literal tuple/listで比較する。 |
| `test_land_rejects_flake_receipt_with_divergent_runner_blobs` | tip runner変更時にflake receiptを拒否し、main HEAD不変。 | receiptにSHAを埋めず、実commitのblob差をlandに再計算させる。 |
| `test_land_red_only_path_does_not_require_runner_blob_equality` | runnerが異なってもflake空のred-only受理集合は変わらない。 | P7 guard条件を反対側からpinする。 |
| `test_real_v4_flake_waiter_receipt_passes_release_authority_and_land` | real checkerがflakeを生成し、real waiterのv4 receiptが `_release_authority_digest` とreal landの双方を通る。 | synthetic outer dictを使わず、producer processが書いた同じbytesを2 consumerへ渡す。 |
| `test_zero_fragment_preserves_land_result_and_commit_graph_bit_for_bit` | exact `LandResult` 期待値へ空flake tupleを含める。 | dataclass equalityで伝搬漏れを検出する。 |
| `test_land_result_release_contract_defaults_fail_closed_and_is_in_json` | 未検証結果は `acceptance_flake_nodeids is None`。 | JSON fieldの存在と値を直接検査する。 |
| `test_compact_core_json_preserves_legacy_64k_message_boundary` | 新JSON field追加後も境界条件を維持する。 | 実serial化bytes長に対して境界を再計算する。 |

### `orchestrator/tests/test_check_acceptance_reds.py`

次の既存3 testをF366の相互pinへ拡張します。root field集合とnode field集合はテスト内の独立literalとし、producer AST、waiter helper、schema定数から生成しません。

| test名 | 主張 | 偽緑にならない理由 |
|---|---|---|
| `test_main_green_wave_red_is_attributable` | 実producerのattributable 5 field receiptをそのままwaiter述語へ渡すと `_StageFailure`。 | `CAR.main` が実fileへ書いたJSONを読み、synthetic dictへ置換しない。 |
| `test_main_green_wave_green_is_recorded_as_flake` | 実producerのflake 5 field、3 rc全0が `red=(), flake=(nodeid,)` になる。 | producerのfull dictを独立literalで先に固定してから実consumerへ渡す。 |
| `test_main_red_is_non_attributable_without_wave_rerun` | 実producerの非帰属3 field、`rerun_rc==1` が `red=(nodeid,), flake=()` になる。 | 実producerの書込bytesと実consumer述語を接続し、両者共通helperを期待値生成に使わない。 |

## docs 案

`docs/pegasus-runbook.md:833-843` の置換案です。

```markdown
- **受理は 2 経路ある ([T-1019] / 2026-08-13 第 9 束 #1)。**
  (i) 受入 command が rc=0 → `verdict = "child-green"`。
  (ii) 受入 command が **rc=1 ちょうど**で、
  `tools/check_acceptance_reds.py` が rc=0 かつ `status = "non-attributable-only"` を返し、
  その receipt の `log_sha256` が待ち手の捕獲 log と一致し、
  `red_nodeids ∪ flake_nodeids` が非空 →
  `verdict = "non-attributable-only"`。非帰属 node は
  `classification` / `nodeid` / `rerun_rc` の 3 field で `rerun_rc == 1`、
  flake node は `classification` / `main_rerun_rc` / `nodeid` / `rerun_rc` /
  `wave_rerun_rc` の 5 field で 3 個の rc が全て 0 でなければならない。
  `red_nodeids` と `flake_nodeids` は各々 sorted・unique で互いに素とし、receipt と
  land 結果 JSONへ別々に残す。`flake` は原因分類ではなく「初回全走は赤、main 単独再走は緑、
  wave tip 単独再走も緑」という観測分類である。`flake_nodeids` が非空なら、待ち手と land は
  `tested_main:tools/run_tests.py` と `tested_tip:tools/run_tests.py` の blob 等値を Git から
  再計算して要求する。この SHA を receipt fieldへ追加しない。
  rc が 0 でも 1 でもない非 0 (`_DELETION_GATE_RC = 13` / `_PEGASUS_DISPATCH_RC = 16` /
  signal 由来など) は**テスト失敗以外の理由で落ちた走行**なので受理しない。
  checker の `status = "green"`、rc=1、rc=2も受理しない。
```

`docs/pegasus-runbook.md:878-882` の置換案です。

```markdown
- **rc=0 は「receipt が発行され、lease を保持したまま返った」を意味する。**
  受入 command 自身が緑だったとは限らない。受理経路 (ii) では初回全走が rc=1 であり、
  `red_nodeids` または `flake_nodeids` が残る。**台帳へ「全テスト緑」と書く前に receipt の
  `verdict`、`red_nodeids`、`flake_nodeids` を読み、`verdict = "non-attributable-only"` なら
  2 集合を別々に台帳へ記録すること。** 成功時は release しない。
  **land の終端で親が `release --wave "$W"` する**こと。それ以外の終わり方では待ち手が
  release する。
```

`docs/spool/decisions/2026-08-17-dev-wave-t1302-r2-nonattrib-1.md` 案です。

```markdown
---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-17
wave: dev-wave-t1302-r2-nonattrib
seq: 1
---

## {{D:r2-flake-observation}}. R2 の flake を別集合で受理し runner 同一性を要求する

**決定:** D371 と D389 を次の範囲で部分改訂する。

- 初回受入全走が `child_rc == 1` であり、checker が
  `rc == 0` かつ `status == "non-attributable-only"`、捕獲 log の hash 一致を満たすという
  D389 の条件は全て維持する。
- tested main 単独再走が rc=1 の node は `red_nodeids`、main と wave tip の単独再走が
  いずれも rc=0 の nodeは `flake_nodeids` へ分ける。verdict名は
  `non-attributable-only` のままとし、両集合の和集合が非空のときだけ成立する。
- 非帰属 node は exact 3 fieldかつ `rerun_rc == 1`、flake nodeは exact 5 fieldかつ
  `main_rerun_rc == rerun_rc == wave_rerun_rc == 0` とする。各集合は sorted・unique、
  相互に素とし、outer receipt、land結果JSON、台帳まで分離を保つ。
- outer receiptを `dev-wave-acceptance-receipt/v4` へ上げ、v3 fallbackは設けない。
- flakeが1件以上ある場合だけ、待ち手とlandの両方が
  `tested_main:tools/run_tests.py` と `tested_tip:tools/run_tests.py` のblob等値をGitから
  再計算して要求する。新しいreceipt fieldや永続識別子は作らない。
- `tools/check_acceptance_reds.py` は変更しない。rc値のexact pinは、現producerに対する
  narrowingではなく、破損receiptと将来driftへの防御深度である。

**理由:**
- flake 1件で受入全走を捨て続ける構造を解きつつ、非帰属とflakeを監査可能な別集合として残せる。
- flakeはwave側runnerが返したrc=0を新たに受入証拠として使う経路であるため、そのrunnerを
  mainと同じblobへ束縛する必要がある。
- checkerの実producer出力とwaiterのexact consumer述語を相互pinし、F366と同型の
  producer・consumer driftを恒久検出する。

**明示的に受容する残余:**
- flakeは原因ではなく観測の分類である。production code、`conftest.py`、共有fixture、
  pytest plugin、test file自身、`tools/run_tests.py` 以外の選択・build設定、
  初回と再走のargvや環境差、負荷や外部汚染による全走限定赤を区別しない。
- このため決定的な赤もflakeとして通りうる。差分到達可能性の完全な写像が無い限り
  この残余は閉じられない。検査を消して緑を買う変更は許さない。

**却下した選択肢:**
- flakeを `red_nodeids` へ混ぜる — 観測差がreceiptと台帳から失われる。
- 新しいverdict名を作る — 受理条件は集合で十分に表現でき、consumer閉包だけを増やす。
- flakeを従来どおり拒否する — R2が発効せず、受入全走を捨て続ける。
- runner blobをreceiptへ書く — landがGitから再計算でき、自己申告fieldを増やす必要がない。
```

`docs/spool/worklog/2026-08-17-dev-wave-t1302-r2-nonattrib-2.md` 案です。`base` は現在のT-1302本文から算出した値で、先行waveが同項目を更新した場合は再計算が必要です。

```markdown
---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-17
wave: dev-wave-t1302-r2-nonattrib
seq: 2
title: 非帰属 checker の R2 を flake 観測付きで発効する (コード + docs、branch dev-wave-t1302-r2-nonattrib)
---

## 本文

- ユーザー裁定 R2 の flake 別集合化、観測分類としての残余受容、flake限定runner束縛を
  {{D:r2-flake-observation}} に記録した。
- 変更前の焦点走は 503 passed / 2 failed で、赤2件はlogin nodeのdispatch経路に由来する
  変更前からの環境赤だった。変更後の受入ではこのbaselineとの差分を親が判定した。

## 次の一手差分

### 完了

- [T-1302] 非帰属 checker の R2 を、waiter・outer receipt v4・land・3 test file・runbook・
  decisionの閉包で発効した。flakeは別集合で追跡し、flake経路のrunner main/tip blobを束縛した。
  remaining: none
  base: d22493a12155e80c0b1989e409764ecfc36853018b84b008383bb1b8a7281fe4
```

## リスク

| リスク | 対応 |
|---|---|
| 発行済みv3 receipt | v4 landとrelease-authorityで拒否される。意図したfail-closedであり、新waiterから撮り直す。 |
| schema consumer取り残し | runtimeはlandの2入口、3 call site。wait側2 schema assertion、land fixture、release-authority testも同じ変更で更新する。 |
| 結果伝搬の欠落 | `_RedCheckResult`、outer JSON、land local変数、`_AcceptanceVerification`、`LandResult`、`as_json` の順に2集合を追跡する。 |
| runner gateの過剰適用 | flake非空だけを条件にし、red-onlyでGit queryが増えないテストと、child-green既存テストでpinする。 |
| waiterだけ、またはlandだけのgate | 同じblob不一致を両層で独立に拒否する。crafted receiptでwaiterを飛ばしてもlandが閉じる。 |
| producer・consumerの共倒れ比較 | 実producer JSON、独立literal field集合、実consumerの3点比較にし、ASTや共通helperから期待集合を作らない。 |
| `LandResult` field追加による既存テスト赤 | exact dataclass equality、既定JSON、64 KiB境界テストを更新する。 |
| D393のv3記述 | 歴史的既存Dは書き換えず、新Dを部分改訂の正本にする。 |
| flakeの因果残余 | deterministicな全走限定赤も通りうることを新Dとrunbookへ明記し、保証を盛らない。 |
| テスト実測 | read-only段では未実走。親が `tools/run_tests.py` 経由で測り、変更前の環境赤2件と区別する。 |

## 総括

- waiterは実producerの2 node形だけをexactに受理し、redとflakeを分離します。
- outer receiptはv4へ上げ、land結果と台帳まで `flake_nodeids` を失わず伝搬します。
- flake経路だけrunnerのmain/tip blob等値をGitから再計算し、receiptに自己申告fieldを増やしません。
- 実producer3分類と実consumer述語の相互pinでF366の再発を検出します。
- D371/D389は既存本文を触らず、新Dによる部分改訂として残余を明示受容します。