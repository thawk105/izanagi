---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-29
wave: dev-wave-t1819-a1-parent-submitter
seq: 1
title: [T-1819] A-1 投入器の起票前提を反証し、残っていた実在欠陥 5 件を局所修正した (code + tests + docs、branch worktree-dev-wave-t1819-a1-parent-submitter、変異 事前登録 7/7・事後登録 3/3 KILLED)
---

## 本文

- 起票 (2026-08-26) の前提「A-1 に親側直接 qsub と acquisition receipt の create-only 書き出しが
  無い」は着手時の実測で覆った。同日 land した [T-2006] が D1028 に従って `run_submit` /
  `_run_qsub` / `_canonical_qsub_contract` / `_exclusive_write` と 4 本の test を実装済みだった。
  「他 job body の `submit_*.sh` に対応する部品が無い」という字面も設計差であり、A-1 の job body 自身が
  「親が直接 qsub する。この file は投入器ではない」と宣言している。段 2 は `guard_bash.decide()` へ
  実 command 列を与える read-only probe を走らせ、正式投入経路が機械防壁を通ることを rc=0 で実測した。
- ただし durable measurement base を作る部品だけは本当に無く、policy が指す base も実在しなかった。
  手本の A-2 は preregister で base を作る。この一点において「正式投入経路が塞がっている」は事実だった。
- 実装したのは投入器に残る実在欠陥 5 件だけである。R1 acquisition receipt の create-only 書き出しが
  原子的でなく、compute 側 job body が path の存在だけで待機を終えて即読みするため途中 bytes を読む窓が
  あった。R2 qsub 前の fresh-attempt 検査が evidence 4 path のうち 3 つを見ていなかった。
  R5 durable base の作成部品が無かった。段 6 レビューが足した MF1 staging の後始末欠落、
  MF2 staging 衝突による未承認の過剰拒否、MF4 staging basename の長さ上限。
  新しい署名・nonce・schema・汎用 framework は作っていない。既存テストの期待値も変えていない。
- 段 2 が提案した CCBench strict clean gate は不採用にし裁定パッケージで返す ({{D:a1-ccbench-acceptance-set-owner}})。
  段 3 の 2 本ともそのままの実装に反対した。sol は「A-1 の arm は CCBench を dirty 化して作られる」を
  refuted (同じ live source に異なる CMake flags) とした一方、allowlist 内の dirty source が
  generator receipt 経由で valid な A-1 へ入る経路は real と判定した。
- wave 中に local main が 10 commit 進み `/rulings` 第 12 回の裁定 49 件が fold された。主題照合で
  **D1262 が本 wave の裁定の根拠を置き換えた**ため、U1 の結論は変えず理由を差し替えた。
  D1291 (qsub の `-o` / `-e` を repo 外へ) は `submit_certify.sh` が対象で、A-1 は evidence path が
  durable base 直下 = repo 外のため既に適合しており追加実装は無い。
- 変異は**事前登録 7 件と事後登録 3 件を分けて**記録する。段 6 のレビュー所見に対する fix の変異を
  fix 子の起動前に登録する規則が `DW-M01` に無いため事後登録が生じた ({{F:stage6-fix-mutation-timing}})。
  10 件とも KILLED・期待 node 完全一致だが、M1 (15 node) と M6 (11 node) は過剰決定であり、
  `DW-M03` に従い冗長 gate と明記して単独変異の帰属証拠から外す。publish 経路の帰属は
  M2 (2 node)・M8・M9・M10 (各 1 node) が担う。
- 段 5 実装子と段 6 fix 子はいずれも計算ノード混雑でテストを実走できず、正直に「未実走」と報告した。
  テストは親が実測した。gen_S は QUE 45 / RUN 14 / HLD 24 で、親の焦点走も 1 度
  queue-wait-timeout (rc=16、`child_started=false`、infra 分類) に当たっている。
- 変異 wrapper は共有木の観測 bytes 変化で 1 度 rc=125 になった。並行 wave が main checkout を
  絶えず動かしているためで、独立 clone を `--source-repo` に渡して回避した。
- 正式 qsub、A-1 の実測投入、CCBench gate、login 側 shell 投入器、push、次 wave 起動は行っていない。

## 次の一手差分

### 完了

- [T-1819] 起票前提の反証と、A-1 投入器に残っていた実在欠陥 5 件の局所修正を完了した。
  remaining: none
  base: a6ba2de5f6cfbd66a102fc516872079b8ccc76a6f1f45f67ec5d4ed36d6d20e6

### 更新

- [T-1818] **P2・要照合**: 非認証成果物型の実体は [T-2006] が D1028 に従い投入器と同じ変更単位で
  実装済みである可能性が高い。本 wave が [T-1819] で同じ stale carry を実測したため併記する。
  着手前に main の現物へ照合し、済んでいれば実装せず閉じる。
  base: b9b968a29c5df6038db2addf8c880ba11180e1f14a7fd96d7e3a40c4abb674eb

### 新規

- {{T:a1-ccbench-acceptance-set}} **P2・ユーザー裁定待ち**: A-1 が dirty な CCBench source を
  受理し続けるかを、D1262 の再凍結と同じ変更単位で決める。段 3 sol が
  `submodule.external/ccbench.ignore=all` で親 status を通過する経路と、allowlist 内 dirty source が
  generator receipt 経由で valid な A-1 へ入る経路を実測している。
