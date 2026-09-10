結論は **land 不可**です。validator 本体は成立していますが、契約の解決・identity への束縛経路と回帰 gate に must-fix があります。pytest は実行していません。

### A-01 — identity helper が ambient contract を再解決する

対象: [p3_s4_loop_trigger_gating.py:471](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/p3_s4_loop_trigger_gating.py:471)、[backoff_sweep.py:68](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/backoff_sweep.py:68)、[backoff_sweep_report.py:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/backoff_sweep_report.py:35)  
判定: **real — must-fix**

```python
# trigger default_cfg
return ident.bind_environment_contract(cfg, env_contract.lookup(ENV_TAG))

# run_one_iteration
contract = _admit_env_contract(resolved_site)
campaign_cfg = _campaign_cfg_for_site(cfg, resolved_site, _contract=contract)

# historical report
cfg = config_for(tag, workload)  # 内部で env_contract.lookup
layout = discover_campaign_dir(cfg.spec_slug, cfg.search_tag)
```

trigger は `default_cfg()` と site admission で契約を2回解決します。fresh-module 2件はそのため lookup が2回となり、通常 module の sentinel 2件と exploration 1件は `default_cfg()` が注入 seam `_lookup` を通らず ambient registry を引くため、提示された5赤と一致します。

同じ hidden lookup は `backoff_repro`、S4 loop/sort、kickoff/red、S1、S6、S8a、autonomous workload の identity factory にも残っています。特に `backoff_sweep_report` は prefix discovery の前に現在契約を要求するため、歴史 campaign の ID 非依存読み出しを実質的に狭めます。

成果物影響: valid な trigger/exploration campaign が WAL 作成前に拒否され、また current registry に対象 env がないだけで既存 WAL から材料レポートが生成されなくなる。

修正案: config/layout helper 内の lookup を廃止し、実走は guard が返した contract、planning は永続化済みの明示 H を引数で渡す。歴史 reader は slug/search-tag の導出に契約を要求しない。

### A-02 — trigger wrapper が binder の衝突拒否を迂回する

対象: [p3_s4_loop_trigger_gating.py:328](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/p3_s4_loop_trigger_gating.py:328)、[ident.py:52](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/ident.py:52)  
判定: **real — must-fix**

```python
if existing_contract is not None and existing_contract != contract.contract_sha256:
    cfg = replace(cfg, search_config={
        key: value for key, value in cfg.search_config.items()
        if key != ENVIRONMENT_CONTRACT_SEARCH_KEY
    })
...
return ident.bind_environment_contract(cfg, contract)
```

`bind_environment_contract` 自体は異なる既存値を拒否しますが、公開 trigger 経路はその直前に既存 H を削除します。OTHER では異なる文字列を、PEGASUS_COMPUTE では `None` を含む既存 key を黙って除去して再束縛できます。したがって変異1の helper test が赤になっても、実経路の「上書き禁止」は守られません。

成果物影響: H_A に束縛された入力が拒否されず H_B の campaign ID、lock、WAL、provenance として記録され、入力が参照した契約との対応が失われる。

修正案: site contract を一度だけ解決して未束縛 config に束縛する。既に H がある場合は exact 一致だけを許し、wrapper から key 削除処理をなくす。

### A-03 — recovery 追記順を守る専用 gate がない

対象: [test_campaign.py:979](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/tests/test_campaign.py:979)、[wal.py:1271](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/wal.py:1271)  
判定: **real — must-fix（gate 欠落）**

```python
# 現在の順序 test
wal.repair_truncated_tail(lay)
assert open(lay.wal_file, "rb").read() == before

# production recovery
validate_commit_contract_bindings(records, campaign_lock=campaign_lock)
...
_append_records_locked(layout, fd, recoveries)
```

事前登録変異6の nodeid は receipt/truncate だけを検査し、`recover_interrupted_attempts` が不正 COMMIT のある WAL へ recovery ABORT を追記しないことを検査していません。現行実装順は正しいものの、recovery 側の validator を追記後へ移す回帰をこの nodeid は殺しません。

