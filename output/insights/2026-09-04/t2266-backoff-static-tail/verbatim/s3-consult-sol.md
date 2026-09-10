## 命題 1 — 同一ビルド・同一 job

**所見: real（同一の pin・toolchain・build 手順・job 環境） / refuted（同一 binary）。**

- 29 個の静的点は `none`、`adaptive` と合わせた 31 genome として一度に列挙されます。[backoff_extended_sweep.py:282](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/orchestrator/campaign/backoff_extended_sweep.py:282)
- job body は workload ごとに driver を一度だけ起動します。[b10_backoff_grid.sh:570](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/tools/pegasus/b10_backoff_grid.sh:570) 実 WAL も各 workload について `build_start`、`bench_done`、`commit` が各 31 件あり、29 静的点は各 workload の同一 job 内で測定されています。
- build cache は job ごとに一つです。[b10_backoff_grid.sh:252](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/tools/pegasus/b10_backoff_grid.sh:252) ただし workload 間では共有されません。
- 同一 binary ではありません。各 genome を `trace=True/False` の二種類で事前 build し、静的値ごとの perf binary SHA が異なることを明示的に要求しています。[backoff_extended_sweep.py:197](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/orchestrator/campaign/backoff_extended_sweep.py:197) [backoff_extended_sweep.py:165](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/orchestrator/campaign/backoff_extended_sweep.py:165) 実 WAL でも各 job の 31 perf binary はすべて別 SHA でした。
- 満たすのは「同一 CCBench pin、patch、compiler/toolchain、Release 設定、trace-disabled 設定、job-local cache を使い、意図した `BACKOFF_FIXED` だけを変えた build」という意味です。`BACKOFF_FIXED` は compile-time macro なので、完全に同じ build 設定でもありません。
- 3 workload は job 951689、951690、951691 の別 job です。submitter 自体が 1 workload = 1 job と定義しています。[submit_b10_backoff_grid.sh:87](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/tools/pegasus/submit_b10_backoff_grid.sh:87) [submit_b10_backoff_grid.sh:163](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/tools/pegasus/submit_b10_backoff_grid.sh:163)
- 依頼は同時に「条件を割って複数ノードへ投入」と要求しているため、整合的な解釈は「各 workload 内では全 b を同じ allocation で比較し、workload は別 job」です。workload を跨いだ単一 job を要求すると読むなら refuted です。

したがって、親の「4 点は依頼どおり」は、同一 binary まで含意する表現としては不正確ですが、性能比較で通常必要な同一 build protocol・同一 workload job という意味では成立します。

## 命題 2 — 測定の意味

**所見: real。ただし abort 率は 5 rep 集約値ではありません。**

- `throughput_tps` の定義は CCBench の `throughput[tps]`、すなわち commits/sec です。欠損時だけ `commit_counts_ / actual_extime` へフォールバックします。[benchparse.py:53](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/orchestrator/calibrator/benchparse.py:53)
- `abort_rate` は `aborts / (commits + aborts)` です。CCBench の直接出力を優先し、欠損時に生カウントから再計算します。[benchparse.py:66](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/orchestrator/calibrator/benchparse.py:66)
- 条件は 1,000,000 records、48 threads、3 秒、5 rep です。[p2_2.py:53](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/orchestrator/campaign/p2_2.py:53) driver がそのまま `PerfConfig` に渡します。[backoff_extended_sweep.py:385](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/orchestrator/campaign/backoff_extended_sweep.py:385)
- `.dat` の `throughput_tps` は5個の生 TPSの中央値です。[analyze.py:208](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/orchestrator/calibrator/analyze.py:208) [backoff_extended_sweep_report.py:503](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/orchestrator/campaign/backoff_extended_sweep_report.py:503)
- `.dat` の `abort_rate` と `latency_ns` は平均でも中央値でもありません。TPS が中央値に最も近い代表 1 rep から取ります。[runner.py:1254](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/orchestrator/calibrator/runner.py:1254)
- `cv` は同じ採用 round の5 TPSについて、標本標準偏差を平均で割った値です。[analyze.py:220](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/orchestrator/calibrator/analyze.py:220) 5%を超えると最大3 roundまで再測定します。[stability.py:58](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/orchestrator/calibrator/stability.py:58)
- 実 WAL では全 3 job・全 31 点が `reps=5`、`rounds=1`、`unstable=false`。全格子の最大 CV は write-heavy 3.08%、balanced 3.19%、read-heavy 1.18%で、5% gate 内です。
- 依頼済み4点だけなら最大 CV は write-heavy 0.262%、balanced 0.313%、read-heavy 0.168%で、TPS の測定品質は良好です。

よって静的 `T(b)` と abort 率という量自体は要求と一致します。ただし CV は TPS の within-round ばらつきだけで、abort 率の誤差、独立 session 間ドリフト、信頼区間は表しません。「abort 率も n=5 で集約済み」と解釈するならその部分は refuted です。

