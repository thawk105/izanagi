以下は基準 `f5677a66` に対する、実装者がそのまま差分化できる粒度のプランです。範囲は code+test の単一実装単位、docs は親が編集する前提です。

### 1. 既定監査の選択集合

`tools/check_ai_provenance.py:1364-1371`

現状:

```python
def _commit_range(rev_range: str | None) -> list[str]:
    if rev_range is None:
        policy = _policy_commit()
        descendants = _git(
            "rev-list", "--reverse", "--ancestry-path", f"{policy}..HEAD"
        ).splitlines()
        return [policy, *descendants]
    return _git("rev-list", "--reverse", rev_range).splitlines()
```

変更後:

```python
def _commit_range(
    rev_range: str | None, *, head: str | None = None,
) -> list[str]:
    if rev_range is None:
        if head is None:
            raise RuntimeError(
                "authoritative history requires a pinned HEAD"
            )
        policy = _policy_commit(head)
        commits = _git(
            "rev-list", "--reverse", f"{policy}..{head}"
        ).splitlines()
        return [policy, *commits]
    return _git("rev-list", "--reverse", rev_range).splitlines()
```

`--ancestry-path` を削除し、`policy..H` の plain range を使う。`--reverse` と policy 自身の前置は維持する。

`tools/check_ai_provenance.py:4-5` の docstring も、必要なら次へ更新する。

```text
既定では docs/ai-provenance.md の一意な追加 commit と、起動時に固定した HEAD へ到達する
その後の commit を検査する。
```

### 2. epoch 適用の authoritative 配線

`tools/check_ai_provenance.py:1170-1184`

現状は epoch resolver が暗黙の `HEAD` を使う。

```python
def _scope_policy_commit() -> str | None:
    commits = _git(
        "log", "--reverse", "--format=%H", "-S", "scope=", "--", POLICY_PATH
    ).splitlines()
```

変更後:

```python
def _scope_policy_commit(head: str | None = None) -> str | None:
    tip = head or "HEAD"
    commits = _git(
        "log", "--reverse", "--format=%H", "-S", "scope=",
        tip, "--", POLICY_PATH,
    ).splitlines()
    return commits[0] if commits else None


def _implementation_policy_commit(
    head: str | None = None,
) -> str | None:
    tip = head or "HEAD"
    commits = _git(
        "log", "--reverse", "--format=%H", "-S",
        IMPLEMENTATION_POLICY_NEEDLE, tip, "--", POLICY_PATH,
    ).splitlines()
    return commits[0] if commits else None
```

`tools/check_ai_provenance.py:1457-1523`

現状:

```python
def _normal_commit_audit(
    commit: str,
    *,
    scope_epoch: str | None,
    implementation_epoch: str | None,
    ancestry: _Ancestry | None = None,
) -> CommitAudit:
```

```python
and descends(scope_epoch)
```

```python
and descends(implementation_epoch)
```

変更後:

```python
def _normal_commit_audit(
    commit: str,
    *,
    scope_epoch: str | None,
    implementation_epoch: str | None,
    ancestry: _Ancestry | None = None,
    authoritative: bool = False,
) -> CommitAudit:
```

`descends` を双方向判定へ拡張し、適用式を共通化する。

```python
def is_descendant(ancestor: str, descendant: str) -> bool:
    if ancestry is None:
        return _is_descendant(ancestor, descendant)
    return ancestry.is_descendant(ancestor, descendant)


def applies_epoch(epoch: str | None) -> bool:
    if epoch is None:
        return False
    return (
        is_descendant(epoch, commit)
        or (
            authoritative
            and not is_descendant(commit, epoch)
        )
    )
```

そのうえで:

```python
if scoped and applies_epoch(scope_epoch):
    findings.extend(
        NormalFinding(finding, None) for finding in scoped
    )
```

```python
if applies_epoch(implementation_epoch):
    waiver = _waiver_audit(label, message)
    ...
```

第2項は `authoritative=True` のときだけ評価する。明示 `--range` は `False` のままなので、現在の単項 lineage 判定を維持する。

`tools/check_ai_provenance.py:1600-1615`

現状:

