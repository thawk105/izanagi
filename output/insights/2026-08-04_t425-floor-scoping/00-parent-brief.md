# 段 1 brief — [T-425] floor scoping 安価測定 + 取得設計裁定パッケージ

- **scope**: (1) 既存 driver `orchestrator/campaign/between_run_floor.py` の最小 env 化 (Pegasus で走る最小適応、新規 infra なし)。(2) gen_S 1 node の安価 job で 2 動作点 (balanced rr50 + write-heavy rr5) の within/between (8 sessions × 5 reps) を実測。値は **scoping** — floor でも品質ゲートでもない。(3) 真正 floor 取得設計の裁定パッケージ (D145 決定 5 の前提 4 件 + T-425 列挙項 + below-within の事前規定)。
- **確定済みユーザー裁定**: (162) 走行中 land「新規 infra は建てない。1 wave 縛りは測定規模。既存 driver の最小 env 化で安価に測る。値は scoping で floor でなく品質ゲートに使わない」。D145 決定 1〜5 (estimand 命名・非配線・within/between 用途分離・署名別・infra 前提 4 件) と整合させる。
- **不変条件**:
  - I1: scoping 出力を repo 内のどの `<env>/calibration/between_run_noise_*.json` にも置かない (`screening_driver.load_between_run_floor` の glob に不可視)。artifact は job checkout (repo 外) に置き、repo へは insight の digest だけ入れる。成果物影響: 破ると scoping 値が compare の丸め閾値へ静かに配線され受理集合が偽 faster 側へ動く。
  - I2: FROZEN_MANIFEST 23 件の bytes・`output/s8b-freeze/`・`output/campaigns/`・registered calibration に触れない。成果物影響: 破ると proof chain 検査赤で land 不能。
  - I3: 新規コード・テスト・insight で三軸語 literal (`"ycsb_rratio": "50"` 等) を直書きせず変数合成 (unknownness live-grep の hit 集合と D88 検出語 scan を動かさない)。成果物影響: 破ると 8b freeze の positive control 数が現実とずれ、監査が偽装差分を疑う状態になる。
  - I4: 測定 job は wave worktree 外の専用 checkout (`/work/1/SFC/tanab/dev-wave-jobs/t425-floor-scoping/run/`) で committed bytes を走らせる (F98 回避 = campaign 形 runtime 出力を worktree に作らない)。
  - I5: job script は interpreter 版数 gate (python3 → 3.9 問題、floor_campaign.sh:157-178 と同型) を持ち、`qsub -v VAR=value` の sanctioned 形 (F99) を使う。records/threads/clk は Pegasus registered calibration (rr50, 1M, 48) と実行時照合する (p2_2._resolve と同型)。
  - I6: 正しさゲート・防壁・受理集合に触れる変更はしない。新 gate も新設しない (O13 不成立)。
- **成果物の形**: (a) env 化 diff + テスト (codex author、wave branch へ commit)。(b) scoping 実測値 (JSON/MD digest → insight 逐語)。(c) 裁定パッケージ `/work/1/SFC/tanab/dev-wave-jobs/t425-floor-scoping/ruling-package.md`。(d) worklog/decisions fragment。
- **並列分割**: 軽量版 (DW-C00 該当なし: 設計択一は裁定パッケージでユーザーへ返し本 wave では決めない・防壁非接触・受理集合不変)。段 2・3 省略。段 5 = codex author 1 本 (小 diff、所有 = orchestrator/campaign + tools/pegasus の新 job script + テスト)。段 6 = fix 子 (必要時) + 親の受入・変異 matrix。
- **環境 (実測 2026-08-04 14:40)**: 緊急保守 15:00–19:00 (job 実行不可)、gen_S QUE 227 滞留・RUN 0、SFC 残 308.47 pt、quota 健全。login python3 = 3.10.12。投入は保守明け後、dispatch_compute (tests) と scoping job の双方が queue 待ちになる前提で待機計画を持つ。
- **provisional 前提 (親裁定・攻撃対象)**:
  - (P1) 動作点は rr50 + rr5 の 2 点で足りる (rr95 は省く。linux の 3 点非一様性は転移知識として package に引用)。
  - (P2) SESSIONS=8/reps=5/EXTIME=3 は既存 driver のまま変えない (「測定規模」の縮小は点数で行う)。
  - (P3) 単一テナント検査は既存 `_assert_single_tenant` (competing bench pids) のまま + uptime/load の telemetry 記録のみ追加せず解釈で扱う (gen_S Exclusive OFF の残余は package に明記)。
  - (P4) queue 滞留で測定が wave 内に完了しない場合は、submit receipt + 検証済み env 化 + 値スロット pending の package で閉じ、再開手順を worklog に書く (測定を省くのではなく待ちの実測事実を記録する)。
