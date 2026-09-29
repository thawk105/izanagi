---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-29
wave: dev-wave-vhash-cicada-rts-check
seq: 1
title: [T-2882] Cicada の書き込み側 rts 検査に、VHash 小モデル v0 の穴 (PENDING の直前版で検査を打ち切る) は無いと、原論文と CCBench の実装と小モデルの探索で確かめた (insight のみ、branch worktree-dev-wave-vhash-cicada-rts-check)
---

## 本文

- 依頼: 並行 VHash wave の md_8 (`/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_8.txt`)。比較相手 Cicada の正しさに関わるので最優先とされた。
- 正本: `output/insights/2026-09-29/vhash-cicada-rts-check/README.md`。内容は、原論文と CCBench (gitlink 68106660) の対応表、食い違いの出所、小モデルでの確認、確かめたこと・確かめていないこと。
- 結論の要点:
  - CCBench の最終書き込み検査 (`cc/cicada/transaction.cc:576-593`) は、PENDING を確定まで待ち、ABORTED を飛ばしてから、確定版の rts を見る。原論文 (§3.2・§3.4 (b)・付録 A 定義 1) も同じである。
  - v0 の規則は、md_4 のモデルが書き込み検査の対象を独自に決めたものだった。出典メモ §4 は「PENDING は待つ」と書いている。
  - md_8 項 2 の実 Cicada 再現走行は、発火条件「同じ形を持つなら」が成立しないので行っていない。
- repo 外の probe の結果 (`/work/SFC/tanab/tmp/vhash-cicada-rts-check-2026-09-29/probe_vc.py`、md_4 のモデルを import のみ):
  - v0 / v1 の値は md_4 の表と全行一致した。
  - forwarding なしの v0 でも S8 の閉路は同形で出た。
  - 待ちを入れた vC / vCnf は、10 場面で閉路・GC 違反・deadlock が 0 だった。
  - S8 の窓から到達した 12 終端は、「P 確定・T abort・W 確定」と「P abort・T 確定・W abort」の 2 種類だけで、T と W の両 commit の到達状態は 0 だった (固定場面の有界モデル内)。
- 段 3 相談 2 本 (レンズ: 正しさ境界 / 実効性・過剰・削除): 中心結論を覆す所見はなかった。次の所見はすべて文言・限界の明記として採用した。
  - 付録 A 補題 2 は読み側の根拠
  - DELETED は失敗扱い
  - 「メモと無関係」は言い過ぎ
  - vC の一般化の限定
  - 延べ数の呼び方
  - 窓から abort への因果の提示
- 相談 A の「C++ の記憶模型上の相互見落とし (store-buffer 形)」は、v0 とは別の形で要検証である。x86 の実行環境での到達は親の推定では無い。一次資料の「確かめていないこと」に記録し、起票しなかった (DW-S04)。
- 記録前の独立 read-only レビュー 2 本 (事実照合 / 過大主張・過剰・削除): must-fix は 2 件。
  - W が確定する側で T が待つ相手は、P:A でなく W:A だった。
  - 「必ず」の範囲が、固定 S8 モデルの到達状態を超えて読めた。
  - 両方とも直した。W が確定する側の説明は推測で書かず、解析に両決着の最短列を足して実際の列から書き直した。
  - should-fix 7 件も直した (一次資料 §9)。
  - 修正後の焦点再レビュー 1 本では、全所見が closed、新しい must-fix はなかった。should-fix 2 件 (件数の数え違い、precheck の INSERT 除外の記述) も直した。
- セッション異常 (親の作法、実害なし): 相談 2 本の待ち手を重複して張り、即座に止めた (DW-C00 の 1 条件 1 本)。
- エージェント工数: Codex plan 1・consult 2・review 2・focus 1 (gpt-6-sol / medium)。計算ノードは 0 (probe は Pegasus login で合計 47 秒)。

## 次の一手差分

### 完了

- [T-2882] Cicada の書き込み側 rts 検査が v0 反例と同じ形を持たないことを、原論文と CCBench の実装で確かめ、実物のどの手順が穴を塞ぐか (PENDING の確定を待つ) とモデルの前提との食い違いを一次資料に記録した。同じ形を持たないので、再現走行は発火しなかった。
  remaining: none
  base: 7b16f2ef2c7fa723d3a3ff4dae4a261c43f43ab6b12f12c4ee8ca2fc14fd1aec
