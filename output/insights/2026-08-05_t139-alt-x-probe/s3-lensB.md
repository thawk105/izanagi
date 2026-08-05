判定は **NO-GO**。以下は静的検査のみで、新しい build・pytest・qsub・性能計測は実行していない。

[blocker] 所見: 提案修正は、計測対象上では仮説 (i) の per-element 走査を除去しておらず、W2 逆転を二仮説だけでは定量説明できない。  
根拠: YCSB key は常に 8 byte (`external/ccbench/include/ycsb.hh:44-48`)。旧 mode2 はその 8 byte を 8 iteration 回り (`tools/pegasus/probes/t139_positive_control.patch:72-76`)、新案も同じ 8 iteration を回った後に mix する (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-alt-x-probe/s2-plan.md:50-72`)。したがって改善は漸近量でなく乗算数等の定数差だけである。さらに5標本集計では、W2 の transaction attempt rate が mode1 約 1.488M/s → mode2 約 1.334M/s (-10.4%)、abort 率が 31.23% → 35.06%へ悪化している。代表標本でも mode2 は abort 0.3499 / 888,148 tps、mode1 は 0.3140 / 1,025,816 tps (`output/env/pegasus/t139-positive-control-probe/0_877859.nqsv/run-16-W2-mode2-r1.log:13-21`, `.../run-17-W2-mode1-r1.log:13-21`)。第3の機序は、単一 mutex の backpressure が record-lock 競合を抑え、2 stripe の futex/wakeup・CAS timing が同時進行と abort を増やした可能性である。  
予測: W1 は旧 mode2 が 121,586–131,224、mode1 上限 96,131、stock 下限 743,407なので、padding 後も概ね横ばい〜上昇なら受理されやすい。W2 は新 modeX の全標本が 1,038,788 を超える必要があり、旧 mode2 の最良 888,148からでも +17%、最悪からなら +23%必要で、paddingだけで届く保証はない (`throughput.tsv:2-31`)。  
成果物影響: 放置すると false verdict から「仮説を直しても代替 X は死んだ」と誤記し、候補実装の欠陥と mutex scheduling 機序を区別できない。  
最小の直し方: per-byte loop を実際に除く固定回数 load にし、既存ログから得られる attempt rate・abort rateを事前登録済み副次診断に加える。因果帰属するなら padding-only / mixer-only ablation は別の事前登録 wave にする。

[blocker] 所見: 段2の stripe 関数は追補の明示要件を満たさず、追補の「先頭・末尾・長さ」要件自体も退化防止として不十分。  
根拠: 追補は先頭窓・末尾窓・長さを最低条件とする (`brief-addendum.md:44-46`) が、案は末尾と長さしか読まない (`s2-plan.md:50-72`)。提示式を100,000件へそのまま評価すると YCSB は 50,051/49,949だが、`warehouse/<i>/district` は 9,910/90,090となる。後者は先頭と末尾が共通なので、先頭窓を足しても情報量は増えない。追補が実測した 50,003/49,997は別の suffix-only 式であり (`brief-addendum.md:28-46`)、提案式の throughput 根拠ではない。  
成果物影響: 放置すると modeX が実質 1 stripeへ退化した結果を候補の不成立として記録し、probe verdict と後続候補集合を誤らせる。  
最小の直し方: 中央付近を含む固定個数の窓を混ぜ、段4で YCSB と少なくとも1つの共通 prefix/suffix 可変長族に対する最大 bucket 比を固定する。

[blocker] 所見: 「stockへ近づきすぎるから2 stripe」という親 brief の理由は定量的に支持されない。  
根拠: 平均値は stock/mode1 が W1 で 8.05倍、W2 で10.01倍 (`throughput.tsv:2-31`)。gate-only の線形目安でも4 stripeは W1約373k、W2約4.09Mで、それぞれ stock 下限743,407、10,194,690からまだ遠い。W1で初めて上限懸念が出るのは約8 stripeである。対して2 stripeはW2下限を越えるために旧実装から約20%の平均改善を必要とする。親の根拠は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-alt-x-probe/brief.md:42-46`。1 stripeへ減らす案は mode1そのもので strict inequality を満たせない。  
成果物影響: 放置すると「2」という未根拠の候補選択が false verdict を決め、結果後に3/4 stripeへ替えるとD126違反になる。  
最小の直し方: 段4で2を維持するなら stock 非分離を理由から外し、保守的2-stripe候補だけを試すと明記する。部分回復を得る確率を優先するなら、結果を見る前に3または4へ変更する方が定量的には妥当。

[blocker] 所見: retry・timeout・失敗分類がT-338 Q8の閉表になっていない。  
根拠: 現 driver は科学的な acceptance false でも `awk` が rc=1を返しPBS failureになる (`tools/pegasus/probes/t139_positive_control_probe.sh:77-78`)。プラン自身も再投入余地を認めるが (`s2-plan.md:301-321`)、段4択一に retry 数とrc処理を残したままである (`s2-plan.md:410-414`)。D134は correctness anomalyを終端reject、結果を見る前に外部証拠で確定したinfraだけ置換可、走行開始後の性能欠測はrejectまたは判定不能と固定している (`docs/decisions.md:6526-6530`)。現案では modeX build失敗、liveness timeout、性能timeout、単独性違反をすべて「verdict無し」にまとめられる。  
成果物影響: 放置すると遅い／飢餓する候補のattemptだけを捨てて再投入でき、採用raw集合と受理結果が変わる。  
最小の直し方: qsub前に閉表を固定する。exact true/falseは終端・retry禁止、liveness/correctness異常は終端reject、性能開始後timeoutはreject/判定不能、事前に外部証拠で確定したinfraだけ予備1本へ置換、build修正は新hash・新studyとして全submissionを残す。

[blocker] 所見: J=1 の限定は条件付きで正しいが、pass/fail後の行動と語彙が未登録で、親はT-338の射程を狭めすぎている。  
根拠: worklog (134) はこの「代替X probe再走」の cluster 数・schedule・事前登録がQ1〜Q5に従属すると明記する (`docs/archive/worklog-phase3-0803-134.md:67-70`)。裁定済みQ5はpilot先行、d≈1.0なら約11 cluster、結果後の標本追加禁止である (`docs/archive/worklog-phase3-0803-142-143.md:3-11`)。一方、親はJ≈11を「本走だけ」と切り離し (`brief.md:52-55`)、プランはJ=1で条件が「十分」とする (`s2-plan.md:237-271`)。J=1を安価なengineering screenに限定すること自体は許されるが、「modeX成立」やcluster間再現性は言えない。未較正10k/100kをheadline・floorへ使わない限定は正しい (`s2-plan.md:266-271`)。  
成果物影響: 放置すると局所1 jobのorderingが「代替X成立」または正例生成経路へ昇格し、後続J・候補・参照が結果依存で決まる。  
最小の直し方: `engineering_screen / J=1 / uncalibrated / nonqualification` と固定し、pass→同一bytesを次のQ1〜Q11準拠study候補へ送るだけ、false→このexact候補を終端不成立、別候補は新wave、判定不能→候補状態不変、まで事前登録する。

[blocker] 所見: 現在の単独性検査は exclusivity witness として有効でない。  
根拠: 検査は `load1<=48` と `ycsb_.*\.exe` の `pgrep`だけ (`probe.sh:10-14`)。48-threadの自ジョブにより前回load1は2.04から38.45まで単調に蓄積している (`solo-checks.txt:1-72`)。したがって他種のCPU/IO負荷を見逃す一方、自身の残留loadで過剰拒否もしうる。gen_Sは48/48 coreを割り当てるがexclusive submitではない (`docs/pegasus-runbook.md:45-48`)。QUE 123/RUN 40は待ち時間の情報であり、割当ノードの単独性証拠ではない。  
成果物影響: 放置すると汚染標本が `solo 36/36` として受理されるか、自己残留loadによる欠測をinfra retryへ流して標本集合が変わる。  
最小の直し方: 自job treeを除外したprocess/cgroup概況、CPU affinity、PSI、pre/post snapshotを記録し、foreign workload検出を理由コード化する。現検査だけなら「限定screen」と改称し、単独性成立を主張しない。

[major] 所見: 通常経路は1時間に十分収まりそうだが、failure-pathの資源上限は閉じていない。  
根拠: 現PBSは1時間 (`t139_positive_control_probe.pbs:4`)。前回は依存2 build、6 CCBench build、liveness、30 performance runを含め176秒だった (`.../t139_positive_control_probe.pbs.e877859:9-14`)。一方、依存buildにはtimeoutがなく (`t139_positive_control_probe.pbs:46-51`)、6 armそれぞれにconfigure 600秒・build 900秒を許すため (`probe.sh:35-40`)、内部上限合計はwalltimeを超える。加えてgeneric targetのcompile smokeは別途要求されるが予算化されていない (`s2-plan.md:329-336`)。  
成果物影響: 放置すると最大1時間を消費してverdict無しとなり、retry分類の穴へ接続する。  
最小の直し方: dependency・全build・smoke・run・finalize reserveを合わせた絶対deadlineを1時間未満で固定し、generic smokeを同jobに含めるか別requestとして明示会計する。

[major] 所見: artifactを発行しない結論は正しいが、親 brief の権威境界参照はstale。  
根拠: briefはD126決定(3)を現在理由としている (`brief.md:19-20`)。しかしD162は既に「producerではなく独立validatorだけが適格性権威」と条文化済み (`docs/decisions.md:8001-8020`)。残っているのはvalidator/consumerの機械化であり、worklogも実装被覆0/9とする (`docs/archive/worklog-phase3-0805-196.md:47-51`)。  
成果物影響: 放置しても今回のcertified受理集合は変わらないが、stage7の判断参照と「なぜ発行不能か」のproof chainが誤る。  
最小の直し方: frozen briefは書き換えず、段4裁定でD162 erratumを置き、「J=1非適格＋validator未実装」を非発行理由にする。

[refuted] 所見: 「[T-338]が全件裁定済みなので[T-139]の裁定側着手条件が成立」は正しい。  
根拠: worklog (142) は11/11裁定完了と下流T-139 blocker解消を明記する (`docs/archive/worklog-phase3-0803-142-143.md:22-24,34-40`)。D162も11問全件裁定済みを再確認する (`docs/decisions.md:8003-8007`)。ただしQ11実装はartifact発行の別条件であり、上記J=1限定を正当化するものではない。  
成果物影響: この疑いによる値・受理集合・参照の変更は不要。  
最小の直し方: 着手条件とartifact発行条件を別文にする。

[refuted] 所見: `/work` へ復旧したgflags/glogの静的互換性には反証材料がない。  
根拠: 実体は非symlink directory、HEADは gflags=`e171aa2…`、glog=`8f9ccfe…`、両 `git status --porcelain --untracked-files=all` は空で、policyのpinと一致する (`tools/pegasus/policy.json:14-17,36-38`)。同pinは前回の計算ノードでgflags/glogをbuild/install済み (`...pbs.o877859:30-57,189-214`)。  
成果物影響: 調達path変更だけでbuild値や受理集合が変わるとの疑いはrefuted。ただし新modeX buildの緑は未主張。  
最小の直し方: 計画どおりroot/head/clean witnessをrawへ残す。

[refuted] 所見: 「artifact未発行なのでcertified受理集合は不変」と「軽量版にしない」は妥当。  
根拠: D126はprobeがgateを新設せず受理集合不変とする (`docs/decisions.md:6221-6224`)。`DW-C00` は設計択一・正しさ防壁・受理集合のいずれかに触るとき独立敵対検証子を要求する (`docs/dev-wave/core.md:11-15`)。P1のstripe択一とP2のpin/権威境界が該当する。  
成果物影響: certified選択・材料レポート・proof chain・凍結bytesは不変。変わるのはprobe-local候補とrawだけ。  
最小の直し方: 「受理集合」は常に `certified受理集合` と限定して書く。

[refuted] 所見: 追補はfalse sharingをW2逆転の原因とは主張しておらず、限定は適切。  
根拠: 追補は明示的に原因帰属を否定する (`brief-addendum.md:18-20`)。なお前回binaryの `gates` は `0x4f600` にあり (`output/.../nm-mode2.txt:115`)、40-byte mutexの開始はoffset 0と40で同じ64-byte lineに入るため、構造的共有は「しうる」より強く裏が取れる。それでも因果量は未測定である。YCSB 2分割均等性も、追補はthroughput改善とは述べていない。  
成果物影響: この文言自体による受理集合変更はない。因果へ昇格した場合だけmodeX設計根拠が過大になる。  
最小の直し方: 段4でも「配置確認済み・原因未実証」を維持する。

## 総括

- **NO-GO**。qsub前に、機序と定量予測、stripe関数、stripe数、Q8失敗閉表、J=1後の分岐、単独性witnessの6点を固定する必要がある。
- **blocker: 6件**。
- **refuted:** [T-338] 11/11裁定済み、通常時1時間不足、`/work` pin調達の静的不整合、certified受理集合の変更、軽量版にすべきとの疑い、追補がfalse sharing原因を断定したとの疑い。
- **裁定パッケージ候補:** gflags/glogをversionedな共通調達経路へ一般化する件、Pegasus全probe共通のprocess/cgroup/PSI単独性witness、padding/hash/stripe数を分離する再利用可能な機序ablation設計。