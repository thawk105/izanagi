### A-1

**主張:** A1/A0 の「帯外集合が当該 CPU を含む」という判定は、pin の限界効果を測っておらず、因果確認条件になっていない。

**攻撃対象:** A1、A0、P1、事前登録の「48/48 かつ 30/30 で CONFIRMED」。

**具体的な失敗シナリオ:** package-wide turbo や `/proc/cpuinfo` 読み取りが全 CPU に起こすサンプリング処理によって、毎回多数または全 CPU が帯外になれば、pin 先 `c` と A0 の self CPU は自動的に集合へ含まれる。pin を別 CPU へ移しても各 CPU の帯外確率が一切変わらない世界で、現基準は CONFIRMED を返す。これは現実的な偽陽性である。

**強度:** **強い**。判定式そのものから導ける反例であり、機械固有の仮定を要しない。

**最小の是正案:** 既存 A1 の各 48 要素を使い、CPU `i` ごとに `pin=i` のときと `pin≠i` のときの帯外率・MHz 差を比較する paired contrast を事前登録する。pin 順はランダム化し、無処置時の基礎帯外率も条件に入れる。240 読みを増やす必要はなく、分析と順序だけの変更で済む。

### A-2

**主張:** A1 の R=5 と A0 の30回は、APERF/MPERF のキャッシュと測定時間窓を束縛しない限り独立反復ではなく、一件のキャッシュ値を複製する危険がある。

**攻撃対象:** A0、A1、A3、P1、P3、1件でも外れれば REFUTED とする基準。

