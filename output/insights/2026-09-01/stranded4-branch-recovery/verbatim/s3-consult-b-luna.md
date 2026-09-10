静的検査のみを行い、pytest は実走していない。親の failed 4 は直接故障数として正しいが、外部 session root の依存閉包全体ではない。

## 所見

### `_REAL_ROLLOUT` の直接故障は 4 item だが、session root の依存閉包は 24 test 関数ある

- 判定: BLOCKER
- 根拠: `_REAL_ROLLOUT` を読むのは `test_prompt_replacement_count_zero_expected_and_excess` の 3 item と `test_real_rollout_collector_golden_is_source_bound` の 1 itemだけである。`orchestrator/tests/test_codex_reasoning_ab.py:8575-8617`。一方、`_HISTORICAL_SESSIONS` は module fixture `benchmark_snapshots` でも使われ、21 test 関数、parametrize 展開後 23 item へ伝播するほか、`test_m2_production_golden_requires_both_routes` も直接読む。`orchestrator/tests/test_codex_reasoning_ab.py:787-836,3128-3144`。したがって外部 root 依存は、直接故障 2 関数を含めて計 24 test 関数である。
- 根拠: 現在の login 側 session corpus を `_rollout_matches_session` と同じ owner 判定で静的走査したところ、POS、NEG、author、fix1、fix2 の owner rollout は全て 0 件だった。判定規則は `tools/codex_reasoning_ab.py:534-569`。これは pytest 結果ではないが、同じ corpus を使う local 実行では fixture 23 itemと `test_m2...` も成立しない可能性が高いという推測になる。
- 含意: failed 4 だけを hold しても、実行環境で session root が存在しつつ T-181 の owner rollout が失われていれば、fixture 利用 23 itemと `test_m2...` が追加で赤または error になる。逆に root 自体が無ければ fixture は明示 skip になるが、直接 4 itemと `test_m2...` は救済されない。

### POS rollout 値の閉包は manifest digest と production receipt まで広がる

- 判定: 重要
- 根拠: `ROLLOUT_SHA256` は `TASK_MANIFEST` から導出され、production の直接 consumer は `_find_rollout` と `_verify_rollout_sha` の 2 関数である。`tools/codex_reasoning_ab.py:378-389,572-650`。test 側の直接参照は 6 test 関数と `_install_rollout_pin` helperだが、POS 固有では prompt replacement 3 item、render-prompt wiring 2 item、source-bound 1 itemの計 6 itemになる。`orchestrator/tests/test_codex_reasoning_ab.py:7604-7889,8366-8490,8575-8624`。
- 根拠: 現行 production の T-181 経路は互換 alias よりも `task["provenance"]["rollout_sha256"]` を直接 `render_prompt` に渡す。`tools/codex_reasoning_ab.py:3671-3716`。さらに POS hash を変えると manifest 全体の SHA が変わり、33 production 関数の既定 manifestと、prompt、launch、collect、schedule、material、packet、verdict、aggregate の `task_manifest_sha256` が連鎖して変わる。既存 digestを持つ成果物は `_require_task_manifest_sha256` に拒否される。`tools/codex_reasoning_ab.py:2918-2948,3759-3771,8241-8243,11555-11584`。
- 含意: 案3は rollout pinだけの局所修正ではない。T-181 の manifest identity、run receipt、packet/verdict の参照集合まで別物になる。

### repo 外の生成物を読む test は Codex session 以外にも存在する

- 判定: 重要
- 根拠: repo 全体の `Path("/")`、`/home/`、`/work/`、`expanduser` を検索した結果、生成物を実際に読む test は次の通りだった。

  - T-189 jobs tree: `/work/1/SFC/tanab/dev-wave-jobs`。root 全体が無ければ明示 skipするが、一部 fileだけ消えた場合は失敗する。`orchestrator/tests/test_t189_oracle_wiring_slice.py:38,84-94`
  - T-1434 science slice: 同じ jobs root を無条件に読み、skip guardはない。reader outputなどが移動・削除されると複数 nodeが壊れる。`orchestrator/tests/test_t1434_t1222_science_slice.py:21,49-55,77-130,293-350`
  - B-10 measurement corpus: `IZANAGI_B10_MEASUREMENT_ROOT` 未指定時に `/work/1/SFC/tanab/b10-backoff-grid-runs5` を使う。plot test 1 nodeと provenance test 16 nodeが直接または `_relocated_root` 経由で読む。`orchestrator/tests/test_plot_b10_extended_backoff.py:15-18,146-163`、`orchestrator/tests/test_b10_extended_figure_provenance.py:21-24,216-225,282-315`
