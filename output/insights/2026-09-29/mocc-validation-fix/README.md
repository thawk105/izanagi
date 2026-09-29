# [T-2872] MOCC の validation の隙間を CCBench で直した — lock 状態を読んだ後に版を読み直し、最初の版と違えば abort する 1 commit (`f4a5169e`、branch `izanagi-mocc-validation-fix`、F `25898d00` の子)。上流 CI 2 本を CI image で手元通過し、D297 は意図した修理差分で不合格、trace build の事前登録 112 走で G2 0 件・commit 側 class A 0 件 (同時刻の修正前は G2 8/56 走・class A 1,415 件)

authority: none
default_effect: no-state-change

- 依頼 (逐語): `verbatim/request.md`。段 1 brief: `verbatim/s1-brief.md`。段 4 裁定と事前登録: `verbatim/s4-ruling.md` (R6 が本走の条件)。段 6 裁定: `verbatim/s6-ruling.md`。開始 gate: `verbatim/startup-gate.log` (rc=0、起点 local main `8fe87f852`)。
- 一次資料: `output/insights/2026-09-29/t2872-mocc-g2-split/README.md` (欠陥の切り分け)。先例: `output/insights/2026-09-29/t2854-ccbench-format-ci/README.md` (F と CI の手順)。裁定: D2277 項 1・2、D2293、D297 / D2255 / D2275、D16・D18・D20。
- **izanagi repo のコード変更なし。gitlink・`CCBENCH_FULL_SHA`・`CURRENT_PIN`・patches/ は不変。** CCBench の変更は submodule の新 branch の 1 commit (Codex author、commit は親)。計器・runner・投入 script は repo 外 (job dir `/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/`、sha256 は `verbatim/job-dir-sha256.md`)。
- 本文は**非 certifying の観測記録**であり、headline・certified 選択・floor・oracle・fitness の根拠に使わない。t2849・t2868・t2872 の値と判定は変えていない (規律 2・7)。trace build (正しさ) と trace 無し build (commit 数) は別 build・別集計 (規律 1)。
- 用語: 「F」= 整形 commit `25898d00` (現 pin C `68106660` の 4 commit 後、wave 開始時点で GitHub 未 push)。「X」= 本 wave の修理 commit `f4a5169e`。「割り込み」「class A / B」「Vmid / V3」は一次資料 §3 と同じ意味。「recheck_abort」= X の修理の再読で版が違って abort した件数 (計器が数える)。

## 0. 結論

| 項目 | 結果 | 節 |
|---|---|---|
| 修理 commit | X = `f4a5169ede52630d9357444e3412ffe9aed7c78f` (branch `izanagi-mocc-validation-fix`、F の直接の子、`cc/mocc/transaction.cc` の 1 hunk、Codex author・commit は親)。lock 状態を読んだ後に版を読み直し、最初の版と違えば abort、`max_rset_` は検査した版から取る | §1 |
| 上流 CI 2 本 | format: CI image `:latest` の clang-format 14.0.6 で 213 file・rc=0 (login 14.0.0 も rc=0)。build: CI image `:ci` (GCC 13.3) と CI の手順で configure・build とも rc=0。**CI image による手元通過で、GitHub Actions の緑ではない** | §2 |
| D297 (F → X) | **D297 不合格 (意図した修理差分)**: GCC 11・12 とも rc=1、理由は `cc/mocc/transaction.cc` の TRACE=0 正規化 preprocess 出力の不一致。差分は 1 path・1 hunk・header 0。修理は TRACE=0 を意図して変えるので構造上の不合格 | §3 |
| trace 実測 (事前登録 R6) | **成功 (3 条件すべて)**: 判定不能 0、修正後の trace build の G2 **0/112 走** (95% 上限 3.2%)、修正後の commit 側 class A **0 件** (trace 有り 112 走 + trace 無し 28 走)。同時刻の修正前 F: G2 **8/56 走** (14.3%、区間 6.4〜26.2%)、commit 側 class A 1,415 件。0/112 対 8/56 は両側 Fisher p = 1.1×10⁻⁴ | §4 |
| 修理の再読による abort | 修正後の再読で版が違って abort した件数 (recheck_abort) 6,368 件。1 走あたり trace 無し 159.9 件で、修正前 F が割り込みを受けたまま commit した件数 (class A + B) の 1 走あたり 167.1 件と同じ規模 | §4 |
| 性能の観測 (規律 1、主張に使わない) | trace 無し・計器無しの commit 数 (3 秒、各 28 走): 修正前 7,200,449、修正後 7,241,787 (比 1.006、差 41,338、標準誤差 25,913)。修理で commit 数が目立って下がる様子は見えない | §4 |
| patch 棚卸し | F → X で新たに厳密適用から外れた patch **0 本** (10 本とも F と X で同じ結果)。F で外れる 5 本は修理と無関係 | §5 |
| push | 人間の手番。branch `izanagi-mocc-validation-fix` (X) を push し、GitHub の CI 緑を確かめてもらう。gitlink は進めていない | §6 |

