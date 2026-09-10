## 変異 11 件の成立判定

以下は未実走の静的判定であり、pytest 緑や実際の mutation 結果は主張しない。

- [実測] M1 — 成立。置換点は seed を `started_budget_counts` に適用する [attempt_registry_core.py:1015](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/attempt_registry_core.py:1015) の1箇所。`test_attempt_registry_core_s8b_profile.py::test_seeded_budget_replay_rejects_invalid_counts_and_accepts_exact_limit[True]` など3 nodeと `::test_seeded_budget_replay_rejects_eleventh_start_and_old_apis_are_unchanged` が赤になる。先行拒否はない。判定: refuted / must-fix: 否 / 成果物影響: seeded budget 防壁へ KILLED を帰属できる。

- [実測] M2 — 成立。置換点は [attempt_registry_core.py:999](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/attempt_registry_core.py:999) の値検証1箇所。kill nodeid は `test_attempt_registry_core_s8b_profile.py::test_seeded_budget_replay_rejects_invalid_counts_and_accepts_exact_limit[True|-1|1.5]`。各入力を先に拒否する層はない。判定: refuted / must-fix: 否 / 成果物影響: bool、負数、非 int の拒否をこの gate に帰属できる。

- [実測] M3 — 成立。置換点は既定 separator を使う [s8b_attempt_profile.py:560](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/s8b_attempt_profile.py:560) の1箇所。kill nodeid は `test_attempt_registry_core_s8b_profile.py::test_serialize_session_line_uses_spaced_sorted_utf8_json_and_newline` で、exact bytes は [test_attempt_registry_core_s8b_profile.py:2222](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/tests/test_attempt_registry_core_s8b_profile.py:2222) にある。判定: refuted / must-fix: 否 / 成果物影響: separator 契約を単独で検査できる。

- [実測] M4 — 成立。置換点は newline を加える [s8b_attempt_profile.py:566](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/s8b_attempt_profile.py:566) の1箇所。M3と同じ exact-bytes nodeが独立した末尾差で赤になる。判定: refuted / must-fix: 否 / 成果物影響: JSON separator と framing の帰属を分離できる。

- [実測] M5 — 要再照準。明示的な symlink operand は [s8b_attempt_registry.py:659](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/s8b_attempt_registry.py:659) の1箇所だが、これだけを消しても同じ条件の `not stat.S_ISDIR(lstat-mode)` が即座に拒否する。事前登録が mask 元とした `_read_regular_bytes()` の親 component 検査 [s8b_attempt_registry.py:532](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/s8b_attempt_registry.py:532) へ到達しない。判定: real / must-fix: はい / 成果物影響: SURVIVED を意図した二層防御の証拠に帰属できない。

- [実測] M6 — 空振り。累積候補は [s8b_attempt_registry.py:659](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/s8b_attempt_registry.py:659) と [s8b_attempt_registry.py:532](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/s8b_attempt_registry.py:532) だが、`directory-symlink` fixture のリンク先は空 directory [test_s8b_attempt_registry.py:1919](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/tests/test_s8b_attempt_registry.py:1919) である。両検査を消しても `registry.jsonl` 欠落を [s8b_attempt_registry.py:665](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/s8b_attempt_registry.py:665) が同じ期待 message で拒否するため、`test_generation_enumerator_rejects_unsafe_hex_authority_and_accepts_real_one[directory-symlink]` は赤にならない。判定: real / must-fix: はい / 成果物影響: M5/M6 の mask 対が成立せず、二層同時除去の KILLED 証拠がない。

- [実測] M7 — 要再照準。欠落専用 block は [s8b_attempt_registry.py:665](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/s8b_attempt_registry.py:665) の1箇所で、nodeid は `test_generation_enumerator_rejects_unsafe_hex_authority_and_accepts_real_one[missing-registry]`。ただし `_fail` だけを消すと直後の `_read_regular_bytes()` [s8b_attempt_registry.py:676](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/s8b_attempt_registry.py:676) が同じ欠落を別 message で拒否し、message 差で赤になる。変異を `FileNotFoundError` 時にその世代を `continue` する形まで明記すれば単一理由になる。判定: real / must-fix: はい / 成果物影響: 現状の KILLED は不完全世代拒否の一意な防壁を証明しない。

