## 判定

**NO-GO。must-fix 8 件、nit 3 件。**

静的検査のみで、指定どおり pytest は実行していない。最大の blocker は、実 probe の診断 JSON を図生成器が読めず、実寸 fixture が別 schema を合成して断絶を隠している点である。

## Must-fix 1 — 診断 producer と図生成器の schema が一致しない

位置: [t2187_adaptive_const_probe.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/pegasus/probes/t2187_adaptive_const_probe.py:739)、[同 main](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/pegasus/probes/t2187_adaptive_const_probe.py:2920)、[plot_dynamic_backoff.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/plotting/plot_dynamic_backoff.py:397)、[test_plot_dynamic_backoff.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/orchestrator/tests/test_plot_dynamic_backoff.py:132)

指摘: probe は `trace_events`、`trace_summary`、`directional_success.successes`、文字列の `trigger=count|cap|time` と `parity_branch=none|decrement|increment`、および `median_tps`/`throughputs` を出す。一方 plot は `events`、`summary`、`hits`、整数 trigger/parity、`throughput_diagnostic_only` を要求し、`scored=0` 時の producer の `rate=null` も受理しない。

受理の含意: producer schema を正本に揃えれば、18 run の実診断 JSONから診断図と provenance を生成できる。  
拒否の含意: 現状では `--trace-json` の読込みで必ず失敗し、3 図すべてが生成不能である。

成果物への影響: 診断図・性能図・forest・provenance の一括生成が成立しない。

修正案: plot を現在の probe row に合わせ、文字列 enum、`trace_events`/`trace_summary`、`successes`、nullable rate を検査する。fixture は手書きの別 schema ではなく、probe の parser が返す row から組み立て、exact genome も検査する。

## Must-fix 2 — 欠測規則と journal が解析経路に実装されていない

位置: 事前登録 §6・§8、[plot_dynamic_backoff.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/plotting/plot_dynamic_backoff.py:292)、[同 load_inputs](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/plotting/plot_dynamic_backoff.py:665)、[probe journal](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/pegasus/probes/t2187_adaptive_const_probe.py:832)、[plot test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/orchestrator/tests/test_plot_dynamic_backoff.py:282)

指摘: plot は常に 7 final JSON、各168 row、全点 n=7 を要求し、テストも missing file/row を拒否する。事前登録は complete block 1 件欠測時の n=6、点 timeout の点別 n=6、partial journal の表掲載、最初に完走した retry の採用を要求するが、journal consumer と receipt 選択器がない。

受理の含意: n=6・点別欠測・partial block・retry 選択を実装すれば、障害後も登録済み規則だけで結論を出せる。  
拒否の含意: 現状では障害後に全実験を捨てるか人手で入力を選ぶことになり、結果後の選択余地が残る。

成果物への影響: 欠測表、確認的判定、図、台帳が §6 どおり生成できない。

修正案: journal に schema/header/ordinal/job ID を持たせ、final JSON に journal の件数と SHA256 を束縛する。解析器は complete receipt 6–7件と partial journal を読み、判定用 sample と表掲載用 sample を分離する。なお §8 の「全入力 7+1」は §6 の n=6 と矛盾するため、性能値を見る前に改訂履歴付きで「利用可能な6または7 complete block + 診断1」と明確化する。

## Must-fix 3 — performance の exact 7 cell・軸・巡回を投入前に束縛していない

位置: 事前登録 §2–§3、[parse_cells](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/pegasus/probes/t2187_adaptive_const_probe.py:310)、[_validate_grid_contract](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/pegasus/probes/t2187_adaptive_const_probe.py:408)、[PBS validation](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:90)、[plot order check](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/plotting/plot_dynamic_backoff.py:304)

指摘: performance mode は exact 7 cell を持たず、空白や `1.0` などを正規化し、none/stock と build 重複がなければ任意 grid を受理する。workload、8 thread、rep 0..6、extime、巡回順も投入前には固定されず、plot は `grid_spec` を無視するため、数値的に同じ非 byte-identical cell は正式成果物まで通る。

