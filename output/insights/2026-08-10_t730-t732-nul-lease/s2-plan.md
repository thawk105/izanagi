指定された brief と probe、直前 T-714 の実装・テスト、現行 §7.3、caller 閉包を読みました。以下は静的検査に基づく段 2 プランです。実装・テスト・`check_docs.py` は実走していません。

変更対象はコード／テスト 4 ファイルと docs 1 ファイルだけです。reason code は既存の `path-control-char` / `contract-path-control-char` を再利用します。

## [T-730] 実装 hunk

### H1: 契約 loader の NUL 拒否

[s8c_preregistration_evidence.py:183–190](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t730-t732-nul-lease-merge/orchestrator/campaign/s8c_preregistration_evidence.py:183)

現行の CR/LF guard に NUL の disjunct だけを足す。`_nonempty_string` より前という順序は変えない。

```python
def _safe_path(value: object, *, where: str) -> str:
    if isinstance(value, str) and ("\x00" in value or "\r" in value or "\n" in value):
        raise EvidenceContractError("contract-path-control-char", repr(where))
    path = _nonempty_string(value, where=where)
    pure = PurePosixPath(path)
    if pure.is_absolute() or ".." in pure.parts or path != pure.as_posix():
        raise EvidenceContractError("contract-path", where)
    return path
```

NUL と別の不正条件を併せ持つ文字列は reason の優先順位が `contract-path-control-char` に変わりうるが、NUL なし入力の判定順・reason は不変。

### H2: blob primitive の NUL 拒否

[s8c_preregistration.py:960–970](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t730-t732-nul-lease-merge/orchestrator/campaign/s8c_preregistration.py:960)

D267 の exact `str` 固定後の `text` に対し、同じ一行 guardへ NULだけを追加する。

```python
def read_blob_at(
    repo_root: Path | str, commit: str, path: str, *, required: bool = True
) -> Optional[bytes]:
    rendered = path if isinstance(path, str) else str(path)
    text = "".join((rendered,))
    if "\x00" in text or "\r" in text or "\n" in text:
        raise PreregistrationError("path-control-char")
    root = Path(repo_root).resolve()
    resolved = resolve_commit(root, commit)
    spec = f"{resolved}:{text}"
```

`rendered` / `text` の二段階、文字列化 1 回、例外へ生 path を入れない契約は維持する。

## [T-730] テスト hunk

### H3: 旧経路の NUL alias を先に立証するテスト

[test_s8c_preregistration_core.py:1010](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t730-t732-nul-lease-merge/orchestrator/tests/test_s8c_preregistration_core.py:1010) の、末尾 CR テスト直後かつ既存 CR/LF parameterization の前へ新設する。

```python
@pytest.mark.parametrize(
    "suffix",
    [
        pytest.param("\x00", id="trailing-nul"),
        pytest.param("\x00not-the-contract-path", id="embedded-nul"),
    ],
)
def test_read_blob_at_rejects_nul_alias(tmp_path: Path, suffix: str) -> None:
    root = _init_repo(tmp_path)
    prefix_path = "alias-target.txt"
    prefix_blob = b"nul-prefix-blob\n"
    _write(root, prefix_path, prefix_blob)
    head = _commit(root, "NUL alias fixture")
    candidate = prefix_path + suffix

    _assert_tree_blob(root, head, prefix_path, prefix_blob)
    assert candidate != prefix_path
    assert candidate == candidate.strip()
    assert _legacy_unframed_blob(root, head, candidate) == prefix_blob
    with pytest.raises(M.PreregistrationError) as caught:
        M.read_blob_at(root, head, candidate)
    assert caught.value.reason == "path-control-char"
    assert str(caught.value) == "path-control-char"
```

fixture の構造は次のとおり。

- POSIX/Git tree に NUL を含む名前は作れないため、`candidate` 自体のファイルは作らない。
- NUL 前の `alias-target.txt` だけを実在する blob として commit し、`_assert_tree_blob` で確認する。
- guard 導入前を再現する `_legacy_unframed_blob` に NUL 入り要求文字列を渡し、実在する prefix blob が返ることを先に assert する。
- その後にだけ `read_blob_at` の拒否を assert する。

したがって、CR/LF テストの「NUL を含む intended filename の実在」までは再現できないが、問題の本体である「契約上は異なる文字列なのに旧 Git 要求が prefix blob を返す」は同じ順序で立証できる。

### H4: `_safe_path` の埋め込み NUL

[test_s8c_preregistration_predicates.py:182–206](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t730-t732-nul-lease-merge/orchestrator/tests/test_s8c_preregistration_predicates.py:182) を次の形にする。