- [実測] M8 — 要再照準。明示比較は [s8b_attempt_registry.py:757](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/s8b_attempt_registry.py:757) の1箇所で、nodeid は `test_generation_resolver_rejects_stale_recovery_policy_and_accepts_current`。比較を消しても、直後の `core.assert_registry_rows()` [s8b_attempt_registry.py:763](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/s8b_attempt_registry.py:763) が core の同じ digest 比較 [attempt_registry_core.py:721](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/attempt_registry_core.py:721) で拒否する。test は message 差で赤になるだけで、live 合成2段 v1は正入力にならない。判定: real / must-fix: はい / 成果物影響: resolver 固有 gate の KILLED として数えると誤帰属になる。

- [実測] M9 — 成立。物理 path と genesis protocol の比較は [s8b_attempt_registry.py:747](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/s8b_attempt_registry.py:747) の1箇所。kill nodeid は `test_generation_resolver_rejects_protocol_path_mismatch_and_accepts_match` [test_s8b_attempt_registry.py:1985](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/tests/test_s8b_attempt_registry.py:1985)。core は物理 path を受け取らないため後段 mask はない。判定: refuted / must-fix: 否 / 成果物影響: path/genesis 束縛へ KILLED を帰属できる。

- [実測] M10 — 成立。外殻の hook 呼出しは [s8b_attempt_registry.py:1323](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/s8b_attempt_registry.py:1323) の1箇所。既存 kill nodeid は `test_root_lock_serializes_two_updates_after_same_old_snapshot_barrier` [test_s8b_attempt_registry.py:1574](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/tests/test_s8b_attempt_registry.py:1574)、追加 nodeは `test_locked_update_seam_does_not_reacquire_lock_or_run_prelock_hook` [test_s8b_attempt_registry.py:2159](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/tests/test_s8b_attempt_registry.py:2159)。判定: refuted / must-fix: 否 / 成果物影響: prelock 順序を直接検査できる。

- [実測] M11 — 成立。4軸へ戻す置換点は adapter wrapper [s8b_attempt_registry.py:995](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/s8b_attempt_registry.py:995) の1箇所。kill nodeid は新設された `test_v2_profile_is_rejected_by_public_mutation_but_slot_lookup_is_five_axis` [test_s8b_attempt_registry.py:2197](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/tests/test_s8b_attempt_registry.py:2197)。helper を直接呼ぶため public `_assert_profile()` の v2 拒否を通らない。判定: refuted / must-fix: 否 / 成果物影響: measurement ordinal を含む5軸 identity の証拠になる。

## 回帰閉包

- [実測] 差分追加は15 test関数、静的展開21 nodeであり、自己申告の22 node [s5-author.md:7](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t1851-unit-a/artifacts/t1851-unit-a/s5-author.md:7) は1多い。内訳は profile側8 node [test_attempt_registry_core_s8b_profile.py:2066](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/tests/test_attempt_registry_core_s8b_profile.py:2066)、adapter側13 node [test_s8b_attempt_registry.py:1845](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/tests/test_s8b_attempt_registry.py:1845)。判定: real / must-fix: はい / 成果物影響: 既存172 nodeへ単純加算した閉包は193 nodeである。

- [実測] adapter が scheduler の authority定数を新たに trust root として読む [s8b_attempt_registry.py:704](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/s8b_attempt_registry.py:704) ため、段3の scheduler consumer 1 nodeとは別に `test_policy_is_canonical_empty_and_pins_the_observed_value_range` [test_s8b_scheduler_accounting.py:78](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/tests/test_s8b_scheduler_accounting.py:78) が新たに閉包へ入る。したがって最小閉包は `172 + 21 + 1 = 194 node`。判定: real / must-fix: はい / 成果物影響: 親の回帰選択へこの1 nodeを追加しないと trust root の導出が未検査になる。

