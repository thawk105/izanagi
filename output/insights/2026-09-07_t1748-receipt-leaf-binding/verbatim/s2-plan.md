## 素材の棚卸し

受領証本体は Git HEAD の blob と一致することまで確認されますが、受領証が参照する report / journal は `_assert_digest` による working-tree bytes の再読と SHA-256 照合であり、各参照自体の tracked 性は検査していません。

- 受領証 bytes: [s8c_acceptance_receipt.py:1940](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1748-receipt-leaf-binding/orchestrator/campaign/s8c_acceptance_receipt.py:1940) で読み、同ファイル `1947-1951` で HEAD blob と一致させる。ここに検査対象の各 leaf が入るが、再導出素材ではない。
- manifest / registry: `1953-1954` で再読するが、cross-binding leaf の preimage は決めない。
- lifecycle prefix: `1955-1962` で再読するが、leaf の preimage は決めない。
- trial report bytes: receipt の `trials[].report_path` / `report_sha256` は `924-929` で parse され、`1973-1975` で再読される。次を決める。
  - 全 mode: `trial_id`、`do_build`、`cells` 数。
  - build: `campaign_root`、cell admission、proposal path / digest、generation / harness projection。
- attempt journal bytes: `trials[].attempt_journal_path` / `attempt_journal_sha256` は `930-937` で parse され、`1976-1980` で再読される。`_journal_events` (`1346-1358`) を通じ、全 mode の `journal_role_attempt_ids`、build mode の provider / raw-response binding を決める。
- attempt-registry prefix: `1560-1581`, `2026-2027` で再読するが、leaf preimage は決めない。

3 mode の結論は次のとおりです。

| mode | report + journal だけで leaf を再計算できるか | 根拠 |
|---|---:|---|
| `no-build` | できる | `_cross_binding_no_build_receipt` (`autonomous_trial_completeness.py:4165-4189`) の preimage は固定 schema、report の `trial_id` / `cells` 数、journal の role `invocation_id`、空の `bindings`、固定 `unbound_fields` だけ。 |
| `build-failure` | できる | `_cross_binding_failure_receipt` (`4192-4214`) も同じ素材だけ。mode 判定に使う campaignless failure cell も report 内の exact shape (`336-367`, `4235-4261`) から決まる。`run_root` のディレクトリ存在は必要だが、leaf preimage の追加 bytes ではない。 |
| `build` | できない | report / journal から直接決まるのは最初の 7 field、すなわち `input_payload_sha256`, `raw_response_path`, `raw_response_sha256`, `provider_payload_sha256`, `provider_envelope_sha256` (`4279-4341`) と `proposal_path`, `proposal_sha256` (`3453-3577`, `4342-4344`) まで。残る 6 field は外部現物が必要。 |

build mode で不足する field と現物は次です。

- `build_records`: campaign WAL の実 bytes (`4417-4452`) から `4465-4478`, `4543-4546` で作る。
- `bench_records`: WAL と Layer 3 の `runs` を照合して `4508-4523`, `4547-4550` で作る。
- `artifact_refs`: `reports/layer3_report.json` と列挙された campaign artifact 全 bytes を `3339-3403`, `4383-4394`, `4551-4554` で再読して作る。
- `source_refs`: WAL、`loop_state.json.whiteboard`、Layer 3 `source_refs` を `3406-3433`, `4524-4533`, `4555-4558` で突き合わせる。
- `admission_decision`: report cell、Layer 3 report、`campaign.lock`、WAL、独立 admission verifier の結果を `4400-4446`, `4559-4564` で照合する。
- `proposal_build_source_bindings`: proposal bytes、provenance report、source-preimage artifacts、campaign lock / WAL を `3482-3574`, `3580-3636`, `3776-4162`, `4453-4464` で結合する。

さらに、build の先頭 7 field も値そのものは report / journal から得られますが、issuer と同じ保証を得るには raw response、provider payload / envelope、proposal bytes の再読が必要です (`3482-3499`, `4288-4314`)。

なお、`build-failure` leaf は helper 単体では構成できますが、現行 acceptance issuer は campaignless cell を `trial_registry.py:6152-6157` で leaf 発行前に拒否します。また standalone verifier の descriptor gate (`s8c_acceptance_receipt.py:1425-1444`) と fallback cell の exact key set (`autonomous_trial_completeness.py:342-345`) も両立しません。したがって現行 v5 issuer が実際に発行するのは `no-build` または `build` です。

## 採る案

(P1-a)〜(P1-c) ではなく、`verify_s8c_cross_binding` を standalone verifier から同じ現物に対して再実行する別案を採ります。

(P1-a) の「`run_root` / `output_root` が得られない」という前提は、現行コードでは成立しません。

