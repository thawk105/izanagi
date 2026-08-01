# T-126 qualification-first amendment — 段 1 brief

- scope は、ユーザーが択 (a) と裁定した qualification-first amendment の 1 wave に限定する。
- formal headline へ昇格不能な qualification-only series、逐次停止の純粋判定核、厳格な機械
  receipt と検証器、live positive control を成果物にする。
- production near-floor admission、headline gate、Layer3 authoritative consumer は別 wave に残す。
- bench rep 打ち切り、verify seed 逐次停止、floor 校正削減、bench-only 軽量形は対象外。
- D19 の between-run floor、reps=5、D36 の legacy+S2、anomaly 即 reject は一切変えない。
- qualification の入力は専用 namespace だけで受け、formal source eligibility を付与しない。
- live control の既存 artifact は
  `output/campaigns/p2-2-silo-read-heavy-enumerate-5ffcabad/runs/wal.jsonl`。
  `B0-T-W0` 対 `B0-L-W0` は committed で差 0.5%、between-run floor 内の既知 no-difference pair。
- 現 host は Pegasus login node、submodule は `d706650` で初期化済み。コード・テストは login
  node、live control は Pegasus 計算ノードの単一 job / process 内で走らせる。
- Pegasus は `allow_resume=false` のため、qualification series は allocation を跨いで再開しない。
  中断・walltime 超過・環境 attestation 不成立は receipt 不成立へ fail-closed に倒す。
- live receipt は「qualification plumbing が実データで発火した」証拠であり、same-boot 系列へ
  SPRT の名目 α/β や production readiness を主張しない。
- receipt が valid でも formal promotion は行わず、次 wave の production gate を自動起動しない。
- 既存被覆は `near_floor` 境界・report 警告・generic WAL / env contract。純増検出力は
  SPRT 全系列、qualification namespace 非交差、receipt の identity / provenance / terminal
  完全性、formal consumer 非到達、live job の実発火である。
- 放置時の成果物影響: T-126 は unqualified のままで、production gate を安全に実装するための
  live 証拠と hold 解除材料が存在しない。certified 選択・formal report の現値は変わらない。
- `(P1)` receipt は immutable JSON 1 個 + 参照する series ledger / round WAL の strict validator
  とし、valid receipt 自体に promotion authority を与えない。親の provisional 裁定であり攻撃対象。
- `(P2)` control pair と Pegasus same-boot run は statistical validation でなく wiring
  qualification の positive control と裁定する。親の provisional 裁定であり攻撃対象。
- 実装面は隔離した Codex author worker 1 本へ所有させ、manager はコード・テストを編集しない。
- 受理集合・proof chain・新 gate に触るため、独立 plan、敵対相談 2 本、実装後 review 2 本を省略しない。
