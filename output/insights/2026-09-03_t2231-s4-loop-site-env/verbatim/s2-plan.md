## プラン

- [p3_s4_loop.py:62-65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/campaign/p3_s4_loop.py:62): import 群へ `execution_guard` と `site_policy` を追加する。移植元は `p3_s4_loop_trigger_gating.py:57-58`。

- `p3_s4_loop.py:112-114`: `ENV_TAG`、`CLK`、`NUMA` は残し、直後へ以下を追加する。移植元は `p3_s4_loop_trigger_gating.py:103-111`。

  ```python
  _SITE_ENV_TAGS = {
      site_policy.OTHER: ENV_TAG,
      site_policy.PEGASUS_COMPUTE: "pegasus",
  }
  _CAMPAIGN_ENV_KEY = "measurement_env"
  _current_site = site_policy.current_site
  _lookup = env_contract.lookup
  ```

- `p3_s4_loop.py:484` の diff-reject 節直前へ、移植元 `p3_s4_loop_trigger_gating.py:444-472` と同型で次を追加する。

  ```python
  def _site_admits_measurement(site: str) -> bool
  def _admit_env_contract(
      site: str,
  ) -> env_contract.ExecutionEnvironmentContract
  def _campaign_cfg_for_site(
      cfg: CampaignConfig,
      site: str,
      *,
      _contract: Optional[env_contract.ExecutionEnvironmentContract] = None,
  ) -> CampaignConfig
  ```

  `_site_admits_measurement` は `{OTHER, PEGASUS_COMPUTE}` の exact set のみ許可する。`_admit_env_contract` は admission を先に検査し、拒否時は `ExecutionGuardError`、許可時だけ `_lookup(_SITE_ENV_TAGS[site])` を行う。`_campaign_cfg_for_site` は `PEGASUS_COMPUTE` の場合だけ `search_config["measurement_env"]="pegasus"` を追加し、最後に `ident.bind_environment_contract` を行う。

- [p3_s4_loop.py:510-513](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/campaign/p3_s4_loop.py:510): `record_diff_reject` の署名と `env_tag: str = ENV_TAG` は互換性のため残す。ただし production 経路である `run_one_iteration` 内の三呼出し `:1454-1457`、`:1475-1478`、`:1486-1489` はすべて `env_tag=contract.env_tag` を明示する。移植元の adapter は `p3_s4_loop_trigger_gating.py:511-519`。

- [p3_s4_loop.py:1058-1090](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/campaign/p3_s4_loop.py:1058): `default_cfg` は admission policy を bind した cfg を返すが、環境契約はまだ bind しない形へ変える。すなわち `:1090` の `ident.bind_environment_contract(...ENV_TAG...)` を外す。移植元の `default_cfg` も環境未束縛で返す `p3_s4_loop_trigger_gating.py:620-621`。これは P4 の必須修正であり、理由は後述する。

- [p3_s4_loop.py:1374-1418](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/campaign/p3_s4_loop.py:1374): `run_one_iteration` の既存 positional 引数を維持したまま、末尾へ次の keyword-only 引数を追加する。

  ```python
  *,
  dependency_prefix: str = "",
  _resolved_site: Optional[str] = None,
  _contract: Optional[env_contract.ExecutionEnvironmentContract] = None,
  ```

  B4 の既存 launcher gate 後に、移植元 `p3_s4_loop_trigger_gating.py:1013-1028` の三分岐を置く。両方未指定なら `_current_site()` と `_admit_env_contract()` で解決し、片方だけなら `TypeError`、両方指定なら admitted site と `_SITE_ENV_TAGS[site] == contract.env_tag` を検査する。その後 `:1417` を `_campaign_cfg_for_site(cfg, resolved_site, _contract=contract)` へ置き換える。移植元の公開入口での解決順は `:889-893`。

