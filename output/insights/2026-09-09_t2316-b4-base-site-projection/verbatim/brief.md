# 段 1 brief — [T-2316] base の B4 launcher へ site 射影を入れる

## 研究前進

進むのは B-4 (reflux ablation) の base 軸を Pegasus 計算ノードで実際に走らせること。
現状 `PEGASUS_COMPUTE` では base の正式 B4 経路が最初の授権境界で止まり、build に到達しない
= base 軸の certified 選択結果・proof chain が 1 件も生産できない。最小差分は
`p3_b4_launcher._driver_configs` の site 射影を trigger と同じ形で base にも掛けること。
完了判定は「PEGASUS_COMPUTE を解決 site とした base の launcher が、driver 側と同じ campaign ID を
出す」ことを test で pin できること。

## 機序 (実測で確定、推測ではない)

- `p3_b4_launcher.py:147-176 _driver_configs` は `driver_kind == "trigger"` のときだけ
  `_current_site()` → `_admit_env_contract()` → `_campaign_cfg_for_site()` を掛ける。
- base の driver 側 `p3_s4_loop.py:2588-2598 main` は、`default_cfg` の直後に必ず
  `cfg = _campaign_cfg_for_site(cfg, resolved_site, _contract=contract)` を掛ける。
- ゆえに PEGASUS_COMPUTE では launcher の `context.campaign_id`
  (`p3_b4_launcher.py:548 prepare_launch` の `ident.campaign_id(selected_cfg)`、未射影) と、
  driver が `require_b4_production_context` へ渡す `expected_campaign_id` (射影済み) が食い違う。
  base の授権境界は 3 箇所 — `p3_s4_loop.py:1742` / `1896` / `2346`。最初に当たるのは 2346
  (`boundary="base drive_iteration"`)。ここで `B4LauncherAuthorizationError` になり build へ届かない。
- `_campaign_cfg_for_site` が id を変えるのは `PEGASUS_COMPUTE` のときだけ
  (`search_config["measurement_env"] = "pegasus"`、D125 / D261)。OTHER では key を足さないので
  現に動いている OTHER 経路の回帰ではない。
- 同 launcher が `exploration_campaign_layout(campaign_id(selected_cfg))` へ sidecar を書くため
  (`p3_b4_launcher.py:568-569`)、sidecar も driver が見る campaign dir と別の場所に落ちる。

## scope

- **入れる**: `_driver_configs` が `driver_kind == "base"` のときも `p3_s4_loop` の
  `_current_site` / `_admit_env_contract` / `_campaign_cfg_for_site` で射影する。
- **入れる**: その射影を pin する test。現行 `orchestrator/tests/test_p3_b4_launcher.py` には
  `site` / `PEGASUS` / `measurement_env` の出現が **0 件** で、trigger 分岐すら未 pin。純増はここ。
- **入れない (scope 外)**: `sort` の site 対応 = [T-2318]。`p3_s4_loop_sort.py` には helper 3 点が
  そもそも無い (`_current_site` 等の hit 0)。driver 種の一般 dispatch 表へ畳むと sort を巻き込むので取らない。
- **入れない (scope 外)**: [T-2317] の `_assert_layout_matches_campaign` / `_with_campaign_location` 移植。
- **入れない (scope 外)**: 仮想リスク向けの gate・検査・台帳・一般化 (依頼の明示指示)。

## 確定済みユーザー裁定・前提の実測

- 依頼が挙げた前提 [T-2232] の Pegasus job script 着地: `6bf28173c` が local main HEAD の祖先
  (`merge-base --is-ancestor` = yes)。到達不能条件は解けている。実測済み、覆す新事実なし。
- 実装は Codex author (D95)。親はコード・テストを直接編集しない。
- 段 4 loop の実行場所は Pegasus (D1517)。

## DW-G 群

- **G01 生死実験先行**: 該当なし。新軸・大型機構ではなく既存 driver への対称 3 行。
- **G02 blocker 限定**: 該当する。「試行欠落」を実際に変える欠陥なので 1 cycle 後送りにしない。
- **G03 族一般化**: しない。base 1 例のみ。sort は独立 task。
- **G04 発火 gate**: 発火条件は実在する。計測 ID `981655.nqsv` (bnode116、2026-09-07)、
  一次資料 `output/insights/2026-09-07_t2232-s4-loop-first-dispatch`。base 段 4 loop の
  job body が PEGASUS_COMPUTE で現に投入された実績。
- **G05 成果物影響**: 放置すると PEGASUS_COMPUTE 上で B-4 base 軸の試行が 0 件のままで、
  certified 選択結果と proof chain に base 軸の行が生じない。

## 不変条件 (緩めない)

- 規律 2: 授権境界 `require_b4_production_context` の拒否力を弱めない。campaign ID の一致要求は
  そのまま。射影を足すことで「一致するようになる」のであって、比較を緩めるのではない。
- 未知 site は fail-closed のまま (`_site_admits_measurement` の exact set)。
- OTHER の campaign_id を変えない。
- `sort` の現行挙動を 1 bit も変えない。
- `p3_b4_launcher.py` は `campaign_lock.py:93` の enforcement source かつ
  `p3_b4_closed_critic.py:649` の proof chain 記録対象。**未 commit のままだと
  contract-loader-drift で焦点走が全赤になる。段 6 の焦点走・変異の前に必ず commit する。**

## (P1) 親の provisional 裁定 = 攻撃対象

- **(P1-a)** 修正は `_driver_configs` 内の分岐追加だけで足り、`prepare_launch` /
  `launch_bootstrap_impl` / `launch_continuation_impl` の呼び出し側は変えなくてよい。
- **(P1-b)** base の射影は trigger と同じ 3 手 (`_current_site` → `_admit_env_contract` →
  `_campaign_cfg_for_site`) をそのまま `p3_s4_loop` の同名 helper で行えばよく、
  `bind_admission_policy` は launcher 側では不要 (trigger が現にそうしている)。
- **(P1-c)** `_campaign_cfg_for_site` は冪等で、driver 側の二重射影は id を変えない。

## 成果物の形

- `orchestrator/campaign/p3_b4_launcher.py` の `_driver_configs` の差分。
- `orchestrator/tests/test_p3_b4_launcher.py` へ PEGASUS_COMPUTE 下の base 射影を pin する test。
  受理側 (base の launcher id == driver id) と拒否側 (射影を外すと授権境界が拒否する) を対で置く。
- 受入所要台帳 `orchestrator/tests/acceptance_duration_ledger.json` へ新 nodeid の追記
  (main 取り込み後に 1 回)。

## 並列分割方針・受入環境

- 段 2 plan 1 本 (read-only)、段 3 敵対相談 2 本 (異なるレンズ)、段 5 実装 1 本 (author)、
  段 6 敵対レビュー 2 本 + fix。授権境界 = 正しさ防壁に触り受理集合が変わるので、
  DW-C00 に従い敵対検証子を省かない (軽量版にしない)。
- 実装面は単一ファイル 1 関数 + test 1 ファイルなので、段 5 は 1 子で所有を分けない。
- 受入・実測はログインノード上の repo 内 test。Pegasus 実機投入は本 wave の scope 外
  (新規 Pegasus 実行体を要する実測は同じ wave で走らせない)。site は
  `site_policy.current_site` を test 側で PEGASUS_COMPUTE へ解決させて検査する。
