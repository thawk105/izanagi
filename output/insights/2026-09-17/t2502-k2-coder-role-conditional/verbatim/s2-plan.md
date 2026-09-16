## 差分の位置と形

必読8ファイルはすべて読めた。以下の行番号は現 checkout の変更前を指す。実装・ファイル書込み・pytest 実走は行っていない。

production の変更は `orchestrator/campaign/p3_s4_loop.py:2669` と `:2670` の間への条件追加だけとする。前後の既存行を含む完成形は次のとおり。

```python
    resolved_knowledge = _resolve_knowledge_manifest_argument(
        a.knowledge_manifest,
    )
    if (
        a.run_iteration
        and not a.emit_planner_context
        and resolved_knowledge is not None
        and resolved_knowledge.manifest.sources
        and a.coder_role is None
    ):
        raise ValueError(
            "--run-iteration で --knowledge-manifest の sources が非空の場合は "
            "--coder-role が必要"
        )
    knowledge_de_novo_claim = a.knowledge_de_novo_claim == "true"
```

P1〜P3 の判定：

- **P1：位置は採用、経路 guard は補正する。** manifest 解決直後なら `_prepare_knowledge_campaign` の `layout.ensure()`（`:1555`）と `write_receipt`（`:1556`）、run 側呼出し（`:2728`）より前に拒否できる。ただし argparse は emit/run を排他的にせず、現状は emit 分岐（`:2689`）が先に実行され `:2713` で戻る。`a.run_iteration` だけでは両指定時の既存 emit 経路を変えるため、`and not a.emit_planner_context` を含める。新しい検査ではなく、既存の経路優先順位の保存である。
- **P2：採用。** `KnowledgeManifest.sources` は tuple（`knowledge_manifest.py:113`）。truthiness で非空を判定する。projection（同 `:490`）や retrieval status の再検査は不要。空 sources の契約は既に parser の `:320`〜`:332` にある。
- **P3：採用。** `ValueError` と上記の日本語 message を使う。`load_proposal_file` の既存相互必須検査（`:2309`〜`:2317`）と signature は変更しない。

通過経路の不変性は以下のとおり。同一の入力・初期状態・時計等の外部結果を前提に、追加条件は読み取りのみで、既存の引数・データ・書出し関数を変更しない。したがって identity・receipt・WAL の bytes を変える差分はない。別実行間の時刻入り bytes の一致を実測したという意味ではない。

| 経路 | 追加条件の結果と既存処理 |
|---|---|
| emit のみ | `a.run_iteration` が偽。`:2695` の prepare、projection、JSON 出力はそのまま |
| emit＋run 併記 | `not a.emit_planner_context` が偽。既存どおり emit が優先される |
| run、manifest 無し、role 無し | `resolved_knowledge is not None` が偽。prepare は `:1544` の既存戻り、loader は legacy |
| run、manifest 無し、role 有り | 同じく追加拒否なし。loader へ `knowledge_input=None` と role が渡り、`:2311` の既存検査で拒否される |
| run、空 sources、role 無し | sources が偽。既存の identity・receipt を作り、`:2775` により legacy loader を通る |
| run、空 sources、role K2 | sources が偽。従来どおり projection と role を K2 loader に渡す |
| run、非空 sources、role K2 | `a.coder_role is None` が偽。既存 K2 consumer をそのまま通る |
| run、非空 sources、role 無し | **今回だけ変更する経路。** prepare・loader・drive より前に拒否 |
| emit/run とも無し | run guard が偽。既存 fixture 経路を保存 |

## テスト差分

変更先は `orchestrator/tests/test_p3_s4_loop.py`。既存 helper と正例の直近、`:7262` の前へ新規テストを置く。

**負例：`test_main_nonempty_manifest_requires_coder_role_before_prepare`**

新しい共通 helper は作らず直書きする。`_run_main_with_actual_proposal_loader`（`:7158`）は成功を assert し（`:7201`）、成功用 drive spy を自分で登録する（`:7193`）。今回必要な未到達 spy と receipt 観測には適さない。

構成を以下に固定する。

