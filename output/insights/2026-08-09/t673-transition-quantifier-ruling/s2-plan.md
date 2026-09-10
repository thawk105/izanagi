# 段 2 実行プラン

条件付き GO。HEAD は brief 記載どおり `4be7a362cb4186995803593ad767b5f8cc84349d`、作業木は静的確認時点で clean だった。pytest、mutation harness は実走しておらず、以下の KILLED / SURVIVED はすべて事前登録する期待値である。

計画上、親 brief へ二点補正が必要になる。

- brief の `N={1,2,3,4,8,64}` だけでは、M=64 の候補について frontier は `8 < frontier < 64` としか実測できない。正確な境界には `N=63` を追加する。
- 現行 spec schema は期待結果も spec 内に固定するため、同一 bytes の spec で A の SURVIVED が B/C では KILLED、という改善を KILLED と分類できない。同一 replacement core を hash 照合し、option 別 expectation spec を作る必要がある。

## 1. 量化点の棚卸し

### 1.1 `_validate_activation_transition` 内

対象は [`env_contract_activation.py:257`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/orchestrator/campaign/env_contract_activation.py:257)〜`:329`。

| site | 量化・集合操作 | `[:N]` で意味が変わる条件 |
|---|---|---|
| `:264` | 全 `predecessor_rows` から env→row 写像を作る | M>N でこの側だけを切ると `:268` の key 不一致になり、元は受理する遷移を拒否する。fail-open には両写像や後続 loop も同時に切る multi-site 変異が必要 |
| `:265` | 全 `successor_rows` から env→row 写像を作る | 同上。単独 truncation は主に過剰拒否 |
| `:268` | 両 key 集合の exact equality | prefix が一致し suffix だけ異なる入力を prefix 比較へ変えれば不一致を見逃す。ただし public caller の `:378-383` が各 record を catalog と exact 照合するため production では前段に mask される |
| `:275-291` | 全 successor env の同一性、exactly +1 を検査し `changed` を作る | M>N かつ、先頭 N に少なくとも一つ正当な +1、未走査 suffix に downgrade/skip/hash substitution があると false accept。逆に先頭 N が全据置で suffix だけが正当に変わると `:293` で false reject |
| `:293-297` | `changed` 非空という存在量化 | 独立した slice anchor はない。`:275` の truncation により存在判定の母集合が縮む |
| `:300-324` | 全 changed env に successor predicate を適用 | `len(changed)>N`、先頭 N が exact `True`、suffix に `False`・非 bool・通常例外があれば false accept。先頭側で既に失敗する fixture では受否は変わらず、呼出列や診断だけが変わる |
| `:325-329` | callback failure が一つ以上あったか | 独立 anchor はなく、`:300` の全件走査に従属 |

結論は次のとおり。

- 「遷移規則を各 env に適用する、単一行の `for ... in collection` truncation anchor」は `:275` と `:300` の二点で尽きる。brief の二点はこの限定では完全。
- 「関数内の集合上の量化」全般なら、`:264`、`:265`、`:268`、`:293`、`:325` も存在する。したがって「量化は二つしかない」と一般化してはならない。

### 1.2 直接 caller と前処理

[`validate_activation_records:332`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/orchestrator/campaign/env_contract_activation.py:332) は対象 gate より前に次を全件検査する。

| site | 量化 | truncation 条件・本 wave での扱い |
|---|---|---|
| `:238-253` | 全 registered env と全 generation pair | catalog prefix 化は M>N の正当入力を未登録扱いにする。別 gate の過剰拒否族なので本 spec 外 |
| `:351-358` | 全 record の pair shape、filename 重複 | `any(... raw_records[:N])` 単独では後段が全 record を読むため、主に診断変化 |
| `:365-405` | 全 record edge を順に検査 | `ordered[:N]` は、expected head が prefix を指し suffix record が存在する fixture なら、元の head mismatch を消して false accept し得る。record 軸の別 truncation 族 |
| `:378-383` | 各 record の env 集合と catalog の exact equality | rows prefix 化は通常 M>N の正当 record を拒否する |
| `:384-394` | 全 env の generation/hash catalog 照合 | suffix の不正 pair が後段の transition と ever-active 包含を通る fixtureなら false accept し得る。env transition とは別の registry gate |
| `:466-475` | directory の全 entry | `entries[:N]` は正しい pinned prefix の後ろにある不正な extra entry を無視し得る |

