---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-27
wave: dev-wave-t1769-b4-wiring-probe
seq: 1
title: [T-1769] B-4 事前登録 §5.1 (ii) の非標本 probe を新設し、outcome 非生成を発火する機構で保証した — 事前登録の記述 1 件が sort について偽だったことも実測で判明 (コード + docs、branch worktree-dev-wave-t1769-b4-wiring-probe、変異 matrix = baseline PASSED・14/14 一致・KILLED 9・SURVIVED 5・MISMATCH 0)
---

## 本文

- 依頼は「§5.1 (ii) を満たす非標本 probe を設計・実装し、outcome を生成しないことを機械保証する。
  恒真な保証にせず、生成してしまう負例で発火することを検査で示す」。**実装し、発火を実測した。**
  実装は `orchestrator/campaign/p3_b4_wiring_probe.py` (2159 行)、検査は
  `orchestrator/tests/test_p3_b4_wiring_probe.py` (1171 行)。素材は
  `output/insights/2026-08-27_t1769-b4-wiring-probe/`。
- **段 3 の敵対レンズが親 brief の一般化を refuted し、そこから事前登録文書の誤りが 1 件出た。**
  親は「build 無し経路は切替点を通らない」を driver 非依存の事実として brief に書いたが、
  実測すると sort driver だけは無条件に通る。**事前登録 §10 の同じ記述も sort について偽だった。**
  driver 別に書き分け、sort の build 無し経路が probe にならない本当の理由 (iteration を実走して
  checkpoint と whiteboard 結果を書く) へ差し替えた。probe の証拠はこれを driver 別の guard 式として
  機械記録する。
- **段 6 レビュー A が最重要の恒真を突いた。** 負例が遮断機構を子 process で直接組み立てて
  発火を見るだけで、**CLI 本体がその機構を装着することを一度も検査していなかった。**
  本体から装着を消しても証拠 boolean は `true` のまま全検査が通る形だった。
  fix で観測由来へ変え、実 `main(argv)` を通る負例を置き、変異 MW01/MW02 で殺されることを実走で示した。
- **段 6 レビュー B が受入で必ず赤になる箇所を予測し、親が実測で確定した。**
  新規 test file に自走 harness が無く `test_plain_runner_coverage.py` が赤。
  親の段 6 焦点走はこの consumer を漏らしていた。レビューが無ければ受入全走を 1 回捨てていた。
- **レンズ B の総括「停止せよ」は refuted した。** 承認経路が実 campaign 3 件の台帳を読む事実は
  正しいが、迂回すると digest 生成が要求する exact な型を作れず正しさゲートの緩和になる。
  黙らせず開示する形に変えた ({{D:b4-probe-admission-overlay-disclosure}})。
- **親が事前登録した変異 15 件のうち 3 件は生存、7 件は過剰決定だと段 6 レビューが静的に指摘した。**
  これは実装でなく親の登録設計の不備であり、実効 gate へ再照準して 14 件に組み直した。
  期待ノードは推測せず観測走で実観測した完全集合を使い、本走で 14/14 完全一致した。
- **生存 5 件の原因は遮蔽ではなく到達不能だった。** 親は当初「他層が同じ入力を拒否している」と
  見立てたが、遮蔽候補を同時に外す両層同時変異でも 5 件とも生存した。実装を読み直すと、
  違反 ledger へ追記する箇所は追記の直後に必ず例外を送出するため、違反が記録されたまま publish へ
  到達する状態は構造的に起こらない。多重防御として残し、発火する保証には数えないと決めた
  ({{D:mutation-unreachable-defence}})。
- **親が読込み契約を守らず、変異走行 3 回を捨てた。** 変異 harness の走らせ方 (runner argv へ
  明示投入を入れる、local は runner が自壊する、probe は全件 SURVIVED 期待で登録する) は
  **着手時点の `docs/dev-wave/mutation.md` DW-M07 に既に書かれていた。** 条件 dispatch 15 番は
  「fix 後に変異を走らせる直前」に同節を読めと定めるが、親は DW-M01〜M06・M08 だけを読み
  M07 を飛ばした。結果、受領証 0 行で 3 走が同じ位置で止まり、local 指定への切替えという
  誤った切り分けも 1 回挟んだ。**文書の欠落ではないので段 8 の候補は却下した。**
- **実装子は pytest を 1 nodeid も実走できなかった** (計算資源の認証で child 未起動、rc=16)。
  実測はすべて親が行った。焦点走 = 新規 test 62 件緑、内容走査型 consumer 群 1902 件緑、
  `check_docs.py` / `check_codex_agents.py` rc=0。
- **§5 の欄は 1 つも埋めていない。** §5.1 (i) の先行 freeze は記入者とレビュー者の指名を含み、
  人間の手番である。本 wave の実走は道具の dogfood であって §5.1 (ii) の採用証拠ではないと
  証拠 JSON・insight・事前登録の 3 か所へ明記した。

## 次の一手差分

### 更新

- [T-1769] **P1・人間の手番待ち**: B-4 §5.1 (ii) を満たす sanctioned CLI は
  `orchestrator/campaign/p3_b4_wiring_probe.py` として実在する (2026-08-27)。
  残るのは §5.1 (i) の先行 freeze — 候補 driver 集合・各 exact command・証拠 path と hash・
  合格 0 件/複数件の決定規則・**記入者とレビュー者** — を別 commit で固定すること。
  記入者とレビュー者の指名は人間の手番であり AI が確定できない。指名が済めばその版に従って
  (ii) を実測し、合格した driver と軸だけを §5 へ記入できる。
  base: e8bfbf2f4c9f961113fd998b3d96da5e25041aa7c3d1d3076951668d0a62995b
