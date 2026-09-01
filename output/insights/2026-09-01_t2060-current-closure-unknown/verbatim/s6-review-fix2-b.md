## 新設負例の実効性

- N-01 / real / `orchestrator/tests/test_codex_reasoning_ab.py:1103-1123`, `:803-888` / 重複負例は resolver の `len(candidates) != 1` に実際に到達する。
  - `_session_meta_bytes` が有効な session identity を作り、2つの別 path へ配置する (`:7729-7743`, `:1108-1113`)。
  - recursive scan が両方を `matches[label]` へ追加し (`:867-874`)、欠落分岐を通らず count 2 で `RC_SESSION` になる (`:880-888`)。
  - テストは診断文字列に加えて `caught.value.rc == TOOL.RC_SESSION` も検査しているため、文字列一致だけではない (`:1115-1123`)。

- N-02 / real / `orchestrator/tests/test_codex_reasoning_ab.py:1126-1145`, `tools/codex_reasoning_ab.py:483-503,640-655` / 破損負例は手前で落ちず、SHA 不一致経路へ到達する。
  - 先頭の session meta は有効で、末尾の `corrupt\n` だけが追加される (`test_codex_reasoning_ab.py:1131-1135`)。
  - `_session_meta_rows` は末尾行を無視するため identity は1件として解決される。resolver は `_verify_rollout_sha` を呼ぶ (`:879-894`)。
  - `_verify_rollout_sha` が全 bytes を hash し、`RC_SNAPSHOT` を上げる (`codex_reasoning_ab.py:651-655`)。
  - テストは診断と `RC_SNAPSHOT` の両方を検査する (`test_codex_reasoning_ab.py:1137-1145`)。過剰決定ではない。

## 変異 B1〜B4 の成立可否と exact 逐語

各 old は対象ファイル内で出現1回であることを確認した。

### B1

M-01 / real / `orchestrator/tests/test_codex_reasoning_ab.py:904-907` / direct reader へ戻せば欠落が skip されず `RC_SESSION` となり、欠落負例が赤になる。

```python
    resolved, missing = _resolve_required_historical_rollouts(
        sessions_root,
        pins=pins,
    )
```

これを従来型の `TOOL._find_rollout` による直接解決へ置換すると、0件入力は production の count 検査 (`tools/codex_reasoning_ab.py:628-636`) で拒否される。前後に別の skip 層はない。B1 は成立する。

### B2

M-02 / real / `orchestrator/tests/test_codex_reasoning_ab.py:880-882,1103-1123` / 変異は適用できるが、現在の負例では KILLED にならない。

```python
        if not candidates and not named_candidates[label]:
            missing.append(label)
            continue
```

条件を `if len(candidates) != 1:` へ広げれば、重複2件は `missing` に入り、後続の duplicate raise を `continue` で回避する。他に重複を拒否する層はない。

ただし `_require_historical_rollouts` はその後 `pytest.skip` する (`:908-912`)。`pytest.raises(ValidationError)` の node は失敗せず「skip」になるため、通常の pytest mutation 判定では rc 0、つまり SURVIVED となる。

修正方法は、この負例から `_require_historical_rollouts` ではなく `_resolve_required_historical_rollouts` を直接呼び、重複変異時に `pytest.raises` 自体を失敗させること。

### B3

M-03 / real / `orchestrator/tests/test_codex_reasoning_ab.py:890-894,1126-1145` / 事前登録の「不在分岐」には SHA 情報がなく、実装後の有効な anchor は SHA 検査呼び出しになる。

```python
        TOOL._verify_rollout_sha(
            rollout,
            label,
            expected_sha256=expected_sha256,
        )
```

これを `RC_SNAPSHOT` 捕捉後に `missing.append(label); continue` する形へ変異させれば、SHA 不一致を skip へ倒せる。手前の identity/count 検査は当該入力を拒否しないため、変異自体の帰属は一意である。

