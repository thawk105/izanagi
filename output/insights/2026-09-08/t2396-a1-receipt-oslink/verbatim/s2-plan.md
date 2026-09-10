## 結論

推奨は次のとおりです。

- submission receipt は完成済み staging file を `os.link(..., follow_symlinks=False)` で公開し、その後に staging link を撤去する。
- completion receipt も同じ共通 helper に揃える。
- staging basename は submission を `.s-<pid hex>`、completion を `.c-<pid hex>` とし、長い basename を切り詰めても相互衝突しないようにする。
- materialization は directory 公開なので変更しない。
- `receipts/submission-failure.json` も本 wave では変更しない。
- 公開後の staging 撤去失敗では完成名を巻き戻さない。公開済み状態を専用の `PaperStoryError` subtype で報告し、v3 では虚偽の submission-failure receipt を追加しない。
- JSON の schema、field、canonical bytes は一切変えない。

以下の行番号は基準 commit `0e02169b0` の現行行です。前段への挿入により実装後の行番号は後ろへずれます。

## `os.link` の呼び出し形

決定する呼び出しは次です。

```python
os.link(staging, path, follow_symlinks=False)
```

理由は次のとおりです。

- `staging` と `path` は同一 parent に置かれるため、cross-filesystem hard link にはならない。
- `follow_symlinks=False` を明示し、source path が意図せず dereference される形を採らない。
- `dir_fd` は使わない。現行 A-1 経路は `Path` と `_fsync_directory(path.parent)` で同一 parent を扱っており、parent descriptor を保持していない。ここだけ descriptor lifecycle を追加する必要はない。
- `create_only_store.py:166-177` は no-follow read と既存 claim 読取りのため、先に parent descriptor を開く設計であり、そこでの `dir_fd` はその既存設計に沿ったもの。A-1 receipt にその構造を持ち込む必要はない。
- `create_only_store.py:207-213` は `follow_symlinks=False` の先例、`calibrator/cli.py:344-353` は path 指定による link-unlink の先例になる。

例外分岐は `FileExistsError` を先に捕捉し、それ以外の `OSError` とコード上で明確に分けます。

- 既存先: `PaperStoryError`
- message: `no-replace submission receipt publish failed: File exists`
- completion の既存先: `no-replace completion receipt publish failed: File exists`
- その他の `OSError`: 同じ prefix に `exc.strerror` を付ける。
- 現行 submission の prefix `no-replace submission receipt publish failed: ...` は維持する。

## production の逐語変更案

`orchestrator/campaign/paper_story_a1_paired.py:34` の import を変更します。

変更前:

```python
from typing import Any, Mapping, Sequence
```

変更後:

```python
from typing import Any, Literal, Mapping, Sequence
```

`orchestrator/campaign/paper_story_a1_paired.py:418-420` の直後へ、公開済み cleanup failure を区別する内部例外を挿入します。

変更前には存在しません。

変更後:

```python
class _PublishedReceiptCleanupError(PaperStoryError):
    """Receipt publication succeeded, but owned staging cleanup failed."""
```

この subtype は schema、receipt、evidence を増やさず、公開後失敗を caller が誤分類しないためだけに使います。

`_submission_receipt_staging_path`、`_remove_submission_receipt_staging` は receipt 共通名へ変えます。置換位置は `orchestrator/campaign/paper_story_a1_paired.py:836-871` です。

変更前:

```python
def _submission_receipt_staging_path(path: Path) -> Path:
    """Derive a PID staging basename no longer than the valid final basename."""
    suffix = f".s-{os.getpid():x}"
    basename_budget = len(os.fsencode(path.name))
    stem_budget = basename_budget - len(os.fsencode(f".{suffix}"))
    stem = path.name
    while stem and len(os.fsencode(stem)) > stem_budget:
        stem = stem[:-1]
    if not stem:
        raise PaperStoryError("submission receipt basename cannot fit staging name")
    return path.parent / f".{stem}{suffix}"


def _remove_submission_receipt_staging(
    staging: Path, identity: tuple[int, int]
) -> None:
    try:
        info = staging.lstat()
    except FileNotFoundError:
        return
    except OSError as exc:
        raise PaperStoryError(
            f"submission receipt staging cleanup stat failed: {exc}"
        ) from exc
    if (
        not stat.S_ISREG(info.st_mode)
        or (info.st_dev, info.st_ino) != identity
    ):
        raise PaperStoryError("submission receipt staging cleanup identity differs")
    try:
        staging.unlink()
        _fsync_directory(staging.parent)
    except OSError as exc:
        raise PaperStoryError(
            f"submission receipt staging cleanup failed: {exc}"
        ) from exc
```

変更後:

