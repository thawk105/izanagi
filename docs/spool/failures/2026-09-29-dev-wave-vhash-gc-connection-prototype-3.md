---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-29
wave: dev-wave-vhash-gc-connection-prototype
seq: 3
---

## 新規

### {{F:model-refs-vs-implicit-floor}}. 小モデルで安全な公開手順を C++ へ写すとき、モデルの版ごとの参照集合に当たる保護が実装では「tx 開始時の下限を変えない」暗黙の不変条件だったことを見落とし、待機中に既読版を回収させた [誤前提] [手順漏れ]

- 事象: VHash 構成 E の段 4 で、親の仮裁定 P5 が「安全点で ThreadRtsArray を最新の MinWts−1 へ上げる (stock と同じ意味の値で、下げないので安全)」とした。段 3 の相談 2 本と段 6 のレビュー 2 本・焦点再レビューはこの点を反例にしなかった。計算ノードの smoke 4 で、待機の前後の既読版の照合 (保持版検査) が E-hb 159 / 3,938、E 174 / 3,882 の変化を出した。
- 根本原因: md_10 の小モデルは既読版を版ごとの refs で守り、回収境界 (gc_floor) は cand_ts そのものだった。Cicada には refs が無く、既読版を守っているのは「ThreadRtsArray = tx 開始時の MinWts−1 を tx の間変えない」ことである。親は「下限を下げない」(tx 境界の単調性) だけを検討し、「tx の途中で上げる」ことが暗黙の保護を外すと考えなかった。モデルの規則の対応表 (G1〜G7) に、実装側で何がその規則の前提 (refs) を担うかの列が無かった。
- 恒久対応: 下限は前進に成功したときだけ t′−1 へ公開し、それ以外は変えない ({{D:vhash-gc-connection-prototype}})。保持版検査を計器 build に常設し、smoke・本計測・検査の全 run で 0 を確かめる形にした (`patches/cicada-forwarding-gc.patch` の `CICADA_GC_COUNT`、driver の `held_changed`、検査起動器の終了コード)。一次資料 §3.3 に経緯。
- 再発検知: 保持版検査 (待機中の既読版の wts・status の変化) が 0 でない run を、検査起動器が非 0 で終える。モデルの規則を実装へ写す wave では、規則ごとに「モデルでその前提を担う状態」と「実装でそれを担うもの」を対にして段 1 の brief に書く (本 F を段 1 の攻撃面に含める)。

## 再発

### F683

- **再発: 2026-09-29** — VHash 構成 E の計算ノード smoke が、gate 前の dependency build 抜け (1 回目)、`#line` のずれ (2 回目)、計器なし build の未使用引数 (3 回目) と 1 回に 1 件ずつ止まった。3 回目の後に「build 行列の全 macro の組で -Werror の構文検査を実 header で通す」を fix 子に課し、4 回目で通った。検査起動器も dependency build 抜けで 1 回空振りし、2 回目は driver の成功経路と 1 段ずつ突き合わせさせて通した (その突き合わせで genome が旧定義だったのも見つかった)。