```python
def _audit_history(commits: list[str]) -> HistoryAudit:
    ...
    scope_epoch = _scope_policy_commit()
    implementation_epoch = _implementation_policy_commit()
    ancestry = _build_ancestry(commits)
```

変更後:

```python
def _audit_history(
    commits: list[str],
    *,
    authoritative: bool = False,
    head: str | None = None,
) -> HistoryAudit:
    ...
    if authoritative and head is None:
        raise RuntimeError(
            "authoritative history requires a pinned HEAD"
        )
    scope_epoch = _scope_policy_commit(head if authoritative else None)
    implementation_epoch = _implementation_policy_commit(
        head if authoritative else None
    )
    ancestry = _build_ancestry(
        commits,
        authoritative=authoritative,
        head=head,
    )
```

呼び出し側へ:

```python
return _normal_commit_audit(
    commit,
    scope_epoch=scope_epoch,
    implementation_epoch=implementation_epoch,
    ancestry=ancestry,
    authoritative=authoritative,
)
```

`tools/check_ai_provenance.py:1576-1593` の `_ledger_policy_is_visible` も同じ式へ合わせる。これは受理条件ではなく stale の理由判定だが、`333605d6` の implementation epoch が lineage 外にあるため、既定監査で `policy-epoch-not-visible` と誤診しないために必要である。

```python
def _ledger_policy_is_visible(
    spec: KnownViolationSpec,
    *,
    implementation_epoch: str | None,
    ancestry: _Ancestry,
    authoritative: bool = False,
) -> bool:
```

```python
return (
    implementation_epoch is not None
    and (
        ancestry.is_descendant(
            implementation_epoch, spec.commit
        )
        or (
            authoritative
            and not ancestry.is_descendant(
                spec.commit, implementation_epoch
            )
        )
    )
)
```

`_known_violation_audit` にも `authoritative: bool = False` を追加し、1720-1724 から渡す。

### 3. CAB seed 集合の bitset

`tools/check_ai_provenance.py:1390-1410`

現状:

```python
class _Ancestry:
    index: dict[str, int]
    bits: tuple[int, ...]
    cab_policy_mask: int

    def has_cab_policy(self, commit: str) -> bool:
        i = self.index.get(commit)
        return False if i is None else bool(
            self.bits[i] & self.cab_policy_mask
        )
```

変更後:

```python
class _Ancestry:
    index: dict[str, int]
    bits: tuple[int, ...]
    cab_policy_mask: int
    cab_policy_ancestor_mask: int = 0

    def has_cab_policy(
        self,
        commit: str,
        *,
        authoritative: bool = False,
    ) -> bool:
        i = self.index.get(commit)
        if i is None or not self.cab_policy_mask:
            return False

        lineage = bool(self.bits[i] & self.cab_policy_mask)
        if lineage:
            return True

        return (
            authoritative
            and not bool(self.cab_policy_ancestor_mask & (1 << i))
        )
```

`cab_policy_mask` は seed 自身の union、`cab_policy_ancestor_mask` は全 seed の祖先集合の union とする。

`tools/check_ai_provenance.py:1413-1446`

現状:

```python
def _build_ancestry(commits: list[str]) -> _Ancestry:
```

```python
policy_hits = _git(
    "log", "--full-history", "--no-renames", "--format=%H",
    "-S", CO_AUTHORED_BY_POLICY_NEEDLE, *commits, "--", POLICY_PATH,
).splitlines()

mask = 0
for sha in policy_hits:
    j = index.get(sha)
    if j is not None:
        mask |= 1 << j
return _Ancestry(index, tuple(bits), mask)
```

変更後:

```python
def _build_ancestry(
    commits: list[str],
    *,
    authoritative: bool = False,
    head: str | None = None,
) -> _Ancestry:
    if authoritative and head is None:
        raise RuntimeError(
            "authoritative ancestry requires a pinned HEAD"
        )

    tips = [head] if authoritative else commits
    ...
    policy_hits = _git(
        "log", "--full-history", "--no-renames", "--format=%H",
        "-S", CO_AUTHORED_BY_POLICY_NEEDLE,
        *tips, "--", POLICY_PATH,
    ).splitlines()

    seed_mask = 0
    seed_ancestor_mask = 0
    for sha in policy_hits:
        j = index.get(sha)
        if j is None:
            continue
        seed_mask |= 1 << j
        seed_ancestor_mask |= bits[j]

    return _Ancestry(
        index,
        tuple(bits),
        seed_mask,
        seed_ancestor_mask,
    )
```