```python
def _receipt_staging_path(
    path: Path,
    *,
    receipt_kind: Literal["submission", "completion"],
) -> Path:
    """Derive a kind-separated PID staging basename within the final-name budget."""
    marker = receipt_kind[0]
    suffix = f".{marker}-{os.getpid():x}"
    basename_budget = len(os.fsencode(path.name))
    stem_budget = basename_budget - len(os.fsencode(f".{suffix}"))
    stem = path.name
    while stem and len(os.fsencode(stem)) > stem_budget:
        stem = stem[:-1]
    if not stem:
        raise PaperStoryError("receipt basename cannot fit staging name")
    return path.parent / f".{stem}{suffix}"


def _remove_receipt_staging(
    staging: Path, identity: tuple[int, int]
) -> None:
    try:
        info = staging.lstat()
    except FileNotFoundError:
        return
    except OSError as exc:
        raise PaperStoryError(
            f"receipt staging cleanup stat failed: {exc}"
        ) from exc
    if (
        not stat.S_ISREG(info.st_mode)
        or (info.st_dev, info.st_ino) != identity
    ):
        raise PaperStoryError("receipt staging cleanup identity differs")
    try:
        staging.unlink()
        _fsync_directory(staging.parent)
    except OSError as exc:
        raise PaperStoryError(
            f"receipt staging cleanup failed: {exc}"
        ) from exc
```

dev/ino identity 契約は変えません。

- `_exclusive_write_bytes` が作成直後の `(st_dev, st_ino)` を返す。
- cleanup は `lstat()` で final symlink を追わず、regular file と dev/ino の一致を確認する。
- 一致しない staging は削除せず `PaperStoryError` にする。
- `FileNotFoundError` は既に撤去済みとして受理する。
- unlink 後に parent directory を fsync する。

submission と completion は basename の切り詰め後に stem が一致しても、末尾がそれぞれ `.s-<pid hex>` と `.c-<pid hex>` になるため衝突しません。

`_publish_submission_receipt` は共通 helper と二つの薄い wrapper に置換します。置換位置は `orchestrator/campaign/paper_story_a1_paired.py:874-890`、`_exclusive_write_text` の直前です。

変更前:

```python
def _publish_submission_receipt(path: Path, value: object) -> None:
    raw = _canonical_json_bytes(value)
    staging = _submission_receipt_staging_path(path)
    staging_identity = _exclusive_write_bytes(staging, raw)
    published = False
    try:
        try:
            _renameat2_directory(staging, path, _RENAME_NOREPLACE)
        except OSError as exc:
            raise PaperStoryError(
                f"no-replace submission receipt publish failed: {exc.strerror}"
            ) from exc
        published = True
        _fsync_directory(path.parent)
    finally:
        if not published:
            _remove_submission_receipt_staging(staging, staging_identity)
```

変更後:

```python
def _publish_receipt(
    path: Path,
    value: object,
    *,
    receipt_kind: Literal["submission", "completion"],
) -> None:
    raw = _canonical_json_bytes(value)
    staging = _receipt_staging_path(path, receipt_kind=receipt_kind)
    staging_identity = _exclusive_write_bytes(staging, raw)
    published = False
    try:
        try:
            os.link(staging, path, follow_symlinks=False)
        except FileExistsError as exc:
            raise PaperStoryError(
                f"no-replace {receipt_kind} receipt publish failed: {exc.strerror}"
            ) from exc
        except OSError as exc:
            raise PaperStoryError(
                f"no-replace {receipt_kind} receipt publish failed: {exc.strerror}"
            ) from exc
        published = True
        _fsync_directory(path.parent)
    finally:
        try:
            _remove_receipt_staging(staging, staging_identity)
        except PaperStoryError as exc:
            if published:
                raise _PublishedReceiptCleanupError(str(exc)) from exc
            raise


def _publish_submission_receipt(path: Path, value: object) -> None:
    _publish_receipt(path, value, receipt_kind="submission")


def _publish_completion_receipt(path: Path, value: object) -> None:
    _publish_receipt(path, value, receipt_kind="completion")
```

新 helper の配置と caller は次です。

- `_publish_receipt`: 現行 `:874` の位置。
- `_publish_submission_receipt`: `_publish_receipt` の直後。caller は現行 `:3244` と `:3343`。
- `_publish_completion_receipt`: submission wrapper の直後。caller は現行 `:4260` と `:4350`。
- `_receipt_staging_path`: 現行 `:836`。production caller は共通 publisher、`_run_submit_v3`、`run_submit`。
- `_remove_receipt_staging`: 現行 `:849`。caller は `_publish_receipt` の `finally` だけ。

## staging 撤去と `published` の扱い

現行は `published=False` のときだけ cleanup するため、rename 成功後は staging path 自体が消えている前提でした。hard link では source staging が残るので、この条件付き cleanup は使えません。

変更後は次の順序です。

1. canonical JSON を staging へ create-only write し、file fd を fsync。
2. `os.link` で完成名を原子的に追加。
3. `published=True` にする。
4. parent directory を fsync し、完成名の公開を先に durable にする。
5. `finally` で成功・失敗を問わず、dev/ino 検査付きで staging を撤去。
6. staging unlink 後にも既存 helper が parent directory を fsync。

`published` は cleanup の有無には使わず、cleanup failure の意味を区別するために残します。

- link 前または link 失敗後の cleanup failure:通常の `PaperStoryError`。完成名はこの呼出しでは公開されていない。
- link 成功後の cleanup failure: `_PublishedReceiptCleanupError`。完成名は公開済みであり、巻き戻さない。
- 完成名を unlink して「公開失敗」に戻すことはしない。既に consumer から見えた create-only receipt を消す方が危険なため。
- command 自体は非ゼロで報告するが、「公開された receipt」と「submission-failure receipt」を同時生成しない。

