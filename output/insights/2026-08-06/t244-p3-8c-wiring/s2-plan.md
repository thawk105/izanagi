# 実装プラン（静的読解・条件付き）

指定された全ファイルを読めた。以下の行番号は現行 HEAD 基準である。ファイル変更および pytest 実走は行っておらず、すべて未実走である。

先に結論を示すと、brief のままの全面実装は不可である。理由は次の2点。

- 現在の `drive()` 戻り値から、ledger の `accepted/rejected` に必要な正式な `evidence_digest` と `constraint_sha256` を一般には導出できない。
- `BatchCommitted` 後は `BatchReservationAbandoned` を受理できないため、P5 の「例外なら放棄」は ledger FSM と両立しない。

本 wave で安全に実装できるのは、`do_build=False` に限定し、workload 未実行を `tombstoned / None / None` として sealed にする配線パイロットである。ビルドありの origin binding は、正式な結果証拠契約が追加されるまで fail-closed にする。

## 1. 編集面と値型

編集対象は次の2ファイルに限定する。

- `orchestrator/campaign/p3_autonomous_workload_trial.py`
- `orchestrator/tests/test_p3_autonomous_workload_trial.py`

`reflux_origin_ledger.py`、authority JSON、report schema、preregistration contract は変更しない。

### driver の型追加

`orchestrator/campaign/p3_autonomous_workload_trial.py:282-303`、既存の `PreparedCampaignIdentity` / `_RunScopeBinding` の直後に追加する。

```python
@dataclasses.dataclass(frozen=True, slots=True)
class OriginLedgerClient:
    read_origin: Callable[[str], reflux_origin_ledger.OriginSnapshot]
    commit_event: Callable[..., reflux_origin_ledger.EventReceipt]


@dataclasses.dataclass(frozen=True, slots=True)
class OriginBinding:
    origin_id: str
    replicate_count: Literal[1]  # 呼出側が明示。runtime でも exactly 1 を検証。


@dataclasses.dataclass(slots=True)
class _OriginBatchState:
    batch_id: str
    query_ordinal: int
    replicate_ordinal: int
    candidate_salt: str | None
    result_evidence_salt: str | None
    constraint_salt: str | None
    candidate_commitment: str | None
    state_commitment: str
    phase: Literal["reserved", "committed", "prepared", "sealed", "abandoned"]
```

追加 import は `base64`、`secrets`、`Literal` と ledger module。candidate/result/constraint commitment は ledger と同一の domain separator と canonical JSON を使うが、ledger 側は変更しない。

`orchestrator/campaign/p3_autonomous_workload_trial.py:149-150` の既存 sentinel の隣に `_ORIGIN_LEDGER_NOT_PROVIDED` を置く。

### batch identity

- `origin_id`: `OriginBinding.origin_id`
- `R`: `OriginBinding.replicate_count`。本 wave は runtime でも `== 1` を要求する。
- `batch_id`: `f"{trial_id}:{workload}:g{generation}"`。同一試行の再送で安定し、token 長制約内に収まることを事前検証する。
- `iteration_index`: reserve 直前の `OriginSnapshot.iterations_used`
- `query_ordinal_start`: 同 snapshot の `queries_used`
- member の `query_ordinal`: `query_ordinal_start`
- `replicate_ordinal`: `0`。ただし public snapshot では既出 candidate の replicate 数を取得できないため、`batch_count == 0` かつ `origin_distinct_candidate_count == 0` を activation 条件にする。既に sealed batch がある origin は reserve 前に拒否する。
- salt: 各 member につき `secrets.token_hex(16)` を3回。32文字 lowercase hex、ゼロ値でないこと、3値が相異なることを driver でも検証する。

operation ID は `batch_id` に `:reserve`、`:commit`、`:prepare`、`:seal`、`:abandon` を付ける。

## 2. ledger field 対応表

### `CommittedBatchMember`

| field | driver の実在値 |
|---|---|
| `query_ordinal` | reserve 前 snapshot の `queries_used` |
| `candidate_commitment` | `sha256(bytes.fromhex(candidate_salt) + b"izanagi-reflux-origin-batch-member/v1\0" + canonical_json({"candidate_wire_b64": base64.b64encode(coder.wire.encode("ascii")), "query_ordinal": q, "replicate_ordinal": 0}))` |

