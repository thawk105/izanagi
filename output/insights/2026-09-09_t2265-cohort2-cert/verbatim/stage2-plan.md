## 結論と設計境界

編集対象は親 brief 指定どおり次の 3 file に限定する。

- [t2187_adaptive_const_probe.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:110)
- [t2187_adaptive_const_probe.pbs](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:23)
- [test_t2187_adaptive_const_probe.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/orchestrator/tests/test_t2187_adaptive_const_probe.py:87)

事前登録 doc、cohort 2 解析器、insight は変更しない。実装方針は次のとおり。

- `CERT_THREADS = (24, 48)` とするが、1 request は必ず singleton thread、かつ raw 値も `"24"` または `"48"` の exact literal とする。`24,48` の同時指定は引き続き拒否する。
- probe 内に事前登録の 12 seed を明記した不変 tuple/frozenset を置き、解析器の [PREREGISTERED_SEEDS](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/orchestrator/campaign/backoff_counterfactual_cohort2_analysis.py:77) とテストで集合一致させる。
- 新規 p2 request は seed 必須、12 値だけ受理する。p1、p0、`tuned`、`cw-as-dyn` へ seed を渡す経路は閉じたままにする。
- actual `(cell, threads, compile seed)` を一つの `CertificationAxes` 相当の値として `_certification_contract` から返し、claim、genome、row、group、published receipt 検査へ同じ値を通す。
- 既発行 p2 default-seed receipt は、new-request allowlist とは分離した exact legacy compatibility branch だけで再受理する。

## 固定値参照の全数調査

実行した静的検索は次の 2 本である。

```text
rg -n -F 'CERT_THREADS[0]' probe.py test_t2187_adaptive_const_probe.py
rg -n -F 'CERT_STEP_POLICY_SEED_BY_CELL' probe.py test_t2187_adaptive_const_probe.py
```

`CERT_THREADS[0]` は production 8 箇所、test 1 箇所の計 9 箇所だった。加えて tuple 自体との比較が [probe.py:1393](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:1393) にある。

| 現行位置 | 用途 | 変更 |
| --- | --- | --- |
| [probe.py:110](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:110) | thread 閉表 | `(24, 48)` にする |
| [probe.py:1393](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:1393) | request shape | `len(threads) == 1`、raw literal exact、`threads[0] in CERT_THREADS` をすべて要求 |
| [probe.py:2228](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:2228) | row の `thread_num` | 検証済み `row_threads` の文字列と比較 |
| [probe.py:2235](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:2235) | row の `threads` | exact int かつ閉表 member を要求 |
| [probe.py:2590](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:2590) | group row thread | 24 row が同一 `group_threads` であることを要求 |
| [probe.py:2597](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:2597) | group workload flag | 各 row の `thread_num == str(group_threads)` |
| [probe.py:2648](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:2648) | receipt 出力 | 実 `group_threads` を記録 |
| [probe.py:2745](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:2745) | published receipt | receipt の実値が exact int、24/48 member であることを要求 |
| [probe.py:2803](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:2803) | published row | receipt と row の thread exact 一致 |
| [probe.py:2810](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:2810) | published row flag | `thread_num == str(receipt_threads)` |
| [test:982](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/orchestrator/tests/test_t2187_adaptive_const_probe.py:982) | synthetic fixture | `str(document["threads"])` または helper 引数へ変更 |

`CERT_STEP_POLICY_SEED_BY_CELL` は定義 1 箇所、production read 5 箇所だった。

| 現行位置 | 用途 | 変更 |
| --- | --- | --- |
| [probe.py:349](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:349) | p1/p2 固定 map | 削除。p1 fixed seed と p2 request seed を別契約にする |
| [probe.py:2029](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:2029) | performance artifact seed | performance artifact 自身の legacy default seed と、認証 request seed を分離する。後述の裁定点 |
| [probe.py:2231](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:2231) | result row seed | document から実 seed を取り、cell 別 seed 契約と exact 比較 |
| [probe.py:2585](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:2585) | group seed | 24 row の seed presence/value が一意であることを要求 |
| [probe.py:2719](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:2719) | published receipt seed | receipt の実 seed を検証。旧 p2 default@48 だけ legacy allowlist |
| [probe.py:3192](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:3192) | live request seed | `_certification_contract` が返した実 compile seed を使用 |

