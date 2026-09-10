# 実装プラン

行番号は現時点の補助情報とし、関数名と定数名を主な目印にする。Web 検索、書込み、pytest 実走は行っていない。

## 1. 実装編集点

### 1.1 `_load_adjudication` の join と task 別検査

対象: `tools/codex_reasoning_ab.py:9238` の `_load_adjudication`

現在の実行順は次のとおり。

1. `revealed` と `map_rows` は `:9263`、`:9294` ですでに読み込まれる。
2. verdict 行の検査ループが `:9322-9336` で先に走り、`:9327` から `_validate_verdict_row` を呼ぶ。
3. `mapping` の辞書化はその後の `:9337-9341`。
4. `slot_by_run` はさらに後の `:9366-9370`。
5. 実際の `mapping[packet_id].run_id -> slot_by_run -> slot` join は `:9371-9425` の mapping ループ内で初めて成立する。

したがって、現在の `_validate_verdict_row` 呼出時点では、revealed mapping のファイル自体は読まれているが、packet ごとの task を得る join はまだ成立していない。ここへそのまま `benchmark_task_id` を渡すことはできない。

変更は次の順序にする。

1. `:9322-9336` の既存 `_validate_verdict_row` 呼出しは残す。これは blind verdict の manifest 全体 union 検査を維持し、manifest 全体にも存在しない ID を従来どおり拒否する。
2. `slot_by_run` 構築後、既存 `_slot_dimension_map` (`:9885-9903`) を使って slot ごとの dimensions を一度だけ作る。この helper は `_validated_slots_price_version` と `_slot_dimensions` を既に正しく接続しているため、非 null price の扱いを複製しない。
3. mapping ループの冒頭で `packet_id -> run_id -> slot -> slot_dimensions[slot_id]` を確定する。slot または dimensions が得られない場合は既存の join failure に加えて明示的な dimension join reason を残し、その packet を `joined` に入れない。
4. dimensions の `benchmark_task_id` を使い、次を取得する。

   ```python
   known_finding_ids_for_manifest(
       task_manifest,
       benchmark_task_id=dimensions["benchmark_task_id"],
   )
   ```

5. conservative intersection を作る前の各 raw reader verdict 行について、全 finding の `equivalent_to` をこの task 別集合で検査する。非 null かつ集合外なら、packet ID、task ID、finding ID を含む reason、例えば `"<packet>: finding equivalent_to is unknown for benchmark task <task>: <id>"` を追加する。
6. この検査は parent と second-reader の両方へ行う。一方の reader だけが不正 ID を出し、後段の conservative intersection から消えた場合も拒否する。
7. 同じ dimensions から得た `oracle_kind` を combined verdict に追加する。

   ```python
   verdict = {
       "oracle_kind": dimensions["oracle_kind"],
       ...
   }
   ```

8. `oracle_kind` は `row_sha = _sha256(_canonical_bytes(verdict))` (`:9440`) より前に追加する。後から追加すると `judgments[].combined_verdict_sha256` が oracle binding を覆わないため不可。

`_validate_verdict_row` (`:11480-11525`) の signature と既定の union 動作は変更しない。`append_verdicts`、`freeze_verdicts`、`reveal_mapping` は task がまだ blind な段階で使われるため、ここを task 別へ変えない。

### 1.2 `_aggregate_verified` の独立照合

対象: `tools/codex_reasoning_ab.py:10078` の `_aggregate_verified`、特に slot ループ `:10154-10184`

`verdict = verdicts.get(slot_id, {})` と、`slot_dimensions` から得た `dimensions` の直後で exact 比較を追加する。

```python
if verdict.get("oracle_kind") != dimensions["oracle_kind"]:
    reasons.append(
        f"{slot_id}: adjudication oracle_kind does not match scheduled slot"
    )
```

missing field も `None != "positive" / "negative"` として拒否する。分類や集計には引き続き manifest と schedule 由来の `dimensions["oracle_kind"]` を使い、verdict 側の値を authority にしない。

既存の task 別 equivalent 検査 `:10179-10184` は残す。これにより `_load_adjudication` と aggregate の両層が独立に fail-closed となり、reason の抑制も行わない。

### 1.3 変更しない面

- `TASK_MANIFEST` (`:265`) と `_manifest_task_entry` (`:235`) は変更しない。canonical bytes と digest は不変。
- `append_verdicts`、`freeze_verdicts`、`reveal_mapping` の blind union 検査は維持する。
- D767 の `task_acceptance_status = unbound` は変更しない。
- 独立 oracle ledger や新しい oracle hash schema は作らない。

## 2. 既存 helper の再利用判断

新しい production helper は不要。