### `PreparedBatchMember`

| field | driver の実在値 |
|---|---|
| `query_ordinal` | 上記と同じ `q` |
| `candidate_commitment` | commit 時と同じ値 |
| `result_evidence_commitment` | `do_build=False` 限定案では、`outcome="tombstoned"`、`evidence_digest=None` の ledger 規定 preimage に result salt を付けた SHA-256 |
| `constraint_commitment` | tombstoned のため constraint preimage は `b""`。constraint salt を付けた SHA-256 |

### `OpenedBatchMember`

| field | driver の実在値 |
|---|---|
| `query_ordinal` | snapshot の `queries_used` |
| `replicate_ordinal` | fresh-origin 制約下で `0` |
| `candidate_salt` | `secrets.token_hex(16)` |
| `candidate_bytes` | `coder.wire.encode("ascii")` |
| `result_evidence_salt` | candidate salt と異なる `secrets.token_hex(16)` |
| `outcome` | `do_build=False` 限定案では `"tombstoned"` |
| `evidence_digest` | `None` |
| `constraint_salt` | 他の2 salt と異なる `secrets.token_hex(16)` |
| `constraint_sha256` | `None` |

ビルドありの場合は以下が埋められない。

| drive 結果 | 埋められない field | 理由 |
|---|---|---|
| `certified` | 正式な `evidence_digest` | WAL、report、preview diff のどれを result evidence の正本とするか未裁定 |
| `rejected` | `evidence_digest`、`constraint_sha256` | 全 reject が exact-mask verifier anomaly ではなく、current return に constraint class SHA がない |
| `aborted` / custom failure | `outcome`、`evidence_digest`、`constraint_sha256` | ledger の3 outcome へ意味を損なわず写像できない |
| drive 例外 | result 一式 | 実行開始済みか否かを戻り値なしで確定できない |

`auditor.diff_digest` や `outcome["digest"]` を代用品として埋める案は採らない。それらが result evidence / exact constraint の正本であるという契約がないためである。

## 3. event 呼出しの挿入位置

### `BatchReserved`

`p3_autonomous_workload_trial.py:1571` の planner 呼出し直前。現行の前後3行は次のとおり。

```text
1568             "leading_indicators": dict(leading_payload),
1569             "whiteboard": whiteboard,
1570         }
     [BatchReserved をここに挿入]
1571         planner, event = _invoke(
1572             role="planner",
1573             provider=providers["planner"],
```

ここで snapshot を読み、IDLE、非 terminal、fresh-origin、R=1、`do_build=False` を検証して reserve する。wall-budget 判定は既に終わっているため、wall-budget break では reservation を作らない。

### `BatchCommitted`

proposal bytes の書込み成功後、drive kwargs 作成前。現行アンカーは次のとおり。

```text
1688             "descriptor_sha256": hashlib.sha256(descriptor_path.read_bytes()).hexdigest(),
1689         }
1690         _write_bytes_bound(proposal_path, _canonical_json_bytes(proposal_value))
     [BatchCommitted をここに挿入]
1691         drive_kwargs = {
1692             "layout": layout,
1693             "cache_root": cache_root,
```

candidate bytes は `coder.wire.encode("ascii")`。proposal JSON や descriptor bytes は candidate bytes にしない。

### `BatchResultsPrepared` → `BatchSealed`

drive 戻り値の required fields と binding commitment を検証した後、generation record や critic へ進む前に連続して置く。

```text
1736                    for character in binding_commitment)
1737         ):
1738             raise AutonomousTrialError("harness binding commitment が不正")
     [BatchResultsPrepared をここに挿入]
     [BatchSealed を直後に挿入]
1739         generation_record["harness"] = outcome
1740         generation_record["outcome"] = outcome["outcome"]
1741         current_metrics = _metric_projection(outcome)
```

「drive の直後」ではなく最低限の戻り値検証後にする。未検証の戻り値で origin を seal すると、driver 自身が後で不正と判断する結果を不可逆に記録するためである。

各 receipt の `current_state_commitment` を次 event の `expected_state_commitment` に渡す。

### `BatchReservationAbandoned`

