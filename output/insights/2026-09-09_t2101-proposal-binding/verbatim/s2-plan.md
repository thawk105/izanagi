## 前提の確認

- 指定された 8 ファイルを全文確認し、関連する canonical JSON 実装、campaign lock、WAL、build、既存テストを静的に追跡した。
- D1343 に従い、変更対象は `--b4-reflux-ablation` を持つ formal B-4 の 3 driver に限定する。通常の非 B-4 経路は変えない。
- read-only のため、編集、commit、pytest 実走は行っていない。以下の行番号は現行 worktree 基準。
- 「campaign lock」には二つあるため区別する。

  - identity file `campaign.lock` の原子的作成: `orchestrator/campaign/ident.py:538-615`、実書込みは `orchestrator/campaign/wal.py:2897-2921`
  - 実行中の advisory lock: `orchestrator/campaign/loop.py:414-419` → `orchestrator/campaign/lock.py:72-84`

## canonical hash の定義

対象は proposal JSON を parse して得た top-level document の浅い copy から、top-level の `b4_closed_critic_receipt_sha256` だけを除いた値とする。入れ子に同名 key があっても除かない。

```python
canonical_document = dict(document)
canonical_document.pop(B4_PROPOSAL_RECEIPT_SHA256_KEY, None)
canonical_bytes = attempt_registry_core.canonical_json_bytes(
    canonical_document
)
digest = hashlib.sha256(canonical_bytes).hexdigest()
```

`canonical_json_bytes` は `orchestrator/campaign/attempt_registry_core.py:197-206` の公開実装を使う。理由は以下。

- `p3_b4_analysis_ledgers.py:26` と `p3_b4_prerun_issuer.py:35` が既にこの実装を B-4 registry/publication の正準化に使っている。
- `p3_b4_launcher.py:67-74` や `s8b_prediction_runner.py:195-202` に同型の private 実装があるが、launcher の private 関数を loop から参照すると層が逆転し、既存の loop と launcher の相互参照も悪化する。
- B-4 の登録値と実行側を同じ公開 serializer に揃えられる。

正確な wire 規則は次のとおり。

- object key は Python `str` 順、すなわち Unicode code point 順に昇順。
- object/array の区切りは `,`、key/value は `:`。空白と末尾 LF は付けない。
- `ensure_ascii=False`。非 ASCII は文字として出力し、全体を UTF-8 bytes 化する。
- JSON 文字列内の制御文字、quote、backslash は `json.dumps` の規則で escape する。
- `allow_nan=False`。`NaN`、`Infinity`、`-Infinity`、overflow して非有限 float になる数は hash を持たず、B-4 proposal として拒否する。
- int と float は区別される。`1` は bytes 上も `1`、`1.0` は `1.0` なので別 hash。
- `1e0`、`1E+00`、`1.00` はすべて Python float `1.0` になり同じ hash。整数 token `1` とは異なる。
- 指数表記は parse 後の Python float を `json.dumps` が出す最短 round-trip 表現へ正規化する。異なる十進 token が同じ binary float へ丸められた場合も同じ hash になる。
- Unicode normalization はしない。見た目が同じでも code point 列が異なれば別 hash。
- whitespace、object key 順、非 ASCII の literal/escape、`\/` と `/` など、同じ Python JSON value に parse される表記差は同じ hash。
- duplicate key に新しい規則は足さない。現行 loader の parse 規則を維持し、通常経路は最後の key、K2 経路は既存の duplicate-key 拒否を使う。hash は実際に実行へ渡る parse 結果から作る。

P1-3 に同意する。receipt hash は continuation 中に `p3_b4_launcher.py:582-606` で得た terminal receipt に合わせて proposal へ追加され、registry 封印時の preimage にできない。これを含めると bootstrap と continuation で同じ事前提案を束縛できない。

なお、optional な justification、uncertainty、confidence、auditor 内容も proposal document の一部なので hash に含める。除外は receipt key 一つだけである。

## 登録値への到達経路

P1-1 の明示 argv 方式に同意する。attempt identity は `attempt_id` を使う。

1. `p3_b4_launcher.main` の `orchestrator/campaign/p3_b4_launcher.py:632-658` に次を必須引数として追加する。

   - `--b4-prerun-publication <absolute-root>`
   - `--b4-attempt-id <attempt-id>`