- 根拠: 現在は jobs rootと B-10 rootの両方が存在する。親の受入実測でも今回の赤として報告されていないため現在故障の証拠はないが、前者は job tree整理、後者は測定 corpus移動で将来壊れうる。
- 含意: 今回だけを「repo 外 pin の唯一例」と扱うと、T-1434 と B-10 の受理集合にも同じ retention/relocation riskが残る。ただし一般化 gate の追加は本 wave の scope 外である。

### production toolにも homeと固定 measurement/cache rootへの明示依存がある

- 判定: 参考
- 根拠: Codex session の既定 root は `codex_worker_launch.py`、`codex_worker_ledger.py`、`codex_reasoning_ab.py` の3箇所で `CODEX_HOME/sessions` または `~/.codex/sessions` になる。`tools/codex_worker_launch.py:4979-4985`、`tools/codex_worker_ledger.py:153-168,1105-1121`、`tools/codex_reasoning_ab.py:12091-12097,12124-12137`。Claude ledgerも `~/.claude/projects` を読み、欠落を `root_missing` として明示する。`tools/claude_session_ledger.py:35,102-103,1325-1348`
- 根拠: その他の生成物依存は、manual probe の `/work/1/SFC/tanab/izanagi-thirdparty-cache`、paper-story policy内の durable measurement base、user agent定義 `~/.claude/agents`、bench lock `~/.izanagi/bench.lock` である。`orchestrator/manual_probes/test_t2000_legacy_build_probe.py:76,1714-1741`、`orchestrator/campaign/paper_story_a1_paired.v2.json:41`、`orchestrator/campaign/paper_story_a2_certification.v2.json:8`、`hooks/guard_agent.py:46-70`、`orchestrator/campaign/lock.py:24-34`
- 根拠: `tools/codex_reasoning_ab.py:190-193` の `/home/.../dev-wave-t153e-t15423` は read pathではなく prompt内旧 rootの置換文字列である。`/proc`、`/sys`、`/run`、`/tmp`、`/scr`、`/usr/bin`、`/etc` の残りの絶対 pathは OS interface、scratch、実行 binaryであり、過去生成物 pinとは別分類だった。
- 含意: 動的 ledgerは欠落を明示的な error/issueにできるが、固定 T-181 testのような path literalは retentionで突然 acceptance を止める。manual probeや測定 campaignは各専用 corpus/cacheが消えた時点で実行不能になる。

### 案1にそのまま使える既存の環境依存 hold は存在しない

- 判定: BLOCKER
- 根拠: `growth_test_holds.py` の契約は `hold_axis`、`ruling`、`reason`、`correctness_gate`、`release_condition`、`measured_seconds`、任意の `collateral_note` で、axisは repo growthの5種に限定される。`orchestrator/tests/growth_test_holds.py:19-40,619-665`。`barrier_nodes` は `reason` 内の advisory JSONであり、独立 fieldでも自動 evaluatorでもない。`orchestrator/tests/growth_test_holds.py:172-185`
- 根拠: `flaky_test_holds.py` は exact node IDごとに same-treeの green/red観測、failure signature、cause、既存 `F`、reintroduction taskを必須とし、既定 acceptanceでは無条件 skipする。`orchestrator/tests/flaky_test_holds.py:26-40,84-167,200-238`、`orchestrator/tests/conftest.py:2001-2018`。今回に対応する F が無いという親の調査結果から、現契約では登録不能である。
- 根拠: `freeze_verification_hold.py` は、ユーザー裁定、exact check ID台帳、`status="held"`、解除条件、stderr marker、成果物への `held_checks` 搬送を持つ先例である。`orchestrator/campaign/freeze_verification_hold.py:14-62,68-110`。ただし T-181 testを登録できる汎用機構ではない。
- 含意: 案1を実装するには、ユーザー裁定の下で T-181 source verification専用の明示的 `held/unavailable` 状態を追加する必要がある。単なる `pytest.skip` は案4であり、既存 freeze holdの名前だけを流用すると裁定範囲を越える。

### 現存 rollout は16行目の token slice形を満たしうるが、張り替えは新測定に相当する

