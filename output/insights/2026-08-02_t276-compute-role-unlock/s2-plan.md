結論として、実装案は組めます。ただし親 brief のままでは「MITM を閉じた」「既存 CLI で計算ノード role が解禁された」の 2 点は主張できません。以下はその過大表現を除いた推奨 plan です。静的調査のみで、編集・pytest は行っていません。

## 段 4 で先に確定すべき修正

1. P3 は限定する必要があります。7 個の TLS 関連 env を拒否して保証できるのは「列挙した env override を child に入れない」ことまでです。固定 proxy が system trust store 上の CA で TLS interception できる場合、MITM は防げません。「proxy は CONNECT metadata しか見えない」は削除対象です。

2. 「既定挙動が 1 bit も変わらない」と P5 の「全 projected provenance に receipt」を同時には満たせません。本 plan は前者を優先し、`transport_receipt` は明示 opt-in 時だけ追加します。既定 direct 行には追加しません。

3. 現在の production caller は opt-in を渡しません。したがって本 scope のままでは API は解禁されても、`p3_autonomous_workload_trial --provider claude-headless` は引き続き proxy を落とします。実 CLI まで開くなら、段 4 で同 caller の明示 flag 配線を T-276 の追加 scope として裁定する必要があります。

## 1. 新 leaf の API と判定順序

新規 `orchestrator/campaign/claude_transport.py:1-190` は、campaign 内依存を `site_policy` だけに限定します。それ以外は `collections.abc`、`dataclasses`、`hashlib`、`json`、`os`、`pathlib`、`stat`、`urllib.parse` など stdlib のみです。

公開 API は次で固定します。

```python
class ClaudeTransportError(RuntimeError):
    ...

@dataclass(frozen=True)
class ClaudeTransportAdmission:
    transport_env: dict[str, str]
    receipt: dict[str, object]

TRANSPORT_POLICY_RELATIVE_PATH = PurePosixPath(
    "tools/pegasus/policies/transport_v1.json"
)

def admit_claude_transport(
    *,
    source_env: Mapping[str, str],
    repository_root: Path,
) -> ClaudeTransportAdmission:
    ...
```

- 成功時の `transport_env` は exact 2 key のみです。
- 契約、site、policy、env の全拒否は `ClaudeTransportError` に統一し、proxy の実値は例外文へ出しません。
- 部分的な env / receipt は返しません。
- public API に `site=` 注入引数は設けません。production は必ず `site_policy.current_site()` を読みます。

Fail-closed 順序は次のとおりです。

1. `source_env` が `Mapping`、`repository_root` が実 directory であることを検査。
2. `site_policy.current_site()` を 1 回だけ呼び、exact `PEGASUS_COMPUTE` 以外を即拒否。policy file はまだ読みません。
3. source env に次の 7 key が 1 個でも存在すれば、空文字でも拒否:
   `SSL_CERT_FILE`、`SSL_CERT_DIR`、`REQUESTS_CA_BUNDLE`、`CURL_CA_BUNDLE`、`NODE_EXTRA_CA_CERTS`、`NODE_TLS_REJECT_UNAUTHORIZED`、`SSLKEYLOGFILE`。
4. 未受理 proxy 名を拒否:
   `HTTP_PROXY`、`HTTPS_PROXY`、`NO_PROXY`、`ALL_PROXY`、`FTP_PROXY`、`no_proxy`、`all_proxy`、`ftp_proxy`。
5. fixed repo-relative policy pathを read-once。missing、symlink component、非 regular file、上限超過、read error は拒否。
6. UTF-8、duplicate key、NaN/Infinity、top-level exact keys、schema/site/mode、endpoint map の型と exact keys を検査。
7. source env に lowercase 2 key が双方存在し、`type(value) is str` で、policy 値と文字列 exact 一致することを検査。strip、case-fold、URL 正規化、末尾 slash 補完はしません。
8. exact 2 key の env と receipt を構築し、内部整合を確認して返します。

Policy URI は `http` scheme、明示 port、userinfo/query/fragment/control character なしを要求します。これは credential 入り URL を provenance に残さないためで、実値の正規化には使いません。

