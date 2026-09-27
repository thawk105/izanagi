# [T-2104] campaign advisory flock の保持区間を認可から checkpoint 完了まで広げる (D1346)

authority: none / default_effect: no-state-change (可変状態の正本は worklog 末尾と現行 phase doc)

## 1. 何をしたか

- **欠陥 (一次資料 output/insights/2026-08-29/t2049-b4-raw-record-producer/verbatim/s6-ruling-addendum.md §B の B-1 と「裁定パッケージへの追加」項 4):**
  campaign の実行所有 flock は `loop.run_campaign()` の内側でしか取られず、base driver (`p3_s4_loop.drive_iteration`) の
  B-4 認可・preflight (検疫)・checkpoint (`save_loop_state`) と、`main()` の B-4 事前認可から driver 呼出しまでは lock の外だった。
  B-4 の raw record producer は終端 record が無いとき同じ lock を非ブロッキングで試し、取れれば `terminal-record-absent` として
  不可逆な欠測に封印するので、実行中の arm を終了済みと誤判定しえた (block score・欠測数・verdict が変わる)。
- **実装 (D1346、コード 3 file + test 2 file、Codex author):**
  - `orchestrator/campaign/lock.py`: `campaign_lock` が保持 handle (`HeldCampaignLock`: path・pid・保持中フラグ) を yield し、退出時に保持中を偽にしてから unlock する。
    通常の取得・同一 process 再入の拒否 (CampaignBusy) は不変。
  - `orchestrator/campaign/loop.py` `run_campaign`: keyword-only の任意引数 `held_campaign_lock`。未指定なら従来どおり自分で取る。
    指定時は exact 型・保持中・PID・path 一致を WAL より前で確かめて取得を省き、不一致は TypeError / ValueError。
  - `orchestrator/campaign/p3_s4_loop.py`: `drive_iteration` は layout 解決直後 (`_load_provenance` より前) から、入口停止を含む
    checkpoint 完了まで非ブロッキングで保持し、critic digest は区間外。`main()` の `--run-iteration --b4-reflux-ablation` は
    事前認可の state 読込より前から候補 driver の復帰まで保持し、handle を driver → run_campaign へ渡す。stock control へは持ち越さない。
  - 変えないもの: 公開 `run_one_iteration`、main の fixture 直呼び、stock control の run_campaign、sort / trigger / policy driver、producer。
- **対象 driver を base に限った根拠:** docs/phase3-b4-reflux-ablation-preregistration.md §5「対象 driver と軸」= `base (silo-backoff-magnitude)`。

## 2. 実測

| 走行 | 対象 | 結果 |
|---|---|---|
| 焦点走 f1 (実装 30cd2978c) | 変更 3 module を参照する test 39 file | 2 failed / 5080 passed / 20 skipped (174 秒)。赤 2 件とも本 wave 帰属 (preflight probe の到達回数 1 固定 [実測 6]、`test_reflux_campaign_issuer` の signature 末尾 pin) |
| fix-1 (54f37387f) | loop.py の引数位置、probe の回数条件 | 各 1 行 |
| 再走 f2 (54f37387f) | test_p3_s4_loop / test_campaign / test_reflux_campaign_issuer | 1146 passed / 3 skipped / 赤 0 (37 秒) |
| 旧 driver 確認 (p3_s4_loop.py だけ ad114fba0 版を commit した使い捨て木) | 新しい負例 7 件 | **7 failed、理由は全件「DID NOT RAISE CampaignBusy」** = producer が実行中の arm の lock を取れてしまう誤判定の再現 (7.70 秒) |
| 変異 harness 本走 (独立 clone・dispatch) | 10 変異 (対照 M0a/M0b + M1〜M8) | 10/10 KILLED、登録した完全集合と全件一致。mutation-ledger.json |
| commit 済み変異の個別走 (drift 無し) | M1 / M2 / M3 / M5 | M1→driver 負例 5、M2→checkpoint[False] のみ、M3→checkpoint[True] のみ、M5→受け渡し正例と拒否 test |

- 新しい負例 7 件: `test_p3_s4_loop.py::test_base_flock_covers_real_b4_authorization`・`test_base_flock_covers_real_backoff_preflight`・
  `test_base_flock_covers_real_checkpoint[False]`/`[True]`・`test_base_flock_conflict_precedes_b4_consumption`・
  `test_main_b4_flock_covers_real_pre_authorization`・`test_main_b4_flock_covers_real_checkpoint`。各 probe は producer の実
  `_execution_lock_for_root` が driver の lock path と一致することを assert してから CampaignBusy を要求する。
