### 所見 1

- **主張**: 7 本の qsub 変数に即時の形式エラーはないが、plan の検査順は誤っており、実際の最初の外部依存 gate は canonical path ではなく `hostname` である。
- **根拠**: PBS は必須変数と job ID を検査した後、`^bnode[0-9]+` を先に要求し (`t2187_adaptive_const_probe.pbs:28-41`)、その後に canonical `PBS_O_WORKDIR`、HEAD、tracked-clean を検査する (`同:43-56`)。plan は canonical 判定を第 1 としている (`s2-plan.md:134-140`)。7 argv は mode=`performance`、trace=`0`、extime=`6`、rep=`0..6`、stage=`1` で、各 cell は 5 または 11 field、巡回順も正しい (`s2-plan.md:57-63`; driver の field 検査は `t2187_adaptive_const_probe.py:445-549`)。既存実物の hostname は `bnode001` と `bnode065` である (`978014 JSON:20-24`; `985851 JSON:17-21`)。ただし submit tree が本当に canonical か、投入時にも clean かは plan の期待値だけで実測出力がない (`s2-plan.md:117-130`)。
- **これが本当なら何が壊れるか**: 非 bnode なら全 job が artifact 作成前に exit 2、bnode でも logical path や dirty tree なら次の gate で同様に全滅する。
- **確度**: plausible

### 所見 2

- **主張**: extime 3 と extime 6 を同じディレクトリへ置く運用ミスは起こせるが、取り違えたまま図が受理される経路はない。
- **根拠**: 出力名は `stage${STAGE}-rep${REP_INDEX}-${PBS_JOBID//:/_}.json` で (`t2187_adaptive_const_probe.pbs:419-444`)、実物の job ID `0:978014.nqsv` は `stage1-rep0-0_978014.nqsv.json` になっている (`978014 JSON:24,57`)。全旧新ファイルを glob して 14 本渡せば 6 または 7 本の本数検査で落ちる (`plot_dynamic_backoff.py:1242-1248`)。6 または 7 本へ絞って旧 artifact を 1 本でも混ぜれば、cohort 2 診断が要求する extime 6 (`同:661-683`) に対し旧実物は extime 3 (`978014 JSON:27`) なので `_common_identity` が落とす (`plot_dynamic_backoff.py:293-296,1254-1259`)。job ID が異なるため通常の名前衝突もない。
- **これが本当なら何が壊れるか**: 誤選択時は作図が rc=1 で止まり、誤った値の図や provenance は公開されない。
- **確度**: real

### 所見 3

- **主張**: 経験的な所要時間は 40 分枠へ収まるが、要求された「内側予算の和 + 終了余裕 < 外側 watchdog」は performance 分岐には存在せず、plan の時間安全性は上限として閉じていない。
- **根拠**: nominal は `731 + 168 x (6-3) = 1235` 秒である (`s1-brief.md:117-121`)。ただし `wall_seconds` は driver 開始後だけで、scheduler 時間は prologue を足した `job_total_seconds` である (`t2187_adaptive_const_probe.py:3872-3880`)。実物でも `714.436 + 9.693 = 724.130` 秒である (`978014 JSON:15203-15209`)ため、見積りは約 `1235 + 10 = 1245 < 2400`、余裕は約 1155 秒となる。一方、performance exec は `OUTER_WALLTIME_S`、`BUILD_BUDGET_S`、`PROLOGUE_BUDGET_S`、`EXIT_MARGIN_S` を一切渡さない (`t2187_adaptive_const_probe.pbs:420-444`)。`7440 < 8100` の検査は certify 専用 (`t2187_adaptive_const_probe.py:1458-1471`)。performance は各点に 180 秒 timeout を置くだけで (`同:107,3792-3803`)、7 build には deadline がなく (`同:3722-3760`)、168 点すべてが timeout 未満でも理論上の run 合計は最大約 30240 秒になる。
- **これが本当なら何が壊れるか**: 累積時間が 2400 秒を越えた任意の rep は PBS に終了させられ、最終 JSON 作成前なので journal だけが残り、2 本以上なら図の最低 n=6 に届かない。
- **確度**: real

### 所見 4

- **主張**: 親の「7 job 間で build cache のファイル取り合いは起きない」という主張は driver 実コードで裏付けられる。
- **根拠**: PBS は job ID を含む `/scr/${PBS_JOBID//:/_}-t2187` を排他的に作る (`t2187_adaptive_const_probe.pbs:266-270`)。gflags/glog の build/install 木もその配下である (`同:343-371`)。driver はさらに `$TMPDIR/ccbench-src` へ isolated checkout を作り (`t2187_adaptive_const_probe.py:658-683`)、build cache も `$TMPDIR/build-variants` に置く (`同:3657-3662`)。同一 node でも job ID が別なら書込み先は分離される。
- **これが本当なら何が壊れるか**: build 木の相互上書きは起きないが、同一 node での同時実行による CPU・メモリ競合までは防がない。
- **確度**: real

### 所見 5