この最後の点のため、`_run_submit_v3` の catch を分けます。変更位置は `orchestrator/campaign/paper_story_a1_paired.py:3243-3251` です。

変更前:

```python
    try:
        _publish_submission_receipt(submission_path, receipt)
    except PaperStoryError:
        _write_v3_submission_failure(
            failure_path, study_id=study_id, source_commit=expected_head,
            attempt=attempt, intent_sha256=intent["intent_sha256"],
            jobs=failure_jobs,
        )
        raise
```

変更後:

```python
    try:
        _publish_submission_receipt(submission_path, receipt)
    except _PublishedReceiptCleanupError:
        raise
    except PaperStoryError:
        _write_v3_submission_failure(
            failure_path, study_id=study_id, source_commit=expected_head,
            attempt=attempt, intent_sha256=intent["intent_sha256"],
            jobs=failure_jobs,
        )
        raise
```

`_run_submit_v3` 内の staging freshness path も変更します。位置は現行 `:3082` です。

変更前:

```python
    staging_path = _submission_receipt_staging_path(submission_path)
```

変更後:

```python
    staging_path = _receipt_staging_path(
        submission_path, receipt_kind="submission",
    )
```

legacy `run_submit` の staging freshness path も変更します。位置は現行 `:3278` です。

変更前:

```python
    submission_staging_path = _submission_receipt_staging_path(submission_path)
```

変更後:

```python
    submission_staging_path = _receipt_staging_path(
        submission_path, receipt_kind="submission",
    )
```

## P1 completion receipt

completion receipt は同じ staging + hard-link 形へ揃えるのを推奨します。

根拠は、現行 `orchestrator/campaign/paper_story_a1_paired.py:4260` と `:4350` が完成名を `O_EXCL` で直接開いてから bytes を書くため、書込み途中の停止で不完全な完成名が残り得ることです。submission と同様、完成済み staging だけを公開すべきです。

`_run_complete_v3` の `orchestrator/campaign/paper_story_a1_paired.py:4259-4261` を変更します。

変更前:

```python
    completion_path = Path(evidence["completion_receipt"])
    _exclusive_write(completion_path, completion)
    _fsync_directory(completion_path.parent)
```

変更後:

```python
    completion_path = Path(evidence["completion_receipt"])
    _publish_completion_receipt(completion_path, completion)
```

legacy `run_complete` の `orchestrator/campaign/paper_story_a1_paired.py:4349-4351` も同様です。

変更前:

```python
    completion_path = Path(evidence["completion_receipt"])
    _exclusive_write(completion_path, completion)
    _fsync_directory(completion_path.parent)
```

変更後:

```python
    completion_path = Path(evidence["completion_receipt"])
    _publish_completion_receipt(completion_path, completion)
```

`_canonical_json_bytes(completion)` は現行 `_exclusive_write` が生成している bytes と同じです。したがって completion JSON の schema、field、indent、sort、末尾 newline は変わりません。

## P2 materialize を変えない根拠

materialize は変更しません。

コード上の事実は次です。

- `orchestrator/campaign/paper_story_a1_paired.py:8266-8269` で staging を `staging.mkdir(mode=0o700)` により directory として作る。
- `:8279-8293` で `receipt.json`、`result.json`、`README.md`、必要なら sizing pilot をその directory 内へ書く。
- `:8199` で completion marker も `staging / COMPLETION_MARKER` に書く。
- `:8202-8205` で staging directory 全体を `_publish_staging_noreplace` または `_publish_staging_after_einval` へ渡す。
- `:8303-8305` の `_publish_complete_staging(staging, destination, ...)` が directory publish 境界である。

`os.link` は regular file の hard link には使えますが、directory の hard link は通常の user process には許可されません。したがって file receipt と同じ primitive へ置換できません。

次は維持します。

- `_renameat2_directory`: `:8019-8042`
- `_publish_staging_noreplace`: `:8044-8052`
- `_observe_materialization_publish`: `:8092-8128`
- `_publish_staging_after_einval`: `:8155-8186`
- `_publish_complete_staging`: `:8188-8207`
- `_publish_materialization_bundle`: `:8256-8309`
- `PUBLISH_RENAME_NOREPLACE`、`PUBLISH_EINVAL_FALLBACK`、`_RENAME_DEFAULT`、`_RENAME_NOREPLACE`: `:393-396`

`test_paper_story_a1_paired.py:2240-2407` 付近の materialization 正負例も変更しません。

## P3 submission-failure receipt

`receipts/submission-failure.json` は本 wave では変更しないのを推奨します。

現行経路は `orchestrator/campaign/paper_story_a1_paired.py:3037-3067` です。

