## 総括

- 変更は 2 files・9 hunks 想定（driver 7、test 2）。
- 新規 test は 10 関数。変異候補は 9 件＋等価対照 1 件。
- P1〜P4 と不変条件を採用し、比較述語・成功 payload・`run_series`・`verify()` は維持する。
- 親 brief への留保は 1 点：指定の `create_json` は fsync を伴い、D474 の非 fsync 方針とは一致しない。
- 本計画は指定された `create_json` を使う。非 fsync 化や artifacts API の変更は追加しない。
- 必読資料を静的確認済み。書込み・pytest 実走は行っていない。
- 以下の行番号は現在の checkout 基準。test fixture の実位置は L261。

## 1. 変更一覧（file:line）

以下、`driver` は `orchestrator/qualification/t126_driver.py`、`tests` は `orchestrator/tests/test_t126_qualification_driver.py`。

| Hunk | 位置 | 現行 → 変更後 |
|---|---|---|
| D1 | `driver:41` | artifacts import に `QualificationWriteCapability` を追加し、新 helper の型注釈に使う。 |
| D2 | `driver:99` 付近 | `QualificationDriverError` の直接 subclass `AttestationMismatchError` を追加。詳細は §3。 |
| D3 | `driver:465` | 不一致・空比較時の汎用例外 → 比較行と hash 等を渡した `AttestationMismatchError`。条件式は変更しない。 |
| D4 | `driver:475` 後 | module-level `_run_attestation_child(...) -> int` を追加。成功 JSON と不一致 sidecar の書込みを担当。 |
| D5 | `driver:475` 後 | module-level `_attestation_rejection_message(...) -> str` を追加。sidecar の存在・読取り結果から診断文を作る。 |
| D6 | `driver:1204` | closure の子側処理を D4 呼出しへ置換。`os._exit` は closure に残す。 |
| D7 | `driver:1242` | 固定文言の `AttestationError` → D5 の返した message を持つ同じ例外。 |
| T1 | `tests:367` 後 | sidecar・成功 bytes・障害系・message の新規 9 tests。既存 `_attest_fixture` を再利用。 |
| T2 | `tests:675` 後 | 診断 message を `run_series` に通し、reject evidence の exact keys を確認する 1 test。 |

accepted path は現行どおり：

```text
{prefix}/attestation/{stage}-{n}.json
```

sidecar path は：

```text
{prefix}/attestation/{stage}-{n}.mismatch.json
```

ここで `prefix = attempts/{attempt_id}`、`n = round_index`、`None` の場合は `final`。helper は既存 accepted relative path に `Path(relative).with_suffix(".mismatch.json").as_posix()` を適用し、命名の重複を避ける。

sidecar の exact top-level keys は次の 9 個：

```text
schema_version
status
stage
round_index
expected_profile_sha256
observed_profile_sha256
observed_profile_projection_schema
comparisons
failed_fields
```

値の仕様：

```python
{
    "schema_version": "t126-qualification-attestation-mismatch/v1",
    "status": "rejected",
    "stage": stage,
    "round_index": round_index,
    "expected_profile_sha256": exc.expected_profile_sha256,
    "observed_profile_sha256": exc.observed_profile_sha256,
    "observed_profile_projection_schema":
        exc.observed_profile_projection_schema,
    "comparisons": exc.comparisons,
    "failed_fields": [
        row["field"] for row in exc.comparisons
        if row.get("verdict") != "pass"
    ],
}
```

`comparisons` は pass 行を含む全行を元の順序で保存する。比較行の `field / expected / observed / verdict` を加工しない。schema 名は診断文書の識別子にとどめ、schema file・validator 登録・新しい gate は作らない。

`execution_guard.py` は変更しない。

## 2. 子側処理の抽出

追加する signature：

```python
def _run_attestation_child(
    *,
    repo_root: Path,
    contract,
    capability: QualificationWriteCapability,
    relative: str,
    stage: str,
    round_index: Optional[int],
) -> int:
    ...
```

`relative` は現行 closure が生成する accepted JSON の capability-root 相対 path。処理骨格：