`bits[j]` は seed `j` 自身を含む祖先集合なので、`bits[j]` の union が「commit がどの seed の祖先でもない」の反対条件になる。単一 root を作らず、複数 seed を保持する。

`_normal_commit_audit` の CAB 判定は:

```python
cab_policy_applies = ancestry.has_cab_policy(
    commit,
    authoritative=authoritative,
)
```

`ancestry is None` の逐次 oracle では、`authoritative=False` の既存経路を維持する。authoritative oracle も必要なら、`_has_co_authored_by_policy` を hit 集合返却 helper に分け、次を独立計算する。

```python
any(_is_descendant(seed, commit) for seed in seeds)
or not any(_is_descendant(commit, seed) for seed in seeds)
```

### 4. HEAD の一回解決と drift

`tools/check_ai_provenance.py:1352` 付近へ追加:

```python
def _resolve_head() -> str:
    head = _git("rev-parse", "HEAD").strip()
    if re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", head) is None:
        raise RuntimeError(f"git rev-parse HEAD returned invalid SHA: {head!r}")
    return head


def _assert_head_unchanged(start_head: str) -> None:
    end_head = _git("rev-parse", "HEAD").strip()
    if end_head != start_head:
        raise RuntimeError(
            "HEAD が監査中に変化した: "
            f"start={start_head}, end={end_head}"
        )
```

`tools/check_ai_provenance.py:2611-2618`

現状:

```python
else:
    commits = _commit_range(args.rev_range)
    history = _audit_history(commits)
```

変更後:

```python
else:
    authoritative = args.rev_range is None
    head = _resolve_head() if authoritative else None

    if authoritative:
        _assert_authoritative_repository()

    commits = _commit_range(args.rev_range, head=head)
    history = _audit_history(
        commits,
        authoritative=authoritative,
        head=head,
    )

    if authoritative:
        _assert_head_unchanged(head)
```

この全体を既存の `try` 内に置く。drift・stale・repository guard は findings 出力より前に例外化するため、rc=2 が rc=1 より優先される。

`--range` では `authoritative=False`、`--message-file` ではこの分岐自体を通らない。したがって両経路では HEAD 解決、drift 検査、repository guard を新たに実行しない。

### 5. shallow / graft / replace / policy add

`tools/check_ai_provenance.py:2611` の既定経路から呼ぶ新規 helper:

```python
def _assert_authoritative_repository() -> None:
    shallow = _git(
        "rev-parse", "--is-shallow-repository"
    ).strip()
    if shallow != "false":
        raise RuntimeError(
            "authoritative history is unavailable in a shallow repository"
        )

    grafts = Path(
        _git("rev-parse", "--git-path", "info/grafts").strip()
    )
    if not grafts.is_absolute():
        grafts = REPO / grafts
    try:
        graft_bytes = grafts.read_bytes()
    except FileNotFoundError:
        graft_bytes = b""
    if graft_bytes.strip():
        raise RuntimeError(
            f"authoritative history is unavailable with grafts: {grafts}"
        )

    replacements = _git("replace", "--list").splitlines()
    if replacements:
        raise RuntimeError(
            "authoritative history is unavailable with git replace"
        )
```

検出コマンドは次のとおり。

- shallow: `git rev-parse --is-shallow-repository` が `true` なら rc=2。
- graft: `git rev-parse --git-path info/grafts` で得たファイルの非空内容を rc=2。空ファイルは graft 無しとして扱う。
- replace: `git replace --list` の 1 行以上を rc=2。

`tools/check_ai_provenance.py:1352-1361`

現状は path add の最後を無条件採用する。

```python
commits = _git(
    "log", "--diff-filter=A", "--format=%H", "--", POLICY_PATH
).splitlines()
...
return commits[-1]
```