```python
def _write_v3_submission_failure(
    path: Path,
    *,
    study_id: str,
    source_commit: str,
    attempt: Path,
    intent_sha256: str,
    jobs: Sequence[Mapping[str, object]],
) -> None:
    statuses = [dict(item) for item in jobs]
    while len(statuses) < len(WORKLOAD_ORDER):
        ordinal = len(statuses)
        statuses.append({
            "workload": WORKLOAD_ORDER[ordinal],
            "ordinal": ordinal,
            "status": "not-attempted",
            "request_id": None,
            "returncode": None,
        })
    _exclusive_write(path, {
        "schema_version": V3_GROUP_SUBMISSION_FAILURE_SCHEMA,
        "status": "not-successful",
        "reason": "scheduler-or-infrastructure-failure-before-bench",
        "study_id": study_id,
        "source_commit": source_commit,
        "attempt_root": os.fspath(attempt),
        "intent_sha256": intent_sha256,
        "jobs": statuses,
        "recorded_epoch": int(time.time()),
    })
    _fsync_directory(path.parent)
```

据え置く理由は次です。

- D1732 が直接指定したのは group submission receipt。
- failure receipt は成功した attempt の proof chain を閉じる完成名ではない。
- partial bytes が failure 名を占有するリスクは残るが、成功済み attempt の completion を妨げるものではない。
- この経路まで共通 publisher にすると、失敗処理中の二次失敗、既存 failure receipt との意味、retry policy を別途決める必要が生じる。
- 今回そこまで広げると P3 の独立論点を同じ commit に混ぜる。

ただし、公開成功後の staging cleanup failure では `_PublishedReceiptCleanupError` を `_run_submit_v3` が先に捕捉するため、`submission.json` と `submission-failure.json` の矛盾した同時生成は避けます。

## 既存 7 テストの逐語書換え

対象は `orchestrator/tests/test_paper_story_a1_job_contract.py` の 7 本です。

`test_m1_submission_receipt_is_complete_before_final_path_is_visible`、現行 `:2310-2343` の primitive inspection 部分。

変更前:

```python
    real_rename = paired._renameat2_directory
    publish_boundaries = []

    def inspect_publish(staging, destination, flags):
        if destination == submission_path:
            raw = staging.read_bytes()
            document = json.loads(raw)
            assert staging != destination
            assert not os.path.lexists(destination)
            assert raw == paired._canonical_json_bytes(document)
            assert set(document) == paired._SUBMISSION_RECEIPT_KEYS
            assert flags == paired._RENAME_NOREPLACE
            publish_boundaries.append((staging, destination))
        return real_rename(staging, destination, flags)

    monkeypatch.setattr(paired, "_renameat2_directory", inspect_publish)
```

変更後:

```python
    real_link = paired.os.link
    publish_boundaries: list[tuple[Path, Path]] = []

    def inspect_publish(
        staging: Path,
        destination: Path,
        *,
        follow_symlinks: bool,
    ) -> None:
        if destination == submission_path:
            raw = staging.read_bytes()
            document = json.loads(raw)
            assert staging != destination
            assert not os.path.lexists(destination)
            assert raw == paired._canonical_json_bytes(document)
            assert set(document) == paired._SUBMISSION_RECEIPT_KEYS
            assert follow_symlinks is False
            publish_boundaries.append((staging, destination))
        real_link(
            staging,
            destination,
            follow_symlinks=follow_symlinks,
        )

    monkeypatch.setattr(paired.os, "link", inspect_publish)
```

同じ test の末尾へ追加:

```python
    assert not os.path.lexists(paired._receipt_staging_path(
        submission_path, receipt_kind="submission",
    ))
```

この書換え後も、完成済み canonical bytes が final path の可視化前に staging にあり、final path がまだ存在せず、公開境界が一度だけ通ることを検査します。

`test_m2_submission_receipt_publish_is_no_replace`、現行 `:2346-2360`。

変更前:

```python
    occupied = tmp_path / "occupied.submission.json"
    occupied.write_bytes(b"existing receipt\n")
    with pytest.raises(paired.PaperStoryError, match="no-replace"):
        paired._publish_submission_receipt(occupied, {"value": "replacement"})
    assert occupied.read_bytes() == b"existing receipt\n"

    clean = tmp_path / "clean.submission.json"
    paired._publish_submission_receipt(clean, {"value": "accepted"})
    assert clean.read_bytes() == paired._canonical_json_bytes({"value": "accepted"})
```

変更後:

```python
    occupied = tmp_path / "occupied.submission.json"
    original = b"existing receipt\n"
    occupied.write_bytes(original)
    occupied_staging = paired._receipt_staging_path(
        occupied, receipt_kind="submission",
    )
    with pytest.raises(
        paired.PaperStoryError,
        match=r"^no-replace submission receipt publish failed: File exists$",
    ):
        paired._publish_submission_receipt(
            occupied, {"value": "replacement"},
        )
    assert occupied.read_bytes() == original
    assert not os.path.lexists(occupied_staging)

    clean = tmp_path / "clean.submission.json"
    clean_staging = paired._receipt_staging_path(
        clean, receipt_kind="submission",
    )
    paired._publish_submission_receipt(clean, {"value": "accepted"})
    assert clean.read_bytes() == paired._canonical_json_bytes(
        {"value": "accepted"}
    )
    assert not os.path.lexists(clean_staging)
```

