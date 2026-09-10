## 総括

- P1 は `_session_meta_rows()` を一度だけ呼び、二つの状態を 1 パスで最後まで評価する。helper は追加しない。
- 既存テストで赤になるのは、10 variant 中 `distinct-fields` を含むテスト関数 1 本だけである。
- 型 A、型 B、子 ID の非退行、真の重複拒否を pin 無しの 3 テスト関数で固定する。
- pin fast path、SHA 照合、pin 無し全走査、件数非 1 の `RC_SESSION` は構造を変えない。
- base `ab3feb0443a2` を静的に確認した。pytest は実行せず、ファイルも変更していない。

## 判定式の実装形

対象は [tools/codex_reasoning_ab.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t936-rollout-identity/tools/codex_reasoning_ab.py:283) の現行 `:283-292`。

before:

```python
def _rollout_matches_session(path: Path, session_id: str) -> bool:
    for row in _session_meta_rows(path):
        if row.get("type") != "session_meta":
            continue
        payload = row.get("payload")
        if not isinstance(payload, dict):
            continue
        if payload.get("id") == session_id or payload.get("session_id") == session_id:
            return True
    return False
```

after:

```python
def _rollout_matches_session(
    path: Path, target_session_id: str
) -> bool:
    has_target_identity = False
    has_descendant_reference = False
    for row in _session_meta_rows(path):
        if row.get("type") != "session_meta":
            continue
        payload = row.get("payload")
        if not isinstance(payload, dict):
            continue

        root_session_id = payload.get("session_id")
        payload_id = payload.get("id")
        own_session_id = (
            payload_id if isinstance(payload_id, str) else root_session_id
        )

        if own_session_id == target_session_id:
            has_target_identity = True
        if (
            own_session_id != target_session_id
            and root_session_id == target_session_id
        ):
            has_descendant_reference = True

    return has_target_identity and not has_descendant_reference
```

実装判断:

- helper は追加しない。`own` の導出はこの述語だけで使われ、局所変数で十分である。
- `_session_meta_rows` `:232-252` は変更しない。
- 1 パスを採る。返却値は既に materialize 済みの list なので、2 パスでも file 再読は起きない。一方、1 パスなら `own` を各行で一度だけ導出し、二つの存在条件を同じ場所で固定できる。
- 途中 return は行わない。後続行に子孫宣言がある可能性を残し、行順に依存させない。
- 新述語が真なら、ある行で `id == target` または fallback 後の `session_id == target` が成立する。したがって file・target の組について `M_new(F, X) ⇒ M_old(F, X)` となり、候補 file の受理集合は現行の真部分集合になる。
- `_find_rollout(P)` が旧 `RC_SESSION` から成功へ変わるのは、旧一致集合から誤った子 file を削るためであり、旧述語が拒否した file を新規受理する変更ではない。

`_find_rollout` `:295-341` は P4 の局所改名だけを行う。

| 現行行 | before | after |
|---|---|---|
| `:297` | `session_id: str` | `target_session_id: str` |
| `:303` | `SESSION_IDS.get(pinned_label) == session_id` | `... == target_session_id` |
| `:311` | `separator in session_id` | `separator in target_session_id` |
| `:312` | `glob.escape(session_id)` | `glob.escape(target_session_id)` |
| `:322` | `_rollout_matches_session(candidate, session_id)` | `_rollout_matches_session(candidate, target_session_id)` |
| `:334` | `_rollout_matches_session(path, session_id)` | `_rollout_matches_session(path, target_session_id)` |
| `:338` | error 文中の `{session_id}` | `{target_session_id}` |

次は変更しない。

- `:301-330` の `eligible` fast path
- `:332-335` の `rglob("rollout-*.jsonl")` 全走査
- `:336-340` の件数検査と `RC_SESSION`
- `:344-350` の `_verify_rollout_sha`
- `:3067-3125` の消費側。特に `:3090-3091` の複数 meta 拒否は T-937 のまま残す

## 既存テストへの影響

対象は [orchestrator/tests/test_codex_reasoning_ab.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t936-rollout-identity/orchestrator/tests/test_codex_reasoning_ab.py:1978)。

### 10 variant の全判定

現行は pytest parameter ではなく関数内ループなので、収集されるテストは 1 nodeid である。その関数が最後の `distinct-fields` で赤になる。

