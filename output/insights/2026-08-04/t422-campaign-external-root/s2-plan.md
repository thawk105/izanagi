# 段 2 実装プラン

静的読解だけで起草した。pytest・ビルド・実測は行っておらず、緑赤は主張しない。

## 1. 注入 seam

対象は [orchestrator/campaign/layout.py:323](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:323) の探索用 factory だけとする。

環境変数名は `IZANAGI_EXPLORATION_OUTPUT_ROOT` とする。値は `exploration/` 自体ではなく、既存の `output_root` 引数と同じ「base output root」を表す。したがって値が `/job-output` なら campaign root は `/job-output/exploration/campaigns/<id>` になる。

優先順位は次で固定する。

1. 非空の明示 `output_root`
2. `IZANAGI_EXPLORATION_OUTPUT_ROOT`
3. 現行の `repo_output_root()`

### layout.py の変更粒度

[layout.py:23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:23)

```diff
 import os
+import stat
 import tempfile
```

[layout.py:221](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:221) 付近へ private 定数を追加する。

```diff
+_EXPLORATION_OUTPUT_ROOT_ENV = "IZANAGI_EXPLORATION_OUTPUT_ROOT"
```

[layout.py:323](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:323) の factory 直前へ resolver を追加する。

```python
def _resolve_exploration_output_root(output_root: str = "") -> str:
    if output_root:
        return output_root

    configured = os.environ.get(_EXPLORATION_OUTPUT_ROOT_ENV)
    if configured is None:
        return repo_output_root()
    if configured == "":
        raise ValueError("IZANAGI_EXPLORATION_OUTPUT_ROOT が空")

    candidate = Path(configured)
    if not candidate.is_absolute():
        raise ValueError("... は絶対 path 必須")

    # anchor から存在する component を lstat。
    # symlink、途中の非 directory、既存 leaf の非 directory を拒否。
    # 最初の未作成 component 以降は layout.ensure() に作成を委ねる。
    ...

    resolved = candidate.resolve(strict=False)
    repository = Path(repo_output_root()).parent.resolve(strict=True)
    if resolved == repository or resolved.is_relative_to(repository):
        raise ValueError("... は repository 外でなければならない")
    return str(resolved)
```

検証契約は以下とする。

- 空文字は「未設定」と扱わず `ValueError`。shell 展開失敗から repo-local 既定へ黙って戻り、F98を再発させないため。
- 相対 path は拒否。cwd が異なる driver 間で root が分裂するのを防ぐ。
- 正規化後に現在の repository root と同一、またはその配下なら拒否する。`..` や symlink alias での迂回も許さない。
- env path の既存 component は、外部を指すものも含め symlink を拒否する。未作成の末尾 directory は許可する。
- env 由来だけを正規化して絶対 path として返す。
- 明示 `output_root` は resolver 冒頭でそのまま返す。相対 path・symlink を含む既存の明示引数契約は、この wave では変更しない。
- env 未設定時も `repo_output_root()` の文字列をそのまま返し、`resolve()` 等を掛けない。既定 path の文字列表現と生成 bytes を変えない。
- エラーは既存探索境界と同じ `ValueError` とし、directory 作成前に発生させる。

[layout.py:323-330](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:323) は次の一行だけを差し替える。

```diff
 def exploration_campaign_layout(campaign_id: str, output_root: str = ""):
     cid = _campaign_slug(campaign_id)
-    root = output_root or repo_output_root()
+    root = _resolve_exploration_output_root(output_root)
     return ExplorationCampaignLayout(
         root=os.path.join(root, "exploration", "campaigns", cid),
     )
```

factory の docstring に、優先順位と env が base root であることも明記する。

### 変更しない layout 契約

- [layout.py:37-43](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:37) `repo_output_root()` は不変。
- [layout.py:205-212](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:205) `_campaign_slug()` は factory で引き続き最初に通し、traversal 防御を変更しない。
- [layout.py:215-218](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:215) official `campaign_layout()` は env を参照しない。
- [layout.py:224-275](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:224) `ensure_exploration_namespace()` の body・引数意味論・exact bytes・marker symlink 拒否は不変。
- [layout.py:311-320](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:311) `ExplorationCampaignLayout.ensure()` は、自身の `root` から求めた namespace directory を明示して helper に渡す現行形を維持する。env をここでも読み直して二重に `exploration/` を付けない。
- 手組みした `ExplorationCampaignLayout` も、その root を env に上書きされない。