受理の含意: rep index ごとの exact 文字列と全軸を driver/PBS で先に検査すれば、§2 の腕 identity と §3 の巡回を投入前に保証できる。  
拒否の含意: 現状では誤った job が高価な build/run を完走し、表記差だけなら正式図にも受理される。

成果物への影響: JSON の腕 identity、`cell_order`、図 legend、rep 対応の証明が byte-exact でなくなる。

修正案: legacy 汎用 grid と本 campaign を明示 mode で分け、後者には7本の canonical cell textと7巡回を定数化する。`cells`、workloads、threads、rep、reps、extime、stage、出力 subdirectory を exact 比較する。

## Must-fix 4 — 凍結済み prereg と `repo_head` の結び付けが fail-closed でない

位置: 事前登録 §0・§8、[_validated_repo_head](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/pegasus/probes/t2187_adaptive_const_probe.py:649)、[_prereg_sha256](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/pegasus/probes/t2187_adaptive_const_probe.py:665)、[plot identity](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/plotting/plot_dynamic_backoff.py:195)、[fixture identity](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/orchestrator/tests/test_plot_dynamic_backoff.py:61)

指摘: probe は現在の prereg bytes の hash を記録するだけで、凍結値 `1e43a8944d36299b7e32c14cd0e1d403a1e405d325405460caafbc87736fd4d4` と照合しない。`repo_head` は HEAD 文字列との一致だけで dirty worktree を拒否せず、plot も任意の40/64桁 hexを入力間で揃えるだけで受理する。

受理の含意: frozen blob と clean commit を検証すれば、結果前に存在した事前登録・driver・patchを後から検証できる。  
拒否の含意: prereg や driver を未コミットで変更しても、その新しい hash を全 job が記録すれば正式入力として通る。

成果物への影響: レポートと図の「凍結済み規則に従った」という provenance claim が成立しない。

修正案: frozen prereg SHAを probe/plot の両方で照合し、`repo_head` の blobが同じ SHAであること、worktreeが tracked/untracked とも clean であることを qsub 前と driver 起動時に検査する。

## Must-fix 5 — §8 の probe/PBS identity と full ccbench pin が provenance に閉じていない

位置: 事前登録 §8、[performance payload](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/pegasus/probes/t2187_adaptive_const_probe.py:2760)、[PBS exec](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:325)、[figure provenance](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/plotting/plot_dynamic_backoff.py:1026)

指摘: `repo_head`、`prereg_sha256`、A/B patch と stack は JSON・図 provenance に載る点は正しいが、probe/PBS の実行 argv・SHAが記録されない。performance JSON の `ccbench_commit` は短縮 `511c953` で、別 field の full `ccbench_head` は図 provenanceへ引き継がれない。

受理の含意: qsubから図までの実行 closure を記録すれば、同じ入力と解析規則を再現できる。  
拒否の含意: 現状の provenance だけでは、どの PBS bytes・driver argv・full pin が測定を作ったかを復元できない。

成果物への影響: 図 provenance と投入台帳の proof-chain が §8 の必要項目を欠く。

修正案: driver path/SHA、PBS path/SHA、canonical driver argv、full ccbench SHAを各 JSON に記録して図へ転送する。qsub argv 自体は job 内から完全復元できないため、親が create-only launch manifest を事前生成し、その path/SHAを全 jobへ渡す。

## Must-fix 6 — forest が H1〜H7 の「判定」を図示せず、複合 reject 規則も未登録

位置: 事前登録 §4、[_point_verdict](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/plotting/plot_dynamic_backoff.py:538)、[_robust_benefit](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/plotting/plot_dynamic_backoff.py:600)、[_hypotheses](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/plotting/plot_dynamic_backoff.py:648)、[forest](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/plotting/plot_dynamic_backoff.py:819)

指摘: 対内 log 比、Student-t、±3%、各点の5判定語、H1〜H7の対比と受理条件は一致し、CLI override もない。しかし図は composite verdict を表示せず、H2では判定対象外の16点、H6では判定対象外の21点も同じ強調で描き、さらに hypothesis-level の `rejected/inconclusive` の境界は prereg に定義されていない。