- `known_finding_ids_for_manifest` (`:3017-3042`) は `benchmark_task_id` と `case` の選択引数をすでに持つ。task 別集合の取得にそのまま使える。
- `_slot_dimensions` (`:8998-9087`) は manifest 由来の `benchmark_task_id` と `oracle_kind` を返す。
- `_slot_dimension_map` (`:9885-9903`) は `_slot_dimensions` に price concentration を正しく渡す既存 wrapper なので、`_load_adjudication` ではこちらを再利用する。
- `_aggregate_verified` の `equivalent is not None and equivalent not in known_finding_ids` (`:10179-10184`) を同じ述語の先例とする。

受理集合は「既存 union 検査 AND 新しい task 別検査」となるため、union から task 別集合への真部分集合化だけが起きる。

## 3. テスト fixture 設計

対象: `orchestrator/tests/test_codex_reasoning_ab.py`

### 3.1 再利用できる既存部品

- `_synthetic_task_manifest` (`:6089-6107`) は、既定で `alpha-finding`、`beta-finding`、`gamma-finding` という task ごとに異なる集合と、異なる `oracle_kind` を作る。
- `_v3_slot` (`:6222-6246`) は外部 task ID を持つ v3 slot を作れる。
- `_packet_fixture` (`:12818-12853`) は外部 manifest digest を packet state へ入れられるが、1 packet のみで revealed join まで作らない。
- `test_task_manifest_digest_is_recorded_through_packet_freeze_and_reveal` (`:13042-13111`) は、`make_packets -> append_verdicts -> freeze_verdicts -> reveal_mapping` の digest 連鎖を実コードで組み立てている。ただし現状は task が `alpha` 1 件だけなので narrowing の証明には使えない。
- `_verdict_packet_swap_restore_fixture` (`:13827-13983`) は `_load_adjudication` まで通る一式を持つが、組込み manifest と POS 2 slot のため task 別集合差がない。
- `_canonical`、`_descriptor`、`_custodian_mapping_path`、`make_packets` はそのまま再利用できる。

要件をすべて同時に満たす既存 fixture はない。したがって専用 helper を追加する。

### 3.2 新しい外部 v3 adjudication fixture

`_synthetic_task_manifest` から `alpha` と `beta` の 2 task を作り、canonical JSON ファイルへ書いた後 `_load_task_manifest` で読み戻す。単なる module 内 dict ではなく、外部 v3 manifest のロード経路を通す。

fixture は次を作る。

1. `alpha-finding` のみを持つ alpha と、`beta-finding` のみを持つ beta。
2. `_v3_slot` による alpha/beta の slot と、それぞれ別 run/output を持つ `final_attempts`。
3. packet source manifest に外部 digest `d` を記録し、`make_packets(..., task_manifest=external)` を呼ぶ。
4. private mapping を fixture 内で読み、beta run に対応する blind packet ID を特定する。
5. `append_verdicts`、`freeze_verdicts`、`reveal_mapping` のすべてへ同じ external manifest を渡す。
6. material manifest 自身にも `task_manifest_sha256=d` を記録する。
7. packet state、private mapping、各 verdict 行、freeze、revealed map の `task_manifest_sha256` がすべて `d` であることを fixture または digest testで明示的に assert する。
8. freshness判定を安定させるため、既存 swap fixtureと同様に state、log、freeze、revealed の mtime を単調に設定する。
9. combined verdict の期待 digestには新しい `oracle_kind` を含める。

これにより、manifest を変えたのに一部 artifact だけ古い digestを使う経路を作らない。

## 4. 正例、負例、変異耐性

追加または更新するテストは次の3本を中核とする。

1. `test_load_adjudication_accepts_task_local_findings_and_binds_oracle_kind`
   - alpha packet は `alpha-finding`、beta packet は `beta-finding`。
   - task-specific reason がなく、joined row の `oracle_kind` がそれぞれ `positive`、`negative` であることを確認する。

2. `test_load_adjudication_rejects_cross_task_equivalent_from_manifest_union`
   - `alpha-finding` が manifest union には含まれる一方、beta の集合には含まれないことを先に assert する。
   - beta packet の parent row だけへ `alpha-finding` を入れ、second-reader は findings を空にする。
   - blind `append_verdicts` は union により通るが、post-reveal の `_load_adjudication` は task-specific reason を出すことを確認する。
   - 一方だけに入れることで、不正 finding が conservative intersection から消えても raw verdict 検査が発火することも証明する。

3. `test_aggregate_verified_rejects_adjudication_oracle_kind_mismatch`
   - matching verdict の正例を作った後、1 slot の `oracle_kind` を逆値へ変更するか削除する。
   - exact mismatch reason、`valid is False`、`experiment_complete is False` を確認する。

受理: 各 raw finding が `equivalent_to is None or equivalent_to in K(task(packet))` を満たし、combined verdict の `oracle_kind` が slot-derived value と exact 一致するとき、新しい2ゲートは reason を追加しない。  
拒否: 非 null `equivalent_to` が packet の task 集合外、または `oracle_kind` が不一致・欠落なら reason を追加し、既存の完了判定を fail-closed にする。

