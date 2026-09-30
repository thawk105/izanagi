---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-30
wave: worktree-dev-wave-vhash-workload-space
seq: 3
---

## {{D:vhash-workload-space-stage2-regions}}. VHash の「提案が Cicada に勝てる負荷」の第 2 段は、長い read-only tx を含む 4 領域で機構を最良設定の Cicada と直接比べる

**決定:**
1. 負荷の空間のふるい分け (一次資料 `output/insights/2026-09-30/vhash-workload-space/README.md`、126 点 × 2 genome × 2 反復) の結果、
   第 2 段 (機構を比較相手と直接比べる別 wave) の候補領域を、事前登録した規則 (同 §1.5) が選んだ次の 4 つとする:
   (a) 読み比率 5%・長い read-only tx (batchR)、(b) read-only 指定率 95%・thread 12、(c) 読み比率 5%・batchR・skew 0.9〜0.97、
   (d) batchR・read-only 指定率 0%。確かめる機構の割当と現実の用途との対応は同 §4。
2. 第 2 段の比較相手は md_11 の観測最良設定 (D2302) とし、既定設定の値を伸びしろの根拠にしない。長い tx が無い条件では、
   H4-lag (境界年齢 p50 ≥ 1,024 µs) の通過が層 S で既定 46 行・最良 3 行と大きく違い、既定の伸びしろは既定の GC 公開の遅さを含むためである。
3. batchR の H4 の値は stock Cicada の read-only commit の欠陥 (md_22) を含む。比較相手に ro-gcflag 修正を入れるか (ユーザー確認待ち) で
   第 2 段の H4 の相手が変わるので、第 2 段は両方の比較相手を並べるか、確認の結果を待ってから (d) を測る。

**理由:**
- 4 領域のうち 3 つが batchR を含み、batchR の 84 行すべてで MinRts の公開が 0 回、論理生存版数は record の 5.4〜14.5 倍 (層 S) だった。
  長い read-only tx は現実の用途 (分析 query・閉じない cursor・一貫 dump) に対応し、先行研究も GC の停止として扱っている。
- H2 (前進) は全域で小さく (h2 最大 0.046)、偏りを上げても深い update read のうち候補がある割合が下がるので、単独の主条件にしない。

**却下した選択肢:**
- 既定設定を相手に伸びしろの大きい領域を選ぶ — 既定は最良より 2〜4.5 倍遅く (md_11)、審査で意味が無い。
- 規則を満たさなかった「最良設定だけで u1 ≥ 0.05」の高偏り領域を候補に加える — 登録した規則 (両 genome) を結果を見て変えることになる。
  最良設定だけの近い領域として一次資料 §4 に記録するに留める。