production caller は [`env_contract.py:524`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/orchestrator/campaign/env_contract.py:524)、issuer は [`issue_env_contract_activation.py:206`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/tools/issue_env_contract_activation.py:206) から同じ gate を呼ぶ。遷移判定の重複実装はない。

これら caller 側の別量化族は棚卸しには残すが、今回の mutation spec へ混ぜない。混ぜると A/B/C の比較対象が「二つの遷移述語」から逸脱する。

## 2. mutation spec 設計

### 2.1 schema と固定値

[`mutation_harness.py:193-319`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/tools/mutation_harness.py:193) に従い、各 spec は次を持つ。

```json
{
  "schema": "izanagi-dev-wave-mutation-spec/v1",
  "estimated_run_seconds": 60,
  "timeout_seconds": 3600,
  "hang_timeout_seconds": 600,
  "mutations": []
}
```

全 mutant は以下で共通とする。

- `category`: `"negative"`
- `hang_risk`: `false`
- `file`: `"orchestrator/campaign/env_contract_activation.py"`
- old anchor は HEAD 上で各 exactly one、静的 count は双方 `1`
- base spec は brief どおり十二件。frontier 確定版は `N=63` 二件を加えた十四件

### 2.2 replacements の逐語

量化点 G、[`env_contract_activation.py:275`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/orchestrator/campaign/env_contract_activation.py:275):

```json
"old": "    for successor in successor_rows:\n"
```

各 `N` の new:

```json
"new": "    for successor in successor_rows[:N]:\n"
```

量化点 P、[`env_contract_activation.py:300`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/orchestrator/campaign/env_contract_activation.py:300):

```json
"old": "    for predecessor, successor in changed:\n"
```

各 `N` の new:

```json
"new": "    for predecessor, successor in changed[:N]:\n"
```

`N` は base `{1,2,3,4,8,64}`、境界拡張では `{1,2,3,4,8,63,64}`。

### 2.3 現状 A の expected status / nodes

略号は次の exact nodeid とする。

- `D4`: `orchestrator/tests/test_env_contract_activation.py::test_transition_rejects_fourth_env_downgrade`
- `P2`: `...::test_transition_rejects_when_second_changed_env_successor_is_false`
- `P3`: `...::test_transition_rejects_when_third_changed_env_successor_is_false`
- `P4`: `...::test_transition_rejects_when_fourth_changed_env_successor_is_false`

| mutant | expected_status | expected_nodes |
|---|---|---|
| `G-N1` | `KILLED` | `[D4]` |
| `G-N2` | `KILLED` | `[D4]` |
| `G-N3` | `KILLED` | `[D4]` |
| `G-N4` | `SURVIVED` | `[]` |
| `G-N8` | `SURVIVED` | `[]` |
| `G-N63`（境界拡張） | `SURVIVED` | `[]` |
| `G-N64` | `SURVIVED` | `[]` |
| `P-N1` | `KILLED` | `[P2, P3, P4]` |
| `P-N2` | `KILLED` | `[P3, P4]` |
| `P-N3` | `KILLED` | `[P4]` |
| `P-N4` | `SURVIVED` | `[]` |
| `P-N8` | `SURVIVED` | `[]` |
| `P-N63`（境界拡張） | `SURVIVED` | `[]` |
| `P-N64` | `SURVIVED` | `[]` |

これは current fixture の最大 M=4、[`test_env_contract_activation.py:59-70`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/orchestrator/tests/test_env_contract_activation.py:59) と、tail witness `:571-586`、`:921-990` に対応する。

docstring の「N >= 5」(`:554-556`) は「最初に未検査になる env の一基準位置」を指す。slice bound としては `[:4]` が既に生存するため、frontier は KILLED through `N=3` / SURVIVED from `N=4`。

### 2.4 runner scope

A の mutation runner は上の四 node だけを指定する。これにより診断 call-count 由来の赤を混ぜず、受理集合が変わる semantic kill に絞れる。

この scope は frontier を取りこぼさない。

- G は D4 一件で `N=1,2,3` を全て殺す。
- P は suffix 位置 2、3、4 の三件で各境界を殺す。
- ファイル全体に五 env 以上の catalog/fixture はないため、現状の `N>=4` survivor を殺す別 node は存在しない。
- harness 自身も collection 時に全 `expected_nodes` の実在を検査する (`mutation_harness.py:945-986`)。

