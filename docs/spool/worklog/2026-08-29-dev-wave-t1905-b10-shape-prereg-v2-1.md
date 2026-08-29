---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-29
wave: dev-wave-t1905-b10-shape-prereg-v2
seq: 1
title: [T-1905] B-10 待ち方 grid の事前登録を probe 開示のうえ v4 へ再設計した (docs + code + tests、branch worktree-dev-wave-t1905-b10-shape-prereg-v2、変異 12/12 KILLED)
---

## 本文

- ユーザー裁定により、codex が「再設計が残るため除外」とした T-1905 を本 wave で着手した。
  設計を固めること自体が AI の作業である、という裁定に従う。実測投入は行わない。
- 上限 1.0% exclusive は据え置いた。cell 単位の免除・警告化・flag・環境変数のいずれも作っていない。
  形の登録可否は記号導出の基準へ寄せた ({{D:b10-shape-eligibility-symbolic-criterion}})。
- D1057 の「撹拌器が全単射だから最上位 bit は半々」は反証していない。無効になったのは
  有限な実行時 start 列への転用だけである ({{D:b10-binary-premise-scope-correction}})。
  probe は最上位 bit の出現数を記録しておらず `p` を測っていないため、
  binary の平均超過の原因を bit の偏りに帰属させていない。
- binary を外した判断は事前登録ではなく probe を見た後の改訂である。文書は
  「観測済みの事実」「事後改訂」「前向きに固定した規則」の 3 段順で書いた。
- D1270 の「新しい日付版」は、D1058 が固定した canonical path 上の新しい版として作った
  ({{D:b10-preregistration-new-version-at-pinned-path}})。**この読み方はユーザー確認を経ていない。**
  別 path の日付入り file を望む場合は差し戻しになる。
- 親が書いた v4 初版に誤りがあり、自分で検出して訂正した。`external_floor_reference_widths` を
  object から flat list へ作り替え、登録済みの `terminology` と `reference_width_pct`
  (1.9 / 3.0 / 0.62) を落としていた。新旧 spec の構造比較で検出し v3 と同一へ戻した。
  段 5 実装子は誤った文書に忠実に追随していたため fix 子でコード側も戻した。
- 段 3 敵対相談は real 11 件 (レンズ A) と 6 件 (レンズ B)。親 brief の「一次で不変」
  「12 対 / 3 族」は誤りと確定し、正しくは symmetric-modulo も p に一次で、
  Holm は 18 対 / 3 族、residual だけ 12 cell である。
- 段 6 敵対レビューの must-fix 3 件を fix 子で閉じた。provenance が key 集合しか閉じていない、
  prior block record から binary が report へ再流入できる、変異 M7 が前段 mask で殺せていない、
  の 3 件。恒真な test 1 件も実体を呼ぶ形へ直した。
- 変異の期待 node は推測せず、全件 SURVIVED 期待の probe 走で観測した完全集合を焼き込んだ。
- 段 5 実装子と 2 本の fix 子はいずれも pytest を実走できていない。計算ノードの
  dispatch 直列制約により親が全走を担った。子の非実走は緑と記録していない。
- 正式投入 (build / verify / perf)、probe の再走、折り返し二値の実装、push は行っていない。
- 一次資料は `output/insights/2026-08-29_t1905-b10-prereg-v2/`。

## 次の一手差分

### 更新

- [T-1905] **P1・事前登録 v4 が発効 → 正式投入待ち**: 上限 1.0% を据え置いたまま 2 形 grid
  (`constant` / `symmetric-modulo`) で発効した。登録 12 cell の最大絶対偏差 0.5616942857142844%。
  probe の再走は不要。次は発効版 commit を指した build / verify / perf の正式投入である。
  base: b25ef577b775c4dacac72b67a5814fa80d69be55bae9ae0def8914873d9dd8cb

### 新規

- {{T:b10-folded-binary-ladder}} **P2・新規**: 3 水準 ladder を回復する折り返し二値の設計を
  事前登録 §9 に記録した。formula と patch の SHA が変わるため、D1098 / D1281 に従って
  旧 formula の消費者を別名で凍結し、新しい placeholder を凍結してから物理残差 probe を
  走らせ直す別 wave が要る。採否はユーザー裁定へ送る。
- {{T:b10-in-situ-residual-diagnosis}} **P3・新規**: 合成ループではなく本走中の要求待ち量分布と
  実待機時間を測る診断。規律 1 の trace 分離により別 build・別 run が要る。
  現状の物理残差は合成ループの `start` 列しか覆っていない。
