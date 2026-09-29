# 段 4 裁定 — [T-2902] Cicada 観測最良設定の正しさ検査 (md_20)

入力: s1-brief.md、plan.md (段 2)、consult-a.md・consult-b.md (段 3)。裁定 inbox (`/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/`) の最新 `2026-09-29-interactive-evolution-verdicts.md` に Cicada / VHash / T-2902 の語なし。local main は wave 開始時の 8fe87f852 から不動 (22:2x JST)。

## 所見の裁定

| 所見 | 判定 | 採否 | 対処 |
|---|---|---|---|
| plan 異議 1・A1・B3 (選択→登録の窓、inline 件数は到達確認にすぎない) | real | 採用 | R3 の忠実性診断 (選択時の版・登録時の版・commit 時の版の 3 点比較、未来版の登録検出) |
| plan 異議 2・A3 (mismatch 0 は安全の証拠でない) | real | 採用 | R3 で選択時の値を足して窓を狭め、R6 で診断値は「0 でなければ不合格」、0 を安全の証明とは書かない (R8) |
| A2 (body を観測しない・再読は R を増やさない) | real | 採用 | R8 の限界として明記 |
| A4・B7 (正例の帰属が弱い・正例 run 自身の整合) | real | 採用 | R5 |
| A5・B2 (SINGLE_EXEC と実行時 flags の束縛) | real | 採用 | R2 |
| A6・B1 (小走行の陰性を主比較条件に広げる) | real | 採用 | R8 (cell 単位の結論、1M・t48・3 秒は未検査) |
| B4 (正例が BEST100 に届かない) | real | 採用 | R4 に BEST100 の正例を追加 |
| B5 (見積り未成立) | real | 採用 | R4 (L0 実測で残りを積算してから投入) |
| B6 (先行実装の過多) | 一部 real | 一部採用 | TRACE=0 同一性は落とす (R7)。1 軸切り分けの自動 mode は作らず CUSTOM spec で表す (R6)。忠実性診断は主判定の証拠なので残す |
| plan 異議 6 (BACK_OFF の後勝ち) | real | 採用 | R2 |
| plan 異議 4 (既定での正例実績は BEST の代用にならない) | real | 採用 | R4・R5 |
| plan 異議 5 (P4 は必要条件でない) | real | 採用 | R7 |

## 裁定