2. `launch_bootstrap_impl` の `p3_b4_launcher.py:532-556` と `launch_continuation_impl` の `:558-609` に両値を渡す。
3. `_driver_argv` の `p3_b4_launcher.py:177-193` が、既存の `--run-iteration` とともに両 flag を必ず argv に入れる。
4. `DRIVER_REGISTRY` の `p3_b4_launcher.py:140-144` を通じて base/sort/trigger の実 `main` が受け取る。
5. 各 driver の `load_proposal_file` へ publication root と attempt id を渡す。
6. 共通 helper が `p3_b4_prerun_issuer.load_b4_prerun_publication` を呼ぶ。同 loader は:

   - root と 3 artifact を `p3_b4_prerun_issuer.py:1009-1046` で同一 directory FD から読む。
   - registry を `:1048-1056` で `load_scheduled_attempt_registry` に通す。
   - receipt、registry、manifest、commitment、completeness を再検証し、`:1162-1177` で `B4PrerunPublication.registry` を返す。

7. `publication.registry.scheduled_attempts` から `attempt.attempt_id == supplied_attempt_id` の行を exact に 1 件選び、`attempt.initial_proposal_sha256` を期待値にする。

`attempt_id` を選ぶ理由は以下。

- `initial_proposal_sha256` と同じ `B4ScheduledAttemptInput` に属する: `p3_b4_analysis_ledgers.py:124-143`
- 全 attempt で必須かつ非空: `:305-312`
- registry 内一意性が強制される: `:469-472`
- `block_id` は optional であり、非 eligible 行では存在しない場合がある。
- ordinal は並び順であって外部 identity ではない。
- manifest membership は要求しない。registry に存在するが manifest の 201 行に未選択の attempt を拒否する追加 gate は本題外。

publication 不正、attempt id 不正、不在、複数一致、登録 hash 不正のいずれも `B4ProtocolError` として fail-closed にする。期待 hash を launcher の別引数として渡す案は採らない。

## 拒否の発火位置

比較は各 `load_proposal_file` の「同一 buffer の parse、既存 receipt/schema 検査」の直後、dataclass 化して `drive_iteration` へ渡す前に置く。

| driver | 比較の呼出し位置 | 比較後に初めて到達する実行境界 |
|---|---|---|
| base | `p3_s4_loop.py:2473-2481` が呼ぶ `load_proposal_file` `:2007-2103` 内 | worktree enter `:2485`、`drive_iteration` `:2486` |
| sort | `p3_s4_loop_sort.py:738-742` が呼ぶ loader `:439-500` 内 | worktree enter `:746`、`drive_iteration` `:747` |
| trigger | `p3_s4_loop_trigger_gating.py:1289-1293` が呼ぶ loader `:919-981` 内 | worktree enter `:1297`、`drive_iteration` `:1298` |

その後の境界はすべて比較より後になる。

- identity `campaign.lock`:

  - base: `p3_s4_loop.py:2209-2212`、さらに resolved 実行内 `:1630-1634`
  - sort: `p3_s4_loop_sort.py:573-576`、さらに `:399-403`
  - trigger: `p3_s4_loop_trigger_gating.py:1092-1095`、さらに `:776-779`
  - 共通の原子的作成は `ident.py:518-522` → `:538-602` → `wal.py:2897-2921`

- WAL 書込み:

  - interrupted attempt recovery は `ident.py:523-535`
  - diff reject の最初の明示 WAL は `p3_s4_loop.py:703-739`
  - campaign 評価の `BUILD_START` は `pipeline.py:1838-1849`
  - trigger binding WAL は `wal.py:1595-1611`

- campaign 実行開始:

  - base `p3_s4_loop.py:1699-1708`
  - sort `p3_s4_loop_sort.py:413-418`
  - trigger `p3_s4_loop_trigger_gating.py:811-820`

- advisory campaign lock は共通の `loop.py:414-419` → `lock.py:72-80`
- actual trace/perf build は `pipeline.py:1919-1950`
- 各 driver の condition gate や sort oracle も proposal load 後なので、hash 不一致時には到達しない。

launcher の sidecar は現状 `p3_b4_launcher.py:547` / `:600` で driver 呼出し前に書かれる。これは campaign build、identity lock、WAL、campaign 実行ではない。本変更を loop-sideかつ単一読取りに保つ限り、proposal mismatch より前の sidecar 作成は残るため、「一切の artifact mutation 前」とは主張しない。

## 恒真化しないための設計

**(a) 登録値を proposal から導かない**