正例は `alpha -> alpha-finding / positive` と `beta -> beta-finding / negative` の組である。

変異確認では、task 別検査を一時的に union 取得へ戻すと負例2の期待 reason が消え、そのテストが落ちることを確認する。aggregate の exact 比較を削除した変異では負例3の mismatch reason が消え、同じくテストが落ちる。

## 5. 既存テストの追随編集

新しい `oracle_kind` が combined verdict と digest に入るため、以下を更新する。

- `_full_manifest` (`:1487`、combined dict `:1673-1685`): run/slot に対応する manifest-derived `oracle_kind` を combined hashへ含める。
- `test_bound_price_reaches_supervisor_replay_verify_and_aggregate_consumers` 内の mocked verdicts (`:9011-9017`): 各 slot の `oracle_kind` を追加する。
- `_aggregate_rows` (`:12041-12091`): POS は `positive`、NEG は `negative` を verdict に追加し、多数の既存 aggregate test を一括で追随させる。
- `test_bound_price_aggregate_rejects_attempt_price_mismatch` の手組 verdict (`:12192-12196`): slot由来値を追加する。
- `_bound_cost_aggregate` (`:14299-14335`): slot由来値を追加する。
- `_verdict_packet_swap_restore_fixture` の combined hash (`:13938-13957`): `oracle_kind` を含める。
- nonempty slots に対して `{}` verdicts を渡す cost tests (`:14799`、`:14917`、`:14949`) は、各 slot に matching `oracle_kind` を持つ最小 verdictを渡す。特に `test_f4_aggregate_uses_loaded_descriptor_state_without_manifest_reread` は現在 `valid is True` を要求するため必須。

## 6. 恒真化の危険

以下を明示的に避ける。

- 組込み `TASK_MANIFEST` は `_manifest_task_entry` (`:235-262`) が POS/NEG の両方へ同じ `sorted(_LEGACY_KNOWN_FINDINGS)` を入れるため、task 別集合と union が同一になる。
- 外部 manifest でも task が1件だけなら unionと task集合が同一になる。既存 digest-chain test の alpha 1件 fixture が該当する。
- 2 taskでも両方に同じ finding listを入れれば恒真になる。
- cross-task値が manifest union にも存在しなければ、既存 blind union検査だけで拒否され、新実装を削除してもテストが通る。
- `findings=[]` または全 finding の `equivalent_to=None` では述語が空虚に真になる。
- conservative findingsだけを検査すると、一方のreaderだけにある不正IDが消える。raw reader rowsを検査対象にする必要がある。
- oracle testで両側に同じ `oracle_kind` を入れる、または verdict 行自体を用意しないと exact binding の発火を証明できない。

## 7. `_load_adjudication` の呼び出し全数

signature は変更しない。既存の `task_manifest` 既定引数、`slots`、`final_attempts` だけで必要な join が成立するため、新しい引数は不要であり、既存呼び出しのAPI追随編集も不要。

現時点の call expression は全8箇所。

- production 1箇所: `_replay_manifest` 内 `tools/codex_reasoning_ab.py:11166`
- test adapter 1箇所: `original_load_adjudication(...)` `orchestrator/tests/test_codex_reasoning_ab.py:9150`
- `test_material_packet_source_requires_replayed_snapshot_evidence` 2箇所: `:14012`、`:14021`
- `test_m6_verdict_packet_swap_restore_digest_layers_are_redundant` 3箇所: `:14047`、`:14087`、`:14120`
- `test_reader_disagreement_is_conservative` 1箇所: `:14231`

`capture_snapshot_evidence` adapter はすでに `task_manifest` を受け渡している。`*args, **kwargs` の monkeypatch も現行 signature のまま互換である。

## 8. 到達度への所見

実装後、`_load_adjudication` は「未実装」ではなく「部分実装」が妥当。閉じるのは現行 task manifest に記録された `known_finding_ids` と `oracle_kind` の post-reveal task別束縛機構である。

閉じない面は、独立 oracle ledger、その固有 hash 契約、task 固有 acceptance の登録であり、acceptance は引き続き `unbound`。`append_verdicts` などの blind段階で unionを使うこと自体は意図した状態として記述するべきである。

静的検査のみ実施しており、pytest の緑は主張しない。

## 総括

- `_load_adjudication` の現行 verdict ループ時点では task join は未成立なので、post-join の第2検査を追加する。
- 既存 helperだけで task別 finding集合と manifest-derived `oracle_kind` を取得でき、新規 production helperは不要。
- combined verdictへ `oracle_kind` を hash前に入れ、aggregateで exact再照合する。
- 外部2-task v3 fixtureで union内かつ対象task外の findingを使い、恒真化と実装欠落を検出する。