- issuer の `run_root` は journal path の親です (`trial_registry.py:6081`)。
- receipt は journal path を保持し、standalone verifier はそれを repository 内の現物へ解決済みです (`s8c_acceptance_receipt.py:1976-1980`)。したがって verifier も同じ `run_root = resolved_journal_path.parent` を得られます。
- build issuer は `report_output_root = run_root.parent.parent` を計算し、campaign roots から得た root と一致させています (`trial_registry.py:6123-6138`)。
- `verify_s8c_cross_binding` 自身も campaign roots から同じ root を導出し、引数が与えられれば一致を要求します (`autonomous_trial_completeness.py:4270-4277`)。verifier は build 時に `run_root.parent.parent` を渡せます。
- no-build は root を使う前に返り (`4225-4230`)、build-failure も `output_root` の検査前に返ります (`4232-4261`)。

(P1-b) は採りません。build leaf を report / journal だけから作れる別の digest に置き換えると、現在 leaf が束縛している 6 field を耐久保証から落とします。また、report / journal 内の自己申告値だけを再ハッシュするのは D920 と同型です。

(P1-c) も採りません。issuer が projection sidecar とその digest の両方を書く設計では、sidecar の元になった campaign 現物を再検査しない限り同一走行側の値同士の照合です。さらに新しい durable path の規約と発行処理が必要になり、最小変更ではありません。

この案が恒真でない理由は、照合する二辺の由来が異なるためです。

- expected leaf は tracked receipt の bytes に入っている issuer 出力 (`trial_registry.py:6306-6308`)。
- actual leaf は receipt 内の leaf を入力にせず、現在の report / journal bytes (`s8c_acceptance_receipt.py:1973-1980`) から再び `verify_s8c_cross_binding` を実行して得る。
- build ではさらに provider artifacts、proposal、Layer 3 report、campaign lock / WAL、source preimage という別ファイルの実 bytes を再読する。
- top-level aggregate は leaf 一致を確認した後の二次検査として残す。攻撃者が forged leaf に合わせて aggregate も再計算しても、外部現物から再導出した actual leaf は変わらない。

発行側と検証側の式は次のように一致します。

```text
issuer:
  R_i = item.journal_path.resolve().parent
  O_i = None                                  if no-build
        R_i.parent.parent                     if materialized build
  P_i = verify_s8c_cross_binding(
          report=item.report,
          events=item.events,
          run_root=R_i,
          output_root=O_i)
  L_i = P_i["receipt_sha256"]                 # trial_registry.py:6168-6173, 6306-6308
  A   = cross_binding_aggregate_sha256(
          sorted({trial_id, receipt_sha256=L_i}))
                                                # trial_registry.py:6330-6340

standalone:
  report_i = decode(_assert_digest(report_path, report_sha256))
  events_i = decode(_assert_digest(journal_path, journal_sha256))
  R'_i = resolved_journal_path.parent
  O'_i = None                                  if no-build
         R'_i.parent.parent                    if build
  P'_i = verify_s8c_cross_binding(
           report=report_i,
           events=events_i,
           run_root=R'_i,
           output_root=O'_i)
  require stored L_i == P'_i["receipt_sha256"]
  require stored A == aggregate(stored L_i)
```

未変更の現物に対しては `report_i == item.report`、`events_i == item.events`、`R'_i == R_i` です。build issuer は `O_i == R_i.parent.parent` を既に要求しているため `O'_i == O_i`。同じ canonicalizer と同じ `verify_s8c_cross_binding` の mode 別式 (`4165-4214`, `4579-4588`) を使うので、正当な発行 leaf は必ず通ります。

個別 leaf の再導出は current v5 にだけ適用します。legacy v3/v4 は readable compatibility を維持し、従来の aggregate 検査だけを残します。これにより `require_current_verified_receipt` が受理し得る集合を強化しつつ、legacy receipt の既存受理集合は狭めません (`s8c_acceptance_receipt.py:2043-2055`)。

## 変更手順

1. [s8c_acceptance_receipt.py:4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1748-receipt-leaf-binding/orchestrator/campaign/s8c_acceptance_receipt.py:4)

   module docstring の「Layer 3 に依存しない」という断言を、import 時は cold のままだが current receipt の cross-binding 検査時に completeness verifier を遅延ロードする説明へ直す。top-level import は増やさない。

2. `s8c_acceptance_receipt.py:1346-1358` の `_journal_events` 直後

   private helper を追加する。

   - `report_bytes` を `_reference_object` で decode。
   - `journal_bytes` を既存 `_journal_events` で decode。
   - `_resolved_reference(root, trial.attempt_journal_path, "attempt journal").parent` から `run_root` を得る。
   - report の `do_build` が `True` なら `output_root=run_root.parent.parent`、それ以外は `None`。
   - `autonomous_trial_completeness` を関数内 import し、`verify_s8c_cross_binding` を呼ぶ。
   - `AutonomousTrialCompletenessError` は cause を保持した `AcceptanceReceiptError("[receipt-cross-binding] ...")` に変換する。
   - 戻り値の `receipt_sha256` を返す。receipt にある leaf はこの helper へ渡さない。