| variant | P1 の判定 | 分類 |
|---|---|---|
| `literal` | `id == session_id == target` で受理 | 無関係なので触らない |
| `unicode-escape` | `id` で受理 | 無関係なので触らない |
| `utf16-le` | own が target | 無関係なので触らない |
| `utf16-be` | own が target | 無関係なので触らない |
| `utf32-le` | own が target | 無関係なので触らない |
| `utf32-be` | own が target | 無関係なので触らない |
| `reordered-keys` | `session_id` fallback で受理 | 無関係なので触らない |
| `id-only` | `id` で受理 | 無関係なので触らない |
| `session-id-only` | P3 の fallback で受理 | 無関係なので触らない |
| `distinct-fields` | own は `other`、target は親参照なので拒否 | バグの仕様固定なので期待を反転 |

`test_find_rollout_session_meta_encoding_and_payload_field_equivalence` `:1978-2017` は、意味が equivalence ではなくなるため `test_find_rollout_session_meta_encoding_and_payload_identity_semantics` へ改名する。repo 内に旧名の参照はない。

各 variant に `should_match` を持たせ、`distinct-fields` だけ次を期待する。

```python
with pytest.raises(TOOL.ValidationError) as excinfo:
    TOOL._find_rollout(sessions_root, session_id)
assert excinfo.value.rc == TOOL.RC_SESSION
assert str(excinfo.value) == (
    "session target-session rollout count is 0, expected 1"
)
```

### 残る `_find_rollout` テスト

以下はすべて「無関係なので触らない」。P1 による期待変更はない。

- `:2020` `test_find_rollout_checks_later_session_meta_in_same_file`
- `:2030` `test_find_rollout_preserves_zero_and_duplicate_failure` の 0/2 件
- `:2049` `test_find_rollout_session_meta_scanner_ignores_decode_errors_and_non_objects`
- `:2065` `test_find_rollout_session_meta_scanner_parses_only_candidates`
- `:2094` `test_find_rollout_session_meta_scanner_propagates_value_error`
- `:2115` `test_find_rollout_session_meta_single_escape_variants` の 12 variant
- `:2144` `test_find_rollout_session_meta_bomless_utf_variants` の 4 variant
- `:2156` `test_find_rollout_continues_after_bad_candidate_in_same_file`
- `:2170` `test_find_rollout_ignores_unreadable_file_before_match`
- `:2192` `test_find_rollout_ignores_empty_and_blank_rollouts`
- `:2233` `test_find_rollout_pinned_checks_content_before_returning`
- `:2259` `test_find_rollout_pinned_requires_exactly_one_named_candidate`
- `:2285` `test_find_rollout_pinned_sha_mismatch_falls_back_to_duplicate_rejection`
- `:2314` `test_find_rollout_pinned_requires_sha_pin_eligibility`
- `:2333` `test_find_rollout_pinned_requires_label_id_pairing`
- `:2366` `test_find_rollout_pinned_rglob_reaches_arbitrary_depth` の 2 variant
- `:2396` `test_find_rollout_pinned_returns_resolved_symlink`
- `:2421` `test_find_rollout_pinned_zero_named_candidates_uses_full_scan`
- `:2451` `test_find_rollout_ineligible_pin_preserves_opaque_session_id` の 4 variant。`:2447` の Unicode escape の字面も変更しない
- `:2495` `test_find_rollout_pinned_glob_metacharacters_are_literal`
- `:2521` `test_find_rollout_pinned_permission_error_is_speculative`
- `:2563` `test_find_rollout_pinned_memory_error_is_speculative`
- `:2590` `test_find_rollout_pinned_does_not_catch_base_exception`
- `:2623` `test_find_rollout_pinned_preserves_session_meta_encodings_and_bad_rows` の 3 variant
- `:2663` `test_find_rollout_pinned_candidate_value_error_propagates`
- `:2695` `test_find_rollout_pinned_parses_only_named_candidate_lines`
- `:2738` `test_find_rollout_pinned_skips_unrelated_value_error`

file 全体についても追加の赤はない。

- `:296-298` の fake Codex は P/P 行を生成する。
- `:529-533` の `id_mismatch` fixture でも、検索 target は `id` と同じである。`:3313` の M4 は従来どおり消費側の mismatch で拒否される。
- `:2769-2827` の二つの wiring test は `_find_rollout` を monkeypatch しており、述語を実行しない。
- `:2831-2839` の historical POS と、fixture 構築で使う pin 付き 5 label は、親 probe で旧述語と P1 が同じ file を返すことを確認済みである。