`p3_autonomous_workload_trial.py:1571-1802` の一世代分を `try/finally` で囲み、`finally` で phase が `reserved` の場合だけ abandon する。閉じ位置は現行の return 直前。

```text
1799             prior_reverse = _reverse_decision_by(critic, planner, current_metrics)
1800         if outcome.get("stop_reason") != "continue":
1801             result["stop_reason"] = str(outcome["stop_reason"])
1802             break
     [finally: phase == "reserved" なら BatchReservationAbandoned]
1803     return result
1804
1805
```

phase が `committed` の場合、abandon は ledger に拒否される。限定案では `do_build=False` を根拠に tombstoned の prepare/seal を試みる。seal 自体が失敗した場合は例外を隠さず伝播し、abandon に偽装しない。

## 4. 注入 seam

### `_run_workload`

`p3_autonomous_workload_trial.py:1446-1456` の末尾へ explicit keyword を追加する。

```python
origin_binding: OriginBinding | None = None,
origin_ledger: OriginLedgerClient = _PRODUCTION_ORIGIN_LEDGER,
```

既存の直接呼出しは変更不要。`origin_binding is None` のときは `origin_ledger` のメソッドを一切評価しない。

### `_finish_trial`

`p3_autonomous_workload_trial.py:1228-1255` に以下を追加し、`1297-1315` の `_run_workload` 呼出しへ workload 単位で転送する。

```python
origin_bindings: Mapping[str, OriginBinding] | None,
origin_ledger: OriginLedgerClient,
```

### `run_trial`

`p3_autonomous_workload_trial.py:1831-1854` に次の explicit keyword を追加する。

```python
origin_bindings: Mapping[str, OriginBinding] | None = None,
origin_ledger: OriginLedgerClient | Any = _ORIGIN_LEDGER_NOT_PROVIDED,
```

claude-headless 拒否は、既存の `providers` 拒否と `drive/preview` 拒否の間、`p3_autonomous_workload_trial.py:1863-1867` に置く。artifact 作成開始の `:1957` より前である。

拒否条件は、claude-headless で次のいずれかが真の場合。

- `origin_bindings is not None`
- `origin_ledger is not _ORIGIN_LEDGER_NOT_PROVIDED`

sentinel の場合だけ production の `read_origin` / `commit_event` を持つ client に解決する。CLI 引数は新設しないので、通常 CLI から origin binding は発火しない。

## 5. break と例外の扱い

採用するのは per-generation の `try/finally` である。

| 経路 | reservation 状態 | 処理 |
|---|---|---|
| wall-budget break `:1550` | 未作成 | ledger call なし |
| planner invalid `:1589` | reserved | finally で abandon |
| coder invalid `:1627` | reserved | finally で abandon |
| auditor invalid `:1680` | reserved | finally で abandon |
| harness stop `:1802` | sealed | abandon なし |
| critic invalid `:1798` | sealed | abandon なし |
| planner～proposal write の例外 | reserved | finally で abandon |
| commit 後、no-build drive/検証の例外 | committed | tombstoned prepare/seal。元例外は再送出 |
| ledger event 自体の例外 | 状態依存 | swallow せず伝播。成功を推測しない |

親の N4 が数える5 break とは別に、現行コードには critic-invalid break もある。ただし critic は seal 後なので放棄対象ではない。

明示的な各 break への abandon 挿入は採らない。3 role-invalid 分の重複、例外の取りこぼし、将来の return/break 追加時の漏れ、二重 abandon の危険があるためである。

## 6. origin なしの bytes 不変

次をコード上の禁止事項にする。

- `origin_binding is None` では snapshot、salt生成、時刻取得、ledger call をしない。
- report、journal、proposal、raw response、namespace に origin field を追加しない。
- schema version を変更しない。
- 既存 `drive` / `preview` の引数、順序、戻り値を書き換えない。

新規テストでは、変更前 HEAD で決定的 fixture run を計算ノード上で生成し、全 artifact の相対パス→SHA-256 map を literal golden として固定する。`monkeypatch.chdir(tmp_path)`、相対 `run_root=Path("run")`、固定 `_now_iso` により絶対 tmp path と時刻を排除する。実装後の origin なし run をその map と byte-for-byte 比較する。

