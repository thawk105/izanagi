---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-17
wave: dev-wave-t2632-b4-prerun-issue-caller
seq: 1
title: [T-2632] B-4 prerun publication 発行器の production 呼び手を足し、現物 3 campaign で 1 回だけ実発行を試みた — 候補 0・発行器は design_not_feasible で typed 拒否・封印 receipt は未取得、足りない入力 12 field を確定した (コード + docs、branch worktree-dev-wave-t2632-b4-prerun-issue-caller、変異 matrix = baseline PASSED・負例 10/10 KILLED・等価対照 1 SURVIVED・MISMATCH 0・期待 node 完全一致)
---

## 本文

- ユーザー依頼は「T-2632 の 3 条件のうち独立に閉じられる (1) を進める — 事前登録 §6 が名指す `output/b4-prerun-publication` へ
  bootstrap 集合を封印発行する経路。発行器の production 呼び手が tests 以外に 0 件なので、現物から
  `B4ScheduledAttemptInput` の行と planned_result_artifacts を組む最小の呼び手を Codex author で足す。組めるなら 1 回だけ
  実発行、組めなければ何が足りないかを実測で書いて返す (実発行を完了条件にしない)」。
- 一次資料は `output/insights/2026-09-17/t2632-b4-prerun-issue-caller/README.md` (段 1 brief、段 4 / 段 6 裁定、
  plan、敵対相談 2 本、レビュー 3 本、実発行試行の生 JSON を同 dir に凍結)。job dir は
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-prerun-issue-caller/`。
- **brief 前の実測で依頼の前提が覆った。** 前 wave README「(1) は (2) と独立に閉じられる」は、封印 receipt の取得については
  成立しない — 発行器は適格行 < 201 で `design_not_feasible` を返す。独立に閉じられるのは production 経路の実在だけ。
  さらに `initial_proposal_sha256` は現行の保存形式 (whiteboard 5 field = D39 決定 3、WAL は genome / src_token) から
  導けず (D1846 が確認)、非空 batch は現物から構成できない。段 4 で再裁定し、成果の認定範囲を「現物からの不足報告 +
  空 batch での発行器到達」に限定した。
- 設計判断は {{D:b4-prerun-caller-scope}} (呼び手の責務、bootstrap 所属を batch 所属で真にしない、前 wave の順序訂正)。
- **親の brief は段 3 の 2 レンズに 2 点訂正された。** (a) P1「発行 batch に含めた行は `bootstrap_member` 真」は述語の恒真化で
  不採用 (D1881 の理由と同型)。(b) N5「成功 precursor は registry 行にならない」は誤り — 台帳型は SUCCESS を受理し
  manifest の適格性で除く。`rejected` だけを候補にする根拠は D1936 項 8 の供給源限定であって台帳の受理集合ではない。
  段 3 B は「条件 9 の充足数を増やしたと書かない」「自然赤 + §5 の 2 欄は receipt の十分条件でない」も指摘し採用。
- **実装 (commit `2d71a0454`、Codex author) は `orchestrator/campaign/p3_b4_prerun_caller.py` (172 行) と
  `orchestrator/tests/test_p3_b4_prerun_caller.py` (15 node)。** 段 6 の敵対レビュー 2 本で must-fix 4 件
  (欠落記録の `artifact_path` が未参照の checkpoint を指す → null、`json.loads` の `RecursionError` が typed stop から漏れる、
  未使用 3 field の必須検査を削る、M3 / M4 / M9 は fail-closed kill でなく診断感度 pin として別枠記録) → fix 子 1 本で closed、
  焦点再レビュー 1 本で回帰なし。plan の訂正: `B4PrerunIssuerError` に `.detail` 属性は無く `str(exc)` から接頭辞を除く。
- **現物 3 campaign への実発行の試行 (1 回、01:38 JST、HEAD `2d71a0454`、login):** rc=2、`design_not_feasible` /
  `fewer than 201 eligible scheduled attempts`、candidate_count 0、campaigns = base 4 行 / sort 1 行 / trigger 2 行
  (全 `success`)、stderr 空、`output/b4-prerun-publication` は前後とも不在、作業ツリー clean。発行器まで到達して typed に
  拒否されたのであり、封印発行の成功ではない。
- **足りない入力 (現物に 1 件でも `rejected` があっても組めない 12 field):** attempt_id / block_id / digest_red_classes /
  workload / calibrated_workload_member / initial_proposal_sha256 / bootstrap_member / reference_tps /
  reference_snapshot_hash / reference_receipt_hash / reference_is_unique / arm_digest_received。receipt に要るものの
  全体像 (201 適格赤、予定 attempt と走行の対応、proposal exact value と bootstrap 所属根拠、§5 の 2 欄と precursor への
  結合、全予定 attempt の planned result path) と依存図は insight に書いた。
- 焦点走: 新 test 15 + issuer 42 = 57 緑 (login)、consumer 5 file 202 緑 (dispatch、request 2284.nqsv、150 秒)、
  `check_docs` / `check_codex_agents` / 全史 provenance 監査 (10809 件) rc=0。
- 変異 matrix (container worktree `2d71a0454`、`run_tests.py orchestrator/tests/test_p3_b4_prerun_caller.py`、dispatch):
  probe (全件 SURVIVED 期待) で観測 node を集め、本走は baseline PASSED、負例 10 件 (M1〜M10) すべて KILLED で期待 node と観測 node が完全一致 (matching 11/11)、等価対照 M0 は SURVIVED、MISMATCH 0、harness rc=0。M3 / M4 / M9 は fail-closed の検出力に数えない診断感度 pin (DW-M08) として別枠にし、fail-closed 検出力は M1 / M2 / M5 / M6 / M7 / M8 / M10 の 7 件。probe の観測 node は段 6 焦点再レビューの静的予測表と完全一致した。
- 裁定パッケージ候補 3 件 (insight に本文): (1) 本 wave の成果の認定範囲、(2) bootstrap 集合の定義と固定時点、
  (3) proposal・走行・参照点の対応証拠の出所。いずれも「推奨どおりなら新しい許可は不要」の形で、実装は伴わない。
- 工数: codex 子 7 本 (plan 1、consult 2、author 1、review 2、fix 1、focus review 1 = 全段 `gpt-6-astra` / `medium`)。
  計算ノード job: consumer 焦点走 1、変異 (probe 13 + 本走 13 走)、受入 1。

## 次の一手差分

### 更新

- [T-2632] **P2・更新**: B-4 の適格な赤 precursor の在庫を 0 件から増やす。供給源 (合成ループ campaign の whiteboard) と
  §5.1.1 の適格条件は変えない。成功例への置換と母集合を作るための追加基盤は D1936 項 8 が不採用にしている。
  2026-09-17 の wave で発行器の production 呼び手 (`orchestrator/campaign/p3_b4_prerun_caller.py`) が入り、現物 3 campaign への
  実発行の試行は候補 0 で発行器まで到達し `design_not_feasible` で typed に拒否された (封印 receipt 未取得)。
  **前 wave の順序「(1) 封印発行は (2) と独立」は receipt の取得については成立しない** — 発行器は適格行 < 201 を拒否し、
  非空 batch は現行の保存形式 (whiteboard 5 field、WAL の genome / src_token) から構成できない (12 field の出所なし、
  {{D:b4-prerun-caller-scope}})。残る順序は (2) §5 の 2 欄の記入、(3) 専用 checkout からの通常 base campaign 起動と
  自然発生赤の回収、(4) proposal・走行・参照点の対応証拠の出所と bootstrap 集合の定義・固定時点の裁定、その後に (1) の
  呼び手で封印発行。得られた少数は D1986 項 4 により記述報告までに留める。
  一次資料は `output/insights/2026-09-17/t2632-b4-prerun-issue-caller/README.md`。
  base: 1863292c74c6edd7436547615677fef25bf6350a60db65ba39040421c30174ad
