# 親の実測値 (段 3 相談への入力)

probe script の逐語: `/home/SFC/tanab/.claude/jobs/f8a552e6/tmp/t2316/probe_site.py`
(repo 外に置き、worktree を `sys.path` に入れて実行した。repo 内には何も書いていない)

## 実測 1 — site 別の campaign ID 影響

`site_policy.socket` を `SimpleNamespace(gethostname=lambda: <名前>)` へ差し替えた上で
`p3_s4_loop.default_cfg(reflux=..., b4_reflux_ablation=True, _b4_launch_context=<test context>)`
を作り、`_campaign_cfg_for_site` の前後で `ident.campaign_id` を比べた。
test context は `B4L.create_b4_launch_context_for_test(driver_kind="base", arm="on")` で作った。

```
--- hostname='test-host' -> site=OTHER
    contract.env_tag=linux-baremetal
    reflux=True  before=p3-s4-loop-s4-autonomous-4e54b9ea
    reflux=True  after =p3-s4-loop-s4-autonomous-4e54b9ea  changed=False
    reflux=True  twice =p3-s4-loop-s4-autonomous-4e54b9ea  idempotent=True
    reflux=True  measurement_env=None
    reflux=False before=p3-s4-loop-s4-autonomous-7a8e044f
    reflux=False after =p3-s4-loop-s4-autonomous-7a8e044f  changed=False
    reflux=False twice =p3-s4-loop-s4-autonomous-7a8e044f  idempotent=True
    reflux=False measurement_env=None
--- hostname='bnode116' -> site=PEGASUS_COMPUTE
    contract.env_tag=pegasus
    reflux=True  before=p3-s4-loop-s4-autonomous-4e54b9ea
    reflux=True  after =p3-s4-loop-s4-autonomous-c510996c  changed=True
    reflux=True  twice =p3-s4-loop-s4-autonomous-c510996c  idempotent=True
    reflux=True  measurement_env='pegasus'
    reflux=False before=p3-s4-loop-s4-autonomous-7a8e044f
    reflux=False after =p3-s4-loop-s4-autonomous-f33bb5d8  changed=True
    reflux=False twice =p3-s4-loop-s4-autonomous-f33bb5d8  idempotent=True
    reflux=False measurement_env='pegasus'
--- hostname='pegasus02' -> site=PEGASUS_LOGIN
    _admit_env_contract RAISED: ExecutionGuardError:
        計測用 env bytes は site='PEGASUS_LOGIN' では生成できない
```

## 実測 2 — この wave が走っているホスト

`hostname` = `pegasus02`。`site_policy.current_site()` = `PEGASUS_LOGIN`。
`_site_admits_measurement` の許可集合は `{OTHER, PEGASUS_COMPUTE}` なので **PEGASUS_LOGIN は許可外**。

`classify_site` は 4 値を返しうる — `OTHER` / `PEGASUS_COMPUTE` / `PEGASUS_LOGIN` / `PEGASUS_SUSPECT`。
親 brief は当初これを 2 値と読み違えていた。訂正済み。

## 実測 3 — pytest 下の site

`orchestrator/tests/conftest.py:244-253` が `module.socket` を
`SimpleNamespace(gethostname=lambda: "test-host")` へ差し替え、`current_site` 本体は温存する。
したがって pytest 下では site=OTHER に解決される。

## 実測 4 — 変更対象関数の既存呼び手

`B4L._driver_configs` の repo 内呼び手は次のとおり (worktree で grep)。
`orchestrator/tests/test_p3_b4_closed_critic.py` に 8 箇所ある。

```
test_p3_b4_closed_critic.py:180  def _marked_driver_configs(driver_kind="base"):
test_p3_b4_closed_critic.py:185      return B4L._driver_configs(driver_kind, config_context)
test_p3_b4_closed_critic.py:532      on_cfg, off_cfg = B4L._driver_configs(driver_kind, config_context)
test_p3_b4_closed_critic.py:819      on_cfg, off_cfg = _marked_driver_configs()
test_p3_b4_closed_critic.py:1002     on_cfg, off_cfg = _marked_driver_configs()
test_p3_b4_closed_critic.py:1029     on_cfg, off_cfg = _marked_driver_configs()
test_p3_b4_closed_critic.py:2322     on_cfg, off_cfg = _marked_driver_configs()
test_p3_b4_closed_critic.py:2702     on_cfg, off_cfg = B4L._driver_configs("base", config_context)
```

既存の trigger 側 test は `test_p3_b4_closed_critic.py:168` で
`TRIGGER_LOOP._current_site` を `return_value=trigger_site` へ patch している。
base 側には対応する patch が無い。

## 実測 5 — 前提と閉包

- `[T-2232]` の Pegasus job script 着地: `6bf28173c` は local main HEAD (`cbcdb6c91`) の祖先。
- `p3_b4_launcher.py` の blob sha `139a9cf1bf71d0119c13906328990298196d0256` と
  file の sha256 `294888f6fa49444c90f5a38fe7b7e417fce57e70fa34faf713fa20c6a7f48513` を
  tracked file 全体へ検索 → **0 件**。凍結 bytes の hash pin は無い。
- ただし `p3_b4_launcher.py` は `campaign_lock.py:93` の enforcement source 一覧に載り、
  `p3_b4_closed_critic.py:649` の proof chain 記録対象でもある。
- `orchestrator/tests/test_p3_b4_launcher.py` には `site` / `PEGASUS` / `measurement_env` の
  出現が 0 件。trigger 分岐すら test で押さえられていない。
