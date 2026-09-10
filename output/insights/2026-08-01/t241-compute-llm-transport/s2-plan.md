指定資料はすべて読了した。以下は現行行番号基準の推奨 plan であり、実装・テスト実行は行っていない。

## 実装方針

transport 情報は raw Claude envelope や既存の frozen `agent_provenance` へ混ぜず、次へ記録する。

| 経路 | record / field | 記録内容 |
|---|---|---|
| 8b | journal `run_header.transport_env_keys` | 実際に subprocess へ渡した proxy key 名の昇順 list |
| 8c | `role-attempt.transport_env_keys` | valid / invalid 両 attempt で同じ list |
| 8c report | `cells[].generations[].roles[]` | 上記 attempt event がそのまま射影される |

値、URL、資格情報、値の SHA-256 は一切記録しない。SHA-256 も秘密由来の安定識別子・推測照合器になる一方、今回必要なのは「どの key を渡したか」だけだからである。

## file:line 実装計画

### 1. allowlist を base と transport に分離する

[s8b_prediction_runner.py:66](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/s8b_prediction_runner.py:66)〜70 を次の形にする。

```python
LEGACY_JOURNAL_SCHEMA_VERSION = "8b-prediction-journal/v1"
JOURNAL_SCHEMA_VERSION = "8b-prediction-journal/v2"

CLAUDE_BASE_ENV_ALLOWLIST = frozenset({
    "PATH", "HOME", "LANG", "LC_ALL", "TERM",
})
CLAUDE_TRANSPORT_ENV_ALLOWLIST = frozenset({
    "http_proxy", "https_proxy", "no_proxy",
    "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY",
})
CLAUDE_ENV_ALLOWLIST = (
    CLAUDE_BASE_ENV_ALLOWLIST | CLAUDE_TRANSPORT_ENV_ALLOWLIST
)
```

同じ場所に単一 projection helper を置く。

```python
def _project_claude_env(
    source_env: Mapping[str, str],
) -> tuple[dict[str, str], tuple[str, ...]]:
    projected = {
        key: source_env[key]
        for key in sorted(CLAUDE_ENV_ALLOWLIST)
        if key in source_env
    }
    transport_keys = tuple(
        key for key in sorted(CLAUDE_TRANSPORT_ENV_ALLOWLIST)
        if key in projected
    )
    return projected, transport_keys
```

`if key in source_env` とし、`source_env.get(key)` や既定値補充は使わない。これにより「不存在なら生成しない」「存在する空文字値もそのまま通す」が区別される。`ALL_PROXY/all_proxy` は P1 の受理集合外なので追加しない。

### 2. 8b provider と journal header を束縛する

[s8b_prediction_runner.py:141](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/s8b_prediction_runner.py:141) の `JournalBinding` に、JSON とは分離した immutable な

```python
transport_env_keys: tuple[str, ...] = ()
```

を追加する。`__post_init__` では「昇順・重複なし・全要素が `CLAUDE_TRANSPORT_ENV_ALLOWLIST` 内」を検査し、`header_values()` は v2 header に `list(self.transport_env_keys)` を出す。

[s8b_prediction_runner.py:1089](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/s8b_prediction_runner.py:1089)〜1092 は以下へ置換する。

```python
source_env = os.environ if environ is None else environ
self.env, self.transport_env_keys = _project_claude_env(source_env)
```

[s8b_prediction_runner.py:793](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/s8b_prediction_runner.py:793)〜798 では、既存の provider kind / role SHA 照合と並べて

```python
provider.transport_env_keys == binding.transport_env_keys
```

も要求する。これで header が宣言した key と実際の subprocess env が食い違う偽 provenance を拒否できる。

[s8b_prediction_runner.py:1441](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/s8b_prediction_runner.py:1441)〜1461 の production binding 構築では、provider 作成後に `transport_env_keys=provider.transport_env_keys` を渡す。

### 3. 8b journal schema を v1/v2 で exact に分ける

