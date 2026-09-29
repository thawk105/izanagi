# 段 4 裁定 — md_23 (T-2908) gc_records 修理 (2026-09-29 22:5x JST、親)

入力: s1-brief.md、d1-result-summary.md、plan.md (段 2)、consult-a.md・consult-b.md (段 3、受理済み)。依頼の正本 = request-md_23.txt (起動時に読んだ本文。md_23.txt は 21:59 に別依頼で上書きされ、VHash 親セッションが上書きを認めて本 wave の継続を確認した)。

## 所見の裁定

| 所見 | 判定 | 採否・理由 |
|---|---|---|
| A1 回収 (`delete rec`) の寿命を X1 の安全性として扱えない | real (記録)、X1 固有の新しい危険としては refuted | X1 が新たに回収するのは「最上段が aborted、その下が自分の deleted 版 D1」の tuple で、条件は最上段の wts < MinRts (既存の正常経路 = 最新版 D1 の wts < MinRts より遅い)。aborted 版は gcq に積まれず誰にも解放されない、D1 の gcq 処理は D1 の next を切るだけ (transaction.cc:831-838) なので、X1 が辿る D2→D1 は生きている。tuple を指す他の参照 (実行中 tx の scan / read set、他 thread の gcq_) は正常経路と同じ既存の寿命問題 (brief P4)。**挙動で確かめる**: 修理版の ASan build (Debug・ENABLE_SANITIZER=ON) で F×t4 を 3 回、AddressSanitizer の報告 0 を事前登録 (R3 の V1)。報告が出たら修理の採否へ戻す。 |
| A2 / plan「回収時に pending 不在は未証明 (wts ≥ rts の clamp が無い)」 | refuted (静的)、記録 | 各 thread の localClock_ は減らない (time_stamp.hh:30-40、elapsed ≥ 0 と boost ≥ 0 の加算だけ) ので thread ごとの wts は単調増加。MinWts は公開済み ThreadWtsArray の最小 (util.cc:291-315) で、各 thread の公開値 ≤ その thread の現在 wts。よって rts = MinWts−1 < 自分の wts、MinRts ≤ 各 thread の公開 rts < その thread の実行中 tx の wts。回収判定 (最上段 wts < MinRts) の時点で、最上段以下の版に実行中 tx の版 (pending) は無い。配列の初期値 0 は、全 thread が GC 旗を立てるまで leader が MinRts を更新しない (util.cc:281-289) ので効かない。さらに X1 は pending・committed・null を見たら ERR を残す (黙って回収しない)。一次資料には「静的な論証、group_commit=0 の場合」と書く。 |
| A3 trace の合格は修理分岐が発火した履歴の証拠にならない | real | 採用。trace build に使い捨ての計数 patch (repo 外、Codex author) を修理の後に重ね、gc_records で aborted を読み飛ばして回収した回数を stderr に出す。trace の合否と同じ run で「読み飛ばし回数 > 0」を要求する。加えて W op D を出した thread が 2 つ以上であることを数える。 |
| A4 / B3 CUSTOM の rc が判定を強制しない | real | 採用。起動器に build ごとの期待値 (expect) と run 指定を足し、期待外なら起動器 rc=1 (R3)。 |
| A5 受理集合の表現を限定 | real (nit) | 採用。「観測した設定 (INLINE_VERSION_OPT=0・SINGLE_EXEC=0・WRITE_LATEST_ONLY=0・REUSE_VERSION=1・group_commit=0) で validation と commit の経路を変えない」と書く。 |
| A (親の実測) TRACE=0 の ERR 行番号 | real | 採用。修理は transaction.cc の行数を変えうる。計装 patch は transaction.cc に `#line 909`・`#line 934` を固定値で置く。909 行以降に `__LINE__` を使う ERR は無い (親の読み) ので命令列は同じ見込みだが推測。V2 で (F+fix) 対 (F+instr+instr-tpcc+fix) の TRACE=0 命令列比較 (tpcc の 3 TU) を実測する。 |
| B1 依頼文の不一致 | real | 解消済み (上記の正本)。一次資料に明記。 |
| B2 CUSTOM は全 build に同じ cell×thread×repeat | real | 採用。build spec に build 別の `runs` ([cell, thread, repeat] の列) を足す。 |
| B4 無修理対照は thread 別に | real | 採用。t4・t8 それぞれで既知 ERR ≥ 1 を要求。 |
| B5 計測量の根拠 | real | 採用。R3 に build 数・run 数・walltime を書く。 |
| B6 共存確認を完了条件にしない | real | 採用。必須の厳密適用は pin C、pin C+instr、C1'+instr+instr-tpcc、F、F+instr+instr-tpcc、F+instr+instr-tpcc+broken-skip-read-recheck の順の後。他 wave の patch (version-lifetime、forwarding 系) との重ねは login の `git apply --check` を 1 回だけ試して結果を README に書く (合否に使わない)。`-instr` 付きの別 patch は単一 patch が当たらない場合に限る。 |
| B7 所有と CI の方向 | real (nit) | 採用。md_19 の branch とは混ぜない。 |
| B 変異案 (1 段だけ読み飛ばす) | real | 採用 (M2)。 |

