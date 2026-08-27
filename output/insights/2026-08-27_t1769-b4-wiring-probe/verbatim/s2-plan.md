## 設計判断

### 1. probe module の配置と名前

新規 module は次に固定する。

- 絶対 path: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1769-b4-wiring-probe/orchestrator/campaign/p3_b4_wiring_probe.py`
- module 名: `orchestrator.campaign.p3_b4_wiring_probe`
- CLI: `main(argv)`、必須引数は `--driver {base,sort,trigger}` と `--evidence-set-id ID`
- sanctioned entrypoint ID: `orchestrator.campaign.p3_b4_wiring_probe.main`
- `--campaign-dir`、`--output-root`、fixture root 注入引数は設けない。

`materializer_admission.py:1-19,45-52,161-165` の registry は build materializer / coder-authority issuer の登録簿である。probe を `CODER_ENTRYPOINT` に登録すると build authority を持つかのような誤分類になるため、そこは変更しない。production module の固定 entrypoint ID、直接実行 bootstrap、docs の exact command、専用 consumer test を合わせて sanctioned CLI とする。

`orchestrator/campaign/*.py` の一覧・内容走査による要求は次のとおり。

| consumer | 走査内容 | 新 file の満たし方 |
|---|---|---|
| `test_p3_exploration_namespace.py:74-83,103-136` | `exploration_campaign_layout()` と `CampaignLayout()` / `run_campaign()` の併存を driver と判定 | probe は `CampaignLayout()` のみを隔離 fixture に使い、`exploration_campaign_layout()` を呼ばない。したがって driver 集合に入らず、同 test の `_DRIVER_CONTRACTS` (`:290-380,414-417`) は変更しない |
| `test_p3_build_authority_cli.py:193-209,629-685` | tracked Python 全体から coder-authority helper と動的 alias を走査 | `add_*coder_build_authority_argument`、`build_run_context(... coder_authority=...)` を probe から呼ばない |
| 同 `:1189-1200` | campaign file 本文に exact 文字列 `--build` がある file を materializer と判定 | probe の source/docstring/定数に exact `--build` を置かない |
| `test_s8b_floor_campaign.py:6049-6157` | 全 campaign Python の `--build` 定数、`buildcache.build*` 呼出しを AST 走査 | どちらも持たない。interdiction は subprocess 全般を遮断し、build command の固定列挙を持たない |
| `test_s8b_oracle_manifest_contract.py:39-104` | oracle loader / `verify_manifest` の import alias と呼出し consumer を列挙 | oracle module/function を import・call しない |
| `test_s1_known_axes_freeze.py:520-546` | production file 内の `s1_expected_goldens` 参照を内容走査 | 参照しない |
| `test_campaign_import_invariant.py:824-947,1001-1045` | campaign file の direct bootstrap、相対 sibling import、legacy namespace を全 tracked/untracked source から検査 | `p3_s4_loop.py:57-60` と同じ逐語 bootstrap を、最初の runtime 相対 import より前に一度だけ置く。campaign sibling は相対 import のみ |
| `test_s8b_floor_stats.py:848-874` | `verify_floor_artifact_with_live_admission(` の consumer 集合 | 参照しない |
| `test_s8b_ratified_freeze.py:2375-2385` | `RatifiedFreeze(` の直接構築を内容走査 | 参照・構築しない |
| `test_campaign.py:5128-5252` | tests/output を除く全 Python から `loop.run_campaign` / `pipeline.evaluate` 呼出しを解決し exact inventory と比較 | production probe は両者の callable identity を読むだけで呼ばない。実体負例は tests 配下に置くため production inventory は不変 |
| `test_frozen_artifacts.py:41-88,236-246` | exact 23 path のみを凍結 | 新 evidence path を `FROZEN_MANIFEST` に追加せず、既存 23 件を変更しない |

### 2. §5.1 (ii) の 4 検査

既存負の対照の正本は `test_p3_s4_loop.py:2029-2201`、identity 分離は `:2204-2233` である。probe は以下を CLI 内部から実行する。

1. 切替点通過

   - 静的側は、選択 driver の `main` から `p3_s4_loop.make_critic_digest` までの call graph を AST で生成する。
   - 現行 callsite は base `p3_s4_loop.py:1514,1722`、sort `p3_s4_loop_sort.py:506,695`、trigger `p3_s4_loop_trigger_gating.py:1036`。trigger は `main:1072 → drive_iteration:899 → make_critic_digest:1036` を辿る。
   - alias resolver は `from . import p3_s4_loop as L`、`X = L`、`f = X.make_critic_digest`、literal `getattr(L, "make_critic_digest")`、module 属性呼出しを canonical symbol に正規化する。
   - 同じ scope での再代入、star import、非 literal `getattr`、`globals()/locals()/__dict__`、動的 import、解決不能な module alias が、証明に使う path に入った場合は「未到達」ではなく `StaticInventoryError` で fail-closed にする。
   - 動的側は policy-admitted な隔離 view を引数に、実体 `p3_s4_loop.make_critic_digest` を on/off 各 1 回呼ぶ。profile ledger が実体 `__code__` の call event を 2 回観測する。wrapper/stub を切替点の代用にしない。
   - 静的 path と動的実体 identity の両方が一致して初めて検査 1 を合格にする。

2. on で赤詳細が現れる

   - `p3_s4_loop.record_diff_reject()` (`p3_s4_loop.py:370-392`) で、隔離 layout に marker 付き synthetic diff-quarantine record を作る。
   - `require_admitted_campaign(... CERTIFIED_ACCEPTANCE)` (`artifact_admission.py:1128-1193`) で exact `CertifiedCampaignView` を発行する。
   - 実 `make_critic_digest(... reflux=True)` を呼び、marker と `# rejections` heading が存在することを検査する。
   - digest 本文や marker は stdout に出さず、evidence には出現回数と digest SHA-256 だけを残す。

3. off で §8 項目 1・2が成立する

   - profile ledger で実体 4 loader の call event を数える。on は各 1、off は各 0 とする。既存 test の spy (`test_p3_s4_loop.py:2051-2163`) と同じ性質だが、probe では wrapper の返り値で置き換えず、隔離 WAL を読む実 loader をそのまま通す。
   - `render_text([build_digest(tag, {}, view)])` を独立に作り、`make_critic_digest(... reflux=False)` と UTF-8 bytes exact equality を比較する。既存 test `:2166-2201` と同じ比較である。
   - on に 2 heading、off に 2 heading がないことも記録する。

4. on/off の campaign identity 分離

   - 選択 driver の実 `default_cfg(reflux=True/False)` を呼ぶ。定義位置は base `p3_s4_loop.py:892-915`、sort `p3_s4_loop_sort.py:249-284`、trigger `p3_s4_loop_trigger_gating.py:548-579`。
   - `search_config["reflux"]` を除いた `vars(cfg)` が exact equality、`canonical_preimage` と `campaign_id` が不一致であることを確認する。既存 test `test_p3_s4_loop.py:2204-2224` を再利用した判定である。
   - probe は authoritative layout を構築・閲覧しない。§5.1 が求めるのは identity 分離なので、path 分離は既存 test `:2226-2233` に任せる。

fixture は test module から import しない。CLI が実際に使う synthetic admitted view の作成は production module 内の private `_make_probe_view()` に置く。新 test 側はこの API の結果を検査するが、既存 test fixture を production へ移植しない。

### 3. interdiction 窓

P3 の module 属性置換案は採らない。既に束縛された local reference を遮断できないためである。代わりに CPython の call-profile と audit hook を一体の process-wide interdiction とする。

outcome producer 集合の権威は、`execution_guard.require_certified_writer_authorization` (`execution_guard.py:107-119`) とする。同 API は「certified sink が書く前の authorization」と自ら規定しており、probe の call/non-call から導かれない。

AST inventory は次のように作る。

- candidate driver、`loop.py`、`pipeline.py` の import/assignment/call graphを canonical symbol へ解決する。
- authority anchor を呼ぶ `loop._authorize_measurement` (`loop.py:154-171`) と `pipeline.evaluate` (`pipeline.py:705-725,864-870`) を seed にする。
- reverse call closure を取り、`loop.run_campaign` (`loop.py:232-254,308-313,456-465`) と各 driver の `run_one_iteration` / `drive_iteration` / `main` を自動的に producer 集合へ入れる。
- producer の名前 list は手書きしない。新 function が authority anchor への path を持てば自動的に集合へ入る。
- driver の `main` から、動的 import、process launch、`ctypes`/`cffi`/extension loader、未解決 callable によって authority anchor を迂回できる edge が増えた場合は inventory 自体を失敗させる。
- inventory 全体を canonical JSON 化して SHA-256 を evidence に残す。

遮断は producer の `__code__` 集合を `sys.setprofile` と `threading.setprofile` に登録し、call event 時、関数本体の最初の命令より前に `OutcomeGenerationError` を送出する。

迂回別の扱いは次のとおり。

- 既に束縛済みの local reference: module 属性でなく `frame.f_code` を照合するので遮断。
- 別 module の再 import / alias: 同じ code object なので遮断。seal 後の candidate module reload/import は audit hook で拒否し、`sys.modules` identity と source hash を evidence publish 前に再検証する。
- `getattr` 文字列呼出し: 解決結果の code object で遮断。静的到達性側は literal のみ解決し、動的文字列は fail-closed。
- subprocess: `subprocess.Popen`、`os.system/popen/spawn*/exec*` の audit event を拒否する。
- 例外として、v2 lock 発行に必要な `contract_loader_binding._run_git` (`contract_loader_binding.py:252-313`) からの `/usr/bin/git` read-only argv だけを許す。`rev-parse` / `cat-file blob` の閉じた形、clean environment、実行元 frame を全照合し、それ以外の argv は拒否する。
- C 拡張: producer の Python ancestor で先に止める。candidate driver closure に新しい native loader/direct native callable が出た場合は AST inventory を失敗させる。任意の hostile native code 全般に対する OS 権限分離までは主張しない。

窓は `main()` の argument validation 直後から process exit までとする。

1. campaign module import 前に audit phase を開く。
2. imports と AST inventory 後に profile phase を seal。
3. 4 検査、隔離 workspace の cleanup、evidence JSON の publish、JSON 全 bytes の SHA-256 計算、sidecar publish中も維持。
4. production CLI では restore せず、その process を終了する。

### 4. 非恒真の裏取り

`orchestrator/tests/test_p3_b4_wiring_probe.py` の概略 `430-570` に、各負例を独立 child process で置く。

対象実体は次を名指しする。

- `p3_s4_loop.run_one_iteration` (`:1066`)
- `p3_s4_loop.drive_iteration` (`:1423`)
- `p3_s4_loop_sort.run_one_iteration` (`:299`)
- `p3_s4_loop_sort.drive_iteration` (`:423`)
- `p3_s4_loop_trigger_gating.run_one_iteration` (`:793`)
- `p3_s4_loop_trigger_gating.drive_iteration` (`:899`)
- `pipeline.evaluate` (`pipeline.py:705`)

各 test は以下を行う。

- inventory が対象の実 `__code__` を含むことを先に確認する。
- Python の argument binding が完了するだけの全 required 引数を dummy で渡し、実 function object を呼ぶ。
- profile callback が `co_firstlineno` の function entry で `OutcomeGenerationError` を出すことを確認する。
- exception の `module`、`qualname`、`path`、`firstlineno` が対象実体と一致することを確認する。
- audit ledger の許可外 subprocess count が 0、隔離 canary tree の before/after manifest が exact equality、WAL/checkpoint/digest が存在しないことを確認する。

stub を呼ぶ負例、production module に `--negative-control` のような穴を足す形は採らない。child process の Python snippet が private guard を組み、production CLI には負例起動口を公開しない。

### 5. 証拠 JSON と保存先

保存先は repo 固定 root から導出する。

```text
output/insights/2026-08-27_t1769-b4-wiring-probe/
  <evidence-set-id>/
    base.json
    base.json.sha256
    sort.json
    sort.json.sha256
    trigger.json
    trigger.json.sha256