成果物影響: 拒否対象台帳へ recovery ABORT が追加され、WAL bytes、attempt 状態、terminal 集合が拒否前に変わり得る。

修正案: 不一致 COMMIT と別の active attempt を同居させ、`ensure_resumable_wal` または `recover_interrupted_attempts` 後も WAL bytes が完全不変であるテストと対応変異を追加する。

### N-01 — guided の製品 exemption はあるが、実測2赤はテスト準備が迂回

対象: [test_guided.py:272](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/tests/test_guided.py:272)、[test_guided.py:373](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/tests/test_guided.py:373)、[guided.py:171](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/guided.py:171)  
判定: **real — nit**

```python
# production
require_environment_contract=False

# 失敗するテスト準備
ident.ensure_resumable_wal(
    guided._trial_config(meta, trial), layout,
    admission_policy=guided._NO_BUILD_POLICY,
)
```

`cmd_start` と `cmd_evaluate` は明示 exemption を渡しています。2赤は、それらを呼ぶ前の fixture seed が既定 `True` の低水準 helper を直接呼ぶためです。

成果物影響: **nit** — production の受理集合・成果物値は直接変えないが、guided 正例を製品入口まで到達させない。

修正案: fixture の低水準呼出しにも明示 exemption を渡すか、公開 `cmd_*` 経路だけで準備して exemption を実際に検査する。

### R-01 — validator の恒真性、必須性、hash/env 検査

対象: [wal.py:947](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/wal.py:947)、[ident.py:155](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/ident.py:155)  
判定: **refuted**

```python
if (type(search_config) is not dict
        or ENVIRONMENT_CONTRACT_SEARCH_KEY not in search_config):
    return
expected = search_config.get(ENVIRONMENT_CONTRACT_SEARCH_KEY)
resolved = env_contract.resolve_by_contract_sha256(expected)
...
actual = record.payload.get(COMMIT_CONTRACT_SHA256_KEY)
if actual != expected:
    raise AttemptTopologyError(...)
if record.env_tag != resolved.contract.env_tag:
    raise AttemptTopologyError(...)
```

発火集合は明確です。

- lock に H がない: record に field があっても要求しない。
- lock に H がある: 全 COMMIT の欠落、非 str、形式不正、大文字、不一致を拒否。
- H が未知・ever-active でない: `EnvContractError` を `AttemptTopologyError` に変換。
- COMMIT の `env_tag` が解決契約と違う: 拒否。
- resolver の別例外も受理へ倒れず伝播する。

identity 側は certified の既定が `require_environment_contract=True`、production で `False` を渡すのは guided の2入口だけです。WAL validator の必須性を record field から推論する経路はありません。

成果物影響: なし。不正 COMMIT は terminal/certified 集合へ射影されず、H のない grandfathered lane は維持される。

修正案: なし。ただし A-02 の wrapper 迂回は別途修正が必要。

### R-02 — 事前登録8変異の expected nodeid

対象: [test_campaign.py:377](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/tests/test_campaign.py:377)、[test_campaign.py:881](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/tests/test_campaign.py:881)、[test_campaign.py:3247](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/tests/test_campaign.py:3247)  
判定: **refuted — 8件とも静的には期待 nodeid が赤**

| # | expected nodeid | 静的な kill 理由 |
|---|---|---|
| 1 | `test_bind_environment_contract_rejects_conflicting_prebound_hash` | 条件を恒偽にすると helper が復帰し、直後の `assert False`。後段 identity は使わない。 |
| 2 | `test_pipeline_no_bench_wal_commit_binds_authorized_contract` | mutation は authorization 後の payload のみ。raw COMMIT の exact H assertion が不一致。 |
| 3 | `test_pipeline_bench_wal_commit_binds_authorized_contract` | 同上。bench mock は certified まで進み、raw assertion が不一致。 |
| 4 | `test_commit_contract_validator_rejects_missing_field_without_defaulting` | custom `Payload.get(KEY, expected)` が expected を返すため mutant は復帰し、`assert False`。validator 直呼び。 |
| 5 | `test_commit_contract_requirement_is_derived_from_lock_not_record_presence` | custom `__contains__` が record field を欠落扱いするため record-derived mutant は exempt し、`assert False`。 |
| 6 | `test_commit_contract_rejection_precedes_tail_repair_mutation` | validator を repair 後へ移すと receipt/truncate 後の bytes または runs-dir 集合 assertion が失敗。 |
| 7 | `test_commit_contract_validator_rejects_unknown_ever_active_hash` | H と COMMIT は同じ `"0"*64`。resolver 削除なら受理後の `assert False`、単純行削除なら `resolved` 未定義でも同 nodeid が赤。 |
| 8 | `test_commit_contract_validator_rejects_contract_env_tag_mismatch` | H と形式は正当で、env 比較削除時だけ復帰して `assert False`。 |