しかし B2 と同じく、現在の負例は赤ではなく skip になる。したがって KILLED 期待は refuted。B2 と B3 は別 node (`:1103`, `:1126`) なので同一 node 帰属問題はないが、両方とも lower-level resolver を検査する形へ直す必要がある。

### B4

M-04 / real / `orchestrator/tests/test_codex_reasoning_ab.py:909-912,1089-1100` / label を落とすと `match=label` が失敗し、診断感度 pin として赤になる。

```python
        pytest.skip(
            "historical rollouts unavailable; expired session labels: "
            + ", ".join(missing)
        )
```

受理集合は変わらないので、事前登録どおり kill 数には含めない扱いが妥当。

## 受入の 26 entry が解消するか (差 2 件の説明を含む)

A-01 / real / `orchestrator/tests/test_codex_reasoning_ab.py:916-1036` / 既存26件の rollout 欠落原因は静的にはすべて再配線されている。ただし全走緑は未実測で、portable fixture の問題が残る。

26件の対応は次のとおり。

- 21 error:
  - `test_parent_numstat_controls_remain_pinned` の1件は historical fixture に移り、欠落時 skip。
  - 残る20件は rollout 非依存の `benchmark_snapshots` に移る。
- 5 failed:
  - `test_m2_production_golden_requires_both_routes`
  - `test_prompt_replacement_count_zero_expected_and_excess[0]`
  - `[9]`
  - `[10]`
  - `test_real_rollout_collector_golden_is_source_bound`
  
  以上は `historical_rollouts` を要求し、欠落時 skip となる。

28との差2件は、ファイル末尾の以下である。

- `test_attempt_four_is_rejected_before_launch` (`:12308`)
- `test_f3_4_prelaunch_exception_completes_pair_and_allows_next_generation` (`:12333`)

旧 fixture の静的 consumer は23 nodeだったが、実測 error は先頭側の21 nodeだけだった。そこへ直接失敗5件を足して26 entryとなる。上記2 nodeは collection 順で最後にあり、Junit entry に記録されなかった trailing consumer である。早期打切りか選択条件かは、射影資料に実行コマンドと Junit がないため断定できない。

算術は次のとおり。

- 実測26: `1 historical化 + 20 portable化 + 5 historical化`
- 静的28: 上記に未記録の portable 2件を加え、`6 skip + 22実走`

この2件にも verifier 配線が追加されている (`:12313-12315`, `:12338-12340`)。

## 新しい時限装置の有無

T-01 / refuted / `s6-fix2-diff.patch:5-16`, `orchestrator/tests/test_codex_reasoning_ab.py:128,391-404` / repo 外絶対 path、ホーム、固定日付の新規 literal は増えていない。

