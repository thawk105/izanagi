### 実測済み α と本番案は別の取得プロトコル

**場所**: [tools/pegasus/probes/t419_probe_causality.py:34](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/tools/pegasus/probes/t419_probe_causality.py:34)、[tools/pegasus/probes/t419_probe_causality.py:301](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/tools/pegasus/probes/t419_probe_causality.py:301)、[tools/pegasus/probes/t419_probe_causality.py:3006](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/tools/pegasus/probes/t419_probe_causality.py:3006)、[tools/pegasus/probes/t419_probe_causality.py:4012](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/tools/pegasus/probes/t419_probe_causality.py:4012)

**なぜ危険か**: 9/9 を得た α は、48 CPU の randomized pin sweep から連続する 5 target の各先頭 primary read を採る。各 target には discarded anchor と 50 ms deadline 付き read 列がある。本番案は固定した等間隔 5 target を間隔保証なしで一度ずつ読むため、target、anchor、時間窓が全部違う。例えば 150 ms の上向き burst は集中した 5 読みを全滅させて誤拒否し、遅い下向き変動は短い静穏窓だけ読めば誤受理し得る。login 実演も最小後に 1 CPU 帯外で、canonical pass の実演ではない。

**成果物影響**: 再較正後の受理集合、材料レポートの環境一致、試行台帳の採否が、9/9 の根拠を持たない別プロトコルで変わる。

**提案**: target 規則、anchor、開始間隔、全体 horizon、lateness の扱いを方式契約と identity に含める。実験手続きをそのまま移すか、提案中の本番手続きを bnode で別途検証するまで 9/9 を妥当性根拠に使わない。

### `method` は K 回取得の証拠にならない

**場所**: [orchestrator/calibrator/schema_v2.py:243](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/calibrator/schema_v2.py:243)、[orchestrator/campaign/env_attestation.py:519](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/env_attestation.py:519)、[orchestrator/campaign/env_attestation.py:623](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/env_attestation.py:623)、[tools/pegasus/run_probe.py:53](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/tools/pegasus/run_probe.py:53)

**なぜ危険か**: outward schema に残るのは最小値、`method`、governor だけで、K snapshots、pin target、pre/post CPU、時刻は消える。単読みを K 回複製した実装、cache した vector、例外時の直接 `_parse_cpuinfo()` fallback でも、同じ最小値と method を作れば成果物上は正規 α と区別できない。開発時 unit test は、実際に発行された probe・較正が K 回取得したことの事後証拠にはならない。一次資料の「schema (K 回保持)」を P2 は未裁定のまま落としている。

**成果物影響**: certified 選択・材料レポート・試行台帳が、実質単読みの profile を α として参照し、誤った受理集合を監査不能な形で固定し得る。

**提案**: P2 は明示裁定へ戻す。採るなら versioned acquisition transcript を probe output、hash projection、較正 receipt に束縛する。schema を広げない裁定なら、少なくとも「α の実行証拠を満たした」「U-2 条件が完全成立した」とは扱わない。

### affinity mask の一致は観測者効果の復元ではない

**場所**: [orchestrator/campaign/env_attestation.py:404](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/env_attestation.py:404)、[orchestrator/campaign/env_attestation.py:435](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/env_attestation.py:435)、[orchestrator/calibrator/cli.py:527](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/calibrator/cli.py:527)、[orchestrator/campaign/s8b_oracle_driver.py:934](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/s8b_oracle_driver.py:934)

**なぜ危険か**: broad affinity を戻しても、thread は最後の target CPU に残り得る。P-state、cache、温度も戻らない。さらに restore syscall が失敗した場合、`AttestationError` にはなるが thread は最後の singleton に残るため、「必ず復元」は成立しない。oracle は各行直前、calibrator は測定前後に probe するので、決定的な同じ 5 CPU を毎回暖めた状態が後続測定へ逆流し得る。TSC を α の後に置く順序も fake TSC テストでは観測されない。

**成果物影響**: throughput が target CPU の暖機・配置に依存し、certified 選択、材料レポートの性能値、試行台帳の測定値が系統的に歪み得る。

**提案**: affinity mutation は短命な helper process に隔離し、親 process の mask を変更しない。併せて post-probe carry-over の ablation、必要な settle 契約、TSC との順序を方式 identity に固定する。

### `/proc/self/stat` は pin した thread を見ていない

**場所**: [tools/pegasus/probes/t419_probe_causality.py:1768](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/tools/pegasus/probes/t419_probe_causality.py:1768)、[orchestrator/campaign/execution_guard.py:319](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/execution_guard.py:319)

**なぜ危険か**: Linux の `sched_setaffinity(0, ...)` は calling thread に作用する一方、`/proc/self/stat` は thread-group leader の stat である。worker thread から probe すると、pin した thread と別 task の processor を検査して誤拒否する。逆に leader が偶然 target にいると、壊れた pin 検査へ偽の裏付けを与える。他 thread は自由に走れるため、同一 process の追加 busy CPU も α の前提外である。

**成果物影響**: 呼出 thread により同じ環境の受理可否が変わり、profile、拒否記録、再取得 attempt の再現性が壊れる。

**提案**: `/proc/thread-self/stat` または `/proc/self/task/<native_tid>/stat` を使う。worker-thread test と、default Linux runtime の parser testを追加する。単一 thread 前提なら明示的に検査する。

### pin 不発の重要経路がテストから抜けている