## 追加テスト設計

現行 `_write_rollout` `:2214-2217` の直後へ、pin を使わない 3 テスト関数を追加する。filename は `rollout-0.jsonl`、`rollout-1.jsonl` とし、ID を名前へ埋め込まない。

### 型 A: 取り違え

テスト名:

```text
test_find_rollout_disambiguates_parent_from_child_root_reference
```

最小 fixture:

```json
parent: {"type":"session_meta","payload":{"id":"parent-session","session_id":"parent-session"}}
child:  {"type":"session_meta","payload":{"id":"child-session","session_id":"parent-session"}}
```

assertion:

```python
assert TOOL._find_rollout(tmp_path, parent_id) == parent.resolve()
assert TOOL._find_rollout(tmp_path, child_id) == child.resolve()
```

現行 OR 述語では親検索が 2 件になり、最初の assertion が positive control として失敗する。二つ目は子自身を引く経路の非退行を固定する。

### 型 B: 親行コピー

テスト名:

```text
test_find_rollout_disambiguates_fork_with_copied_parent_meta
```

親 file は型 A と同じ。子 file は最低限次の 2 行を持つ。

```json
{"type":"session_meta","payload":{"id":"child-session","session_id":"parent-session","source":{"subagent":{"thread_spawn":{}}},"forked_from_id":"parent-session"}}
{"type":"session_meta","payload":{"id":"parent-session","session_id":"parent-session"}}
```

assertion は型 A と同じ二つにする。親検索では第 1 行が veto を立て、第 2 行が親 own を立てても file 全体を拒否する。子検索では第 1 行の own により子 file を返す。

さらに同じ二行を逆順にした parameter variant を加える。実 corpus 再現は上記順序の case が担い、逆順 case は「先に親コピーを見て即 `True`」という順序依存の変異を殺す。

### 真の重複の負例

テスト名:

```text
test_find_rollout_true_duplicate_parent_identity_remains_rejected
```

P/P の同じ `session_meta` を持つ二つの file を作る。両方とも P1 を満たすため、次を期待する。

```python
with pytest.raises(TOOL.ValidationError) as excinfo:
    TOOL._find_rollout(tmp_path, parent_id)
assert excinfo.value.rc == TOOL.RC_SESSION
assert str(excinfo.value) == (
    "session parent-session rollout count is 2, expected 1"
)
```

既存 `:2030` の id-only 重複は変更せず、P/P 形の対象限定負例を追加する。

## pin fast path への影響

`tools/codex_reasoning_ab.py:322` で fast candidate にも新述語が適用されるため、P1 の影響は次のように閉じる。

- 正しい親 candidate の P/P 行は P1 を満たす。`session-id-only` も fallback により維持される。
- 子 C/P を親 P の candidate として見つけても P1 が拒否し、`:332-335` の全走査へ落ちる。
- 子 C/P を子 C で検索した場合は own が C なので受理される。子を直接 pin する将来経路も壊さない。
- candidate が P1 を満たしても、`:326` の `_verify_rollout_sha` が成功するまで返さない。
- P1 または SHA 検査が失敗した場合の speculative fallback、全走査、件数検査は現行どおりである。
- 親 probe では POS、NEG、fix1、fix2、author の 5 label が旧述語と同じ file に解決している。
- pin 無しでは必ず `:333` の全 `rollout-*.jsonl` 走査を行う。探索打ち切り、head 制限、件数上限、filename による同一性判定は追加しない。
- 1 パス化は `_session_meta_rows()` 後の list 評価だけであり、file 読取りや rollout 全体の走査を短縮しない。parse-count 系テストの `json.loads` 回数も変わらない。

## 改名 (P4) の影響範囲

P4 は二つの private signature に揃えて適用する。

```text
tools/codex_reasoning_ab.py:283
_rollout_matches_session(path, session_id)
→ _rollout_matches_session(path, target_session_id)

tools/codex_reasoning_ab.py:295-300
_find_rollout(sessions_root, session_id, *, pinned_label=None)
→ _find_rollout(sessions_root, target_session_id, *, pinned_label=None)
```

既存 `_find_rollout` 呼出元は次が全件である。

