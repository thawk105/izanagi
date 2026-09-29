---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-30
wave: dev-wave-mocc-validation-fix
seq: 3
---

## 新規

### {{F:bool-define-silently-disables-trace}}. JSON の真偽値を Python の str() で CMake の define へ渡し、`-DTRACE=True` の build が `#if TRACE` を 0 と評価して trace を出さなかった [計測汚染] [恒真ゲート]

- 事象: [T-2872] の修理検証で Codex author が作った使い捨て runner が、arm 定義 JSON の `"trace": true` を `str(arm['trace'])` で `CCBENCH_TRACE=True` にした。CMake はそれを `-DTRACE=True` として compile 命令へ渡し、`#if TRACE` は未定義識別子 `True` を 0 と評価するので、trace 有りのはずの T arm が trace 無しで build された (trace 無しの arm も `-DTRACE=False` で、偶然 0 と同じ意味だった)。smoke 1 回目 (request 36271.nqsv) で trace_*.log が 0 本になり、verifier が rc=2、判定が T の 6 走を判定不能にして `success` false で止まった。runner の selftest 8/8・静的レビュー 2 本はこれを捕まえなかった。
- 根本原因: 起点の runner は arm 定義の `trace` を整数 (1/0) で持っていたが、改作で JSON の真偽値に変わり、define を作る 1 行が型の変化に追随しなかった。build の成功と benchmark の rc=0 は define の値を検査しない。
- 恒久対応: 改作後の runner (job dir `/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/tools/moccfix_probe.py`、sha256 `e70ee41d…`) が build 後・benchmark 前に、対象 TU の実 compile 命令 (compile_commands) の `-DTRACE=` が arm の trace (`1`/`0`) と一致し、計器 define の有無も arm と一致することを確かめ、違えば停止する (fails-closed)。memory `bool-define-stringified-true-disables-if` (trace を有効にした build は compile 命令の `-D` の値を実物で照合してから走らせる)。
- 再発検知: 上の build 後照合と、trace 有り arm の判定を trace の実在 (trace_*.log の本数) に依存させる既存の R0 (判定不能で止まる)。関連: F707 (要求した define が黙って無視される)、F718 (define の値の符号化の衝突)。

## 再発

### F819

- **再発: 2026-09-30** — [T-2872] の修理検証 wave で、親が実装子 B の投げ文に先例 job dir の直下にある `run-build.sh`・`run-judge.sh` を `build/`・`judge/` 配下と書き、子が「読めなければ即停止」で 2 call・40 秒で rc=1 (receipt failure_class=f43_fragment) になった。DW-O01 の「参照 path の実在を先に検査」を親が省いた。投げ文の全絶対 path を抜き出して実在を検査する使い捨て script (job dir `scripts/check_prompt_paths.py`) を通してから B2 として再投入し、以降の投げ文 4 本も同じ検査を通した。
