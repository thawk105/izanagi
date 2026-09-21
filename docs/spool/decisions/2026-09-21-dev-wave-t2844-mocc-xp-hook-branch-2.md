---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-21
wave: dev-wave-t2844-mocc-xp-hook-branch
seq: 2
---

## {{D:mocc-xp-candidate-mode}}. mocc の pin 候補 commit の正例・負例は既存 driver の候補 mode で旧 6 走を再走し、候補の識別は build 前の停止条件にして check は旧 14 key を変えない

**決定:** mocc の X/P 計装を e9e477ca の単一の子 commit として載せた候補 C の正例・負例は、`orchestrator/campaign/s3_mocc_lock_coverage.py` の候補 mode (`--candidate-oid`) で、旧 driver と同じ 6 走 (stock single / high、lockskip single / high、permutation-erase single、early-unlock single) を C の checkout 上で再走する。
計装 patch は C に重ねず、負例 patch だけを C に直接当てる。TRACE=0 は e9e477ca と C を等長 build dir で比べる。
候補の識別 (commit が指定 OID に解決する、親が e9e477ca ちょうど 1 本、e9e477ca → C の raw diff が `cc/mocc/transaction.cc` の mode 不変な変更 1 行だけ、C の blob が e9e477ca + `patches/instr-mocc-lock-coverage-pin-candidate.patch` の再構成 blob と一致) は、依存物の準備と build より前の fail-closed 停止条件にし、観測値を JSON に記録する。
check は既存 `compute_checks()` の 14 key を無変更で使い、候補固有の check key は足さない。出力は新 path の JSON だけで、旧 JSON 3 本へは書かない。

**理由:**
- 依頼は T-2294 の正例・負例を C 上で取り直すことであり、同じ行列と同じ判定式を使えば旧証拠と同じ命題を C について述べられる。
- 識別を停止条件にすれば、候補の条件を満たさない commit では compute を使わず JSON も作られない。check key にすると all_pass=false の JSON が残るだけで、候補でない commit の測定に計算を使ってしまう。
- 容器を `std::unordered_multiset` に変えたので TRACE=1 の観測負荷は T-2294 と同一でなく、旧 compute 実測は C へ引き継げない (D2207)。
- 他 wave の木の submodule は C の object を持つ保証が無いので、repo の test は e9e477ca + 候補 patch で候補 source を再構成して検査し、C との束縛は driver の git 実測・JSON・親が固定した期待値で持つ。

**却下した選択肢:**
- 段 2 plan の 21 key 案 (候補固有 7 key、hot-update-unlock の正負例 2 走、`objcopy` による `.text` bytes 比較を追加) — hot 経路は mutation proof (T-2757) の命題で依頼の対象外、候補の識別は停止条件で足り、proof-surface の真は stock 正例の certified が含意する。
  `.text` bytes 比較を採らない代わりに、材料では `.text` bytes 一致を主張しない (TRACE=0 の証拠は D297 と、nm / strings / 正規化逆アセンブル一致)。**最も強い反論:** D1687 は補助 witness として `.text` の一致を compute JSON に記録すると書き、T-2294 は bytes 一致を login の別実測で支えていたので、候補には bytes 一致の証拠が無い。採らないのは、T-2294 の compute JSON 自体が正規化逆アセンブル一致を compute 側の witness として記録した先例であり、D1603 の材料 (2) が D297 の結果だからである。
- 新しい driver file を作る — build・condition gate・負例 patch の経路を複製することになり、materializer 登録簿などの追随が増える。
- 候補の source を repo に置かず、test が job dir の bundle を読む、または C を fetch する — 通常の受入の可搬性を満たさない。