## 2. `claude_projected_provider.py` の変更ハンク

対象は現行の [imports:11-34](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/claude_projected_provider.py:11)、[constructor:95-106](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/claude_projected_provider.py:95)、[env projection:157-170](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/claude_projected_provider.py:157)、[provenance:297-317](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/claude_projected_provider.py:297) です。

- `__init__` の末尾へ keyword-only 引数
  `allow_pegasus_compute_transport: bool = False`
  を追加し、`type(value) is bool` を要求します。
- 現行の base env comprehension と `HOME` 検査は行単位で保持します。
- `False` の場合は leaf を呼ばず、site 判定も policy read もせず、`self.transport_receipt = None` とします。
- `True` の場合だけ leaf を呼び、返った exact 2 key を `self.env` へ追加します。
- [subprocess call:224-233](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/claude_projected_provider.py:224) は変更せず、最終的な `dict(self.env)` がそのまま `env=` へ入る構造を維持します。
- response provenance はまず現行 17 key を同じ形で組み、opt-in 時だけ
  `provenance["transport_receipt"] = ...`
  を追加します。既定時の key 集合も不変です。

[`CLAUDE_ENV_ALLOWLIST`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/s8b_prediction_runner.py:71)、[`ClaudeHeadlessProvider` の env projection](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/s8b_prediction_runner.py:1153)、[その 8-key provenance producer](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/s8b_prediction_runner.py:1303) は一切変更しません。

### 既存 caller

production caller は 1 箇所だけです。

- [`p3_autonomous_workload_trial.py:628-648`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:628): planner/coder/auditor/critic の 4 instance を構築。

直接 constructor を呼ぶ既存 test は次の 4 箇所です。

- [`test_p3_autonomous_workload_trial.py:730-742`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/test_p3_autonomous_workload_trial.py:730)
- [同:978-986](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/test_p3_autonomous_workload_trial.py:978)
- [同:997-1006](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/test_p3_autonomous_workload_trial.py:997)
- [同:1021-1029](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/test_p3_autonomous_workload_trial.py:1021)

全て keyword 呼出しであり、新引数を省略するため既定 `False` のままです。これが既存 caller 非変更の構造的根拠ですが、同時に production CLI がまだ opt-in しない根拠でもあります。

## 3. Receipt schema と consumer 閉包

`provenance["transport_receipt"]` は次の exact schema とします。

| key | 型・値 |
|---|---|
| `schema_version` | `str`、`claude-transport-receipt/v1` |
| `mode` | `str`、`explicit-http-proxy-env` |
| `site` | `str`、`PEGASUS_COMPUTE` |
| `admitted_env_keys` | `list[str]`、昇順 exact `["http_proxy", "https_proxy"]` |
| `endpoint_values` | exact 2-key `dict[str, str]` |
| `endpoint_values_sha256` | canonical endpoint map の lowercase 64hex |
| `policy_path` | fixed POSIX path `tools/pegasus/policies/transport_v1.json` |
| `policy_sha256` | policy raw bytes の lowercase 64hex |
| `source_tls_trust_override_keys` | accepted run では exact `[]` |
| `forwarded_tls_trust_override_keys` | exact `[]` |

正規化規則は以下です。

- key は case-sensitive。大小文字統合なし。
- endpoint 文字列は policy と source env の生文字列を保存。trim、hostname 正規化、percent decode、default port 補完なし。
- `endpoint_values_sha256` の pre-image は UTF-8 canonical JSON:
  `ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False`。
- `policy_sha256` は semantic JSON でなく改行を含む raw file bytes。
- 提案 policy bytes に対する固定 vector は、policy SHA
  `67297d505bf01df80c6b77dbe21d837a19091018c41e8e2106ce432b5cbd33f2`、
  endpoint map SHA
  `f08f46ffdec97849236010f3dcc8d6a313e43bd5c7c689c44d6b05ca7d65c962`
  です。