## 命題 3 — 1000 と 999 の符号化

**所見: real。親と段 2 の読解は正しいです。**

符号化の実体は [silo-backoff-fixed.patch:69](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/patches/silo-backoff-fixed.patch:69) の合成枝です。主要な逐語部分は次です。

```cpp
(static_cast<uint64_t>(BACKOFF_FIXED) / 1000ULL == 0ULL)
    ? static_cast<double>(BACKOFF_FIXED)
    : ((static_cast<uint64_t>(BACKOFF_FIXED) / 1000ULL == 1ULL)
       ? static_cast<double>(
           (static_cast<uint64_t>(BACKOFF_FIXED) % 1000ULL) + ...
         ) / 2.0
       : ...)
```

- `999 / 1000 == 0` なので第1枝に入り、`now_backoff = 999.0`。固定 999 µs は表現できます。
- `1000 / 1000 == 1`、`1000 % 1000 == 0`。mode 1 の中心・振幅・剰余演算がすべて 0 となり、`now_backoff = 0.0`。現在の入力符号化で固定 1000 µs は測れません。
- `.dat` の比較は次のとおりです。

| workload | T(0) | 表示 T(1000) | TPS差 | abort(0) | abort(1000) | abort差 |
|---|---:|---:|---:|---:|---:|---:|
| write-heavy | 2,361,787 | 2,386,090 | +1.029% | 0.7896 | 0.7847 | -0.0049 |
| balanced | 3,850,119 | 3,829,076 | -0.547% | 0.6775 | 0.6783 | +0.0008 |
| read-heavy | 10,219,045 | 10,233,974 | +0.146% | 0.1536 | 0.1539 | +0.0003 |

すべて対応する CV の範囲内で、3 workload とも 0 µs と同一域です。これは符号化仮説と強く整合します。`1000` 行は独立な固定 0 反復であり、真の `T(1000)` ではありません。

## 命題 4 — 測定の鮮度

**所見: real。2026-08-26 の歴史的な trace-disabled 静的測定として現在も使用できます。**

絶対規律 7 は、現行コードとの差だけで過去測定を無効にしてはならないと明記しています。[CLAUDE.md:97](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/CLAUDE.md:97)

実測した無効化条件の状況は次のとおりです。

- 証拠コピー3件の SHA-256 は、元 `.dat` および各 `completion.json` の記録と完全一致しました。成果物破損は成立していません。
- 3 job は repository commit `78c7a2c1408da05c9c6391451192d81963b84034`、CCBench `511c9538e4e8efa54b45cda62e72389ed3b706ec` に束縛されています。
- 現行 `pin.CURRENT_PIN` も `511c953` のままです。[pin.py:28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/orchestrator/campaign/pin.py:28)
- 測定 commit と現行 HEAD で `patches/silo-backoff-fixed.patch`、`benchparse.py`、`p2_2.py`、noise/CV処理、report の bytesまたは測定定数は不変でした。
- driver には後日 condition gate が追加され、pipeline には refactor がありますが、これだけでは過去の観測事実を無効化しません。現在のコードを再実行した性能値そのものだと主張しない限り問題ありません。

使えなくなる条件は、成果物の SHA 不一致、測定 source binding の欠落、対象とする符号化・workload・動作点の意味変更、または現行性能そのものを主張する場合です。今回、前3条件は成立していません。現行性能の厳密な数値を主張するなら再測定が必要ですが、それは過去測定の無効化とは別です。

## 命題 5 — 目的が閉じるか

**所見: real（tail 存在と谷の絶対値） / refuted（指定6点と機序の完全閉鎖） / 判定不能（tail 差替え後の完全な歩行 model）。**

既存28有効点で閉じる部分は明確です。

- T-2216 §5 の「b > 100 µs は1点も未測定」は実測が否定します。[mechanism.md:200](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/output/insights/2026-09-02_t2216-adaptive-backoff-nonmonotonicity-mechanism.md:200)
- write-heavy は 560 µs で 1,252,136 TPS、600 µs で 1,218,351 TPSです。適応側の谷 1,241,671 TPSを両側から挟むため、「谷に届く静的 tail が存在する」は外挿なしで閉じます。
- 750 の欠測はこの存在証明を崩しません。700、800、900 µsまで滑らかに低下しています。

閉じ残る部分もあります。

- `T(750)` とその abort 率。
- 真の固定 `T(1000)` と abort 率。現符号化では測定不能です。
- 動的 `Backoff_` の滞在分布、遷移損失、スレッド同調、履歴依存、leader 固有 abort、窓内 commit 分布。
- §4-bis の混合仮定そのもの。静的 tail は「動的に b にいる時も固定 b と同じ性能」という仮定を検証しません。[mechanism.md:180](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/output/insights/2026-09-02_t2216-adaptive-backoff-nonmonotonicity-mechanism.md:180)

tail 差替えの定量的な向きは、滞在重みを固定した単純混合なら上向きです。

