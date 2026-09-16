---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-16
wave: dev-wave-t2634-nonsilo-floor-lift
seq: 2
---

## {{D:nonsilo-within-run-floor-lift}}. 非 silo の within-run floor は既取得の較正 4 対に限って文書登録し、between-run の実測は D1373 の関門を維持したまま未実施と記録する

**決定:** D2044 項 12 (非 silo の within-run floor の保留を、実測で示された protocol と workload に限って
解除する) を次のとおり実装する。

1. 解除の対象は、accepted な認定較正 record が存在する 4 対 — tictoc / rr50・rr95、mocc / rr50・rr95 —
   に限る。登録する量は各 record の `noise_floor` (1 セッション内 reps=10 の throughput の変動係数) で
   あり、性能比較の値でも、D1639 が「床値」と呼ぶ between-run noise floor でもない。
2. 登録先は現行 phase doc の 8b 節とし、silo の rr95 / rr5 の accepted 較正と同じ形 (record の path、
   request、node、records、採用点 LLC miss、within-run CV) で書く。値は insight の散文ではなく record
   自身の `saturation.miss_rate_at` と `noise_floor.cv` から取る。環境契約の世代 registry
   (`orchestrator/campaign/env_contract.py`) は変えない — これは世代ごとに 1 件の較正を契約値へ束縛する
   pin であって、較正の一覧ではない。
3. この登録は文書上の解除である。層 3 report の within-run 候補は `calibration/` 直下の glob と契約 pin の
   和集合だけで `registered/` を走査しない (D1508) ので、登録によって 4 件が report へ流入するようには
   ならない。silo の rr95 / rr5 も同じ状態にあり、登録の水準はそれと揃う。report へ接続するには契約世代の
   登録・活性化と、その契約を持つ campaign が別に要る。本決定はそれを行わない。
4. 依頼が名指した between-run floor の実測 (`orchestrator/campaign/between_run_floor.py --protocol
   {tictoc,mocc}`) は行わない。現行 CCBench pin `511c9538` の checkout で、tictoc は driver の
   `BASELINES` に無く引数解析で拒否され、mocc は `_protocol_source_has_trace_hook_evidence_only` が
   偽を返し `main()` が build 前に拒否する。この関門は D1373 が「規律 2 の関門」と定めたものであり、
   迂回も緩和もしない。親が login node で実測したのは述語の値 (silo=True、mocc=False、tictoc=False)・
   `BASELINES` の鍵集合・引数解析の 3 点で、driver の rc=2 と `ValueError` は実装から導いた静的帰結である。
   関門は checkout の source text だけを読むので計算ノードでも同じ判定になるが、計算ノードで実走して
   確かめてはいない。
5. between-run 実測の再開に必要な条件を必要条件として記す。mocc は、実際に checkout される
   `cc/mocc/CMakeLists.txt` の SOURCES に列挙された同一 file に `trace.hh` の include・`#if TRACE`・
   `izanagi_trace::` 呼出しの 3 証拠が (コメントと literal `#if 0` を除いて) 揃う pin へ進むこと。
   現行の hook は submodule branch `izanagi-t1943-mocc-g2-readfrom-witness` にあり pin の祖先ではない。
   tictoc はそれに加えて hook 自体の移植 (現行 phase doc 段 7 Group B) と driver の baseline 対応が要る。
   いずれも関門を通る条件であって、測定の成功や verifier の通過を保証しない。
6. 変えないもの: D1373 の関門、`orchestrator/tests/test_between_run_floor.py` の期待値、CCBench pin、
   既存の較正 record 8 件と `between_run_noise_*.json` の bytes、非 silo の rr5・cicada・silo の状態語。
   `BASELINES` へ tictoc を足すことも行わない — 足しても関門で止まり測定は開通せず、今回の登録に要らない。

**理由:**
- D2044 項 12 は「実証されていない組へ保証を広げない」ために範囲を 4 対に限った。登録の根拠はこの明示的な
  用途限定の解除であり、「較正の変動係数は D1360 の禁止対象ではなかった」という読み替えには置かない。
  D1360 は stock 専用計測経路の値を公式 report にも入れないと定めており、その一般解除は行っていない。
- D1373 は判定を固定の許可リストでなく source の事実へ束縛した。pin が進んで hook が checkout に
  現れれば判定は自動的に変わる。関門を触らずに待つのが設計どおりである。
- accepted な較正は trace 分離検査 (binary に `izanagi_trace` が無い) を通っているが、それは正しさ検証の
  通過ではない。登録に「certified」「検証済み」の語を付けない。

**却下した選択肢:**
- 全 protocol・全 workload の保留を一括解除する — 実証されていない組へ保証を広げる。
- 較正の within-run CV を between-run floor の代わりに使う — 別の量であり、D19 / D1639 が塞いだ経路。
- D1373 の関門を緩める、または pin を本 wave で進めて測る — 前者は規律 2 の弱体化、後者は凍結成果物が
  束縛する pin の変更で本 wave の範囲を超える。
- `BASELINES` へ tictoc を先に足しておく — 関門で止まるので測定は開通せず、今回の登録にも寄与しない。
- 4 件を層 3 report へ接続するため契約世代を登録する — 依頼の範囲外で、登録・活性化・campaign の設計を
  伴う別の変更単位。
