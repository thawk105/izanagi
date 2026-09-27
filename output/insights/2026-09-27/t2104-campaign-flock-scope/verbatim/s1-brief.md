# 段 1 brief — [T-2104] campaign advisory flock の範囲拡大 (D1346)

worktree (子はここを読む): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2104-flock-scope (base = local main ad114fba0)

- **研究前進:** B-4 (reflux ablation) の raw record producer が、実行中の arm を「終了済み・終端 record なし」と誤判定して不可逆な欠測 (`terminal-record-absent`, lock acquired=true) に封印する経路を塞ぐ。放置すると B-4 の block score・欠測数・verdict が変わる (D1346 理由)。完了判定 = 誤判定の再現 test (修正前に赤・後に緑) と既存の並行実行契約 test の緑を同じ単位で置く。
- **確定済みユーザー裁定:** D1346 — 公式 loop の advisory flock の範囲を authorization・preflight・実行・checkpoint 完了までへ広げる。却下: 内側区間のまま / producer 側の推測で補う。一次資料 = output/insights/2026-08-29/t2049-b4-raw-record-producer/verbatim/s6-ruling-addendum.md「裁定パッケージへの追加」項 4 と §B (B-1 欠陥)。
- **scope:** driver 側の lock 保持区間の拡大と、それに必要な最小の受け渡し口だけ。producer (p3_b4_raw_record_producer.py) は変えない。仮想リスク向けの gate・検査・台帳・一般化は足さない。
- **非接触 (並走 T-2865 所有):** orchestrator/campaign/p3_s4_loop_policy.py、tools/pegasus/ 配下すべて。
- **不変条件:** 規律 2 (正しさゲートを緩めない)。既存契約 test の期待値を変えない — 特に test_campaign.py::test_campaign_lock_reentry_rejected_in_same_process (同一 process の再入は CampaignBusy)、test_campaign_lock_same_campaign_rejects_competing_process、test_campaign_lock_different_campaigns_can_run_in_parallel、test_p3_s4_loop.py::test_b4_consumption_publish_allows_only_one_concurrent_writer、producer の flock 競合 test 群 (test_p3_b4_raw_record_producer.py)。run_campaign を単独で呼ぶ既存 caller の挙動 (自分で lock を取る) は不変。
- **凍結・pin (DW-O09 実測):** loop.py / lock.py / p3_s4_loop.py は campaign.lock の contract-loader 閉包 (96 path、live 計算) の member。B-4 projection closure (live 計算、p3_b4_closed_critic.py `projection_closure_manifest`) に入るのは p3_s4_loop.py だけ。B-4 事前登録の projection hash 欄は未記入 (値未登録) なので凍結値は壊れない。3 file の現 sha256・blob を git grep した hit は output/insights/2026-08-27_t1769-b4-wiring-probe/ の歴史記録 (lock.py) だけで、live 照合 test は見つからない (規律 7 により歴史記録は更新しない)。producer の出力 bytes は変えないので DW-O10 は不成立。

## 実アンカー表

| 箇所 | 現状 |
|---|---|
| orchestrator/campaign/lock.py:71-89 `campaign_lock(path, blocking=False)` | fd を開き flock LOCK_EX(|NB)、busy は CampaignBusy。handle を yield しない |
| orchestrator/campaign/loop.py:522 `run_campaign(...)`、:725-730 | authorization・perf preflight・layout 生成の後、ExitStack で `campaign_lock(campaign_lock_path(layout, declared_use_class, output_root))` を取る (内側区間) |
| orchestrator/campaign/layout.py:62-69 `campaign_lock_path` | key = sha256(realpath(layout.root))[:20]、`<resolve_campaign_output_root(use_class, output_root)>/campaign-locks/<key>.flock` (exploration で output_root 空なら環境変数の正規化値、無ければ repo の output/。段 4 で訂正) |
| orchestrator/campaign/p3_s4_loop.py:3077 `drive_iteration` | :3137 layout 解決 → :3157 load_loop_state → :3161 require_b4_iteration_authorization → :3181 consume → :3194 ident.ensure_resumable_attempts → check_stop (早期 save_loop_state :3205) → :3216 `_run_one_iteration_resolved` (preflight/quarantine → :2639 run_campaign) → :3233 _append_provenance_entry → :3239 save_loop_state (checkpoint) → critic digest |
| orchestrator/campaign/p3_s4_loop.py main() 周辺 :3786-3871、:4001-4003 | main 側にも B-4 の preflight authorization (`preflight_authorization = require_b4_iteration_authorization(`) と、drive_iteration を経ない `_run_one_iteration_resolved` 呼び出しがある。区間の扱いは plan で棚卸しする |
| orchestrator/campaign/p3_s4_loop_sort.py:524 / p3_s4_loop_trigger_gating.py:1005 `drive_iteration` | 同じ B-4 authorization → 実行 → L.save_loop_state の形 |
| orchestrator/campaign/p3_b4_raw_record_producer.py:1329 `_execution_lock_for_root`、:1609-1621 | 終端 record 不在時に `campaign_lock(execution_lock, blocking=False)` を試し、取れたら lock_acquired=True で terminal-record-absent |

