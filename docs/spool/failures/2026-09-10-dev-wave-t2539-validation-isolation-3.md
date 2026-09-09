---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-10
wave: dev-wave-t2539-validation-isolation
seq: 3
---

## 再発

### F688

- **再発: 2026-09-10** — 抵触した作業は段 7 の記録そのものだった。変異本走を投入した直後、
  待機時間で insight 一次資料 (`output/insights/<date>_<task>/` の逐語と変異 spec) を配置し、
  harness が untracked 16 件を検出して `rc=2` で中止した。insight を repo 外へ退避して
  走らせ直し `rc=0` で完走した。**入口の「待機中は独立な解析・検証・合成・文書を進める」は、
  段 7 の記録作業に適用すると `DW-M05` と必ず衝突する** — 記録の成果物は repo 内 path を
  持つからである。F688 の恒久対応「変異投入の直前に、待機中に行う作業を repo 外への
  書き込みだけと宣言してから投入する」は正しく、守らなかったのが原因である。
  変異走行中に進めてよい記録作業は、job directory 側の handoff と、repo 外に置く下書きだけ。