3. `s8c_acceptance_receipt.py:1972-1989`

   既存 trial loop で report / journal digest と arm execution の検査が終わった後、`receipt.schema_version == SCHEMA_VERSION` の場合だけ上記 helper を呼ぶ。`trial.cross_binding_receipt_sha256` と再導出 digest が異なれば、例えば

   ```text
   [receipt-cross-binding] trial leaf differs from independently rederived projection
   ```

   で拒否する。

4. `s8c_acceptance_receipt.py:2004-2025`

   現行 aggregate 検査は変更せず残す。個別 leaf の独立再導出と top-level aggregate の両方が必要であり、aggregate を再導出の代用にしない。

5. [test_s8c_acceptance_receipt_v2.py:231](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1748-receipt-leaf-binding/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:231)

   `_fixture` の report に実 mode として `"do_build": False` を入れる。必要なら run-start (`248-252`) にも同じ値を入れ、actual producer の no-build shape に合わせる。

6. `test_s8c_acceptance_receipt_v2.py:490-516`

   `_upgrade_to_current` の `sha256("cross-binding-leaf-{index}")` を削除する。各 row の既存 report / journal を読み、`autonomous_trial_completeness.verify_s8c_cross_binding` (`autonomous_trial_completeness.py:4217-4230`) を `run_root=journal_path.parent`, `output_root=None` で呼び、その `receipt_sha256` を設定する。top-level aggregate の既存計算 `508-516` はそのまま使う。

7. `test_trial_registry.py:1822-1903`

   既存 build issuer 正例の末尾で発行された receipt を既存 `_commit` (`144-150`) により track し、`s8c_acceptance_receipt.verify_acceptance_receipt` を呼ぶ。これにより materialized build の正当な issuer leaf が新検査を通ることを固定する。新しい重い fixture は作らない。

`autonomous_trial_completeness.py` と `trial_registry.py` の production 計算式には変更不要です。

## 負の対照

`test_s8c_acceptance_receipt_v2.py` に `test_v5_rejects_reaggregated_single_cross_binding_leaf_substitution` を追加します。

fixture は次の既存部品を使います。

- `_fixture` (`163-294`) で Git repo、6 report、6 journal、receipt を構成。
- 是正後の `_upgrade_to_current` (`490-524`) で actual no-build projection 由来の 6 leaf と v5 attempt binding を設定。
- `_rewrite_receipt` (`297-299`) で canonical bytes を書き、tracked HEAD にする。
- `receipt.cross_binding_aggregate_sha256` または既存 `_cross_binding_aggregate_for_schema` (`309-321`) で aggregate を再計算。

テスト手順は以下です。

1. 是正済み fixture を v5 に上げ、いったん `verify_acceptance_receipt` が成功することを確認する。
2. `value["trials"][-1]["cross_binding_receipt_sha256"]` だけを別の正規 SHA-256 値へ置換する。
3. top-level `cross_binding_receipt_sha256` も forged leaf 群から再計算する。これにより現行 aggregate-only gate は通る状態を作る。
4. report / journal bytes とその digest は変更しない。
5. receipt を再度 commit し、`verify_acceptance_receipt` が新しい trial-leaf mismatch で拒否することを確認する。

最後の row を変えることで、「先頭だけ検査する」変異も殺せます。

## 副作用

- subprocess 起動点 pin:

  `s8c_acceptance_receipt.py` の唯一の syntactic subprocess 起動点は `_git` の `subprocess.run` (`1043-1050`) です。[test_ccbench_spawn_sites.py:230](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1748-receipt-leaf-binding/orchestrator/tests/test_ccbench_spawn_sites.py:230) はこれを 1 件に pin し、`test_reviewed_process_launch_inventory_is_recursive_and_exact` (`2600-2607`) が照合します。今回追加するのは関数内 import と Python 関数呼出しだけなので、新規 process launch はなく、pin は変更不要です。

- acceptance duration ledger:

  新規 node ID の手動登録は必須ではありません。`conftest.py:1534-1554` は ledger にない node を `None` として fail-soft に扱い、ledger schema test も内部 `nodeid_count` の一致だけを検査しています (`test_update_acceptance_duration_ledger.py:306-325`)。実際、現在の ledger の `test_s8c_acceptance_receipt_v2.py` 節 (`15561-15585`) に後続の既存 v5 tests は未登録です。したがって本修正で推測時間を追加したり `nodeid_count` (`acceptance_duration_ledger.json:19525`) を手編集しません。後日、実測 JUnit から ledger 全体を更新する場合だけ新 node が取り込まれます。