実 seed を genome にも通すため、直接 map を読まない [probe.py:2273](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:2273) と [probe.py:3330](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:3330) も `genome_for(cell, step_policy_seed=actual_seed)` に変える。

実装後の静的完了条件は、production の `CERT_THREADS[0]` と `CERT_STEP_POLICY_SEED_BY_CELL` がともに 0 hit になること。

## Python probe の行単位プラン

- [probe.py:110](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:110)

  `CERT_THREADS = (24, 48)` に変更し、その近傍へ事前登録どおりの 12 seed を順序付き tuple と membership 用 frozenset で追加する。値は解析器 77–92 行と十進 literal で一致させる。

- [probe.py:127](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:127)–168

  既存 4 claim 定数は legacy 48-thread claim として bytes を保持する。新たに `_certification_claim(cell, threads, seed, *, allow_legacy)` を設け、検証済み軸から新 claim を生成する。

- [probe.py:315](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:315)–352

  `CERT_CLAIMS` は既存 receipt の互換用として残す。`CERT_STEP_POLICY_SEED_BY_CELL` は削除し、次の二つを混同しない helper に置換する。

  - p1: request seed は禁止、compile seed は `STOCK_STEP_POLICY_SEED`
  - p2: request seed 必須、compile seed はその request 値
  - tuned/dynamic: seed field なし

- [probe.py:1014](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:1014)

  dynamic prefix、absolute path、24 unique path の既存検査は残す。新しい投入 recipe では group root を軸入り `attempt_id` で分ける。probe 側は混在 row を group-axis 検査で reject し、同じ path の再利用は create-only/collision として fail closed にする。

- [probe.py:1371](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:1371)

  `_certification_contract` を actual axes の唯一の生成点にする。処理順は、seed を伴う非-p2の conflict、raw cell allowlist、parsed cell equality、workload、singleton thread、extime、repetition、slot、group bindings、path set、budget の順とする。

  戻り値は loose tuple ではなく `cell/workload/threads/step_policy_seed/claim` を持つ frozen value にする。

- [probe.py:1936](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:1936)

  `expected_threads` を追加し、performance artifact 内に request と同じ thread の対象 cell row が存在することを要求する。seed については、供給済み artifact が default seed しか持たないため、artifact 自身の seed identity は従来どおり exact default とし、certification binary の実 seed とは別に扱う案を推す。

- [probe.py:2173](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:2173)

  `_validated_certification_row` は document の実 thread と実 seedを先に検証し、それから workload flags、claim、genome、source evidence をその同じ値へ束縛する。p2 の default seed は新規 row として受理しない。

- [probe.py:2452](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:2452)

  `_group_receipt_payload` は 24 row から `(cell, threads, seed)` の singleton identity を作る。異なる thread または seed が混ざれば、一般 build identity 検査より前に `group-cell-identity-mismatch`。receipt の `threads`、`step_policy_seed`、`claim` は singleton の実値を出す。

- [probe.py:2684](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:2684)

  `_validate_published_group` も receipt の実軸を起点に全 24 row と exact 比較する。legacy branch は `(p2, 48, STOCK_STEP_POLICY_SEED, old exact claim)` の組だけに閉じ、新規 request allowlistへ default seed を戻さない。

- [probe.py:3164](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:3164)

  `_certify_main` は contract が返す実軸だけを使用する。payload、workload flags、claim、seed field、`genome_for`、performance expectations、group finalization へ同じ値を渡す。

- [probe.py:3604](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:3604)

  lines 3611–3612 の無条件 conflict を削除し、cell-aware な判定を `_certification_contract` へ移す。`backoff-trace-certification-conflict` と performance mode の seed 契約は変更しない。

## Claim 文字列の設計

**案 A: literal 閉表。**

`(cell, threads, seed)` を key とする全 claim を literal で列挙する。thread 軸を全 4 cell に適用すると、新規 request identity は tuned 2、dynamic 2、p1 2、p2 24 の計 30。これに legacy p2 default@48 を別表で足す。

