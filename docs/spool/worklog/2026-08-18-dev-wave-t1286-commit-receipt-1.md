---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-18
wave: dev-wave-t1286-commit-receipt
seq: 1
title: COMMIT へ verifier 発行の一回限り receipt を要求し、新 lock を批准済み digest と比較し、ident の第 3 経路を塞いだ — 焦点走 1388 passed の下で門は開いたままだった (コード + テスト + 記録、branch worktree-dev-wave-t1286-commit-receipt、変異 matrix = baseline PASSED・9/9 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- **本 wave の主要な発見は「実装して緑になった後も門が開いていた」ことである。** 段 6 の敵対
  レビュー 2 本が独立に同じ中核欠陥へ到達した。焦点走 23 file が 1388 passed / 0 failed の状態で、
  `VerifyResult(trace_dir="never-read", serializable=True, n_txns=1)` を手で構築して issuer へ
  渡すだけで live receipt が発行できた。trace parser も verifier entrypoint も一度も呼ばれない。
  同型が 3 面あった (primary issuer・replay issuer・capability 再利用)。
  **「receipt を要求する検査を足した」ことと「receipt が verifier 由来である」ことは別**であり、
  前者だけを実装するとテストも同じ caller-built 経路で receipt を作るため全緑になる。
- **恒真の罠を段 1 の実測で先回りした。** repo 内の campaign lock は
  `output/campaigns/` 30 件と凍結 2 件の計 32 件で、**すべて v1** (`authority` が null)。
  v2 は 1 件も無い。既存の per-COMMIT contract 検査は v2 でも legacy key でもない lock で
  早期 return するため live 32 件のどれでも 1 度も発火していなかった。新 gate を同じ v2 枝の
  内側へ置いていれば実装しても発火しない恒真な保証になっていた。gate は lock version 分岐の外へ置いた。
  同じ実測が {{D:enforcement-source-ratification}} の副作用評価にも効いた — 批准台帳を 0 行のまま
  land すると新 certified lock 生成は fail-closed になるが、v2 lock が存在しないため live 影響はゼロである。
- **レンズ A の「T-1287 を land せずユーザー裁定へ戻せ」を部分 refuted した。** レンズ A は
  repo 内 JSONL 台帳の自己批准可能性と D287 / D414 を根拠に勧告したが、脅威モデルを
  取り違えている。規律 2 が名指しする主体は AI 実装者であり、親は `hooks/` 配下への書き込みが
  Write でも Bash リダイレクトでも機械的に拒否されることを実測した。残る制限は採用し、
  **「人間が批准したことの証明」は謳わない**ことを設計と文言の制約として固定した。
  外部 trust root と署名の要否は裁定へ返す。
- **親 brief の主張を 7 件撤回した。** producer 数 (3→5)、`guided.py` の実効防護、pin 閉包の
  file 数 (8→12)、live lock 件数 (30→32)、実装順序、判定器 module 候補、[T-396] との衝突。
  段 3 の 2 レンズが親自身の実測も攻撃対象にした結果である。
- **[T-396] は plan と着地結果が食い違った。** T-396 の段 2 プランは closure 定数と
  exact-list pin を編集する計画だったが、land した差分はこれらを 1 件も含まない。
  段 4 で「衝突する」と裁定した前提は着地結果では成立せず、積集合は空だった。
  **並行 wave との衝突判定は plan でなく着地差分で行う。** {{F:concurrent-wave-collision-by-plan}}
- **赤の帰属を 2 度、実測が覆した。** (1) 単位 B の初回測定 66 failed のうち 29 件は
  closure member の未 commit 差分による `contract-loader-drift` で、commit すると 37 へ落ちた。
  (2) must-fix 巡の副作用 8 件のうち 2 件は本 wave が一度も触っていない test file だったが、
  main tip の checkout では 178 passed であり、実測の結果 8 件すべて本 wave 帰属だった。
  **「触っていない file だから非帰属」という論法を使ってはならない。**
- **codex 子は本 wave でも pytest を 1 件も実走できず**、測定は全巡 親が引き受けた。
  段 3 の 2 レンズは codex 認証の 401 で出力ゼロ即死し、prompt を変えて job-id を変えることで
  再投入した (同一 prompt は「既存の完全な receipt は上書きできない」で rc=2)。
- **エージェント工数**: codex 子 11 本 (plan 1・consult 2 + 失敗 2・author 3・fix 6・review 2)。
  段 5 単位 A は 35 model call / 604 秒。段 6 の must-fix 収束に fix を 2 巡要した。
- 変異は 9 件とも wave 前の実コードの形 (検査なし・v2 枝限定・直接呼び・exact 14 閉包・
  receipt 自身との自己照合) を再現した。m2 / m3 / m4 / m6 は killer がちょうど 1 node で、
  その門が守る性質を名指しするテストだけが落ちる。m7 / m8 / m9 は閉包 consumer が広く
  過剰決定のため冗長 gate として記録し、単独変異の精密な証拠には数えない。
- 正本 = `output/insights/2026-08-18_t1286-commit-receipt-closure/README.md`

## 次の一手差分

### 完了

- [T-1286] 全 `STAGE_COMMIT` producer 5 件 (campaign WAL 3 / qualification 2) に、
  verifier が実走行の内側で発行する PID・process seal 付き capability へ結び付いた
  一回限りの receipt を要求させた。支配点は `wal.append` と `QualificationEventSink.emit` の 2 つで、
  lock version 分岐の外へ置いた。一回限りは ledger 単位である。
  remaining: none
  base: e5fe802995f1ed0bb2e67f80799fdf96f51ce71c847e677ad5b91d02fad84828
- [T-1287] 新 certified lock の生成時に、closure の path→blob map 全体の canonical hash を
  批准済み digest 集合と比較する。台帳は `hooks/` 配下の read-only JSONL で、AI 実装者は
  機械的に追記できない。0 行のまま land するため新 certified lock 生成は fail-closed になる。
  remaining: none
  base: 4be7f6c166f8710ea5858b7cdbbcd7ee4565b2455b3b683c5716f02332ca03ef
- [T-762] `ident.py` の第 3 経路を塞いだ。current head 用と historical prefix 用の
  検証済み wrapper 2 種を `env_contract` へ置き、直接呼びが素通りしていた 4 検査
  (行ごとの calibration 検証・registry 交差検査・verified hash 集合の更新・fork 安全 cache) を回復した。
  remaining: none
  base: f7301e1f26c46b261698f2ee498269b4e066bfc69e8653e20b0155bc15951eaa
- [T-1252] 認証閉包の対象へ S8C 判定器 3 module を含めた。閉包は exact 14 から 25 path へ広げ、
  批准比較自身の自己保護と receipt 実装面も加えた。
  remaining: none
  base: 0a114216730d68dbd5b86ad682ac61714ab4acd076bb941213460fbec3ca049e

### 新規

- {{T:receipt-cross-layout-single-use}} **P2・新規 (本 wave の段 3 レンズ A が検出、scope 外)**:
  同じ lock bytes を 2 つの layout root へ置くと、各 ledger の消費済み集合は空なので
  同じ COMMIT receipt が各 1 回通る。外部状態を持たない限り「全 layout 横断で一回限り」は
  証明できない。裁定文の「一回限り」を ledger 単位と読むか全 layout 横断と読むかを決める。
- {{T:commit-receipt-consumer-verification}} **P2・新規 (本 wave の段 3 レンズ B が検出、scope 外)**:
  `s1_report.py` / `tools/plotting/plot_backoff.py` / `p2_2_report.py` / `backoff_repro.py` は
  `STAGE_COMMIT` の存在だけで sample を採り、receipt を再検証しない。裁定は producer 面を
  名指しており consumer 面は未裁定である。歴史 raw 専用とするか receipt 検証を要求するかを決める。
- {{T:ratification-external-trust-root}} **P3・新規 (本 wave の段 6 レンズ A が検出、scope 外)**:
  批准台帳の `hooks/` 配置は AI 実装者の追記を機械的に塞ぐが、暗号学的な人間承認証明ではない。
  外部 trust root と署名を新設するかを決める。粗い provenance 方針との整合も併せて裁定する。
