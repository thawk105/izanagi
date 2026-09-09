---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-10
wave: dev-wave-t2533-t1998-prereg-digest
seq: 2
title: [T-2533] T-1998 の事前登録を実値つきで新設し、consumer の受理条件へ束縛した — 依頼が指した「凍結済みを erratum で直す」は発火せず、親自身の測定値 1 件を実測で訂正した (コード + テスト + docs + insight、branch worktree-dev-wave-t2533-t1998-prereg-digest、変異 8/9 KILLED + 登録 SURVIVED 1・期待 node 完全一致)
---

## 本文

- **依頼文の理由付けが一次資料と矛盾していた。** 「旧 digest のままでは A-5 の別 boot 再取得を
  開始できない (但し書き 3 が外れない)」は、D1525 が「A-5 は Pegasus では充足しない。未充足のまま
  残す」と確定していることと衝突する。後続裁定でも A-5 は再投入しないと決まっている。
  digest を直しても但し書き 3 は外れない。成果物は変わらないので、訂正を明示して本題を進めた。
  本 wave が閉じたのは D1874 が認可した stock-inline 対の事前登録という別の穴である。
- **「凍結済みの事前登録を erratum で直す」も発火しなかった。** repo 内に T-1998 の事前登録は
  存在せず、旧 digest の hit は過去の submit / reservation 記録と insight 逐語だけだった。
  新規作成として作った。
- **親が段 1 で出した target の source digest が誤っていた。** 段 3 のレンズ A が
  「正式 producer は patch 適用下で走るので、その値は producer が記録する値ではない」と指摘し、
  親が `patchharness.applied` の内側で測り直して確定させた。baseline は patch の有無で
  変わらないが (inert 設計)、target は変わる。設計判断は {{D:prereg-source-digest-under-patch}}。
- **段 3 の 2 レンズが独立に、事前登録が consumer の受理集合を束縛していないことを突いた。**
  段 2 の形では、呼び手が結果を見た後に成果物から identity を写して手組みすれば、canonical 文書を
  1 度も読まずに受理へ到達できた。設計判断は {{D:t1998-prereg-binds-consumer}}。
- **D1790 の 2 定数の割り当ても 2 レンズが独立に差し戻した。** 段 1 brief と段 2 plan は
  「成果物側の sha」を job body sha に読み替えていたが、D1790 の逐語はどちらも事前登録文書の
  sha である。成果物が記録する `repository_commit` から測定時点の文書 blob を復元する形で閉じた。
  初版で 2 定数が同値になることは正しく、不等性は要求しない ({{D:t1998-two-pins-equal-in-v1}})。
- **段 6 のレビュー B が挙げた「process 起動 exact 台帳の未登録」を親が実走で確認し、2 failed だった。**
  焦点走の対象集合に `test_ccbench_spawn_sites.py` が入っておらず、`subprocess.run` を足すと
  掛かる層を取り逃がしていた。module 名の grep では出ない。
- **受入 attempt 1 の赤 10 件は変更に帰属しない。** 同じ木で当該 2 file を単独走させると
  `test_t1259_qsub_env_delivery_probe.py` は全件 passed になり、`test_codex_worker_launch.py` は
  別の node が落ちた。失敗 node が走行ごとに入れ替わるので、負荷と並行 codex session に依存する
  赤である。やり直して 22,348 passed / 68 skipped の緑を得た。
- **段 2 の子の出力に、job body digest の壊れた literal が 2 箇所あった** (`…858bilho6f…`、
  `…104485_CTX8b5…`)。子自身が直後に正しい 64 桁を書き直していた。親は現物から機械生成した値の
  正本を job dir へ置き、以後の子へ射影して遮断した。逐語は当時のまま保存し、insight の
  erratum 節に記録した。
- 計算ノードの queue が他 wave で混雑しており、provenance 全監査と変異本走はいずれも
  D612 の opt-in 上書き (3600/600) を使った。1 度目の provenance は上書き無しで queue-wait timeout に
  なり、orphan hold を 2 箇所へ作った。両方消すまで rc=16 が続く。
- 記録は `output/insights/2026-09-10_t2533-t1998-prereg-digest/`。

## 次の一手差分

### 完了

- [T-2533] T-1998 の事前登録を `docs/t1998-balanced-stock-inline-preregistration.md` として新設し、
  実値 (gitlink `511c9538…`、環境契約 digest `e576e9cd…`、job body script digest `dff913cb…`、
  arm 別 source digest `2d691b45…` / `678b7203…`) を固定した。consumer は既存の成果物比較を
  すべて通した後、作業木文書の sha・成果物 commit の文書 blob の sha・その blob 由来 identity の
  3 つを要求する。歴史成果物の digest は書き換えていない。正式測定は起動していない
  (認可は D1874 が既に与えている)。
  remaining: none
  base: a5c5606277230a20efe0c2a7b166544deea556a9bc5bb1f560b2081ca3b1ac6f

### 新規

- {{T:t1998-formal-measurement-submit}} **P2・新規**: T-1998 の正式測定を投入する。
  事前登録は着地済みで、D1874 が認可を与えている。投入は
  `tools/pegasus/submit_t1998_balanced_stock_inline.sh` を 1 回だけ使い、balanced の 1 job を出す。
  成果物が返ったら `consume_balanced_stock_inline_pair` を通し、受理・拒否・inconclusive と
  両 arm の 5 sample・median・`unstable` を報告する。事前登録前に取れた 2026-09-07 の生値を
  混ぜない。**投入は人間手番として残す。**
- {{T:t1998-consumer-entry-point}} **P3・新規**: T-1998 consumer の正式な entry point を決める。
  現状 consumer を通る解析は canonical 文書へ束縛されたが、consumer を呼ばずに数値を主張する
  経路は塞いでいない。production の CLI / submitter へ loader を不可避化するか、
  「consumer を通った解析だけが適格」と明記して閉じるかの裁定が要る。