Projected provenance の現 consumer は [response の無加工コピー:590-597](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:590) です。したがって receipt は成功 attempt の以下へ伝播します。

- `attempts.jsonl` の `role-attempt.provenance.transport_receipt`
- `report.json` の `cells[].generations[].roles.<role>.provenance.transport_receipt`

[`AttemptJournal.append()`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:396) は generic writer で provenance exact-key gate を持ちません。tracked Python 全体の静的再検索でも、projected 固有の `capability_lowering` consumer は [`test_p3_autonomous_workload_trial.py:1014`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/test_p3_autonomous_workload_trial.py:1014) の 1 件だけでした。

一方、s8b の exact gate は [`_AGENT_PROVENANCE_KEYS`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/s8b_selector_freeze.py:88) と [`set(provenance) != ...`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/s8b_selector_freeze.py:223) です。これは別 producer `ClaudeHeadlessProvider` の 8-key receipt にだけ到達し、本変更からは非到達です。

## 4. Policy schema と registry 差分

新規 `tools/pegasus/policies/transport_v1.json:1-10` は、末尾 newline を含め次の exact bytes とします。

```json
{
  "schema_version": "pegasus-claude-transport-policy/v1",
  "site": "PEGASUS_COMPUTE",
  "mode": "explicit-http-proxy-env",
  "endpoint_values": {
    "http_proxy": "http://10.120.96.1:8080",
    "https_proxy": "http://10.120.96.1:8080"
  }
}
```

[`registry_v1.json:3-8`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/tools/pegasus/policies/registry_v1.json:3) は sorted order を保って次を追加します。

```diff
     "tools/pegasus/policies/floor_v1.json",
+    "tools/pegasus/policies/transport_v1.json",
     "tools/pegasus/policy.json"
```

閉集合 gate の要求は次のとおりです。

- registry exact 2 key、schema、非空 string list、sorted unique: [`test_pegasus_policy_registry.py:370-385`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/test_pegasus_policy_registry.py:370)
- entry は canonical repo-relative、実在、regular、非 symlink、tracked: [同:386-408](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/test_pegasus_policy_registry.py:386)
- policy directory は flat な regular files のみ: [同:410-421](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/test_pegasus_policy_registry.py:410)
- directory の全 file + legacy 2 件と registry の exact 一致: [同:422-429](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/test_pegasus_policy_registry.py:422)

この test は `git ls-files` を使うため、新規 policy が未追跡の worker 状態では赤になります。親が stage/commit した snapshot で受入する必要があります。

## 5. `test_claude_transport.py` の境界テスト

新規 `orchestrator/tests/test_claude_transport.py:1-360` は、production 定数や実行時 `os.environ` を expected oracle に使いません。

| test | 受理・拒否する境界 |
|---|---|
| `test_committed_policy_matches_independent_literal` | committed policy bytes と SHA が test 内の独立 literal に exact 一致することを受理 |
| `test_admit_accepts_literal_compute_pair_and_exact_receipt` | fixed compute site、固定 policy、明示 source dict の lowercase 2 値だけを受理し、env/receipt 全 field を literal 比較 |
| `test_projected_provider_default_never_calls_transport_leaf` | resolver を「呼ばれたら失敗」に差し替え、既定 `False` が現行 env・argv・provenance key 集合のまま成功することを受理 |
| `test_projected_provider_opt_in_passes_exact_env_and_receipt` | fake runner の `kwargs["env"]` を base 5 + lowercase 2 の完全な literal dict と比較し、receipt 永続化を受理 |
| `test_real_subprocess_shim_observes_admitted_pair_without_overrides` | 実 `subprocess.run` で起動する小 shim が 2 値を観測し、TLS/uppercase/secret を観測しないことを受理 |
| `test_rejects_non_compute_site_before_policy_read` | LOGIN/SUSPECT/OTHER を、policy が欠落していても site 理由で先に拒否 |
| `test_rejects_tls_trust_override_presence` | 指定 7 key を空値・非空値の双方で拒否 |
| `test_rejects_unadmitted_proxy_names` | uppercase、no/all/ftp proxy key の存在を拒否 |
| `test_rejects_missing_or_non_string_required_pair` | 片方欠落、`None`、bytes、bool 等を拒否 |
| `test_rejects_endpoint_value_drift_without_normalization` | trailing slash、前後空白、case 差、別 port、userinfo 付き値を拒否 |
| `test_rejects_policy_surface_failures` | missing、symlink、directory、special/oversized file を拒否 |
| `test_rejects_malformed_duplicate_or_nonfinite_json` | non-UTF8、duplicate key、NaN/Infinity、top-level 非 object を拒否 |
| `test_rejects_policy_schema_or_endpoint_shape_drift` | extra/missing key、schema/site/mode 差、endpoint key 差、非 string 値を拒否 |

