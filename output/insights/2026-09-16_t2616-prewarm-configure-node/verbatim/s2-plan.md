## 現物で確かめた事実

**推奨は「受入全走だけ早期起動し、非受入 xdist の既存経路と nonce 伝播を残す」設計です。ただし、前試行 (b) の crash は現資料から特定できません。120 秒も適用対象と同じ条件での裏付けがありません。**

必読10ファイルはすべて読取り可能でした。ファイル変更・pytest 実行・commit はしていません。以下の行番号は現在の checkout に対するものです。

| 略称 | ファイル |
|---|---|
| C | [orchestrator/tests/conftest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2616-prewarm-configure-node/orchestrator/tests/conftest.py) |
| R | [orchestrator/tests/real_repo_receipt_memo.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2616-prewarm-configure-node/orchestrator/tests/real_repo_receipt_memo.py) |
| O | [orchestrator/tests/sort_swo_oracle_receipt_memo.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2616-prewarm-configure-node/orchestrator/tests/sort_swo_oracle_receipt_memo.py) |
| A | [tools/acceptance_shards.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2616-prewarm-configure-node/tools/acceptance_shards.py) |
| T | [orchestrator/tests/test_real_repo_serialization.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2616-prewarm-configure-node/orchestrator/tests/test_real_repo_serialization.py) |
| F | [orchestrator/tests/test_pytest_failure_digest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2616-prewarm-configure-node/orchestrator/tests/test_pytest_failure_digest.py) |
| P | [orchestrator/tests/test_run_tests_task_run.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2616-prewarm-configure-node/orchestrator/tests/test_run_tests_task_run.py) |

確認した重要点は次のとおりです。

- 現行は C:2326 の `pytest_configure_node` で nonce を伝播し、C:2359 の collection 完了通知から C:2242 の同期 barrier を呼びます。
- `_izanagi_acceptance_shard_spec` は A:797 の環境変数読取りを経て A:891 で設定されます。**属性自体は全走・consumer 存在の証明ではありません。** 担当テストは A:901–912 の collection 後に決まります。
- 正規 runner は [tools/run_tests.py:692](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2616-prewarm-configure-node/tools/run_tests.py:692) で焦点走を受入形から除外し、同:1495–1532 で全 suite と shard plugin を起動します。一方、plugin 自体には同じ選択制限がありません。
- README:51–57 は **shard-1 / shard-2 に consumer がいなかった**と記録しています。「受入なら各 shard に必ず consumer がいる」という brief の P2 は成立しません。
- **「215 対 1」は秒数ではなく比率です。** [README:62](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2616-prewarm-configure-node/output/insights/2026-09-14_acceptance-5min-floor/README.md:62) の実値は receipt **28.328 秒**、oracle **0.132 秒**、barrier **28.329 秒**です。
- この checkout の `test_memo_barrier_*` は **9関数**です。依頼の10本とは不一致です。10本目を捏造せず、下表で9本すべてと関連 cleanup test を扱います。

## (b) probe 入れ子 xdist crash の機序

**特定できません。** 指定された逐語資料と README は crash の発生を記録していますが、失敗 nodeid、worker traceback、撤去した (b) の差分を含みません。現行コードだけで過去の赤2件を特定の例外へ帰属させることはできません。

現物で特定できた入れ子 xdist の入口は以下です。これは**調査対象の名指し**であり、過去の赤2件との同定ではありません。