**場所**: [orchestrator/tests/test_env_attestation.py:67](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/tests/test_env_attestation.py:67)、[orchestrator/campaign/env_attestation.py:404](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/env_attestation.py:404)

**なぜ危険か**: プランの負例は set の `OSError` と wrong processor だが、「set は成功を返す、affinity は broad または別 singleton のまま、processor seam だけ target を返す」がない。fake が requested target を内部状態へ写して `current_processor()` でも返すと、検査自身が常に真になる。exact `get_affinity()=={target}` を削る変異が生存し、K 回が同じ CPU または非 pin で行われても最小値だけで通り得る。

**成果物影響**: 単読み相当の観測が新 method で受理され、再較正後の certified 受理集合が広がる。

**提案**: set 成功後も affinity が変わらず、processor は target を返す直交 fixture を追加し、cpuinfo read 0 回・復元完了まで assert する。pre、post、mask の三検査は別々の変異にする。

### 変異の赤が別の fail-closed 層で作れてしまう

**場所**: [orchestrator/campaign/env_attestation.py:211](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/env_attestation.py:211)、[docs/failures.md:2425](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/docs/failures.md:2425)、[docs/failures.md:2811](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/docs/failures.md:2811)

**なぜ危険か**: setaffinity-error test が runtime の read 数だけを見る場合、禁止された fallback が直接 `_parse_cpuinfo(path)` を呼べばカウンタを迂回できる。さらに fake の restore も同じ `OSError` なら、fallback 後も restore 層で赤くなりテストは通る。CPU 集合検査も collector、reducer、呼出側へ重ねる案なので、一層だけ削る変異は別層に mask される。F107/F126 と同型で、KILLED は受理集合変化への帰属にならない。

**成果物影響**: 変異台帳が偽の KILLED を記録し、単読み fallback や検査委譲欠落を監査済みとして後続の certified chain へ渡す。

**提案**: singleton set だけ一度失敗させ、元 affinity の restore は成功させる。runtime と直接 parser の双方を spy にし、fallback があれば実際に profile が返るところまで fixture を閉じる。CPU 集合 drift は reducer の純関数 test、public→collector の委譲は専用 spy testへ再照準する。

### `min` は一過性を一般には吸収しない

**場所**: [tools/pegasus/probes/t419_probe_causality.py:203](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/tools/pegasus/probes/t419_probe_causality.py:203)、[orchestrator/campaign/env_attestation.py:721](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/env_attestation.py:721)

**なぜ危険か**: 1 CPU の 5 値が `[3000,3000,2101,3000,3000]` なら、時間の大半が帯外でも最小 2101 で受理される。反対に `[2101,2101,1800,2101,2101]` は一度だけの下向き glitch が最小へ固定され誤拒否される。従って「一過性を吸収」「持続的な劣化は残す」は上向き値かつ全 K 回という限定付きであり、無時間契約では「持続的」の長さも定義されない。提案テストは 3000 MHz 側しか扱わない。

**成果物影響**: 高値が 4/5 の環境を受理し、低値が 1/5 の環境を拒否するため、certified 選択と試行台帳の環境判定が非対称に変わる。

**提案**: 4/5 高値と 1/5 低値を固定するテストを追加し、この性質を仕様として明記する。対称な transient 耐性を要求するなら α 自体の再裁定が必要で、本 wave で述語を変えない。

### 親 brief の拒否理由と login 一般化は成立しない

**場所**: [output/insights/2026-08-04_t419-probe-causality/ruling-package.md:110](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/output/insights/2026-08-04_t419-probe-causality/ruling-package.md:110)、[orchestrator/campaign/execution_guard.py:347](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/execution_guard.py:347)、[orchestrator/campaign/execution_guard.py:358](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/execution_guard.py:358)

**なぜ危険か**: method mismatch は probe が profile を返した後にだけ発生する。pin、K、restore が失敗すれば先に `strict attestation probe failed` になる。成功しても login 実演どおり sample が残れば method と samples の両方が failure list に入るため、「拒否理由が method 不一致へ変わる」は偽である。また 96 CPU login の正常系 pin・20 ms は、48 CPU batch cpuset、失敗経路、固定 target 手続きの根拠にならない。一次資料自身も bnode138 exact config 以外へ一般化していない。330 件の method-only 緑は既存被覆の欠落だけを示し、実装妥当性は示さない。

**成果物影響**: certified 受理集合は当面空のままでも、材料・試行側の拒否種別、failure list、参照先は brief の宣言どおりにならない。

**提案**: 成果物影響を「受理集合は閉鎖維持。拒否は acquisition failure または method を含む複数比較 failure」に訂正する。bnode では提案そのものの手続きと復元を別途確認する。

## 総括

最も危険なのは、実装予定の固定・集中読みが 9/9 を得た α と別物なのに、その差を method identityにも runtime 証拠にも残さない組合せである。これでは単読み退化だけでなく、未検証の時間窓まで α として認証される。

親 brief には、P2 の method-only 証拠、P3 の固定等間隔 5 点、P4 の `/proc/self/stat` をいずれも反対する。login 実演は機構の存在しか示さず、canonical pass、bnode 手続き、復元失敗、所要時間の一般化には使えない。

**判定: NO-GO。** 段 5 前に、取得時系列の version 化、thread 正規 stat、affinity mutation の隔離、P2 の明示裁定、単一理由の変異再照準が必要である。本所見は read-only の静的レビューであり、テストの緑・赤は実測していない。