- `p3_s4_loop.py:1493-1502`: `run_campaign` 呼出し直前に移植元 `p3_s4_loop_trigger_gating.py:802-810` と同じ `campaign_options` を組む。`PEGASUS_COMPUTE` の場合だけ `env_contract=contract` を渡し、さらに非空の `dependency_prefix` だけを渡す。呼出し本体は移植元 `:811-819` と同型で次へ差し替える。

  - `ENV_TAG` → `contract.env_tag`
  - `CLK` → `contract.clocks_per_us`
  - `NUMA` → `list(contract.numactl)`
  - `env_contract.authorize(ENV_TAG)` → `env_contract.authorize(contract.env_tag)`
  - 末尾に `**campaign_options`

- [p3_s4_loop.py:1783-1812](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/campaign/p3_s4_loop.py:1783): `drive_iteration` にも、既存 positional 引数を維持して `dependency_prefix`、`_resolved_site`、`_contract` の keyword-only 引数を追加する。`_assert_coder_value_domain` 後に同じ三分岐を置き、`:1809` を `_campaign_cfg_for_site` へ置き換える。`:1881-1884` の `run_one_iteration` 呼出しには、解決済みの三値を渡して実 hostname を再解決させない。移植元は `p3_s4_loop_trigger_gating.py:995-1031,1118-1126`。

- [p3_s4_loop.py:1912-2037](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/campaign/p3_s4_loop.py:1912): `main` にも `_resolved_site` / `_contract` の paired injection を追加する。CLI の既存引数整合 gate `:1957-1974` より後、最初の出力や layout 導出より前に一度だけ解決する。

  - `--emit-planner-context` 経路 `:1979-2011` でも、`default_cfg` の直後かつ knowledge bind より前に `_campaign_cfg_for_site` を適用する。これを外すと compute の planner context と実 iteration が別 campaign_id になる。
  - 通常経路の `:2036` も同じ helper へ置換する。
  - `drive_iteration` `:2086-2095` と fixture の `run_one_iteration` `:2121-2123` へ同じ pair を渡す。

- `_assert_resume_allowed`、`_receipt_provenance`、`_append_provenance_entry` はこのプランには追加しない。移植対象を親 brief の四形に留め、trigger 固有 provenance 台帳も新設しない。

## テスト計画

- [test_p3_s4_loop.py:75-82](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/tests/test_p3_s4_loop.py:75): `OTHER` とその契約を返す小さな test helper を置き、既存の base `run_one_iteration` / `drive_iteration` / `main` 呼出しへ `_resolved_site` と `_contract` を必ず一緒に渡す。対象は現行 `:591`、`:2469`、`:3502`、`:3600-3643`、`:3973`、`:4235-4751`、`:4825`、`:5652-5747`、`:5842-6172` 周辺。赤条件: 注入 pair が入口間で失われ、実機 `pegasus02` の login 判定へ落ちるか、対象テスト本来の gate より先に site 解決が走ること。

- `test_p3_s4_loop.py:2986-3015` 直後に `test_s4_site_admission_matrix_is_closed` を追加する。`OTHER` / `PEGASUS_COMPUTE` だけが真で、`PEGASUS_LOGIN` / `PEGASUS_SUSPECT` / 任意未知値は偽、拒否値では `_lookup` 未到達を検査する。赤条件: 既知 site 集合が広がるか、拒否 site が契約 lookup へ到達すること。

- 同位置に `test_s4_injected_site_and_contract_are_an_atomic_pair` を追加する。片方だけの二ケースが `TypeError`、login と site-contract 不一致が `ExecutionGuardError`、正しい両方指定時は `_current_site` が未呼出しであることを検査する。形は既存 `test_p3_s4_loop.py:4036-4082` の trigger 注入を踏襲する。赤条件: partial injection、host 再解決、site-contract の取り違えが通ること。

