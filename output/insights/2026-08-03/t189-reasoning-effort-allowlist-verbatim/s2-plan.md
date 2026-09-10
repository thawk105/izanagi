# 実装プラン

結論は、`orchestrator/codex_roles/` に依存を持たない小モジュールを新設し、製品別の二つの順序付き tuple を正本にします。CLI 2 面は `argparse.choices`、worker spec/argv 面は既存の形検査後の集合検査で拒否します。

pytest は指示どおり実行しておらず、以下は静的調査に基づく plan です。

## 正本の置き場所と形

新規ファイルは `orchestrator/codex_roles/effort_levels.py` とします。

- [`events.py`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/codex_roles/events.py) は JSON/event 境界であり、値域 catalog を混ぜるのは不自然です。
- [`policy.py`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/codex_roles/policy.py) は role 入出力の semantic policy、[`spec.py:610`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/codex_roles/spec.py:610) は role manifest policy なので、製品 CLI capability の正本にはしません。
- `tools/dev_waves/schema.py` に置けば既存 import を使えますが、fake-only supervisor の wire schema が Codex CLI capability を所有する逆転になります。
- 新モジュールは逆 import を持たないため、依存は `tools/* → orchestrator.codex_roles.effort_levels` の一方向です。`codex_roles/__init__.py` が読む `spec` / `policy` 側から `tools/dev_waves` への import はなく、循環しません。
- `__init__.py` には再 export せず、3 consumer が leaf module を直接 importします。

全内容は次のとおりです。

```python
"""Izanagi が Claude/Codex CLI へ渡す effort 値の製品別許可リスト。"""
from __future__ import annotations

CLAUDE_EFFORTS: tuple[str, ...] = (
    "low",
    "medium",
    "high",
    "xhigh",
    "max",
)

CODEX_REASONING_EFFORTS: tuple[str, ...] = (
    "low",
    "medium",
    "high",
    "xhigh",
    "max",
)

__all__ = ["CLAUDE_EFFORTS", "CODEX_REASONING_EFFORTS"]
```

`frozenset` ではなく tuple にする理由は、5 要素の membership cost が無視でき、`argparse` の usage と `invalid choice` 診断の列挙順を決定的にできるためです。

単一集合でも現在の結果は同じですが、採りません。Claude の値域は M1、Codex は M3/M4 という別の根拠を持ち、Codex は既に model 差があります。二定数なら、将来 Codex 側だけを model capability に分解するとき Claude へ値を漏らしません。

model 別絞り込みは本 waveでは入れません。特に `gpt-5.4-mini` の `max` 拒否を今 map 化すると、未列挙 model の扱いと served-model attestation まで決める必要があります。今回は requested value の製品別 allowlist に限定し、`max` を保持、呼び出し実績のない `none` は含めません。

## 既存 role policy 集合

次の二箇所は変更しません。

- [`orchestrator/codex_roles/launcher.py:349-358`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/codex_roles/launcher.py:349) の `{low, medium, high, xhigh}`
- [`orchestrator/codex_roles/spec.py:602-621`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/codex_roles/spec.py:602) の `{medium, high}` と role 固有固定

いずれも capability 集合ではなく、role manifest の独立した policy subset です。`CODEX_REASONING_EFFORTS` へ直接置換すると、それぞれ `max`、または `low/xhigh/max` を許してしまい禁止された拡張になります。intersection/difference で導出してもローカル policy 宣言は残り、将来の capability 変更が role policy を暗黙変更するため採りません。

したがって、[`test_codex_agents.py:130-137`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/tests/test_codex_agents.py:130)、[`test_codex_agents.py:406-436`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/tests/test_codex_agents.py:406)、[`test_codex_role_runtime.py:468-480`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/tests/test_codex_role_runtime.py:468) の期待値変更もありません。

## 面 1: Codex worker launcher

対象は [`tools/codex_worker_launch.py:35-39`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/codex_worker_launch.py:35) と [`:2475`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/codex_worker_launch.py:2475) です。

1. E402 import 群へ `CODEX_REASONING_EFFORTS` を追加します。
2. parser を次に変更します。

```python
run.add_argument(
    "--reasoning",
    choices=CODEX_REASONING_EFFORTS,
    required=True,
)
```