- 受け渡し契約: `test_campaign.py::test_run_campaign_accepts_matching_held_lock_without_reentry`・`test_run_campaign_rejects_invalid_held_lock_before_wal`。
- 既存の並行実行契約 test (同一 process 再入拒否・別 process 競合・別 campaign 並行・B-4 消費の単一 writer・producer の busy→deferred) は期待値を変えずに緑 (f1/f2)。
- **drift 層:** 変更 3 file はいずれも campaign.lock の contract-loader 閉包の member で、未 commit の書換えはコメントだけでも
  同じ 148 node を赤にする (M0a = M0b)。新しい負例のうち 5 件 (preflight・checkpoint 2・main 経由 checkpoint・受け渡し正例) はこの核に入るため、
  harness では M2・M3 の固有の赤が 0 になる。これを commit 済み変異の個別走で補った (先例 T-2849)。

## 3. DW-O13 実測 (照合する path が本番で一致するか)

- driver の cfg は `_campaign_cfg_for_site` で環境契約を bind 済みで、run_campaign の再 bind は同一契約なら冪等。lock dir は
  `resolve_campaign_output_root("exploration", "")` と、producer が campaign root の字面から逆算する明示 base とで同じ値になる。
- 実 campaign 53 件で driver の loop_state.json と run_campaign 側の runs/wal.jsonl が 53/53 同居 (verbatim/dw-o13-colocation-probe.log)。
  これは同居の実例であって lock path 値の一致の証明ではない (段 3 の指摘)。path 値の一致は負例 test が producer の関数で直接 assert する。

## 4. scope 外の real 所見 (起票しない、DW-S04)

- **sort / trigger driver の同型の窓:** `p3_s4_loop_sort.py` / `p3_s4_loop_trigger_gating.py` の drive_iteration も B-4 認可 → 実行 → checkpoint が
  run_campaign の lock の外にある。今回の B-4 対象 (base) の記録には効かない。B-4 の対象 driver を変えるときに同じ変更が要る。
- **producer の非保証文「flock は campaign 実行の内側区間しか覆わず…」**(`p3_b4_raw_record_producer.py` の `B4_RAW_RECORD_NON_GUARANTEES`):
  旧コードで走った campaign には依然成り立つので今回は変えない。新規 base campaign の説明としては古くなる。
- **path 不一致の拒否が B-4 認可の消費より後になる (段 3 sol の所見):** 本番の main は layout を注入しないので起きない。
  test の注入 layout でだけ起き、そこでは run_campaign の照合が WAL 前に fail-closed。消費前の追加照合は仮想リスク向け gate として採らなかった。
- 段 6 レビュー B の nit 2 件 (重複 assert) は成果物影響が無いので直さない (DW-G05)。

## 5. 手順上の事故 (段 8 で routing)

- 段 1 brief の provisional 裁定に「照合して不一致は fail-closed」を書いた時点で条件 13 (gate・検証の新設) が成立していたのに、
  DW-O13 を段 2 前に読まなかった。段 4 直前に気づき、段 2・3 (codex 3 本) を無効化して再実行した (superseded 成果物は job dir)。
- 実装子 worktree の `git worktree add` が共有 filesystem の EINTR で 1 回 rc=128 (自作の空 branch を削除・prune して再作成)。
- submodule 初期化 tool が 1 回目 `runtime-io-failure` rc=1、同じ引数の 2 回目で rc=0。

## 6. 所在

- job dir (repo 外): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2104-flock-scope (prompt・log・変異 spec・結果 JSON 11 MB)
- verbatim/: 段 1 brief・段 3 相談 2 本 (v2)・段 4 裁定 (段 6 の追補つき)・段 6 レビュー 2 本・焦点再レビュー・DW-O13 probe log
- **逐語の可逆最小正規化 (DW-S07):** `git diff --check` 抵触のため、verbatim/s6-review-A.md と s6-review-B.md の行末空白 (Markdown の改行用 2 空白) だけを除いた。
  可視文字は不変。原文: s6-review-A.md sha256=ee29b817bb130d3dccf0d4c23b47212fcbd128065cae4bdfcfcb0857e70d6a60・1259 bytes・該当 3 行、
  s6-review-B.md sha256=f1ab7e102d8eb81caf113a4d8ec0fd28455df66ea3aa0f66c96e5d955daf0847・1678 bytes・該当 6 行。
  復元法: 原文は job dir の out/s6-review-A-1.md・out/s6-review-B-1.md (同一 bytes)。s6-review-A.md の 3・4・5 行目、s6-review-B.md の 3・4・5・8・9・10 行目の末尾へ半角空白 2 個を戻す。