| 外側 test / fixture | 内側走行の行 | 内側の内容 |
|---|---|---|
| T:5041 `test_receipt_memo_real_xdist_order_has_no_worker_payer` | T:5104–5113 | `-n 1 -p orchestrator.tests.conftest -p receipt_order_plugin`。一時ファイルの consumer と同名のテストを実行 |
| F:665 `failure_digest_e2e` | F:714–732 | コピーした実 conftest を自動 discovery し、`-n 2 --dist loadgroup` で24件を意図的に失敗させる |
| F:780 `test_e2e_real_conftest_digest_has_real_failures_and_exact_account` | 上記 fixture を利用 | 同じ入れ子走行の digest を検査 |
| F:999 `test_real_dispatch_relay_preserves_complete_e2e_digest` | 上記 fixture を利用 | 同じ digest の relay を検査 |
| P:871 `test_live_xdist_controller_writes_one_sidecar_and_one_loadgroup_attestation` | P:890–899 | `-n 2 --dist loadgroup -p orchestrator.tests.conftest`、consumer でない2件を実行 |

内側での各値は次のようになります。

| 項目 | 現物から言えること |
|---|---|
| shard spec | 上記起動引数は `tools.acceptance_shards` をロードしていません。T:5093–5098、F:521–531、P:887–899 は shard 環境変数を消しませんが、**環境変数の継承だけでは Config 属性は生えません**。A:873 の plugin hook が実行されて初めて設定されます。外部 `PYTEST_PLUGINS` 等による追加ロードの有無は実行ログが必要です。 |
| controller の `workerinput` | controller Config にはありません。`pytest_configure_node` が受け取る **node の** `workerinput` と別物です。C:2328–2336。 |
| worker の `workerinput` | 内側 controller が配線した値を worker Config が読む契約です。receipt nonce の必須読取りは C:2598–2605、oracle は C:2655–2662。 |
| session nonce | 内側 controller は親環境の nonce を再利用せず、C:2607 / 2664 でそれぞれ新規生成します。親の値は復元用に保存されます。 |
| run ID | T の probe は T:5095–5098、F の probe は F:524–526 で外側 xdist 環境を除去します。C:2578–2587 は内側 controller の UID を確定します。P の probe は外側環境をそのまま継承するため、実際の worker 側 UID は観測して確認すべきです。 |
| cache path | receipt は R:131–163 の `tempdir/izanagi-t057-receipt-{sha256(uid)}-{sha256(nonce)}-{HEAD}.json`。oracle は O:128–158 の同型で prefix が `izanagi-sort-swo-oracle-`。正常な内側 nonce なら外側 cache と別 namespace です。 |
| probe が実際に cache を作るか | T:5064–5076 は receipt endpoint を `FakeMemo` に置換するため、通常は receipt cache を作りません。F/P の一時テストは consumer でなく、現行の lazy 経路では prewarm しません。 |

**静的に確定できる退行条件**はあります。

`pytest_configure_node` の冒頭に「spec がなければ return」を置くと、非受入 probe への nonce 伝播まで飛びます。その場合 worker の C:2603、または C:2660 が `UsageError` を送出します。これはコードから証明できますが、**前試行 (b) がこの変更をしていた証拠はありません**。

親で最初に確認する command は次です。既存の走行成果物だけを検索します。

```bash
rg -n --glob '*.xml' --glob '*.log' --glob '*.json' \
  'worker.*crash|controller session nonce|cache-missing|cache-path-unavailable|nested pytest timeout' \
  /work/1/SFC/tanab/.izanagi-acceptance-shards
```

旧 (b) の実装を author 側で再現した後、次を実行します。現行コードを走らせても旧 crash の再現にはなりません。

```bash
python3 tools/run_tests.py --force-dispatch -q --tb=long --showlocals \
  orchestrator/tests/test_real_repo_serialization.py::test_receipt_memo_real_xdist_order_has_no_worker_payer \
  orchestrator/tests/test_pytest_failure_digest.py::test_e2e_real_conftest_digest_has_real_failures_and_exact_account \
  orchestrator/tests/test_pytest_failure_digest.py::test_real_dispatch_relay_preserves_complete_e2e_digest \
  orchestrator/tests/test_run_tests_task_run.py::test_live_xdist_controller_writes_one_sidecar_and_one_loadgroup_attestation
```

