# handoff: Pegasus env_contract 登録段 wave (2026-07-18 夜)

- 担当: claude fable (bg session、マネージャーループ)。worktree =
  `.claude/worktrees/s8b-c22-launch-cert` (中身は branch `worktree-s8b-env-contract-pegasus`。
  ディレクトリ名が旧 wave 名なのはハーネス隔離パス固定の回避策)
- タスク: worklog (13) 次の一手 2 — Pegasus env_contract 登録段 (計算ノード実測 + attestation)
- プラン: insights 付録 A (凍結済み) (v1)
- 状態: (2026-07-19 更新) **実装・レビュー全完了 → wave commit 済み → certification ジョブ段**。
  初回投入 867863 は qstat 時刻表記 (NQSV `Started Request Time`) のパーサ不一致で allocation 段
  fail-closed (6 秒、証拠 = job-staging/0:867863.nqsv/)。qstat-fix 適用済み、再投入へ。
  最終ゲート = 全走 1870 passed / 26 skipped / 0 failed、W2-fix 統合レビュー (opus) 判定 =
  commit 可 (抜き取り変異 8/8 KILL 独立再現)。W5 編入事項 = 契約不変式 required⟹single_process +
  pegasus literal/golden 群。以下は経過ログ (古い順):
  - ベースライン全走 1549 passed / 24 skipped (worktree、前 wave 末と一致)
  - codex 敵対相談 C1-C3 完了 (gpt-5.6-sol reasoning=max)。逐語 + プロンプト + **親裁定表** =
    `output/insights/2026-07-18_env-contract-pegasus-consultations.md` (全所見 real、縮小 2 点:
    FD 常時保持 openat 全面化 / APERF/MPERF は見送り)。親検算で C1/C2/C3 の中核クレーム実コード
    確認済み
  - プラン v2 凍結 = insights 付録 A (凍結済み) (設計裁定 §1、単位分割 §2:
    W0 interface 凍結 → W1 並列 L1-L4 → W2a/W2b 結線 → W3 ジョブ資材 → W4 実測 → W5 登録 → W6 docs)
  - W0 (interface 凍結) codex 実装完了 → opus レビュー 2 レンズ完了。レンズ B = 準拠 12/12・
    Critical/High ゼロ。レンズ A = production 健全 (live hole なし・golden 独立再計算一致) だが
    **変異ゲートで positive control 欠落 11 本** (A1 accepted cross-check 7 / A2 常時 cross 2 /
    A3 requested_s 遮蔽 / A4 tsc median 遮蔽)。A5 (/scr 完全一致限界 + "pegasus-runbook §1"
    substring) は W5 申し送り
  - W1 波 codex 全 6 単位**実装完了** (W0-fix / L1 / L2 / L3 / L4 / W3、各報告で全走緑)。レビュー
    進行: W0×2 完了 (A: positive control 11 本欠落 → W0-fix で解消済) / L2×2 完了 (polish 条件付き
    合格) / L3-B 完了 (High: AST 登録漏れ検出) / L1×2・L3-A・L4×2・W3×2 実行中
  - **レビュー 10/10 完了**。所見台帳 = insights 付録 B (凍結済み) (正本コピー、
    ~/.claude/jobs/9b2bec65/tmp/findings_ledger.md と同一)。全単位「polish 条件付き合格」、
    refuted 級の設計欠陥なし。主要 High: L4 visibility gate 未接続 / L4-A acquisition gate
    fail-open 実証 (host 照合) / W3-A ERR trap × set +e で拒否 forensic が dead / L3-B AST 登録漏れ
  - **現在: polish 単位 (22 項目) codex 実行中** (プロンプト = tmp/exec_polish.md)。walltime 包含
    意味論 (required_s <= elapstim_req_s、実機 blocking) / visibility gate / captured_utc /
    attestation_mode 必須引数化 / 変異ゲート閉鎖の負例群 / AST 登録 / ERR trap 修正を一括
  - 次: polish → 親検算 (全走 + 変異抜き取り) → W2a∥W2b (floor/oracle 結線、プロンプト準備済み =
    tmp/exec_w2a.md, exec_w2b.md) → opus 2 レンズレビュー → 親最終ゲート → W4 (smoke ×3 →
    tolerance 凍結 (式は台帳 W3-B 節の親案) → certification ジョブ) → W5 登録 → W6 docs。
    W4 検収 = C3 の 9 条件 + smoke 確定 11 項 + module 実在確認 (台帳参照)