受理の含意: 判定対象と composite outcome を図示し、outcome 語を凍結すれば、forest 単体で H1〜H7 の答えを監査できる。  
拒否の含意: 現状では図から H2/H6 の採用点や最終判定が分からず、台帳の `rejected` と `inconclusive` は事後追加規則になる。

成果物への影響: forest caption、仮説台帳、レポートの結論語が同一の登録済み判定を表さない。

修正案: 各 panel に composite status と条件を表示し、H2/H6 の非判定点を明示的に弱める。三値判定を維持するなら性能値を見る前に規則を prereg へ追記し、不要なら `acceptance_condition_met` と満たさなかった predicate の列だけを出す。

## Must-fix 7 — abort 副次指標が登録済みの対内 percentage-point 差でない

位置: 事前登録 §4、[_aggregate_performance](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/plotting/plot_dynamic_backoff.py:489)、[thread figure](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/plotting/plot_dynamic_backoff.py:758)

指摘: prereg は abort率を「同一 block 内の percentage-point 差」として示すと固定しているが、実装は各腕の生 abort率を別々に平均して t CI を描く。paired abort difference は計算も provenance 出力もされない。

受理の含意: 同一 contrast・blockの abort差を出せば、副次指標も paired design と整合する。  
拒否の含意: raw arm CI の重なりを読者が差の判断へ使い、登録した副次解析と異なる解釈を招く。

成果物への影響: thread図の下段と provenance の abort 節が prereg と不一致である。

修正案: H1〜H7ごとに `100*(abort_a-abort_b)` の block sample、平均、t CIを provenanceへ出し、図または副表で示す。raw abort系列を残す場合は記述用と明記する。

## Must-fix 8 — 32 job の exact 投入例と distinct-host 成立条件がない

位置: 裁定 §6、事前登録 §3・§7、[PBS examples](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:7)、[diagnostic/cert checks](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:118)、[group arguments](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:309)

指摘: PBS 自体には正しい値を渡せるが、記載例は legacy 2腕×2 thread、certify pilot は `tuned` と `...` を含む非実行例である。7巡回 perf、診断1本、`cw-as-dyn` 認証24本の exact command/group-result path集合がなく、独立 jobが同じ nodeへ再配置される可能性も plot の distinct-host 要求と調停されていない。

受理の含意: create-only launch manifestから32 commandを生成すれば、裁定どおり perf 7・診断1・認証24を同じ束縛で投入できる。  
拒否の含意: 現状は手作業の長い `qsub -v` に依存し、誤腕・誤rep・欠けた24 path・host重複による再投入が起こりうる。

成果物への影響: 投入台帳、7 block 成立、認証 group receipt の再現性が保証されない。

修正案: rep 0 canary＋巡回6本、診断1本、dynamic pilot＋残り23本を生成する専用 manifest/helper を置く。全24結果 path、共通 attempt ID、performance artifact/SHA、verifier identity/SHA、mode別 exact outdirを事前検査し、hostnameだけを見た重複時の扱いも prereg に固定する。

## Nit 1 — 一般11-field parser が整数 µs と inert 値を投入前に拒否しない

位置: [parse step](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/pegasus/probes/t2187_adaptive_const_probe.py:284)、[dynamic validation](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/pegasus/probes/t2187_adaptive_const_probe.py:359)、[patch static assertions](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/patches/cicada-adaptive-dynamic.patch:89)

指摘: parser は 0.001 µs単位を受理するため、整数 µsでない adaptive bounds、`step_adapt=0` なのに100/100でない bounds、`dyn=1` で ceiling<50 を build前には拒否しない。patch の static_assert が後で落とすため誤測定にはならないが、PBS費用を消費する。

受理の含意: parser側でも同じ制約を持てば、invalid jobをprologue/build前に止められる。  
拒否の含意: 正式7腕は整数なので結果の意味は変わらないが、汎用11-field APIの拒否位置が遅い。

成果物への影響: 正式成果物ではなく、失敗 job と費用台帳にだけ影響する。