## DW-O13 実測 — 照合する path が本番で一致するか (親、2026-09-27 15:2x JST)

- 照合の入力は「driver が `campaign_lock_path(layout, "exploration", "")` で得る path」と「run_campaign が `layout_constructor(authorization.campaign_identity, output_root)` から得る path」。
  producer は WAL・campaign.lock を持つ root (= run_campaign 側の layout) から `_execution_lock_for_root` で同じ式を再計算する。
- コード: base drive_iteration の cfg は `_campaign_cfg_for_site` (p3_s4_loop.py:170-184) で環境契約を bind 済み。run_campaign の `ident.bind_environment_contract` (loop.py:370、ident.py:100-118) は同一契約なら同じ cfg を返し、異なれば ValueError。よって campaign id は一致する。
- 実環境の値: 過去の実 exploration campaign 53 件 (T-1112・T-2795・T-2797 B-5・T-2860 の output root) を読み取り専用で走査し、driver が書く loop_state.json と run_campaign 側の runs/wal.jsonl が 53/53 で同じ root に同居 (probe_colocation.py / .log)。
- 結論: 一致は本番で到達可能。注入 layout を渡す test 経路で食い違う場合は照合で fail-closed になる。

## 親の provisional 裁定 (攻撃対象)

- (P1) 受け渡し: lock を再入可能にする案は既存契約 test (同一 process 再入の拒否) を壊すので採らない。driver が外側で取った lock を run_campaign へ明示的に渡し、run_campaign は渡された保持が自分の計算する lock path と一致し生きていることを確かめたうえで自分では取らない。不一致は fail-closed。照合項目は最小にする (path 一致と保持中であること。追加の照合を足すなら必要性を示す)。
- (P2) 対象 driver: **base (p3_s4_loop.py) だけ。** 親の実測: docs/phase3-b4-reflux-ablation-preregistration.md §5「対象 driver と軸」欄は `base (silo-backoff-magnitude)` と記入済み。依頼も p3_s4_loop.py を名指す。sort・trigger は同じ窓を持つが今回の B-4 の記録に効かないので触らず、insight に「対象 driver を変えるときの候補」として記録する。policy は非接触。
- (P3) 区間: base drive_iteration は layout 解決直後、_load_provenance・load_loop_state・authorization より前に非ブロッキングで取得し、checkpoint (save_loop_state、早期停止経路の save を含む) の完了まで保持。critic digest 生成は区間外。B-4 以外の mode でも同じ区間を保持する。**base main() の `--run-iteration` 経路は driver より前に B-4 認可を事前確認し (:3865-3880)、proposal 読込と `--isolate-worktree` の patchharness.checkout を経て drive_iteration に入るので、main が事前確認の前から drive_iteration の戻りまで保持し、driver へ保持を渡す。** checkpoint を持たない経路 (公開 run_one_iteration の単独呼出し、main の fixture 直呼び :4001-4008、stock control の run_campaign :2387) は従来どおり (run_campaign が自分で取る)。
- (P4) 取得は非ブロッキング。競合時は authorization を消費する前に CampaignBusy で止まる。
- (P5) producer の非保証文「flock は campaign 実行の内側区間しか覆わず…」は変えない (旧コードで走った campaign には依然成り立つ・producer 出力 bytes を変えない)。

## 成果物の形と分割

- 実装: lock.py / loop.py / p3_s4_loop.py と test。1 単位 (所有が素集合に割れない一枚岩) の Codex author 1 本。
- 負例 test: base の外側区間 (authorization 中・preflight 中・checkpoint 中) と main の事前認可中に producer と同じ lock path を非ブロッキングで取りに行き、修正前は取れてしまう (= 誤判定の再現)、修正後は CampaignBusy になることを実体 (producer の `_execution_lock_for_root` と実 `campaign_lock`) で示す。
- 受入・実測環境: 焦点走と受入全走は Pegasus 計算ノード (`tools/run_tests.py` dispatch、`tools/dev_wave_wait.py acceptance`)。所在は worklog、機体固有は docs/pegasus-runbook.md。