| b | 旧指数外挿 T | B-10 実測 T | 比 |
|---:|---:|---:|---:|
| 150 | 1.902 M | 2.048 M | 1.08倍 |
| 200 | 1.538 M | 1.849 M | 1.20倍 |
| 500 | 0.429 M | 1.305 M | 3.04倍 |
| 900 | 0.078 M | 1.035 M | 13.21倍 |

刻み25 µsの旧 model は `P(Backoff > 100)=3.8%`です。[mechanism.md:169](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/output/insights/2026-09-02_t2216-adaptive-backoff-nonmonotonicity-mechanism.md:169) 150〜900 µsでの最大差は約0.964 M TPSなので、滞在重み固定かつ未測定 900超を除けば、tail 差替えの寄与は最大でも約 `0.038 × 0.964 M = 0.037 M TPS`。旧予測 2.860 Mを観測 1.242 Mへ近づけず、わずかに上げる方向です。

一方、完全な model 予測は判定不能です。T と abort 率は leader 周期と遷移確率にも入るため、差替え後は滞在分布自体が変わります。[t2216_backoff_walk_model.py:365](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2266-backoff-static-tail/tools/t2216_backoff_walk_model.py:365) また有効な 901〜1000 µs 曲線、特に model が到達可能な 1000 µs が欠けています。

決着に必要な測定: 有効な 999または符号化修正後の1000を含む一貫した静的曲線と rep 単位 abort 率を取得し、補間規則を固定して歩行 model を再実行する。

## 段 2 プランへの所見

- **欠落:** [s2-plan.md:7](/work/1/SFC/tanab/dev-wave-artifacts/t2266-backoff-static-tail/s2-plan.md:7) は単一 build cache だけを挙げ、全静的点が別 binaryであることを明示していません。「同一ビルド」の検算としては不十分です。
- **欠落:** [s2-plan.md:8](/work/1/SFC/tanab/dev-wave-artifacts/t2266-backoff-static-tail/s2-plan.md:8) と [s2-plan.md:69](/work/1/SFC/tanab/dev-wave-artifacts/t2266-backoff-static-tail/s2-plan.md:69) は `.dat` の TPS が5 rep中央値、abort率が代表1 repであることを記していません。
- **集約不一致:** [s2-plan.md:69](/work/1/SFC/tanab/dev-wave-artifacts/t2266-backoff-static-tail/s2-plan.md:69) は、生値平均で較正した T-2216 model と B-10 の `.dat` 中央値を直接比較しています。差は既測4点で最大0.14%と小さく結論は変わりませんが、正式な再解析では WAL の生 TPSを平均へ再集約すべきです。
- **欠落:** [s2-plan.md:70](/work/1/SFC/tanab/dev-wave-artifacts/t2266-backoff-static-tail/s2-plan.md:70) は非線形性には触れていますが、完全な model 再計算に有効な 901〜1000 µs 曲線が足りないことを明記していません。
- **欠落:** [s2-plan.md:85](/work/1/SFC/tanab/dev-wave-artifacts/t2266-backoff-static-tail/s2-plan.md:85) の既存 pipeline 流用では、abort率の全 rep は保存されません。新規測定を選ぶなら、代表1 repという定義を明示するか、rep単位値を保存する必要があります。
- **表現の過大さ:** [s2-plan.md:105](/work/1/SFC/tanab/dev-wave-artifacts/t2266-backoff-static-tail/s2-plan.md:105) の「科学的な tail の空白は閉じた」は、tail の存在と谷の絶対値については正しい一方、混合仮定と機序までは閉じません。同文書の63行目の留保を結論にも残すべきです。
- 999の符号化、新規 driver不要という B-10 opt-in 案、registry を回避する判断には、計測妥当性の観点から明白な誤りはありません。

## 総括

- 親の「既測4点」は、各 workload 内の同一 job・同一 pin/toolchain/build protocolという意味では real。
- 同一 binaryという意味では refuted。各 b は compile-time macro が異なる別 binaryである。
- 3 workload は別 job・別 node・別 cacheであり、比較単位は workload 内である。
- `.dat` の TPS は5 rep中央値、abort率はTPS中央値に対応する代表1 rep、CVはTPSの標本 CV。
- 既測4点の CV は最大0.313%で、TPS測定は安定している。
- 1000は固定0へ復号され、999は固定999として表現可能。3 workloadの0/1000実測もこれを支持する。
- 過去成果物の SHA、pin、patch、metric 定義は保たれ、測定鮮度を無効にする条件は成立していない。
- 既存 tail は静的曲線が適応側の谷まで低下する事実を閉じるが、750、真の1000、動的機序は閉じない。
- 固定滞在重みなら実測 tail は model 予測を上げ、谷の再現をさらに悪化させる。
- 滞在分布まで再計算した完全な予測方向は、999/1000と rep単位 abort 曲線がないため判定不能。
- pytestおよび新規性能測定は実行していない。以上は既存成果物の再計算と静的検査による結論である。