- 長所: 出力 bytes が目視可能で、生成ロジックの誤りがない。
- 短所: 同じ長文を約 31 本持ち、thread や seed の転記ずれが最大の危険になる。
- 検査: key 集合を期待する閉集合と equality 比較し、thread または seed を十進表記で 1 だけ変えた key が存在しないこと、claim の数字を 1 文字変えると row/group/published 検査が落ちることを確認する。

**案 B: 検証済み軸から厳密生成。推奨。**

cell 固有の固定本文と、検証後の `threads`、`seed` だけから deterministic に生成する。生成 claim は解析せず、consumer 側でも同じ関数の出力と全文 equality 比較する。

- p2: 「認証対象は threads=X、step policy seed=Y のこの実行体に限り、他の seed・thread 数・機構の各枝は認証しない」とする。
- p1: 実 thread と既定 compile seed `11400714819323198485` を書き、variable seed を認証したと読めない文言にする。
- tuned/dynamic: seed 軸が非適用であることを明確にし、48-thread identity では既存定数をそのまま返す。
- legacy p2 default@48 は `allow_legacy=True` の published receipt 検証だけが旧 literal を返す。
- 検査: `(48, seed)` から `(48, seed±1)`、`(24, seed)` から `(25, seed)` へ変えた場合に期待 claim が必ず異なり、旧 claim の流用が exact equality で拒否されることをテストする。

生成案は、受理可能性を先に閉表で確定してから文字列化するので受理面を広げない。一方、31 本の長文複製を避けられ、実軸と claim の転記ずれも起きにくい。

## Group receipt と名前空間

1 group は従来どおり 3 workload × 8 slot の exact 24 request とする。group identity は次の組である。

```text
(exact cell literal, exact threads, exact compile seed, attempt_id)
```

新規 attempt 名は `_LABEL_RE` [probe.py:213](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.py:213) に収まる ASCII のみとする。

```text
p2: c2p2-seed14481721328008317845-t48-a1
p1: c2p1-default-t24-a1
```

`_LABEL_RE = [A-Za-z0-9][A-Za-z0-9._-]*` なので、英数字と `-` の上記形式は適合し、`+`、`:`、空白は入らない。

各 group の配置を次で固定する。

```text
CERT_ROOT/<attempt_id>/group-receipt.json
CERT_ROOT/<attempt_id>/results/certify-<workload>-slot<0..7>-<attempt_id>.json
```

したがって 13 group または 25 group について、

- `attempt_id` は seed literal と thread を含むため全 group で一意
- group root と receipt path も一意
- 各 group の `--group-result-path` はその root 内の 24 本だけ
- 同じ workload/slot でも group root と末尾の attempt が異なる
- trace temporary directoryは group 固有の `out.parent` の下に作られる

となる。実装テストでは 25 group 分を組み立て、attempt、receipt、600 result path がすべて一意であることを `len(set(...))` で確認する。

## 負例と reject 理由

| 入力 | 理由コード |
| --- | --- |
| p2 + 事前登録外の 13 番目 seed | 新設 `certification-step-policy-seed-mismatch` |
| threads 23 / 25 / 47 / 49 | 既存 `certification-workload-shape-mismatch` |
| p1 + seed | 既存 `step-policy-seed-certification-conflict` |
| p0 + seed | 現行の判定順を保ち `step-policy-seed-certification-conflict` |
| tuned / cw-as-dyn + seed | 既存 `step-policy-seed-certification-conflict` |
| p2 + seed なし | 新設 `certification-step-policy-seed-missing` |
| `24,48` の複数 thread | 既存 `certification-workload-shape-mismatch` |
| p0 + seed なし | 既存 `certification-cell-mismatch` |
| seed の負数、hex、underscore、uint64 超過 | argparse の既存 `_uint64_decimal` 拒否 |

既存の cell、workload、extime、repetition、slot、binding、namespace、budget、verifier、anomaly、build identity に関する `CertificationReject` 分岐は削除しない。seed conflict は削除ではなく、非-p2に対する同じ理由コードとして cell-aware contract へ移動する。

## 既存受理形の維持