- 同位置に `test_s4_other_identity_is_unchanged_and_compute_is_split` を追加する。未束縛 `default_cfg()`、OTHER 適用後、同じ OTHER の再適用について `ident.canonical_preimage` と `campaign_id` が完全一致し、`measurement_env` が無いことを確認する。compute は `measurement_env="pegasus"` を持ち別 ID になることを確認する。現行 golden `test_p3_s4_loop.py:4185-4189` は更新しない。赤条件: OTHER の search_config/preimage が一文字でも変わるか、compute が同じ namespace に入ること。

- `test_p3_s4_loop.py:540-606` の既存 run_campaign spy を拡張するか、直後に `test_s4_selected_contract_values_flow_to_run_campaign` を追加する。同じ `env_tag` の contract を `replace` して clocks と numactl に sentinel を入れ、`ENV_TAG` / `CLK` / `NUMA` ではなくその exact 値、同じ env_tag の authorization が渡ることを確認する。赤条件: module 定数への逆戻り、再 lookup、numactl 空 tuple の取り違えが起きること。

- 同じ build-spy fixture で `test_s4_compute_forwards_env_contract_and_dependency_prefix` を追加する。注入した `PEGASUS_COMPUTE` / pegasus contract と sentinel prefix が `run_campaign` へ届き、OTHER では両 option が省略されることを検査する。赤条件: compute が legacy build seamへ流れる、prefix が落ちる、または OTHER の既存呼出し形が変わること。

- `test_p3_s4_loop.py:5930-6064` の reject tests を site 注入対応にし、`test_s4_compute_reject_records_pegasus_env_tag` を追加する。preflight、dry quarantine、build quarantine の三 reject 分岐について WAL の `env_tag` が `contract.env_tag` になることを検査する。赤条件: `record_diff_reject` の既定 `linux-baremetal` が compute WAL に漏れること。

- `test_p3_s4_loop.py:5627-5705` の `test_emit_context_and_run_iteration_share_manifest_campaign_identity` を OTHER 注入で hermetic 化し、compute 注入ケースも加える。赤条件: `main` の planner-context 早期 return が site projection を迂回し、run-iteration と異なる campaign_id を使うこと。

- `test_p3_s4_loop.py:4174-4196` の既存 golden は保持する。加えて `default_cfg().bound_environment_contract is None` と、OTHER を bind 後も既存 ID が同じことを検査する。赤条件: `default_cfg` が linux contract を先行 bindして compute projection を再び不可能にするか、OTHER ID が変化すること。

- pytest は実走しない。ここで行ったのは source、署名、call graph、既存テストの静的照合のみである。

## identity 不変の論証

`CampaignConfig.bound_environment_contract` は [model.py:82-84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/campaign/model.py:82) で `compare=False` の runtime carrier である。さらに [ident.py:196-235](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/campaign/ident.py:196) の `canonical_preimage` は `spec_content`、commit、search tag/config、trial の五面だけを直列化し、bound contract を含めない。

移植する `_campaign_cfg_for_site` は、移植元 `p3_s4_loop_trigger_gating.py:463-472` のとおり `search_config` を変更するのは `site == PEGASUS_COMPUTE` の場合だけである。OTHER では `ident.bind_environment_contract(cfg, contract)` しか行わない。

[ident.py:100-118](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/campaign/ident.py:100) は未束縛なら runtime field だけを `replace` し、同じ契約が既にあれば同じ cfg を返す。したがって OTHER では `canonical_preimage` の byte 列、SHA-256、先頭 8 hex、campaign_id がすべて不変である。

`p3-s4-loop-s4-autonomous-0b53a387` は歴史的 campaign であり、現行 `default_cfg` の golden は既に `8ee68c0c` へ進んでいる (`test_p3_s4_loop.py:4185-4189`)。本移植で守るべき厳密条件は、同じ入力 cfg に対する OTHER の移植前後 preimage が同一であること、ならびに歴史的 `0b53a387` の output、overlay、pin を更新しないことである。この条件なら既存 campaign の ID や bytes は一切変わらない。