```python
@pytest.mark.parametrize(
    ("owner", "control"),
    [
        pytest.param("required", "\r", id="required-cr"),
        pytest.param("required", "\n", id="required-lf"),
        pytest.param("required", "\x00", id="required-nul"),
        pytest.param("consumer", "\r", id="consumer-cr"),
        pytest.param("consumer", "\n", id="consumer-lf"),
        pytest.param("consumer", "\x00", id="consumer-nul"),
    ],
)
def test_contract_loader_rejects_embedded_path_control_chars(
    owner: str, control: str
) -> None:
    value = json.loads(CONTRACT_FILE.read_bytes())
    candidate = f"dir/in{control}side.py"
    assert candidate == candidate.strip()
    if owner == "required":
        value["conditions"][0]["required_evidence"][0]["path"] = candidate
    else:
        value["conditions"][0]["consumer_requirement"]["path"] = candidate

    with pytest.raises(M.EvidenceContractError) as caught:
        M.load_contract_bytes(json.dumps(value, ensure_ascii=False).encode("utf-8"))
    assert caught.value.reason_code == "contract-path-control-char"
    assert "\x00" not in str(caught.value)
    assert "\r" not in str(caught.value)
    assert "\n" not in str(caught.value)
```

JSON fixture は `json.dumps` 上では NUL が `\u0000` として符号化され、`json.loads` 後の path 値では実 NUL に戻る。POSIX ファイルは不要。

### H5: `_safe_path` の末尾 NUL

同ファイル [209–227 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t730-t732-nul-lease-merge/orchestrator/tests/test_s8c_preregistration_predicates.py:209) を次の形にする。

```python
@pytest.mark.parametrize(
    "control",
    [
        pytest.param("\r", id="trailing-cr"),
        pytest.param("\n", id="trailing-lf"),
        pytest.param("\x00", id="trailing-nul"),
    ],
)
def test_contract_loader_reports_explicit_path_reason_for_trailing_controls(
    control: str,
) -> None:
    value = json.loads(CONTRACT_FILE.read_bytes())
    current = value["conditions"][0]["required_evidence"][0]["path"]
    value["conditions"][0]["required_evidence"][0]["path"] = current + control

    with pytest.raises(M.EvidenceContractError) as caught:
        M.load_contract_bytes(json.dumps(value, ensure_ascii=False).encode("utf-8"))
    assert caught.value.reason_code == "contract-path-control-char"
    assert "\x00" not in str(caught.value)
    assert "\r" not in str(caught.value)
    assert "\n" not in str(caught.value)
```

### H6: C0 一般拒否を殺す正例

同ファイルの現行 [240 行直後](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t730-t732-nul-lease-merge/orchestrator/tests/test_s8c_preregistration_predicates.py:240) へ新設する。TAB は POSIX/Git filename に実在できるため、一つの node で `_safe_path` と `read_blob_at` の両層を通す。

```python
def test_contract_and_blob_guards_accept_embedded_tab_path(tmp_path: Path) -> None:
    value = json.loads(CONTRACT_FILE.read_bytes())
    candidate = "nested/tab\tpath.py"
    payload = b"embedded-tab-path\n"
    value["conditions"][0]["required_evidence"][0]["path"] = candidate
    raw = json.dumps(value, ensure_ascii=False).encode("utf-8")

    contract = M.load_contract_bytes(raw)
    assert contract.conditions[0].required_evidence[0].path == candidate

    root = _init_repo(tmp_path)
    _write(root, core.EVIDENCE_CONTRACT_PATH, raw)
    _write(root, candidate, payload)
    head = _commit(root, "embedded TAB path")
    assert core.read_blob_at(root, head, candidate) == payload
```

これにより「C0 全般」「空白全般」「`ord(ch) < 0x20`」への過剰一般化は、拒否テストが増えただけでは見逃す問題を正例で検出できる。

## 既存テストへの影響

現行の対象 2 test file に NUL path の既存正例はないため、既存期待値の反転・削除は不要。変更するのは上記の新規 parameter node と正例だけである。

静的に changed line を通る既存テスト群は次のとおり。

- `test_s8c_preregistration_core.py`

  - `test_read_blob_at_accepts_normal_path`
  - `test_read_blob_at_rejects_trailing_cr_without_aliasing`
  - `test_read_blob_at_rejects_embedded_path_control_chars[embedded-cr]`
  - `test_read_blob_at_rejects_embedded_path_control_chars[embedded-lf]`
  - `test_read_blob_at_rejects_standalone_embedded_cr_as_policy`
  - `test_read_blob_at_uses_checked_text_without_str_subclass_format_hook`
  - `test_read_blob_at_rejects_control_chars_after_single_stringification`
  - `test_git_timeout_generation_commit_and_blob_limits_fail_closed`