必要な観測は、内側 controller/worker の PID、hook 名、spec の有無、`node.workerinput` / `config.workerinput`、両 nonce、UID、HEAD、計算した cache path、worker の最初の例外全文です。既存 test の失敗時出力へ追加し、**成功時 stderr の契約は変えません**。

## (a) IZANAGI_FREEZE_HOLD 漏れの経路

receipt 側から stderr までの呼出し鎖は確定できます。

1. **C:876–904** `_prewarm_receipt_memo`
   controller の背景 thread が `_real_repo_locks` 内で writer endpoint を呼ぶ。
2. **R:650–656 → R:494–579**
   `prewarm_real_repo_receipt` → `_ReceiptMemo.prewarm`。
3. **R:555–558 → R:115–117**
   `_resolve_now()` → import 時に保存した production resolver。
4. [s8b_oracle_driver.py:166](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2616-prewarm-configure-node/orchestrator/campaign/s8b_oracle_driver.py:166)
   `_resolve_t080_receipt` → `t080_freeze_migration.verify_receipt`。
5. [t080_freeze_migration.py:2284](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2616-prewarm-configure-node/orchestrator/campaign/t080_freeze_migration.py:2284)
   同:2297–2314 の `_load_artifact` → 同:1874–1877 の `held_marker`。また同:2348–2352 → 同:2409–2410 にも marker 発行経路がある。
6. [freeze_verification_hold.py:68](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2616-prewarm-configure-node/orchestrator/campaign/freeze_verification_hold.py:68)
   `held_marker` が同:86–90 で **その process の `sys.stderr` へ直接 write / flush**。同:77–91 の抑制単位は `(PID, check_id)`。

したがって出力者は、内側 pytest controller の prewarm thread が呼んだ production verifier です。外側 worker の marker が単に環境経由で運ばれるわけではありません。

空 stderr を期待する該当 test は **P:871 `test_live_xdist_controller_writes_one_sidecar_and_one_loadgroup_attestation`** です。P:897 で内側出力を捕捉し、**P:902 で `result.stderr == ""`** を要求します。consumer のないこの内側 controller で解決を始めれば、上記 marker と prewarm 診断行が混入し得ます。

failure digest については別に区別が必要です。

- F:731 の内側 timeout は15秒、F:497–517 は超過時に process group を終了します。
- digest の期待は F:743–744、利用する test は F:780 / 999。
- 現行 C:3133–3150 では memo cleanup が digest 出力より先です。

余計な prewarm による timeout、または cleanup 例外なら digest に届かない経路はあります。しかし、**前試行の digest 欠落がどちらだったかは未特定**です。「marker が digest を消した」とは結論しません。

## 発火条件の設計 (択一と推奨)

**「spec を必要条件にし、正規の全 suite 選択であることを併せる案」を推奨します。spec 単独案は採りません。**

早期起動の条件を次に限定します。

- controller Config である。
- `_izanagi_acceptance_shard_spec` が実在する。
- collect-only / setup-only 等でなく、全 suite を要求している。
- file / nodeid / `-k` / `-m` 等による焦点選択でない。

全 suite 判定は C:2016–2034 の既存述語を利用できますが、それだけでは不十分です。C:1015 の narrowing 集合は `--ignore` 等だけなので、**parsed options の `keyword` / `markexpr` 等も判定する**必要があります。これは発火対象を定める変更であり、別の受入 gate や検査系列は作りません。

| 案 | 判定 |
|---|---|
| 全 controller で早期起動 | 不採用。(a) を再発させ、D518 に反する |
| spec 属性だけで早期起動 | 不採用。plugin 自体は焦点選択を禁止していない |
| spec ＋全 suite 選択だけ早期起動 | **推奨**。consumer のない焦点走には resolver 費用を追加しない |

具体的な退行防止策は以下です。

1. **nonce 伝播を先に完了し、その後で prewarm 条件を判定する。**
2. **非受入 xdist の collection 後 prewarm を残す。** T:5041 のような consumer probe には必要です。
3. worker の待機は、当該 controller が **workerinput で明示した早期 job** にだけ適用する。継承環境や spec の有無から待機を推測しない。
4. 早期 job がある session では collection 後の二重起動・同期 join をしない。