**具体的な失敗シナリオ:** upstream v5.15 では `/proc/cpuinfo` の open 時に全 CPU の準備処理が走り、`arch_freq_get_on_cpu` は APERF/MPERF 差分を短時間キャッシュする。[v5.15 cpuinfo open](https://kernel.googlesource.com/pub/scm/linux/kernel/git/stable/linux-stable.git/+/refs/tags/v5.15/fs/proc/cpuinfo.c)・[v5.15 APERF/MPERF 実装](https://kernel.googlesource.com/pub/scm/linux/kernel/git/stable/linux-stable.git/+/refs/tags/v5.15/arch/x86/kernel/cpu/aperfmperf.c)。pin 直前に作られた値が再利用されれば、実際には pin 効果があっても `c` が帯外にならず REFUTED になる。逆に5回が同一キャッシュなら、5/5 は再現性の証拠ではない。最初の一回だけ stale-refresh 経路へ入り、その後だけ挙動が違う可能性もある。

**強度:** **強い**。カーネル実装上の既知の時間依存であり、brief は間隔も初回処理も指定していない。

**最小の是正案:** 各 affinity 条件の最初の読みを APERF/MPERF の基準点として破棄し、処置を保持したまま実 kernel に対応する固定間隔を置いて次を判定対象にする。upstream v5.15 相当と確認できれば50 ms程度で十分保守的で、全240回へ入れても約12秒増である。R=5を維持するなら48回追加、R=4でよければ追加読みなし。

### A-3

**主張:** A1 の陽性は「現行 probe の自己観測」という経路ではなく、affinity 切替・実験 driver の前処理・全 CPU へのサンプリング IPI を束ねた介入の効果しか示さない。

**攻撃対象:** A1 を「因果の本体」とする記述、P1、F108 の根本原因表現。

**具体的な失敗シナリオ:** `/proc/cpuinfo` open は `arch_freq_prepare_all()` を通じて対象 CPU 上で APERF/MPERF callback を実行しうる。さらに実験 driver が pin 後にJSON構築やループを行えば、`c` は本番 `_parse_cpuinfo()` より長く busy になる。`c` が追随しても、「本番 probe の読み取りが構造的に必ず作る」のか、「pin と実験用前処理が作った」のか、「全 CPU を起こす測定 IPI と package turbo の相互作用」なのかが残る。

**強度:** **中**。介入が複合であることは確実だが、driver がまだ未実装なので前処理量は未確定である。

**最小の是正案:** A1 の対照を「同じ full-vector 読みで、対象 `i` は観測するが reader は別 CPU」にする。A2 は対象 `k` 上の helper を「sleep」と「busy」で比較し、reader は同じ別 CPUへ固定する。A1 の既存データに加え、A2 の sleep 対照8件だけで経路を分離できる。

### A-4

**主張:** A4 の読み前後 processor だけでは、読み取り中 migration が帯外2個を作ったという P2 を確認も棄却もできない。

**攻撃対象:** A4、A0 の self CPU、P2。

**具体的な失敗シナリオ:** 現行 `_parse_cpuinfo()` は [`Path.read_text()` で動的 procfs 全体を取得](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/orchestrator/campaign/env_attestation.py:197)し、その後に解析する。タスクが `c→d→c` と移れば前後は同じでも2 CPUを活動させる。一方、APERF/MPERF 値が open 時に準備済みなら、前後 processor が異なってもその migration が値を作ったとは限らない。CPU block ごとの生成時刻とも対応しない。

**強度:** **強い**。二つの端点から途中の経路を復元できないという観測不能性である。

**最小の是正案:** A4 は「migration と整合的」という記述的 arm に格下げし、CONFIRMED/REFUTED に使わない。厳密な立証には timestamp 付き scheduler trace が必要だが、権限と規模を増やすため本 wave では P2 の migration 部分を未解決として残す。追加コストはゼロ。

### A-5

**主張:** `c=0..47` と「vector index == c」は、48 CPU という個数を CPU ID の連続性と取り違えている。

**攻撃対象:** A1、A2 の CPU 0 固定、β の除外 index。

**具体的な失敗シナリオ:** PBS cpuset が48 CPUを与えても、その ID が `48..95` や非連続集合なら `nproc=48` は成立する。A1 は許可外 CPUへの pin で失敗するか、sorted vector の位置と CPU ID を誤対応する。CPU 0 は housekeeping/IRQ が集中する特殊 CPUである可能性もあり、A2 の固定基準として中立ではない。

**強度:** **中**。Pegasus の実際の割当てが `0..47` なら発火しないが、brief はそれを事前条件として assert していない。

**最小の是正案:** `sorted(sched_getaffinity(0))` を sweep 対象にし、要素数48を assert する。cpuinfo の `processor` IDから vector位置への明示 map を保存し、A2 の reader CPUも許可集合から選ぶ。追加読み・追加 arm は不要。

### A-6

**主張:** A3 の「全要素が厳密 2101.0」は現行 canonical 述語ではなく、α の成立可否を誤判定する。

**攻撃対象:** A3、P3、P5、方式 α の成功基準。

**具体的な失敗シナリオ:** 現行 comparator は expected median を中心に frozen tolerance を適用するため、median=2101.0、2%なら受理帯は概ね `[2058.98, 2143.02]` である。[実装](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/orchestrator/campaign/env_attestation.py:600)。α の結果が全要素2110 MHzなら正しさ gate は通るのに、brief の「厳密2101.0」は失敗扱いする。逆に2101.0への一致は、P5 の fallback/定数値問題を解消しない。

**強度:** **強い**。brief と実 comparator の判定対象が明確に異なる。

**最小の是正案:** α/β/γ の評価には canonical comparator と同じ expected median・inclusive tolerance をそのまま使う。厳密一致率は P5 用の副次診断へ分離する。追加コストはゼロで、受理集合も動かない。

### A-7

**主張:** A3 の「48 CPUを巡回してK回読み」と規模「3×48」は、方式 α の実際の推定量を一意に定義していない。

**攻撃対象:** A3、P3、規模欄、方式 α。

**具体的な失敗シナリオ:** α が「`/proc/cpuinfo` をK回開き、各回の48要素を位置ごとに最小化」なら K=3 は full-file open 3回である。A3 が記述どおり各 CPUへ pin して3回ずつ、計144回 openするなら、全 CPUを意図的に reader CPUにする別の介入であり、本番 α よりはるかに汚染的である。また最小値は上側外れだけに有効で、低周波側の一過性外れがあれば Kを増やすほど悪化する。

**強度:** **強い**。file-open 数と scalar sample 数の混同は事前登録の再現性を壊し、どちらの解釈でも片方が誤る。

**最小の是正案:** α を「unpin の本番相当条件で K=3 consecutive full-vector reads、位置ごとの cumulative minimum」と明記する。`k=1,2,3` の結果と上下別の外れを同じ3回から算出する。追加読みなし。

### A-8

**主張:** 現設計は α/β/γ の通過率を数えられても、自己汚染の除去能力と真正な環境逸脱の拒否能力を分けて評価できない。

**攻撃対象:** P3、P4、A2、A3、「同じ実験データで3方式の成立可否を評価」。

**具体的な失敗シナリオ:** quiet 条件で帯外が self の1個だけなら β と γ はともに通り、αも別読みで通る可能性があるため弁別不能である。さらに A2 で真正な非self busy `k` だけが帯外になったとき、γ が通ることは成功ではなく、環境逸脱を見逃す偽陰性である。βも migration 中の実際の汚染 CPUを一意に除外できない。

**強度:** **強い**。方式ごとの感度・特異度を定義しない限り、同じ「pass」が正反対の意味を持つ。

**最小の是正案:** 同一 raw vector に3方式を適用し、`quiet/self-only` を should-pass、A2 の sustained nonself busy を should-reject とする2×3判定表を事前登録する。A2 に sleep 対照を足せば追加は8条件だけで、別の大規模 arm は不要。

### A-9

**主張:** A2 は busy helper の無処置対照がなく、`k` が帯外に現れても busy loop の因果とは言えない。

**攻撃対象:** A2、P1 の精密化、P4。

**具体的な失敗シナリオ:** `k` が直前の kernel thread、IRQ、以前の APERF/MPERF cache、またはCPU固有の高値ですでに帯外だった場合、busy child を置いた後に `k` を観測しても陽性になる。逆に busy loop が package powerを使って turbo binを下げれば、活動を増やしたのに `k` が帯内へ下がることもあり、「busy原因なし」という誤った陰性になる。

**強度:** **強い**。介入前または sham 対照がない単群事後測定では原因帰属できない。

**最小の是正案:** 同じ reader CPU・同じ `k` について、pin 済み sleeping child と busy childをランダム順で比較し、帯外 indicatorだけでなくMHz差も採る。8 busy条件に8 sleep条件を加えるだけ。

### A-10

**主張:** A2 を途中で走らせる順序は、キャッシュ・P-state hysteresis・package温度を後続 A1/A3へ持ち込み、arm 間独立性を壊す。

**攻撃対象:** A1〜A4 の実行順、A2、A3 の単独版とA2併走版、warm-up未指定。

**具体的な失敗シナリオ:** busy child停止直後も、APERF/MPERF の差分窓には busy期間が残り、hardware turbo・thermal/power状態も即座には戻らない。直後の A3 単独版が帯外を保持すれば、α は単独ノードでも収束しないと誤判定される。逆に最初の A0だけ stale-refresh を踏めば、A0と後続 arm の差は介入差でなく warm-up差になる。例外時に child が残れば汚染はさらに直接的になる。

**強度:** **強い**。A2 は唯一の能動的な持続負荷であり、時間窓を共有する設計になっている。

**最小の是正案:** quiet A0/A1/A4とA3単独版を先にランダム化ブロックで実行し、A2およびA3-A2併走版を最後にまとめる。各ブロック初回を破棄し、child は必ず terminate・wait・生存確認する。追加 arm はなく、必要なら固定 cooldown 約1秒だけ。

### A-11

**主張:** ログインノード実測3は計算ノードの P1〜P5 に転移せず、事前確率以上の証拠として使えない。

**攻撃対象:** 前提実測3、P1〜P5。

**具体的な失敗シナリオ:** 96 logical CPU・HT有効の共有 login nodeでは、別ユーザーや sibling thread の活動、IRQ、package-wide turbo budgetが複数 indexを帯外にできる。48 physical core・HT無効・単独割当てでは sibling経路が消え、単一コア turboは逆に高くなりうる。driver/governor/boost、kernel build、NUMA/package構成も計算ノードでは未取得である。「busyなコアが帯外」という関係の符号・個数・持続時間すら保存される保証はない。

**強度:** **強い**。brief 自身が topology・同居性・cpufreq 値の相違または未観測を認めている。

**最小の是正案:** login結果は仮説生成だけに使い、CONFIRMED の分母・成功数へ一切混ぜない。計算ノードの randomized A1 contrast と controlled A2だけで判定する。追加コストなし。

### A-12

**主張:** P5 の「他要素が厳密2101.0なら実効クロックを測っていない」という推論は、v5.15 の fallback と source mixture を無視している。

**攻撃対象:** P5、cpufreq driver/governor/boost の記録、`cpuinfo_cur_freq` 可読性。

**具体的な失敗シナリオ:** upstream v5.15 の `proc.c` は APERF/MPERF 値を得られない場合、cpufreq の既知値、さらに基準クロックへ fallback しうる。[v5.15 proc.c](https://kernel.googlesource.com/pub/scm/linux/kernel/git/stable/linux-stable.git/+/refs/tags/v5.15/arch/x86/kernel/cpu/proc.c)。したがって idle/stale CPUは厳密2101.0、active CPUだけAPERF/MPERF由来の2950 MHzという混合観測が成立する。`scaling_cur_freq` も多くの構成では最後に要求した P-stateで、必ずしも瞬時の実周波数ではない。[CPUFreq documentation](https://www.kernel.org/doc/html/v5.15/admin-guide/pm/cpufreq.html)。`cpuinfo_cur_freq` が読めないことも「実周波数が基準値」の証拠ではない。

**強度:** **強い**。P5 の結論は fallback 不成立を証明しない限り論理的に導けない。

**最小の是正案:** `uname -r/-v`、boot cmdline、CPU isolation、kernel configの可読範囲、policyの `affected_cpus/related_cpus`、min/max/bios limitを記録し、P5 の結論を「hybrid source と整合的」までに制限する。数十個の静的読みだけで、新 arm は不要。

### A-13

**主張:** 現在の束縛項目は「busy user process」を、idle/C-state・kernel活動・電力熱制約・PBS外乱から分離できない。

**攻撃対象:** 記録する束縛、P1、P2、A2、A4。

**具体的な失敗シナリオ:** APERF/MPERF は wall-clock瞬時値ではなく活動区間の比率であり、idle CPUを測定 IPI が起こした短い区間だけで高値になりうる。invariant TSC は turboに追随しないため、TSC一致は反証にならない。IRQ、softirq、RCU、kernel threadは `ps/pgrep` だけでは捕捉できず、PBS prologue直後の処理や短命な他jobもsnapshot間を通過できる。NUMA/physical packageとcpufreq policyを固定順 CPU sweepに重ねれば、時刻・package・CPU IDが交絡する。thermal throttling、PL1/PL2、BIOS capは busy loop後の値を逆方向へ動かす。NUMA単独の直接経路は**弱い**が、readerの実行時間とpackage loadを介する経路は残る。

**強度:** **中**。各要因の発火は未観測だが、C-state・IRQ・package制約は実機で通常存在し、現記録では棄却不能である。

**最小の是正案:** trialごとではなく各 arm の前後だけ、per-CPU `/proc/stat`・interrupt差分、cpuidle usage/time、thermal throttle count、package/core/NUMA/policy対応、PBS/cgroup cpusetと排他割当てを採る。診断用 `scaling_cur_freq` 等は primary outcome の後に読み、cacheを先に温めない。約2 snapshot/armで、追加時間は数秒規模。

## 総括

(a) **できない** — 現状は pin と帯外 index の共変を示せても、pin の限界効果と APERF/MPERF の時間窓を分離していない。  
(b) 最重大3件:  
- **A-1:** 「集合に含む」は対照差でなく、全CPU帯外でも偽 CONFIRMED になる。  
- **A-2:** cache/stale/warm-up未束縛により R=5 が疑似反復となり、一件の外れで偽 REFUTED になる。  
- **A-6/A-12:** A3の厳密2101.0とP5の解釈が、canonical述語およびkernel fallbackの双方に反する。  
(c) 最小構成: A1を既存240読みの randomized paired contrastへ置換し、各条件の初回をanchorとして破棄する。  
A2へ同一`k`の sleeping-child対照を8件だけ追加し、busy/sleep差を測る。  
quiet armsを先、A2系を最後に置き、同じraw vectorへα/β/γのshould-pass/should-reject表を適用する。  
これ以上の arm 拡大は不要だが、A4 migrationは因果立証から外すべきである。