既存先を拒否し bytes を保存する性質に加え、正負両方の staging 撤去と例外 message まで固定するので弱くなりません。

`test_submission_receipt_rename_failure_removes_owned_staging`、現行 `:2492-2526` は link failure の二分類へ改名します。

変更前:

```python
@pytest.mark.parametrize(
    "rename_failure",
    [
        OSError(errno.EIO, "input/output error"),
        paired.PaperStoryError("renameat2 no-replace is unavailable"),
    ],
    ids=("oserror", "paper-story-error"),
)
def test_submission_receipt_rename_failure_removes_owned_staging(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    rename_failure: Exception,
) -> None:
    """Acceptance implication: cleanup leaves the namespace reusable after failure.
    Rejection implication: either rename failure path must remove its owned staging file.
    Positive example: a later clean destination publishes after the failed attempt.
    """
    destination = tmp_path / "failed.submission.json"
    staging = paired._submission_receipt_staging_path(destination)

    def fail_rename(_staging, _destination, _flags):
        raise rename_failure

    with monkeypatch.context() as patch:
        patch.setattr(paired, "_renameat2_directory", fail_rename)
        with pytest.raises(paired.PaperStoryError):
            paired._publish_submission_receipt(destination, {"value": "failed"})
```

変更後:

```python
@pytest.mark.parametrize(
    "link_failure",
    [
        FileExistsError(errno.EEXIST, os.strerror(errno.EEXIST)),
        OSError(errno.EIO, os.strerror(errno.EIO)),
    ],
    ids=("file-exists", "other-oserror"),
)
def test_submission_receipt_link_failure_removes_owned_staging(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    link_failure: OSError,
) -> None:
    """Acceptance implication: cleanup leaves the namespace reusable after failure.
    Rejection implication: both link failure classes remove their owned staging file.
    Positive example: a later clean destination publishes after the failed attempt.
    """
    destination = tmp_path / "failed.submission.json"
    staging = paired._receipt_staging_path(
        destination, receipt_kind="submission",
    )

    def fail_link(
        _staging: Path,
        _destination: Path,
        *,
        follow_symlinks: bool,
    ) -> None:
        assert follow_symlinks is False
        raise link_failure

    with monkeypatch.context() as patch:
        patch.setattr(paired.os, "link", fail_link)
        with pytest.raises(paired.PaperStoryError):
            paired._publish_submission_receipt(
                destination, {"value": "failed"},
            )
```

現行 test の後半はそのまま残します。

```python
    assert not os.path.lexists(staging)
    assert not os.path.lexists(destination)

    clean = tmp_path / "clean-after-failure.submission.json"
    paired._publish_submission_receipt(clean, {"value": "accepted"})
    assert clean.read_bytes() == paired._canonical_json_bytes(
        {"value": "accepted"}
    )
```

従来の二つの failure branch を、`FileExistsError` とそれ以外の `OSError` という新しい実 branch に対応させます。

`test_submission_receipt_cleanup_preserves_replaced_staging`、現行 `:2529-2556` の helper と monkeypatch 部分。

変更前:

```python
    staging = paired._submission_receipt_staging_path(destination)
    replacement = tmp_path / "foreign-staging"
    replacement.write_bytes(b"foreign staging\n")

    def replace_then_fail(active_staging, _destination, _flags):
        active_staging.unlink()
        replacement.rename(active_staging)
        raise paired.PaperStoryError("renameat2 no-replace is unavailable")

    with monkeypatch.context() as patch:
        patch.setattr(paired, "_renameat2_directory", replace_then_fail)
```

変更後:

```python
    staging = paired._receipt_staging_path(
        destination, receipt_kind="submission",
    )
    replacement = tmp_path / "foreign-staging"
    replacement.write_bytes(b"foreign staging\n")

    def replace_then_fail(
        active_staging: Path,
        _destination: Path,
        *,
        follow_symlinks: bool,
    ) -> None:
        assert follow_symlinks is False
        active_staging.unlink()
        replacement.rename(active_staging)
        raise OSError(errno.EIO, os.strerror(errno.EIO))

    with monkeypatch.context() as patch:
        patch.setattr(paired.os, "link", replace_then_fail)
```

残りの assertion は維持します。

```python
        with pytest.raises(
            paired.PaperStoryError, match="staging cleanup identity differs",
        ):
            paired._publish_submission_receipt(destination, {"value": "failed"})
    assert staging.read_bytes() == b"foreign staging\n"

    clean = tmp_path / "clean-after-replacement.submission.json"
    paired._publish_submission_receipt(clean, {"value": "accepted"})
    assert clean.is_file()
```

dev/ino が異なる foreign staging を消さない性質はそのままです。

`test_submit_rejects_foreign_staging_before_intent_and_qsub`、現行 `:2568-2570`。

変更前:

```python
    staging = paired._submission_receipt_staging_path(
        Path(evidence["submission_receipt"])
    )
```

変更後:

```python
    staging = paired._receipt_staging_path(
        Path(evidence["submission_receipt"]),
        receipt_kind="submission",
    )
```

foreign staging が intent と qsub より前に拒否される assertion は一切変えません。

