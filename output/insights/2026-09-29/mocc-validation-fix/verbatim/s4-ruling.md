# 段 4 裁定 — [T-2872] MOCC validation 修理 (dev-wave-mocc-validation-fix)

入力: brief `s1-brief.md`、plan `out/s2-plan.md`、相談 A `out/s3-consult-A.md` (並行性の正しさ)、相談 B `out/s3-consult-B.md` (測定・記録・過剰)。3 本とも `check_codex_output.py` rc=0。
裁定 inbox の再走査 (22:1x JST): wave 開始後の更新は `2026-09-29-interactive-evolution-verdicts.md` (21:47、開始前・MOCC 無関係) だけ。local main は `8fe87f852` のまま。

## 所見の裁定

| # | 出典 | 所見 | 判定 | 採否・処置 |
|---|---|---|---|---|
| 1 | plan §1・A | 案 A (lock 読みの後に版を再読、`check` と違えば既存の版不一致経路で abort、`max_rset_` は `check`) | real | 採用 (R1) |
| 2 | plan §1・A | 版の単調性は tid 31 bit・epoch 32 bit の周回と record 再生成まで含めると無条件に言えない | real | 採用。記録は「通常の連続 publish で前進する範囲」と限定 |
| 3 | A | Silo 同値は「lock 読みの瞬間に成立する検査条件」の同値で、全スケジュールの受理一致ではない (案 A は L 後の publish で余分に abort しうる) | real | 採用。記録の言い方を限定、余分な abort は P の commit 数と再読 abort 件数で観測 |
| 4 | A | `max_rset_ = max(max_rset_, check)` に反対する根拠なし | refuted (攻撃不成立) | plan どおり |
| 5 | A | cold read の torn read 経路は別に残る。本 wave で直す必要なし | real (scope 外) | 実装しない。insight に「torn read 全般は直していない」と書く |
| 6 | A | hot read・自己 write・DELETE/INSERT・node set・MQLOCK へ証明を広げない | real | 記録で限定 |
| 7 | A | 修理後の commit 側 class A=0 はほぼ構造上の帰結 (恒真に近い)。修理の再読による abort 件数を別に記録せよ | real | 採用 (R6 の計器に再読 abort の計数を足す) |
| 8 | B must | F の G2 が 0 件のときの書き方が brief と plan で 2 通り | real | R6 で「0 件なら同時刻の G2 対照は不成立と報告、延長しない」に統一。完了判定から F の G2 を外す |
| 9 | B | F 側・N・P を X と同数にする必要はない (費用) | real | 採用 (R6: T_F 56、N・P 各 28) |
| 10 | B must | smoke 外挿で固定費を二重計上 | real | 採用 (R8: 固定費 B と batch 費 M を分けて測り合算) |
| 11 | B | F/X の順序交替を実装条件に | real | 採用 (R7) |
| 12 | B | X の V3 は F と母集団が違う。class B の F/X 率比較をしない | real | 採用 |
| 13 | B must | runner の arm 別 source の保証 (checkout・HEAD 照合・build と verifier の両方へ arm の source) | real | 採用 (R7) |
| 14 | B must | D297 の rc=1 は他の失敗と区別できない。stderr の理由を記録、結果名は「D297 不合格 (意図した修理差分)」 | real | 採用 (R5) |
| 15 | B nit | format の本判定は CI image :latest、login は補助 | real | 採用 (R4) |
| 16 | B | 棚卸しは C/F/X の 3 列、rc=0 の意味は静的判定・未確定は未確定と書く | real | 採用 (R9) |
| 17 | plan §7・B | `broken-mocc-lockskip-validation.patch` は read set の lock 検査ではなく write set の施錠を飛ばす | real (親の brief の読み違いではないが、名前からの誤読を防ぐ) | 棚卸しの表に明記 |
| 18 | plan §2 | 後段の `#line` 値は据え置く | real | 採用 (R2) |

## 実装方針 (plan v2)

