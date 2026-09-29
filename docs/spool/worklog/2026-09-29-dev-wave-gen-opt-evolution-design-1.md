---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-29
wave: dev-wave-gen-opt-evolution-design
seq: 1
title: 母集団型の探索の枠組みの設計 — 既存の方策 loop の上に母集団の層を足す差分 (世代同期の多系列 + 外側の親選択) を段階導入で推奨し、ShinkaEvolve の「直接採用ゼロ」を今の前提で再判定し、比較・費用・用語の条件を一次資料にした (docs のみ、計算なし、branch dev-wave-gen-opt-evolution-design)
---

## 本文

- 依頼: 並行 gen-opt wave の md_4 (`/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_4.txt`、共通指示は同 dir の `common.txt`)。依頼の冒頭の「前提の訂正」(09:4x JST 追記) は、ユーザーの指摘「すでに進化探索ループの枠組みはできてるよね？」を受けて親セッションが足したもので、枠組みを一から設計せず既存ループへの差分に絞るよう求めた。親セッションからも同じ内容の連絡を受けた。
- 台帳に「母集団型の探索の枠組みの設計」を含む item は無かった。本 wave が設計を届けるので、完了済みの item を新たに立てず、このエントリで記録し、後続の実装を新規 item として起票した。探索の本走そのものの item は md_1 の wave (gen-opt-roadmap-revision) が起票する。
- 一次資料: `output/insights/2026-09-29/gen-opt-evolution-design/README.md`。推奨は段階導入 (先に独立 K 系列 = 案 A を回せる状態にし、世代同期の多系列 + 外側の親選択 = 案 B の 3 部品を足し、案 B を探索本走に採るかは ablation E1・E2 の結果で決める)。本エントリは採用の決定ではなく、採否は探索本走の確認のときにユーザーが決める。
- 新事実 (実測): 方策 pair の候補 1 本の評価 434〜491 秒の約 9 割は性能構成の検査 5 本 (直列)。検査 1 本の区間は観測した 3 組では trace の commit 数と同じ向き (性能構成の検査 20 本の各値で 100 万 commit あたり約 36〜40 秒) で、abort を含む取引数とは対応しない。方策 driver の campaign 設定には同時検査の key が無い。出所は [T-2871] の生死確認系列の WAL (一次資料 §6.1)。
- 確かめていないこと: Shinka の 62 技法の個別の判定 (2026-07-07 の記録は session 内だけで repo に無い)、方策軸の balanced・read-heavy の単価、同じ submit checkout から別系列の pair job を同時に流せるか、既存記録での順位の再現性、LLM の週上限で回せる機会数。
- 軽量版 (docs-only): 段 2・3 は省いた。段 6 の read-only review 2 本 (レンズ A: 一次資料との事実照合 / レンズ B: 設計の択一と規律) はどちらも NO-GO で、所見 13 件 (must-fix 9・should 4) をすべて real として直した。主なもの: 検査時間が取引数に比例するという誤り (2 本目の候補で反証)、Shinka の理由の数え違い (D9 を深掘りの理由に数えた)、選択の寄与を分ける ablation (E2) の欠落、選ばれなかった系列の失格理由が次の生成へ届かない設計、二段評価が正しさの信号を減らすこと (推奨から外した)、費用表に endpoint の再計測が無いこと、推奨が案 A との比較より用語の達成を優先していたこと。焦点再レビュー 1 本は 12 件 closed・1 件 partial と新所見 2 件 (検査の秒数の範囲を狭く書いた、カードを渡さない LLM 対 機械の比較も入力が揃わないのに LLM 固有の寄与の対照と呼んだ) で、親が WAL で検算し roadmap §1 と照合して直した。逐語と裁定は一次資料の `verbatim/`。
- エージェント工数: Explore 子 1 (sonnet、既存部品の棚卸し)、Codex review 2・focus 1 (gpt-6-sol / medium)。計算ノードの job は投げていない (受入全走を除く)。
- セッション異常: EnterWorktree の name 形が filter driver の設定読み取りエラーで失敗し、手動の worktree add (並行 wave と同時で約 16 分) の後に path 形で入った。

## 次の一手差分

### 新規

- {{T:population-layer-impl}} **P3・新規**: 母集団型の探索の枠組みの設計 (本エントリ、一次資料 `output/insights/2026-09-29/gen-opt-evolution-design/README.md`) を段階導入で実装し、生死確認する。前提は [T-2867] の実装 (方策 driver の系列ごとの campaign identity と停止規則の切り離し、機械生成 IR の口、G_rand と (1+1) の生成器、系列制御と起動器、LLM の round tool) の着地で、作り直さずに再利用する。手順は (1) 既存記録での順位の再現性 (一次資料 §5.4 手順 0、計算なし)、(2) 規模 S の生死確認 (1 島・K = 3・2 世代、換算 1.56〜1.68 node 時間、別系列の pair job の同時投入の独立性を含む)、(3) 選択器・親の系譜と前世代の結果の口・世代の起動器・report (一次資料 §8 の N1〜N3・N5・N6、Codex author)、(4) 方策 driver への同時検査の key (§5.4 手順 1)。用語を得る ablation (E0〜E2 の 4 構成 × 10 run、endpoint 込みで換算 235〜253 node 時間、同時検査で 120〜152) と探索の本走はユーザー確認の後で、案 B を本走に採るかは E1・E2 の結果で決める。実装の検査と合わせて 1 タスク合計 2 node 時間以上なら見積りを添えてユーザーに確認する。優先度は親の暫定。
