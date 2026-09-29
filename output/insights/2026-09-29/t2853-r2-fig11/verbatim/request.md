# 依頼の逐語 (2026-09-29 JST、/dev-wave 引数)

[T-2853] 再現パッケージ R2 の fig11 単位 (A-6 read-heavy fixed 2 µs、現行 policy 5 node) を、現行 repo の
  paper-story certification driver で Pegasus に測り直す。投入単位は図 1 本 = 1 タスク
  (output/insights/2026-09-27/t2853-repro-rest/README.md §3.3)。計画は
  output/insights/2026-09-23/t2853-figure-rerun-plan/README.md §2.2、元 attempt は a6-20260908b
  (output/insights/2026-09-08_t2411-paper-story-a6-certification/、結果稿
  docs/paper-story/results/2026-09-18-a6-certification-reject.md)。先例は fig8b 単位
  (output/insights/2026-09-28/t2853-r2-fig8b/README.md) で、原 cohort と合成しない別 attempt
  として、表と同じ生成器の図に並べる。試算 1.69 node 時間は暫定なので、投入形を決めた時点で全 job の Elapse
  見積りで判定し直し、2 以上ならユーザー確認後に投入。trace 保全口は driver に渡せるなら使う。fig6 の wave
  と並走するので submit checkout と出力先は分ける。成果は insight のみ。規律 1・2 は不変。本題だけ。仮想リスク向けの
  gate・検査・台帳・一般化の追加は scope 外。