- consumer:

  - `require_current_verified_receipt` は内部で `verify_acceptance_receipt` を再実行します (`s8c_acceptance_receipt.py:2039-2058`)。
  - production の直接 consumer は `layer3_report.build_accepted_report` (`layer3_report.py:904-924`)。`render_accepted` (`1035-1055`) がそこへ委譲します。
  - `trial_registry.py:6168-6377` は verifier consumer ではなく receipt producer。
  - `tools/dev_wave_land.py:934` の同名 `_verify_acceptance_receipt` は dev-wave landing receipt 用の別関数であり、この API の consumer ではありません。
  - test consumer は `test_s8c_acceptance_receipt.py:162-345`、`test_s8c_acceptance_receipt_v2.py:719-1376`、`test_trial_registry.py:1775-1779`、`test_layer3_report.py:670-672`。変更対象は current-v5 fixture と build 正例だけです。

- schema:

  v5 top-level keys は `s8c_acceptance_receipt.py:73-81`、trial keys は `96-103` で固定されています。dataclass (`200-256`)、parser (`746-1027`)、issuer の `receipt_value` (`trial_registry.py:6342-6372`) は変更しません。したがって `p3-8c-trial-acceptance-receipt/v5` の field 集合、schema version、canonical receipt bytes の定義は変わりません。

- certifying:

  `certifying=False` の構造検査 (`s8c_acceptance_receipt.py:853-861`) と issuer (`trial_registry.py:6368-6369`) は変更しません。理由コードの追加・削除もありません。

## 変異事前登録候補

1. `s8c_acceptance_receipt.py:1972-1989` の planned leaf check を削除する。

   殺す node ID: `orchestrator/tests/test_s8c_acceptance_receipt_v2.py::test_v5_rejects_reaggregated_single_cross_binding_leaf_substitution`

2. 同 planned block で rederived digest の代わりに `trial.cross_binding_receipt_sha256` 自身を expected 値に使う。

   殺す node ID: 同上。forged leaf と aggregate を自己整合させても report / journal は旧 leaf のままなので、正常実装との差が出る。

3. planned equality を `stored != rederived` から `stored == rederived` に反転する。

   殺す node ID: `orchestrator/tests/test_s8c_acceptance_receipt_v2.py::test_v5_attempt_binding_accepts_all_predeclared_observed_units`

4. planned schema guard を v5 では発火しない条件へ変える。

   例: `receipt.schema_version == SCHEMA_VERSION` を `receipt.schema_version == CROSS_BINDING_V2_SCHEMA_VERSION` にする。

   殺す node ID: 新しい leaf-substitution test。

5. `s8c_acceptance_receipt.py:1972-1989` の loop を `receipt.trials[:-1]` に変え、最後の leaf を検査しない。

   殺す node ID: 最後の row を改変する新しい leaf-substitution test。

6. `s8c_acceptance_receipt.py:1346-1358` 直後の planned helper で、decoded journal events の代わりに `events=()` を渡す。

   殺す node ID: `orchestrator/tests/test_trial_registry.py::test_p5_six_complete_terminal_reports_pass_acceptance`。同 fixture は `test_trial_registry.py:977-1054` で実 role events を持ち、issuer leaf の `journal_role_attempt_ids` は空ではない。

7. planned helper の `run_root=resolved_journal_path.parent` を `run_root=repository_root` に変える。

   殺す node ID: `orchestrator/tests/test_trial_registry.py::test_s8c_acceptance_registered_build_reports_reach_receipt_for_h1_h2_workloads`。build proposal の authority root と canonical relative path が変わり、再導出が失敗する。

8. planned helper で build report を `{**report, "do_build": False}` として渡し、常に no-build leaf を作る。

   殺す node ID: standalone 正例を追加した `orchestrator/tests/test_trial_registry.py::test_s8c_acceptance_registered_build_reports_reach_receipt_for_h1_h2_workloads`。

## 総括

- must-fix:
  - current v5 の各 leaf を、receipt 内の leaf ではなく report / journal と、build 時はそこから到達する campaign 現物から再導出する。
  - forged leaf に合わせて top-level aggregate も更新した負の対照を置く。
  - `test_s8c_acceptance_receipt_v2.py:505-507` の合成 leaf fixture を actual no-build 式へ直す。
  - actual build issuer 正例を standalone verifier まで通す。

- 変更不要:
  - `trial_registry.py` の発行式。
  - `autonomous_trial_completeness.py` の 3 mode 計算式。
  - receipt schema / canonical bytes / certifying / reason codes。
  - subprocess pin と acceptance duration ledger。

- legacy v3/v4 の readable compatibility は今回狭めない。current capability は `require_current_verified_receipt` が v5 のみを受理するため、T-1748 の downstream 耐久保証は v5 leaf の再導出で閉じる。

- ファイル変更、pytest、その他の検査は実行していません。