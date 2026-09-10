# 段 1 brief 追補 — 段 2 起動後に取れた実測

本追補は `s1-brief.md` を置き換えない。段 2 planner 起動後に親が実測した事実を足すだけである。
段 3 レビュアーと段 4 裁定はこの追補も入力に含める。

## A1. 親の (P3) は親自身が反証した (段 4 で正式裁定)

`orchestrator/campaign/p3_s4_loop.py:217-231` の `record_diff_reject` は
`STAGE_BUILD_START` と `STAGE_ABORT` を **`env_tag` 付きで WAL へ書く**。
したがって brief の (P3)「reject 経路は計測しないので guard 対象外でよい」は**成立しない**。
`do_build=False` の dry 経路でも reject は WAL を書くため、誤った env_tag が台帳に残る。
guard は計測直前ではなく **env_tag 付きの永続化より前**に置く必要がある。

## A2. 永続化の順序 (実測)

`drive_iteration` (`p3_s4_loop_trigger_gating.py:439-490`) の順序:

1. `layout.ensure()` — campaign ディレクトリ生成
2. `_write_provenance_header(layout, ...)` — provenance JSON (env_tag を含まない)
3. `L.load_loop_state` / `check_stop`
4. `run_one_iteration(...)` (`:367-`)
   - `layout.ensure()`
   - `ident.ensure_campaign_identity(cfg, layout)` — `campaign.lock` を書く
   - `_quarantine_and_audit(...)` — reject なら **env_tag 付き WAL 書き込み** (A1)
   - `run_campaign(cfg, [genome], perf, ENV_TAG, CLK, numactl=NUMA, ...)` — 計測
5. `_append_provenance_entry` / `save_loop_state` / digest 書き出し

entrypoint は 3 本しかない (`main()` の fixture 経路 → `run_one_iteration` 直呼び、
`main() --run-iteration` → `drive_iteration`、`--preview-diff` → 永続化なし)。
**`run_one_iteration` が env_tag 付き永続化の単一 choke point である。**

## A3. 計算ノード上の site 判定 (実測、request `875967.nqsv`)

Pegasus 計算ノード `bnode114` 上で実測した値:

- `site_policy.current_site()` = `'PEGASUS_COMPUTE'`
- `site_policy.available_cpus()` = 48
- `site_policy.refuses_heavy_work('PEGASUS_COMPUTE')` = **False**

帰結は 2 つある。

- **偽タグ経路は実在する。** 計算ノードでは既存の重処理拒否が効かないので、
  本 driver は今日そのまま走り、2100 clocks/µs の機械の値を
  `env_tag=linux-baremetal` / `clocks_per_us=1800` として WAL へ焼く。
- **過剰拒否リスクも実在する。** 受入テストはまさに `bnode*` 上で走る
  (baseline request `875911.nqsv`、`bnode114`、48 workers)。
  既存の `test_drive_iteration_writes_entry_and_checkpoint`
  (`orchestrator/tests/test_p3_s4_loop_trigger_gating.py:396`) と
  `test_drive_iteration_entry_failure_blocks_checkpoint` (`:434`) は実物の
  `drive_iteration` → `run_one_iteration` → `record_diff_reject` を通る。
  よって `run_one_iteration` 冒頭で `PEGASUS_COMPUTE` を無条件に拒否する guard は、
  **受入環境でこの 2 テストを赤にする**。設計はこの衝突を解かねばならない。

## A4. 正規の注入 seam が既に repo にある (`DW-O14`)

`site` をキーワード引数で受け、`None` のとき `current_site()` へ委譲する形が既存の正規 seam である。

- `orchestrator/campaign/s8a_trigger_coverage.py:91` — `site_policy.current_site() if site is None else site`
- `orchestrator/campaign/s5_permutation_coverage.py:120` — 同型
- `orchestrator/campaign/buildcache.py:337` — `_resolve_site`
- テスト側の使用例は `orchestrator/tests/test_hooks.py:531-817` (`GB.decide(cmd, site="PEGASUS_LOGIN")` 等)

monkeypatch は最後の手段であり、本 wave では不要と親は見ている。