- `tuned` の 5-field cell/genome bytes は既存 [test_five_field_cells_preserve_legacy_cell_and_genome_bytes](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/orchestrator/tests/test_t2187_adaptive_const_probe.py:1352) を無変更で残す。
- `cw-as-dyn` と全 4 cell の raw/parsed exactness は [test_public_certification_accepts_each_exact_cell_and_rejects_widening](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/orchestrator/tests/test_t2187_adaptive_const_probe.py:1759) で維持する。
- performance artifact の default-seed identity は [test_cohort2_performance_binding_requires_extime_and_default_seed](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/orchestrator/tests/test_t2187_adaptive_const_probe.py:2715) の期待値を変えない。
- `CERT_CLAIMS` の既存 4 literal と schema v3 は [test_counterfactual_stack_artifacts_use_schema_v3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/orchestrator/tests/test_t2187_adaptive_const_probe.py:2164) で保持する。
- `c2-p1-a1` は `(p1,48,default seed,old claim)`、`c2-p2-a1` は legacy `(p2,48,default seed,old claim)` として `_validate_published_group` の exact compatibility test を追加する。

ただし「新規 p2 request は seed なしで拒否」と「従来の seed 省略 p2 request をそのまま受理」は同じ CLI 入力なので両立しない。推奨する境界は、new request は拒否し、既発行 receipt の再受理だけを残すことである。

## PBS driver の行単位プラン

- [PBS:23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:23)–26

  既存 4 cell literal を不変のまま保ち、p2 用 12 seed の shell `case` 閉表を追加する。

- [PBS:70](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:70)–92

  `IZANAGI_T2187_THREADS` と `IZANAGI_T2187_STEP_POLICY_SEED` の取り込みは維持する。seed を整数化せず十進文字列のまま保持する。

- [PBS:102](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:102)–141

  mode、trace、extime、list delimiter、thread syntax、rep、seed syntax の順序は維持する。lines 118–121 の無条件拒否だけを cell-aware block へ移す。

- [PBS:182](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:182)–202

  certify block 内の順序を次にする。

  1. seed があり cell が exact p2 でなければ既存 conflict
  2. cell が登録 4 literal のいずれか
  3. p2 は seed 必須
  4. p2 seed が shell の 12-value `case` member
  5. workload singleton
  6. `THREADS_RAW` が exact `"24"` または `"48"`
  7. cell-specific extime と slot
  8. group/path/identity/time-budget 検査

- [PBS:403](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:403)–417

  24 path、absolute path の既存検査を保持する。

- [PBS:426](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:426)–429

  seed argument array を performance branch の外で構築する。空なら空配列、p2 certify なら `(--step-policy-seed "$STEP_POLICY_SEED")`。

- [PBS:447](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-cert/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:447)–473

  certify exec に `"${STEP_POLICY_SEED_ARGS[@]}"` を追加する。出力名には既に attempt id が入り、thread/seed は新 attempt naming で束縛する。

## テスト計画

変更する既存 nodeid は次のとおり。

- `...::test_public_certification_exact_axes_reject_widening` — 24 rejection を削除し、23/25/47/49 と複数 thread の拒否を検査する。
- `...::test_public_certification_accepts_each_exact_cell_and_rejects_widening` — p2 case に事前登録 seed を明示し、actual axes 戻り値を検査する。
- `...::test_cohort2_certification_is_exact_and_policy2_uses_default_seed` — certification の p2 default 前提を除去して、p1 default と p2 explicit seed を分離する。汎用 `genome_for(cell)` の default 動作自体は残す。
- `...::test_pbs_certify_mode_preserves_literal_performance_exec_and_exact_axes` — PBS の thread 条件を 24/48 閉表へ更新する。
- `...::test_pbs_dynamic_output_and_plus_transport_are_fail_closed` — certify branch に seed forwarding が存在する期待へ更新する。
- `...::test_group_receipt_requires_exact_24_terminal_request_set` — fixture の `thread_num` を document の実 thread から作る。
- `...::test_cohort2_performance_binding_requires_extime_and_default_seed` —期待値を変更せず、performance reference の従来 identity を守る。

追加する nodeid と殺す欠陥は次のとおり。