### 回避する恒真パターン

- `expected = {k: os.environ[k] ...}`: 使用禁止。source と expected は別の test literal にする。
- production の `ADMITTED_KEYS` / TLS denylist を import して expected を組む: 使用禁止。test 側に独立 literal を列挙。
- policy file を読み、それ自身から expected endpoint/hash を導出: 使用禁止。raw bytes と 2 SHA を固定 literal 化。
- `hashlib.sha256(result["endpoint_values"])` を expected にする: 使用禁止。既知 digest と比較。
- `runner.kwargs["env"] == provider.env`: 自己比較なので禁止。完全な literal dict と比較。
- `set(env) <= allowlist` や「2 key を含む」だけ: secret/extra key を見逃すため禁止。mapping exact 一致。
- fake runner だけ: production runner 分岐の退化を見逃すため、実 subprocess shim を第 2 vector にする。
- receipt metadata 同士の一致だけ: 実 `env=` への配線漏れを見逃すため、runner 引数と child 観測も検査。

## 6. 既存テストへの波及

赤くなり得る既存 test は静的に次のとおりです。

- `test_pegasus_policy_registry.py`: file/registry の片方だけ、未追跡、並び順違反で赤。
- [`test_p3_autonomous_workload_trial.py:995-1017`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/test_p3_autonomous_workload_trial.py:995): default env を変えた場合に赤くすべき箇所。現状は provenance subset 検査なので新 test で exact gate を補います。
- [同:940-990](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/test_p3_autonomous_workload_trial.py:940): opt-in default や初期化順を誤ると cleanup/error 型が変わり得ます。
- [`test_s8b_prediction_runner.py:887-899`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/test_s8b_prediction_runner.py:887) と [同:920-925](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/test_s8b_prediction_runner.py:920): allowlist または s8b provenance へ誤波及すると赤。
- [`test_s8b_selector_freeze.py:490-524`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/test_s8b_selector_freeze.py:490)、`test_s8b_ratified_freeze.py`、`test_s8b_floor_campaign.py`、`test_s8b_ratified_verify.py`: exact 8-key receipt へ誤波及すると赤。
- `test_frozen_artifacts.py`: selector journal/freeze bytes を誤って変更すると赤。
- `test_site_policy.py`: leaf は既存分類を利用するだけなので通常は非到達ですが、site 判定自体を触っていないことの回帰確認対象です。

親の実測対象は新 test、上記関連 test、全走、`check_codex_agents.py`、`check_docs.py` です。Pegasus login node 上では pytest を直接走らせず、`tools/run_tests.py` から計算ノードへ dispatch します。

## 7. 親が更新する docs の節

文面は起草せず、更新箇所だけを示します。