- helper の入力に expected hash を置かない。
- expected は必ず `load_b4_prerun_publication(...).registry.scheduled_attempts` の対象行から取る。
- proposal 内の `initial_proposal_sha256`、`proposal_sha256` などは登録値として読まない。現行 closed schema `projection_guard.py:306-350` では未知 key として拒否される。
- observed だけを proposal document から導き、expected と observed の出所を分離する。

**(b) 束縛不在を許さない**

- formal launcher の両 CLI 引数を `required=True` にする。
- 3 driver では B-4 mode のとき publication root と attempt id の両方を必須化する。
- 片方のみ、両方なし、空 attempt id、publication load 失敗はすべて拒否する。
- 非 B-4 mode に両引数を与えた場合も拒否し、通常走行へ値が紛れ込まないようにする。
- missing binding を `None` として比較を省略する分岐は作らない。

**(c) 候補集合に含意されないこと**

現行コードには、registry 行と実 proposal 内容を一致させる前提がない。

- issuer は caller supplied の `scheduled_inputs` をそのまま受け取る: `p3_b4_prerun_issuer.py:709-727`
- ledger が `initial_proposal_sha256` に確認するのは lowercase 64 hex だけ: `p3_b4_analysis_ledgers.py:339-340`
- registry seal はその値を payload に転記する: `:370-392`、`:670-683`
- launcher の proposal は独立した任意 path: `p3_b4_launcher.py:638`、`:648`、`:657`
- 現在の 3 loader は receipt key と schema は見るが registry を一切見ない: base `p3_s4_loop.py:2025-2103`、sort `p3_s4_loop_sort.py:457-500`、trigger `p3_s4_loop_trigger_gating.py:936-981`

したがって実際に新しく拒否される入力が存在する。具体例は次のとおり。

1. schema-valid な proposal A、例えば base の value と implementation がともに 20 の document を作る。
2. attempt `t` の registry 行に `H(A)` を入れて publication を封印する。
3. 同じ attempt id `t` を指定したまま、proposal path の内容を schema-valid な Bへ変更する。例えば value と implementation をともに 21 にする。
4. B は registry membership、proposal schema、value/literal attribution をすべて満たすため、現行コードでは campaign へ進む。
5. 新検査は registry 行を同じ `t` で引いたまま `H(B) != H(A)` を検出して拒否する。

つまり「registry に attempt があること」と「その attempt に登録された proposal hash と一致すること」は別述語であり、後者は前者に含意されない。正例 A と変異 B を同じ publication/attempt id で走らせるテストを positive control にする。

## 単一読取り

3 loader の現行 `open(...); json.load(f)` を次の形へ変える。

```python
with open(path, "rb") as stream:
    proposal_bytes = stream.read()

text = proposal_bytes.decode("utf-8")
document = json.loads(text, ...)
```

- proposal path を開くのはこの一度だけ。
- parse、receipt key 除去、schema 検査、canonical hash、Planner/Coder/Auditor 構築はすべてこの `proposal_bytes` 由来の同じ `document` を使う。
- base K2 の `object_pairs_hook=knowledge_manifest._reject_duplicate_keys` は `json.loads` 側へそのまま移す。
- 共通 binding helper は path を受け取らず、既に parse 済みの document を受け取る。これにより helper が proposal file を再度開けない構造にする。
- parent brief の「proposal bytes を取る public helper」は、再 parse の余地を残すため、`require_b4_proposal_registry_binding(publication_root, attempt_id, document)` へ少し狭める。bytes の所有者は loader 一箇所だけにする。

二度開く実装への攻撃列は以下。

1. path P は proposal A を指す。
2. hash 用の一回目の open が A を読み、registry の `H(A)` と一致する。
3. close 後、攻撃者が `os.replace` で P を schema-valid な Bへ差し替える。
4. parse 用の二回目の open が B を読む。
5. gate は Aを承認したのに、campaign は Bから作った Planner/Coder/Auditor を実行する。

parse と hash の順を逆にしても、B→A の差し替えで同じ問題になる。単一 buffer なら path が読取り後に差し替えられても、承認値と実行値は同じ in-memory document のままである。

trigger の `_write_source_preimage_artifact` は `p3_s4_loop_trigger_gating.py:348-385` で proposal path を再読するが、formal launcher は `_require_source_preimage_artifact=False` のままなので B-4 実行では発火しない。この別用途の一般化まで変更しない。

## 既存テストへの波及

以下は B-4 loader または launcher の新しい必須引数で赤になる。すべて registry binding fixture を与えて既存の検査目的を維持する。期待値の緩和、反転、skip は不要。