- [実測] 新設 test file は0。追加 nodeは既存の2 fileだけで、3 file全選択型の既存閉包に自動包含されるため、file集合を列挙する meta-test の更新対象はない。判定: refuted / must-fix: 否 / 成果物影響: meta-test の file列挙漏れはない。

- [実測] 所有外 production caller の実測は4箇所。`trial_registry.py` の callable 2件 [trial_registry.py:2244](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/trial_registry.py:2244)、[trial_registry.py:3467](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/trial_registry.py:3467) と、`load_attempt_registry` の2件 [s8b_holdout_admission.py:5620](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/s8b_holdout_admission.py:5620)、[s8b_scheduler_accounting.py:335](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/s8b_scheduler_accounting.py:335)。自己申告は callable を2件と定量化し、残り2 fileは名前だけ列挙しており、列挙実体は4、明記数は2 [s5-author.md:33](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t1851-unit-a/artifacts/t1851-unit-a/s5-author.md:33)。判定: nit / must-fix: 否 / 成果物影響: 所有外 file自体の数え落としはないが、報告の集計値は曖昧。

- [実測] `assert_registry_rows` の公開 signature は [attempt_registry_core.py:1361](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/attempt_registry_core.py:1361) で維持され、8cの2箇所はいずれも `rows, profile, expected_binding` だけを渡す。戻り値も従来どおり `RegistryRows` である。判定: refuted / must-fix: 否 / 成果物影響: `trial_registry.py` の callable 2経路に静的な破壊はない。

## 正例の恒真性

- [実測] P1は `test_canonical_v1_lifecycle_ignores_non_generation_sibling` [test_s8b_attempt_registry.py:1878](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/tests/test_s8b_attempt_registry.py:1878) が create、start、classify、observe、terminalを実APIで通す。列挙が canonical path を落とす、または mutation pathを過剰拒否すれば赤になるため恒真ではない。判定: refuted / must-fix: 否 / 成果物影響: 正規1段 v1 の受理維持を検査できる。

- [実測] P2は同じ node が非64 hexの `consumption-catalog.jsonl` を作り [test_s8b_attempt_registry.py:1885](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/tests/test_s8b_attempt_registry.py:1885)、列挙結果とその後の mutation を検査する。非hex siblingを拒否または世代扱いすれば赤になる。判定: refuted / must-fix: 否 / 成果物影響: 非世代 sibling の許容を実経路で固定する。

- [実測] P3は core の seed 9 + start 1 [test_attempt_registry_core_s8b_profile.py:2086](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/tests/test_attempt_registry_core_s8b_profile.py:2086) と、実adapterの他世代9 + current1 [test_s8b_attempt_registry.py:2120](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/tests/test_s8b_attempt_registry.py:2120) の両方にある。seedを無視すると前者は counts 比較、後者は11件目拒否で赤になるため恒真ではない。判定: refuted / must-fix: 否 / 成果物影響: 境界値10の受理と11の拒否を両層で検査できる。

## その他の所見

- [実測] `_peek_registry_genesis()` の型 guard [s8b_attempt_registry.py:587](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/s8b_attempt_registry.py:587) は、production唯一の callerが `_read_regular_bytes()` の bytes を `assert data is not None` 後に渡す経路 [s8b_attempt_registry.py:1211](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/s8b_attempt_registry.py:1211) なので現物入力では到達不能。この guardを無効化する変異は構造的に SURVIVED する。不到達を直接testで到達可能に見せるべきではない。判定: real / must-fix: はい / 成果物影響: mutation台帳に帰属不能な防御分岐が1つ増える。