- 判定: BLOCKER
- 根拠: 現存 7169 rolloutを静的走査し、16行以上ある7129件中3088件で、16行目が `event_msg`、`token_count`、`total_token_usage` を持つことを確認した。例えば `/home/SFC/tanab/.codex/sessions/2026/08/15/rollout-2026-08-15T08-25-02-01a00297-dc9a-7af0-bfe8-37eed0879f09.jsonl:16` が要求形を満たす。これは corpus構造の確認であり、test合格の確認ではない。
- 根拠: 張り替え時に最低限変わるのは POSの session ID、rollout SHA、`prompt_source` の SHA/chars/bytes/replacements、`_REAL_ROLLOUT`、`_REAL_TOKEN_SLICE`、slice SHA、`input_tokens == 17295` の literal、および manifest literal testである。`tools/codex_reasoning_ab.py:196-223`、`orchestrator/tests/test_codex_reasoning_ab.py:145-166,1765-1786,8611-8624`
- 根拠: `snapshot.numstat` は rolloutから自動導出されず、別の frozen literalとして manifestへ入る。`tools/codex_reasoning_ab.py:283-337,990-1004`。新 rolloutの promptが同じ artifact path集合を要求しない場合は `render_prompt` が拒否するため、artifact names、snapshot hashes、numstatも新しい taskとして取り直す必要がある。`tools/codex_reasoning_ab.py:3720-3757`
- 含意: 同じ prompt bytesと同じ snapshot意味論を持つ厳密な再収録 sessionなら snapshot値を維持できる余地はあるが、任意の現存 rolloutへの張り替えは T-181 provenanceの修復ではない。新 task ID、manifest、事前登録、測定成果物を持つ別測定として扱う必要がある。

### 原本が無い環境では全受入 waveを止めるという主張は、現在の受入形について正しい

- 判定: BLOCKER
- 根拠: 受入の既定 targetは `orchestrator/tests` 全体で、恒久 exclusionは現在空である。`tools/run_tests.py:55-56`、`orchestrator/test_selection_contract.py:61`。shard実行も全 suiteをcollectした後でのみ担当外をdeselectする。`tools/run_tests.py:1460-1508`、`tools/acceptance_shards.py:825-852`
- 根拠: shard allocatorは fileを同一連結成分にするため、`test_codex_reasoning_ab.py` の関連 nodeは全て同じ1 shardへ入る。`tools/acceptance_shards.py:321-357,377-442`。したがって別 shardに隠れた直接 consumerはなく、割当てが将来変わっても、いずれか1 shardが必ず4 itemを実行する。
- 根拠: 直接2関数には file不在を条件にした skipがない。root全体が無くても `_REAL_ROLLOUT.read_bytes/read_text` は失敗する。`orchestrator/tests/test_codex_reasoning_ab.py:8575-8617`
- 含意: 現行の full acceptanceでは、原本 pathが無い限り K=1、2、3のいずれでも `child-green` にならず、waveは止まる。訂正点は「全環境で永久に」ではなく、「この絶対 pathに原本が無い環境で行う全受入 wave」であり、原本が残る別環境ならこの4 itemは成立しうる。

## 各案の評価

### 案1: 条件付きで可能

凍結 provenanceを維持し、source verificationだけを明示的な `held/unavailable` 状態にする方向は実装可能である。ただし既存 registryに適合する登録先はなく、ユーザー裁定、exact check ID、機械可読 status、解除条件、default acceptanceで失われる検査と barrier nodeの記録を新たに定義する必要がある。現行 `flaky_test_holds.py` へ入れるには既存 F が必要なうえ無条件 skipになるため、案1の「原本がある環境では実行する」とは一致しない。

### 案2: 条件付きで可能

SHA-256 が `9b90d510...` と一致する原本 bytesをバックアップなどから回収できれば、repo内へ固定し、pathだけをrepo相対へ変える実装は可能である。その場合は T-181 literalを変えずに source-bound検査を復旧できるが、現時点で原本が0件なので単独では実装不能である。

### 案3: 条件付きで可能

現存 rolloutには要求される16行目構造が多数あり、コード上の張り替え自体は可能である。しかし T-181 の POS rowを上書きする形は凍結済み測定を別 sessionへ改変するため、受理可能な実装ではない。新 task ID、新 manifest、新 snapshot/測定成果物として開始する場合に限り可能であり、それは過去の赤の修復ではなく新測定になる。

### 案4: 実装可能

`Path.is_file()`、`pytest.skip`、`skipif` のいずれでも少量の変更で実装できる。ただし source-bound検査を file不在環境で恒真化し、held理由、解除条件、失われた保証を成果物へ残さないため、正しさゲートとしては採用できない。

## 総括

推奨は案1で、T-181 の literalは不変のまま、source verificationをユーザー裁定付きの明示的 `held/unavailable` 状態として設計する。これは「再現不能」と「過去の測定事実」を分離し、案4の黙示的弱体化も避けられる。原本の厳密な preimageが回収できた時点では案2へ移行する。

この推奨が誤りだとすれば、freeze hold型の `held` 状態を acceptanceが非成功として正しく搬送できず、実質的に案4と同じ恒真ゲートになることが原因である。