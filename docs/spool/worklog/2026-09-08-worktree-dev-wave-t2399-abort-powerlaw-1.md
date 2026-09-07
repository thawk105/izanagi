---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-08
wave: worktree-dev-wave-t2399-abort-powerlaw
seq: 1
title: [T-2399] 静的 backoff tail の abort 率は単一冪則でなく、-0.5 近傍を生む形は 1 つに絞れない (docs のみ、branch worktree-dev-wave-t2399-abort-powerlaw)
---

## 本文

依頼の前提が実測で覆った wave である。記録済み 8 点格子の再解析だけで閉じ、新規測定はゼロ。
結論と数値は `output/insights/2026-09-08_t2399-abort-powerlaw-mechanism/` にある。

**段 3 の 2 レンズ、段 6 の 2 レンズ、焦点再レビューの計 5 本がすべて NO-GO を返した。
所見は計 32 件、棄却はゼロ。** うち 2 件は主結論を書き換えさせ、8 件は解析 script の
恒真な判定を暴いた。

**敵対レビューが親 brief の数値を 3 件、主張を 2 件訂正した。** 段 2 と段 3 が指摘したのは
局所の傾きの単調性、信頼区間の幅 0 の読み方、変動率の桁である。段 6 が覆したのは
「単調な形ならどれでもよい」という一般化と、記録丸めを伝播しない優劣判定である。

**解析 script は repo へ入れていない** (先行 wave と同じ扱い)。標準出力の逐語だけを insight へ置いた。
親は同一引数で再走し、実装子が申告した標準出力の sha256 と一致することを確認した。

**この job の実行環境では、背景の待ち手 (until ループ、sleep、Monitor) が軒並み即座に戻った。**
Monitor は実体と食い違う完了イベントを 2 回出し、存在しない成果物を byte 数付きで報告した。
最終的に `tail --pid` で producer の終了そのものを待つ形に落ち着いた。
生死判定は毎回 `ps` と成果物の実在で行った。

**親の手順違反 1 件。** heredoc 本文に前後を空白で挟んだ半角スラッシュを書いたところ、
bash guard がそれを filesystem root の path と読んで fails-closed で拒否した。
拒否 message が実際の引き金を示さないため、原因特定に 6 回の試行を要した。

## 次の一手差分

### 完了

- [T-2399] 静的 backoff tail の abort 率の形を再解析し、単一冪則の否定と、-0.5 近傍を生む形が
  1 つに絞れないことを示した。因果は未確定として観測要件を列挙した。
  remaining: none
  base: ea7590fcdff7168781cd82f41878d266c6b67aaa0bf3ef68fa6f8359b89c1c0e