現行 `_HEADER_KEYS` は [s8b_prediction_runner.py:76](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/s8b_prediction_runner.py:76)〜80。次の二形へ分ける。

```python
_HEADER_KEYS_V1 = {現在の12 key}
_HEADER_KEYS_V2 = _HEADER_KEYS_V1 | {"transport_env_keys"}
```

[s8b_prediction_runner.py:338](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/s8b_prediction_runner.py:338)〜364 の `_validate_header_schema()` は、

- schema=v1 なら `_HEADER_KEYS_V1` と exact 一致
- schema=v2 なら `_HEADER_KEYS_V2` と exact 一致し、transport list も検査
- v1+新 field、v2−新 field、future schema はすべて拒否

とする。

[s8b_prediction_runner.py:367](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/s8b_prediction_runner.py:367)〜374 の binding 照合では、既存 v1 header に限って schema と存在しない transport field の比較を省く。新規作成は常に v2、既存の tracked v1 journal は read-only compatibility として受理する。

以下は変えない。

- `_ENVELOPE_KEYS`: [s8b_prediction_runner.py:89](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/s8b_prediction_runner.py:89)
- `_INVOCATION_KEYS`: [s8b_prediction_runner.py:85](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/s8b_prediction_runner.py:85)
- raw envelope の保存・検査: [s8b_prediction_runner.py:1160](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/s8b_prediction_runner.py:1160)〜1215
- `ProviderResponse.provenance`: [s8b_prediction_runner.py:1219](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/s8b_prediction_runner.py:1219)〜1231

特に最後へ field を追加しない。そこへ追加すると [s8b_selector_freeze.py:88](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/s8b_selector_freeze.py:88)〜91 と [同:223](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/s8b_selector_freeze.py:223)〜252 の exact `agent_provenance` schema、さらに既存 frozen prediction bytes まで巻き込むためである。

### 4. projected provider へ同じ projection を波及させる

[claude_projected_provider.py:22](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/claude_projected_provider.py:22)〜31 で `_project_claude_env` を import する。

[claude_projected_provider.py:153](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/claude_projected_provider.py:153)〜157 は 8b と同じ二値代入へ置換する。

```python
source_env = os.environ if environ is None else environ
self.env, self.transport_env_keys = _project_claude_env(source_env)
```

[claude_projected_provider.py:269](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/claude_projected_provider.py:269)〜289 の response provenance には追加しない。invalid return 前にも記録する必要があるため、記録責務は次の driver 側へ置く。

### 5. 8c の valid / invalid attempt 双方へ記録する

[p3_autonomous_workload_trial.py:523](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/p3_autonomous_workload_trial.py:523)〜538 の `_invoke()` の `base` に次を追加する。

```python
"transport_env_keys": list(
    _validated_transport_env_keys(
        getattr(provider, "transport_env_keys", ())
    )
),
```

これにより、例外側の append [同:547](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/p3_autonomous_workload_trial.py:547)〜563 と成功側 [同:564](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/p3_autonomous_workload_trial.py:564)〜571 の双方へ入る。fixture/custom provider の属性欠落は空 list とする。

`AttemptJournal.append()` は [同:370](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/p3_autonomous_workload_trial.py:370)〜397 の generic event writer で、8b の `_HEADER_KEYS` 相当の exact key validatorを持たない。この wave で新たな包括 schema gate は作らず、追加 field の形は provider helper と焦点テストで固定する。

`SCHEMA_VERSION` は role payload [同:575](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/p3_autonomous_workload_trial.py:575)〜592 にも入るため bump しない。bump すると transport 修正だけのはずが role 文脈と payload SHA を変えてしまう。

### 6. 現行 runbook を同期する

[phase3-s8c-autonomous-trial-runbook.md:39](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/docs/phase3-s8c-autonomous-trial-runbook.md:39)〜44 を、base 5 key + present-only transport 6 key、key 名だけ記録、値非記録へ更新する。

同 runbook [§4:118](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/docs/phase3-s8c-autonomous-trial-runbook.md:118)〜121 の「invalid は path/SHA だけ」は、`transport_env_keys` も残る、と訂正する。