## 1. 修理の中身 (`verbatim/F-to-X-diff.md`、`verbatim/mk-X.log`)

- X は F の直接の子、変更 path は `cc/mocc/transaction.cc` だけ (mode 不変、1 hunk、+16 −1)。validation の read set 走査で、既存の版比較 (F 1032〜1043 行) と writer lock の検査 (1045〜1059 行) は 1 byte も変えず、その後ろに次を足した。
  - 版を `__atomic_load_n(..., __ATOMIC_ACQUIRE)` で読み直し (`check_after_lock`)、(epoch, tid) が検査した版 `check` と違えば、既存の版不一致と同じ状態 (`failed_verification_`、`status_ = aborted`、`ADD_ANALYSIS` の `local_validation_failure_by_tid_`) で abort する。
  - `max_rset_` は 3 回目の load ではなく検査した版 `check` から取る (Silo の read set 検査 `cc/silo/transaction.cc` 453〜478 行が 1 回の load で版比較・lock bit・`max_rset_` を賄うのと同じ扱い)。
  - 理由を書く英語コメント 2 行。`#if TRACE` 区間・既存の `#line` の値・writePhase・read phase は不変。新たな `#line` は足していない (修理から次の `#line 1158` までの論理行番号が 15 進むだけで、`ERR` の `__LINE__` (521・1289 行) には届かない)。
- 形の選択 (段 4 R1、段 3 相談 A): 案 A (lock の後に版を再読) を採った。既存条件に条件を足すだけなので、同じ観測列で元のコードが拒否した取引を新たに受理しない。案 B (lock を先に読み版は 1 回) も Silo の考え方に対応するが、lock を読んだ後に他者が施錠してまだ公開していない実行を受理しうるので、依頼の「受理集合を縮める方向だけ」を字義で満たさない。
- 言える範囲: 修理後に通過する取引では、lock を読んだ瞬間に「版が読んだ版のままで、他者の writer lock が無い」が成り立つ (版が record ごとに前進し同じ値へ戻らない範囲で)。これは lock を読んだ瞬間の検査条件が Silo の 1 word 検査に対応するという意味で、全スケジュールの受理結果が Silo と一致するという主張ではない (案 A は lock 読みの後の publish でも abort するので余分な abort がありうる)。`Tidword` の tid 31 bit・epoch 32 bit の周回や record の再生成まで含む ABA の不在は証明していない。
- 直していないもの: read phase の cold 読みの torn read の経路 (T-2774 §3 (i))、hot record の read lock・自己 write・INSERT/DELETE・node set・MQLOCK への論証の拡張 (一次資料 §2 の被覆境界と同じ)。
- commit message は上流の流儀の英語 (件名 `fix(mocc): recheck the read-set version after the lock check in validation`)、trailer は Codex author・Codex reviewer・Claude manager (D2293 の先例と同形)。段 6 レビュー A が hunk に所見なし、message の 2 箇所 (観測を片側の辺と書く、`max_rset_` の入力の変化を書く) を指摘し、親が直した。