- [実測] 横断予算の実効層は `_atomic_update_locked()` [s8b_attempt_registry.py:1252](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/s8b_attempt_registry.py:1252) で、既存6 mutation callerは外殻 `_atomic_update()` を通る。一方、`launch_floor_attempt()` の production callerは0、resultはv4 [s8b_floor_contract.py:34](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/s8b_floor_contract.py:34)、campaignの `assemble_result()` に台帳引数はない [s8b_floor_campaign.py:7789](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/s8b_floor_campaign.py:7789)。自己申告もA2'未実装と明記している。判定: refuted / must-fix: 否 / 成果物影響: A1'が certified選択、材料レポート、proof chainへ発火するとの過大主張はない。

- [実測] 新規commentは authoritative readをlock内で再実行すると限定し [s8b_attempt_registry.py:1228](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/s8b_attempt_registry.py:1228)、live-lock guardもA2'送りと明記する [s8b_attempt_registry.py:1250](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/s8b_attempt_registry.py:1250)。journal TOCTOU窓を閉じたとの記述はない。判定: refuted / must-fix: 否 / 成果物影響: 未解決窓について保証の先取りはない。

- [実測] `serialize_session_line` の production callerは0で、定義 [s8b_attempt_profile.py:556](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/s8b_attempt_profile.py:556) とtest [test_attempt_registry_core_s8b_profile.py:2219](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/tests/test_attempt_registry_core_s8b_profile.py:2219) だけである。docstringの「exactly once」は配線済みとも読めるが、journal窓を閉じたとの明記ではない。判定: nit / must-fix: 否 / 成果物影響: runtime保証ではなく、文言上の曖昧さだけが残る。

- [実測] 差分は production 741 changed LOC、test 634 changed LOC、合計1375 changed LOCで、裁定見積り約900 [s4-adjudication.md:170](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t1851-unit-a/s4-adjudication.md:170) を475 LOC、約53%超過した。新設 testは21 nodeで見積り35〜45を14〜24下回る。判定: real / must-fix: 否 / 成果物影響: review規模は過小見積り、敵対検査量は過大見積りだったため、親の容量記録を訂正する必要がある。

## must-fix

- [実測] M5/M6を、完全な regular `registry.jsonl` を持つ symlink先と、列挙側の全 symlink判定および親component検査を明示した対へ再登録する [s8b_attempt_registry.py:532](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/s8b_attempt_registry.py:532)。判定: real / must-fix: はい / 成果物影響: 現状ではM6が空振りし、二層防御を証明できない。

- [実測] M7を「欠落時に `continue` して不完全世代を無視する」など、後段readへ落ちない具体的置換へ再登録する [s8b_attempt_registry.py:665](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/s8b_attempt_registry.py:665)。判定: real / must-fix: はい / 成果物影響: message差による見かけのKILLEDを防ぐ。

- [実測] M8はadapterとcoreの二層同時変異として登録するか、比較所有者を一層へ集約する [attempt_registry_core.py:721](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/attempt_registry_core.py:721)。判定: real / must-fix: はい / 成果物影響: recovery-policy拒否の帰属を正しくする。

- [実測] 回帰選択を最小194 nodeへ訂正し、scheduler authority pin nodeを含める [test_s8b_scheduler_accounting.py:78](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/tests/test_s8b_scheduler_accounting.py:78)。判定: real / must-fix: はい / 成果物影響: 新trust rootの回帰閉包を閉じる。

- [実測] 到達不能な `_peek_registry_genesis` 型guardは削除または防壁として数えない [s8b_attempt_registry.py:587](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/s8b_attempt_registry.py:587)。判定: real / must-fix: はい / 成果物影響: 構造的SURVIVEDを防壁証拠へ混入させない。

## 総括

- [実測] M1〜M4、M9〜M11の7件は成立する。
- [実測] M5、M7、M8は要再照準、M6は空振りである。
- [実測] M5/M6のmask対とM8の単一理由性は現コードでは成立しない。
- [実測] P1〜P3は実在し、静的には恒真ではない。
- [実測] 最小回帰閉包は194 node、追加test実数は21 nodeである。
- [実測] 8cの callable 2経路はsignature・戻り型とも静的互換である。
- [実測] A1'が最終成果物へ発火するとの過大主張はない。
- [実測] pytestおよびmutationは実走しておらず、緑は主張しない。