`test_submit_accepts_clean_evidence_and_staging_namespace`、現行 `:2602-2604`。

変更前:

```python
    staging = paired._submission_receipt_staging_path(
        Path(evidence["submission_receipt"])
    )
```

変更後:

```python
    staging = paired._receipt_staging_path(
        Path(evidence["submission_receipt"]),
        receipt_kind="submission",
    )
```

clean namespace が一度だけ submit でき、最終 staging が残らない assertion は維持します。

`test_submit_accepts_name_max_submission_basename`、現行 `:2633`。

変更前:

```python
    staging = paired._submission_receipt_staging_path(submission)
```

変更後:

```python
    staging = paired._receipt_staging_path(
        submission, receipt_kind="submission",
    )
```

final basename が `PC_NAME_MAX` ちょうどでも staging basename が上限内に収まる検査は維持します。

## 新規テストの逐語案

`orchestrator/tests/test_paper_story_a1_job_contract.py:2361` の直後へ、completion helper の正負例を追加します。

```python
def test_completion_receipt_publish_is_no_replace(
    tmp_path: Path,
) -> None:
    occupied = tmp_path / "occupied.completion.json"
    original = b"existing completion\n"
    occupied.write_bytes(original)
    occupied_staging = paired._receipt_staging_path(
        occupied, receipt_kind="completion",
    )
    with pytest.raises(
        paired.PaperStoryError,
        match=r"^no-replace completion receipt publish failed: File exists$",
    ):
        paired._publish_completion_receipt(
            occupied, {"value": "replacement"},
        )
    assert occupied.read_bytes() == original
    assert not os.path.lexists(occupied_staging)

    clean = tmp_path / "clean.completion.json"
    clean_staging = paired._receipt_staging_path(
        clean, receipt_kind="completion",
    )
    paired._publish_completion_receipt(clean, {"value": "accepted"})
    assert clean.read_bytes() == paired._canonical_json_bytes(
        {"value": "accepted"}
    )
    assert not os.path.lexists(clean_staging)
```

同じ付近へ、公開後 cleanup failure の契約を追加します。

```python
def test_receipt_cleanup_failure_reports_already_published_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    destination = tmp_path / "published.submission.json"
    staging = paired._receipt_staging_path(
        destination, receipt_kind="submission",
    )
    expected = paired._canonical_json_bytes({"value": "published"})

    def refuse_cleanup(
        active_staging: Path,
        identity: tuple[int, int],
    ) -> None:
        assert active_staging == staging
        assert identity == (
            active_staging.stat().st_dev,
            active_staging.stat().st_ino,
        )
        assert destination.read_bytes() == expected
        raise paired.PaperStoryError(
            "receipt staging cleanup failed: injected",
        )

    monkeypatch.setattr(
        paired, "_remove_receipt_staging", refuse_cleanup,
    )
    with pytest.raises(
        paired._PublishedReceiptCleanupError,
        match="receipt staging cleanup failed: injected",
    ):
        paired._publish_submission_receipt(
            destination, {"value": "published"},
        )
    assert destination.read_bytes() == expected
    assert staging.read_bytes() == expected
```

`test_complete_only_issues_completion_receipt_without_materialize` の直後、現行 `:2861` に v2/v3 wiring 検査を追加します。

```python
def test_completion_publish_wiring_covers_v2_and_v3() -> None:
    source = Path(paired.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    for function_name in ("_run_complete_v3", "run_complete"):
        function = next(
            node for node in tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name == function_name
        )
        calls = [
            node for node in ast.walk(function)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
        ]
        assert sum(
            node.func.id == "_publish_completion_receipt"
            for node in calls
        ) == 1
        assert not any(
            node.func.id == "_exclusive_write"
            and node.args
            and isinstance(node.args[0], ast.Name)
            and node.args[0].id == "completion_path"
            for node in calls
        )
```

v3 submission testsの近く、現行 `test_v3_submit_fans_out_exact_workload_triple_and_publishes_group_receipt` の後へ、cleanup failure が failure receipt を偽造しない検査を追加します。

```python
def test_v3_published_cleanup_failure_does_not_write_failure_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _repo, attempt, head, _policy = _v3_submit_cli_fixture(
        tmp_path, monkeypatch,
    )
    qsub_calls: list[list[str]] = []

    def qsub(argv, *, cwd):
        ordinal = len(qsub_calls)
        qsub_calls.append(list(argv))
        return subprocess.CompletedProcess(
            argv, 0, f"{123 + ordinal}.server\n", "",
        )

    def publish_then_report(path: Path, value: object) -> None:
        path.write_bytes(paired._canonical_json_bytes(value))
        raise paired._PublishedReceiptCleanupError(
            "receipt staging cleanup failed: injected",
        )

    failure_calls = []
    monkeypatch.setattr(paired, "_run_qsub", qsub)
    monkeypatch.setattr(
        paired, "_observe_qstat_visibility", _v3_visibility,
    )
    monkeypatch.setattr(
        paired, "_publish_submission_receipt", publish_then_report,
    )
    monkeypatch.setattr(
        paired,
        "_write_v3_submission_failure",
        lambda *args, **kwargs: failure_calls.append((args, kwargs)),
    )

    with pytest.raises(
        paired._PublishedReceiptCleanupError,
        match="receipt staging cleanup failed: injected",
    ):
        paired.run_submit(SimpleNamespace(
            study_id=paired.V3_PILOT_STUDY_ID,
            expected_head=head,
            attempt_root=os.fspath(attempt),
        ))

    evidence = paired._v3_attempt_evidence_paths(attempt)
    submission_path = Path(evidence["submission_receipt"])
    assert len(qsub_calls) == 3
    assert json.loads(submission_path.read_bytes())[
        "schema_version"
    ] == paired.V3_GROUP_SUBMISSION_SCHEMA
    assert failure_calls == []
    assert not Path(evidence["submission_failure"]).exists()
```

