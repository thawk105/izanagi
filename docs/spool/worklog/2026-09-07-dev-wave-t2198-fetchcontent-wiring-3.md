---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-07
wave: dev-wave-t2198-fetchcontent-wiring
seq: 3
title: [T-2198] 認証経路のオフライン配線は閉じた trace0 文法に塞がれ、実装せず裁定へ返した (docs のみ、branch worktree-dev-wave-t2198-fetchcontent-wiring)
---

## 本文

- **D1524 の理由節の前提が反証された。** 「足りないのは引数の引き回しだけである」という
  記述に対し、引き回しても A-6 の read-heavy は 1 件も測れないことを実コードで確認した。
  阻害要因の連鎖と逃げ道の不在は {{D:a2-trace0-grammar-blocks-offline-wiring}}、
  失敗としての記録は {{F:upstream-argv-wiring-blocked-by-downstream-closed-grammar}}。
- 段 4 で `DW-S04` に従い実装せず、解消案 3 つと親の推奨 (案 1) を添えてユーザー再裁定へ返した。
  段 5・6 を飛ばし `4 → 7 → 8 → 9` とした。実装面の差分はゼロなので `DW-S04` の規定により
  変異 matrix を免除する。
- 段 3 の敵対レンズ 2 本が親 brief の誤りを 3 点突き、親がいずれも一次資料で追認した。
  - 通す引数は 4 本でなく 5 本 ({{D:fetchcontent-wiring-needs-five-arguments}})。
  - 「source dir を渡さない caller の identity は 1 bit も動かない」は一般化しすぎ。正しくは
    「新 5 引数をすべて既定値のままにする caller は動かない」。base と receipt だけを渡す
    base-only caller は既存 API で有効で、identity も argv も変わる。
  - 段 1 の pin 閉包の「literal pin 0 件」は編集対象 4 file の話でしかなく、policy JSON の
    golden 4 値を閉包から落としていた。
- FetchContent の build identity が依存内容を完全には束縛しない件を
  {{D:fetchcontent-identity-does-not-bind-all-dependency-content}} に記録した。A-2 / A-6 は
  cache root が job-local なので実際の露出は無く、本 wave の blocker ではない。
- A-6 の tracked destination `output/insights/2026-09-02_paper-story-a6-certification` が既に存在し
  `materialize` は既存 destination を無条件で拒否する。本 wave は実測しないので blocker では
  ないが、案 1 を採る場合は実測前に destination を決める必要がある。
- 実測の投入は行っていない。実装面の変更もゼロで、記録のみの wave である。
- エージェント工数: 段 2 プラン 1 本 (codex plan, xhigh, rc=0)、段 3 敵対相談 2 本
  (codex consult sol / luna, xhigh, いずれも rc=0)。段 5・6 の子は起動していない。

## 次の一手差分

### 更新

- [T-2198] **P1・ユーザー裁定待ち**: 認証経路のオフライン配線は、閉じた trace0 argv 文法を
  広げない限り発火しない。文法は凍結された認証プロトコルの同一性に含まれるため、
  {{D:a2-trace0-grammar-blocks-offline-wiring}} の解消案 1 / 2 / 3 から人間が選ぶ。
  親の推奨は案 1 (文法へ厳密な枠を足し golden 4 値を張り直す)。
  base: 69e75709b5e349cef30a458bb7ce5e50caf73fa076702ccb0b5a7885c5a0e938
