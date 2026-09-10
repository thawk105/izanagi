# [T-422] 段 1 brief — campaign 実行先の worktree 外部化 (F98 択 (iii))

## scope

exploration campaign の実行先を、wave worktree の外 (job 専用の /work 配下) へ向けられるように
する。防壁 (hooks/guard_bash.py / tools/dev_wave_land.py / orchestrator/campaign/durable_root.py)
のコードは一切変更しない。

## 確定済みユーザー裁定 (2026-08-04)

「campaign の実行先を使い捨て worktree の外へ出す (防壁は 1 つも緩めない)」。
実装方向まで裁定済みであり、F98 の択 (i) (land 緩和) / 択 (ii) (guard carve-out) へ戻さない。

## 背景 (F98)

wave worktree 内で campaign を 1 回起動すると `output/exploration/namespace.json` と
`output/exploration/campaigns/<id>/campaign.lock` が生成される。
`tools/dev_wave_land.py` の `_verify_wave_clean` (785-787 行) は wave worktree の status record
1 件 (untracked 含む) で land を拒否する。`hooks/guard_bash.py` は repo 内の campaign tree /
namespace marker の削除を拒否する。消せないものが在ることを land が許さず、campaign を実走した
wave は正規経路で段 9 を完了できない。

## 前提実測 (2026-08-04、wave worktree)

1. `exploration_campaign_layout(cid)` は output_root 省略時 `repo_output_root()` = repo 直下
   `output/` (orchestrator/campaign/layout.py:323-330)
2. `_verify_wave_clean` は untracked 含む完全 clean 要求 (tools/dev_wave_land.py:785-787)
3. guard_bash の防護は repo 相対判定 — 外部 /work 配下の同形 path
   (`/work/.../output/exploration/campaigns/foo` 等) の rm は現行コードで ALLOW (実測 5 case)。
   repo 内は DENY のまま。外部化は guard に触れずに成立する
4. durable-root admission (`authorize_output_root`) の利用者は
   orchestrator/campaign/s8b_floor_campaign.py:2845 のみ (official floor 経路)。exploration
   書き込み経路は admission 非接触
5. 注入 seam の棚卸し:
   - `orchestrator/campaign/s8b_oracle_exploration.py:75-76` — `--output-root` CLI あり
   - `orchestrator/campaign/loop.py:99,126` — `run_campaign(..., output_root="")` 引数あり
   - `orchestrator/campaign/p3_kickoff.py:114`、`p3_s4_loop.py:678,679,803,896,926`、
     `p3_s4_loop_sort.py:231,232,320,437,476`、`p3_s4_loop_trigger_gating.py:555,556,630,767,807`、
     `p3_s4_red.py:167` — `exploration_campaign_layout(cid)` を output_root なしで呼ぶ (seam なし)
   - `orchestrator/campaign/p3_autonomous_workload_trial.py:1043,1222,1268` — 一部は既存
     campaign path からの逆導出
   - 使い捨て smoke driver (output/insights/2026-08-04_wave-a-campaign-transport-smoke/driver/) は
     trial/trigger 経由で既定 root
   - 既存 env 慣行: `IZANAGI_BENCH_LOCK` (orchestrator/campaign/lock.py:29)、`IZANAGI_TRACE_DIR`、
     `IZANAGI_RESERVATION_*`

## 不変条件

- guard_bash / dev_wave_land / durable_root / hooks の挙動・コード不変 (裁定)
- env/seam 未設定時の既定挙動は現行どおり repo output root (後方互換)。既存凍結成果物の
  bytes・pin は変わらない
- 機械固有 path (実際の /work job dir) は shared code / 横断 docs に書かない — 注入側
  (job script / runbook) だけが持つ
- campaign_id の path traversal 防御 (`_campaign_slug`) と exploration namespace marker の
  exact-bytes / symlink 拒否契約は維持する

## 成果物の形

- layout.py の exploration 経路への外部 root 注入 seam (コード + テスト)
- F98 再発検知検査: 外部 root を指定して campaign layout を ensure した使い捨て worktree が
  `_verify_wave_clean` を通ることを直接撃つテスト。既定 root では拒否される対照も固定。
  既存被覆 (orchestrator/tests/test_dev_wave_land.py) は main 側 untracked 衝突のみで、この性質は純増
- 運用手順の最小 docs (機械固有 path は書かない)

## provisional 裁定 (親の暫定判断であり攻撃対象)

- (P1) seam は layout.py の環境変数 1 本 (`IZANAGI_` 慣行、名称は plan で確定) を既定とし、
  output_root 引数明示が env に優先する。per-driver CLI flag の全追加は取らない
- (P2) 外部 root の置き場規約は docs に「job 専用 /work 配下」とだけ書き、実 path は
  job script / runbook 側が持つ
- (P3) F98 再発検知は pytest の temp fixture worktree で行う (実 wave worktree を汚さない)

## 成果物影響 (DW-G05)

実装しない場合、計算ノードで campaign を実走する全 wave が段 9 で land 不能のまま (F98)。
T-410 / T-420 系の再開条件が塞がれ続ける。certified 選択・レポート・台帳の既存値は変わらない
(exploration runtime 出力の置き場のみの変更、proof chain 非接触)。

## 分割方針

実装は Codex author 1 本 (layout seam + テストは所有一体)。段 2 プラン起草 + 段 3 敵対相談
(interface 変更 + gate 新設のため省略しない)、段 6 敵対レビュー 2 本 + 変異 matrix + 受入。