修正案: adaptive時の3 step値を整数 µsに限定し、inert値100/100、dynamic ceiling≥50を明示検査する。

## Nit 2 — transition test が K=0 の counter 非読取りを固定していない

位置: 裁定 A-MF13、[transition tests](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/orchestrator/tests/test_dynamic_backoff_transitions.py:406)、[stock comparison](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/orchestrator/tests/test_dynamic_backoff_transitions.py:445)

指摘: K境界、OR cap、rate-limit、刻み上下限、ceiling縮小/floor、stock遷移出力は検査されるが、「K=0なら counter を読まない」は観測されていない。positive-gradient時の ceiling倍増と1000 clampも直接固定されていない。

受理の含意: counter accessorの観測 seam とceiling上昇ケースを足せば、裁定の遷移契約全体をmutation testで守れる。  
拒否の含意: 現実装は静的には仕様どおりだが、該当枝の将来退行をこのtest群は捕まえない。

成果物への影響: 現在の数値成果物には直結しないが、遷移testを完全な受入証拠とは呼べない。

修正案: K=0経路で counter-read hook が0回であるケースと、50→100→…→1000の単調増加/clampケースを追加する。

## Nit 3 — performance/diagnostic の実費から PBS prologue が抜ける

位置: 事前登録 §3、[PBS prologue measurement](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:279)、[performance exec](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:325)、[probe timer](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/pegasus/probes/t2187_adaptive_const_probe.py:2749)

指摘: PBS は prologue時間を計るがperformance/diagnostic branchには渡さず、JSONの `wall_seconds` はdriver開始後だけである。見積りの算術は perf 1 job約17.5分、certify期待6–10 node-hourで整合するが、実費を成果物から監査できない。

受理の含意: prologueとdriverを分けて保存すれば、見積りと実費を同じ台帳で比較できる。  
拒否の含意: 科学的判定は変わらないが、費用報告はscheduler logへの外部依存が残る。

成果物への影響: 費用台帳のjob総時間がprologue分だけ過小になる。

修正案: certifyと同様に prologue elapsed/CPUをperformance/diagnosticへ渡し、総job時間も記録する。

## 受理できた点

- §2 の7腕に書かれた数値、patch A SHA、patch B SHA `eb6669…` は裁定と一致する。
- 5-field genomeは旧 canonical bytesを保持し、追加defineはextended/diagnostic時だけ入る。
- K=0⇒cap=0、adaptive時の初期step範囲、dynamic時の `step_max*4<=50` は検査される。
- patchのtrace stdoutは12 fieldで、probe testの合成行は実際の出力順・数値形式と一致する。
- 方向的中は action符号と次窓throughput差の符号で再計算され、action 0はunscored、`dropped!=0`は拒否される。
- point-levelの対内log比、t分位点、±3%、5判定語、H1〜H7対比、全7×24点のprovenance出力は一致する。
- plot fixtureの件数自体は7×168 row＋18 runで、accepted/rejected/inconclusiveの3状態を通る。ただし Must-fix 1 のとおり診断rowの形が実producerと異なる。
- 診断throughputは描かれず、`headline_eligible=false` と計装系の軌跡という表示は入っている。
- PBSは`repo_head`をdriverへ渡し、JSONはA/B patch stackとordered stack digestを記録する。

## 総括

- **must-fix: 8件**
- **nit: 3件**
- **未閉鎖の段3所見:** MF-01（hypothesis-level outcome語とabort副次解析）、MF-06（診断のconsumer closure）、MF-07（exact投入・distinct host）、MF-09（n=6・partial journal・retry）、MF-11（判定を図示するforest）、MF-12（frozen blob・probe/PBS argv・full provenance）
- MF-02〜MF-05は裁定後の値・主張境界で閉じている。MF-08の見積り訂正は閉じ、実費記録だけをnitとした。MF-10は裁定でrefutedされたため、未閉鎖には数えない。
- **GO / NO-GO: NO-GO**。特に Must-fix 1、2、4、8を直すまで、性能値・診断・認証のいずれも投入すべきでない。