- **R1 所有と単位。** 実装単位は 1 本 (unit U、worktree `/work/1/SFC/tanab/izanagi/.codex/worktrees/cbv-u`、branch `dev-wave-cbv-u`)。Codex author が編集してよいのは untracked の `.cicada-launcher/launch_cicada_run.py` (md_17 の写しを親が置く) と `.cicada-launcher/diag-cicada-inline-fidelity.patch` (新規) の 2 つだけ。親が repo 外 (job dir) へ退避して使う。repo の tracked file (patches・判定器・external/ccbench の gitlink) は変えない。instr patch の bytes 不変 (D2294)。
- **R2 build と実行時の束縛。** build spec ごとに五軸 (BACK_OFF・INLINE_VERSION_OPT・INLINE_VERSION_PROMOTION・REUSE_VERSION・WRITE_LATEST_ONLY) を持つ。configure argv は共通引数から `-DCCBENCH_BACK_OFF=` を取り除いてから五軸と `CCBENCH_SINGLE_EXEC=0` を一度ずつ足し、同じ CMake key の重複を起動前に拒否する (後勝ちに頼らない)。CMake cache で `CCBENCH_BACK_OFF`・`CCBENCH_INLINE_VERSION_OPT_CICADA`・`CCBENCH_INLINE_VERSION_PROMOTION`・`CCBENCH_REUSE_VERSION`・`CCBENCH_WRITE_LATEST_ONLY`・`CCBENCH_SINGLE_EXEC`・`CCBENCH_TRACE`・`CCBENCH_ADD_ANALYSIS` を照合し、`ycsb_cicada.exe` target の 3 TU (transaction.cc・util.cc・ycsb_cicada.cc 各 1 件) の compile command の -D で `TRACE=1`・`ADD_ANALYSIS=0`・`SINGLE_EXEC=0` と五軸を照合する (md_11 `check_compile_commands` と同型、-D の重複拒否)。binary sha256 を記録。実行時は cell の全 flag (`ycsb_tuple_num`・`ycsb_rratio`・`ycsb_max_ope`・`ycsb_zipf_skew`・`ycsb_rmw`・`thread_num`・`extime`・`gc_inter_us`・`group_commit=0`・`clocks_per_us`) を argv に明示し、stdout の `#FLAGS_*` 行を argv と照合する (md_11 `check_flags` と同型)。照合結果と stdout / stderr の sha256 を run record に残す。照合が 1 つでも外れた run は判定対象外 (不成立) とする。
- **R3 忠実性診断 (repo 外、全検査 build に重ねる)。** `diag-cicada-inline-fidelity.patch` を instr patch の後に、この wave の全ての検査 build (BEST・BEST100・CTRL・正例) に当てる。追加は `#if TRACE` の内側だけ (repo 外なので内側で `#if INLINE_VERSION_OPT` を使ってよい。OPT=0 でも compile できること)。trace の C / R / W / E 行の中身・順序は 1 byte も変えない。
  - 選択時の版: `read_internal` で版の選択を決めた比較に使った wts の値 (scan の最後の `ldAcqWts()` の値、aborted を飛ばした場合は飛ばした後の版で読み直した値) を保存し、read set の要素 (直後に登録した要素) に持たせる。stock の選択の判定・分岐は変えない (値を変数に受けるだけ)。
  - commit した txn の R ごとに数える: `R` (総数)、`R_INLINE` (選択した版が inline slot)、`SEL_REG` (選択時 ≠ 登録時 `trace_read_wts_`)、`SEL_COMMIT` (選択時 ≠ traceCommit 時の `ver_->ldAcqWts()`)、`REG_FUTURE` (登録時の wts > その読みの基準時刻 trts)。W ごとに `W`・`W_INLINE` (new_ver_ が inline slot)。終了時に stderr へ 1 行 `CICADA_DIAG_FIDELITY R=<n> R_INLINE=<n> W=<n> W_INLINE=<n> SEL_REG=<n> SEL_COMMIT=<n> REG_FUTURE=<n>` (OPT=0 の build では `R_INLINE`・`W_INLINE` を `na`)。語 `IZANAGI_` を含めない。
  - 根拠: wts は書き手ごとに一意で、slot の再利用は wts を上書きするので、選択時と commit 時の値が一致すれば、その読みの版はその間に別の版へ再利用されていない (書き換えの途中の瞬間は除く — R8 の限界)。
- **R4 matrix と計算。** 共通: YCSB、skew 0.9、rmw 0、extime 1、group_commit 0、TRACE=1、pin C + instr + diag (+ 壊し)。
  - **L0 (1 job):** BEST・CTRL の W2 (rr50・max_ope 10) tuple 200・t4・GC 10、BEST100・CTRL の W4 (rr95・max_ope 100) tuple 200・t4 (BEST100 は GC 1000、CTRL は GC 10)、正例 P-BEST (BEST + skip-read-recheck) の W2 tuple 200・t4・GC 10。目的は build 束縛・flag 照合・忠実性診断・判定器到達・単価。
  - **J1 (L0 合格後、workload ごとに job を分けて複数ノードへ):** W1 (rr5)・W2 (rr50): BEST の GC {100, 10} × t{4, 48} と CTRL の GC 10 × t{4, 48}。W3 (rr95): BEST・CTRL の GC 10 × t{4, 48}。W4: BEST100 の GC {1000, 10} × t{4, 48} と CTRL の GC 10 × t{4, 48}。tuple はすべて 200。W4 の run の commit 数が 1,000 未満なら、同じ build・同じ flag で tuple 1,000 の run を同じ job の追加 run として加える (事前登録した第二尺度、他の cell で代用しない)。正例: P-BEST の W2 tuple 200・t48・GC 10、P-BEST100 (BEST100 + skip-read-recheck) の W4 tuple 200・t4・GC 1000。L0 と重複する cell は再走しない。
  - **J2 (尺度確認、条件付き):** md_11 と同じ tuple 1M・t48 (extime 1)。L0 / J1 の trace 行数と判定器秒数から 1 run の判定器所要を予測し、600 秒未満かつ全 job の Elapse 合計 (実測 + 予測) が 6,000 秒未満のときだけ、W1〜W3 の BEST・CTRL (GC = md_11 最良値 / 10) と W4 の BEST100・CTRL を投げる。満たさなければ投げずに「未検査」と書く。
  - **予算:** 全 job の Elapse の総和を 2 node 時間 (7,200 秒) 未満に保つ。L0 の実測後に残り (J1・正例・J2・切り分けの予備 900 秒) を積算してから投入する。判定器の timeout は雛形の 900 秒を保つ (timeout した run は不成立)。