ファイル全体を runner target にすると G-N1 などで別の正例・診断 node も赤くなり、上記 expectation は `MISMATCH` になる。その場合は「追加 coverage」として別 ledger にし、この focused spec を流用しない。

### 2.5 「同一 spec」制約の解決

厳密に同一 bytes の spec は使えない。

- `SURVIVED` expectation は `expected_nodes=[]` が必須 (`mutation_harness.py:269-274`)。
- candidate が同じ mutant を殺して赤 node を出しても、harness は実測 failures と空集合が一致しないため `MISMATCH` とする (`:1177-1193`)。

したがって次の形にする。

1. `mutation-core.json` 相当の比較用 digestとして、各 mutation の `(id, category, replacements, hang_risk)` を正規化 hash する。
2. A/B1/B2/C-AST/C-bytecode ごとに schema-valid な expectation spec を作る。
3. 全 option で core hash が一致しなければ比較を停止する。
4. exact-byte 同一 spec を強制する裁定なら、新規 kill は `MISMATCH` としか記録できない。これを KILLED と読み替えてはならない。

## 3. 候補テスト

### 3.1 共通の配置と測定用 materialize

逐語原本は次に置く。

```text
/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t673-transition-pbt-package/probes/
  test_t673_b1.py
  test_t673_b2.py
  test_t673_c_ast.py
  test_t673_c_bytecode.py
```

mutation harness は runner target を固定 HEAD の tracked file に限定し (`mutation_harness.py:543-582`)、untracked file も拒否する (`:360-372`)。したがって repo 外原本を直接 mutation runner に渡せない。

測定時だけ、各 alternative を使い捨て branch/commit の

```text
orchestrator/tests/test_t673_transition_probe.py
```

へ同一 bytes で載せる。commit は測定専用で land 対象外とし、前後の SHA-256 を照合する。本番ファイルと既存 `test_env_contract_activation.py` はその commit でも不変にする。

insights には `.py` を置かず、既往の運用どおり fenced code block と SHA-256 で逐語凍結する。先例は `worklog-phase3-0808-318.md:47-50`。

### 3.2 B1: stdlib の決定的生成テスト

計画行割り:

- `test_t673_b1.py:1-15`: imports と既存 helper
- `:16-35`: `_catalog(env_count)` と hash 生成
- `:36-65`: G/P の parameterized detector
- `:66-95`: cost-only profile

再利用する既存面:

- `_chain`: [`test_env_contract_activation.py:130-154`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/orchestrator/tests/test_env_contract_activation.py:130)
- `_validate`: `:157-170`
- `activation` / `REPO_ROOT`: `:26-34`
- `CATALOG`、`THREE_ENV_CATALOG`、`FOUR_ENV_CATALOG`: `:59-70` は A の比較に使うが、可変 M には使わない
- `_is_synthetic_successor`: `:73-89` は env-a/b に hard-code されているため M>2 では再利用しない

既存 helper は変更不要である。`_chain` は既に任意 `registered_contracts` を受け、catalog から env 数と hash を導く。probe 内だけで以下を一般化する。

- env tag は `env-000` のような zero-pad slug とし、sort 順と tail を固定
- generation 1/2 の hash は `sha256(f"{env_tag}:g{generation}")`
- M は `(1,2,4,8,16,32,64)`
- G fixture: 先頭 M−1 は `g1→g2`、末尾だけ `g2→g1`、predicate は常時 `True`
- P fixture: 全 env `g1→g2`、predicate は末尾 env だけ `False`
- parameter id は明示的に `M1`、`M2`、…、`M64`

B1 expectation は、G/P とも `M>N` の parameter node 全てが赤になる。

| N | candidate expected nodes の M suffix |
|---:|---|
| 1 | `M2,M4,M8,M16,M32,M64` |
| 2 | `M4,M8,M16,M32,M64` |
| 3 | `M4,M8,M16,M32,M64` |
| 4 | `M8,M16,M32,M64` |
| 8 | `M16,M32,M64` |
| 63 | `M64` |
| 64 | `[]` / `SURVIVED` |

したがって B1 は N=63 まで殺し、N=64 以上の残穴を残す。