## P1〜P4 への回答

- **P1: 賛成。** `env_contract.py:253-260,291-300` では pegasus が 2100 / `()`、linux-baremetal が 1800 / numactl prefix であり、現行 `p3_s4_loop.py:1497` の `CLK` / `NUMA` は compute 契約と矛盾する。移植元も `p3_s4_loop_trigger_gating.py:811-815` で contract の exact 値を渡している。

- **P2: 賛成。** [loop.py:239-260](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2231-s4-loop-site-env/orchestrator/campaign/loop.py:239) の `run_campaign` は `env_contract` と `dependency_prefix` を受理する。`env_contract` は authorization と evaluate へ `loop.py:377-380,531-538`、非空 prefix は evaluate へ `:539-540` で転送される。したがって移植元 `p3_s4_loop_trigger_gating.py:802-819` の compute 分岐をそのまま使える。

- **P3: 賛成。** 三機構とも今回の四形からは外す。ただし resume 安全弁を外す帰結は具体的である。別 process が同じ pegasus campaign root を開くと、`drive_iteration` は `p3_s4_loop.py:1858-1865` で既存 identity/WALを recovery して `loop_state.json` を読み、`:1875,1885` で `iteration` を増やして checkpoint を上書きする。`state_to_dict` `:890-898` により `iteration`、`reverse_recommendations`、`whiteboard` の値が変わる。既存テスト `:5895-5927` が示すように incomplete WAL には recovery `abort` が追記され、`:6108-6147` のとおり checkpoint は iteration 1 から 2、whiteboard 1 件から 2 件へ進みうる。build outcome なら `s4_loop_digest.txt` も `:1892-1900` で更新される。これは移植後も残る未強制面である。一方 `_receipt_provenance` / `_append_provenance_entry` は trigger 固有台帳 `p3_s4_loop_trigger_gating.py:20-26,427-439,495-508` の新設を伴うため明確に scope 外である。

- **P4: 反対。** `default_cfg` の現行 ENV_TAG bindを残してはならない。`p3_s4_loop.py:1090` が linux-baremetal を先に bindした cfgへ compute の pegasus contract を `_campaign_cfg_for_site` が bindすると、`ident.py:113-117` の「異なる environment contract を再 bind できない」により `ValueError` になる。よって `default_cfg` は未束縛で返し、`:1417`、`:1809`、`:2036` と `main` の planner-context 早期経路で site 解決する。OTHER identity は runtime carrierが hash対象外なので不変である。

## 残存リスク

- PEGASUS_COMPUTE は実機から到達不能であり、compute 分岐、empty numactl、required attestation、dependency prefix は注入テストだけの確認となる。

- `allow_resume=False` はこの wave では base loop入口に強制されない。したがって pegasus campaign の cross-process checkpoint/WAL更新可能性が残る。

- base loop は `CampaignSummary.execution_receipt` を永続化しない。run_campaign 内の検証は行われるが、trigger provenance と同等の caller-side記録は残らない。

- `p3_b4_launcher.py:165-173` は現状 trigger だけを site projectionしている。base の B4 compute routeでは launcher contextの campaign_idと、site-aware mainが導く campaign_idが食い違う可能性がある。

- targeted test file外にも base公開APIの直接callerがあるため、全 suiteのhost依存回帰は未実測である。

- [T-2232] の job script、attestation exact照合、reservationとclaim rootの束縛は引き続き未実測かつ本wave外である。

## 総括

- 四つの移植形は、閉じたsite写像、契約admission、contract由来のrun_campaign引数、paired injectionで構成する。
- P1とP2は親案を支持し、P3もscope外を支持する。
- 最大の修正点はP4で、`default_cfg`のlinux契約先行bindを残すとcompute経路が必ず再bind errorになる。
- 親の段4ではP4の反転と、未強制の`allow_resume=False`およびB4 launcher不整合を受容するかを裁定すべきである。