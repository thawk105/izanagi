# 段 1 brief — [T-2231]+[T-2199] 段 4 loop へ site-aware な環境契約配線を移植する

- 基準 commit: c7ed56589 (local main)、branch worktree-dev-wave-t2231-s4-loop-site-env
- 正本: worklog carry [T-2231]/[T-2199] (entry 1212 = docs/archive/worklog-phase3-0902-1212.md:425,459)

## scope

`orchestrator/campaign/p3_s4_loop_trigger_gating.py` に既にある site-aware 配線を
`orchestrator/campaign/p3_s4_loop.py` へ**移植する**。新設ではない。移植する形は 4 つ。

1. `_SITE_ENV_TAGS` (OTHER→"linux-baremetal"、PEGASUS_COMPUTE→"pegasus") と `_CAMPAIGN_ENV_KEY`
2. `_site_admits_measurement` / `_admit_env_contract` / `_campaign_cfg_for_site`
3. `run_campaign` 呼出しを `contract.env_tag` / `env_contract.authorize(contract.env_tag)` へ
4. 公開 API の `_resolved_site` / `_contract` 注入 (両方同時必須、片方だけは TypeError)

## 確定済みユーザー裁定

- 実行場所は Pegasus で決着済み ([T-2199]、D59 の 4 前提をこの job について満たす方向)。
- [T-2232] の Pegasus job script は本 wave の scope 外。
- 次に出る障害 (attestation の exact 照合、reservation と claim root の束縛) は未実測の予測であり、
  先回りして実装しない。
- 仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外 (DW-G05)。

## 実測した前提 (brief 時点、2026-09-03 20:25 JST)

- 本 job の実行場所は `pegasus02` = `site_policy.PEGASUS_LOGIN`。`_site_admits_measurement` は
  {OTHER, PEGASUS_COMPUTE} だけを許すので **login node では fail-closed で raise する**。
  これは意図された挙動だが、`_current_site()` を直に呼ぶ経路を持つ既存テストは
  この機体で赤になりうる。移植は `_resolved_site`/`_contract` 注入込みでなければ成立しない。
- 契約の実値: pegasus = clk 2100 / numactl 空 / allow_resume=False。
  linux-baremetal = clk 1800 / numactl ("numactl","--interleave=all") / allow_resume=True。
  移植先の module 定数 `CLK=1800` / `NUMA=["numactl","--interleave=all"]` は前者と食い違う。
- `p3_s4_loop.py` は `execution_guard` と `site_policy` を未 import (`replace` は import 済み)。
- 既存 campaign directory `p3-s4-loop-s4-autonomous-0b53a387` が campaign output 配下に存在する。

## 不変条件

- **site=OTHER での campaign identity を 1 bit も変えない。** `_campaign_cfg_for_site` は
  OTHER のとき `search_config` を触らず `ident.bind_environment_contract(cfg, contract)` だけを行う
  = 現行コードと同一。上記既存 campaign の campaign_id が変わってはならない。
- 未知 site は fail-closed。既知 site 集合を暗黙に広げない (規律 2 を緩めない)。
- 計測層以外の数値を混ぜない。異なる env-tag の throughput を混ぜない (D59)。
- 実装面は Codex `role=author` が書く (D95)。親は docs だけ書く。

## 成果物

- `orchestrator/campaign/p3_s4_loop.py` の移植差分
- `orchestrator/tests/test_p3_s4_loop.py` の site 注入テスト (trigger 版 L2725/L4036-4089 と同型)
- 段 7 の worklog / insights fragment

## 割れうる前提 (親の provisional 裁定・攻撃対象)

- **(P1) CLK / NUMA も contract 由来へ移す。** 移植元の `run_campaign` 呼出しは
  `contract.clocks_per_us` / `list(contract.numactl)` を渡している。「run_campaign 呼出しの形を写す」
  の文字どおりの読みではこれも含まれる。module 定数 `CLK` / `NUMA` は残すが呼出しでは使わない。
  反論があれば段 3 で攻撃してよい。
- **(P2) `campaign_options["env_contract"]` と `dependency_prefix` の PEGASUS_COMPUTE 分岐は移植する。**
  これがないと Pegasus で run_campaign が契約を受け取れず、移植の目的 (build 到達) を満たさない。
- **(P3) `_assert_resume_allowed` と `_receipt_provenance` / `_append_provenance_entry` は scope 外。**
  前者は allow_resume=False の pegasus で効く安全弁だが、carry が名指ししていない。後者は
  provenance 台帳の新設に当たり DW-G05 に抵触する。段 3 の攻撃対象とし、段 4 で裁定する。
- **(P4) 移植先の 4 つの `ident.bind_environment_contract(cfg, env_contract.lookup(ENV_TAG))`
  (L1090/L1417/L1809/L2036) のうち、どこまでを site 解決へ差し替えるか。** provisional には
  `default_cfg` (L1090) は ENV_TAG のまま残し、iteration 経路 (L1417/L1809) と main (L2036) を
  site 解決へ移す。移植元も `default_cfg` 相当は触っていない。

## 並列分割方針

段 2 プラン 1 本 → 段 3 敵対 2 本 (レンズ A: 移植忠実性と受理集合、レンズ B: identity 不変と
既存テスト破れ) → 段 5 実装子 1 本 (単一 file + そのテストで所有が割れない) → 段 6 レビュー 2 本 + fix 1 本。
正しさ防壁 (計測 site の受理集合) に触るため軽量版にはしない。
