---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-26
wave: dev-wave-mocc-trace-pair
seq: 1
title: mocc の pilot を同一 source の性能と正しさの対として取り直し、3 本中 1 本の G2 anomaly を記録した (コード + 計測 + docs、branch worktree-dev-wave-mocc-trace-pair、変異 matrix = baseline PASSED・19/19 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- 依頼は「クロスプロトコル素材 mocc の pilot を、性能と正しさの対として取り直す。同一 workload・
  同一 build 系統で trace-enabled 側と trace-disabled 側を対にし、片側だけの単一観測にしない。
  正しさ検証と性能計測は必ず別ビルド・別 run (規律 1)。C-1 は現在の論文の必要条件ではないので、
  成果を headline・certified な選択・floor・oracle・fitness の根拠に格上げせず、
  `official_certification=false` のままである点も正直に記録する」。
- **対でなかった理由は source の不一致だった。** 既存 TRACE=1 証拠は ccbench `ef9328a3`、
  既存 TRACE=0 証拠は `058d0c4e` で、後者は前者の子。trace hook は保持されているので同一 source の
  対は原理的に成立する — これを DW-G01 の生死確認 1 本 (98 秒) で先に確かめてから機構を作った。
- **本 wave の一次の障害は「2 本目が投げられないこと」だった。** N>=2 を阻む実測障害が 3 つあり、
  うち共有 hydrate 先の in-place 汚染 ({{F:mocc-shared-hydrate-inplace}}) は 1 つ前の mocc pilot が
  「scope 外所見」として handoff へ送っていた既知型である。対を N 本取る wave では回避できなかった。
  残り 2 つは {{F:submit-residue-blocks-next-submit}}。
- **段 3 の 2 レンズが独立に同じ核心へ収束した。** 「pair receipt は内容の形を厳しく見るが、
  その bytes を job へ結ぶ provenance chain が切れている」。実装前の receipt は証拠 artifact を
  filename か null でしか指しておらず、**実 job が生成していない合成 JSON を certified として
  pair へ通せた** ({{F:evidence-not-bound-to-producer}})。設計は {{D:mocc-trace-pair-gate}}。
- **段 6 のレビューが「実機で必ず落ちる gate」を 1 件見つけ、親が実測で確定させた。**
  同一 mode の binary SHA 一致を必須にしていたが、同じ ccbench source の TRACE=0 ビルドが
  2 回で異なる SHA を出す。**本 wave の対がまさにその形で、この gate を採っていたら
  対はそれ自身に拒否されていた。** `DW-O13` に従い到達不能な述語は採らず記録に降格した
  ({{D:mocc-pair-no-binary-sha-gate}})。過剰拒否を検出する positive control を変異登録し、
  本走で KILLED を確認している。
- **TRACE=1 の 3 本のうち 1 本が non-serializable だった。** verifier は G2 anomaly を 1 件
  (2 トランザクションの rw サイクル) 返し、job は rc=1 で fail-closed した。同 run の integrity は
  clean である。**MoCC 実装の性質か izanagi の trace hook の取り違えかは確定していない。**
  どちらとも断定せず構造化して残し、上流 PR / push の判断は人間に委ねる。
- **certified な TRACE=1 が 2 本しか無かったが、本数条件を緩めなかったし追加投入もしなかった。**
  `n_trace0 == n_trace1 >= 2` は段 4 で実装前に決めた述語であり、事後に落とすのは規律 2 が禁じる
  方向と同型である。緑が出るまで正しさの run を回して緑だけ報告するのは selection bias になる。
  理由は {{D:mocc-pair-cardinality-not-relaxed}}。対から外した TRACE=0 の 3 本目とその値も
  一次資料に全部書いた。
- **成果物の限界を本文へ明記した。** pair receipt の `prohibited_uses` は宣言であって強制ではなく、
  それを読む consumer は repo 内に存在しない。checker の自己申告 SHA は外部 trust anchor ではない。
  live 判定器の TOCTOU は塞いでいない。TRACE=1 receipt の計数から throughput は導出できるが
  導出して性能値として扱わない。
- **paper-story の 2026-08-26 版は凍結物なので編集していない。** C-1 の更新は同ディレクトリ
  README の「最新スナップショット以後に確定したこと」へ書いた。「対でない」は解消し、
  「`official_certification=false` の pilot である」は解消していない。
- **読み込み契約の違反を 1 件自己検出して巻き戻した。** gate を新設する wave なので `DW-O13` が
  段 2 前に成立していたのに、読まずに段 2 の plan 子を回した。旧 plan を invalidate し、
  実 receipt 2 本を渡して段 2 を再実行した。再実行版は全述語の入力を実物で実測し、
  到達不能な案 (tracked policy 全体の byte identity) を裁定へ回してきた。
- **待ち手の誤読を 1 件踏んだ。** 変異本走の 1 回目が起動 1 分で spec の `category` 未知値により
  中止していたが、待ち手は成果物不在のため timeout (rc=70) を返し、外からは「まだ走っている」
  ように見えた。`ps` で producer の生死を確かめて気づいた。`category` の許可値は
  `negative` / `positive` / `both-layers` の 3 つである。
- **裁定パッケージへ回したものが 6 件ある。** pair receipt を必須入力として読む consumer gate の
  新設 (proof chain と oracle gate に触るため依頼の射程外)、TRACE=1 receipt からの計数 field 除去
  (producer の出力 bytes と既存受理集合を変える)、live 判定器の TOCTOU 閉塞、checker の外部
  trust anchor、PBS 出力既定の repo 外化 (機体固有値を repo へ持ち込むため)、attempts root の
  compute node 可視性検査 (現状も fail-closed するので正しさの穴ではない)。

## 次の一手差分

### 新規

- {{T:mocc-g2-reproduction-rate}} **P1・新規**: 同一 workload で mocc の TRACE=1 を反復し、
  G2 anomaly の再現率を測る。本 wave の観測は同一 source 4 本中 1 本にすぎず、
  MoCC 実装の性質か trace hook の取り違えかを分けられていない。
- {{T:mocc-pair-consumer-gate}} **P2・新規・ユーザー裁定待ち**: pair receipt の
  `prohibited_uses` を機械的に強制する consumer gate を置くか決める。置くなら headline・
  certified 選択・floor・oracle・fitness 側に触るため proof chain の scope に入る。
- {{T:mocc-pilot-provenance-residue}} **P2・新規**: mocc pilot の provenance 残件をまとめて扱う。
  TRACE=1 receipt からの計数 field 除去、live 判定器の TOCTOU 閉塞、checker の外部 trust anchor。
- {{T:mocc-pair-operational-residue}} **P3・新規**: pair receipt の sidecar 名が出力ファイル名から
  導出されず固定なので同一 directory に 2 つ目を作れない件、PBS 出力既定の repo 外化、
  attempts root の compute node 可視性検査。