- `test_s8c_preregistration_predicates.py`

  - 既存 CR/LF loader node 全件
  - `test_contract_loader_accepts_normal_relative_paths`
  - `test_contract_semantic_hash_ignores_formatting_but_not_values`
  - `test_registry_rejects_control_char_contract_before_evidence_ref_construction`
  - canonical contract を読む registry／snapshot／negative-control テスト群

- [test_s8c_preregistration_invariant.py:125](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t730-t732-nul-lease-merge/orchestrator/tests/test_s8c_preregistration_invariant.py:125)

  - `test_candidate_freeze_matches_contract_and_generation_chain`

これらの fixture path はすべて NUL-free なので期待値は現状維持。既存 node が赤になれば、NUL 以外への過剰拒否、exact-string 化の退行、または error precedence の意図しない変更として扱う。

## caller の閉包

次の grep を基準に確認した。

```text
rg -n '\b_safe_path\s*\(' --glob '*.py' .
rg -n '\bread_blob_at\s*\(' --glob '*.py' .
```

`_safe_path` の immediate caller は exact 2 口だけ。

- [s8c_preregistration_evidence.py:225](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t730-t732-nul-lease-merge/orchestrator/campaign/s8c_preregistration_evidence.py:225): `required_evidence[*].path`
- [s8c_preregistration_evidence.py:252](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t730-t732-nul-lease-merge/orchestrator/campaign/s8c_preregistration_evidence.py:252): `consumer_requirement.path`

その transitive caller は `load_contract_bytes`、`semantic_contract_sha256`、`PredicateRegistry.evaluate_all`。したがって契約の検証・意味 hash・registry 評価すべてに上層防壁が届く。

`read_blob_at` の production caller は次の閉包。

- [s8c_preregistration.py:991](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t730-t732-nul-lease-merge/orchestrator/campaign/s8c_preregistration.py:991): `parse_preregistration_at` の `SOURCE_PATH`
- [s8c_preregistration.py:1491](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t730-t732-nul-lease-merge/orchestrator/campaign/s8c_preregistration.py:1491): `_module_blob`。`_activation_report_at` の core/evaluator module 読取へ到達
- [s8c_preregistration.py:1565](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t730-t732-nul-lease-merge/orchestrator/campaign/s8c_preregistration.py:1565): `_activation_report_at` の `SOURCE_PATH`
- [s8c_preregistration.py:1716](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t730-t732-nul-lease-merge/orchestrator/campaign/s8c_preregistration.py:1716): `prepare_revision` の generation record
- [s8c_preregistration_evidence.py:378](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t730-t732-nul-lease-merge/orchestrator/campaign/s8c_preregistration_evidence.py:378): `_ConditionProbe.read_kind` の契約由来 evidence path
- [s8c_preregistration_evidence.py:679](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t730-t732-nul-lease-merge/orchestrator/campaign/s8c_preregistration_evidence.py:679): `PredicateRegistry.evaluate_all` の契約本体
- invariant test の direct call 2 口: 143、154 行

実際に hostile な契約 path が届きうる主経路は `_ConditionProbe.read_kind`。通常は上層 `_safe_path` で先に止まり、手組み dataclass・loader bypass・公開 primitive の直接呼出しは下層 `read_blob_at` が止める。その他は定数生成 path なので、NUL guard の到達対象ではあるが挙動は変わらない。

## 受理集合が NUL だけ縮む根拠

上層の旧 guard を `CR ∨ LF`、新 guard を `NUL ∨ CR ∨ LF` とすると、NUL を含まないすべての入力で真偽は同一。その後の `_nonempty_string` と `PurePosixPath` 検査は無変更。

下層も exact `text` に対する旧 guard が `CR ∨ LF`、新 guard が `NUL ∨ CR ∨ LF` になるだけで、commit 解決・Git spec・blob 検証は無変更。

したがって今までどおり通るのは以下。

- NUL/CR/LF を含まない通常の relative path
- `Path("nested/evidence.txt")` など、文字列化結果が NUL-free の path-like 値
- 埋め込み TAB を含む POSIX path（H6 で固定）
- その他の C0 文字で、既存 validator が別理由で拒否していなかったもの

CR/LF は従来どおり同じ reason で拒否される。NUL を含み、別の既存条件でも拒否されていた入力は reason の優先順位だけ変わりうるが、NUL-free 入力の受理・拒否・reason は変わらない。

## 変異検査の事前登録候補