Pegasus §7.1 の network 記述修正は親 brief の S3 であり、今回指定された S1/S2 実装 plan には混ぜない。

## テスト変更と殺す変異

| テスト | 変更内容 | 殺す変異 |
|---|---|---|
| `test_claude_headless_argv_stdin_env_and_neutral_cwd` [現:525](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/tests/test_s8b_prediction_runner.py:525) | fixture env に6 proxy key、`ALL_PROXY`、secret を入れ、期待 mapping を base+6 の exact 値へ更新 | proxy 1 key の追加漏れ、`dict(source_env)` による secret/`ALL_PROXY` 漏洩を殺す |
| 新規 `test_claude_headless_transport_env_is_presence_based` | proxy 1個のみ、空文字 `NO_PROXY`、残り不存在を与え、存在2個だけ渡ることを検査 | `if source_env.get(key)` による空値脱落と、不存在 key の空値生成を殺す |
| 更新 `test_run_header_is_first_record_and_matches_binding` [現:143](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/tests/test_s8b_prediction_runner.py:143) | v2 と `transport_env_keys` の exact header を期待 | header への記録漏れ、値/map/hash の記録、field 名違いを殺す |
| 新規 `test_run_header_v1_compatibility_and_v2_exact_shape` | v1旧形とv2新形を正例、v1+field・v2−field・未知 key を負例にする | 既存 frozen v1 の破壊と、optional-anything に弱めた schema を殺す |
| 新規 `test_drive_rejects_transport_binding_mismatch` | provider の実 key と header binding を故意にずらす | 固定文字列を header に書くだけで実 subprocess env と束縛しない変異を殺す |
| `test_claude_headless_provenance_uses_envelope_measurements` [現:577](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/tests/test_s8b_prediction_runner.py:577) | exact response provenance 集合は従来どおり維持 | transport field を誤って frozen `agent_provenance` 経路へ混ぜる変異を殺す |
| `test_projected_provider_lowers_source_tools_and_binds_effective_prompt` [現:317](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/tests/test_p3_autonomous_workload_trial.py:317) | proxy大小文字・空値・secret を与え、env と `transport_env_keys` を exact 検査 | 共有 consumer が旧 base-only projection のまま残る変異と env 全継承を殺す |
| 新規 `test_role_attempt_records_transport_keys_when_valid` | valid `_invoke()` の返却 event と JSONL に同じ key list があることを検査 | provider 属性にはあるが journal/report へ永続化しない変異を殺す |
| 新規 `test_role_attempt_records_transport_keys_when_invalid_without_values` | credential 入り proxy URL + nonzero provider を使い、invalid event に key 名だけ残り URL は JSONL に現れないことを検査 | 成功時しか記録しない変異と proxy 値の漏洩を殺す |

既存 exact 検査 [test_s8b_prediction_runner.py:544](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/tests/test_s8b_prediction_runner.py:544)〜556 は削らず、入力側に全許可 key を用意したうえで union allowlist と exact 一致させる。

## 隔離契約が不変である根拠

| 契約 | 8b | projected/8c |
|---|---|---|
| runtime `tools=[]` | inline agent 構築 [s8b:1062](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/s8b_prediction_runner.py:1062)〜1068 | [projected:135](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/claude_projected_provider.py:135)〜142 |
| 空 MCP | [s8b:1078](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/s8b_prediction_runner.py:1078)〜1086 | [projected:144](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/claude_projected_provider.py:144)〜151 |
| setting sources 無効 | argv [s8b:1095](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/s8b_prediction_runner.py:1095)〜1107 | argv [projected:159](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/claude_projected_provider.py:159)〜178 |
| session 非永続 | `--no-session-persistence` [s8b:1107](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/s8b_prediction_runner.py:1107)、重複拒否 [同:1216](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/s8b_prediction_runner.py:1216)〜1218 | flag [projected:178](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/claude_projected_provider.py:178)、重複拒否 [同:231](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/claude_projected_provider.py:231)〜268 |