- **R1 修理:** F の `cc/mocc/transaction.cc` の read set 検査 (1031〜1062) で、1059 行 `#endif // RWLOCK` の後、`max_rset_` の更新の前に plan §1 の文 (版の acquire 再読 → (epoch, tid) が `check` と違えば `failed_verification_ = true`・`status_ = aborted`・`ADD_ANALYSIS` の `local_validation_failure_by_tid_` 計上・`return false`) を挿入し、`max_rset_` の右辺を `check` にする。変数名は `check_after_lock` 相当の意味の通る名前。短い英語コメント 1〜2 行で「版と lock を別の load で読むので、lock の後に版を読み直す」理由を書く。他の行 (trace 区間・writePhase・read phase・lock 検査の既存経路) は 1 byte も変えない。clang-format 14 で整形済みの形にする。
- **R2 `#line`:** 既存値は据え置く。新たな `#line` は足さない。
- **R3 commit:** F の直接の子 1 commit、変更 path は `cc/mocc/transaction.cc` だけ、mode 不変。件名 `fix(mocc): recheck the read-set version after the lock check in validation` (親が最終決定)、本文は plan §3 を基に英語、trailer は Codex author・reviewer・Claude manager (D2293 の先例)。author 名は先例と同じ `thawk105`。
- **R4 CI:** format の本判定 = CI image `:latest` (14.0.6) で `git ls-files -- cc include common | grep -E '\.(cc|hh|cpp)$' | xargs clang-format --dry-run --Werror`、X の clean checkout、対象 file 数・rc・version を記録。login の 14.0.0 は補助。build = CI image `:ci` を計算ノードで `apptainer --userns`、先例 `run_ci_build.sh` の親 OID 固定を F に替えた改作 (Codex author)、CI argv + offline 供給 4 引数、「CI image と CI の build 手順による手元通過」と記録。image は先例 job dir の sif を sha256 照合して再利用。
- **R5 D297:** F → X を GCC 11.4・12.3 で (header 用 4 引数付き、先例 `run_judge.sh` の改作)。期待 = 両方 rc=1、stderr に `cc/mocc/transaction.cc` の TRACE=0 正規化 preprocess 出力の不一致。記録: `git diff-tree --raw -r F X` の path = `cc/mocc/transaction.cc` だけ・header 0、F→X の source diff = 修理 hunk だけ。結果名「D297 不合格 (意図した修理差分)」。include 活性の合格・header 分岐の合格は名乗らない (検査器は先行する不一致で止まる)。rc=1 でも stderr の理由が違えば停止して調べる。
- **R6 実測の事前登録 (本裁定で凍結、結果を見て変えない):**
  - cell: 48 thread・1,000,000 record・rr95・rmw 0・max_ope 10・zipf 0.9・3 秒、stock genome (`BACKOFF_FIXED=-1,BACK_OFF=1,KEY_SORT=0,TEMPERATURE_RESET_OPT=1`)、Release・gcc-11、template `patches/silo-backoff-fixed.patch`。
  - arm: T_F・T_X (TRACE=1 + 各版の計器、verifier で検査)、N_F・N_X (TRACE=0 + 計器)、P_F・P_X (TRACE=0 素)。F = `25898d00…`、X = 修理 commit。
  - 反復: 2 job × 14 batch。1 batch = T_X 4・T_F 2・N_F 1・N_X 1・P_F 1・P_X 1。合計 T_X 112・T_F 56・N_F 28・N_X 28・P_F 28・P_X 28。延長しない。
  - 計器: F 版 = 切り分けの計器と同じ意味 (Vmid は版比較通過直後・lock 読みの前、V3 は `max_rset_` の後)。X 版 = Vmid・lock 読みの位置は F と同じ、修理の再読の不一致 abort を thread ごとに数える (**recheck_abort**)、V3 は修理の再読を通過した後。class A = commit した取引で lock 未施錠かつ Vmid≠V1。class B は各版内の補助観測で F/X の率を比べない。
  - **判定 (成功 = 3 条件すべて):** (a) R0 = 0 (T_X・N_X の全走で benchmark・verifier の失敗・溢れ・TSV 欠落なし)、(b) T_X の G2 = 0/112、(c) T_X と N_X の commit 側 class A の合計 = 0。
  - **失敗時:** (b) か (c) が破れたら修理は不十分とみなし、push 依頼を出さず停止して調べる (規律 2)。(a) の判定不能は該当走を判定不能と記録し、延長で埋めない。
  - **同時刻の対照 (報告のみ、完了判定に入れない):** T_F の G2 件数 (0 件なら「同時刻の G2 対照は不成立」と書く、延長しない。旧率 5/112 なら 56 走で 0 件の確率 ≈ 7.7%)。N_F・T_F の commit 側 class A (0 なら計器の感度の対照が不成立と書く)。X の recheck_abort 件数 (修理が割り込みを実際に弾いた観測)。
  - **性能の観測:** P_F・P_X の commit 数を並べるだけ (headline・性能主張に使わない、規律 1)。N と T の commit 数も参考に並べるが計器・trace の観測者効果込みと書く。
- **R7 runner:** 切り分けの runner を Codex author が改作 (repo 外)。各 arm に source full OID、clean clone を detached checkout して HEAD の完全一致を照合、template → 計器を各々 `git apply --check` → `git apply` (失敗で停止)。macro off の前処理一致は同じ commit 内だけ (P_F source 対 N_F source、P_X 対 N_X)。build と verifier の両方へその arm の source を渡す。arm 別 source SHA・計器 patch SHA・binary SHA・実行順を結果に残す。batch 内の F/X 対は batch ごとに先後を入れ替える。verify は batch の benchmark 後に T 6 本を並列。固定費 (build) と batch 費 (benchmark・verify) を分けて時間を記録。
- **R8 費用:** smoke = 1 job × 1 batch (本走と同じ argv で batches だけ 1)。見積り = 2 × 固定費 B + 28 × batch 費 M。wave の計算合計 (D297・CI build・smoke・本走・受入) が 2 node 時間以上なら、本走の投入前にユーザー確認を取る。
- **R9 棚卸し:** 10 本を X でも `git apply --check`。表は C・F・X の 3 列 (C→F で外れた 2 本、C から外れている計器 3 本、F→X で新たに外れたもの)。X で当たる patch は macro 有効時に狙いの経路が残るかを source で静的に判定し、決められないものは「意味未確定」。patches/ は変えない。F=0→X≠0 が出たら扱いを本裁定の追補で決める (検査を甘くする方向は取らない)。
- **R10 変異:** izanagi の実装面の差分は 0 (docs のみ) なので変異 matrix は免除 (DW-S04)。修理の効き目の負例は「修理を外した版」= 修正前 F の arm (N_F・T_F で class A > 0 を期待) として R6 に事前登録した。受理集合を縮める修理の過剰拒否は、P_X の commit 数と recheck_abort 件数で観測する (閾値は置かない)。

## 実装単位
- 単位 A (子木 moccfix-a、clone `output/runs/moccfix/ccbench`、所有 = `cc/mocc/transaction.cc` だけ): R1。
- 単位 B (子木 moccfix-b、所有 = repo 外に持ち出す使い捨て script 群を子木の `output/runs/moccfix-b/` に書く): 計器 2 本 (F 版・X 版)、runner と arm 定義 (R6・R7)、CI build script と format script の改作 (R4)、D297 判定 script の改作 (R5)。X の OID が要るので A の commit 後に投入。
- 親: branch・commit・bundle、CI・D297・smoke・本走の投入、棚卸し、記録。