変更後:

```python
def _policy_commit(head: str | None = None) -> str:
    tip = head or "HEAD"
    commits = _git(
        "log", "--full-history", "--no-renames",
        "--diff-filter=A", "--format=%H",
        tip, "--", POLICY_PATH,
    ).splitlines()

    if not commits:
        raise RuntimeError(
            f"{POLICY_PATH} の導入 commit が履歴にない。"
            "commit 前は --message-file で検査すること"
        )
    if len(commits) != 1:
        raise RuntimeError(
            f"{POLICY_PATH} の導入 commit が一意でない: "
            f"hits={len(commits)}"
        )
    return commits[0]
```

非一意検査は `_commit_range(None)` からのみ到達するため、明示 `--range` は変わらない。

注意点として、brief の「`_policy_commit()` の `-S` hit 数チェック」は現ソースと一致していない。現状の `_policy_commit()` は `-S` ではなく `--diff-filter=A` を使い、`-S` は scope、implementation、CAB の seed 検出に使われている。policy add の一意性を検査する正しい plumbing は上記の `--diff-filter=A` hit 数である。literal な `-S` を要求する場合は、何を needle とするかが未確定であり、親裁定が必要になる。path add を意味するなら `--diff-filter=A` を採用する。

### 6. 既知違反台帳

`tools/check_ai_provenance.py:630-636`

現状の tuple 終端:

```python
KnownViolationSpec(
    "3df9b0aa379f84500e3f59add9ad76e421019d50",
    MISSING_CODEX_AUTHOR,
    _T1140_T330_MERGE_RULING,
    note=_T1140_T330_NOTE,
),
)
```

変更後:

```python
KnownViolationSpec(
    "3df9b0aa379f84500e3f59add9ad76e421019d50",
    MISSING_CODEX_AUTHOR,
    _T1140_T330_MERGE_RULING,
    note=_T1140_T330_NOTE,
),
KnownViolationSpec(
    "333605d680ec15f3f74b00e9e2746ae317b85dc5",
    MISSING_CODEX_AUTHOR,
    "worklog(299) 2026-08-07 /rulings",
),
)
```

`MISSING_CODEX_AUTHOR` は `_NOTE_REQUIRED_FINDING_KINDS` に含まれず、note は不要。`note=""` の dataclass default を使う。対象 commit の実 finding は `output/insights/2026-07-28_t142-review-verbatim/count_abort_reasons.py` と `count_frontier.py` に対する Codex author 欠落。

### 7. 契約文書

`docs/ai-provenance.md:6-7`

現状:

```text
本規約は導入 commit 自身と以後の commit に
適用し、既存履歴を書き換えない。
```

変更後:

```text
既定監査は各規則の内容検出 commit 自身と、その祖先でない HEAD 到達 commit に適用する。導入祖先は legacy とし、履歴を書き換えない。
```

`docs/ai-provenance.md:17`

現状:

```text
この規則は内容検出した導入 commit 以後へ適用する (F25)。
```

変更後は削除する。前後は次の 1 文だけにする。

```text
checker は raw 候補行数と隔離 Git parser の認識数を照合し、一致しなければ拒否する。
```

`docs/ai-provenance.md:29-31`

現状末尾:

```text
導入 commit 以降にのみ適用して遡及せず、
  checker も内容検出した導入 commit 以後だけ検査する。
```

変更後は削除する。scope の段落は次で終わる。

```text
- `scope` (任意、2026-07-17 導入): その構成が担った作業範囲の短い識別子。**同じ role が複数行に
  わたる commit では全行に必須**、単独行は省略可。
```

`docs/ai-provenance.md:48`

現状:

```text
本節を導入する commit 以後、実装面を変更する AI 関与 commit は Codex author を必須とする。
```

変更後:

```text
実装面を変更する AI 関与 commit は Codex author を必須とする。
```

byte 計測は次のとおり。

- 削除対象: `104 + 77 + 129 + 38 = 348B`
- 挿入文: `180B`
- `docs/ai-provenance.md`: `6270B → 6102B`
- family 現在 `8977B → 8809B`
- `PR-A02` 案を含めても family は約 `8869B` で 9000B 未満

