---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-30
wave: worktree-dev-wave-vhash-workload-space
seq: 1
title: VHash md_29 (md_28 を統合): 提案が Cicada に勝てる負荷の範囲を、計器で 126 点 × 2 genome × 2 反復にふるい分け、第 2 段の候補 4 領域を登録した規則で選んだ (branch worktree-dev-wave-vhash-workload-space)
---

## 本文

- 依頼: `/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_29.txt` (md_28 を含む)。一次資料 `output/insights/2026-09-30/vhash-workload-space/README.md`、設計判断 {{D:vhash-workload-space-stage2-regions}}、失敗の再発 F139。
- 結論 (一次資料 §0): 長い read-only tx を 1 worker が続ける条件 (batchR) の 84 行すべてで stock Cicada の MinRts 公開が 0 回、生存版は record の 5.4〜14.5 倍 (層 S)。長い tx が無ければ最良設定の境界年齢は 128〜512 µs と小さく、既定の H4 は既定の公開の遅さを含む。H2 (前進) は全域で小さく (h2 最大 0.046)、偏りを上げると深い read は増えるが候補の割合が下がる。候補は規則どおり 5 個 (実質 4 領域、3 つが batchR)。計器入り build の値で、性能・正しさの主張はしない。
- 手順の事前登録: 点の選び方・述語・候補の選び方を一次資料 §1 に書いて計測の投入前に commit した (4449cd02a)。段 6 の指摘で H4 の順位の付け方を計測前に明記 (6ee05af4e)。縮小 (§1.6) は所要 probe の実測で不要と判定。
- 棄却・限定した所見: 段 6 の S6-2 (driver の smoke に W 条件の所要測定が無い) は refuted (smoke + 所要 probe の 2 job で親が満たした)。焦点再レビュー 2 の「3 反復以上で反復別の列が欠ける」は 2 反復の本 wave に影響しないので nit (一次資料 §7)。段 3 の「abort 理由の細分類は重い」は refuted (md_28 が理由を要求)。
- 期待値の訂正 1 件: 作図器の test で、この wave の前回 fix が足した K=4 の候補率の期待値 (分母 10000・率 .005) を登録定義 (位置 ≥ K の update read、500・.1) へ親の裁定で訂正した (fix 子は既存期待値の規則どおり停止してから、許可を受けて直した)。
- セッション異常: (1) 開始時に job artifact dir と handoff を harness 既定の home (`$CLAUDE_JOB_DIR/tmp`) に作り、段 2 の後で `/work/SFC/tanab/tmp/vhash-workload-space-2026-09-30/` へ移した (開始 gate の log は home の handoff path を記録)。(2) 実装子 A の初回が model call 上限 100 で打ち切られ、途中 commit から続きを出した。(3) fix 子に sandbox で `git checkout` を指示し無変更停止、残った空の index.lock で次の子の起動器の終端 commit が失敗 → 親が占有 0 件を確かめて lock を消し、残差を `.sh` 経由で commit した。(4) 計算ノード smoke が 2 回空振り (gate の件数 pin、compile error、F139 の再発)。(5) 変異の `--plan-only` が container の削除で Lustre の EINTR、`--resume` も rc=125 → 親が container を削除して自分の登録 1 件だけ prune。変異本走の wrapper は共有木の観測で rc=125 (child_rc=0、結果は有効)。(6) 受入 1 回目 (child-green) の後、land の PREP で main を前方 merge したら、main 側の condition gate の site 数総和 pin が本 wave の VLIFE 増分を含まず赤 (文字の競合 0 件、F1079 と同型の積の取りこぼし)。手で直さず abort し、同じ file を変えた lock-order-axis の着地を待って main を 1 回取り込み、Codex が総和 pin を数え直した (298) merge で受入を取り直した。
- 子の工数: Codex plan 1・相談 1・author 3・fix 8・review 2・焦点再レビュー 2 (内訳は一次資料 §9)。
- 計算ノード: smoke 3 回 271 s、所要 probe 336 s、本計測 6 job 2,453 s (6 台に同時分割)、変異本走 445 s、合計 3,505 s (約 0.97 node 時間)。受入全走は別。

## 次の一手差分

### 新規

- {{T:vhash-workload-stage2}} **P2・新規**: VHash の「提案が Cicada に勝てる負荷」の第 2 段。{{D:vhash-workload-space-stage2-regions}} の候補 4 領域 ((a) 読み比率 5%・長い read-only tx、(b) read-only 指定率 95%・thread 12、(c) 読み比率 5%・長い read-only・skew 0.9〜0.97、(d) 長い read-only・read-only 指定率 0%) で、機構 (hot 配置 B・前進 C・GC 接続 E・区間 GC・read-only commit の公開) を md_11 の最良設定の Cicada と同時刻対照で直接比べる。(d) は比較相手に ro-gcflag を入れるかの確認 ([T-2933]) の結果を待つか両方を並べる。根拠: `output/insights/2026-09-30/vhash-workload-space/README.md` §0・§4・§10。