変更するのは subprocess の `env=` を作る箇所だけであり、inline agent JSON、argv、MCP bytes、cwd、session 検査には触れない。ただし、これは D106 が述べるとおり「構成が不変」という根拠であって、CLI process の能力を観測証明したという主張にはしない。

## S2 受入計画

親が Pegasus 計算ノードで runbook [§3.2:75](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/docs/phase3-s8c-autonomous-trial-runbook.md:75)〜82 の command を一意な trial id で実行する。

受入条件は次を機械的に数える。

- CLI rc=0、report `status=complete`
- workload 3件、各 generation 1件、各 outcome=`dry-pass`
- `role-attempt` が12件、全件 `status=valid`、`attempt=1`、`retry=false`
- 全12件の `transport_env_keys` がジョブ開始時に存在した許可 transport key 集合と一致し、少なくとも実測済みの `http_proxy` / `https_proxy` を含む
- journal に proxy URL・資格情報・値 hash がない
- fix 前対照は親の既存 artifact を保存し、再実行しない

関連 pytest、`check_codex_agents.py`、`check_docs.py` は親が `tools/run_tests.py` 経由で計算ノード実行する。本回答では一切実行しておらず、緑は主張しない。

## リスク

- lowercase/uppercase が同時に存在し値が異なる場合、実際にどちらを採用するかは Claude CLI/HTTP stack 依存である。key provenance だけでは経路の優先順位までは証明しない。
- `NO_PROXY/no_proxy` は値次第で proxy を迂回させる。P1 に従い素通しするが、存在の記録だけでは内容の妥当性を証明しない。
- 既存 v1 journal の resume では transport field が歴史的に存在しない。新規 v2 だけを「記録済み」と呼ぶ必要がある。
- 8c journal は key-closed schema を持たない。今回そこまで新設すると別の受理 gate になるため、焦点テスト以上の一般化はしない。
- S2 は projected provider の live 証拠であり、8b provider の Pegasus live E2E 証拠ではない。

## 親 brief の欠陥・過大表現

1. brief 37行目・85行目の「共有点1箇所」「provider 2本+そのテスト」は不足している。allowlist 定義は1箇所でも、projection は2箇所、durable provenance sink は8b headerと8c driverの2箇所である。
2. `ProviderResponse.provenance` へ単純追加する案は、`s8b_selector_freeze.py` の exact `_AGENT_PROVENANCE_KEYS` と frozen prediction を見落とす。本 plan はその経路を避ける。
3. P2 の値 SHA 候補は過剰である。資格情報入り URL の hash は秘匿値そのものではないが、安定相関子・推測照合器になる。
4. 「文脈・能力は1 bitも増えない」は字義上誤りである。外部到達能力は意図的に増える。正確には「role prompt、tools、MCP、settings、session 契約は増やさない」。
5. brief 62〜63行目の「8c/8b の全 role attempt が role-invalid」は不正確である。8c は各 cell の最初の planner invalid で止まるため通常は3件だけが attempt され、8b は provider 例外が journal の `role-invalid` invocation になるとは限らない。
6. S2 の live 受入は8cだけなので、「両 provider の live transport を証明した」とは言えない。
7. tracked journal は [test_frozen_artifacts.py:67](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/tests/test_frozen_artifacts.py:67) で bytes pin され、floor/ratified consumer も複数ある。brief に DW-O09 の live copy / frozen snapshot /歴史記録分類がない。親が段1前に処理していなければ、dispatcher 契約どおり段1へ巻き戻す必要がある。

## 総括

- allowlist は base 5 key と present-only transport 6 key に分離し、両 provider が同じ helper を使う。
- provenance は8b v2 `run_header` と8c全 `role-attempt`へ key名だけ記録し、値・hashは残さない。
- raw envelope、frozen `agent_provenance`、tools/MCP/settings/session 契約は変更しない。
- テストは未実行であり、unit/full/live 受入は親がPegasus計算ノードで行う。