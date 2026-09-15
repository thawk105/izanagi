---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-15
wave: dev-wave-t2625-sealed-snapshot-qualification
seq: 2
---

## {{D:sealed-write-denial-errno-set}}. 封止 source への書込み拒否は errno 集合で求め、mount-ro は別 witness で要求する

**決定:** 封止した source への書込みが拒否されることを `EROFS` または `EACCES` の受理で求め、
0 (成功) は拒否する。mount が read-only であることは、同じ連言の中の `chmod` が `EROFS` を返すことと
mountinfo の `ro` / `tmpfs` で引き続き要求する。内容不変・`.git` 不在・copy inventory 一致も据え置く。

**理由:**
- 判定後の材料再生成を禁じる既存機構が file と directory の write bit をすべて落とすため、
  `open(O_WRONLY)` は mount の read-only 検査より先に権限検査で拒否される。計算ノードでの実測値は
  `chmod` が `EROFS`、書込みが `EACCES` であった。どちらの機構が先に拒否するかを固定した期待は、
  実装と食い違っていた。
- 所有者の `chmod` は mode bits では拒否されないので、`chmod` の `EROFS` は mount-ro の witness に
  なる。連言のままなので、mode bits だけで守られていて mount-ro が無い状態は依然として赤になる。
  この性質は、その状態を負例として持つテストで守る。
- ただし `EROFS` を mount-ro の**一意な**証明とは扱わない。LSM 等が同じ errno を返す余地は
  排除していない。成立の根拠は連言であって単一の errno ではない。

**却下した選択肢:**
- 書込みの errno を見ない — 書込みが成功しても緑になる。
- `chmod` の条件や mountinfo の条件を外す — mount-ro の witness を失う。
- 封止内で新規 file 作成を試して mount-ro を直接 witness する — directory も write bit を落として
  いるので、その経路も権限検査が先に効く。拒否順序の一般化は実測していない。

## {{D:sealed-snapshot-oracle-contract-id}}. 封止 snapshot の evidence 再導出は準備側と同じ入力を受け取る

**決定:** oracle 束縛 configuration の contract id を、build の呼び出し元から封止 session と
admission を経て evidence の再導出まで通す。既定は未指定で、非 oracle 経路の挙動は変えない。
再導出した token と準備側 token の不一致拒否、および evidence 全体の比較は変更しない。

**理由:**
- 再導出が contract id を受け取らないため、準備側 token と**必ず**食い違い、封止 snapshot は
  oracle 束縛 configuration を一度も通せなかった。計算ノードでの実走で初めて発現した。
- 受け渡しは再導出の入力を準備側と揃えるだけであり、照合が検出する内容差は失われない。
  contract id は内容 digest を置換せず追加する。
- ただしこれは contract id 自体の独立再検証ではない。同じ値を両側へ渡すので、contract id の
  正当性は準備側の契約一致と oracle の PASS 要求が担う。この限界は成果物へ明記する。

**却下した選択肢:**
- token 照合を外す・緩める — 内容差を拒否する性質を失う。
- 準備側から contract id を落として合わせる — 準備側の identity を弱める。
- oracle 束縛 configuration を qualification から外す — 正式受入の前提が「閉じないことを正式に
  受理する」を却下しており、除外したまま完了扱いにはできない。
