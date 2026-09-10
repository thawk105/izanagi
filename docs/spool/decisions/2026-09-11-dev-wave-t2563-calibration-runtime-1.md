---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-11
wave: dev-wave-t2563-calibration-runtime
seq: 1
---

## {{D:calibration-runtime-no-adoption}}. 認定較正は要求時間増加を既定解とせず、実時間の短縮を示せないコピー並行化を撤回する

**ユーザー裁定:** 今回の指示はD1936項38の「必要分の要求時間増加」を既定解とする方針を変更する。
要求時間・timeout・標本数は本waveで変更しない。正しさ検証・単独性・trace/perf分離・標本設計を
維持した最小変更だけを検討し、短縮効果を示せなければ実装を残さない。

**実測と採否:** mocc/rr50/t48をbefore991694、3copy並行化候補after991727で各1回測定した。
両方accepted、scheduler186→182秒。未変更configureですでに3秒差があり、copy周辺の粗い区間は
両方1秒だった。別ノード各1回であり、4秒差をcopy並行化へ帰属できないため候補を全撤回する。
これは効果ゼロの証明ではない。追加測定・新規基盤・gflagsのリンク先変更へ広げない。

**時間式:** 最終構成は既存逐次処理で、旧時間式の不整合は未解決。
timeout上限の部分和を実所要と扱わず、実測186秒やouter timeoutで最大経路の包含を証明したとも
扱わない。要求時間増加へ戻さず、時間式再凍結を完了扱いにしない。

**出所:** `output/insights/2026-09-11/t2563-calibration-runtime/README.md` とbefore/afterの一次資料。