```text
tools/codex_reasoning_ab.py:627
tools/codex_reasoning_ab.py:1758
tools/codex_reasoning_ab.py:3076

orchestrator/tests/test_codex_reasoning_ab.py:712
orchestrator/tests/test_codex_reasoning_ab.py:2017
orchestrator/tests/test_codex_reasoning_ab.py:2027
orchestrator/tests/test_codex_reasoning_ab.py:2044
orchestrator/tests/test_codex_reasoning_ab.py:2062
orchestrator/tests/test_codex_reasoning_ab.py:2090
orchestrator/tests/test_codex_reasoning_ab.py:2107
orchestrator/tests/test_codex_reasoning_ab.py:2132
orchestrator/tests/test_codex_reasoning_ab.py:2153
orchestrator/tests/test_codex_reasoning_ab.py:2167
orchestrator/tests/test_codex_reasoning_ab.py:2189
orchestrator/tests/test_codex_reasoning_ab.py:2200
orchestrator/tests/test_codex_reasoning_ab.py:2254
orchestrator/tests/test_codex_reasoning_ab.py:2278
orchestrator/tests/test_codex_reasoning_ab.py:2307
orchestrator/tests/test_codex_reasoning_ab.py:2329
orchestrator/tests/test_codex_reasoning_ab.py:2352
orchestrator/tests/test_codex_reasoning_ab.py:2391
orchestrator/tests/test_codex_reasoning_ab.py:2415
orchestrator/tests/test_codex_reasoning_ab.py:2438
orchestrator/tests/test_codex_reasoning_ab.py:2485
orchestrator/tests/test_codex_reasoning_ab.py:2516
orchestrator/tests/test_codex_reasoning_ab.py:2553
orchestrator/tests/test_codex_reasoning_ab.py:2586
orchestrator/tests/test_codex_reasoning_ab.py:2618
orchestrator/tests/test_codex_reasoning_ab.py:2658
orchestrator/tests/test_codex_reasoning_ab.py:2691
orchestrator/tests/test_codex_reasoning_ab.py:2732
orchestrator/tests/test_codex_reasoning_ab.py:2761
orchestrator/tests/test_codex_reasoning_ab.py:2763
orchestrator/tests/test_codex_reasoning_ab.py:2836
```

すべて第 2 positional argument で、`session_id=` keyword caller は repo 内にない。したがって呼出行の変更は不要である。`:2776-2785` と `:2809-2816` の monkeypatch 用 signature double は、明瞭化のため仮引数だけ `target_session_id` に揃える。

`_rollout_matches_session` の呼出元は次の全件。

```text
tools/codex_reasoning_ab.py:322
tools/codex_reasoning_ab.py:334
orchestrator/tests/test_codex_reasoning_ab.py:2544
orchestrator/tests/test_codex_reasoning_ab.py:2613
```

後二つは保存した callable を positional に呼ぶため、変更不要である。`tools/codex_reasoning_ab.py:3070,3093` の `session_id` は payload の root session 値なので改名しない。

## 残る不確実性

1. `payload.id` が非文字列の場合の fallback:

   - 推奨: 欠落、`null`、数値を含む全非文字列で `payload.session_id` へ fallback する。本プランの after はこれ。
   - 代案: key が欠落した場合だけ fallback し、非文字列の `id` は拒否する。

   P3 は欠落 case しか明示しておらず、親 probe も型別件数を報告していない。推奨案を採るなら、段 4 でこの意味を明文化する。

2. P4 の範囲と根拠:

   - 推奨: `_find_rollout` と `_rollout_matches_session` の両方を `target_session_id` にする。
   - 代案: brief が直接名指した `_find_rollout` だけを改名する。

   base `ab3feb04` の `docs/decisions.md:3007` にある D75 は freeze 恒久設計であり、命名規則ではない。brief `:62` の D75 参照は根拠として成立しないため、段 4 では P4 を局所的な可読性改善として採るか、正しい参照を特定してから採るかを明示裁定する必要がある。

3. 「受理集合」の定義域:

   - 推奨: file・target の候補述語集合を意味すると明記する。この意味では P1 は現行の真部分集合である。
   - 代案: `_find_rollout` 呼出し全体の成功集合を意味するなら、旧 `RC_SESSION` の 2 ID を成功へ変える T-936 自体と両立しない。

`tools/codex_reasoning_ab.py:3090` の複数 meta 拒否はこの択一とは別であり、T-937 として scope 外に残す。