1. `_resolved_knowledge_fixture(tmp_path, name="missing-role")`（`:1024`）で、実 parser/resolver を通した非空 manifest を得る。
2. `_k2_proposal_document()` の `coder` をその `["proposal"]` に置き換えて有効な flattened proposal を作り、`_write_k2_proposal`（`:7152`）で保存する。guard 削除時に K2 wrapper の schema 違反で先に落ちない入力にする。
3. 既存 helper の `:7168`〜`:7175` と同じく、resolver の戻り値、tmp 配下の layout、`patchharness.assert_pinned_clean` を設定する。実 `load_proposal_file` は残す。
4. `_prepare_knowledge_campaign` と `KM.write_receipt` を `Mock(wraps=実関数)` で観測する。ここでは fail させない。変異時に後段の drive spy まで到達できるようにする。
5. `drive_iteration` には到達時に `pytest.fail("drive_iteration reached")` する spy を登録する。
6. 次の argv を `pytest.raises(ValueError, match="--coder-role")` 内で直接 `L.main` に渡す。

```python
[
    "--run-iteration", str(proposal_path),
    "--no-build",
    "--knowledge-manifest", str(manifest_path),
]
```

7. raises の後に prepare・receipt・drive の各 spy の `assert_not_called()`、`Path(layout.root).exists()` が偽であることを確認する。

これで通常版は副作用前拒否を検証し、条件削除版は実 legacy loader を通って drive spy で失敗する。message だけの差を kill と数えない。

**既存正例2本は無変更。**

- `:7205` の `test_main_manifest_only_accepts_legacy_flattened_proposal`：空 sources＋role 無し。
- `:7241` の `test_main_manifest_and_k2_role_accept_k2_wrapper`：空 sources＋role K2。

条件式上、双方とも新しい拒否には入らない。緑の確認は親の実走で行う。

**非空 sources＋role K2 の実 loader 正例を追加する。**

名前は `test_main_nonempty_manifest_and_k2_role_accept_k2_wrapper`。`:7241` の構成を踏襲し、fixture だけ `_resolved_knowledge_fixture` にする。既存 helper を流用し、coder proposal と prior の一致を assert する。`_k2_proposal_document()` の既定 `knowledge_use=[]` を利用できる。非空 source を必ず使用するという新条件は加えない。

**P5 は採用する。**

`test_emit_context_and_run_iteration_share_manifest_campaign_identity` の後半 argv（`:6586`）だけに次を追加する。

```python
        "--coder-role", "coder-v4-autonomous-k2",
```

前半と共有する `common` には入れない。前半の「非空 manifest＋role 無しでも emit が通る」という検証を維持する。prepare は role を参照せず（production `:1531`〜`:1562`）、identity 比較の目的は保たれる。ただしこのテストは loader を stub 化している（`:6569`）ので、上記の新しい実 loader 正例を代替しない。

**emit/run 併記の保存テストも追加する。**

名前は `test_main_emit_context_takes_precedence_with_nonempty_manifest`。`:6524`〜`:6552` の前半を基に、実 resolver を通す非空 manifest、tmp layout、role 無しで emit と run を併記する。run の proposal path は未作成とし、drive 到達は fail。`main == 0`、context の `knowledge_input == KM.planner_projection(resolved)`、receipt の存在を確認する。

**既存呼出しの静的棚卸し：**

| 所在 | 判定 |
|---|---|
| `test_p3_s4_loop.py:6541` | identity 共有テストの common。後半 argv だけ補正 |
| 同 `:6639` | `test_main_passes_resolved_knowledge_projection_to_proposal_loader`。空 fixture（`:6607`）＋role（`:6640`）なので不変 |
| 同 `:7197` | 成功 helper。既存 caller は `:7229` と `:7251` の2本だけで、双方空 fixture |
| 他 test file の厳密な `\bL\.main\(` | **0件**。単純部分一致の `TOOL.main`、`B4L.main` は別物 |
| `test_p3_b4_proposal_binding.py:461,494,506,517` | `module.main` による間接呼出し。argv に manifest 無し |
| `test_p3_exploration_namespace.py:696,699,713,1160,1222,1476,1534` | driver 共通の `module.main`。base の argv factory は `:244`、`:248`、対応表 `:416`。manifest 無し |