- `...::test_certification_contract_accepts_exact_cohort2_seed_thread_cross_product` — 12 seed × 24/48 のいずれかを欠落させる実装を殺す。
- `...::test_certification_contract_rejects_seed_and_thread_near_misses` — 13 番目 seed、23/25/47/49、missing seed、p1/p0 seed の widening を殺す。
- `...::test_certification_claim_binds_exact_thread_and_seed` — hard-coded 48/default claim と、数字 1 文字の claim drift を殺す。
- `...::test_certification_row_rejects_seed_thread_or_genome_drift` — CLI は正しいが row/genome が別 seed/thread になる欠陥を殺す。
- `...::test_group_receipt_rejects_mixed_thread_or_seed_identity` —個別には有効な 24/48 または異なる preregistered seed の混在を殺す。
- `...::test_certify_main_builds_requested_policy2_seed_and_thread` — `_certify_main` が実 seed を `genome_for` へ渡さない、または run flag が48固定になる欠陥を殺す。
- `...::test_published_cohort2_receipts_reaccept_exact_legacy_identities` — `c2-p1-a1` と `c2-p2-a1` の旧 claim/default@48 compatibility 消失を殺す。
- `...::test_certification_group_namespaces_are_unique_for_25_groups` — attempt、dir、receipt、600 result path の衝突を殺す。
- `...::test_pbs_certification_seed_and_thread_closed_tables_are_exact` — PBS だけが 13 番目 seed、missing seed、非法 thread を通す欠陥を殺す。
- `...::test_probe_seed_table_matches_cohort2_preregistered_seeds` — probe と解析器の 12 seed 転記ずれを殺す。

既存期待値を変えざるを得ないのは、24 を拒否している line 871、seed 省略 p2 を受けている lines 1799–1809、PBS が certify seed を渡さないことを期待する lines 1327、2562、2575 である。それ以外の既存期待は維持する。

テスト実走はしていない。親は実装後にリポジトリ指定の test runner 経由で上記 nodeid と既存 file 全体を走らせる。

## 実装単位

**1 unit 直列**とする。

PBS と Python は同じ seed/thread 閉表を重複して持ち、テスト file は両方の exact equality を担保する。そのため `probe.py + test` と `pbs + test` に分けると test file の所有が重なり、素集合にならない。PBS だけを別 unit にすると閉表更新の中間状態が不整合になる。

## 投入 script の骨格

前 wave の `submit-certify.sh` の identity、performance artifact、24-path 組み立てを保持し、group 関数へ thread と seed を追加する。