- [`docs/decisions.md` D115 末尾後](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/docs/decisions.md:5392): 新 D116 を追加。D96 手続、受理集合、明示 opt-in、policy/receipt、s8b 非波及、MITM 保証の限定、却下案、残余を記録。
- [`D108 決定 (1):4955-4970`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/docs/decisions.md:4955): projected role の限定 opt-in が旧「計算ノードで `claude -p` を起動しない」を supersede する注記。決定 (2)〜(5) と T-236 の凍結は維持。
- [`pegasus-runbook.md §7.1末尾:390-406`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/docs/pegasus-runbook.md:390): 「本訂正では緩めない」を新 D に追随。git/CMake/pip へ一般化しない記述は維持。
- [`pegasus-runbook.md §8:428-431`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/docs/pegasus-runbook.md:428): absolute prohibition を、明示 opt-in + exact policy admission の条件付き許可へ更新。campaign dispatch task 未実装と T-236/T-277 残余は残す。
- [`docs/worklog.md` 末尾](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/docs/worklog.md:1506): 新エントリで実装、実測結果、残余、T-276 の状態を記録。既存 (102) は歴史として改稿しない。
- `docs/phase3-s8c-autonomous-trial-runbook.md §2・§3.2・§3.3`: 現 plan のように既存 CLI caller を変えないなら変更不要。CLI opt-in を追加裁定する場合だけ、Provider/env 契約と起動 flag を親が同期する。

D96、D79、D115 本文は変更不要です。D79 の s8b base 5-key 契約は意図的に現行のままです。

## 8. 実装しても閉じない残余

| この設計で防げるもの | 防げないもの |
|---|---|
| env から任意 proxy endpoint へ差し替える攻撃 | 固定 `10.120.96.1:8080` 自体の侵害・運用者による MITM |
| uppercase/no_proxy/all_proxy による競合・迂回 | system/user trust store、公開 CA 誤発行、Claude/Node TLS stack の欠陥 |
| 列挙した 7 TLS env override と key-log 出力 | `HOME` 配下設定、CLI 内部設定、OS trust root など列挙外の信頼入力 |
| 非 compute site での opt-in | hostname/site 分類そのものが侵害された場合 |
| child `env=` へ入れた exact key/value の証明 | CLI が実際にその proxy を使用したこと、実 TCP peer、CONNECT、証明書 chain |
| endpoint 値・policy bytes が同一だったことの台帳化 | 応答 origin の署名、replay 防止、application-level authenticity |
| credential 入り proxy URL の policy 受理 | plaintext HTTP 通信があれば proxy に内容を読まれ、改変されること |
| 成功した projected response の transport 帰属 | provider init/invoke が失敗して `ProviderResponse` が無い attempt の receipt |

さらに残る点は次です。

- Proxy は TLS interception ができなくても接続先 metadata、時刻、サイズを観測し、遮断・遅延できます。
- Receipt は「env を注入した証拠」であって「安全な route を使った証拠」ではありません。
- 既定 direct 行に receipt を追加しないため、direct と legacy/uninstrumented/custom provider を区別できません。
- 現 production caller は opt-in しないため、repo 内 CLI の transport 断は本 plan だけでは解消しません。
- Invocation failure の attempt へ receipt を残すには `p3_autonomous_workload_trial.py` の error-event 配線が別途必要です。
- Policy file の SHA は記録しますが、runtime checkout の clean/commit identity や policy の Git blob identityまでは認証しません。
- Probe は特定 allocation/profile/CLI 版の証拠です。全 bnode、将来 profile、将来 Claude CLI の実効 route を証明しません。
- T-236 の campaign task、T-277 の measurement admission/build identity、T-278 の `s6_proposal_rounds` は閉じません。
- MITM を本当に「防止済み」と呼ぶには、Claude API 応答の end-to-end 署名検証、証明書/SPKI pin、または信頼済み proxy attestation が必要です。これは現 brief の範囲外の裁定パッケージ候補です。

## 総括

- 推奨実装は、固定 policy・compute-only・lowercase 2 key exact・明示 opt-in・opt-in 時だけの receipt 追加です。
- `CLAUDE_ENV_ALLOWLIST`、s8b provider、exact 8-key freeze、凍結 bytes は変更しません。
- 境界テストは実行時 env・production 定数・戻り値自身から期待値を作らず、固定 literal、既知 SHA、runner 引数、実 child 観測の独立 vector で固定します。
- P3 は列挙 env 攻撃の緩和であって完全な MITM 防止ではありません。また既存 production caller は opt-in しないため、CLI 解禁には追加裁定が必要です。
- read-only の静的計画のみであり、pytest・全走・緑確認は未実施です。