この棚卸しと副作用のない条件追加から、P5 以外に今回の条件で赤になる既存 main テストは見当たらない。全既存テストの緑を実測済みとはしない。

## 変異事前登録の候補

node id を以下に固定する。いずれも prefix は `orchestrator/tests/test_p3_s4_loop.py::`。

```text
N = orchestrator/tests/test_p3_s4_loop.py::test_main_nonempty_manifest_requires_coder_role_before_prepare
E = orchestrator/tests/test_p3_s4_loop.py::test_main_manifest_only_accepts_legacy_flattened_proposal
K = orchestrator/tests/test_p3_s4_loop.py::test_main_manifest_and_k2_role_accept_k2_wrapper
P = orchestrator/tests/test_p3_s4_loop.py::test_main_nonempty_manifest_and_k2_role_accept_k2_wrapper
I = orchestrator/tests/test_p3_s4_loop.py::test_emit_context_and_run_iteration_share_manifest_campaign_identity
C = orchestrator/tests/test_p3_s4_loop.py::test_main_emit_context_takes_precedence_with_nonempty_manifest
```

変異 runner の対象をこの6 node に固定し、その集合内の**失敗 node 完全集合**を次のように登録する。

| 変異 | 確定する内容 | `expected_nodes` |
|---|---|---|
| M1 | 追加した if/raise ブロック全体を削除 | N |
| M2 | `and resolved_knowledge.manifest.sources` を `and not resolved_knowledge.manifest.sources` に変更 | N、E |
| M3 | `and a.coder_role is None` を `and a.coder_role is not None` に変更 | N、P、I |
| M4 | 条件内の `raise ValueError(...)` を `return 0` に置換 | N |
| M5-route | run/emit の経路限定2行を除去し、manifest 条件だけで拒否 | I、C |

M4 は親の二択のうち `return 0` を選ぶ。例外を発生させず成功扱いする変異なので、N の `pytest.raises` が殺す。

M3 について、親が挙げた **K は殺さない**。空 sources で短絡するためである。P と、後半に role を追加した I が過剰拒否を検出する。

M5 の原案「`a.run_iteration` だけ除去」は、本計画では emit 側の `not a.emit_planner_context` が残るため I で殺せない。fixture 経路には作用しうるので、全体として等価とも断定できない。原案は登録せず、経路限定の消失を表す **M5-route** に再照準する。

anchor は最初の節の完成形全体、すなわち resolver 呼出しから `knowledge_de_novo_claim` 代入までの複数行を `old` とする。各変異の `new` も前後の既存行を保持した完成形にする。

- M1：if/raise 部分だけを取り除き、既存の4行を残す。
- M2/M3：上記 anchor 内の該当1行だけ変更。
- M4：条件を残し、raise の3行を `        return 0` に置換。
- M5-route：冒頭を次の形へ置換し、残りは保持する。

```python
    if (
        resolved_knowledge is not None
        and resolved_knowledge.manifest.sources
        and a.coder_role is None
    ):
```

`replacements` は既存 harness の `{file, old, new}` 契約（`tools/mutation_harness.py:623`）を使い、対象 file は production の1本だけとする。独自 spec key は加えない。

DW-M01〜M08 に従い実装前登録、最終 commit で anchor 一意性と node 実在を再確認する。親が既存 harness の dispatch・detached 経路で baseline と変異を実走し、初回結果を保存する。ここでは KILLED を観測したとは報告しない。

## 焦点走の集合

指定の `grep -rl "p3_s4_loop" orchestrator/tests/` 相当を `rg -l` で実施した。以下はすべて `orchestrator/tests/` 配下。文字列一致の弱い参照も含め、次の29 test file を保守的な consumer 焦点集合とする。