### 3.3 B2: Hypothesis

計画行割り:

- `test_t673_b2.py:1-20`: B1 と同じ helper import/catalog factory
- `:21-45`: G property
- `:46-70`: P property
- `:71-95`: cost/statistics 補助

各 property は一つの pytest node とし、次を固定する。

```python
@given(env_count=st.integers(min_value=1, max_value=64))
@example(env_count=64)
@settings(
    max_examples=64,
    derandomize=True,
    database=None,
    deadline=None,
)
```

`@example(64)` は boundary を必ず通すために必要であり、database の replay を correctness 根拠にしない。`derandomize=True` の列は Hypothesis、Python、test function の変更で変わり得るため、三者の version/hash を台帳に残す。[Hypothesis の現行 settings / `@example` 契約](https://hypothesis.readthedocs.io/en/latest/settings.html)

B2 expectation:

- N=1,2,3,4,8,63: respective G/P property node が一件ずつ `KILLED`
- N=64: `SURVIVED`, `expected_nodes=[]`

B2 も残穴は消さず `N>=64` へ移す。

静的確認では現環境の `find_spec("hypothesis")` は `None`。B2 は repo 外 venv に version と wheel hash を固定して測る。依存を用意できなければ B2 は「未測定」とし、結果を補完・推測しない。

### 3.4 別ファイルとして成立するか

成立する。測定 commit 上では sibling import を使う。

```python
from test_env_contract_activation import _chain, _validate, activation, REPO_ROOT
```

既存テスト自身にも sibling import の先例がある (`test_env_contract_activation.py:1574`)。private helper だけを明示 import し、`test_*` 関数を import しないため重複 collection も避けられる。

障害は Python import ではなく、harness の tracked/fixed-HEAD 制約だけである。これは使い捨て測定 commit で解消する。

## 4. 測定プロトコル

### 4.1 検出力

各量化点について次を記録する。

- mutation core hash
- 各 N の `status`、`failed_nodes`、`duration_s`
- `largest_killed_N`
- `smallest_survived_N`
- 未測定区間があれば bracket として表示し、exact frontier と書かない

期待 frontier:

| option | G | P | 残穴 |
|---|---|---|---|
| A | KILLED ≤3 / SURVIVED ≥4 | 同左 | slice bound `N>=4` |
| B1 | KILLED ≤63 / SURVIVED ≥64 | 同左 | `N>=64` |
| B2 | KILLED ≤63 / SURVIVED ≥64 | 同左 | `N>=64` |
| C-AST | 登録した全 N を KILLED | 同左 | literal `[:N]` 族は構造検査で排除。別構文の truncation は残る |
| C-bytecode | 同上 | 同上 | Python/compiler と別構文への限定あり |

### 4.2 コスト

数値は次を取る。

- focal test: compute job stdout の pytest session 秒
- dispatch 込み: harness ledger の `duration_s`
- M 伸長: M=`1,2,4,8,16,32,64` の `_chain+_validate` を同一 batch 数で測った median ns/op と p95
- B2: Hypothesis 実行 example 数、property node 秒、package/version/wheel hash
- LOC: `wc -l` の全 probe 行数と detector-only 行数
- dependency: 新規 package 数、tracked declaration file 数
- 保守負荷:
  - import する private helper 数
  - pin する production identifier/opcode 数
  - 意味保存 refactor 三件中、候補 test が拒否する件数
  - Python/Hypothesis version 更新で再測定が必要か

M の理論計算量を先に「線形」と決めない。`_chain` は `sorted(registered_contracts)` (`test_env_contract_activation.py:136`)、production validation も `sorted(env_tags)` (`env_contract_activation.py:227`) を含むため、厳密には O(M log M) の面がある。実測は `a+bM` と `a+bM log₂M` の双方を当て、M≤64 の実用差を raw 値で返す。

### 4.3 親が実行する command

最初に queue を確認する。

```bash
python3 -m orchestrator.campaign.queue_state
```

A の focal run:

```bash
python3 tools/run_tests.py --force-dispatch \
  orchestrator/tests/test_env_contract_activation.py::test_transition_rejects_fourth_env_downgrade \
  orchestrator/tests/test_env_contract_activation.py::test_transition_rejects_when_second_changed_env_successor_is_false \
  orchestrator/tests/test_env_contract_activation.py::test_transition_rejects_when_third_changed_env_successor_is_false \
  orchestrator/tests/test_env_contract_activation.py::test_transition_rejects_when_fourth_changed_env_successor_is_false \
  -q -rf --durations=0
```

candidate focal run:

```bash
python3 tools/run_tests.py --force-dispatch \
  orchestrator/tests/test_t673_transition_probe.py \
  -q -rf -s --durations=0
```

A spec の preflight。`<spec-sha256>` は freeze 後の実値へ置換する。

```bash
python3 tools/mutation_harness.py \
  --repo /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package \
  --spec /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t673-transition-pbt-package/mutation-spec-A.json \
  --expected-spec-sha256 <spec-sha256> \
  --out /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t673-transition-pbt-package/mutation-ledger-A.json \
  --runner-mode dispatch \
  --plan-only \
  -- python3 tools/run_tests.py --force-dispatch \
  orchestrator/tests/test_env_contract_activation.py::test_transition_rejects_fourth_env_downgrade \
  orchestrator/tests/test_env_contract_activation.py::test_transition_rejects_when_second_changed_env_successor_is_false \
  orchestrator/tests/test_env_contract_activation.py::test_transition_rejects_when_third_changed_env_successor_is_false \
  orchestrator/tests/test_env_contract_activation.py::test_transition_rejects_when_fourth_changed_env_successor_is_false \
  -q -rf
```

本走は外側時間上限のない detached 経路で、`--plan-only` を `--detached` に置換する。

```bash
nohup setsid python3 tools/mutation_harness.py \
  --repo <dedicated-clean-measurement-worktree> \
  --spec <repo-outside-option-spec> \
  --expected-spec-sha256 <spec-sha256> \
  --out <repo-outside-option-ledger> \
  --runner-mode dispatch \
  --detached \
  -- python3 tools/run_tests.py --force-dispatch \
  orchestrator/tests/test_t673_transition_probe.py::test_generation_quantifier \
  orchestrator/tests/test_t673_transition_probe.py::test_successor_quantifier \
  -q -rf \
  > <repo-outside-option-log> 2>&1 < /dev/null &
```

実際には共有 wave worktreeを一時変異しないよう、固定 commit の [`tools/mutation_worktree.py`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/tools/mutation_worktree.py:1) を外側に使うのを推奨する。その wrapper が上と同じ実引数で harness を起動する。

B2 は harness 自身と runner の Python executable が一致する必要がある (`mutation_harness.py:439-444`)。したがって両方を同じ repo 外 venv の Python で起動する。

`--runner-mode dispatch` だけでは不十分で、runner argv の `--force-dispatch` は必須 (`docs/pegasus-runbook.md:806-820`)。pytest を直接起動しない。

### 4.4 成果物と不変確認

各 option について凍結するもの:

- probe 逐語、SHA-256、LOC
- option spec と core hash
- plan-only log
- focal test stdout
- mutation ledger、wrapper receipt、dispatch evidence
- cost table
- benign-refactor sensitivity matrix
- Python / pytest / Hypothesis version

終了前に確認する。

- `orchestrator/campaign/**` は base HEAD と byte-identical
- `orchestrator/tests/test_env_contract_activation.py` は base HEAD と byte-identical
- candidate `.py` と測定専用 commit は land 集合外
- land 候補は insights と spool fragment だけ
- B2 が実行不能なら、その理由と未測定セルを残す

## 5. provisional 裁定 P1〜P4

| 前提 | 最小測定 | 判定可能性 |
|---|---|---|
| P1: 有限 B は残穴を移すだけ | A の N3/N4、B の N63/N64 | bounded M=64 の B1/B2 について確定可能。N63 KILLED・N64 SURVIVED なら確認。Hypothesis に上限を置かない場合も一走で生成される集合は有限なので、観測最大 M を必ず記録し、族全体消滅とは書かない |
| P2: 残穴を閉じるのは C だけ | B で N64 SURVIVED、C で N64 KILLED、neutral-refactor matrix | literal `[:N]` 族についてのみ確認可能。「全 truncation」を閉じたとは言えない。source-adaptive test も実質 C なので B の反例には数えない |
| P3: M cost は線形かつ無視可能 | M=1〜64 の geometric sweep、候補全体の pytest 秒 | strict linear は静的に既に疑義あり。実測で実用上小さいかは決まるが、「争点は依存だけ」とは runtime・LOC・保守負荷を見ずに確定できない |
| P4: Hypothesis は初の第三者 test dependency | tracked dependency file 検索、`find_spec`、B2 venv manifest | 宣言 file 不在と Hypothesis 未導入は再確認済み。一方 pytest と pytest-xdist は既存の第三者依存 (`test_env_contract_activation.py:23`, `run_tests.py:4-12`) なので「初の第三者依存」は反証。「初の tracked 依存宣言機構」なら成立し得る |

## 6. C の具体案

### C1: function-scoped AST invariant

`test_t673_c_ast.py` の計画:

- `:1-20`: source 読込と target `FunctionDef` の exactly-one 解決
- `:21-55`: target binding と iterator の検査
- `:56-80`: G/P の独立 node
- `:81-105`: store/break/dataflow の補強

検査内容:

- G loop target が `successor`、iterator が exact `ast.Name("successor_rows")`
- P loop target が `(predecessor, successor)`、iterator が exact `ast.Name("changed")`
- G body に exactly +1 比較と `changed.append` がある
- P bodyに `is_valid_registered_successor` call がある
- `Break`、iterator parameter の再束縛、`changed` の追加再束縛がない

評価:

- literal `[:N]` は N の大小に依存せず必ず `ast.Subscript` になり発火する。
- whitespace/comment 変更には耐える。
- variable rename、helper extraction、`tuple(changed)` のような意味保存 refactorには偽陽性。
- `islice` を helper 内に隠す、callback 自体を弱める等は射程外。dataflow 検査なしでは事前の prefix 再束縛が偽陰性になる。
- N=1 と N=64 の双方で test node が赤になることを mutation ledger で確認するため恒真ではない。

### C2: bytecode の direct-iterator invariant

`test_t673_c_bytecode.py` の計画:

- `:1-20`: mutated module の import と `dis.Bytecode`
- `:21-60`: source line 275/300 に対応する loop instruction の抽出
- `:61-85`: G/P の独立 node
- `:86-110`: Python version/opcode 記録

現行 Python 3.10 では元コードが双方 `LOAD_FAST → GET_ITER` であり、slice は `BUILD_SLICE → BINARY_SUBSCR` を挟む。各 loop について direct adjacency を要求する。

評価:

- source formatting/comment には耐える。
- literal slice は N に依存せず検出。
- Python/compiler version、`tuple(changed)` などの無害な wrapper で偽陽性。
- helper-based `islice` や先行再束縛は、`STORE_FAST` も検査しなければ偽陰性。
- AST より source syntax への依存は弱いが、runtime/compiler への依存は強い。

### 明示的に却下する C

- target function 内の `ast.For` が二個あることだけを assertする案: `changed[:N]` 後も For は二個なので一件も発火しない。対象変異に対して恒真で却下。
- source に `"for ... in changed"` という文字列があるだけを見る案: comment/docstring や inert loop で満たせるため却下。
- `expected = len(calls); assert len(calls) == expected`: 観測値から期待値を作る自己参照で恒真。却下。
- target function 全体の exact source/AST hash: 対象変異は殺すが、無関係な診断・rename・refactorもすべて拒否する。C1/C2 より偽陽性が大きく、採用候補から外す。
- 有限 M の call-count testだけで「全 N を閉じた」とする案: 現行 `test_successor_predicate_is_called_once_for_each_changed_env` (`:1085-1103`) と同じく、その M 以上は残るため却下。

## 総括

- 対象の truncation anchor は `:275` と `:300` の二点で完全だが、caller の別量化族まで二点とは言わない。
- A の事前登録 frontier は N≤3 KILLED / N≥4 SURVIVED。
- B1/B2 は M=64 なら N≤63 KILLED / N≥64 SURVIVEDで、残穴は消えない。
- exact frontier のため、brief の十二 mutant に N=63 二件を追加する。
- C は AST と bytecode の二案を測り、literal slice 検出力と refactor 偽陽性を同時に返す。
- 最大の不確実性は B2 の未導入依存と、C の refactor 維持費。
- 親の最初の一手は `python3 -m orchestrator.campaign.queue_state`。測定可能なら次に A の四 node focal runを `tools/run_tests.py --force-dispatch` で行う。