monkeypatch は時刻固定だけに使い、ledger 注入には使わない。

## 7. 新設・改修テスト

すべて `orchestrator/tests/test_p3_autonomous_workload_trial.py`。現時点では未実走。

| nodeid 案 | 検出内容／負の control |
|---|---|
| `::test_originless_path_preserves_pre_wiring_artifact_bytes` | 全 artifact の変更前 SHA map と一致。originless 分岐で field を1個追加すれば落ちる。 |
| `::test_originless_path_never_touches_injected_ledger_client` | 例外を投げる client を渡しても binding なしなら完走。guard を常時真にすれば落ちる。 |
| `::test_fixture_origin_binding_real_ledger_seals_one_tombstoned_member` | `_fixture_store_for_test` と real reducer で reserve→commit→prepare→seal、R=1、query/iteration消費、tombstone=1を確認。event を1つ削除・交換すれば落ちる。 |
| `::test_origin_events_surround_planner_drive_and_critic_in_order` | 記録 provider/client で `reserve < planner < commit < drive < prepare < seal < critic`。event を境界外へ移せば落ちる。 |
| `::test_reserved_batch_is_abandoned_on_invalid_role[planner]` | planner invalid で phase IDLE、forfeited query=1。finally を外せば落ちる。 |
| `::test_reserved_batch_is_abandoned_on_invalid_role[coder]` | coder invalid の放棄。coder break だけ先行 return に変えれば落ちる。 |
| `::test_reserved_batch_is_abandoned_on_invalid_role[auditor]` | auditor invalid の放棄。auditor break 前に誤 commit すれば落ちる。 |
| `::test_wall_budget_break_does_not_reserve_origin_batch` | wall-budget 即時終了で client call 0。reserve を wall check 前へ動かせば落ちる。 |
| `::test_precommit_exception_abandons_and_propagates_original_error` | preview/proposal 前例外で放棄し、元例外も保持。例外 swallow または abandon 欠落で落ちる。 |
| `::test_postcommit_no_build_exception_seals_tombstone_not_abandon` | commit 後例外を tombstone seal し、abandon へ偽装しない。P5 の文字どおり abandon にすれば落ちる。 |
| `::test_harness_stop_is_sealed_before_generation_break` | stop_reason 発火時にも batch が sealed。seal を break 後へ動かせば落ちる。 |
| `::test_origin_binding_rejects_build_enabled_before_reservation` | `do_build=True` の binding を ledger call 前に拒否。誤った accepted/rejected 合成を許せば落ちる。 |
| `::test_origin_binding_rejects_origin_with_prior_sealed_batch` | replicate ordinal を観測できない origin を reserve 前に拒否。`replicate_ordinal=0` の固定再利用を許せば落ちる。 |
| `::test_claude_headless_origin_injection_is_rejected_before_artifacts` | claude-headless への binding/client 注入が `run_root` 作成前に失敗。拒否を後置・削除すれば落ちる。 |
| `::test_origin_ledger_failure_is_not_swallowed` | CAS/event error を呼出側へ伝播。catch-and-continue で落ちる。 |

real ledger 正例は、`test_reflux_origin_ledger.py:408-451` の先例どおり、fixture store の `_locked`、`_read_origin_locked`、`_commit_locked` を closure にした `OriginLedgerClient` を使う。production API の monkeypatch は行わない。

既存の次のテスト群は期待値を変更せず、そのまま回帰検査に残す。

- `orchestrator/tests/test_p3_autonomous_workload_trial.py` 全体
- `orchestrator/tests/test_s8c_preregistration_predicates.py` 全体
- `orchestrator/tests/test_reflux_origin_ledger.py` 全体

## 8. 変異事前登録候補

行番号は現行アンカー。新設行は挿入先を併記する。