```python
try:
    try:
        payload = _attest(repo_root, contract)
    except AttestationMismatchError as exc:
        diagnostic = {...}  # §1 の exact keys
        create_json(
            capability,
            Path(relative).with_suffix(".mismatch.json").as_posix(),
            diagnostic,
        )
        return RC_ATTESTATION

    payload.update({"stage": stage, "round_index": round_index})
    create_json(capability, relative, payload)
    return RC_SUCCESS
except BaseException:
    return RC_ATTESTATION
```

この配置で、不一致 sidecar の構築・書込み失敗も既存と同じ rc=31 に畳む。probe/parser/hash 計算等の例外は typed mismatch ではないため、sidecar を書かない。accepted JSON 書込み失敗も従来どおり rc=31。

closure の子分岐は次の形にする：

```python
if is_child:
    os._exit(_run_attestation_child(
        repo_root=source_root,
        contract=contract,
        capability=capability,
        relative=relative,
        stage=stage,
        round_index=round_index,
    ))
```

**`os._exit` は closure 側に残す。** helper は通常の Python 関数として rc を返すため、test から fork なしで実物の `_attest`・JSON 書込みを通せる。fork/process-group の所有・終了処理は既存 closure に維持する。

## 3. typed 例外

```python
class AttestationMismatchError(QualificationDriverError):
    def __init__(
        self,
        *,
        comparisons: list[dict[str, Any]],
        expected_profile_sha256: str,
        observed_profile_sha256: str,
        observed_profile_projection_schema: str,
    ) -> None:
        super().__init__("attestation comparison contains a mismatch")
        self.comparisons = comparisons
        self.expected_profile_sha256 = expected_profile_sha256
        self.observed_profile_sha256 = observed_profile_sha256
        self.observed_profile_projection_schema = (
            observed_profile_projection_schema
        )
```

`_attest` の L465 の条件はそのまま残し、L466 の raise のみ置換する：

```python
raise AttestationMismatchError(
    comparisons=comparisons,
    expected_profile_sha256=verified.attestation_profile_sha256,
    observed_profile_sha256=observed_sha256,
    observed_profile_projection_schema=parsed.schema_version,
)
```

互換条件：

- `QualificationDriverError` の subclass とする。
- message は現行の全文を維持する。
- typed raise は現行どおり L450–464 の `try/except` の外に置く。汎用例外に再包装しない。
- `rc` は直接 subclass として現行の基底値を継承する。production 子の終了 rc は helper が 31 に変換し、親は従来どおり `AttestationError(rc=31)` を上げる。
- 空 comparisons でも同じ型を上げ、属性は `comparisons=[]` とする。
- 成功 return dict（L467–474）は変更しない。

これにより既存の `pytest.raises(QualificationDriverError, match="comparison contains a mismatch")` は維持される。

## 4. 親側 message

追加する signature：

```python
def _attestation_rejection_message(
    *,
    capability: QualificationWriteCapability,
    relative: str,
    attempt_dir: Path,
) -> str:
    ...
```

helper は accepted `relative` から sidecar path を導出する。表示用 path は attempt-dir 相対とし、正常な sidecar がある場合：

```text
attestation child rejected; diagnostic=attestation/pre-round-1.mismatch.json; failed_fields=["effective_clock.governor"]
```

空比較の場合：

```text
attestation child rejected; diagnostic=attestation/post-series-final.mismatch.json; failed_fields=[]
```

具体的な読取り方針：

1. 基本文言を `attestation child rejected` とする。
2. sidecar の実在を確認。無ければ基本文言を返す。
3. `load_json_strict` で読み、`failed_fields` が文字列の list なら `json.dumps(..., ensure_ascii=True)` で表示する。
4. 存在を確認できたが、読取り・JSON・表示用値の形が壊れている場合：

```text
attestation child rejected; diagnostic=attestation/pre-round-1.mismatch.json; failed_fields=unavailable
```

存在確認自体が失敗した場合も例外を外へ出さず、基本文言へ戻す。これは表示のための防御であり、受理判定の validator にはしない。

親の置換は非ゼロ終了分岐だけ：

```python
raise AttestationError(_attestation_rejection_message(
    capability=capability,
    relative=relative,
    attempt_dir=layout.attempt_dir,
))
```

