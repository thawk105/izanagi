## 機序の独立検証

親 brief の因果結論に同意する。現物との照合では、次の流れになっている。

1. launcher は [`_driver_configs`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/p3_b4_launcher.py:147) で全 driver の B4 config を作るが、site 射影は trigger にだけ適用している。同ファイル 151-164 行で base config を生成し、165-173 行の射影分岐を通らず返す。

2. launcher は返された config をそのまま [`prepare_launch`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/p3_b4_launcher.py:536) で選び、549 行の `ident.campaign_id(selected_cfg)` により context を束縛する。したがって現状の base context は未射影 ID になる。

3. base driver の [`main`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/p3_s4_loop.py:2448) は、2589-2590 行で site と contract を解決し、2592-2598 行で `default_cfg` を作った後、2599 行で必ず `_campaign_cfg_for_site` を適用する。PEGASUS_COMPUTE では同ファイル 153-160 行により `search_config["measurement_env"] = "pegasus"` が加わる。

4. `measurement_env` は [`ident.canonical_preimage`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/ident.py:196) の `search_config` に含まれ、226-235 行のハッシュと campaign ID を変える。このため launcher の未射影 ID と driver の射影済み ID が異なる。

5. 実際の正式経路は `main` 2694-2705 行から `drive_iteration` へ入り、[`p3_s4_loop.py:2346`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orbranches/dev-wave-t2316-b4-base-site/orchestrator/campaign/p3_s4_loop.py:2346) ではなく、正しい worktree path の [`p3_s4_loop.py:2346`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/p3_s4_loop.py:2346) にある最初の production context 検査へ達する。ここでは2335行で既に射影された config の IDを要求するため、現状の launcher context を拒否する。build 本体は1814行以降、`run_campaign` は1857行なので、それより前に停止する。

6. sidecar/layout も bootstrap の [`p3_b4_launcher.py:567-570`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/p3_b4_launcher.py:567)、continuation の620-625行で launcher 側 config の IDを使うため、現状は driver の射影済み layout と分裂する。

親 brief の行番号には小さなずれがある。base `main` の射影は「2588-2598」ではなく2599行、launcher の `ident.campaign_id` は548行ではなく549行である。因果そのものは正しい。

## 変更プラン (file:line)

変更対象は [`orchestrator/campaign/p3_b4_launcher.py:147-174`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/p3_b4_launcher.py:147) の `_driver_configs` のみ。現行 trigger 分岐と対称に base 固有分岐を追加する。

変更後の関数全体は次の形にする。

```python
def _driver_configs(
    driver_kind: DriverKind,
    context: B4LaunchContext,
) -> tuple[Any, Any]:
    if driver_kind == "base":
        factory = p3_s4_loop.default_cfg
    elif driver_kind == "sort":
        factory = p3_s4_loop_sort.default_cfg
    else:
        factory = p3_s4_loop_trigger_gating.default_cfg
    configs = tuple(
        factory(
            reflux=reflux,
            b4_reflux_ablation=True,
            _b4_launch_context=context,
        )
        for reflux in (True, False)
    )
    if driver_kind == "base":
        site = p3_s4_loop._current_site()
        contract = p3_s4_loop._admit_env_contract(site)
        configs = tuple(
            p3_s4_loop._campaign_cfg_for_site(
                cfg, site, _contract=contract,
            )
            for cfg in configs
        )
    elif driver_kind == "trigger":
        site = p3_s4_loop_trigger_gating._current_site()
        contract = p3_s4_loop_trigger_gating._admit_env_contract(site)
        configs = tuple(
            p3_s4_loop_trigger_gating._campaign_cfg_for_site(
                cfg, site, _contract=contract,
            )
            for cfg in configs
        )
    return configs
```

base は [`p3_s4_loop.py:123`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/p3_s4_loop.py:123) の `_current_site`、138-145行の `_admit_env_contract`、147-161行の `_campaign_cfg_for_site` をこの順で呼ぶ。trigger は既存の [`p3_b4_launcher.py:165-173`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/p3_b4_launcher.py:165) をそのまま保存する。

`if base / elif trigger` と明記し、sort は両分岐を通らず現在どおりの config を返す。driver module と helper 名を一般 dispatch 表へまとめない。

## (P1) 判定

