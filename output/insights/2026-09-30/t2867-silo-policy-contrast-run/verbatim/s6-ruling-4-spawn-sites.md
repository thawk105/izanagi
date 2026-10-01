# [T-2867] 本走 wave 段 6 裁定 4 (親、2026-10-01 07:4x JST) — 受入 acc1 の赤 5 件

## 事実

受入 acc1 (tip `cda55eeae` → post-claim merge 後 `aa42a70b0`、main `a3bc25de4`): 5 failed / 28,701 passed / 74 skipped。赤はすべて `orchestrator/tests/test_ccbench_spawn_sites.py`:
`test_deferred_gate_ledger_is_exact_and_every_entry_names_a_live_sink`、`test_define_sink_cross_product_classifies_t2155_production_sinks_exactly`、
`test_define_sink_cross_product_has_no_unreviewed_ungated_member`、`test_define_sink_cross_product_t2520_certify_entry_removal`、`test_ro_gc_publish_build_sink_uses_complete_condition_gate_family`。
一次記録: `/work/1/SFC/tanab/.izanagi-acceptance-shards/ffa5891141dcbe17b8b8f492a49ec3c9/shard-1/dispatcher.log`。

1 件目の本文: `_DEFERRED_GATE_MEMBERS` の項目 `("orchestrator/campaign/p3_s4_loop_policy.py", "wave t2867", "campaign", "<module>.run_stock_control", 446)` を exact に要求する。
`run_stock_control` の `run_campaign(cfg, [genome], perf, …)` の呼出しは、本 wave の driver 修正 (commit `1da88472b`、fixed10 経路の gate 呼出しに 9 行足した) で 446 行 → 455 行へ動いた。

## 裁定

- 帰属: 本 wave の driver 修正 (自分起因、DW-O18)。焦点走に driver の consumer である本試験を入れていなかった親の見落とし (DW-O26)。
- 処置 (Codex fix 子 y): `orchestrator/tests/test_ccbench_spawn_sites.py` の中の、この 1 項目の行番号 `446` の 2 か所 (台帳 `_DEFERRED_GATE_MEMBERS` の定義と、1 件目の試験の期待値) を、
  現行の `p3_s4_loop_policy.py` の該当 `run_campaign` 呼出しの行番号に合わせる。**この 2 つの数値の変更だけを許す** (修正に従属する期待値)。
  項目の他の field、他の項目、他の試験の期待値、driver は変えない。変更後、他の 4 件も緑になることを確かめる (台帳が生きた sink と一致すれば連鎖は解ける、という親の読み。違えば報告して止める)。
- 変更の含意: 受理 — 台帳の項目が現行の呼出し箇所を正しく指す。拒否 — 行番号がずれた項目・未審査の gate なし sink は従来どおり赤になる (台帳の意味は変えない)。