これで nonce 欠落と fallback 消失という具体的な退行は閉じられます。**旧 (b) の crash を閉じたとの判定は、上記観測後まで保留**です。

また、全受入の shard-1/2 で余分な prewarm が発生し得ます。これは焦点走への追加費用とは異なりますが、短縮効果の実測に必ず含めます。allocator を変えたり、「consumer は shard-0」と固定したりはしません。

## 実装プラン (file:line 粒度)

| 変更位置 | 実装内容 |
|---|---|
| **C:2326–2355** `pytest_configure_node` | 現行の両 nonce・所要台帳の伝播を維持。その後に早期起動条件を判定。最初の node で Config 所有の job 状態を作り、後続 node は同じ状態を参照する |
| **C:843–873、876–986** | `started` と `prewarmed` を分離。48 worker の configure 通知で48回起動しない。早期起動用の明示引数を設け、未 collection の nodeid を捏造して consumer 判定を通さない |
| **C:879–882** | 二重 guard のコメント2行と `if hasattr(config, "workerinput"): return` を逐語維持 |
| **C:2242–2288** `_run_memo_prewarm_barrier` | 機構・二つの非 daemon thread・例外優先順位・`IZANAGI_MEMO_PREWARM_V1` を残す。早期経路では、この処理を所有する背景 job を開始し、configure hook は join しない |
| **C:2359–2430** | hold 集計と sidecar 処理は維持。早期 job がある場合だけ C:2422 の同期 barrier 呼出しを外す。非受入・焦点 xdist は既存 consumer 判定と同期経路を維持 |
| **C:2291–2322** | serial の動作と逐語 pin 対象の外側 guard を維持。早期 job の明示情報を持つ worker は、両 cache の公開完了を test body 開始前に待つ。worker は resolver を呼ばない |
| **R:131–163、O:128–158** | 既存の UID hash＋nonce hash＋HEAD による名前空間を維持。早期 job の identity/path を controller で確定して workerinput へ渡す。親環境の nonce を鍵にしない |
| **R:494–579、O:523–624** | `.pending` を背景解決開始前に公開。既存 JSON の atomic replace 成功後に ready とする。`BaseException` を含む失敗を `.failed` と job 状態へ記録し、consumer 側で再解決しない |
| **R:597–637、O:639–692** | 早期 job についてだけ bounded wait を追加。未起動・未通知の miss は現行どおり即 fail-closed。壊れた JSON は待ち直しや再解決へ逃がさない |
| **R:434–492、O:453–514** | 現行の blocking `flock` のままでは待機上限を保証できない。早期 reader は同じ deadline 内の非 blocking lock 取得にする。writer の resolver を reader が肩代わりしない |
| **C:2485、2704–2716、3121–3176** | 背景 job を session 終了までに回収し、nonce 復元より前に完了させる。背景例外を消さず、memo 回収失敗時も既存 failure digest の出力を試みる構造にする |
| **T:4415以降、F:665以降、P:871以降** | 下表の既存 test を拡張。新規 test file は作らない |

待機は **二つの memo に対して共通の一つの deadline** とします。receipt に120秒、その後 oracle に120秒という加算にはしません。

D518 の snapshot 条件を守るため、早期 session は **両 memo が公開される前に test body を開始させない**設計にします。controller の collection callback は解放しつつ、worker は必要な残余時間だけ待ちます。これを consumer getter だけの待ちにすると、先行する writer test が snapshot 確定前に動けるため、同じ保証にはなりません。

production resolver、resolution の内容、closed-schema JSON、opt-out は変更しません。

## 既存 test への影響 (1 本 1 行の表)

`memo_barrier_probe`（T:4673）は現在の serial / 非受入 xdist の2経路を残します。早期経路については `start` と `await completion` を分けて追加検査し、既存の「同期呼出しが完了を待つ」という pin を反転させません。