## 2. 呼び出し元の全棚卸し

production の `exploration_campaign_layout(...)` 直接呼び出しは19箇所。いずれも変更不要とする。

| 呼び出し元 | 現行箇所 | 変更 | env 設定時の検討 |
|---|---:|---|---|
| [loop.py:96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/loop.py:96) | 114-126 | 不要 | `campaign_namespace=="exploration"` のときだけ新 resolver へ到達。126行の明示 `output_root` は env に優先する。official 分岐は不変。 |
| [p3_kickoff.py:103](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/p3_kickoff.py:103) | 103-114 | 不要 | 2回の `run_campaign` と114行の WAL 読出し側が同じ env factory を使う。 |
| [p3_s4_loop.py:678](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/p3_s4_loop.py:678) | 678, 679-680, 803, 896, 926 | 不要 | 679行の `layout.root` 比較、713-716行の sink、803/896/926行の再導出がすべて同じ正規化済み env root。env がプロセス中に不変なら自壊しない。異なる root の明示注入は従来どおり build 時に拒否する。 |
| [p3_s4_loop_sort.py:231](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/p3_s4_loop_sort.py:231) | 231, 232-233, 320, 437, 476 | 不要 | backoff 版と同じ。249-252行の `run_campaign` も env rootへ到達し、比較両辺は一致する。 |
| [p3_s4_loop_trigger_gating.py:555](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/p3_s4_loop_trigger_gating.py:555) | 555, 556-557, 630, 767, 807 | 不要 | 555行の build 比較、630行の production 導出、767/807行の返却 root 再検算が同じ factory を使う。768/808行の `CampaignLayout(out["layout_root"])` は path wrapper として使うだけで official factory には戻らない。 |
| [p3_s4_red.py:150](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/p3_s4_red.py:150) | 150-167 | 不要 | 2 sink と167行の読出し layout が同じ env root。 |
| [p3_autonomous_workload_trial.py:1029](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/p3_autonomous_workload_trial.py:1029) | 1043, 1216-1222, 1268 | 不要 | build cell は1268行で env factory を使う。形は常に `<base>/exploration/campaigns/<id>` なので `campaign_root.parent.parent` は `<base>/exploration` のまま。複数 cell も同一 env base を共有し、1218行の集合検査を壊さない。env root は canonical に返すため `Path.resolve()` 後も一致する。 |
| [p3_autonomous_workload_trial.py:1583](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/p3_autonomous_workload_trial.py:1583) | 1589 | 不要 | autonomous trial 自身の `run_root` を明示して marker を作る別経路。env で上書きしない。 |
| [s8b_oracle_exploration.py:57](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/s8b_oracle_exploration.py:57) | 59, 75-77 | 不要 | 必須 `--output-root` が常に最優先。親 env が空・不正でも明示引数があれば env 検証へ入らない。 |
| [layout.py:315](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:315) | 315-316 | 不要 | 既に構築済み layout の namespace を明示するため、factory の選択結果を保持する。 |

`ExplorationCampaignLayout(...)` の production 直接構築は factory 内だけであり、factory を迂回する追加 consumer はない。

p3 driver の root 同一性は「すべて同一プロセスで同じ env を再読する」ことに依存する。runbook には campaign 起動前に一度設定し、実行中に変更しないことを明記する。root を各 driver に別引数で重複配線する変更は行わない。

## 3. layout 契約テスト

[orchestrator/tests/test_campaign.py:3587](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/tests/test_campaign.py:3587) の path 防御群へ、引数なしで動くテスト関数を2本追加する。これは同ファイルの素の Python runner 互換を保つためである。

1. `test_exploration_output_root_env_precedence_and_official_isolation`

   - env を退避・削除し、既定 root が現在と文字列単位で同じことを検査。
   - env に temp の絶対外部 root を設定し、`<env>/exploration/campaigns/<id>` になることを検査。
   - factory を複数回呼び、`root` と `parent.parent` が同一であることを固定。S4比較と autonomous逆導出の構造的回帰検知にする。
   - env を空文字にした状態でも、明示 `output_root` がそのまま勝つことを検査。
   - 同じ env 下で `campaign_layout()` は従来の repo `output/campaigns/<id>` のままであることを検査。
   - `finally` で親 env を exact に復元。