1・4・5・7・8は helper 直呼び、6は repair 直呼び、2・3は発行 record の直接比較です。parser、attempt topology、identity lock、admission の先行拒否を kill 根拠にしていません。

成果物影響: なし。これは静的な変異感度の判定であり、実走済みとは主張しない。

修正案: 8件自体は不要。A-02 と A-03 の実経路・recovery gap を追加で固定する。

### R-03 — repair/recovery の現行実行順

対象: [ident.py:235](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/ident.py:235)、[wal.py:529](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/wal.py:529)、[wal.py:1271](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/wal.py:1271)  
判定: **refuted**

```python
ensure_campaign_identity(...)
repair = wal.repair_truncated_tail(...)
wal.recover_interrupted_attempts(...)
```

repair は `LOCK_EX` 後に parseable prefix を読み、validator を通してから receipt 作成・`ftruncate`。recovery も別の `LOCK_EX` 区間で全 record を再読・検証してから `_append_records_locked` です。2操作を覆う単一 lock ではありませんが、各 mutation と検査は同じ排他区間内にあり、間で追加された record も recovery が再検証します。

成果物影響: なし。現行コードでは拒否対象 campaign による receipt、truncate、recovery 追記は起きない。

修正案: 実装修正不要。A-03 の回帰 gate は追加する。

### R-04 — matching resume の spy と qualification/existing lane

対象: [test_campaign.py:5397](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/tests/test_campaign.py:5397)、[pipeline.py:1026](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/pipeline.py:1026)  
判定: **refuted**

```python
L.evaluate = forbidden_evaluate
L.buildcache.build = forbidden_build
...
assert calls == {"evaluate": 0, "build": 0}
assert summary.skipped == 1 and summary.evaluated == 0
```

この正例では `env_contract` 引数がないため operative builder は `buildcache.build` であり、`build_v2` は分岐外です。全通常 build は `L.evaluate` の下流なので evaluate spy も独立に効きます。loop が `AssertionError` を abort 化しても最終 call-count assertion が検出します。

また qualification event sink は両 COMMIT 分岐で H を追加しておらず、`wal.log` の2口だけが変更されています。H のない既存 lock は validator 冒頭で exempt、matching H の resume は replay terminal skip になります。generic exploration namespace も authorization→H bind→ID/layout の順です。例外は A-01/A-02 の trigger wrapper です。

成果物影響: matching campaign は再評価・再buildされず、qualification ledger と grandfathered WAL の受理集合もこの差分では変わらない。

修正案: なし。

## 総括

- must-fix: ambient lookup を identity/config/layout helper から除き、契約を一度だけ明示伝播する。
- must-fix: trigger wrapper の既存 H 削除を廃止し、衝突を fail-closed にする。
- must-fix: contract 拒否が recovery ABORT 追記より前であることを専用 test/mutant で固定する。
- nit: guided 製品入口は exemption 済みだが、2テストの準備呼出しが既定 `True` のまま。
- refuted: validator の恒真性、record-field 由来の必須性、resolver/env 例外の受理 fallback。
- refuted: 現行 repair/recovery の排他区間と mutation 前の検査順。
- refuted: 8事前登録変異の先行層による偽 kill、および matching-resume spy の甘さ。
- pytest は未実走。提示された実測結果は依然 `7 failed / 1157 passed / 10 skipped` であり、緑とは扱わない。