## A5. 構造的な positive control が既存 API で書ける

`orchestrator/campaign/env_contract.py:230` の
`find_env_literals(source, forbidden, allowed_region=None)` は既に汎用公開 API である
(呼び手が禁止 literal 集合を所有する設計)。driver ソースに対し
`forbidden={1800, "--interleave=all"}` で走らせれば、
「値が 1800 であること」ではなく **「値が contract 由来であって再ハードコードされていないこと」**を
構造的に固定できる。`"linux-baremetal"` は forbidden に含めないので免除 region は要らない。

なお `p3_s4_loop_trigger_gating.py` は `orchestrator/tests/test_env_contract.py:61` の
`V2_ENV_NEUTRAL_MODULES` に**含まれていない** (実測)。本 wave で閉包へ足すかは段 4 の裁定事項。

## A7. proof chain の下流実体 (段 3 起動後に確認。段 4 の裁定材料)

`output/campaigns/p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5/reports/layer3_report.json`
(schema `layer3-material-report/v1`) は次を持つ。

- `env_tags` = `["linux-baremetal"]`
- `runs[].run_cmd` に launch 行が逐語で焼かれている:
  `numactl --interleave=all perf stat ... -clocks_per_us=1800 ...`
- `meta.campaign_id` = `p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5`
- `artifact_refs[]` が `campaign.lock` / `runs/wal.jsonl` 等を sha256 で束ねる
- `noise_floor` = null、`noise_floor_provenance` = `"no-matching-env-record"`

したがって `DW-G05` の成果物影響は WAL に留まらない。別 env の計測が混入すると、
**材料レポートの `env_tags` が実態と食い違い、`run_cmd` の `numactl` / `clocks_per_us` が
実際に使われた launch 条件と一致しなくなる**。ここは proof chain の一次資料である。

## A8. 段 2 planner の主張に対する親の裏取り (3 件とも成立)

- 「driver の `CLK` / `NUMA` を外部参照する consumer は無い」→ 成立。
  外部が読むのは `TRIGGER_LOOP.ENV_TAG` だけ (`orchestrator/tests/test_p3_s4_loop.py:168`)。
- 「`test_env_contract.py` に baremetal / pegasus の golden がある」→ 成立
  (`:215` `test_lookup_baremetal_golden`、`:231` `test_lookup_pegasus_golden`)。
- 「campaign_id は `p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5`」→ 成立
  (`layer3_report.json` の `meta.campaign_id` field で確認)。

## A6. 変更前ベースライン (実測、request `875911.nqsv`)

Pegasus 計算ノード / 48 workers で
`test_p3_s4_loop_trigger_gating.py` + `test_p3_s4_loop.py` + `test_env_contract.py` =
**183 passed in 2.33s**、rc=0。段 6 の受入はこの集合と比較する。

**erratum (段 3 レンズ B 所見 7 により訂正、親が一次資料で確認):**
本節は当初 baseline の実行ノードを `bnode114` と書いたが誤りである。
`output/pegasus-dispatch/54354d2cdf7e776ebeede4fd63f45691/{result,receipt,compute-visible}.json`
の 3 つとも **`bnode002`** を記録している。`bnode114` は A3 の probe (`875967.nqsv`) の方である。
pass 数と所要時間は変わらない。

## A9. 親 brief の「8c は未着手 = 前向き」という位置づけは誤り (erratum)

段 3 レンズ B 所見により、親が一次資料で確認した。
`docs/phase3-s8a-trigger-runbook.md` §1(f) 「harness 実走 (single-tenant!)」に、
現行の人手駆動起動経路が逐語で書かれている:

```
python3 -m campaign.p3_s4_loop_trigger_gating --run-iteration <scratch>/prop.json \
    [--extra-source PATH:ROLE ...]
```

したがって本件は「8c が来たら問題になる」前向き hardening ではなく、
**メインセッションが今日この形で起動する経路の穴**である。brief の前提実測の
最後の 1 行 (「8c supervisor が駆動する軸」は前向きの位置づけ) を撤回する。
緊急度は親の当初評価より高い。