`IMPLEMENTATION_POLICY_NEEDLE` と `CO_AUTHORED_BY_POLICY_NEEDLE` の実本文出現数は、編集前後とも各 1 件に固定する。

`docs/provenance/audit.md:15-16`

現状:

```text
導入 commit から `HEAD` までの欠落、排他違反、フィールド順、値と role の形式を検査する。別範囲は
`--range <range>`。導入前の欠落は legacy とし遡及違反にしない。correction 範囲の権威は `PR-C03`。
```

変更案:

```text
既定監査は各規則の内容検出 commit 自身と、その祖先でない HEAD 到達 commit の欠落、排他違反、フィールド順、値と role の形式を検査する。別範囲は
`--range <range>`。導入祖先は legacy とし遡及違反にしない。correction 範囲の権威は `PR-C03`。
```

`tools/check_docs.py` に対する grep の結果、個別の非遡及文言や両 needle の exact-pin は存在しない。該当する検査は次の全て。

- `tools/check_docs.py:54-59`: provenance 文書の列挙。
- `tools/check_docs.py:194-218`: entry 6300B、reference 各1600B、family 9000B、PR-A01/A02/A03 の節 registry。
- `tools/check_docs.py:4890-4926`: `docs/provenance/**` の追加・欠落・symlink 検査。
- `tools/check_docs.py:4942-4979`: UTF-8 読取、byte 上限、行長検査。
- `tools/check_docs.py:4982-4991`: family byte ceiling。
- `tools/check_docs.py:5021-5031`: provenance Markdown の曖昧構文検査。
- `tools/check_docs.py:5164-5184`: PR-A01/A02/A03 の一意 H2 と孤児節検査。
- `tools/check_docs.py:5186-5235`: budget、section、dispatch の path 閉包と ownership 検査。
- `tools/check_docs.py:5238-5310`: `docs/ai-provenance.md` の条件 dispatch 表 header、3列、row count、condition、reference path の構造検査。

`tools/check_docs.py` 自体の変更は不要。

### 8. テスト計画

`orchestrator/tests/test_check_ai_provenance.py:724` 直後に新設:

```text
test_default_commit_range_uses_plain_reachability_and_policy_prefix
```

policy 導入前に分岐し、後で merge された side commit を作り、

```python
expected = _git(
    tmp_path, "rev-list", "--reverse", f"{policy}..{head}"
).splitlines()
assert provenance._commit_range(
    None, head=head
) == [policy, *expected]
```

を固定する。旧 `--ancestry-path` では side commit が欠落する構造にする。

`orchestrator/tests/test_check_ai_provenance.py:724` 近傍に新設:

```text
test_authoritative_epoch_predicate_covers_merged_side_branch
```

epoch 導入 commit の sibling branch に、scope 無しの複数 role と Codex author 欠落を持つ `tools/side.py` commit を作る。

- `authoritative=True`: scope finding と `missing-codex-author` が出る。
- `authoritative=False`: 同じ selected set でも両 finding が出ない。

これが第2項の有効範囲を pin する。

`orchestrator/tests/test_check_ai_provenance.py:868` 近傍に新設:

```text
test_authoritative_cab_predicate_covers_merged_side_branch
```

CAB seed 導入前に分岐した side commit を後で mergeし、既定監査では split CAB を検出、明示 `--range` では従来どおり検出しないことを固定する。

`orchestrator/tests/test_check_ai_provenance.py:5693-5780`

既存の次を拡張する。

- `test_ancestry_bitset_matches_merge_base_oracle_for_every_pair`: `is_descendant` の既存等価性を維持。
- `test_ancestry_pickaxe_mask_matches_per_commit_oracle`: lineage 判定に加え、独立 oracle で次を比較する。

```python
expected = bool(seeds) and (
    any(provenance._is_descendant(seed, commit) for seed in seeds)
    or not any(
        provenance._is_descendant(commit, seed)
        for seed in seeds
    )
)
assert ancestry.has_cab_policy(
    commit, authoritative=True
) is expected
```

