## 所見

**B1｜must-fix｜欠測を許す裁定と作図が噛み合わない。** [plot_vhash_cicada_tuning.py:82](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/tools/plotting/plot_vhash_cicada_tuning.py:82) と [同:136](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/tools/plotting/plot_vhash_cicada_tuning.py:136) は J1 に W4、J2 に W5 を必須とする。J0b/J0c の待機 build は compile 不能で、裁定は W5 欠測で続行すると定める。R4 では J1 の W4 も外す。**放置時の成果物への影響:** 有効な部分集合の実測が揃っても、図２種の生成が例外で止まる。**推奨:** summary の測定済み workload だけを描き、欠測と理由を図の caption・provenance に残す。

**B2｜must-fix｜縮小梯子 R4 の W4 候補が生成されない。** [driver.py:139](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/tools/vhash_cicada_tuning/driver.py:139) は W4 の候補を常に `selected["W4"]` から取る。R4 では W4 を J1 から外すので、[analysis.py:73](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/tools/vhash_cicada_tuning/analysis.py:73) の選抜結果は空になり、J2 は control だけになる。**放置時の成果物への影響:** R4 適用時の W4 の「最良設定」と GC 曲線から、裁定した W3 上位２候補が消える。**推奨:** R4 専用の固定経路で W3 上位２点と control を W4 の J2 条件に渡す。

**B3｜should｜build 単価からの walltime 見積りは過小になり得る。** [analysis.py:139](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/tools/vhash_cicada_tuning/analysis.py:139) は J0 の各 build 秒を並列レーンへそのまま配るが、J0c は２ build・各 `-j 24`、J1 の７ build 並列なら各 build の `-j` は小さくなる。[driver.py:438](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/tools/vhash_cicada_tuning/driver.py:438)。**成果物への影響:** 80 node 分の計測枠を過小判定すると、後半の J2 条件が欠ける。**推奨:** J1 の実際の並列数で build 単価を再確認し、親が J0 実 Elapse・40 分予約を含めて投入前に再計算する。現時点の J0/J0b は build 失敗による Elapse 18 秒・32 秒で、run 単価には使えない。J0c は点検時に32行まで進み、完了 Elapse は未取得だった。

**B4｜should｜J2 は既定で５ job になる。** [driver.py:139](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/tools/vhash_cicada_tuning/driver.py:139) は W1〜W5 ごとに job を作るが、裁定は J2 を最大４ job と記す。通常の J1 は計486 run・27 build、J2 は rr50@1M 追加時に最大312 run・20 buildとなる。W5 欠測でも J2 は最大276 run・16 build。**成果物への影響:** job 数と依存準備費を少なく見積もり、予算判断が変わる。**推奨:** W5 を W2 job に含めるか、５ job として事前登録の予算表を訂正する。R1〜R4 は条件削減策だが、実 Elapse と並列 build 単価が無い段階では「足りる」と判定できない。

**B5｜should｜compile command 照合が対象 executable に限定されていない。** [driver.py:66](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/tools/vhash_cicada_tuning/driver.py:66) は file 名が一致する全 command を検査する。J0b の manifest には同じ `transaction.cc` と `util.cc` が複数回記録されており、対象外 target の command も混じる。**成果物への影響:** 対象 target の command 欠落を別 target で埋める、または対象外 target の変更で有効 build を無効にする可能性がある。**推奨:** `ycsb_cicada.exe` の object path に属する３ TU を特定して照合する。

**B6｜should｜絶対 throughput の median が最良結果に無い。** [analysis.py:128](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/tools/vhash_cicada_tuning/analysis.py:128) は control 比の score と best を返すが、裁定が併記を求める各条件の TPS median は返さない。図は [plot_vhash_cicada_tuning.py:58](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/tools/plotting/plot_vhash_cicada_tuning.py:58) で mean を描く。**成果物への影響:** 一次資料の「最良設定の絶対 TPS median」を summary・図から直接転記できない。**推奨:** J2 の条件別 median を summary に加え、図の mean と統計量の違いを明記する。

**B7｜should｜副軸の RSS が任意の候補を代表する。** [plot_vhash_cicada_tuning.py:151](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/tools/plotting/plot_vhash_cicada_tuning.py:151) は辞書順で最初の genome だけの maxrss を、候補名を示さず副軸に描く。**成果物への影響:** GC とメモリの関係が control または最良設定の値として読まれ得る。**推奨:** 描く genome を明示して凡例に記すか、副表示を削る。

