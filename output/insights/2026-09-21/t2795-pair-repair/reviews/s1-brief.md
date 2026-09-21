# [T-2795] 段 1 brief — K2 同 job pair launcher と one-shot claim の整合修復 (2026-09-21、base main 5efd69367)

**研究前進:** story §8 B-6 / C35 (K2 手動 loop、critic-3 の最優先要望 R0 = 同 job stock 対照) は、pair launcher (D2183) が Pegasus 契約下の one-shot claim と矛盾して
不成立 (`13339.nqsv`、D2187)。本 wave は launcher を「1 process・1 回の認可/claim の所有期間で候補→stock」に直し、Pegasus 契約の実認可経路を通す結合検査で固定する。
完了判定 = 結合検査緑 + 旧 2 process 形が leaf に拒否され続ける負例緑 + 変異 KILLED + 受入緑 + land (T-2830 / T-2632 より先)。pair 再投入と 4 巡目 (各 1 job) は投入しない (ユーザー予算)。

**確定裁定:** D2187 (修復方向 = (ii')、claim leaf 不変、段 1 で D553 / D2183 への影響を明示、結合検査必須)、D2194 項 2 (4 巡目入力は択 A、投入は本 wave の外)、
D2183 (同 campaign・同 identity・同 WAL、stock 成功 = certified ∧ variant_id(genome) ∧ BUILD_START `src_token == STOCK`)、D464 / D553、D95 (実装面は Codex author)。
却下済み (再提案しない): 同 identity path の DEAD 再取得、claim の rename / 退避 / 削除、別 out_root、stock 未測定を判定に置換、reservation 不要契約への逃げ。

**provisional 裁定 (親、攻撃対象):**
- (P1) 設計 = `loop.py` に「認可 session」を足す。`run_campaign(..., authorization_session=S)` の初回呼出しは従来どおり `_authorize_measurement` で claim を取り、結果を S に保持。
  2 回目以降は S の束縛 (同 pid・S の発行元が loop・再計算した campaign identity / 契約 sha / declared_use_class / 解決済み output root の一致・claim file の record が
  S の record と一致 (所有の再確認)・reservation presence 再検査) を検査して claim 取得だけを省く。S 無しの `run_campaign` は bytes 以外の挙動・呼出し順とも不変。
  対案 (攻撃させる): `loop.py` を変えず 1 回の `run_campaign([候補, stock])` にまとめる — stock を coder 編集入りの木で build することになり D2183 の isolate 要件と結果処理が混ざるので provisional 却下。
- (P2) CLI = `--run-iteration P --stock-control` の同時指定を pair mode として受理 (1 process で候補→stock、同じ S を共有)。`--stock-control` 単独 (B-5 slot が使う) は不変。
  他の排他 (`--value` / `--emit-planner-context` / `--no-build` / `--b4-reflux-ablation` / `--b5-slot` 等) は維持。`--coder-role` / `--allow-coder-derived-build` は候補にだけ効き、
  stock は coder authority 無しの別 build_context と stock 専用 resolver (policy は一致を要求、不一致は拒否)。stock 用に別の pinned-clean worktree を切る。
- (P3) 候補の結果は stock を止めない (D2183 の job body と同じ: 候補 reject / abort / 例外でも stock を試み、rc は候補非零優先で集約)。例外の扱いは plan で具体化。
- (P4) job body: `IZANAGI_S4_STOCK_CONTROL=1` は driver 1 起動 (`--run-iteration P --stock-control`)。fixture (`--value`) + stock は発火する artifact / 計測 ID が無い (DW-G04) ので preflight で rc=2 拒否。既定 (未設定 / 0) の argv は bytes 不変。
- (P5) pair mode の stdout は候補・stock 各 outcome 行を出し、pair 成立は従来どおり WAL outcome で判定 (driver rc から判定しない)。

**既存被覆 (純増の確認):** 認可の使い回し機構は repo に 0 件 (`_AuthorizationResult` は loop.py 内部だけ)。一方、1 回の `run_campaign` に stock と候補の genome を並べる先例は
A-1 paired (`paper_story_a1_paired.py:7295` / `:7545`、balanced schedule) と sweep 系 (`backoff_sweep.py:484`) にある — (P1) の対案の根拠として plan / 相談に比較させる。
D2187 / insight §4 の (ii') 以外に同目的の裁定・failures の恒久対応は無い (F1019 再発追記は「恒久対応は未実施」)。

**D553 / D2183 への影響 (明示):** D553 — sink-local の claim 強制は `loop.py` に残り、single_process 下の全 `run_campaign` は「自分で claim を取る」か「同 process が同 sink で取った同 identity の
claim を所有していることを claim file で再確認する」かのどちらかで、claim 無しの経路は作らない。one-shot leaf は不変 (2 つ目の process は従来どおり拒否)。
D2183 — CLI 排他は `--run-iteration` × `--stock-control` の組だけを pair mode として解除、job body の 2 process 形を 1 process に置換。同 campaign・同 WAL・STOCK 成功条件は不変。

**不変条件:** `campaign_claim.py` bytes 不変 (sha256 2e9c0932…) / identity preimage 不変 (search_config に key を足さない) / stock は LoopState・whiteboard・checkpoint・planner に触れない /
verifier・correctness gate・admission の受理集合は不変 (規律 2) / S 無し経路の既存 test の呼出し順 assert は緑のまま / B-5 (`b5_generator_contrast` の `--stock-control` 単独) は不変。

**条件判定:** 08 = 成立・充足 (submodule 3 段を木の中身で実測)。09 = 不成立 (3 file の現 sha は当時の測定記録 (A-1 受領証・reservation.json・B-4 dogfood) にだけ出現。
実行時 closure (campaign.lock の loader blob 85 path・B-4 projection closure・A-1 source closure) は走ごとに記録され、新しい走は新 sha を束縛・旧記録は不変 (規律 7)。
closure ratification は廃止済み (conftest の互換 fixture)。T-2797 / T-2795 が同 file を編集して land 済み)。10 = 非該当。
13 = 成立 (S の再利用は `run_campaign` の受理形を増やす)。入力 = claim record の field (campaign_identity / protocol_digest / job_id / host / boot_id / pid / proc_starttime / created_utc) は
実 claim (`13339.nqsv`、insight §1) に全 field 実在、pid は pair mode で構造上同値。時間予算の述語は無い。

**成果物:** loop.py (S)、p3_s4_loop.py (pair mode)、p3_s4_loop_pegasus.sh (1 起動)、test (結合検査 = site PEGASUS_COMPUTE・pegasus 契約・実 `run_campaign` / `_authorize_measurement` /
`acquire_claim` / reservation 検査、stub は build/verify/bench と attestation と condition gate のみ + 負例: 旧 2 起動形の ClaimError、S の束縛不一致 (identity / pid / claim record) の拒否、
pair × B-5 の拒否、job contract の 1 起動)、変異事前登録、insight、decisions / worklog fragment、F1019 恒久対応の追記。
**模擬と実の差:** 結合検査は attestation と build/verify/bench を stub する。Pegasus 上の production 1 走は修復後の pair 再投入 (ユーザー予算) が担う — insight と F1019 に明記する。

**分割:** Codex author 2 単位を直列 — A1 (loop.py の S + test_campaign.py の単体)、A2 (p3_s4_loop.py pair mode + job body + test_p3_s4_loop.py 結合検査 + job contract test)。
受入 = `tools/dev_wave_wait.py acceptance --lease-optional` (Pegasus 計算ノード、所在は worklog / runbook の既定)、焦点走は計算ノード dispatch。生の計測 job は投入しない。

## 実アンカー表 (base 5efd69367)

| 面 | アンカー |
|---|---|
| 認可 sink | `orchestrator/campaign/loop.py:165-243` `_authorize_measurement` (claim 取得 :205-236)、`:347` `run_campaign` 署名、`:516-533` 認可呼出し |
| stock 口 | `orchestrator/campaign/p3_s4_loop.py:2005-2016` `_stock_capability_resolver`、`:2019-2114` `_run_stock_control_resolved` (`run_campaign` :2083) |
| 候補口 | `p3_s4_loop.py:2117-2310` `_run_one_iteration_resolved` (`run_campaign` :2280)、`:2717` `drive_iteration` |
| CLI | `p3_s4_loop.py:3072` `main`、B-5 排他 :3176-3184、stock 排他 :3199-3210、build_context :3369-3375、worktree :3395-3401、stock 分岐 :3411-3424、run-iteration 分岐 :3427-3510 |
| job body | `tools/pegasus/p3_s4_loop_pegasus.sh:147-160` (STOCK_CONTROL・stock_identity_argv)、`:669-694` (候補起動・stock 起動・集約) |
| 既存 test | `orchestrator/tests/test_campaign.py:9100-9230` (pegasus 契約・reservation・claim root の fixture と単一 claim assert)、`test_p3_s4_loop.py:540` (site OTHER・single_process=False)、`test_p3_s4_loop_job_contract.py` |
| no-touch | `orchestrator/campaign/campaign_claim.py`、submit-tree-pair (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2795-k2-pair/`) |
| B-5 consumer | `orchestrator/campaign/b5_generator_contrast.py` (`--stock-control` 単独 subprocess)、`tools/pegasus/b5_contrast_launch.py` |