```

`evidence-set-id` は `[a-z0-9][a-z0-9._-]{0,63}` の slug のみ許し、path separator、symlink component、既存 target、campaign root との重なりを拒否する。任意 path 引数は受けない。

JSON の exact schema は以下とする。

```json
{
  "schema_version": "p3-b4-wiring-probe-evidence/v1",
  "evidence_class": "tool-dogfood-non-adoption",
  "sanctioned_entrypoint": "orchestrator.campaign.p3_b4_wiring_probe.main",
  "run": {
    "driver": "base|sort|trigger",
    "axis": "driver.MARKER_ID",
    "evidence_set_id": "slug",
    "argv": ["exact", "argv"],
    "started_at_utc": "RFC3339",
    "completed_at_utc": "RFC3339",
    "python_version": "string"
  },
  "source": {
    "repository_head": "40-hex",
    "probe_path": "repo-relative",
    "probe_sha256": "64-hex",
    "driver_path": "repo-relative",
    "driver_sha256": "64-hex",
    "base_driver_path": "orchestrator/campaign/p3_s4_loop.py",
    "base_driver_sha256": "64-hex"
  },
  "isolation": {
    "kind": "internally-issued-temporary-directory",
    "workspace_realpath_sha256": "64-hex",
    "layout_realpath_sha256": "64-hex",
    "outside_repository": true,
    "workspace_removed_before_publish": true,
    "protected_read_attempts": 0,
    "protected_write_attempts": 0
  },
  "interdiction": {
    "authority": {
      "symbol": "orchestrator.campaign.execution_guard.require_certified_writer_authorization",
      "path": "orchestrator/campaign/execution_guard.py",
      "line": 107,
      "source_sha256": "64-hex"
    },
    "inventory": [
      {
        "module": "string",
        "qualname": "string",
        "path": "repo-relative",
        "firstlineno": 1,
        "code_sha256": "64-hex",
        "reason_path": ["canonical symbols"]
      }
    ],
    "inventory_sha256": "64-hex",
    "profile_hook_active": true,
    "audit_hook_active": true,
    "window": {
      "opened_before_campaign_imports": true,
      "sealed_before_checks": true,
      "active_during_json_publish": true,
      "active_during_sha256_publish": true
    },
    "blocked_outcome_attempts": [],
    "forbidden_subprocess_attempts": 0,
    "allowed_read_only_git": [
      {
        "argv_sha256": "64-hex",
        "returncode": 0
      }
    ]
  },
  "checks": {
    "switchpoint_passage": {
      "passed": true,
      "static": {
        "entrypoint": "module.main",
        "reachable": true,
        "path": [
          {
            "caller": "symbol",
            "callee": "symbol",
            "path": "repo-relative",
            "line": 1
          }
        ],
        "ambiguous_bindings": []
      },
      "dynamic": {
        "callable": "orchestrator.campaign.p3_s4_loop.make_critic_digest",
        "path": "orchestrator/campaign/p3_s4_loop.py",
        "line": 558,
        "code_sha256": "64-hex",
        "call_count": 2,
        "reflux_values": [true, false]
      }
    },
    "on_red_details": {
      "passed": true,
      "marker_occurrences": 1,
      "rejection_heading_present": true,
      "digest_sha256": "64-hex"
    },
    "off_negative_controls": {
      "passed": true,
      "on_loader_calls": {
        "load_rejections": 1,
        "load_liveness_rejections": 1,
        "load_verify_abort_signals": 1,
        "load_diff_rejections": 1
      },
      "off_loader_calls": {
        "load_rejections": 0,
        "load_liveness_rejections": 0,
        "load_verify_abort_signals": 0,
        "load_diff_rejections": 0
      },
      "green_sha256": "64-hex",
      "off_sha256": "64-hex",
      "off_equals_green_bytes": true,
      "on_headings_present": true,
      "off_headings_absent": true
    },
    "campaign_identity": {
      "passed": true,
      "on_reflux": "on",
      "off_reflux": "off",
      "only_reflux_differs": true,
      "on_campaign_id": "string",
      "off_campaign_id": "string",
      "on_preimage_sha256": "64-hex",
      "off_preimage_sha256": "64-hex"
    }
  },
  "result": {
    "passed": true,
    "pass_rule": "all-four-checks-and-zero-interdiction-or-protected-root-violations",
    "preregistration_effect": "none-section-5-remains-unfilled"
  }
}
```

最終 JSON 自身の hash は JSON 内へ書かない。canonical UTF-8 bytes を先に確定し `sha256(bytes)` を計算し、`<file>.sha256` に detached hash と basename を書く。sidecar を先、JSON を最後に hard-link publishし、JSON が見える時点では sidecar も存在する形にする。自己 hash 循環は生じない。

本 wave の dogfood ID は例として `t1769-dogfood` とするが、これらは §5.1 (ii) の採用 evidence ではない。

### 6. 実 campaign への非接触

production CLI は private `_issue_probe_workspace()` だけから `_ProbeWorkspace` capability を得る。layout factory は path でなくこの exact capability を要求する。

- workspace は `TemporaryDirectory` 由来、repo 外、実効 UID 所有、symlink component なしを検査。
- `_ProbeWorkspace` は issuer token、PID、realpath、nonce を持ち、任意 constructor を公開しない。
- `CampaignLayout(root=<workspace>/fixture)` は capability factory 内だけで構築する。
- protected root は repo の `output/campaigns`、`output/exploration/campaigns`、および `IZANAGI_OFFICIAL_OUTPUT_ROOT` / `IZANAGI_EXPLORATION_OUTPUT_ROOT` から保守的に導出した campaign subtree。
- audit hook は protected root に対する read/write/list/scandir をすべて拒否する。evidence root と issued workspace だけを書込み allowlist にする。
- `exploration_campaign_layout()` は namespace marker を書く (`layout.py:485-537,589-597`) ため probe から呼ばない。

新 test `:570-650` には次の負例を置く。

- private workspace issuer を実 campaign 相当 root へ差し替え、capability validation が `CampaignLayout.ensure()` 前に拒否する。
- workspace 内 symlink を protected root へ向け、resolved path 検査が拒否する。
- guard 内で protected WAL の read/write を試み、audit hook が拒否し、外側 test が採取した tree manifest が before/after exact equalityであることを確認する。
- parser が `--campaign-dir` / `--root` / `--output-root` を unknown argument として拒否する。

### 7. 変更 file、参照関係、受理集合確認

変更・生成面は次に限定する。

| file | 変更 | consumer |
|---|---|---|
| `orchestrator/campaign/p3_b4_wiring_probe.py` | 新規 production CLI | 新 `test_p3_b4_wiring_probe.py`、上記 campaign glob/content scanner 群 |
| `orchestrator/tests/test_p3_b4_wiring_probe.py` | 新規正例・実体負例 | pytest collection、`test_campaign_import_invariant.py:1001-1045` の repository scan |
| `docs/phase3-b4-reflux-ablation-preregistration.md` | §5.1 と §10 の CLI 実在反映だけ | `test_campaign_import_invariant.py:950-960,993-1045`、`tools/check_docs.py` |
| `output/insights/2026-08-27_t1769-b4-wiring-probe/<set>/{base,sort,trigger}.json(.sha256)` | CLI dogfood 生成物 | 新 test の schema/hash consumer。`FROZEN_MANIFEST` には入れない |

既存 3 driver、`pipeline.py`、`loop.py`、`test_p3_s4_loop.py` は編集しない。したがって既存 §8 test の判定式や受理集合は変更しない。

親が書込可能環境で行う確認は以下とする。すべて `tools/run_tests.py` 経由にする。

```text
python3 tools/run_tests.py orchestrator/tests/test_p3_b4_wiring_probe.py
python3 tools/run_tests.py orchestrator/tests/test_p3_s4_loop.py -k "make_critic_digest_reflux_off or default_cfg_reflux_separates_campaign_identity"
python3 tools/run_tests.py orchestrator/tests/test_p3_exploration_namespace.py
python3 tools/run_tests.py orchestrator/tests/test_p3_build_authority_cli.py
python3 tools/run_tests.py orchestrator/tests/test_s8b_floor_campaign.py -k materializer_registry_covers_all_python_build_launches
python3 tools/run_tests.py orchestrator/tests/test_s8b_oracle_manifest_contract.py
python3 tools/run_tests.py orchestrator/tests/test_s1_known_axes_freeze.py -k goldens_helper_is_independent
python3 tools/run_tests.py orchestrator/tests/test_campaign_import_invariant.py
python3 tools/run_tests.py orchestrator/tests/test_campaign.py -k certified_writer
python3 tools/run_tests.py orchestrator/tests/test_s8b_floor_stats.py -k live_refreeze_comparison_is_centralized
python3 tools/run_tests.py orchestrator/tests/test_s8b_ratified_freeze.py -k no_production_module_constructs
python3 tools/run_tests.py orchestrator/tests/test_frozen_artifacts.py
python3 tools/check_codex_agents.py
python3 tools/check_docs.py
```

dogfood は base/sort/trigger をそれぞれ起動し、stdout が evidence path と file hash だけで赤 marker/digest を含まないことも確認する。本 read-only 段では pytest 緑を計測していない。

### 8. docs 変更案

対象は `docs/phase3-b4-reflux-ablation-preregistration.md:167-178` と `:389-396`。

§5.1 の before:

> その条件を満たす sanctioned CLI が無い場合は、用意されるまで  
> 対象 driver と軸を記入しない。(i) と (ii) は実走開始前に完了させ、実走開始後は差し替えない。**

after:

> §5.1 (ii) を実行する sanctioned CLI は  
> `python3 -I -B orchestrator/campaign/p3_b4_wiring_probe.py --driver {base,sort,trigger} --evidence-set-id <事前固定 ID>`  
> として実在する。**ただし CLI の実在および本 wave の dogfood evidence は (i) を充足せず、  
> §5 の欄を埋める権限も与えない。**候補集合・各 exact command・証拠 path と hash・0 件/複数件の  
> 決定規則・記入者・レビュー者を、人間の指名を含む別 commit で先に freeze しない限り、  
> 対象 driver と軸を記入しない。(i) と (ii) は正式実走開始前に完了させ、開始後は差し替えない。**

§10 最上位項目の before:

> **§5.1 (ii) を満たす非標本 probe。現時点で、その条件を満たす sanctioned CLI は存在しない。**  
> build を伴う経路は次の synthesis と outcome を生成するため probe にならず、`--no-build` 経路は  
> §3.1 の切替点を通らない。probe は §5.1 (ii) の 4 検査 […] を、**next synthesis と primary / secondary outcome を生成も閲覧もせずに**  
> 行えなければならない。§5.1 (i) の先行 freeze […] も依存条件である。  
> **これが用意されるまで「対象 driver と軸」の欄は埋められず、したがって本書は発効しない。**

after:

> **§5.1 (i) の先行 freeze と人間の指名。** §5.1 (ii) の 4 検査を、next synthesis と  
> primary / secondary outcome を生成も閲覧もせずに行う sanctioned CLI は  
> `orchestrator/campaign/p3_b4_wiring_probe.py` として実在する。interdiction の発火を含む  
> 本 wave の実走は道具の dogfood であり、§5.1 (ii) の採用 evidence ではない。  
> 候補 driver 集合・各 exact command・証拠 path と hash・0 件/複数件の決定規則・  
> **記入者とレビュー者を、人間の指名を含む別 commit で先に freeze する §5.1 (i) は未完である。**  
> この先行 freeze が完了し、その版に従って (ii) を実測するまで「対象 driver と軸」の欄は  
> 埋められず、したがって本書は発効しない。

## 実装プラン

### `orchestrator/campaign/p3_b4_wiring_probe.py`

- 概略 `1-70`: module docstring、直接実行 bootstrap、stdlib imports。campaign imports は audit phase 開始後まで遅延。
- `70-160`: `DriverName`、`DriverSpec`、`StaticInventoryError`、`ProbeIsolationError`、`OutcomeGenerationError`、evidence 定数。
- `160-390`: AST alias resolver、cross-module call graph、switchpoint reachability、authority-anchor reverse closure、producer inventory。
- `390-560`: process audit/profile guard、code/source identity seal、read-only Git 例外、protected-root判定。
- `560-650`: `_ProbeWorkspace` issuer と capability-only layout factory。
- `650-735`: policy-bound lock、synthetic diff rejection、`CertifiedCampaignView` を作る `_make_probe_view()`.
- `735-860`: `_check_switchpoint()`、`_check_on_red()`、`_check_off_controls()`、`_check_identity()`.
- `860-970`: exact schema validation、canonical JSON、detached SHA-256、sidecar-first/no-overwrite publish。
- `970-1040`: argparse、4 検査の集約、全条件合格時だけ publish、stdout の path/hash限定、`main()` guard。

### `orchestrator/tests/test_p3_b4_wiring_probe.py`

- 概略 `1-100`: imports、child-process runner、tree manifest helper。
- `100-230`: actual driver の静的 reachability と alias/rebinding positive/negative controls。
- `230-360`: 4 検査の正例、既存 §8 property との一致。
- `360-430`: schema exact key set、detached hash、stdout red 非開示、failure 時 evidence 0 件。
- `430-570`: 3 driver の実 `run_one_iteration` / `drive_iteration` と実 `pipeline.evaluate` の発火負例。
- `570-650`: protected root read/write、symlink、workspace injection の負例。
- `650-720`: campaign 一覧検査に入っても driver/materializer/oracle consumer と誤分類されない静的 control。

### `docs/phase3-b4-reflux-ablation-preregistration.md`

- 現 `167-178`: sanctioned CLI 実在を反映し、§5.1 (i) と人間指名の先行 freeze は未完と明記。
- 現 `389-396`: blocker を「CLI 不在」から「§5.1 (i) の先行 freeze・人間指名」へ差し替える。
- §5 の値セル `153-163` は変更しない。

### dogfood evidence

実装・test 完了後、親が 3 driver を別 command で実走し、`t1769-dogfood` evidence set に JSON と sidecar を生成する。§5 の対象 driver/軸欄、候補集合、採用規則は書かない。

## リスクと未解決

- **P1:** `orchestrator/campaign/` 配置は一覧検査の射程を広げる。特に source に `exploration_campaign_layout()` や exact `--build` を追加すると別 registry の対象へ誤分類されるため、専用 regression が必要。
- **P2:** 「静的 main 到達性 + 実切替点の直接動的呼出し」は、driver `main()` が実際に runtime で切替点へ到達した証明ではない。outcome 禁止と両立する composite evidence であり、evidence 文言もその限定を明記すべきである。
- **P3:** module 属性置換案は pre-bound local を漏らすため疑う。profile/audit 案は強いが、任意の hostile native code や同権限 process による interpreter 改変を OS 境界で防ぐものではない。candidate closure の native edge を静的に拒否する範囲までに主張を限定する。
- **P4:** profile callback が例外を送出すると profiling が解除されうるため、production は例外を catch して継続せず、そのまま evidence なしで process を失敗終了させる必要がある。
- **P5:** evidence は repo `output/insights` へ書くが、campaign artifacts ではない。evidence root の symlink・既存 file・campaign root 重複を拒否しない実装は不可。
- **P6:** dogfood JSON を §5.1 (ii) 採用 evidence と表現してはいけない。§5 値セルは全て未記入のまま。
- **P7:** docs の「CLI 実在」更新だけで発効したように読める危険がある。§5.1 (i) の別 commit、人間の記入者・レビュー者指名、正式実測が残ることを §5.1 と §10 の両方に逐語で残す。

## 総括

- 新規 CLI は `orchestrator.campaign.p3_b4_wiring_probe` に固定する。
- 4 検査は既存 production API と policy-admitted な隔離 WAL viewだけで行う。
- 切替点は AST 到達性と実 `make_critic_digest` call ledger の二本立てにする。
- outcome producer は certified-writer authorization anchor から自動導出する。
- module 属性置換ではなく profile/audit interdiction を process 全体で維持する。
- 実 `drive_iteration` / `run_one_iteration` / `pipeline.evaluate` を名指しした発火負例を置く。
- campaign root は公開引数にせず、内部発行 capability 由来 workspace だけを許す。
- evidence は detached SHA-256 とし、自己 hash 循環を作らない。
- 既存 driver・§8 test・凍結 23 artifact は変更しない。
- docs は CLI 実在だけを反映し、§5.1 (i) と人間指名による発効阻止を残す。