| 変異 | 単独変異の逐語 | 赤になるべき nodeid |
|---|---|---|
| M-NUL-SAFE | `_safe_path` の条件を旧 `("\r" in value or "\n" in value)` に戻す | `orchestrator/tests/test_s8c_preregistration_predicates.py::test_contract_loader_rejects_embedded_path_control_chars[required-nul]` |
| M-NUL-BLOB | `read_blob_at` の条件を旧 `"\r" in text or "\n" in text` に戻す | `orchestrator/tests/test_s8c_preregistration_core.py::test_read_blob_at_rejects_nul_alias[embedded-nul]` |
| M-C0-SAFE | `_safe_path` を `isinstance(value, str) and any(ord(ch) < 0x20 for ch in value)` に一般化 | `orchestrator/tests/test_s8c_preregistration_predicates.py::test_contract_and_blob_guards_accept_embedded_tab_path` |
| M-C0-BLOB | `read_blob_at` を `any(ord(ch) < 0x20 for ch in text)` に一般化 | 同じ TAB 正例 nodeid |

M-NUL-BLOB は `[trailing-nul]` も赤になる見込みだが、事前登録上の必須検出 nodeid は `[embedded-nul]` 一つに固定すればよい。

## [T-732] docs hunk

現行 [pegasus-runbook.md:784–793](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t730-t732-nul-lease-merge/docs/pegasus-runbook.md:784) の一つの長い bullet を、次の 2 bullet に全置換する。新節は作らない。

```markdown
- **`acquired` の直後に、待ち手自身が local main を取り直し、受入を投入する前に取り込む。**
  `git rev-list --count HEAD..main` が非 0 なら、`git merge --no-ff --no-commit main` →
  `git commit -F <message-file>` で merge commit を作る (message file は待機前に用意する)。
  `git merge --ff-only main` と `--no-edit` は使わない。merge 後に `HEAD..main` が 0 でなければ
  投入しない。競合時は `git merge --abort` →
  `python3 tools/wave_land_window.py release --wave "$W"` の順に実行し、受入を投入せず親へ戻す。
- **`claim` loop・上の merge・受入投入は同じ待ち手 script に置く。** 取り込みを親の待機前作業にし、
  待ち手を `HEAD..main` の検査だけにすると、待機中に main が進むたび取得した lease を捨てる
  (2026-08-10 実測: 24 分待って `acquired`、15 commit 遅れ)。
```

P2 への補正点は、merge を無条件に commit しないこと。取得後に `HEAD..main == 0` なら main はすでに ancestor なので、`git commit -F` を実行すると `nothing to commit` になる。したがって「非 0 のときだけ merge commit」を明記する。merge 後の再検査も F196 の実測済み待ち手と揃える。

lease の範囲は受入のまま。land まで保持する記述は加えない。

### docs 予算

静的計算では、現行 784–793 行は 10 行・1165 bytes・局所最長 82 文字。上の置換は 9 行・936 bytes・局所最長 82 文字で、差分は以下。

- 行数: `-1`
- bytes: `-229`
- runbook 全体: 68982 → 約 68753 bytes
- 全体最長行: 現行 559 行の 185 文字がそのまま最大で、新規行は最大 82 文字

削る冗長部分は、現行の `Not possible to fast-forward` の長い説明と、2026-08-09 の「12 commit / 1324 秒」逸話。2026-08-10 の独立実測 1 件だけを残す。

なお、現行 `tools/check_docs.py` の `TextLimit` 登録には `docs/pegasus-runbook.md` の file-specific byte／最長行 cap はなく、同ファイルへの機械検査は主に §7.0 の構造である。それでも本案は byte・行数とも縮小するため、予算値や checker は一切変更しない。親の段 4 以降で `tools/check_docs.py` を実走して確認する。

## 総括

- [T-730] は既存 CR/LF guard 2 行へ `\x00` の disjunctだけを追加し、reason code・exact-string 化・検査順を維持する。
- NUL filename は作らず、実在する prefix blob と NUL 入り要求文字列を分け、旧 helper の alias 成立を guard 拒否より先に立証する。
- 埋め込み TAB の実ファイルを両層へ通す正例で、裁定外の C0 一般拒否を検出する。
- [T-732] は現行 §7.3 がすでに基本裁定を含むため、784–793 行だけを具体コマンド・競合順序・同一待ち手 script 契約へ精密化する。
- 残る不確実性はテスト未実走であること。probe の NUL alias 実測は一次資料として読んだが、この read-only 段 2 では再実走していない。
- 親が段 4 で裁定すべき点は、(1) 既存 reason code 再利用、(2) `HEAD..main != 0` の場合だけ merge commit を作る補正、(3) 一つの TAB 正例で両層の過剰一般化変異を殺す構成、(4) T-732 を docs-only に保ち executable waiter の新設へ scope 拡大しないこと。いずれも採用を推奨する。