2. `test_exploration_output_root_env_rejects_unsafe_values`

   一つのテスト内で次を個別に factory へ与え、directory 未生成のまま `ValueError` になることを検査する。

   - 空文字
   - 相対 path
   - repository root とその配下
   - `..` 正規化後に repository 配下へ入る絶対 path
   - 外部 directory を指す symlink root
   - 中間 component が symlink の path
   - 既存の非 directory leaf

既存の以下の期待値は編集しない。

- [test_campaign.py:3270-3328](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/tests/test_campaign.py:3270) official既定と明示 exploration root
- [test_campaign.py:3601-3609](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/tests/test_campaign.py:3601) traversal拒否
- [test_campaign.py:3612-3662](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/tests/test_campaign.py:3612) marker先行、exact bytes、marker symlink拒否
- [test_p3_exploration_namespace.py:368](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/tests/test_p3_exploration_namespace.py:368) atomic publish/fsync/temp cleanup
- [test_s8b_oracle_artifacts.py:51](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/tests/test_s8b_oracle_artifacts.py:51) exploration factory の不正 slug 拒否

## 4. F98 再発検知

配置先は新規 layout test file ではなく、[orchestrator/tests/test_dev_wave_land.py:75](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/tests/test_dev_wave_land.py:75) とする。理由は、F98の受入条件が layout path だけでなく `_verify_wave_clean` の実際の判定だからである。

同ファイルの `_Repo` / `_repo`（75-169行）はそのまま再利用できる。temp main repo、linked wave worktree、git config、cleanup が既に揃っている。

### test fixture の最小補助

[test_dev_wave_land.py:26-34](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/tests/test_dev_wave_land.py:26) で `campaign.layout` を読み込む。

[test_dev_wave_land.py:163-169](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/tests/test_dev_wave_land.py:163) の後へ test-only context manager を置く。

- `layout.repo_output_root` を合成 wave の `<wave>/output` に一時束縛する。
- env の有無／値を一時設定する。
- `finally` で関数と env を完全復元する。
- `LAND._verify_wave_clean` や `tools/dev_wave_land.py` 自体は monkeypatch しない。

### 追加する正負2テスト

1. `test_exploration_external_root_keeps_wave_clean`

   - `_repo()` で temp main + wave を構築。
   - external root は temp repository群の外側にある sibling directoryとし、機械固有 pathを使わない。
   - `IZANAGI_EXPLORATION_OUTPUT_ROOT` をその絶対 path に設定。
   - `exploration_campaign_layout("f98-env").ensure()` を実行。
   - root が wave 外で、marker bytes が `b'{"namespace":"exploration"}\n'`、campaign directory が external root 配下であることを検査。
   - `git status --porcelain=v1 --untracked-files=all` が空であることを検査。
   - `LAND._verify_repository(...)` で得た repository に `LAND._verify_wave_clean(...)` を直接当て、例外なしを正例とする。descriptor は `finally` で close。

2. `test_exploration_default_root_makes_wave_dirty`

   - 別の `_repo()` を使い、env を削除。
   - 同じ factory の引数省略で `<wave>/output/exploration/...` が作られることを検査。
   - status に `output/` の untracked record が存在することを確認。
   - `LAND._verify_wave_clean(...)` が `LAND._Reject`、`rc == LAND.RC_DIRT`、理由が `wave worktree must be completely clean` であることを対照として固定。

両テストとも合成 temp repo 全体を fixture cleanup に任せる。実 wave の `output/` を作らず、防護対象の削除も行わない。

## 5. 親 env による既存テスト汚染の防止

[orchestrator/tests/conftest.py:107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/tests/conftest.py:107) の task-run env fixtureとは分離し、その直後へ次を追加する。

```python
@pytest.fixture(autouse=True)
def _isolate_exploration_output_root_env(monkeypatch):
    monkeypatch.delenv("IZANAGI_EXPLORATION_OUTPUT_ROOT", raising=False)
```

必要性は高い。campaign jobから pytest を起動した場合、親 env が残ると「既定 root」を検査する既存テストや subprocess が外部 root を観測し、期待値を変更していないのに結果だけ変わるためである。