- **R5 正例の帰属と分類。** 壊しの事象行 (`CICADA_BREAK_EVENT slug=skip-read-recheck tx_wts a_wts b_wts key`) に対し、帰属 witness = 判定器の代表 witness の巡回のうち、(i) 事象の txn (C 行の版 = tx_wts) を始点とし、(ii) 事象の key 上の rw 辺で、(iii) 辺の読んだ版 = a_wts、かつ (iv) 辺の終点の txn がその key に書いた W の版 = b_wts であるもの。分類「期待した経路で検出」= non-serializable かつ帰属 witness ≥ 1、かつ正例 run 自身の integrity 数値項目 0・C 行 = commit 数・異常終了なし・flag 照合一致・事象行を打ち切らず全件保存、かつ同じ cell の stock 対照 (BEST なら BEST、BEST100 なら BEST100) が R6 で合格。他は「検出したが帰属不能」「盲点」「未発火」(md_3 と同じ語)。正例が示すのは「read set 再検査を壊した履歴をその設定の trace で検出できる」ことまでで、inline slot の ABA や誤記録の検出力は未検査と書く。
- **R6 合否 (結果を見る前に固定)。** stock の run の合格 = rc 0・timeout なし・R2 の照合一致・巡回 0・integrity 数値項目 (md_3 の 11 項目) 全 0・C 行 = stdout の commit 数・全 W > initial_wts・`CICADA_TRACE_READ_WTS_MISMATCH n=0`・`SEL_REG=0`・`SEL_COMMIT=0`・`REG_FUTURE=0`。判定語は「その条件で巡回なし (上限 indeterminate)」。巡回が出た設定はその時点で主比較の相手として失格とし、witness (巡回の txid 列・辺の種別・key・読んだ版・次の版・対応する C/R/W 行) を構造化して残し、plan §7 の表の 1 軸 build (BEST なら CTRL+B0・CTRL+O1、BEST100 なら CTRL+B0・CTRL+R0) を元の巡回 cell だけで追加走行する (起動器の CUSTOM spec で表し、自動展開 mode は作らない)。診断値だけが 0 でない run は「診断異常」とし、合格にも non-serializable にも数えず、raw と条件を残して機序は未解明と書く (その設定は検査通過と書かない)。
- **R7 TRACE=0 同一性。** この wave では取らない (性能値を出さず、instr patch の bytes も変えないため判定の必要条件でない)。BEST / BEST100 の CMake 値での同一性は未確認と一次資料に書く。
- **R8 書き方。** 結論は実走した (genome・workload・tuple・thread・GC・extime) の cell ごとに書く。md_11 の主比較条件 (1M・t48・extime 3) は J2 を走らせても extime が違うので「同じ条件で検査済み」と書かない。trace が記録するのは read set に登録された版への依存であり、同一 txn 内の再読は R を増やさず、読んだ中身 (body) は観測していない。忠実性診断の 0 は、選択時点と commit 時点の 2 点で版の再利用が無かったことを示すだけで、再利用の書き換えの途中の瞬間に読んだ場合は区別できない。certified とは書かない。
- **R9 trace patch の修正。** L0 / J1 で instr patch に記録されない経路が実測で見つかった場合だけ検討する。instr patch の bytes を変えることは並走 wave (md_14・md_21 ほか) の重ね patch に波及するので、その場合は修正せず裁定パッケージとして一次資料とユーザーへ返す。
- **R10 変異 matrix。** repo の実装面の差分がゼロなので免除 (DW-S04)。起動器の帰属関数と照合関数は、Codex author が手作りの入力で正例・負例 (b_wts 不一致で帰属しない、flag 不一致で不成立) を実走して報告する。判定の検出力の実証は R5 の正例。
- **R11 実測環境。** Pegasus 計算ノードに generic dispatch で送る。job ごとに計測用の detached checkout を分ける (md_17 と同じ)。login node では build も計測もしない。