- 固定ファイル名 `_REAL_ROLLOUT` は削除され、むしろ dated rollout への直接依存が減った。
- `/home/SFC/tanab/.codex/sessions` は既存の `_HISTORICAL_SESSIONS` のまま。
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t682-provenance-known-violations/s2-plan.md` への既存依存は `:391-404` にそのまま残る。今回の diff には変更がない。
- 新設 fixture は既存の固定 commit `BASE_COMMIT`、`INTEGRATED_COMMIT`、`ARTIFACT_COMMIT` を使う。新しい literal ではないが、22 node の実行可能性をこれらの object と submodule 状態へ依存させている。

## portable fixture の決定性

P-01 / real / `orchestrator/tests/test_codex_reasoning_ab.py:975-1036`, `tools/codex_reasoning_ab.py:1014-1069,3292-3315,3582-3595` / 「portable」は無条件には成立しない。

main repository の通常ファイルは pinned commits から作られるため、dirty worktree の通常ファイルや時刻には依存しにくい。一方、submodule は次のように current source repo を参照する。

- `_build_snapshot_base` が `_init_submodules_from_local_source(repo, base)` を呼ぶ (`codex_reasoning_ab.py:3311`)。
- submodule の列挙と状態判定は source repo の現在の index、`.gitmodules`、worktree/admin store を使う (`:1017-1045`)。
- source で initialized と判定された submodule だけを snapshot に初期化する (`:1046-1069`)。
- 未初期化のままなら `verify_snapshot` が拒否する (`:3582-3595`)。

したがって submodule が未実体化、HEAD/gitlink が不一致、必要 object がローカルにない環境では module fixture が error となり、その22 consumerすべてが再び赤になり得る。

tmp path は oracle の `snapshot` fieldへ入る (`codex_reasoning_ab.py:3600`) ため生成 JSON の digest は実行ごとに変わる。ただし期待値も同じ実行内で生成されるので、現状は pass/fail の揺れには直結しない。mtime は metadata manifest の比較対象ではない (`:1634-1671`)。

## 他 test file への波及

W-01 / refuted / `s6-fix2-diff.patch:155-176,290-347,535-539` / 既存 test node 名の変更はない。

- `benchmark_snapshots` の名前は維持され、内容だけ portable 版へ差し替えられた。
- `test_real_rollout_collector_golden_is_source_bound` は引数追加だけで node 名は同じ。
- 新しい名前は fixture 2個と負例 node 3個だけ。
- `historical_benchmark_snapshots` の consumer は同一ファイル内の `test_parent_numstat_controls_remain_pinned` だけ。
- `historical_rollouts` の consumer も同一ファイル内に限定されている。

W-02 / real / 射影対象外 / 外部 consumer test、meta test、`REAL_REPO_SERIAL_NODES` 登録簿の完全な参照確認は、この単独段 dispatch の許可資料だけでは実施不能。

許可された2コードファイル内には `REAL_REPO_SERIAL_NODES` はなく、既存 node の rename もないため、既存登録の破損は見えない。新設3 nodeが closed-world meta registryへの追加を要求されるかだけは、対象 registry 自体が射影されていないため未確認である。

## 所見一覧

| ID | 判定 | 実体 | 影響 |
|---|---|---|---|
| N-01 | real | test file `:803-888,1103-1123` | 重複負例は狙った `RC_SESSION` 経路に到達する。 |
| N-02 | real | test file `:1126-1145`; tool `:483-503,640-655` | 破損負例は SHA 不一致だけで赤になる。 |
| M-01 | real | test file `:904-907` | B1 は一意 anchor と単一拒否理由を持つ。 |
| M-02 | real | test file `:880-888,1103-1123` | B2 mutant は負例を赤でなく skip にし、kill できない。 |
| M-03 | real | test file `:890-894,1126-1145` | B3 mutant も skip となり、事前登録の KILLED 期待を満たさない。 |
| M-04 | real | test file `:909-912,1089-1100` | B4 は診断感度 pin として成立する。 |
| A-01 | real | test file `:916-1036` | 既存26件の rollout 欠落経路は再配線済みだが、全走緑は未証明。 |
| A-02 | real | test file `:12308-12340` | 28との差2件は Junit 未記録の末尾2 consumer。 |
| T-01 | refuted | diff `:5-16`; test file `:128,391-404` | 新規の外部絶対 path、ホーム、固定日付 literal はない。 |
| P-01 | real | tool `:1014-1069,3292-3315,3582-3595` | portable fixture は source submodule 実体化状態に依存する。 |
| W-01 | refuted | diff `:155-176,535-539` | 既存 node 名変更による registry 破損はない。 |
| W-02 | real | 射影対象外 | 外部 meta registry への新設3 nodeの波及だけは未確認。 |

## 総括

重複と SHA 不一致の新設負例は本物で、狙った production 経路と rc を検査している。一方、変異 B2/B3 は mutant を赤ではなく skip にするため、現状のままでは KILLED と数えられない。負例を lower-level resolver へ向ける修正が必要である。

既存26 entry の rollout 欠落原因は静的には全件再配線され、差2件も末尾の未記録 consumer と特定できる。ただし合成 fixture は source repo の submodule 初期化状態に依存するため、「どの実行環境でも受入全走が緑」は refuted。pytest は実行しておらず、緑とは報告しない。