## 2. 上流 CI 2 本 (CI image と CI の手順による手元通過。GitHub Actions の緑ではない)

| CI | 手順 | 結果 | 証拠 |
|---|---|---|---|
| format | X の clean checkout で `git ls-files -- cc include common \| grep -E '\.(cc\|hh\|cpp)$' \| xargs clang-format --dry-run --Werror`。本判定 = CI image `:latest` (clang-format 14.0.6)、補助 = login の 14.0.0 | 213 file、両方 rc=0 | `verbatim/evidence/format-ci-X.log` |
| build | 計算ノードで CI image `:ci` (GCC 13.3.0、cmake 3.28.3) を `apptainer --userns`。CI の configure argv (`-DCMAKE_BUILD_TYPE=Release -DENABLE_SANITIZER=OFF` + ccache launcher) と `cmake --build build -j 48` に、offline 供給の 4 引数 (`FETCHCONTENT_FULLY_DISCONNECTED` と依存 3 本の source dir、pin は ThirdParty.cmake の TAG と照合) だけを足した | configure rc=0 (1 s)、build rc=0 (23 s)、全 protocol。警告は第三者 masstree の分だけ | request 36272.nqsv (Elapse 33 S)、`verbatim/evidence/ci-build-report.json` |

- CI との差は先例 (t2854 §3) と同じ: 依存の供給 (手元 cache から clean clone)、空の ccache、runner の資源、image の取得時点。build は先例の Codex author の script を親 OID = F に改作したもの。

## 3. D297 (F → X) — 「D297 不合格 (意図した修理差分)」

- 検査器 `tools/check_trace0_preprocess_identity.py` (main と同一 blob) を GCC 11.4・12.3 で、header 用 4 引数と `--expect-paths cc/mocc/transaction.cc` を付けて実行。両方 rc=1、理由は両方「TRACE=0 正規化 preprocess 出力が不一致: path='cc/mocc/transaction.cc'」(最初の macro context で停止)。`git diff-tree --raw -r F X` は `cc/mocc/transaction.cc` 1 path・header 0、F→X の source diff は 1 path・1 hunk (= §1 の修理 hunk)。request 36298.nqsv (Elapse 9 S)、`verbatim/evidence/judge2-report.json`・`verbatim/F-to-X-diff.md`。
- 読み方: 修理は TRACE=0 の翻訳単位を意図して変える本物の修正なので、TRACE=0 同一性の検査は構造上不合格になる。これは trace hook の混入ではなく修理そのものの差である (差分は §1 の hunk だけ)。**D297 の合格・include 活性の合格・header 分岐の合格は名乗らない** (検査器は先行する不一致で止まる)。
- 1 回目の判定 (36270、同じ結果) は判定 script が結果名を条件なしで付けていたので (段 6 S6-2)、直した script で取り直した値を記録に使う。
- **pin 前進への含意:** 実測したのは F → X で、現時点の X の修理差分は TRACE=0 を変えるので D297 は不合格になる。C → (F・X を含む前進先の tip) でも同じ修理差分を含む限り同じ理由で不合格が見込まれるが、前進先の tip では検査していない。扱い (例: C → F の合格 (D2293) と F → X の意図した差分の審査を分けて受け入れる、または pin 前進用の受理手順を裁定する) は gitlink 前進 wave で決める (§8 の起票)。

## 4. trace build の実測 (事前登録 R6)

