# 依頼の逐語 (ユーザー起動の `/dev-wave`、2026-09-29 14:18 JST 頃)

```
[T-2853] 再現パッケージ R2 の fig6 単位 (A-2 の取り直し: stock BACK_OFF=0 対 fixed 10 / 5 µs、現行 policy
  5 node) を、現行 repo の paper-story certification driver で Pegasus に測り直す。投入単位は図 1 本 = 1 タスク
  (output/insights/2026-09-27/t2853-repro-rest/README.md §3.3)。計画は
  output/insights/2026-09-23/t2853-figure-rerun-plan/README.md §2.2、元 attempt は t2364-20260907b
  (output/insights/2026-09-07_t2364-paper-story-a2-certification/)。先例は fig8b 単位
  (output/insights/2026-09-28/t2853-r2-fig8b/README.md) で、原 cohort と合成しない別 attempt
  として、表と同じ生成器の図に並べる。試算 1.70 node 時間は暫定なので、投入形を決めた時点で全 job の Elapse
  見積りで判定し直し、2 以上ならユーザー確認後に投入。trace 保全口 (env IZANAGI_TRACE_ARCHIVE_ROOT の opt-in) は
  driver に渡せるなら使う。成果は insight のみ。規律 1・2 は不変。本題だけ。仮想リスク向けの
  gate・検査・台帳・一般化の追加は scope 外。
```