- 環境事実 (今夜時点): gen_S 20 本稼働・interactive/debug 空、SFC ポイント残 438.06、quota 余裕
- 注意: EnterWorktree ツールはハーネス不具合で恒常失敗 (ERR_STREAM_PREMATURE_CLOSE)。git 直接操作で
  worktree 運用中。push はユーザー引き渡し (Pegasus 規約)
- **W4 smoke ×3 実測 (2026-07-19、867857-9、bnode003/004/030) の確定事実**:
  - ハード = Xeon Platinum 8468 / 48 CPU / HT off / 1 socket / **NUMA 1 node** → numactl 規則発動 =
    `()` (none) で凍結。hidepid なし、kthreadd 可視、/scr 書込可、ノード無負荷 (load 0.07)
  - **破れた前提 2 つ → W4-fix 単位で修正中**: (1) /proc/1/ns/pid は非 root で読めず PID ns 判定が
    恒久 fail → /proc/2/comm==kthreadd 指標へ差し替え。(2) $PBS_JOBID は `0:NNN.nqsv` 形式で
    request ID (`NNN.nqsv`) と不一致 + qstat -f に渡せない → 先頭 `0:` のみ除去の正規化比較へ
  - module に gcc/cmake なし (intel/cuda/nvhpc のみ) → **システム gcc/g++/cmake を使用**、次回
    smoke でバージョン実測。gen_S Elapse 上限 = 86400s (2h 要求は余裕)
  - effective clock 分布は probe fail のため未取得 → W4-fix 後に smoke 再走 ×3 で取得し tolerance 凍結
- **W4-fix 後 smoke 再走 ×3 (867860-2、bnode003/004/030) — 全 probe 成功、凍結値確定**:
  - effective clock 中央値 = 2101.0 MHz (3 ノード完全一致、governor=performance) →
    **tolerance_pct = 2.0 で凍結** (式: ノード間中央値最大偏差×2、下限 2% → 偏差 0 なので下限発動)
  - TSC = 2100 clocks/us (3 ノード一致)。visibility = hidepid "0" / proc2-kthreadd / shared=True。
    qstat -f は正規化 ID で成功 (rc=0)
  - toolchain 実測: gcc/g++ = システム Ubuntu 11.4.0 (/usr/bin/x86_64-linux-gnu-gcc-11)、
    cmake 3.25.0 (既定 module intelpython/2022.3.1 経由 — module list 記録で pin)
  - **certification ジョブは wave commit 後** (submit_certify の clean tree 検査は provenance gate、
    迂回しない)。投入時に tolerance 2.0 を渡す
- レビュー記録: W0 レンズ B (opus) = Critical/High ゼロ・準拠 12/12・1641 passed 独立検算。
  持ち越し 2 点: (1) schema_v2 の accepted 整合が request_id↔PBS_JOBID 等値を要求 — **smoke で実
  表記を確認してから W5 へ** (fail-closed 方向なので W0 修正不要)。(2) L1 レビュー時に
  「load_verified_calibration が raw bytes を validator へ渡す (dict 直渡しは duplicate-key 検出
  が失われる)」を確認対象に
- 別件: §10.2 追認リスト 5 項 (前 wave 起票) はユーザー裁定待ちのまま — 本 wave 完了報告時に再提示