- cell: 48 thread・1,000,000 record・rr95・rmw 0・max_ope 10・zipf 0.9・3 秒、stock genome (`BACKOFF_FIXED=-1,BACK_OFF=1,KEY_SORT=0,TEMPERATURE_RESET_OPT=1`)、Release・gcc-11、template `patches/silo-backoff-fixed.patch` (切り分けと同じ)。
- arm: T_F・T_X (TRACE=1 + 各版の計器、verifier)、N_F・N_X (TRACE=0 + 計器)、P_F・P_X (TRACE=0 素)。F 版の計器は切り分けの計器と同じ意味 (Vmid = 版比較の直後・lock 読みの前、V3 = `max_rset_` の後)。X 版は Vmid と lock 読みの位置を F と揃え、V3 は修理の再読を通過した後、修理の再読の不一致による abort を recheck_abort として数える (判断は変えない)。macro off の前処理一致は同じ commit 内 (P_F 対 N_F、P_X 対 N_X) で runner が build 前に確かめ、build 後に実 compile 命令の `-DTRACE=` と計器 define を arm ごとに照合した。
- 反復 (結果の前に固定、延長なし): 2 job × 14 batch、1 batch = T_X 4・T_F 2・N_F 1・N_X 1・P_F 1・P_X 1、F/X の先後を batch ごとに交替、benchmark の後に T 6 本を並列で verify。request 36350・36351 (Elapse 3,686 S・3,712 S)。280 走すべて完走、欠測 0。

| arm | 走 | commit 平均 (標準偏差) | 検査した read item | commit 側 class A | class B | recheck_abort | G2 |
|---|---:|---|---:|---:|---:|---:|---:|
| T_F (修正前、trace 有り + 計器) | 56 | 5,657,706 (51,922) | 3,025,221,527 | 366 | 611 | — | **8 / 56** |
| T_X (修正後、trace 有り + 計器) | 112 | 5,657,780 (50,787) | 6,050,250,129 | **0** | 2 | 1,892 | **0 / 112** |
| N_F (修正前、trace 無し + 計器) | 28 | 7,233,721 (104,203) | 1,933,205,054 | 1,049 | 3,629 | — | — |
| N_X (修正後、trace 無し + 計器) | 28 | 7,169,666 (98,924) | 1,916,106,993 | **0** | 0 | 4,476 | — |
| P_F (修正前、trace 無し素) | 28 | 7,200,449 (107,679) | — | — | — | — | — |
| P_X (修正後、trace 無し素) | 28 | 7,241,787 (84,896) | — | — | — | — | — |

- **判定 (runner の join が機械的に出した値、`verbatim/evidence/main-joined-summary.json`):** `all_expected_runs_present` true、`two_job_batch_schedule_complete` true、`R0_X_indeterminate_runs` 0、`T_X_G2_runs` 0 / `T_X_runs` 112、`T_X_N_X_commit_class_a` 0 → `success` true。
- **同時刻の対照:** `T_F_G2_runs` 8 (`T_F_G2_control_established` true)、`T_F_N_F_commit_class_a` 1,415 (`F_class_a_control_established` true)、`F_invalid_runs` 0。修正前 F の G2 の witness 9 件 (8 走) はすべて長さ 2・両辺 rw で、片側の辺で割り込みと一致した (class A 3 件、class B だけ 6 件、一致なし 0、判定不能 0)。切り分け (pin C) の witness と同じ形である。
- **区間と検定 (`verbatim/evidence/stats.log`):** 修正後 0/112 の Clopper–Pearson 95% 上限 3.24% (閉形式 1 − 0.025^(1/112) と一致)。修正前 8/56 = 14.3% (6.4〜26.2%)。両側 Fisher p = 1.07×10⁻⁴。修正前の率は切り分けの 5/112 (pin C) より高いが、同時刻の対照ではなく source (C と F) も違うので比べない。
- **修理の再読による abort の観測:** recheck_abort は 1 走あたり trace 無し 159.9 件・trace 有り 16.9 件。修正前 F で割り込みを受けたまま commit した件数 (commit 側 class A + B) は 1 走あたり trace 無し 167.1 件・trace 有り 17.4 件で、同じ規模だった (別の走どうしの比較で、1 件ずつの対応は取っていない)。修正後の commit 側 class B 2 件は修理の再読の後に publish された観測で、判定の対象外 (段 4 R6)。
- 修正後の class A = 0 は、版が前進する範囲では修理の再読から構造上導かれる (段 3 相談 A)。修理の効き目の独立の観測は G2 0/112 と recheck_abort であり、class A = 0 は予測どおりの値の確認として扱う。
- **性能の観測:** P の commit 数は修正前 7,200,449・修正後 7,241,787 (比 1.006、差 41,338 ± 標準誤差 25,913)。修理で commit 数が目立って下がる様子は見えない。headline・性能主張には使わない (規律 1)。N と T の commit 数は計器・trace の観測者効果込み。
- smoke 2 回: 1 回目 (36271) は runner が arm の `trace` (JSON の真偽値) を `CCBENCH_TRACE=True` として渡し、T arm が `-DTRACE=True` で build された (`#if TRACE` は未定義識別子 `True` を 0 と評価するので trace が出ない)。判定は trace が無い 6 走を判定不能にして `success` false で止まった (fail-closed)。段 6 で直し (S6-1、build 後の compile 命令照合を追加)、2 回目 (36299) で 6 arm が正しく動くことと単価 (固定費 53.0 秒・1 batch = benchmark 78.2 秒 + verify 187.6 秒 ≈ 266 秒、`verbatim/evidence/smoke2-timing.json`) を確かめた。本走の見積り 2 × 53 + 28 × 266 ≈ 7,554 秒 ≈ 2.10 node 時間はユーザー確認の上で投入した (回答「投入する」)。