| 既存 test | 行 | 対応・維持する意味 |
|---|---:|---|
| `test_memo_barrier_calls_both_named_endpoints_once` | T:4712 | 維持。早期経路にも「多数 configure 通知でも各 endpoint 1回」を追加 |
| `test_memo_barrier_propagates_single_exception` | T:4724 | 維持。早期経路では回収時に同じ例外を伝播し、worker に failed を公開することを追加 |
| `test_memo_barrier_waits_for_peer_after_exception` | T:4734 | 維持。背景 job の回収でも peer を置き去りにしない |
| `test_memo_barrier_worker_runs_neither_endpoint` | T:4777 | 維持。worker の ready 待機を加えても endpoint 呼出し0回 |
| `test_memo_barrier_returns_only_after_both_complete` | T:4787 | 維持。早期 configure の復帰と、完了待機の復帰を別に検査 |
| `test_memo_barrier_prewarm_jobs_overlap` | T:4827 | 維持。背景起動後も両 job が非 daemon で重なる |
| `test_memo_barrier_both_failures_keep_receipt_primary` | T:4845 | 維持。背景回収でも receipt 主例外、oracle cause を保持 |
| `test_memo_barrier_emits_one_json_timing_line` | T:4858 | 維持。早期経路は `hook="configure_node"`、既存4キーの診断を1回だけ出す |
| `test_memo_barrier_no_consumers_emits_no_timing` | T:4877 | 維持。consumer なし焦点走では早期起動も診断も0回 |
| `test_memo_cleanup_runs_oracle_after_receipt_cleanup_error` ※barrier prefix 外 | T:4488 | 背景回収を含め、receipt cleanup 失敗で oracle cleanup を飛ばさない |
| `test_receipt_memo_configure_node_wires_nonce_and_restores_nested_env` | T:4415 | spec なしでも nonce が伝わる正例、伝播前 return の負例を追加 |
| `test_oracle_environment_memo_nonce_is_propagated_to_workers_and_restored` | T:3314 | 同じ伝播・復元の検査を oracle に追加 |
| `test_receipt_memo_prewarm_wiring_is_controller_only_and_lazy` | T:4522 | 非受入 fallback を維持し、早期対象／非対象を追加 |
| `test_oracle_environment_memo_prewarm_wiring_is_controller_only_and_lazy` | T:3221 | 同上 |
| `test_receipt_memo_optout_only_selection_does_not_prewarm` | T:4635 | 維持。spec を伴う焦点選択でも解決しない負例を追加 |
| `test_receipt_memo_both_worker_guards_are_required_as_redundant_defense` | T:4886 | 逐語 guard と外側呼出しブロックを維持し、二重除去の変異検出を残す |
| `test_receipt_memo_worker_hook_order_mechanism_rejects_both_mutants` | T:5002 | 非受入の既存順序を維持 |
| `test_receipt_memo_real_xdist_order_has_no_worker_payer` | T:5041 | spec なしの既存 probe を維持。fake を configure 前に取り付ける早期経路の別ケースを同じ file に追加 |
| `test_receipt_memo_consumers_do_not_resolve_during_collection` | T:5410 | collect-only の resolver 0回を維持 |
| `test_sort_swo_oracle_does_not_resolve_during_collection` | T:5445 | 同上 |
| `test_e2e_real_conftest_digest_has_real_failures_and_exact_account` | F:780 | 内側 consumer なし、digest 完備を維持。fixture で不要な prewarm 不発を検査 |
| `test_real_dispatch_relay_preserves_complete_e2e_digest` | F:999 | relay の完全性を維持 |
| `test_live_xdist_controller_writes_one_sidecar_and_one_loadgroup_attestation` | P:871 | **空 stderr assertion を緩めない** |