## R1. 修理 (plan v2 = X1)

`external/ccbench/cc/cicada/transaction.cc` の `TxExecutor::gc_records()` だけを変える。意味:
- 最上段の wts による既存の待機判定 (`>= MinRts` なら break) は最上段の版のまま変えない。
- 最上段から続く `aborted` の版を next で辿って読み飛ばす (何段でも)。
- 読み飛ばした後の版が null、または `deleted` 以外 (pending・committed・その他) なら既存どおり `ERR`。`deleted` なら既存どおり `delete rec` して pop。
- 新しい `#if`・`#define`・`IZANAGI_` の語・診断出力を足さない (既存テスト test_p3_s4_loop.py の裸マクロ登録と test_ccbench_spawn_sites.py の前処理条件の走査に掛けない)。変更は clang-format 14 (CCBench の .clang-format) に合わせる。短い英語のコメント 1〜2 行で理由を書いてよい。
- 受理集合 (validation・commit・abort の経路)、版の install・状態遷移、gc_versions は変えない。

## R2. 置き場と commit

- `patches/fix-cicada-gc-records.patch` (新規、tracked、Codex author): pin C を基点に作る unified diff (`diff --git a/cc/cicada/transaction.cc b/cc/cicada/transaction.cc`)。R 項の順に厳密適用 (`git apply --check` と patchharness の適用) できること。
- CCBench local branch `izanagi-cicada-gc-records-fix` = F 25898d00 の子 1 commit。内容は F に同じ patch を `git apply` した結果 (tree の一致を親が照合)。作成は T-2854 の mk-F.sh 型 (wave 木の submodule に job dir の一時 worktree、非 force、bundle)、段 6 のレビュー後に親が commit -F。trailer 3 行 = Codex author・Codex reviewer・Claude manager。段 9 で主 checkout の submodule git dir へ非 force で fetch (fetch-F-to-main.sh 型)。submodule の HEAD と izanagi の gitlink は動かさない。push は人間。
- `patches/README.md` に節を足す (親、docs)。ledger.json は触らない。
- 上流 CI: format = 修理 commit の clean checkout で `git ls-files -- cc include common | grep -E '\.(cc|hh|cpp)$'` の全 file に clang-format 14 `--dry-run --Werror` (login の /usr/bin/clang-format 14.0.0)。build = T-2854 の run_ci_build.sh を写し親 OID を F に変えた script (Codex author、repo 外) を計算ノードで CI image `:ci` により実行。

## R3. 確認の事前登録 (完了判定。結果を見る前に固定)

計測木 gcfix-m1 (V1) と gcfix-m2 (V2) から 2 job を別ノードへ同時に投入。性能値は取らない。
共通: F cell 以外の cell は md_17 の定義 (M・R2)。TRACE=0 は Release・sanitizer OFF (ASan build だけ Debug・ON)。

**V1 (TRACE=0、同じ job):**
| build | 構成 | run | 期待 (事前登録) |
|---|---|---|---|
| F_T0 | F 無 patch | F×t4×10、F×t8×10 | t4・t8 それぞれで `gc_records` の既知 ERR (stderr の `transaction.cc` と `gc_records`) が 1 回以上 (到達の対照) |
| FIX_F_T0 | F + fix | F×t4×10、F×t8×10 | 20/20 が rc=0 (timeout・signal 0) |
| C_FIX_T0 | pin C + fix | F×t4×3 | 3/3 rc=0 (pin C 用 patch の生死) |
| ONELEVEL_F_T0 (変異 M2) | F + 1 段だけ読み飛ばす変異 patch | F×t4×10、F×t8×10 | 事前登録: 既知 ERR が 1 回以上なら KILLED (何段でも読み飛ばす必要の実証)。0 回なら SURVIVED と記録し、修理の採否には使わない |
| FIX_F_ASAN | F + fix、Debug・ENABLE_SANITIZER=ON | F×t4×3 | 3/3 rc=0 かつ `AddressSanitizer` の報告 0。ASan 以外の assert 等で落ちた場合は既存欠陥の候補として記録し再裁定 |

