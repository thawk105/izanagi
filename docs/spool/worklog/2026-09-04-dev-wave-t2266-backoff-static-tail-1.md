---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-04
wave: dev-wave-t2266-backoff-static-tail
seq: 1
title: [T-2266] 静的 tail の依頼の前提が実測で覆り、残る欠測は 1 点だけだった — 測る機構は入れたが測定はまだ走っていない (コード + テスト + docs + insight、branch worktree-dev-wave-t2266-backoff-static-tail、変異 9/9 KILLED)
---

## 本文

- **依頼の前提が誤りだった。** 依頼と T-2216 材料文書 §5 は「b > 100 µs の静的 `T(b)` は
  1 点も測っていない」を前提にしていたが、**B-10 拡張格子が 2026-08-26 に b = 0〜900 µs の
  有効 28 点を 3 workload 分すべて 1 job 内・trace-disabled で完走させていた**
  (job 951689 / 951690 / 951691)。依頼の 6 点のうち 150 / 200 / 300 / 500 は
  依頼どおりの条件で既に測られている。材料文書 §5 を訂正した。
- **真に未測定なのは 750 の 1 点だけで、1000 は測定不能だった。**
  `patches/silo-backoff-fixed.patch` の合成枝は値を単一量として扱わず、
  商をモード選択・剰余を振幅に使う。1000 は商 1・振幅 0 で**厳密に 0 µs へ復号される** (F718)。
  この符号化では静的値の上限が 999 µs であり、**「静的 1000 µs」は原理的に表現できない。**
  親が patch の現物で 4 分岐を読み、3 workload すべてで 1000 の行が 0 の行と一致することを
  数値で確かめた。既存の binary 同一性検査は別 binary になるので通過する。
- **親の当初の裁定が誤りで、段 3 が突き返した。** 親は「既存データで目的は閉じるので
  0 job で済む」へ傾いたが、レーン B が **real: 依頼は測定行為を要求しており scope の縮小である**
  と判定した。レーン A も独立に、歩行 model の完全再計算は**有効な 901〜1000 µs の点と
  rep 単位 abort 率が無いため判定不能**と述べた。2 レーンが別々の理由で「測ることに実体がある」へ
  到達したので、親は自分の傾きを捨てて測る側へ裁定し直した。
- **今回の測定の主目的の一つは rep 単位の abort 率である。** 既存 `.dat` は
  throughput が 5 rep 中央値、**abort 率が中央値 rep 1 本の代表値**で、
  model の再計算に要る rep 単位 abort が失われていた。この集約規則は段 3 レーン A が実測で確定した。
- **段 6 の敵対レビューが must-fix 4 件を出し、うち 1 件は規律 2 に触れた。**
  非認証の trace-disabled 測定値へ無限定の `certified: true` を付けていた。
  他は (a) `none` と `adaptive` が binary 同一性検査から漏れる (b) abort 率が rep identity を持たず
  呼出順で結合され切り詰めもある (c) rep 保存テストが producer と WAL consumer を両方迂回し、
  事前登録した変異でも緑のままになる。**もう 1 レーンは所見ゼロだったので変異で裏取りした。**
- **既存の凍結 pin が生きていることを変異で確かめた。** 既存 `EXTENDED_SWEEP_US` の上端を
  999 に変える変異が既存テスト 3 件を赤にした。これは実装を守るためではなく、
  「既存格子は書き換えられない」という本 wave の主張の根拠が空でないことの確認である。
- **登録簿は触っていない。** 稼働 wave t2189 との編集面重複は `admission_registry.json` 1 file
  だったが、登録簿は path を鍵にするため既登録 path の内容変更では更新不要と実測で確定し、
  既存 B-10 grid の job body と submitter へ run kind を足す形にした。**衝突は発生していない。**
  停止中の B-10 正式走は別の job body (`b10_backoff_shape_campaign.sh`) を使うことも確認した。
- **子は pytest を 1 件も走らせられなかった。** 実装子・fix 子とも計算ノードの
  queue 拒否 (`qstat -Q preflight rc=1`、dispatcher rc=16) で、テストの実測はすべて親が行った。
- **焦点走が 1 度 rc=16 で落ちたが、これは赤ではなく queue-wait-timeout だった**
  (`child_started: false`)。orphan hold 2 file を job 不在確認後に撤去し、
  D612 の opt-in 上書き (queue 待ち 3600 秒 / grace 600 秒) で通した。
  この上書きが無いと混雑時に焦点走が成立しない。
- **測定はまだ走っていない。** 本 wave が入れたのは測る機構だけで、
  成果物の数値はすべて既存測定の再解析である。投入は land 後。
- 成果物はすべて**非認証**である。trace-disabled の性能測定で直列性の検査を通していない。
  variant 採用の根拠には使えない (規律 2)。

## 次の一手差分

### 更新

- [T-2266] **P1・測定投入待ち**: 静的 tail を測る opt-in mode を既存 B-10 経路へ着地させた。
  `tools/pegasus/submit_b10_backoff_grid.sh --run-kind t2266-tail --output-parent <絶対 path>`
  で 3 workload が 3 job として同時に出る。格子は `none` + `adaptive` + 固定
  {150, 200, 300, 500, 750, 999} の exact 8 点。**依頼の 1000 µs は F718 の符号化により
  測定不能なので、999 で代替しても「6 点完了」とは書かない。**
  得られるのは 750 の初測定、表現可能上限 999 の初測定、既測 4 点の同一 job 内での測り直し、
  適応側の谷との同一 job 内比較、そして**全 rep の throughput と abort 率**である。
  材料は `output/insights/2026-09-04_t2266-backoff-static-tail/README.md`。
  base: 68db043d6f195a42b4b01ba565ac7b643aa82c1be2ee1fd415bd2006c0fb0437

### 新規

- {{T:backoff-fixed-encoding-upper-bound}} **P2・新規**: 静的 backoff の符号化が
  商をモード選択に使うため、**静的値の上限が 999 µs に固定されている**。
  1000 µs 以上の静的点は原理的に測れない。符号化を直すか格子の上端を 999 に固定するかは
  変異軸の設計判断であり、B-10 の待ち方 campaign が同じ wire
  (`constant` / `symmetric-modulo` / `binary`) を使うため影響が及ぶ。
  F718 が別 wave へ送った事項を、上限の実体つきで再掲する。
- {{T:t2266-tail-model-rerun}} **P2・新規**: [T-2266] の測定が揃ったら、
  実測 tail と rep 単位 abort 率で `tools/t2216_backoff_walk_model.py` を再走する。
  補間規則を**結果を見る前に**固定する。旧 model の指数外挿は tail を大きく過小評価しており
  (500 µs で 3.04 倍、900 µs で 13.21 倍)、滞在重み固定の単純混合では寄与が
  最大 +0.037 M tps に留まって否定的結論は覆らない見込みだが、
  滞在分布自体が変わるため完全な予測方向は未確定である。