- **主張**: 7 本を数秒差で qsub しても、異なる node で同時に走ることは保証されず、その逸脱を plot は拒否しない。
- **根拠**: PBS は各 job に `-b 1` を要求するだけで、7 job 間の anti-affinity や同時開始条件を持たない (`t2187_adaptive_const_probe.pbs:2-6`)。plan も「数秒差の同時投入扱い」とするだけである (`s2-plan.md:191-194`)。plot は重複 hostname を列挙するだけで fail しない (`plot_dynamic_backoff.py:1267-1276,1729-1733`)。driver は各点を最大 48 threads で走らせる (`t2187_adaptive_const_probe.py:3786-3803`)ため、同一 node へ同時配置されれば過剰競合になる。queue 遅延が大きくても、各 job 内の paired contrast は保たれる (`plot_dynamic_backoff.py:978-986`)が、開始時刻は受理条件にも provenance 入力記録にも含まれない (`同:1624-1661`)ので、同時 multi-node という運用条件の逸脱は無検知である。
- **これが本当なら何が壊れるか**: 同時 co-location や大きな時刻ドリフトで歪んだ performance 値が、そのまま H1–H7 と provenance の受理集合へ入る。
- **確度**: plausible

### 所見 6

- **主張**: qstat の 8 文字 job 名、終了済み rc=0、途中 JSON の三つについて、plan の待ち方は正しく fail-closed である。
- **根拠**: plan は exact job ID ごとに `qstat -f` し、rc ではなく `job_state` と `Exit_status` を見る (`s2-plan.md:213-220`)。journal は各 row ごとに別名 `OUT.journal.jsonl` へ append、flush、fsync される (`t2187_adaptive_const_probe.py:1323-1330,3861`)。最終 JSON は全ループ終了後に初めて `open("x")` される (`同:3872-3885`)。したがって `F` かつ exit 0 を待てば書込み途中を読む経路はなく、kill 時の journal は plot 入力名にもならない。欠測規則も投入前に n=6、5 以下停止と固定されている (`s2-plan.md:222-229`)。
- **これが本当なら何が壊れるか**: この部分では受理集合は結果閲覧後に変更されず、partial journal や途中 JSON が図へ混入しない。
- **確度**: real

### 所見 7

- **主張**: login node での作図は「計測機の外」と login node の重処理禁止を同時に満たすため、この点は投入前停止理由ではない。
- **根拠**: PBS 自身が probe を bnode 限定にする (`t2187_adaptive_const_probe.pbs:37-41`)一方、作図規約は既取得データを計測機外へ出して描くよう要求する (`FIGURE_CONVENTIONS.md:73-77`)。plot は Agg backend の matplotlib/numpy により既存 JSON を読む処理で (`plot_dynamic_backoff.py:25-29,1796-1808`)、benchmark、floor、oracle の本走ではない。plan の login node 実行 (`s2-plan.md:239`) はこの境界と一致する。
- **これが本当なら何が壊れるか**: 何も壊れず、作図のために計算 node を確保する必要はない。
- **確度**: plausible

### 所見 8

- **主張**: 新設する extime 6 companion 登録文書は、最終 figure provenance に結び付かない。
- **根拠**: plan は新規登録文書の commit/SHA を `submitted-jobs.txt` と insight にだけ記録する (`s2-plan.md:154-162,203-211`)。driver の `prereg_sha256` は常に旧 `docs/dynamic-backoff-preregistration.md` の bytes から作られる (`t2187_adaptive_const_probe.py:84,951-954,3691-3693`)。plot provenance が出す登録参照もこの `identity["prereg_sha256"]` だけで (`plot_dynamic_backoff.py:1709-1724`)、companion commit、SHA、`submitted-jobs.txt` のいずれも含まない。診断実物の値は旧文書の `cc8975...ee68` である (`985851 JSON:20`)。
- **これが本当なら何が壊れるか**: 生成された provenance 単体では extime 6 の outcome-blind 登録を特定できず、旧 extime 3 登録の SHA だけを参照する。
- **確度**: real

### 所見 9

- **主張**: brief と plan が採用した「H1–H7 は extime 3 の凍結判定を置き換えないと図に明記する」という条件は、現在の生成器と最終手順では達成できない。
- **根拠**: brief は図への明記を要求する (`s1-brief.md:90-94`)。plan も条件自体は採る (`s2-plan.md:154-164`)が、最終手順ではその限定を insight にのみ記す (`同:239-240`)。実際の contrasts 図は extime 6 の subtitle (`plot_dynamic_backoff.py:1299-1305`)、H1–H7 の status と acceptance condition (`同:1214-1238,1465-1469`)、未認証 footer (`同:1474-1479`)を出すだけで、「companion」または「extime 3 を置き換えない」という文言を持たない。provenance も H1–H7 の status をそのまま保存する (`同:1742-1747`)。
- **これが本当なら何が壊れるか**: 3 図と provenance は生成できても、図単体では extime 6 の判定が extime 3 の再判定に見え得るため、brief 自身の主張範囲を満たさない。
- **確度**: real

### 所見 10

- **主張**: 正しい入力を渡しても、実データ固有の bbox 検査が落ちれば本 wave の scope 内では完了判定へ到達できない。
- **根拠**: plan 自身が実データ固有の bbox は最終作図時まで未確定と認める (`s2-plan.md:42`)。生成器は 3 図すべてを保存前に layout 検査し (`plot_dynamic_backoff.py:1800-1808`)、例外時は rc=1 で終了する (`同:1838-1840`)。規約も重なり時は一切出力しないと定める (`FIGURE_CONVENTIONS.md:85-90`)。成功した場合だけ 6 図ファイルと provenance を transaction で公開する (`plot_dynamic_backoff.py:1810-1837`)。
- **これが本当なら何が壊れるか**: layout が実値で落ちた場合、禁止された generator 改修なしには「3 図 + provenance」の完了判定へ届かない。
- **確度**: plausible

## 総括

このまま投入してはいけない。投入前に、performance の時間契約、multi-node 同時性、companion 登録の provenance 結合、図上の非置換明記という所見 3・5・8・9を解消する必要がある。