3. `check-receipt --expect-reasoning` と [`_validate_receipt():1983-1985`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/codex_worker_launch.py:1983) は変更しません。過去 receipt の監査互換性まで本 wave の launch admission と同時に狭めないためです。

不正値は receipt を作らず rc=2 にします。`parse_args()` は [`main():2531-2532`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/codex_worker_launch.py:2531) で `_run()` より前に実行されます。launcher-error receipt は preflight 完了後、[`_run():1804-1823`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/codex_worker_launch.py:1804) の supervised/finalization 内部失敗を記録するものです。CLI 契約違反を attempt/launcher failure として記録しません。

## 面 2: dev-waves serve CLI

対象は [`tools/dev_waves/cli.py:14-36`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/dev_waves/cli.py:14) と [`:92`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/dev_waves/cli.py:92) です。

1. `CLAUDE_EFFORTS` を import します。
2. `serve.add_argument("--effort", choices=CLAUDE_EFFORTS, required=True)` にします。
3. `parse_server_profile()` や `SupervisorProfile` は scope 外として変更しません。新規 CLI 入力は面2、永続 worker spec の改竄・旧値は面3で止まります。

`parse_args()` の `SystemExit` は [`main():349-385`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/dev_waves/cli.py:349) の `DevWavesError` handler では捕捉されないため、不正値は argparse の rc=2 です。

## argparse の落とし方

| 方法 | rc | 診断 | receipt |
|---|---:|---|---|
| `choices=`（採用） | 2 | `argument --reasoning/--effort: invalid choice: 'none' (choose from ...)`。usage にも集合が出る | parse 前段なので作らない |
| `type=` + `ArgumentTypeError` | 2 | converter の任意文言。choices は usage に自動表示されない | 作らない |
| parse 後に `parser.error()` | 2 | `error: <独自文言>`。parser 宣言から値域が見えない | `_run` 前なら作らない |
| parse 後に domain 例外 | 面1は `NG:` 付き rc=2、面2は JSON 付き rc=1 | 同じ入力違反で CLI ごとに形式が割れる | 配置次第で launcher-error と混同しうる |

固定された小さい列挙、既存の `--sandbox` / `--profile` と同じ CLI 契約、決定的な help/診断という点から `choices=` を選びます。

## 面 3: worker spec と child argv

対象は [`tools/dev_waves/schema.py:801`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/dev_waves/schema.py:801)、[`:832-854`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/dev_waves/schema.py:832) です。

1. `CLAUDE_EFFORTS` を import します。
2. `parse_worker_spec()` は既存の `_required_string(..., _EFFORT_RE)` を先に実行し、その直後に membership を重ねます。

```python
effort = _required_string(item["effort"], _EFFORT_RE, label="effort")
if effort not in CLAUDE_EFFORTS:
    raise DevWavesError(
        ReasonCode.INVALID_ARGS,
        {"label": "effort", "kind": "unknown"},
    )
```

3. `validate_child_argv()` は既存の `model-effort` 形検査をそのまま残し、その次へ同じ membership エラーを追加します。

これにより、例えば `HIGH` は従来どおり形エラー、正規表現には通る `none` は値域エラーになります。

ReasonCode は既存の `INVALID_ARGS` を使います。`FLAG_UNAVAILABLE` は [`daemon.py:330-360`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/dev_waves/daemon.py:330) のような実行ファイル側 capability 欠落用であり、caller が渡した未知値には不適切です。`kind="unknown"` は profile・action・subtype の閉集合違反で既に使われている語彙です。生の不正値は detail に入れません。

新しい ReasonCode は作らないため、protocol の reason enum は不変です。また、[`receipt.py:106-121`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/dev_waves/receipt.py:106) は `schema_v{n}.json` の canonical bytes だけを hash します。次はすべて無変更です。

- `tools/dev_waves/schema_v1.json`
- `tools/dev_waves/schema_v2.json`
- [`test_dev_waves_receipt.py:383-390`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/tests/test_dev_waves_receipt.py:383) の凍結 hash
- Receipt dataclass と protocol frame
- ReasonCode enum

## 実装単位

