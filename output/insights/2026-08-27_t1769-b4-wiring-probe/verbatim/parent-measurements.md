# 親の実測 (段 1〜段 4 で親自身が測った値)

## M-P1 — 生死確認 (DW-G01)

```
python3 tools/run_tests.py orchestrator/tests/test_p3_s4_loop.py -k "make_critic_digest or reflux" -q
→ 10 passed in 6.70s
Pegasus dispatch request 951477.nqsv (Elapse 13S)
```
検査 2 (on で赤詳細)、検査 3 (off で 4 loader 不呼出し + byte 一致)、検査 4 (identity 分離) は
build 無し・in-process で観測可能。専用機構の前の最安確認はこれで足りる。

## M-P2 — 既存 CLI が probe にならない根拠 (file:line)

`orchestrator/campaign/p3_s4_loop.py:1508`

```python
    if do_build and out["outcome"] != "dry-pass":
        critic_view = require_admitted_campaign(...)
        digest_txt = make_critic_digest(
```

切替点は `do_build` の内側にある。したがって `--no-build` 経路は切替点へ到達しない。
事前登録 §10 の主張は実装と一致する (文書の主張を実測で裏取りした)。

さらに `p3_s4_loop.py:1576` が `--b4-reflux-ablation` と `--no-build` の同時指定を
`B4ProtocolError` で拒否する。3 driver とも同型 (sort:579、trigger:1118)。

## M-P3 — 3 driver の還流配線 (検査の分解)

|driver|`default_cfg(reflux=)`|`make_critic_digest` へ渡す式|
|---|---|---|
|`p3_s4_loop`|892 行|1516 行 `cfg.search_config.get("reflux") == "on"` / 1724 行 `a.reflux == "on"`|
|`p3_s4_loop_sort`|249 行|509 行 `cfg.search_config.get("reflux") == "on"` / 698 行 同左|
|`p3_s4_loop_trigger_gating`|548 行|1039 行 `cfg.search_config.get("reflux") == "on"`|

**分解:** 検査 2・3 は共有関数 `make_critic_digest` の性質であり driver 非依存。
driver ごとに固有なのは検査 1 (自分の CLI 経路が切替点へ到達するか) と
検査 4 (自分の `default_cfg` が identity を分離するか) の 2 つだけである。
親 brief の一般化はこの分解の範囲で成立する。

## M-P4 — 新規 file が発火させる内容走査型の一覧検査 (名前 grep で見つからない型)

親が独立に見つけたもの。段 2 プランの列挙と突き合わせる。

1. `orchestrator/tests/test_p3_exploration_namespace.py:73` `_is_campaign_root_creator`
   AST 述語: 呼出し名集合に `exploration_campaign_layout` を含み、かつ
   `run_campaign` 呼出しか `CampaignLayout` 呼出しを含む module は
   **exploration campaign driver として自動的に発見される**。
   発見されると `_campaign_driver_is_closed` (100 行) が
   module level の `DECLARED_USE_CLASS == "exploration"` を要求する。
   → probe が identity 分離を測るために `exploration_campaign_layout` と
   `CampaignLayout` の両方を呼ぶと、この gate に入る。

2. `orchestrator/tests/test_p3_build_authority_cli.py:1189`
   `test_python_ccbench_manual_materializers_are_explicitly_non_admissible`
   `orchestrator/campaign/*.py` のうち本文に文字列 `--build` を含む file 名の集合が
   `MANUAL_BUILD_FILES` と **exact 一致**すること。`buildcache.py` だけが除外。
   → probe の source に `--build` という literal が現れると (help 文・コメントを含む)
   この集合検査が赤になる。

これらは file 名や関数名の grep では見つからない。段 2 プランがこの 2 件を
拾えていなければ、そこが最初の実測赤になる。

## M-P5 — 権威 anchor の逆到達 (段 2 プランの核心前提を親が実測)

`orchestrator/campaign/execution_guard.py:107`
`def require_certified_writer_authorization(...)` は**実在する** (プランの主張と一致)。

production の直接呼び手 (tests を除く全数):
- `orchestrator/campaign/loop.py:165`
- `orchestrator/campaign/pipeline.py:864` (`evaluate` は 705 行定義。864 は同関数の内側)
- `orchestrator/campaign/s1_direct_comparison.py:796`
- `orchestrator/campaign/screening_driver.py:208, 295`

逆到達の実測:
- `p3_s4_loop.run_one_iteration` (1066 行) は 1166 行で `run_campaign(...)` を呼ぶ。
  `run_campaign` は `loop.py:165` で anchor を呼ぶ。
  **したがって逆閉包は `run_one_iteration` を捕まえる。**

**非恒真性の判定 (レンズ A の軸 1 に親が先に答えたもの):**
目録に載り、かつ probe が誤って呼びうる実体は実在する — probe が import する
まさにその driver module の `run_one_iteration` / `drive_iteration` / `main` である。
したがって遮断集合は「probe が呼ばないもの」から導かれた恒真ではない。

## M-P6 — probe が正当に呼ぶ実体が遮断集合に入らないこと

`p3_s4_loop.record_diff_reject` (370 行) の本体は `wal.log(...)` 2 回だけであり、
anchor へ到達しない。したがって probe は fixture の赤記録を作れる。

`make_critic_digest` (558 行) も anchor の呼び手ではない。逆閉包は anchor の**呼び手**を
集めるので、`make_critic_digest` は集合に入らない。設計の自己矛盾はない。

**ただし段 6 で実測すべき点:** 目録に `make_critic_digest` / `default_cfg` /
`record_diff_reject` / `require_admitted_campaign` が入っていないことを
実際の目録 JSON で確認する。入っていれば probe は自分の検査を実行できず、
静かに緑になるのではなく落ちる (fail-loud) が、原因が分からなくなる。