```bash
#!/bin/bash
set -Eeuo pipefail
umask 077

CERT_ROOT=/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/certify
J=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2-cert
WT=$J/submit-tree
IDENTITY=$J/verifier-identity-c2-cert.json
IDENTITY_SHA='<fixed sha256>'
PERF=/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/perf/stage1-rep0-0_985871.nqsv.json
PERF_SHA=ed7fb0dce88201c87a9d04b23bc1a59d3f00a66a378b05cf756a04687af8ca45

SEEDS=(
  14481721328008317845
  7453732891837486670
  766609016836229506
  14479507243158715447
  3736279228254271919
  6574519577559702715
  15525319108568766040
  13039315294558381935
  16889140200793892447
  15536816158447092057
  13171317188614694465
  3421410286381859835
)

submit_group() {
  local policy=$1 threads=$2 seed=${3:-}
  local cell attempt group_root out_dir group_receipt paths vars p w s

  case "$policy" in
    p1)
      [[ -z "$seed" ]]
      cell='cw-as-dyn-c2-p1:1:1:1000:2560:10000:9223372036854775807:1:1:4:1:1'
      attempt="c2p1-default-t${threads}-a1"
      ;;
    p2)
      [[ -n "$seed" ]]
      cell='cw-as-dyn-c2-p2:1:1:1000:2560:10000:9223372036854775807:1:1:4:1:2'
      attempt="c2p2-seed${seed}-t${threads}-a1"
      ;;
    *) return 2 ;;
  esac

  [[ "$attempt" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]]
  group_root="$CERT_ROOT/$attempt"
  out_dir="$group_root/results"
  group_receipt="$group_root/group-receipt.json"
  mkdir -p -m 700 -- "$out_dir" "$J/pbs-out"

  paths=
  for w in write-heavy balanced read-heavy; do
    for s in 0 1 2 3 4 5 6 7; do
      p="$out_dir/certify-$w-slot$s-$attempt.json"
      paths=${paths:+"$paths+"}$p
    done
  done

  for w in write-heavy balanced read-heavy; do
    for s in 0 1 2 3 4 5 6 7; do
      p="$out_dir/certify-$w-slot$s-$attempt.json"
      [[ ! -e "$p" ]] || continue

      vars="IZANAGI_T2187_MODE=certify"
      vars="$vars,IZANAGI_T2187_CELLS=$cell"
      vars="$vars,IZANAGI_T2187_WORKLOADS=$w"
      vars="$vars,IZANAGI_T2187_THREADS=$threads"
      vars="$vars,IZANAGI_T2187_REP_INDEX=$s"
      vars="$vars,IZANAGI_T2187_STAGE=1"
      vars="$vars,IZANAGI_T2187_EXTIME=6"
      vars="$vars,IZANAGI_T2187_OUT_DIR=$out_dir"
      vars="$vars,IZANAGI_T2187_ATTEMPT_ID=$attempt"
      vars="$vars,IZANAGI_T2187_GROUP_RECEIPT_OUT=$group_receipt"
      vars="$vars,IZANAGI_T2187_GROUP_RESULT_PATHS=$paths"
      vars="$vars,IZANAGI_T2187_PERFORMANCE_ARTIFACT=$PERF"
      vars="$vars,IZANAGI_T2187_PERFORMANCE_ARTIFACT_SHA256=$PERF_SHA"
      vars="$vars,IZANAGI_T2187_EXPECTED_VERIFIER_IDENTITY=$IDENTITY"
      vars="$vars,IZANAGI_T2187_EXPECTED_VERIFIER_IDENTITY_SHA256=$IDENTITY_SHA"
      [[ "$policy" != p2 ]] ||
        vars="$vars,IZANAGI_T2187_STEP_POLICY_SEED=$seed"

      qsub -N "izc2-${policy}-t${threads}-s${s}" \
        -l elapstim_req=02:15:00 \
        -o "$J/pbs-out/$attempt-$w-slot$s.o" \
        -e "$J/pbs-out/$attempt-$w-slot$s.e" \
        -v "$vars" \
        tools/pegasus/probes/t2187_adaptive_const_probe.pbs
    done
  done
}

for seed in "${SEEDS[@]}"; do
  submit_group p2 48 "$seed"
  wait_until_own_queued_jobs_are_at_most_24
done

submit_group p1 24
wait_until_own_queued_jobs_are_at_most_24

if [[ "${RUN_OPTIONAL_24T_P2:-0}" == 1 ]]; then
  for seed in "${SEEDS[@]}"; do
    submit_group p2 24 "$seed"
    wait_until_own_queued_jobs_are_at_most_24
  done
fi
```

`wait_until_own_queued_jobs_are_at_most_24` は親の段 6 で現行 queue API に接続する placeholder である。次 group の24件を加えても、自分の滞留は最大48件になる。

## 親が段 4 で裁定すべき点

1. **推奨:** supplied performance artifact は default-seed の選定/reference identityとして保持し、certification seed は genome/source/row/group で別に exact bind する。request seed と performance row seed の equality を要求すると、12 本の新 performance artifact が必要になり scope 外となる。
2. **推奨:** p2 seed 省略は新規 request では拒否し、既発行 `c2-p2-a1` receipt の再受理だけ legacy branch で残す。同一 CLI を同時に accept/reject はできない。
3. **推奨:** `CERT_THREADS=(24,48)` は登録4 cellすべてに適用する。親の投入対象は p1/p2 だけだが、定数の意味を cell ごとに分裂させない。

## 総括

- 推す設計: 検証済み `(cell, threads, seed)` からの claim 厳密生成。長文閉表の転記ずれを避け、全文 equality は維持できる。
- 実装単位: 1 unit 直列。
- 最大の risk: supplied performance artifact の default seed と、新規 p2 request の実 seed が異なること。
- 段 4 の裁定: performance identity の分離、legacy receipt 限定互換、24/48 を全4 cellへ適用するかの3件。