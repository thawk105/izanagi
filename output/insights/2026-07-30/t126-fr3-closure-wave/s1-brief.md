authority: none
default_effect: no-state-change

# T-126 qualification-first FR3 closure — 段 1 brief

- scope は前 wave の最終 NO-GO で real と裁定済みの FR3-1〜4 だけを閉じる fresh wave とする。
- 確定済みユーザー裁定は qualification-first amendment。headline 昇格不能な専用系列の live
  observational smoke と machine-readable receipt を先行し、production gate / authoritative consumer は
  証拠取得後の別 wave に残す。
- FR3-1: qsub 非 0 の stdout を再利用せず、rc=0 の durable record または bind 前の exact scheduler
  proof だけを submission authority にする。
- FR3-2: scheduler terminal 後、collector 単独で exact job-result staging を回収または破棄し、
  final / failure のどちらかへ閉じる。
- FR3-3: normal submission の valid canonical job-result は非 null canonical pointer と exact bytes を
  必須にし、pointer-null の coherent rehash で retry authority を得られないようにする。
- FR3-4: terminal publisher と early trap は committed scratch の stdlib-only bytes だけを実行し、
  submit 後の persistent worktree import をゼロにする。
- 成果物影響: FR3-1 を放置すると nonexistent / unrelated job を canonical initial として消費し、
  receipt と accounting closure を失う。
- 成果物影響: FR3-2 / FR3-4 を放置すると clean result または terminal accounting があっても
  final / failure receipt のどちらにも収束せず、実行 bytes の proof chain も一致しない。
- 成果物影響: FR3-3 を放置すると member-rejected な canonical RC30 から不正な RC34 retry receipt を作れる。
- 不変条件: evidence-only / no-promotion、`hold_enforced=false`、`statistical_claim=none`、
  qualification lineage の formal Layer3 拒否、正しさ gate、既存 formal caller の受理集合を変えない。
- 不変条件: 既存の凍結成果物 bytes は変更しない。新規 attempt / receipt は committed source と
  canonical submission / accounting / job-result bytes に束縛し、未発行の将来成果物だけを producer が作る。
- 不変条件: Pegasus は `allow_resume=false`。live run は単一 allocation / process で完遂し、
  観測値に合否や統計主張を後付けしない。
- 成果物は FR3-1〜4 の production code、各反例の独立 fixture、更新済み mutation matrix、
  計算ノードでの関連・全受入、live qualification の canonical final または failure receipt とする。
- build、test、check、mutation、live control はすべて Pegasus 計算ノードで実行し、ログインノードでは
  静的読取と隔離 Codex worker の実行だけを行う。
- 段 2 は read-only Codex planner 1 本、段 3 は authority / crash closure の異なる敵対レンズ 2 本。
  段 5 は相互依存する4件を単一 workspace-write author に戻し、親は実装面を編集しない。
- 旧 brief / plan / review は再利用せず、前 wave の実装差分と FR3 裁定を証拠入力としてだけ渡す。
- `DW-O08` に従う submodule `d706650` は初期化済み。既存凍結 bytes を変更しないため
  `DW-O09` / `DW-O10` は発火しない。