| 参照関係 | test file |
|---|---|
| 対象本体・派生 driver | `test_p3_s4_loop.py`、`test_p3_s4_loop_sort.py`、`test_p3_s4_loop_trigger_gating.py` |
| CLI・namespace・job | `test_p3_build_authority_cli.py`、`test_p3_exploration_namespace.py`、`test_p3_s4_loop_job_contract.py` |
| B4 の import・projection・配線 | `test_p3_b4_raw_record_producer.py`、`test_p3_b4_launcher.py`、`test_p3_b4_wiring_probe.py`、`test_p3_b4_closed_critic.py`、`test_p3_b4_proposal_binding.py`、`test_p3_b4_material_report.py` |
| 共有関数・loop consumer | `test_campaign.py`、`test_s1_direct_comparison.py`、`test_s8b_floor_campaign.py`、`test_s8a_trigger_sweep.py`、`test_s6_sort_sweep.py`、`test_sort_swo_oracle.py`、`test_layer3_report.py`、`test_trigger_gate_binding.py` |
| source・adapter・起動規律 | `test_codex_agents.py`、`test_campaign_import_invariant.py`、`test_hooks.py`、`test_pegasus_tools.py` |
| 派生 path・説明・非依存 assert 等の文字列参照 | `test_s8b_oracle_driver.py`、`test_s1_known_axes_freeze.py`、`test_update_acceptance_duration_ledger.py`、`test_auditor_gate.py`、`test_floor_pair_driver.py` |

主要な参照アンカーは、B4 closed critic の `:617`、raw producer の `:33`、namespace の `:416`、job contract の `:11`、codex agents の `:57`、campaign の `:5397`。

検索結果のうち、焦点集合から除くもの：

- `test_pytest_collection_config.py`：`:368`〜`:403` で repository の既定全 suite を子 pytest の `--collect-only` に渡す。今回の条件を検証する consumer ではなく、焦点走が全体 collection へ膨らむため除外。
- `test_real_repo_serialization.py`：collection subprocess（`:1035`）や consumer test の import（`:2912`）を含むメタテスト。今回の main 条件への直接検出力がなく、焦点走から除外する。
- `conftest.py`：共通 fixture・登録情報。通常の test target として指定しない。
- `s1_expected_goldens.py`、`acceptance_duration_ledger.json`：補助データであり test file ではない。

確認した入れ子経路は collection を含む。これを「全 suite のテスト本体を再実行する」とは言い換えない。上記の除外は今回の焦点走だけで、親の受入全走の恒久除外は提案しない。

親の実走は `tools/run_tests.py` 経由とする。変異用6 node 集合と、この consumer 集合は分けて扱う。

## docs の要否

**driver の条件を示す1行の追記が必要。親が編集する。**

`docs/phase3-s4b-runbook.md:43` の K2 manifest 説明直後に、次を追記する。

> driver の `--run-iteration` 経路では、`--knowledge-manifest` の `sources` が非空なら `--coder-role coder-v4-autonomous-k2` が必須で、空取得 (`sources: []` / `completed_empty`) は従来どおり role 省略を許す (D1878)。

`tools/pegasus/README.md:359`〜`:371` は job body の契約と転送 argv を記述しており、今回も正しい。ここへの追記は不要。job body の env 対（`p3_s4_loop_pegasus.sh:60`〜`:96`）は変更しない。

## 親 brief への反論・疑義

1. **P1 の run guard だけでは emit 不変性を満たさない。** 両オプションを argparse が許し、emit を先に処理する現物に合わせ、`not a.emit_planner_context` を加える。
2. **P4 の M3→`:7241` は成立しない。** 空 sources のため role 条件まで進まない。非空＋role K2 の新正例で殺す。
3. **P4 の M5 は guard 補正に合わせて再照準が必要。** run 条件だけの削除を I の kill と事前登録しない。
4. **P5 の修正は必要。** 「既存正例無変更」を identity テスト後半まで文字通り適用すると D1878 と矛盾する。目的を維持する argv 補正を採用し、空取得の既存正例2本は無変更とする。

追加裁定や scope 拡張を必要とする疑義はない。

## 総括

manifest 解決直後に、実際に run 経路へ進む「非空 sources＋role 無し」だけを `ValueError` で拒否する。receipt 作成前に止め、loader・manifest parser・job body は変更しない。

テストは負例、非空＋role K2 正例、emit 優先順位の正例を追加し、既存 identity テストの後半 argv だけ補正する。変異5件と焦点集合を上記のとおり事前登録する。実装・pytest・変異実走は未実施。