**B8｜should｜開始前の依存が別 wave の private helper に残る。** [driver.py:173](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/tools/vhash_cicada_tuning/driver.py:173) に局所化はされているが、`_resolve_toolchain`・`_prepare_dependencies` の仕様変更で測定開始が止まる。policy JSON も重複キーを検出せず読む。[driver.py:181](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/tools/vhash_cicada_tuning/driver.py:181)。calibrator の解析・実行内部関数にも依存する。[analysis.py:9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/tools/vhash_cicada_tuning/analysis.py:9)。**成果物への影響:** 他 wave の変更で J0 が開始不能となり、N・最良設定・図が得られなくなる。**推奨:** 現 pin に必要な準備処理と policy 検証をこの driver 側の小さな関数に固定し、calibrator 依存は公開 API に絞る。

**B9｜nit｜設定 API が裁定より広い。** [driver.py:110](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/tools/vhash_cicada_tuning/driver.py:110) の任意 `k`・`gc_grid`・`reps`・`workloads` と CLI 引数は、事前登録した R1〜R4 以外の run も生成できる。**成果物への影響:** 実行者が未登録の条件表を作る余地があり、結果の範囲と費用が変わる。**推奨:** 固定の既定計画と R1〜R4 だけを選べる形に縮める。`reject_holdout_ratio` とその単独 test は固定 workload の実行経路では到達しないため削除可能。一方、compile binding、欠測検出、実 Figure の重なり検査は成果物の信頼性に直結し、削れない。

## 裁定・事前登録との照合

| s4-ruling 項目 | 判定 |
|---|---|
| A-F1：rr50 全24点×GC３点、他は選抜範囲を限定 | **実装どおり**。限定した結論名は一次資料で必要。 |
| A-F2・R-add1：compile command＋binary SHA、表示行を使わない | **ずれ**。値と SHA は記録するが、command の target 限定が不足（B5）。 |
| A-F3：J1 探索、J2 のみで最良・集合 | **実装どおり**。 |
| A-F4・R-add4：記述的候補集合、session不足でも best は出す | **実装どおり**。ただし絶対 TPS median は不足（B6）。 |
| A-F5：公式 floor・compare・採否へ接続しない | **実装どおり**。 |
| A-F6：W5 は worker 1・固定1 ms の別診断 | **実装どおり**。実測の W5 は compile 不能で欠測となる見込み。 |
| A-F7：perf は J0 較正のみ | **実装どおり**。 |
| A-F8：rep ごとの固定 seed 並べ替えと run 状態記録 | **実装どおり**。 |
| A-F9・plan P4：飽和候補／RSS 下限／perf 不可を区別 | **実装どおり**。ただし N 未決定で workload だけを除く経路は**未実装**。[driver.py:533](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning/tools/vhash_cicada_tuning/driver.py:533) は J0 全体を停止する。 |
| A-F10：正しさ未検証と明記 | **実装どおり**。trace build での後続検査は scope 外。 |
| B-B1：rr50 の N≠1M なら共通点を追加 | **実装どおり**。 |
| B-B3・B-B9：build 単価、予算、縮小梯子 | **ずれ**。単価記録はあるが５ job と build 並列度の見積り問題があり、R4 は B2 の状態。予算の最終判定は親の手作業に残る。 |
| B-B8・plan P8：private helper を一箇所に閉じ、policy と configure を持つ | **実装どおり**。変更耐性の弱さは B8。 |
| R-add2：`-j` 分割、静定180秒、perf parser | **実装どおり**。 |
| R-add3：J0 walltime 30分 | **実装外の投入設定として実行**。J0c spec の投入ログは30分。 |
| 変異 M1〜M9 | 対応する検査は存在する。**変異実走は未確認**。 |
| 図２種と欠測部分集合 | **ずれ**。固定５ workload 描画が B1 に該当。 |

## 正しいと確認した点

J0c の通常 build は成功し、待機 build は `thid`・`clock_delay` 未定義で失敗した。修正後 driver はこの失敗を W5 欠測として記録し、通常型の走を続けている。J1 の control 同席、J2 の control 比、標本 CV、perf なしの順位付け、raw run と出力の create-only 方針は裁定に沿う。

新しい inventory test の変更は２行で最小限。測定 test は stub 主体、作図 test は実寸 Figure ２枚を保存するため費用はあるが、静的点検から全体５分超過とは判断できない。今回は指定どおりテスト・計測を実行していない。

## 総括

この driver は探索用の診断値と GC 曲線を得る土台になる。ただし、**W5 欠測時の図生成**と**R4 の W4 候補生成**は成果物を直接欠かすため修正が必要。論文の構成 A・§28.1 には rr50 の共通1M点と J2 曲線を使えるが、他 workload は「GC=10 で選抜した候補中の観測最良」、W5 は欠測、全値は正しさ未検証と一次資料に明記する必要がある。J0c の完了 Elapse と workload 別単価が出るまで、120 node 分の線を満たすとは確定できない。