- `orchestrator/tests/test_p3_s4_loop.py`

  - `:4601 test_b4_driver_rejects_bootstrap_claim_over_nonempty_admitted_history`
  - `:4611 test_b4_true_bootstrap_reaches_synthesis_for_all_drivers`
  - `:4913 test_b4_proposal_accepts_exact_terminal_receipt_hash`
  - `:4927 test_b4_proposal_rejects_terminal_receipt_hash_mismatch_m9`
  - `:4941 test_b4_proposal_rejects_self_reported_prior_reverse_m10`
  - `:4955 test_b4_bound_decision_reaches_synthesis_and_writes_exact_consumption`

  `_exercise_b4_history_driver` の base/sort/trigger 各 loader 呼出し `:4412-4514` に同じ正当な publication root/attempt id を渡す。

- `orchestrator/tests/test_p3_s4_loop_sort.py`

  - `:1086 test_b4_sort_certified_receipt_advances_through_shared_gate`
  - `:1146 test_b4_sort_proposal_rejects_unbound_hash_and_self_reported_reverse`

- `orchestrator/tests/test_p3_s4_loop_trigger_gating.py`

  - `:2994 test_b4_trigger_certified_receipt_advances_through_shared_gate`
  - `:3073 test_b4_trigger_proposal_rejects_unbound_hash_and_self_reported_reverse`

- `orchestrator/tests/test_p3_b4_closed_critic.py`

  - `_production_launch_context` `:109-160` は実 launcher signature の変更で全利用者へ波及するため、driver stub 用でも明示 publication root/attempt id を渡す。
  - `:2662 test_launcher_positive_uses_real_factory_and_real_base_main_for_commit` は実 publication を発行し、receipt key を除いた proposal core の hash を登録して real main に渡す。
  - `:2868 test_public_b4_receipt_gate_accepts_live_certified_bound_receipt` も direct loader に正当な binding を渡す。

- `orchestrator/tests/test_p3_b4_launcher.py`

  - `:331 test_g9_bootstrap_uses_real_verifier_before_driver`
  - `:347 test_bootstrap_matching_record_checks_all_projections_then_launches`
  - `:376 test_bootstrap_rejects_stale_or_driver_mismatched_projection_before_sidecar`

  invalid admission/projection のテストでは dummy ではあるが型の正しい明示 binding 引数を加え、従来どおり admission が先に拒否することを維持する。matching case では driver argv に両 flag が exact に 1 回あることも確認する。

新規 `orchestrator/tests/test_p3_b4_proposal_binding.py` には以下を置く。

- key 順、空白、非 ASCII escape が同一 hashになる正例
- int/float、`1`/`1.0`、指数表記の固定例
- NaN/Infinity 拒否
- receipt key だけが preimage から外れる確認
- missing root、missing attempt id、unknown attempt id、壊れた publication の拒否
- matching hash の正例
- registry に存在する同じ attempt の schema-valid proposal mutation が拒否される非恒真性
- base/sort/trigger の mismatch が `drive_iteration`、campaign lock、WAL、`run_campaign`、build の spy を一つも呼ばないこと
- proposal path の open 回数が各 loader で 1 回であること

201 行 publication を作る共通 test fixture は `orchestrator/tests/p3_b4_proposal_binding_support.py` に限定して置く。独立した自走 harness は不要で、通常の pytest collection と `tools/run_tests.py` で十分。

静的調査上、上記 runtime テストの中に期待値を反転しなければ成立しないものはない。

一方、`test_p3_b4_prerun_issuer.py:248-264` が固定する `formal_launcher_not_wired_to_require_this_receipt` は本変更後に意味上古くなる。ただしこれは今回の runtime 差分だけでは赤にならない。後述のとおり、厳密 receipt schema の変更を伴うため、この wave で黙って期待値を書き換える案にはしない。

## 編集面の一覧

- `orchestrator/campaign/p3_s4_loop.py`

  - `:63-100`: `attempt_registry_core.canonical_json_bytes` の import
  - `:169` または `B4ProtocolError` 周辺 `:360`: canonical hash、binding 引数整合、publication/attempt lookup、compare の共通関数
  - `:2007-2103`: binary 単一読取り、binding 引数追加、同一 document からの hash/parse
  - `:2290-2296`: 2 CLI option 追加
  - `:2352-2370`: B-4 必須、非 B-4 混入拒否
  - `:2473-2481`: publication root/attempt id を loader へ渡す

- `orchestrator/campaign/p3_s4_loop_sort.py`

  - `:439-500`: binary 単一読取りと `L` の共通 binding helper 呼出し
  - `:658-664`、`:673-686`: CLI option と mode 整合
  - `:738-742`: loader へ両値を渡す