親 brief の A/B/C をそのまま採ります。A を先行し、完了後に B/C を並列化します。

- 単位 A: `orchestrator/codex_roles/effort_levels.py`
- 単位 B: `tools/codex_worker_launch.py`、`orchestrator/tests/test_codex_worker_launch.py`
- 単位 C: `tools/dev_waves/cli.py`、`tools/dev_waves/schema.py`、`orchestrator/tests/test_dev_waves_cli.py`、`orchestrator/tests/test_dev_waves_schema.py`

`launcher.py` / `spec.py` を変更しないため A の所有は新しい leaf module だけです。全所有集合は素集合です。

## テスト計画

### 面 1

[`test_codex_worker_launch.py:332-440`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/tests/test_codex_worker_launch.py:332) の `_base_command` に `reasoning: str = "high"` を追加し、既存全テストの既定値は変えません。`_run_case` と fake Codex を再利用します。

[`test_positive_p1_normal_job_is_accepted():482`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/tests/test_codex_worker_launch.py:482) の直後へ追加します。

- 負例: `reasoning="none"`。subprocess rc=2、stderr に `invalid choice` と `--reasoning`、receipt・manifest・fake child PID が作られないことを確認。
- 正例: `reasoning="max"`。fake launch が rc=0、receipt が `outcome="accepted"` かつ `reasoning="max"` であることを確認。

### 面 2

[`test_dev_waves_cli.py:44-49`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/tests/test_dev_waves_cli.py:44) 付近に、全 required serve option を返す小さい `_serve_argv(effort)` helper を追加します。

[`test_serve_requires_every_absolute_cap_hook_and_model_allowlist():107`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/tests/test_dev_waves_cli.py:107) の後へ追加します。

- 負例: `effort="none"` を `build_parser().parse_args()` へ渡し、`SystemExit.code == 2` と `invalid choice` 診断を確認。
- 正例: `effort="max"` が parse され、`Namespace.effort == "max"` になることを確認。

### 面 3

[`test_dev_waves_schema.py:29-36`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/tests/test_dev_waves_schema.py:29) の `_expect_error` と [`_valid_argv():233-240`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/tests/test_dev_waves_schema.py:233) を再利用します。

[`test_manifest_and_worker_spec_boundaries_are_closed():288-316`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/tests/test_dev_waves_schema.py:288) の WorkerSpec 構築を `_valid_worker_spec(effort="high")` helper へ抽出し、既存期待値は変えません。その後へ次を追加します。

- 負例: `effort="none"` を worker spec と `--effort=none` argv の両方へ与え、各々 `INVALID_ARGS`、detail が `{"label":"effort","kind":"unknown"}` であることを確認。
- 正例: `effort="max"` の worker spec が round-trip し、`--effort=max` argv も `validate_child_argv()` を通ることを確認。
- P2 保護: `effort="HIGH"` は worker spec で従来の `kind="string"`、argv で従来の `kind="model-effort"` になることを確認し、形検査が allowlist より先であることを固定。

実装後の実測は親が計算ノードで上記3テストファイル、全体受入、`check_codex_agents.py`、`check_docs.py` を実行します。本 plan 作成時点ではテスト未実行です。

## 総括

- 採る設計: `orchestrator/codex_roles/effort_levels.py` に製品別の順序付き tuple 二定数を置き、model 別絞り込みは見送る。
- 実装単位 A: `{orchestrator/codex_roles/effort_levels.py}`。
- 実装単位 B: `{tools/codex_worker_launch.py, orchestrator/tests/test_codex_worker_launch.py}`。
- 実装単位 C: `{tools/dev_waves/cli.py, tools/dev_waves/schema.py, orchestrator/tests/test_dev_waves_cli.py, orchestrator/tests/test_dev_waves_schema.py}`。
- (P1改) 同意 — 同値でも製品ごとに根拠と将来の分岐軸が異なり、`max` を残して `none` を除外できる。
- (P2) 同意 — 形エラーと well-formed な未知値を別診断にし、既存診断を保持できる。
- (P3) 同意 — import を持たない新規 leaf module が依存方向・循環回避・テスト配置の点で最も自然。
- plan 実装時に既存テストで赤くなりうるもの: 無し。