追加する待機検査は T 内に置きます。pending→ready、pending→failed、期限切れ、未起動 miss、破損 cache、別 nonce、reader resolver 0回を対象にし、時間経過は fake clock / Event で制御します。

**削除予定は0本です。「10本目の `test_memo_barrier_*`」は現物未確認です。**

## worker 側待ちの時間予算

**120 秒は未検証として扱い、確定値にしません。**

| 観測 | 母集合・条件 | 新しい待機予算への適用 |
|---|---|---|
| receipt 28.328、oracle 0.132、barrier 28.329秒 | README に掲載された診断1件。collection 後起動 | collection 前起動と条件が異なる。分布の max ではない |
| 48 worker の開始待ち28.28〜28.31秒 | 同一走行・同一 barrier の48観測 | 独立48走ではない |
| H の最遅 wall 279.8秒 | 早期起動、赤を伴う全走1件 | worker の cache 待機時間は不明 |

予算の決め方は、**同じ早期起動・canonical K=3・同じ worker 数と実行場所**で観測した待機時間 \(W\) に対して、

`B = ceil(2 × max(W)) 秒`

を提案します。係数2は設計上の余裕の提案であり、実測で正当化済みの係数ではありません。母集合の走数・worker 数・負荷条件・max を記録してから数値を確定します。timeout した観測は分布から除外せず、打切りとして扱います。

必要な時刻は、背景開始、両 cache 公開、worker 待機開始／終了です。既存診断は背景処理の所要を残し、残余待機の計測は専用成果物へ記録します。テストの空 stderr を計測の都合で壊しません。

親での canonical 実測 command は次の形です。`T2616_MEASURE_DIR` は親が用意した書込可能な repo 外成果物ディレクトリ、lease は既存共有値を用います。

```bash
python3 tools/dev_wave_wait.py acceptance \
  --wave dev-wave-t2616-prewarm-configure-node \
  --lease-dir "$IZANAGI_WAVE_LEASE_DIR" \
  --receipt-file "$T2616_MEASURE_DIR/acceptance.json" \
  --log-file "$T2616_MEASURE_DIR/acceptance.log" \
  --owned-path orchestrator/tests/conftest.py \
  --owned-path orchestrator/tests/real_repo_receipt_memo.py \
  --owned-path orchestrator/tests/sort_swo_oracle_receipt_memo.py \
  -- python3 tools/run_tests.py --force-dispatch
```

1走なら母集合は「1走」と明記します。複数走分布がないのに「分布から120秒を導いた」とは報告しません。待機予算は5分上限を緩める根拠にも使いません。

## 未実測・未確定の残り

1. **旧 (b) の失敗 nodeid・差分・worker traceback。** nonce 伝播欠落は証明可能な退行ですが、過去 crash との一致は未確認です。
2. **旧 (a) の赤4件の全件同定。** marker の出力鎖と空 stderr の期待側は特定済み。digest 欠落の直接原因は未確定です。
3. **早期起動時の待機分布。** 120秒の裏付けはありません。
4. **consumer 不在 shard での追加解決費用。** 新設条件でも全受入の一部 shard は余計に解決します。最遅 wall と各 shard wall を測って判定します。
5. **barrier test の本数差。** 現物9定義と依頼10本の差を確認する必要があります。
6. 探索した非必読パスのうち `orchestrator/tests/test_run_tests_failure_digest.py` は存在せず、実体は F でした。root の `pyproject.toml`、`setup.cfg`、`conftest.py`、`orchestrator/conftest.py` も読取り対象としては見つかりませんでした。必読ファイルの欠落ではありません。

## 総括

**移設は、nonce 伝播・非受入 fallback・worker の実解決禁止・既存 barrier 診断を残して行います。** 発火条件は spec 単独でなく、受入全走への限定を伴わせます。

ただし、**旧 crash の原因特定と同条件の待機実測が残っているため、現段階で「赤2件を閉じた」「120秒で十分」とは判定できません。** 上記はその確認手順を含む実装プランであり、実装・実走は行っていません。