- 新しい env テストは autouse fixture 実行後に自分で `setenv` する。
- subprocess test は、明示的に上書きしない限り削除済み env を継承する。
- `test_campaign.py` と `test_dev_wave_land.py` の素の Python runner は conftest を通らないため、新規テスト自身でも env を退避・復元する。
- 既存テストの assertion、fixture output、凍結 bytes、pin は変更しない。

## 6. docs の最小変更

### 出力契約

[docs/orchestrator-design.md:110](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/docs/orchestrator-design.md:110) の exploration namespace 説明へ短い段落を追加する。

- 記載中の `output/exploration/...` は env 未設定時の既定であること。
- 探索用 factory だけが `明示 output_root > IZANAGI_EXPLORATION_OUTPUT_ROOT > repo output` を使うこと。
- official `CampaignLayout`、env scope、既存成果物の所在は変わらないこと。
- env は絶対・非空・repository 外・symlink componentなしであること。

### 運用

[docs/pegasus-runbook.md:581](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/docs/pegasus-runbook.md:581) の「8. 投入前チェックリスト」、campaign 項目の直前へ追加する。

- wave worktree から exploration campaign を起動する job は、job専用の `/work` 配下を `IZANAGI_EXPLORATION_OUTPUT_ROOT` に設定する。
- 実 path は job script が scheduler/job情報から組み立て、shared code・test・docsへ固定値を書かない。
- campaign process 起動前に一度だけ設定し、実行中に変更しない。
- env 未設定は後方互換用の repo-local 既定であり、waveでの実 campaignには使わない。
- 既存の明示 `--output-root` は env に優先する。

`output/README.md`、decisions、failures の既存契約は変更しない。F98の経緯は既に failures にあり、重複記載しない。

## 7. 実装後の検査計画

本 read-only 段では実行しない。親が実装後、Pegasusなら計算ノードへ dispatchして次を行う。

- `python3 -m py_compile orchestrator/campaign/layout.py`
- 焦点テスト:
  - `orchestrator/tests/test_campaign.py`
  - `orchestrator/tests/test_dev_wave_land.py`
- caller波及:
  - `test_p3_exploration_namespace.py`
  - `test_p3_s4_loop.py`
  - `test_p3_s4_loop_sort.py`
  - `test_p3_s4_loop_trigger_gating.py`
  - `test_p3_autonomous_workload_trial.py`
  - `test_s8b_oracle_artifacts.py`
  - `test_s8b_oracle_report.py`
- repository必須検査:
  - `python3 tools/check_codex_agents.py`
  - `python3 tools/check_docs.py`

変異観点は、env lookup除去、優先順位反転、空文字fallback、repo containment除去、symlink許可、official経路へのenv誤適用、env未設定でも外部化する変更をそれぞれ新規4テストで検出できることを確認する。

## 8. 実装しない範囲

- `hooks/` 全体、特に `hooks/guard_bash.py`
- `tools/dev_wave_land.py` と `_verify_wave_clean`
- `orchestrator/campaign/durable_root.py`
- `default_durable_root_policy()`、`authorize_output_root()`、capability経路
- official `CampaignLayout` / `campaign_layout`
- `repo_output_root()`、`env_scope_dir()`
- `ensure_exploration_namespace()` の marker exact-bytes／symlink拒否契約
- 各 driver への新規 CLI flag
- 既存 `output/exploration` 成果物の移動・削除・再生成
- 具体的な機械/job pathのコード・テスト・docsへの埋め込み
- guardまたはlandを緩和する代替案

## 総括

- 変更ファイル数: 6ファイル、すべて既存ファイル
  - production code 1
  - tests 3
  - docs 2
- 新規テスト数: 4関数
  - env/layout契約 2
  - F98正負対照 2
- リスク上位3点:
  1. 親 env 漏洩や実行中の env 変更による root 分裂。autouse隔離、優先順位テスト、runbookの不変運用で抑える。
  2. env root検証後からdirectory作成までのsymlink TOCTOU。既存component拒否とjob専用root運用で縮小するが、durable capability化は明示的にscope外。
  3. S4の再導出比較やautonomousの `parent.parent` 逆導出との不一致。同一factoryへの集約とroot形状テストで固定する。