- `orchestrator/campaign/p3_s4_loop_trigger_gating.py`

  - `:919-981`: binary 単一読取りと共通 binding helper
  - `:1204-1210`、`:1223-1236`: CLI option と mode 整合
  - `:1289-1293`: loader へ両値を渡す

- `orchestrator/campaign/p3_b4_launcher.py`

  - `:177-193`: `_driver_argv` の必須 publication root/attempt id
  - `:532-556`: bootstrap signature と forwarding
  - `:558-609`: continuation signature と forwarding
  - `:632-658`: launcher CLI の required option と両 launch 関数への受渡し

- test 更新:

  - `orchestrator/tests/test_p3_s4_loop.py:4383-4619,4913-5005`
  - `orchestrator/tests/test_p3_s4_loop_sort.py:1086-1169`
  - `orchestrator/tests/test_p3_s4_loop_trigger_gating.py:2994-3089`
  - `orchestrator/tests/test_p3_b4_launcher.py:331-425`
  - `orchestrator/tests/test_p3_b4_closed_critic.py:109-160,2662-2809,2868-2937`
  - 新規 `orchestrator/tests/test_p3_b4_proposal_binding.py`
  - 新規 test helper `orchestrator/tests/p3_b4_proposal_binding_support.py`

`p3_b4_prerun_issuer.py` と `p3_b4_analysis_ledgers.py` は loader/型の既存 API を消費するだけなので、runtime 実装変更は不要。

## やらないこと

- `initial_proposal_sha256` を issuer が計算・記録する producer の実装
- proposal と critic decision の因果的束縛
- 新しい台帳、receipt、署名、capability、one-shot state machine
- registry attempt の manifest membership、driver、workload、arm、planned result path の追加照合
- publication の別 root 再発行や coordinated rewrite の防止
- 非 B-4 proposal への hash binding
- `run_one_iteration` 一般 API の proposal 再構築や汎用 binding framework 化
- trigger の非 B-4 source-preimage artifact 読取り経路の一般改修
- `p3_b4_analysis_contract.py`、`p3_b4_analysis_adapter.py`、`p3_b4_analysis_ledgers.py`、`p3_b4_analysis_path.py`、`p3_b4_analysis_prereg_consumer.py` と `_SOURCE_CLOSURE_PATHS`
- raw/material report の schema や既存 binding 表示の更新
- launcher sidecar、admission record、closed critic receipt の再設計
- 凍結成果物や既存 campaign identity の変更

## 親 brief への異議

P1-1、P1-2、P1-3、P1-4 にはすべて同意する。

実装形について一点だけ狭めたい。親 brief の公開 helper `(publication root, attempt id, proposal bytes)` は、helper 内で JSON を再 parse する実装を誘発しうる。公開面は次の二つにするのが安全である。

- `canonical_b4_proposal_sha256(document)`
- `require_b4_proposal_registry_binding(publication_root, attempt_id, document)`

proposal bytes の open と parse は各 loader の一箇所だけが所有する。

また、既存文言には scope 上の未解決がある。

- `p3_b4_prerun_issuer.py:56-69` の `formal_launcher_not_wired_to_require_this_receipt`
- `p3_b4_raw_record_producer.py:62-64` の「precursor と実 campaign の束縛は転記に留まる」
- それを表示する `p3_b4_material_report.py:82,395-411`

runtime gate 完成後、これらは少なくとも一部が古くなる。ただし `B4_PRERUN_NON_GUARANTEES` は strict receipt bytes の一部で、変更すると `test_p3_b4_prerun_issuer.py:248-264` の exact expectation と publication schema を変える。今回の「本題だけ」「期待値を反転しない」に従い、実装面へ混ぜず、別の明示 scope で整理すべきである。production publication 発行前にはこの文言差を解消する必要がある。

## 総括

実装の核は、formal launcher が publication root と attempt id を 3 driver へ明示的に渡し、各 proposal loader が一度だけ読んだ buffer を parseし、その document から receipt key を除いた canonical JSON SHA-256 を作り、厳密に再検証した registry 行の `initial_proposal_sha256` と比較することである。

registry membership を保ったまま proposal を schema-valid に変える入力が現行コードで受理されるため、この検査は恒真ではない。比較は 3 driver とも `drive_iteration` より前に完了し、identity/advisory campaign lock、WAL、condition build、`run_campaign`、actual build のすべてに先行する。