## 5. patch 棚卸し (patches/ のうち `cc/mocc/transaction.cc` を触る 10 本、`git apply --check` の厳密適用)

| patch | C `68106660` | F `25898d00` | X `f4a5169e` | X で当たる patch の狙いの経路 (静的) |
|---|---|---|---|---|
| broken-mocc-early-unlock | 当たる | **外れる** (1257) | 外れる (1257) | — (C→F で外れた、F の整形 commit の writePhase の context) |
| broken-mocc-hot-update-unlock | 当たる | **外れる** (1257) | 外れる (1257) | — (同上) |
| broken-mocc-lockskip-validation | 当たる | 当たる | 当たる | validation の **write set の施錠**を条件付きで飛ばす (1017 行付近)。名前と違い read set の lock 検査ではない。修理は施錠を代替しないので、壊しの経路は残る (検出率への影響は未実測) |
| broken-mocc-permutation-erase | 当たる | 当たる | 当たる | write set の並べ替え (997 行付近)。修理と無関係、経路は残る |
| broken-mocc-skip-canonical-restore | 当たる | 当たる | 当たる | lock / writePhase 側。修理区間に hunk なし、経路は残る |
| control-mocc-negated-temperature-predicate | 当たる | 当たる | 当たる | 温度述語 (read・update・delete・RLL)。修理区間に hunk なし |
| mocc-temperature-predicate-variant | 当たる | 当たる | 当たる | 同上 |
| instr-mocc-lock-coverage | 外れる (11) | 外れる (11) | 外れる (11) | — (旧 base e9e477ca 向け、C で既に置き換え済み) |
| instr-mocc-lock-coverage-pin-candidate | 外れる (14) | 外れる (14) | 外れる (14) | — (同上) |
| instr-mocc-lock-coverage-temperature | 外れる (30) | 外れる (30) | 外れる (30) | — (同上) |

- **F → X で新たに外れた patch は 0 本** (`verbatim/evidence/inventory-{C,F,X}.tsv`)。F と X の結果は 10 本とも同一。
- 言えるのは厳密適用の可否と、X で当たる 5 本の hunk が修理の区間 (read set 検査) に掛からないことまで。当たる patch が意図した壊し・変異として同じ強さで働くか (検出率) は実測していない。
- 外れる 5 本は本 wave の修理と無関係 (C→F の 2 本は整形 commit F、C から外れる 3 本は旧計装)。扱いは pin 前進 wave の「patch 54 本の厳密適用」(D2277 項 1 (4)) で決める。段 4 R9 の追補は不要だった。

## 6. push の依頼 (人間の手番)

X の branch は land 後に主 checkout の submodule の git dir へ非 force で取り込む (本 wave の段 9)。その後、主 checkout で:

```
cd external/ccbench
git push origin izanagi-tpcc-v3-silo-mocc-fmt   # F が未 push なら先に (整形 commit F の wave の依頼)
git push origin izanagi-mocc-validation-fix
```

- 別名の新 branch なので force は不要。F (`25898d00`) は X の親として一緒に上がる。
- push 後に GitHub の Actions で build・format が緑であること、GitHub から X を取得できることを確かめる。gitlink は本 wave では進めない (§8 の起票)。

上流への説明文の下書き (英語、短く):

> **fix(mocc): recheck the read-set version after the lock check in validation**
>
> MOCC's validation() checks each read-set record's version and its writer lock with two separate loads, because the version (tidword_) and the lock (rwlock_) are different words. A concurrent writer can publish a new version and unlock the record between the two loads; the reader then commits with a stale read, and it also picked up the writer's new version into max_rset_ from a third load. On a read-heavy YCSB setting (48 threads, 1M records, 95% reads, zipf 0.9) this showed up as write-skew (G2) cycles under a serializability checker. This change reloads the version after the lock check, aborts if it changed, and computes max_rset_ from the checked version, as Silo does. Existing checks are unchanged.

## 7. 解釈の上限

- **言えること:** F の MOCC に修理 X を入れると、この cell で、trace build の事前登録 112 走で G2 は 0 件、修正後の commit した取引に validation の割り込み (class A) は 0 件だった。同時刻・同 job の修正前 F は G2 8/56 走・class A 1,415 件だった。修正後では修理の再読の不一致による abort を 6,368 件観測し、その 1 走あたりの件数は修正前 F の割り込み commit (class A + B) の 1 走あたりの件数と同じ規模だった (別の走どうしの比較で、同じ取引が修正前なら commit したという反実仮想は追跡していない)。
- **言えないこと:**
  - MOCC の G2 全般の排除。論証と実測はこの cell の長さ 2・両辺 rw の窓に限る。read phase の torn read、hot record の read lock、INSERT/DELETE、node set、MQLOCK、他の workload は範囲外。
  - 版の ABA 不在の一般的な保証 (有限幅)。
  - 率の上限を超える主張。0/112 の 95% 上限は 3.2% で、修正前の 14.3% とは区別できるが、「G2 が起きない」とは言えない。
  - 性能への影響の主張。P の commit 数は 1 cell・28 走ずつの観測で、trace build と別集計。
  - GitHub Actions の CI 緑 (push 前)、D297 の合格、pin 前進の完了。
  - 計器の窓の中の load (Vmid) が割り込みの頻度に与えた影響の大きさ (切り分け §6 と同じ限界)。
  - patch の意味の保存 (適用可否と hunk の位置の静的判定まで)。

## 8. 次の一手 (spool worklog fragment に書いた内容)

- T-2872 の item は **更新** (完了にしない): 修理 commit・CI 相当・D297 の読み・本走の判定を書き、完了は gitlink 前進の後とする。
- 新規起票 (gitlink 前進 wave): 前提 = F の pin 前進が main に着地、ユーザーが F と X の branch を push、GitHub の CI 緑、GitHub から X を取得。内容 = gitlink・`CCBENCH_FULL_SHA`・`CURRENT_PIN` の同時更新、D297 の C → X の扱い (§3)、patch の厳密適用、修理後の版で測り直すかの提示 (D2277 項 2)。Silo 修理 (`izanagi-silo-intra-txn-fix`) と同じ時期なら両方を積んだ tip への前進を 1 wave にまとめてよい (force push はしない)。

## 9. 段の経過と所見