**V2 (TRACE=1、判定器):**
| build | 構成 | run | 期待 |
|---|---|---|---|
| FIX_F_TRACE | F + instr + instr-tpcc + fix + 計数 patch | F×t4×3、M×t4×2、R2×t4×2 | 各 run rc=0、判定 indeterminate、巡回 0、integrity 数値項目 0、存在履歴違反 0、C 行 = commit 数、READ_WTS_MISMATCH 0。F の各 run で W op D > 0、D を出した thread ≥ 2、計数 patch の読み飛ばし回収 > 0 |
| STOCK_F_TRACE | F + instr + instr-tpcc | M×t4×2、R2×t4×2 | 同じ判定項目で合格 (delete なしの cell で修理前後の判定が同じ = どちらも合格) |
| SKIPRC_FIX_F_TRACE (変異 M3、判定器の検出力) | F + instr + instr-tpcc + broken-skip-read-recheck + fix | F×t4×1 | rc=0 で完走し、判定 non-serializable・巡回 > 0 (delete を含む並行 TPC-C でも判定器が異常を検出する)。帰属は既存の起動器の機能の範囲で (必須にしない) |
| identity | (F + fix) 対 (F + instr + instr-tpcc + fix)、TRACE=0 | tpcc の transaction.cc・util.cc・tpcc_cicada.cc | 命令列の差分 0 byte (起動器の trace_zero_identity 相当)。差があれば記録し再裁定 |

合否は「修理自身が出す量」に依らない: V1 の完走と対照の ERR、V2 の判定器の数値、ASan の報告。計数 patch の値は「修理分岐が同じ run で発火した」ことの確認だけに使う。
合否に throughput、ERR 行が消えたこと単独、`integrity.clean` は使わない。判定の上限は indeterminate で、serializable の証明とは呼ばない。
**見積り:** V1 = 5 build (うち ASan 1) + 76 run (1 run ≈ 1〜2 秒、ASan は数秒) ≈ 10 分。V2 = 3 build + 12 trace run + identity 3 TU×2 ≈ 15 分。CI build ≈ 1 分。合計 < 0.5 node 時間 (2 node 時間の線の下)。walltime は各 00:50:00。

## R4. 変異 (DW-M01)

本 wave は izanagi の判定器・テストを変えないので pytest の変異 matrix は置かない (md_17 R7・md_3 R6 の先例)。実装面は CCBench の修理 (patch と commit) と repo 外の起動器・使い捨て patch で、実系の変異で確かめる:
- M1 = 修理を外した F_T0 (上表、同じ job)。KILLED = t4・t8 それぞれで既知 ERR ≥ 1。
- M2 = 1 段だけ読み飛ばす (while → if 相当) 変異。上表の事前登録どおり。単一理由性: 変異は gc_records の読み飛ばしの段数だけで、他の経路は同一。
- M3 = read 再検査を飛ばす既存の壊し + 修理。判定器が delete を含む並行履歴で巡回を検出すること。
- 「ERR を外す」変異は採らない (異常を隠す向きで、完走では区別できない)。静的な条件確認 (R1 の ERR 分岐が残ること) を段 6 のレビューで確かめる。
起動器は repo 外で変異 matrix の対象外。

## R5. 段 5 の単位と所有

1 単位 XV (Codex author、子木 gcfix-x、branch dev-wave-gcfix-x)。所有:
- tracked: `patches/fix-cicada-gc-records.patch` (新規) だけ。
- repo 外 (untracked、親が job dir へ退避): `.gcfix-launcher/launch_gcfix_run.py` (job dir の版を写して拡張: build 別 runs・expect と rc 集約・CUSTOM trace の stock_pass 相当・W op D の件数と thread 数・計数 patch の出力の集計・cmake 追加引数 (ASan 用)・trace_zero_identity の CUSTOM からの呼び出し (F 基点の 2 構成))、`.gcfix-work/onelevel-cicada-gc-records.patch` (M2)、`.gcfix-work/count-gcfix-skips.patch` (計数、修理の後に当てる)、`.gcfix-ci/run_ci_build.sh` (T-2854 の写し、親 OID = F)。
- external/ccbench は試しに当ててよいが終了時に byte 一致へ戻す。docs・commit・計算ノード投入はしない。
- 既存テストの期待値を変えない。新しい `#if`・`IZANAGI_` を足さない。
規模上限: patches/fix-cicada-gc-records.patch の変更行は +15 / −3 以内 (コメント含む)。

## R6. 記録

一次資料 `output/insights/2026-09-29/vhash-cicada-gc-records-fix/README.md` (親)、`patches/README.md` の節 (親)、fragment (worklog: T-2908 を完了へ、push と pin 前進の item を新設または更新。decisions: 修理方式 X1 と確認の事前登録。failures: 依頼 file の上書き (md_23.txt) を near miss として既存 F に当たるか検索して記録)。