`run_series` は無変更。正確には、L766/L819 の **evidence** keys が `stage/type/message`、`SeriesFSM.reject`（`series.py:366`）の外側 payload keys が `reason/evidence_canonical_json/evidence_sha256`。両方を維持する。

message の拡充に伴い evidence の bytes/hash は変わる。壊れた sidecar を理由とする新しい reject reason・例外型・rc は導入しない。timeout 分岐の message も変更しない。

## 5. test 一覧

新規 tests は次の 10 関数。共通して既存 `_fsm(tmp_path)` 由来の capability/layout を使い、fork せず helper を呼ぶ。通常は `_attest_fixture` の calibration loader と probe だけを stub とし、parser・比較・hash・`create_json`・strict loader は実物を通す。

| Test 名 | 配置・検査内容・stub 境界 |
|---|---|
| `test_t2683_mismatch_preserves_all_comparison_rows` | `tests:367` 後。governor だけを `powersave` に変更。まず実 `_attest` の typed 例外と全属性を確認し、次に child helper を呼ぶ。rc=31、sidecar が 1 個、accepted file 不在、21 行中当該 1 行のみ非 pass、残り 20 行 pass、全行の expected/observed 保持、9 keys・両 hash・projection・`failed_fields` を検査。 |
| `test_t2683_match_preserves_accepted_bytes_without_sidecar` | 同位置。一致入力。成功時の全 payload を旧契約から構成した oracle とし、canonical bytes＋改行とファイル bytes を比較。helper の出力をそのまま期待値に流用しない。rc=0、mismatch file 不在、追加ファイル不在。pre-round と post-series を parameterize。 |
| `test_t2683_empty_comparisons_writes_rejected_sidecar` | 同位置。`compare_profiles` だけ `[]` に差替え。他は実物。rc=31、`comparisons=[]`、`failed_fields=[]`、rejected schema/status、accepted file 不在。 |
| `test_t2683_sidecar_write_failure_preserves_rc` | 同位置。実不一致を発生させ、driver の `create_json` を mismatch path のみ例外にする。`OSError` と `QualificationArtifactError` を parameterize。書込み試行 path を確認し、helper が例外を漏らさず rc=31、accepted file 不在。 |
| `test_t2683_probe_failure_has_no_sidecar` | 同位置。probe だけ `OSError`。実 `_attest` と child helper を通し、rc=31、accepted/mismatch 両方不在。 |
| `test_t2683_existing_sidecar_is_not_overwritten` | 同位置。実 `create_json` で異なる診断 bytes を先置きしてから実不一致。create-only 衝突でも rc=31、先置き bytes 不変、accepted file 不在。writer は stub しない。 |
| `test_t2683_parent_message_names_sidecar_and_failed_fields` | 同位置。実 child helper の出力を実 message helper に渡す。attempt 相対 path と governor 名を exact 比較。pre-round/post-series を parameterize。 |
| `test_t2683_parent_message_without_sidecar_is_legacy` | 同位置。sidecar 不在で実 helper を呼び、固定文言と完全一致。reader は stub しない。 |
| `test_t2683_parent_message_unreadable_sidecar_is_best_effort` | 同位置。壊れた JSON、canonical JSON だが `failed_fields` の型不正、読取り時 `OSError` を parameterize。最後だけ loader を stub。診断 path と `unavailable` を返し、例外を漏らさない。 |
| `test_t2683_diagnostic_rejection_preserves_ledger_contract` | `tests:675` 後。実 child/message helper を順に呼ぶ小さい `attestation_fn` を `run_series` に渡す。非ゼロなら `AttestationError(message)`。実 FSM/ledger/replay を通し、rc=31・rejected・evidence と外側 payload の exact keys を確認。pre-round と post-series の失敗を parameterize。member/reservation/clock は既存 FSM tests 同様に stub。 |

最後の test は、正常 sidecar・不在・読取り不能も parameterize し、診断取得の成否が rc と台帳の構造を変えないことを確認する。post-series ケースは既存 positive control 相当の member 値で終端へ到達させる。

既存 `test_t541_attest_*`、`test_attestation_failure_is_terminal_reject_with_exact_rc` は assertion を弱めず維持する。これらの単体 tests は実 fork/wait の実測を代替しない。closure の委譲・exitcode 分岐は差分レビューでも確認する。

親の焦点走：