- 段 1 (親): brief の provisional (P1)〜(P5)。前提実測 = F の実在と validation の行、`ERR` の `__LINE__` の位置、Silo の検査、patch 10 本の C / F の厳密適用、template と旧計器の F への適用 (旧計器は 1156 行で外れる)。
- 段 2 plan (Codex、read-only) と段 3 相談 2 本 (A = 並行性の正しさ、B = 測定・記録・過剰): 全 real 所見を採用。A は案 A を支持し、ABA と Silo 同値の言い方の限定、class A = 0 が構造上の帰結なので recheck_abort を数えることを出した。B は修正前 F の G2 が 0 件のときの書き方の統一、見積り式の固定費の二重計上、arm 別 source の保証、D297 の rc=1 の読み方を must-fix に出し、F 側の反復を減らす構成 (T_F 56・N/P 各 28) を提案した。段 4 裁定 (`verbatim/s4-ruling.md`) で事前登録 R6 を凍結。
- 段 5: 子木 2 本 (`.codex/worktrees/moccfix-a`・`moccfix-b`、Lustre の混雑で submodule 初期化が 2 本とも 1 回目に `update-no-fetch` で失敗し、同じ引数の 1 回の再実行で通過 = DW-O08)。実装子 A (修理) → レビュー A (hunk に所見なし、message 2 件) → 親が commit X (`verbatim/mk-X.log`)。実装子 B は親の投げ文の path 誤り (先例 job dir の直下にある 2 script を `build/`・`judge/` 配下と記載) で「読めなければ即停止」により 2 call で停止し (F819 の型の再発)、全 path の実在を検査してから B2 として再投入した。
- 段 6: CI build・D297・smoke を 3 つの checkout から並行投入。レビュー B1 (測定の妥当性) と B2 (過剰・削除)、smoke 1 回目の実走で見つけた `-DTRACE=True` の欠陥 (S6-1) を段 6 裁定 (`verbatim/s6-ruling.md`) にまとめて fix 子へ。焦点再レビュー 1 巡で S6-1・3・4・5 closed、S6-2 の残り (両 compiler rc=0 のときの名前) は親が refuted で閉じた。D297 と smoke を直した道具で取り直した。
- 親の投入 wrapper の 1 本目 (`run-checks.sh`) は `{ ...; exit $rc; } > log` の `exit` で script ごと抜けて `.done` を書けず、待ち手が rc=70 を返した (結果は log の終端行で確かめた)。2 本目で直した。
- 計算: CI build 33 S、D297 9 S × 2、smoke 93 S・324 S、本走 3,686 S・3,712 S、計 7,866 S = **2.19 node 時間** (受入を除く、`verbatim/evidence/elapse.tsv`)。Codex 子: plan 1・consult 2・author 3 (A・B・B2、B は不受理)・review 3・fix 1・focus 1。Explore (sonnet) 1 本 (既存 F の検索)。
- 段 7: 記録 commit の後に読み取り専用の記録レビュー 1 本 (`verbatim/s7-review-record.md`) で全数値を原データと照合させ、must-fix 0・should 3・nit 2 (見積りの入力の所在、因果の言い過ぎ、D297 の前進先への一般化、比較単位、採否の書き方) を追補 commit で直した。
- 変異: izanagi の実装面の差分は 0 (docs のみ) なので変異 matrix は免除 (DW-S04)。修理を外した版 = 修正前 F の arm を負例として事前登録し、class A > 0・G2 > 0 を観測した。

## 10. 再現資料

- `verbatim/`: 依頼・brief・plan・相談 2 本・段 4 / 段 6 裁定・実装子 A / B2・fix・レビュー A / B1 / B2・焦点レビュー・記録レビュー・開始 gate・commit message と mk-X.log・F→X の差分 (`F-to-X-diff.md`)・job dir の sha256。
- `verbatim/NORMALIZATION.md`: 逐語の写し 7 file の行末空白・末尾空行の可逆正規化の記録 (元の sha256・byte 数・復元法、DW-S07)。
- `verbatim/evidence/`: format の log、CI build の report、D297 の report 2 回分、棚卸し 3 表、smoke 2 回の summary、本走の結合 summary。
- job dir: 使い捨て道具 v1 (`tools-v1/`) と v2 (`tools/`)、親の投入 script、X.bundle、計算の全出力 (`evidence/`)、Codex receipt (`codex/`)。
