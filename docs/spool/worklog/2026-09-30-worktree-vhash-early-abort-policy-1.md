---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-30
wave: worktree-vhash-early-abort-policy
seq: 1
title: [T-2930] VHash md_31: commit できないと確定した長い tx を待機の安全点で早く abort させる方策を E-max と比べた。早期 abort だけでは回収境界はほとんど縮まず、前進を試して前進できず確定したときだけ abort する組み合わせ (c) が skew 0.9 / 0.95 で E-max より遅れを 2.9 / 4.1 ms 縮めた (patch + driver + 小モデル + insight、branch worktree-vhash-early-abort-policy)
---

## 本文

- 依頼: `/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_31.txt` (一次資料 `output/insights/2026-09-30/vhash-early-abort-policy/README.md`、設計判断 {{D:vhash-early-abort-policy}}、失敗の再発 F273・F722)。
- 結論 (一次資料 §1): 判定 D (既読版より新しく自分の ts より古い committed / deleted の版) は小モデルの有限範囲で健全。方策 b (早期 abort のみ) の回収境界の遅れは E-hb とほぼ同じ (skew 0.9 で 20.4 → 19.6 ms)、方策 c (E-max + `no_room` のとき D で abort) は E-max より skew 0.9 で 19.6 → 15.2 ms、0.95 で 20.3 → 16.0 ms。skew 0.9 では長い tx の試行の約 43〜46% で待機中に commit できないことが確定し、その検出の大半は待機開始から 128〜255 µs の bin に入る。待機型の長い tx は stock でも完了する (md_21 の完了率 0.0003 以下は操作数型の値)。BACK_OFF=1 は完了率を上げる方向だが throughput は 0.29 倍 (記述値)。正しさ検査 8 run で巡回 0 (上限 indeterminate)。
- md_21 §4.3 の訂正: `no_room` を成功前 / 成功後に分けると大半は成功後の再要求で、`no_room` は定義上も abort の確定ではない。
- 棄却・限定した所見: 段 6 レビュー A・B の「早期 abort が GC flag の設定を飛ばす」は refuted (直後の `tx.abort()` の `mainte()` が stock と同じ条件で flag を立てる。違いは診断計数 flag_raises だけ)。段 3 相談 A の「C++ 側の制御可能な shadow 検査」は採らず、実機の shadow 照合を健全性の証拠に数えないことにした (壊した判定は実機で到達しなかった)。レビュー A の「小モデルの read が aborted を飛ばさない」は、子の実測で修正前も同義だった (分岐の明示とテストだけ追加)。レビュー B の「abort 理由別の計数が無い」は限界として一次資料に書いた。
- 実機でだけ出た欠陥 3 件 (smoke 1 の依存物 build 抜け、smoke 2 の `-Werror` 未使用変数、検査 1 の起動器の照合範囲) は F722 の再発として記録。
- 親の操作ミス: 全史 provenance 監査と焦点走 2 を同一 worktree から並行 dispatch し orphan hold で監査が rc=16 (F273 の再発、損害なし、単独で再投入して rc=0)。
- 子の工数: Codex plan 1・相談 2・author 4 (小モデル・patch・driver・repo 外検査起動器)・review 2・fix 4 (fix1 の 3 本・fix2 の 1 本)・焦点再レビュー 1・作図 1。
- 計算ノード: 合計 2,703 s (約 0.75 node 時間、受入全走を除く)。内訳は一次資料 §12。本計測の 6 ノードは計測中に他の request (md_18・md_29 を含む) と同居していない。受入全走は local main を取り込んだ tip で行う。

## 次の一手差分

### 完了

- [T-2930] 構成 E の安全点で commit できないと確定した長い tx を早く abort させる方策 (b・c) を E-max と比べ、`no_room` を成功前 / 成功後に分ける計数も足した ({{D:vhash-early-abort-policy}}、一次資料 `output/insights/2026-09-30/vhash-early-abort-policy/README.md`)。
  remaining: none
  base: 7f07b1a95bd34a908aa817837c2ca7a2553c035d2253486d5482d7b7292d6eae

### 新規

- {{T:vhash-longtx-failure-breakdown}} **P2・新規**: VHash の待機型の長い tx について、失敗の内訳 (待機前半の既読の上書き・待機後半の上書き・書き込み制約・書き込み時の EarlyAborts) を計数し、完了率の rep の揺れ (skew 0.9 で 0.006〜0.216) を 3 秒より長い走行と rep の追加で絞る。md_31 では D の到達 (試行の約 43〜46%) しか分からず、前進 (E) と BACK_OFF の完了率への効果は判定できなかった。根拠: `output/insights/2026-09-30/vhash-early-abort-policy/README.md` §5.3・§6。
- {{T:vhash-early-abort-manyops}} **P3・新規**: 操作数型 (1,000 操作) の長い tx に安全点を置き、判定 D による早期 abort と前進 (E-max) の組み合わせ (方策 c) が操作数型でも回収境界を縮めるかを確かめる。md_31 の安全点は待機型の待機 slice にしかなく、md_21 で完了率 0.0003 以下だった操作数型は測れていない。根拠: 同 §6・§10。