`orchestrator/tests/test_check_ai_provenance.py:5606-5626`

`_build_ancestry` の monkeypatch を kwargs 対応にする。

```python
lambda selected, **kwargs: None
```

新しい `authoritative` / `head` の伝播を壊さないための変更である。

`orchestrator/tests/test_check_ai_provenance.py:724-1058, 785-899`

既存の `--range` テストは、scope/implementation/CAB の第2項が無効なまま通る回帰として保持する。

- `test_history_gate_starts_at_policy_epoch_and_rejects_followup`
- `test_cab_explicit_ranges_accept_pre_policy_and_reject_post_policy`
- `test_cab_policy_is_detected_on_range_from_separate_lineage`
- `test_cab_policy_git_error_fails_closed_with_rc2`

`orchestrator/tests/test_check_ai_provenance.py:1035` 近傍に新設:

```text
test_authoritative_repository_rejects_shallow_graft_and_replace
test_authoritative_repository_rejects_nonunique_policy_add
```

それぞれ以下を作り、既定監査が rc=2 になることを確認する。

- `git clone --depth=1` 相当の shallow repository。
- `git rev-parse --git-path info/grafts` の指すファイルに graft 行。
- `git replace <old> <new>` 後の `git replace --list`。
- `docs/ai-provenance.md` を add、delete、再-add して `--diff-filter=A` hit を2件にする。

`orchestrator/tests/test_check_ai_provenance.py:1062-1325` 近傍に新設:

```text
test_explicit_range_and_message_file_skip_authoritative_repository_guards
```

`_resolve_head` と `_assert_authoritative_repository` を fail-fast monkeypatch し、次を確認する。

- `--range` は既存の rc/output のまま。
- `--message-file` は既存の rc/output のまま。
- どちらも guard を呼ばない。

`orchestrator/tests/test_check_ai_provenance.py:3021-3039, 5824-5844`

forward correction の既存 explicit-range / merge-base テストを維持する。既定監査では selected set 拡大により candidate が増えて rc=1 へ strict 化し得るため、「default でも不変」という期待は置かない。

`orchestrator/tests/test_check_ai_provenance.py:1329-1504`

`test_known_violation_ledger_matches_literal_entries` を 42 entry から 43 entry へ更新し、次を exact-pin する。

```python
(
    "333605d680ec15f3f74b00e9e2746ae317b85dc5",
    "missing-codex-author",
    "worklog(299) 2026-08-07 /rulings",
    "",
    "",
)
```

`orchestrator/tests/test_check_ai_provenance.py:1507` 近傍に新設:

```text
test_t619_known_violation_is_absorbed_in_authoritative_audit
```

実 repo の `333605d6` を `authoritative=True`、固定 `head` で `_audit_history` に渡し、finding が `missing-codex-author` として発生し、台帳 entry にだけ吸収されることを pin する。

`orchestrator/tests/test_check_ai_provenance.py:3813-3829` の policy anchor test を拡張する。

```python
NONRETROACTIVE = (
    "既定監査は各規則の内容検出 commit 自身と、その祖先でない "
    "HEAD 到達 commit に適用する。導入祖先は legacy とし、履歴を書き換えない。"
)
assert entry.count(NONRETROACTIVE) == 1
assert len(entry.encode("utf-8")) == 6102
assert entry.count(provenance.IMPLEMENTATION_POLICY_NEEDLE) == 1
assert entry.count(provenance.CO_AUTHORED_BY_POLICY_NEEDLE) == 1
```

旧4文が残っていないことも exact に確認する。

`orchestrator/tests/test_check_ai_provenance.py:3845-3849`

`test_implementation_policy_epoch_is_pinned_in_this_repo` は、needle の出現回数が不変で epoch SHA が変わらない positive control として維持する。

## 総括

既定経路だけを `H` 固定の plain reachability + seed 集合述語へ変更し、明示 `--range` と `--message-file` は現状維持する。実装上の未確定点は、brief にある「policy add の `-S` hit」が現ソースの `--diff-filter=A` と食い違う点だけで、policy add の意味なら `--diff-filter=A` hit 数検査を採用する。