- **(P1-a): real。ただし正式 launcher 経路に限定する。**  
  `prepare_launch` は `_driver_configs` の返り値から ID を束縛するだけなので、base 分岐追加が自動的に549行へ反映される。bootstrap は567-580行、continuation は593-633行で同じ返却 config と context を再利用する。この3関数の変更は不要である。正式経路は base `main` から `drive_iteration` へ進み、後述のとおり射影済み ID 同士で一致する。

- **(P1-b): real。launcher 側の追加 bind は不要。**  
  base の [`default_cfg`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/p3_s4_loop.py:1397) は1427-1428行ですでに `ident.bind_admission_policy` を適用する。trigger も [`p3_s4_loop_trigger_gating.py:583-621`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/p3_s4_loop_trigger_gating.py:583) で同じ構造であり、現行 launcher の trigger 射影には追加 bind がない。[`ident.bind_admission_policy`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/ident.py:84) は異なる既存 policy を92-93行で拒否し、同じ policy 内容を94-97行で維持する。

- **(P1-c): real。**  
  PEGASUS_COMPUTE の `_campaign_cfg_for_site` は同じ `"measurement_env": "pegasus"` を辞書 merge で再設定するだけで、OTHER はその key を追加しない。続く [`ident.bind_environment_contract`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/ident.py:100) は、既に同じ contract が束縛されていれば113-118行で元の config を返し、異なる contract なら拒否する。したがって同じ site/contract による二重射影は campaign ID を変えない。driver `main` の2599行と `drive_iteration` の2335行による実際の二重射影も安全である。

OTHER では `search_config` が変わらず、runtime の `bound_environment_contract` は [`canonical_preimage`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/ident.py:196) の対象外なので campaign ID は従来値を保つ。

## 授権境界 3 箇所の照合

| 授権境界 | その地点の config | 修正後の正式 launcher ID との関係 |
|---|---|---|
| [`p3_s4_loop.py:2346`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/p3_s4_loop.py:2346) `base drive_iteration` | 2335行で射影済み。正式 `main` からは2599行でも射影済みで、2704-2705行から同じ site/contract が渡る | 一致する。正式経路の最初の境界 |
| [`p3_s4_loop.py:1742`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/p3_s4_loop.py:1742) `base resolved run_one_iteration` | `drive_iteration` の2409-2419行から射影済み config が渡る。公開 `run_one_iteration` 経由でも1909-1916行で射影後、1928行から渡る | 一致する |
| [`p3_s4_loop.py:1896`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/p3_s4_loop.py:1896) `base run_one_iteration` | site 解決1907行、射影1909行より前なので、関数へ渡されたまま | 正式 launcher 経路では到達しない。直接 API caller が raw `default_cfg` を渡すと不一致、事前射影済み config を渡せば一致 |

したがって正式な `p3_b4_launcher -> p3_s4_loop.main -> drive_iteration -> _run_one_iteration_resolved` 経路には不一致は残らない。

ただし1896行の公開 `run_one_iteration` 境界は、直接 caller が未射影 config を渡す場合の条件付き不一致を残す。この関数は正式 launcher から呼ばれておらず、`main` 自身も2694行で `drive_iteration` を選ぶため、T-2316 の実到達経路外である。ここを動かすには `p3_s4_loop.py` の境界順序変更が必要になり、今回の限定 scope には含めない。直接 B4 API を将来正式化するなら別 task で扱う。

## test 設計

現在の [`test_p3_b4_launcher.py`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/tests/test_p3_b4_launcher.py:1) に対する静的 `rg` では、`site`、`PEGASUS`、`measurement_env` はいずれも0件だった。次を追加する。

- import 群15-24行へ `site_policy` を追加する。
- 既存の `_test_context` 35-39行、`_production_context` 58-74行、`_committed_admission_fixture`、`monkeypatch` と `DRIVER_REGISTRY` 差し替えの書式319-386行を再利用する。

追加 node:

1. `test_base_launcher_pegasus_context_matches_driver_authorization`

   - `site_policy.socket.gethostname` を `lambda: "bnode116"` に差し替え、`site_policy.current_site()` が `PEGASUS_COMPUTE` を返すことを最初に確認する。
   - `_committed_admission_fixture` と tmp 配下の `exploration_campaign_layout` を使い、既存 bootstrap test と同様に `B4L.launch_bootstrap(driver_kind="base", arm="on", ...)` を呼ぶ。
   - registry の base driver spy 内で、実 driver `main` と同じ順序で `L._current_site()`、`L._admit_env_contract()`、`L.default_cfg(...)`、`L._campaign_cfg_for_site(...)` を実行する。
   - `measurement_env == "pegasus"` を確認し、spy が受け取った launcher context に対して実物の `B4L.require_b4_production_context` を呼ぶ。
   - `expected_campaign_id=str(ident.campaign_id(driver_cfg))` で受理されること、sidecar の campaign ID と同じことを pin する。これにより `_driver_configs`、`prepare_launch`、context binding、driver 要求 ID を一本で覆う。

2. `test_base_unprojected_pegasus_context_is_rejected_by_driver_authorization`

   - 同じ hostname seam で PEGASUS_COMPUTE を解決する。
   - `L.default_cfg(..., b4_reflux_ablation=True)` の未射影 config と、それへ `_campaign_cfg_for_site` を適用した driver config を作り、両 ID が異なることを確認する。
   - `_production_context(unprojected_cfg)` で旧 launcher 相当の未射影 ID に束縛された production context を作る。
   - 射影済み driver ID を `expected_campaign_id` として実物の `require_b4_production_context` を呼び、`B4LauncherAuthorizationError` の `"campaign id differs"` を確認する。比較自体を差し替えず、現行の厳密な拒否力を positive control とする。

3. `test_base_launcher_other_preserves_campaign_ids`

   - hostname resolver を通常名、例えば `"developer-host"` にし、`current_site() == OTHER` を確認する。
   - `_test_context` で作った raw base on/off config と、`B4L._driver_configs("base", context)` の on/off を比較する。
   - 両 arm で `measurement_env` が追加されず、campaign ID が raw config と同一であることを確認する。これが OTHER の既存 campaign ID 非回帰を直接 pin する。

正規の site 注入 seam は環境変数ではなく hostname resolver である。[`site_policy.classify_site`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/site_policy.py:30) は36行で `environ` を明示的に捨て、40-42行で `bnode[0-9]+` を PEGASUS_COMPUTE と分類する。`current_site` には site 注入引数がなく、73行で `socket.gethostname()` を読む。このため helper 自体を偽装せず、最下層の hostname resolver だけを `monkeypatch` するのが最小かつ実経路を通す seam である。`L._current_site` は123行で `site_policy.current_site` を既に alias しているため、`site_policy.current_site` 自体の差し替えは避ける。

pytest はこの段では実走しない。上記は段6で実測する node 設計である。

## 触らない面

- [`p3_s4_loop.py`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/p3_s4_loop.py): driver 側の site 射影と3つの厳密な授権境界は変更しない。特に133-145行の exact site allowlistを広げず、1742、1896、2346行の campaign ID 比較を弱めない。
- [`p3_s4_loop_trigger_gating.py`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/p3_s4_loop_trigger_gating.py): trigger の挙動は変更しない。633-662行の `_with_campaign_location` / `_assert_layout_matches_campaign` を base へ移植しない。
- `orchestrator/campaign/p3_s4_loop_sort.py`: sort はT-2318のscope。helper 3点を仮定した一般 dispatch を作らず、launcher の既存 sort factory 選択だけを保存する。
- [`site_policy.py`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/site_policy.py): classifier、未知 site の扱い、環境判定を変更しない。
- [`ident.py`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/ident.py): admission policy、environment contract、campaign ID の定義を変更しない。
- [`p3_b4_launcher.py:316-364`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/p3_b4_launcher.py:316): production context validator と campaign ID 一致要求には触れない。
- `orchestrator/tests/acceptance_duration_ledger.json`: author 差分では触れない。新 node の段6実測後、親が実測時間を得てから main 取り込み後の運用追記を行う。
- 新 gate、台帳、一般化、命名整理、型注釈整理は追加しない。

## 総括

T-2316 の実装差分は、launcher の `_driver_configs` に base 専用の3手射影を追加し、launcher test に PEGASUS_COMPUTE の受理、未射影の拒否、OTHER の ID 非回帰を加えるだけで閉じる。

正式 base 経路では、launcher context、sidecar layout、`drive_iteration`、resolved iteration の全 ID が射影済み campaign ID に揃う。sort、trigger、厳密な授権比較、未知 site の fail-closed、OTHER の campaign ID は変更しない。静的読解のみであり、pytest は実走していない。