| path:line | 変異 | 落ちる nodeid |
|---|---|---|
| `p3_autonomous_workload_trial.py:1571` | reserve を planner 後へ移動 | `::test_origin_events_surround_planner_drive_and_critic_in_order` |
| `:1571` 新設 reserve | `member_row_count=1` を `2` に変更 | `::test_fixture_origin_binding_real_ledger_seals_one_tombstoned_member` |
| `:1571` 新設 reserve | `iteration_index=snapshot.iterations_used` を `generation` に変更 | 同上 |
| `:1571` 新設 reserve | `query_ordinal_start=snapshot.queries_used` を `0` に固定 | 同上 |
| `:1571` 新設 guard | `origin_binding is not None` を常時真にする | `::test_originless_path_never_touches_injected_ledger_client` |
| `:1571` 新設 guard | fresh-origin 検査を削除し replicate を常に0にする | `::test_origin_binding_rejects_origin_with_prior_sealed_batch` |
| `:1690` | commit を drive 後へ移動 | `::test_origin_events_surround_planner_drive_and_critic_in_order` |
| `:1690` 新設 helper | candidate bytes を `coder.wire` から proposal JSON bytes に変更 | real-ledger 正例 |
| `:1690` 新設 helper | candidate preimage から `replicate_ordinal` を削除 | real-ledger 正例 |
| `:1690` 新設 salt | 3 salt を同じ定数にする | real-ledger 正例 |
| `:1738` | prepare と seal の順序を交換 | real-ledger 正例 |
| `:1738` 新設 result mapping | tombstoned を accepted、digest を auditor diff に変更 | `::test_postcommit_no_build_exception_seals_tombstone_not_abandon` |
| `:1802-1803` 新設 finally | reserved abandon を削除 | invalid-role 3ケース |
| `:1802-1803` 新設 finally | committed 状態にも `BatchReservationAbandoned` を送る | `::test_postcommit_no_build_exception_seals_tombstone_not_abandon` |
| `:1863-1877` | claude-headless の origin injection 拒否を削除 | `::test_claude_headless_origin_injection_is_rejected_before_artifacts` |
| ledger 呼出し helper 新設箇所 `:305` 前後 | `except Exception: pass` を追加 | `::test_origin_ledger_failure_is_not_swallowed` |

## 9. P1〜P7 の実装可能性評価

| 裁定 | 評価 |
|---|---|
| P1 | 成立。ledger と authority を変更せず caller wiring を追加できる。 |
| P2 | 一部成立。explicit client seam と claude-headless 拒否、fixture-store 実 ledger テストは可能。 |
| P3 | R=1、fresh origin に限定すれば成立。既存 candidate の replicate ordinal は public snapshot から得られない。 |
| P4 | event の位置は実装可能。ただし一般の build outcome は result fields が埋まらず、no-build tombstone 限定でのみ成立。 |
| P5 | 文字どおりには不成立。放棄できるのは `BATCH_RESERVED` のみ。commit 後は prepare/seal か、未確定状態を露出して失敗するしかない。 |
| P6 | 不成立。`--provider fixture --no-build` だけでは origin binding も fixture ledger store も供給されず、CLI 経路は発火しない。直接 `_run_workload` を呼ぶ programmatic fixture test は live だが、production path や通常 CLI path の発火証拠ではない。 |
| P7 | 作業手順として実施可能。コード上の裁定ではない。 |

P6については、production で origin 不在のまま一度も発火しない機能を「配線パイロット」として実装すること自体は可能である。ただし、それを production caller integration や strong DW-G04 evidence と呼ぶのは不適切である。本番 provisioning は scope 外なので、今 wave では「fixture store 上で ledger FSM を通る programmatic liveness」に名乗りを限定すべきである。

## 総括

一文要約: origin binding を explicit keyword seam として追加し、origin なしの bytes を完全維持しつつ、fresh origin・R=1・no-build tombstone に限って real ledger の reserve→commit→prepare→seal／precommit abandon を配線する条件付きプランである。

最も割れうる設計択一は次の3件。

1. no-build 結果を `tombstoned` とするか、現在存在しない正式な result-evidence 契約を先に作るか。
2. public snapshot で replicate ordinal を復元できないため fresh origin に限定するか、ledger API 拡張を別 wave に送るか。
3. commit 後例外を tombstone seal するか、結果不明として open batch と例外を露出するか。

親 brief への不同意は、P5 の「例外なら放棄」は ledger FSM 上不可能であり、P6 の CLI live-path 主張も現行 seam では成立しない点である。また P4 の build outcome 対応は evidence/constraint の正本が未定義なので、捏造なしには実装できない。全テストおよび動作確認は未実走であり、実測は親が計算ノードで行う必要がある。