## 正例・負例と赤になる条件

- `test_m1_submission_receipt_is_complete_before_final_path_is_visible`
  - staging が canonical JSON 完成前に公開される、final path へ直接書く、`follow_symlinks=False` を外す、公開後 staging が残る、のいずれかで赤になる。

- `test_m2_submission_receipt_publish_is_no_replace`
  - 空き先へ canonical bytes を公開できない、既存先で `PaperStoryError` にならない、既存 bytes が 1 byte でも変わる、正負いずれかで staging が残ると赤になる。

- `test_submission_receipt_link_failure_removes_owned_staging`
  - `FileExistsError` と他の `OSError` のどちらかで owned staging または destination が残ると赤になる。

- `test_submission_receipt_cleanup_preserves_replaced_staging`
  - dev/ino 検査が消え、foreign inode を unlink すると赤になる。

- `test_submit_rejects_foreign_staging_before_intent_and_qsub`
  - foreign staging があるのに intent 作成または qsub まで進むと赤になる。

- `test_submit_accepts_clean_evidence_and_staging_namespace`
  - clean namespace を過剰拒否する、receipt が生まれない、staging が残ると赤になる。

- `test_submit_accepts_name_max_submission_basename`
  - staging suffix によって basename が `PC_NAME_MAX` を越える、または有効な最長 submission を拒否すると赤になる。

- `test_completion_receipt_publish_is_no_replace`
  - completion が direct partial-write へ戻る、既存 bytes を変更する、canonical bytes が変わる、staging が残ると赤になる。

- `test_completion_publish_wiring_covers_v2_and_v3`
  - `_run_complete_v3` または `run_complete` が `_exclusive_write(completion_path, ...)` へ戻る、共通 publisher を呼ばなくなると赤になる。

- `test_receipt_cleanup_failure_reports_already_published_state`
  - cleanup failure 時に公開済み final を消す、専用状態を通常の未公開 failure と混同する、cleanup error を握りつぶすと赤になる。

- `test_v3_published_cleanup_failure_does_not_write_failure_receipt`
  - 公開済み `submission.json` と `submission-failure.json` を同時生成すると赤になる。

機構の負例は `test_m2_submission_receipt_publish_is_no_replace` と completion 版が挙動で検知します。実装を `os.replace`、`os.rename`、または flags なし rename に退化させると、既存完成名が上書きされるか例外が出なくなり、`pytest.raises` と元 bytes の完全一致の少なくとも一方が必ず赤になります。AST 上の関数名や monkeypatch の署名だけに依存した検知ではありません。

## 既存 7 テストが守る性質の対応表

| 現行テスト | 現行が守る性質 | 書換え後の守り方 |
|---|---|---|
| `:2310` M1 | 完成 bytes が final path の可視化より先に staging にある | `os.link` 呼出し直前に staging bytes、final 不在、canonical key set を検査し、成功後 staging 不在も確認 |
| `:2346` M2 | create-only、既存 bytes 不変、空き先成功 | 実在する既存 file に対する `PaperStoryError` と bytes 完全一致、正例 canonical bytes、両 branch の staging 不在を確認 |
| `:2500` rename failure cleanup | 二種類の publish failure で owned staging を撤去 | 実際の新 branch である `FileExistsError` と他の `OSError` を注入し、同じ cleanup と再利用可能性を確認 |
| `:2529` replaced staging | identity が異なる staging を消さない | link 境界で staging を別 inode に交換し、dev/ino mismatch と foreign bytes 保存を確認 |
| `:2559` foreign staging precheck | intent/qsub 前の namespace freshness | 新しい kind 付き path を置き、intent と qsub が共に起きないことを維持 |
| `:2593` clean namespace | clean な受理集合を狭めない | 新しい kind 付き path が空なら一度 submit でき、final が存在し staging が消えることを維持 |
| `:2620` NAME_MAX | 有効な最長 final basename を suffix のため拒否しない | submission marker `.s-` を含む新 helper の encoded length を同じ境界で確認 |

期待値の反転、skip、例外許容の拡張はありません。むしろ M2 は例外 message と staging cleanup を追加で固定します。

## 静的波及列挙

指定された production file と二つの test file 内での直接参照は次のとおりです。