```bash
python3 tools/run_tests.py orchestrator/tests/test_t126_qualification_driver.py
```

変異実走は親 brief 指定の container worktree / `tools/mutation_harness.py` へ渡す。

## 6. 変異事前登録の候補

各変異は独立適用する。「専属」は事前指定する主 killer の意味とし、他 test も落ちることを排除しない。

| ID | 変異 | 期待 killer test |
|---|---|---|
| M1 | mismatch 分岐の `create_json` を削除し、rc=31 だけ返す | `test_t2683_mismatch_preserves_all_comparison_rows` |
| M2 | 成功時にも mismatch sidecar を書く | `test_t2683_match_preserves_accepted_bytes_without_sidecar` |
| M3 | sidecar の `failed_fields` を常に `[]` にする | `test_t2683_mismatch_preserves_all_comparison_rows` |
| M4 | `comparisons` を非 pass 行だけへ絞り、pass 行を捨てる | `test_t2683_mismatch_preserves_all_comparison_rows` |
| M5 | 空 comparisons では sidecar を書かず rc=31 を返す | `test_t2683_empty_comparisons_writes_rejected_sidecar` |
| M6 | child helper の書込み例外時 return を rc=34 に変える | `test_t2683_sidecar_write_failure_preserves_rc` |
| M7 | probe 等の汎用失敗にも空 comparisons の sidecar を書く | `test_t2683_probe_failure_has_no_sidecar` |
| M8 | 親 message を常に旧固定文言へ戻す | `test_t2683_parent_message_names_sidecar_and_failed_fields` |
| M9 | sidecar reader の例外を再 raise する | `test_t2683_parent_message_unreadable_sidecar_is_best_effort` |
| E1 | helper の説明 comment のみ変更 | 等価対照。全 test 生存を期待。 |

M2 は成功時 sidecar 不在、M4 は全行保持、M6 は診断書込みと制御結果の分離をそれぞれ直接検証する。構文破壊・import 失敗を killer 成功に数えない。

## 7. リスク

**create-only 衝突。**
`artifacts.py:449` は既存 target を拒否する。stage と round/final の組合せで通常呼出しは区別されるが、衝突時は上書き・再試行名・別名 sidecar を作らず rc=31 とする。既存 sidecar の存在だけでは今回の子が公開した証明にならないため、親 message は診断参照にとどめる。receipt authority や公開成功の証明にはしない。

**D474 と fsync。**
`create_json`（`artifacts.py:527`）は `create_bytes` を呼び、L470 で file、L480/L492 で directory を fsync する。したがって本案は D474 の「rc を変えない」「独立 sidecar」を満たすが、「fsync しない」は満たさない。親の指定を優先して既存 API を使う留保を残す。I/O stall では既存 timeout に達し、rc=31 のまま timeout message となり、sidecar 完成は保証できない。

**`evidence_manifest` と `verify()`。**
`driver:1288` の `rglob` は `run_series` 正常復帰後にだけ到達する。不一致では例外が伝播するため sidecar が成功 manifest に混入する経路は増えない。`verify()`（L1323）は変更せず、失敗 attempt を新しく verify 成功可能にしない。成功時 sidecar 不在の test がこの前提を支える。

**`attestation_records`。**
L1188 で作り、L1260 で成功 JSON の `file_record` を append しているが、その後の消費はない。今回これを整理・転用せず、sidecar record も追加しない。診断のための hash 計算や manifest 登録を増やさない。

**identity file としての driver。**
依頼が示す `contract.py:51` の識別集合に含まれる driver を変更するため、コード identity の digest と、それを含む新規 series identity は変わり得る。「accepted payload bytes 不変」は attestation JSON の意味であり、新旧コードによる attempt 全体の同一 bytes を意味しない。識別集合から driver を外す・古い digest を固定する対応は行わない。歴史 snapshot の pin は親 brief の調査結果に従い更新しない。

**`V2_ENV_NEUTRAL_MODULES`。**
同集合や対象 module を変更しない。新 helper は既存 contract/profile/comparisons を受け渡し、環境名 literal・環境別分岐・新しい probe を追加しない。比較の権威は引き続き既存 `compare_profiles` と現行の非空・全行 pass 条件に限定する。