- `_receipt_staging_path`
  - 新 `_publish_receipt`
  - `_run_submit_v3` 現行 `paper_story_a1_paired.py:3082`
  - `run_submit` 現行 `:3278`
  - 既存 test 現行 `test_paper_story_a1_job_contract.py:2510,2537,2568,2602,2633`
  - 新規 submission、completion、cleanup tests

- `_remove_receipt_staging`
  - 新 `_publish_receipt` の `finally`
  - cleanup failure test の monkeypatch seam

- `_publish_receipt`
  - `_publish_submission_receipt`
  - `_publish_completion_receipt`
  - 他の caller は作らない。

- `_publish_submission_receipt`
  - `_run_submit_v3` 現行 `paper_story_a1_paired.py:3244`
  - `run_submit` 現行 `:3343`
  - tests 現行 `test_paper_story_a1_job_contract.py:2355,2359,2518,2523,2551,2555`
  - v3 cleanup classification 新規 test

- `_publish_completion_receipt`
  - `_run_complete_v3` 現行 `paper_story_a1_paired.py:4260` の置換先
  - `run_complete` 現行 `:4350` の置換先
  - completion 正負例 test

- `_run_complete_v3`
  - `run_complete` 現行 `paper_story_a1_paired.py:4275`
  - 新規 wiring test
  - 指定 test 内に直接実行する既存 caller はない。

- `run_complete`
  - CLI `main` 現行 `paper_story_a1_paired.py:8667`
  - `test_paper_story_a1_job_contract.py:2848`
  - `test_paper_story_a1_paired.py:3465`

関連 fixture は次です。

- `_submit_cli_fixture`: `test_paper_story_a1_job_contract.py:2260` 付近。legacy submit の source、base、HEAD を用意。
- `_stub_successful_submit`: 同 `:2288` 付近。M1、clean、NAME_MAX などの qsub/visibility 正例。
- `_v3_submit_cli_fixture`: 同 `:2864`。v3 submit topology と policy を用意。
- `_v3_visibility`: 同 `:2900` 付近。v3 qstat visibility。
- `_acquisition`: 同 `:145`。legacy submission document fixture。
- `_noncertifying_bundle`: `test_paper_story_a1_paired.py:492` 付近。現行 `:845` では完成済み completion fixture を直接作るが、これは publisher の実装検査ではなく consumer 入力の構築なので変更不要。
- `_scheduler_completion_fixture`: `test_paper_story_a1_job_contract.py:972` 付近。validator 入力 bytes の構築であり、production publisher を模倣する fixture ではないので変更不要。

アンカー表の DW-O26 にある module-level consumer 集合は次です。

- `orchestrator/campaign/materializer_admission.py`
- `orchestrator/tests/test_campaign.py`
- `orchestrator/tests/test_ccbench_spawn_sites.py`
- `orchestrator/tests/test_hooks.py`
- `orchestrator/tests/test_official_perf_closure.py`
- `orchestrator/tests/test_p3_build_authority_cli.py`
- `orchestrator/tests/test_p3_exploration_namespace.py`
- `orchestrator/tests/test_paper_story_a1_headline.py`
- `orchestrator/tests/test_paper_story_a1_job_contract.py`
- `orchestrator/tests/test_paper_story_a1_paired.py`

アンカー表によれば `paper_story_a1_paired.py` の bytes を pin する golden はなく、公開機構を直接 pin しているのは上記 submission tests です。

変更しない `_exclusive_write` の一般 caller、intent、barrier、qsub stdout、request-id、qstat visibility、WAL snapshot、materialization contents は本変更の波及対象に含めません。

## 検証の親への引渡し

この段では read-only 指示に従い、編集、commit、pytest 実行はしていません。緑は主張しません。

実装後に親が確認する焦点は次です。

- 変更した job-contract test file。
- `test_paper_story_a1_paired.py` の materialization tests が無変更のまま通ること。
- submission 正例で final bytes が `_canonical_json_bytes(value)` と完全一致し staging 不在。
- submission 負例で exact `PaperStoryError`、既存 bytes 完全一致、staging 不在。
- completion の v2/v3 wiring。
- Lustre 上では親が既に測った `os.link` の前提をそのまま使用し、新しい probe は追加しない。

## 総括

- 推奨プランは receipt file 共通の `_publish_receipt` を作り、submission と completion を staging + `os.link` + identity cleanup に揃えること。
- `os.link(staging, path, follow_symlinks=False)` を使い、`dir_fd` は追加しない。
- 既存 destination は `PaperStoryError("no-replace submission receipt publish failed: File exists")` とし、bytes を一切変更しない。
- staging は成功時も失敗時も `finally` で撤去する。公開後 cleanup failure は完成名を巻き戻さず、専用 subtype で「公開済みだが cleanup 失敗」と報告する。
- P1 は completion receipt も同じ形へ変更するのを推奨。
- P2 は directory staging のため materialize を変更しない。
- P3 は failure receipt の意味と retry policy が別論点なので変更しない。
- 未解決の実装技術事項はない。
- 親が最終確認すべき択一は、公開後 cleanup failure を本案どおり「完成名を保持して非ゼロ報告」とするか、cleanup error を成功扱いで握りつぶすか。本案は前者を推奨し、後者は staging cleanup invariant を静かに破るため採らない。