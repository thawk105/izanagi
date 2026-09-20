# 根拠の対応表 — `report-draft.md` の各文 `[S-nn]` → 一次資料 (path と SHA-256)

作成 2026-09-20 (wave `dev-wave-t2791-mocc-upstream-report`、着手時 local main `947fd160ab44e6ae82b6eab56ee8d70813fda31d`)。
**この表が無い文は draft に書いていない。** 送信前に draft を直すときは、この表の出所へ再照合してから直す。

## 0. 出所の記号と digest

### 0.1 repo 内 (tracked)。SHA-256 は本 wave で `sha256sum` により計算 (main `947fd160a` の bytes)

| 記号 | path | SHA-256 | 何が書いてあるか |
|---|---|---|---|
| A | `output/insights/2026-09-18/t2774-mocc-torn-read-probe/README.md` | `cfa74f6dd7c1e5a4588d75dd48d362c4f108d20aa702da36ba162bd8ca646282` | [T-2774] 記録 insight: §1 結論、§2 束縛、§3 静的順序論証、§5 結果 (Q2 5 arm × 40、Q1 2 arm × 56)、§6 限界、§8 欠陥 |
| B | `output/insights/2026-09-18/t2779-mocc-g2-observation-conditions/README.md` | `559d8e68ee9d875bd9580ef08e70a9c3641019d225c6d7579a8958a0767a9724` | [T-2779] 記録 insight (§3 = 軽量 witness の静的設計) |
| B2 | `output/insights/2026-09-18/t2779-mocc-g2-observation-conditions/summary.json` | `fee7803f27bbdf2637b4d4f667430e379e1a89f09d47b4056a1892b14a765459` | [T-2779] arm 別 k / m / CP 区間 / discriminator 会計 (機械集計) |
| C | `docs/paper-story/results/2026-09-20-mocc-g2-observation-conditions.md` | `193d03d5c05af8669e7e3b5604c4080e9426a3b6b62e232c216633d4a062780c` | [T-2779] results 稿 (commit `ba8093fbb`): §1 条件・束縛、§2 事前登録、§3 結果 (block 別・合算・Fisher・G2 7 走の構造・会計)、§4 未照合、§5 限定 |
| D | `docs/paper-story/results/2026-09-20-mocc-witlight-four-arm.md` | `77662b55f2b1f113626293ee530d5e0466249192ba2f6babefe4db4e74241d96` | 軽量 witness 4 arm × 60 の results 稿 (commit `5db68f1ee`): §1.2 事前登録、§1.3 検出力、§1.5 束縛 (W・合成 source・configure)、§2 結果、§3 限定、§5 一次資料 |
| D2 | `output/insights/2026-09-19/mocc-witlight-arm-run/README.md` | `a23f68e7310a5a1170ba4eb3ad8fca9c41431b0ce1960b7fcc03175fffa038bc` | 同 wave の記録 insight |
| D3 | `output/insights/2026-09-19/mocc-witlight-arm-run/verbatim/W1-018-e9-witlight-nowit/verifier.json` | `b89dbdafff559a31acc2a7fdb4665f9eaa6d5dfc6079c9b23eb711035dc21abd` | witlight G2 走 1 の verifier 出力 (integrity.clean true、G2、長さ 2) |
| D4 | `output/insights/2026-09-19/mocc-witlight-arm-run/verbatim/W3-005-e9-witlight-nowit-bo1/verifier.json` | `20d07793c5e694a78bae4119e24ac59e36e8cd347017e08287e86d680d93dbb4` | witlight G2 走 2 の verifier 出力 (同上) |
| E | `output/insights/2026-09-18/t2780-mocc-pilot-discriminator/README.md` | `7f48cfff0db1de8b3eaef3e6b951c455c3c80300f73c213fbaae8181656824d3` | [T-2780] pilot discriminator 配線修正と job 5905 の生死確認 (結論 `no-g2`、X/P numstat 65/0) |
| E2 | `output/insights/2026-09-18/t2780-mocc-pilot-discriminator/liveness-recovered-verdict.json` | `0eccfa49aa4f493f890ea9c2cb53e4d7475d73792ebe31570d6eb95b79cffeb2` | job 5905 の判定 (patch binding、gates、`discriminator_conclusion: no-g2`) |
| E3 | `output/insights/2026-09-18/t2780-mocc-pilot-discriminator/job5905/discriminator.json` | `36d72996a4b6a9b6a2ef2f12392a08c0f875a4b4df9852a00d62a1855778203e` | job 5905 の discriminator 出力 (`source_oid` e9e477ca、workload、witness manifest あり = witness on、`comparisons` 0) |
| E4 | `output/insights/2026-09-18/t2780-mocc-pilot-discriminator/job5905/accounting.txt` | `010373874f182a4d99a97fd3bef2dd0f75602b99cb9a6783a71520a2d3ea7abc` | job 5905 の NQSV 会計 (2026-09-18 16:07:41〜16:09:44 JST) |
| F | `output/insights/2026-08-26_mocc-g2-repro/results.md` | `66e3ee95960c125b8f12b2aba82b66db944a438a640909f98e89967e7eef48ec` | [T-1892] 5/42 の結果 (CP 区間、42 走の分類、5 件の構造表、integrity clean、ordinal 32 の 2 reason 辺) |
| G | `output/insights/2026-08-28_t1943-mocc-g2-discriminator/RESULT.md` | `267f3304c29a50de059823a3c5a92fec95538b1ef4187475b22fecdddba49d1e` | [T-1943] 1 cell (request 956466、CCBench e9e477ca、witness on、`no-g2`)、hook branch の fetch と「upstream push は人間手番」 |
| H | `patches/instr-mocc-lock-coverage.patch` | `e9e65b7876050865ee1cbc4d3a05516b09a8fe0b18149e0c063632162fd7bb48` | X/P 計装 patch (D1686) |
| L1 | `orchestrator/verifier/dsg.py` | `e77eaabd929e1e05f853b230041495a19b004a8156ddc805676bbd81ffbcbb05` | module docstring: DSG の辺定義 (ww / wr / rw)、G0 / G1c / G2 分類、版順序の仮定 |
| L2 | `orchestrator/verifier/model.py` | `59136847b040e70002ee73f1b1de52a9ac2545e7beb36f60d95a0a43596067fb` | `Anomaly.phenomenon`、`Integrity` の field 一覧と「unclean なら indeterminate」 |

### 0.2 ccbench submodule の git object (local mirror `.git/modules/external/ccbench`、本 wave で `git rev-parse` / `git show` により確認)

| 記号 | object | blob / commit | 何を確認したか |
|---|---|---|---|
| K1 | `e9e477ca1b55348ab4530de0b1cf663ce4555290:cc/mocc/transaction.cc` | blob `1f4e9453c39a42451e652b3a28d791b90844f184` (1,294 行、SHA-256 `79982b23dce106766dab9e8d8183154d9de4af94724d1a003a09a79e84155a21`、job dir `artifacts/transaction-e9e477ca.cc` に写し) | 行番号 316 / 320 / 322 / 350–352 / 1010 / 1024 / 1038 / 1169 / 1195 / 1207 の内容、`writePhase()` の TRACE block の位置 |
| K2 | `e9e477ca…:cc/mocc/CMakeLists.txt` | blob `8eed989943eecaa9acb0937e9cc9f46d9c1cd2e4` | `RWLOCK` が OPTIONS に無条件で並ぶ |
| K3 | `e9e477ca…:cmake/Options.cmake` | blob `b9a3c740d58add663a26f9009cddea9e730d0f21` | `CCBENCH_BACK_OFF` 既定 1、`CCBENCH_KEY_SORT` 既定 0、`CCBENCH_TEMPERATURE_RESET_OPT` 既定 1、`CCBENCH_TRACE` 既定 0 |
| K4 | `e9e477ca…:include/trace.hh` | blob `570e35e308e1104d53d43ea5556f54b3fb86922a` | trace 形式の header の実在 |
| K5 | `remotes/origin/master` = `50c7946d1bf571a5c9b93a32d935f5f50d442dc6` (commit 日時 2026-06-28 15:48:52 +0900、"Merge pull request #118 …")、同 `:cc/mocc/transaction.cc` = blob `559834e2ce445ca36d857e3bef78728935fa3ffc` | `git diff remotes/origin/master e9e477ca -- cc/mocc/transaction.cc` = 141 insertions / 0 deletions (6,449 byte、job dir `artifacts/mocc-transaction-master-to-e9e477ca.diff`、SHA-256 `17c5e49729727fadb1f6b5a0b75f7dbb6cf2d5bf4167590e80aebf8d4877dcab`)。非空の追加行は全部 `#if TRACE` … `#endif` 内 (awk 走査、TRACE 外の `+` 行は空行 4 本だけ) | 上流 master との差分の性質。`merge-base` = `7e268f2af89f92a6029270e4272f0f65787f2666`、origin/master は e9e477ca の祖先ではない |
| K6 | tag `v1.1.0` = `d9ffac189eb6a8b7096c903102c3b1ee37cad9a0`; `git describe 511c9538` = `v1.1.0-126-g511c9538` | — | 系譜の base |

### 0.3 job dir 原本 (repo 外、durable authority)。SHA-256 は本 wave で再計算し、C / D の表の値と一致

| 記号 | path | SHA-256 |
|---|---|---|
| J1 | `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2774-mocc-torn-read-probe/arm-B/summary-q2.json` | `1ef9af1773a828a26d5280e3a49cacd9c39397e0c91997fc49dda4180539872d` |
| J2 | 同 `arm-B/summary-q1.json` | `d1722280f515b6d23e41847a090b5b438a78a3c78b624eaff3cf6396e467ece1` |
| J3 | 同 `probe/mocc-close-version-counter-gap.patch` (診断 patch 原本、1,168 byte) | `8a25bd0a5687437269c720cb34a4b26024a6f1f119adf1c16281d455b9ecaa1d` |
| J4 | `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2779-mocc-g2-observation-conditions/arm-B/B1..B4/result.json` | `db26afc7…60e427` / `f5cdf50f…200ccdb7` / `c883caa2…643075d` / `7e43392f…667ea25` (全桁は C §6.2) |
| J5 | `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/arm-W/summary.json` | `b1be3ebde10c20ea26de3956495f927d2baa8c06ecc1b7e2d7222f2795310698` |
| J6 | 同 `arm-W/parent-accounting.json` | `20952bb6498d3a2935cb1797d53486b014929f6647c15642c37eb1c9405d0abe` |
| R1 | 本 wave の再計算 v2 (DW-O16、焦点再レビュー後に counter 検査を追加): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2791-mocc-upstream-report/artifacts/recheck_21_cycles.py` と同 `.log` — 21 走の verifier.json (F の `runs/{19,24,30,31,32}/`、T-2774 job dir の `arm-B/Q{1..4}/runs/<ordinal>-<arm>/`、C / D の repo 内 verbatim) から cycle 長・辺種別・版・key・reason 数・integrity の数値 counter 11 個 (orphan_reads / version_dups / dup_txids / genesis_commits / missing_txids / write_version_mismatch / malformed_keys / framing_violations / lock_coverage_violations / write_intent_violations / permutation_violations) と `clean` flag を機械集計 | script `811df1729a790dd02a745948b9cc28209bff953eb94ba25bb0ef897f19653b4b` / log `d08eca3a3afe9e6b572571fb585b8078a9723fe9fb262c1f770a51394dc5c58a` |

## 1. 文ごとの対応

| 文 | 出所 | 該当箇所と、draft の文がそこから何を取ったか |
|---|---|---|
| S-01 | A §1 項 2; F 一次結果; L1 docstring | G2 signal の定義 (長さ 2・両辺 rw)、TRACE=1 build、fork branch。「Adya の G2 = rw を含む cycle」は L1 |
| S-02 | F (5 件の形、42 走の外に先行 pilot `949964.nqsv` の 1 件が「参考」として別記); A §5.1 (7 件: 長さ 2・両辺 rw・別 thid・同 epoch・commit tid 差 1、integrity 違反 counter 0); C §3.4 (7 件: G2・長さ 2・両辺 rw・integrity.clean true); D §2.4 + D3 / D4 (2 件); R1 (21 走の機械再計算: N=21、同 epoch 21/21、tid 差 1 が 20、差 2 が 1 = C §3.4 B2/069、integrity の数値 counter 11 個は全 21 走で 0) | 21 = 5 + 7 + 7 + 2 (表にした 4 実験の合計。先行 pilot 1 件は含めない)。「integrity counter が全部 0」は R1 の counter 検査。`clean` flag の 16 / 5 の内訳は S-40 |
| S-03 | witness on: A §5.1 (instr-wit 0/40、diag-wit 0/40)、A §5.2 (Q1 instr 0/56、diag 0/56); D §2.2 (wit 0/60、wit-bo1 0/60); G (0/1); E2 / E3 (0/1)。witness off の `BACK_OFF=1`: C §3.2 (bo1 2/120)、D §2.2 (nowit-bo1 1/60) | witness on の全 arm と、witness off では BACK_OFF 0 / 1 の両方で signal があること |
| S-04 | A §1 項 7、§6; F 射程; C §0.1 項 5 | 三分岐 (実装 / hook / verifier 仮定) が未分離 |
| S-05 | D2148 項 13 (docs/decisions.md、修正 PR 見送り); K5 (e9e477ca の 1 file と master mirror の静的比較); A §2、C §1.2、D §1.5 (全 producer は fork commit で、計装 / 診断 / 軽量 witness は e9e477ca の上に別 patch を当てた別 source) | 「master で走っていない」と、S-14 の比較が e9e477ca の 1 file に限ること |
| S-06 | — (依頼文) | 事実命題なし |
| S-07 / S-08 | D2148 項 13; C §0.1 項 5・6; D 冒頭限定 1 | 書かないことの列挙 |
| S-09 | C §0.1 項 2・10; D 冒頭限定 5 | TRACE=1、commit 数は性能値でない |
| S-10 | `.gitmodules` (url `https://github.com/thawk105/ccbench`、branch `izanagi-trace`); K6 | 系譜 |
| S-11 | A §2 (058d0c4e = T-1892 の producer、trace hook のみ; e9e477ca = hook branch 先端、witness あり); K1 (`izanagi_mocc_g2_enabled()` で gate); A §2 (`IZANAGI_MOCC_G2_WITNESS=1` env) | 2 producer と witness の on/off 機構 |
| S-12 | D §1.5 (W = `5b02546f…`、親 e9e477ca、branch `izanagi-t1943-mocc-g2-witlight`、`cc/mocc/transaction.cc` +26/−6; 合成 source = e9e477ca + X/P + witlight.patch が e9e477ca + W + X/P と `^#line` 除去後 bytes 一致) | 軽量 witness の identity |
| S-13 | G (hook branch は local へ fetch 済み、upstream push は人間手番); D §1.5 (W は GitHub 未 push); `.gitmodules` + K6 (pin 511c9538 = v1.1.0-126); C §0.1 項 3 (候補 e9e477ca は未 pin) | 公開状態と pin |
| S-14 | K5 | 本 wave の静的検算。後続 master・master 実走は未確認。mirror の fetch 日は成果物に無い (K5 の日付は commit 日時) |
| S-15 | A §4 / C §0.2 (arm・block の定義: arm = 1 構成、block = 1 node での走の群、round ごとに arm を回転); H (sha); E §「計算ノードでの生死確認」(numstat 65 追加・0 削除、touch set 1 file); C §0.1 項 2 (`#if TRACE` 内の lock 被覆・permutation 検査); A §5.1 注 (X/P 無しは zero-cycle が indeterminate) と A §5.1 (X/P 追加 3 対 2 = 片側 Fisher 0.5) | 用語の定義 (初出の前)、計装 patch の性質と 1 対比較 (p = 0.5、効果なしとは言わない) |
| S-16 | A §2 (Q2 configure 6 define = pilot と同一); C §1.3 (+ `-DCCBENCH_CCACHE=OFF`); D §1.5 configure (`-DCMAKE_BUILD_TYPE=Release -DENABLE_SANITIZER=OFF …`); K2 (RWLOCK 無条件) | define の共通部。`-DENABLE_SANITIZER=OFF` は D だけが列挙するので draft では書かない |
| S-17 | C §1.3 (backoff arm は `-DCCBENCH_BACK_OFF=1` だけ置換); A §2 (Q1 は `-DCCBENCH_BACK_OFF=1 -DCCBENCH_KEY_SORT=0 -DCCBENCH_TEMPERATURE_RESET_OPT=1`、BACK_OFF だけが既定と異なる実効差); K3 (既定 KEY_SORT 0、TEMPERATURE_RESET_OPT 1) | BACK_OFF=1 arm の define |
| S-18 | A §2 / C §1.3 / D §1.5 (gcc-11 / g++-11 の path); K3 (`CCBENCH_MASSTREE_USE` 既定 1) | toolchain と index |
| S-19 | A §2 / C §1.3 / D §1.5 / E3 `bindings.workload` / G fixed cell | workload argv。全走同一 |
| S-20 | C §1.5 (4 block = 4 node、gen_S); C §4 項 6 と A §2 末尾 (node 専有の実証なし、runner の `_assert_single_tenant`); J4 の `bindings` に CPU 情報の field が無い (本 wave で key 一覧を確認: runner / repo_head / workload / workload_argv / arms / policy / toolchain / base_dir / configure_defines のみ) | 機体の記述の上限 |
| S-21 | A §4 (各走: trace dir → verifier); C §1.4 (binary sha は block ごとに異なる、source sha・define・toolchain は一致); D §1.5 (同) | 1 走の定義と identity の射程 |
| S-22 | K1 `writePhase()` (`C` 行 = txid thid epoch tid |read_set| |write_set|、`emit_read(… re.tidword_ …)`、`emit_write(… maxtid …)`、TRACE block が write loop の前); C §4 項 12 (C 行の列順) | trace が記録するもの |
| S-23 | L1 docstring (ww / wr / rw の定義、cycle ⇔ non-serializable、G2 = rw を含む cycle) | verifier の graph |
| S-24 | L1 docstring (版順序: 同一キー上で (epoch,tid) が全順序、producer を一意に決める); L2 `Integrity` の field; A §5.1 (integrity 違反 counter 全走 0)、C §3.4 (integrity.clean true、各違反 0)、D3 / D4 | 仮定と integrity 検査 |
| S-25 | A §1 項 7・§6 (分岐 3 = verifier の版順序仮定); F 射程 | 分岐 3 の意味 |
| S-26 | A §6 (discriminator の `supported` / `contradicted` = 「報告された rw 辺の reader version の producer と payload 先頭 8 byte の stamp producer の一致 / 不一致」); K1 (`izanagi_mocc_g2_stamp((*itr).body_, izanagi_txid)`、`izanagi_mocc_g2_emit_lineage(thid_, izanagi_txid, re)`); D §1.4 (S 行の第 5 値 = 保存 producer、L / R 対応) | witness の仕組みと判定語の意味 |
| S-27 | A §1 項 4 (publish `M:1195` 直後に S 行書出し、`unlockCLL()` `M:1207` までの区間を伸ばす); D §3 項 9 (publish 後・unlock 前に残るのは decode + abort + 確保済み vector への push、初回・capacity 増大時の `reserve` は write lock 保持中、窓の短縮量は未実測); D §2.6 (unlock 後の S 出力は残る) | 2 版の witness の位置と、lock 保持中に残る処理 |
| S-28 | A §1 項 3 (discriminator 発火 0、supported / contradicted 0 件、読み値の出所照合は未達); D §2.5 (到達点 0/0/0); G / E3 (`comparisons` 0) | witness on で cycle なし ⇒ 識別 0 件 |
| 表 A 行 1 | F 一次結果 (5/42、CP [0.039806, 0.256317]); A §2 (producer 058d0c4e) | 08-26 |
| 表 A 行 2–4 | A §5.1 表 (p058-plain 2/40 [0.006, 0.169]; e9-plain-nowit 3/40 [0.016, 0.204]; e9-instr-nowit 2/40 [0.006, 0.169]); J1 | 09-18 第 1 実験 (Q2) |
| 表 A 行 5 | C §3.2 (通常 5/120、CP [1.3665%, 9.4559%]); B2; J4 | 09-18 第 2 実験 |
| 表 A 行 6 | D §2.2 (nowit 1/60、CP [0.042%, 8.940%]); J5 / J6 | 09-19 |
| S-29 | F (42 本 = 7 batch × 6 投入、各 1 走); A §4 (round ごとに開始 arm を回転); C §2 項 1 (回転); D §1.2 (回転) | 各実験の設計 |
| S-30 | A §5.1 注 (plain 2 arm = 09-18 第 1 実験の p058-plain / e9-plain-nowit は X/P emitter が無く zero-cycle が現行 verifier で indeterminate、判定確定率ではない); F 全 42 本の分類 (当時の verifier は 37 走を certified と記録) | 分母の意味。08-26 の行は再分類の対象ではない |
| S-31 | A §1 項 4 (走あたり平均 commit 数 797,192 → 784,935 → 711,199 → 541,601 → 543,065、固定 3 秒の走あたり検出率); D §2.6 (on / off = 0.8636 / 0.8450) | 曝露量 |
| 表 B 行 1 | G (request 956466、e9e477ca、witness on、verifier cycle 0、`no-g2`); A §8 項 2 (T-1943 job は pilot が X/P を当てない時期) | 08-28 |
| 表 B 行 2–3 | A §5.1 表 (e9-instr-wit 0/40 [0, 0.088]; e9-diag-wit 0/40 [0, 0.088]) | 09-18 第 1 実験 |
| 表 B 行 4 | E / E2 / E3 / E4 (job 5905、e9e477ca + X/P、witness manifest あり、`no-g2`、2026-09-18) | 09-18 pilot cell |
| 表 B 行 5 | D §2.2 (wit 0/60 [0%, 5.963%]) | 09-19 |
| S-32 | A §5.1 (witness 追加 2 対 0 = 0.247; witness off 合算 7/120 対 instr-wit 0/40 = 0.128); D §2.3 (p = 0.500); D §1.3 (検出力 0.105) | Fisher と検出力 |
| S-33 | A §1 項 4・§6 (観測者効果の静的根拠は first witness の lock 保持中の出力、率差は有意水準に届かない); D §3 項 1 (「on では出ない」とも「60 走で引けなかった」とも両立、区別できない) | 解釈の上限 |
| 表 C 行 1–2 | A §5.2 (Q1 instr 0/56、diag 0/56、CP 上限 0.064); A §2 (Q1 configure) | 09-18 Q1 |
| 表 C 行 3 | C §3.2 (backoff 2/120 [0.2025%, 5.8909%]) | 09-18 第 2 実験 |
| 表 C 行 4–5 | D §2.2 (wit-bo1 0/60; nowit-bo1 1/60) | 09-19 |
| S-34 | C §3.3 (② backoff 対 通常 p = 0.2230864755、「低下を検出できない」「効果ゼロ・同等性は言えない」) | |
| S-35 | C §3.1 (backoff の 2 件は B2 に集中、B1 / B3 / B4 は 0/30); C §5 項 12 | |
| S-36 | A §2 (診断 patch sha `8a25bd0a…`、1,168 byte、37 行); C §1.2 (2 hunk の内容: read 側 `W_LOCKED` なら `ERROR_LOCK_FAILED` で abort、validation 側で counter 検査後に tidword 再読・epoch / tid 変化で abort); J3 | 診断 patch の内容 |
| S-37 | C §3.2 (診断 0/120 [0%, 3.0273%]); C §3.3 (① p = 0.0299507441、主比較 2 本の事前登録) | |
| S-38 | C §2 項 6 (結果別の主張範囲の逐語)、§0.1 項 5・8、§5 項 11・15 | 主張の上限 |
| S-39 | D2148 項 13 (修正 PR 見送り); C §0.1 項 5 (受理集合を縮小する介入、根因同定にも認証にも読み替えない); A §1 項 5 (診断 patch は witness on の arm でしか走らせておらず対照も 0/40) | 提案しない理由。「witness on かつ signal あり」で走らせていない = A §1 項 5 + C §0.1 項 7 |
| S-40 | S-02 と同じ出所 + R1 (数値 counter 11 個は 21/21 で 0; `integrity.clean` true 16 = 計装あり 11 + T-1892 の計装なし 5、false 5 = T-2774 の p058-plain 2 走と e9-plain-nowit 3 走); L2 `Integrity.clean()` (model.py 450–467 行: 全 counter 0 かつ `proof_surfaces.certification_gate_satisfied()` = X/P の text evidence が present (77–82 行) かつ commit witness 一致); X/P evidence 要件の導入 commit = izanagi `e4c949f08` (2026-09-03、A §5.1 注が「現行 verifier (e4c949f08、09-03)」と引く) → T-1892 (08-26) の 5 走はそれ以前の verifier の出力; A §5.1 注 (plain 2 arm は X/P emitter が無い) | 21 件の共通性質 (counter 全 0) と、archive された `clean` flag が単一の verifier 版での再評価ではないこと |
| S-41 | F (5 件: 別 thid、同 epoch、tid 差 1); A §5.1 表 (thid 列 7 対: 7/4、33/16、28/37、9/2、11/9、25/29、24/13; 同 epoch・tid 差 1); C §3.4 表 (7 走の `v_ver`: 6 走は差 1、B2/069 は (59,2577)/(59,2575) で差 2); C §4 項 12 (B1/082 の 1 対 = thread 33 と 0、7 走 14 txid の対応表は作っていない); D §2.4 (版のみ差 1、thread id 記載なし); R1 (同 epoch 21/21、tid 差 1 = 20、差 2 = 1) | 同 epoch 21 / 21、tid 差 1 は 20 / 21、thread id の確認範囲 |
| S-42 | F (key 0x1 / 0x2 / 0x6、0x0 ×3、0xb、0x49; ordinal 32 だけ前向き辺の理由が 2 本 = 0x2 と 0x55); A §5.1 (key 0x0 / 0x1 / 0x2 / 0x4、各辺 reason 1 本); C §3.4 (key 下 4 桁 0005 / 0002 / 0001 / 0003 / 0024 / 0000); D §2.4 (0x2、0x0; 0x4c と 0x1 の 2 reason、0x0); R1 (最大 key 0x55、2 reason 辺は T-1892 ordinal 32 と witlight W3-005 の 2 件) | 最大 0x55、2 reason 辺は 2 件 |
| S-43 | F (生 trace を含む job-staging 12 GB を repo 外へ退避、trace 原本の SHA-256 は `anomaly-projection.md`); A §5.1・§9 (G2 raw 336 file、manifest 一致、非 G2 raw は削除); C §3.4 (336/336 一致); C §4 項 1 (非 G2 353 走の trace は無い); D §2.4 (96 file、manifest ALL MATCH) | 保全の範囲 |
| S-44 | A §1 項 7・§6; F 射程; C §0.1 項 5 | 根因なし |
| S-45 | A §1 項 3; D §2.5; C §0.1 項 7 | 出所照合未達 |
| S-46 | A §5.1 (instr-wit 0/40 の CP 上限 0.088)、A §5.2 (0/56 の CP 上限 0.064); D §2.2 (0/60 の CP 上限 5.963%); D §3 項 1 (0 件は不在証明でない) | CP 上限だけを書き、率の範囲は書かない |
| S-47 | A §5.1 (Fisher 参考値); C §3.3 / §0.1 項 8; D §2.3 | |
| S-48 | K5; A §2 / C §1.2 / D §1.5 (producer は全部 fork commit) | |
| S-49 | C §0.1 項 2・10; D 冒頭限定 5 | |
| S-50 | C §0.1 項 8; D §3 項 8; A §5.1 (node 内相関・回転順・複数比較は未調整) | |
| S-51 | A §2 (binary sha は block ごとに異なる、命令列の一致は未確認); C §1.4; D §4 項 6 | |
| S-52 | K1 (行番号を本 wave で現物照合: 316 / 320 / 322 / 350 / 351 / 1010 / 1024 / 1038 / 1169 / 1195 / 1207); A §1 項 1 (実行順序を直接観測した走は無い) | |
| S-53 | A §3 第 1 項 (cold 読み 316〜356 の順序と「(i) の順序は排除されない」); K1 316–356 行 | |
| S-54 | A §3 第 2 項 (validation 1008〜1039: tidword 比較 1010〜1013 → counter 読み 1024 の 2 load、publish 1195 + unlockCLL 1207 が間に入ると両検査を通る、1038 は再比較ではない); K1 1024–1025 行 (`W_LOCKED && searchWriteSet(...) == nullptr` の条件) | 2 load と、自分の write set にある record は counter 検査の対象外であること |
| S-55 | T-2774 段 2 plan の逐語 `output/insights/2026-09-18/t2774-mocc-torn-read-probe/verbatim/s2-plan.md` 24 行 (操作指定: W は y の旧版を読み x を更新、R は x の旧版を読み y を更新、x ≠ y)、25 行 (両者の旧 payload 読取は相手の更新前に終了)、26–27 行 (W の validation は R の y 施錠前、R の validation は 1010–1013 が T0 を受理した後・1024 より前に W の 1195・1207 が終了)、34 行 (cold・RLL 空・各 write set 一要素); A §3 第 3 項; A §1 項 1 (実走で実証していない) | draft の S-55 は plan の**操作指定から再構成した条件付きの例**であり、「相手の / 互いの read key を自分の write set に含めない」という plan 24 行末尾・README §3 の文言は draft に写していない (README §3 の「相手の read key」を字義どおり適用すると操作指定と矛盾し、plan の「互いの」も一義的でないため、文言でなく操作指定 (W は x だけ書き R は y だけ書く) を出所にする) |
| S-56 | A §3 第 4 項 ((i) が commit まで届くには (ii) も要る) | |
| S-57 | A §3 第 3 項末尾 (同 epoch・tid 差 1 は `max_rset_` (1038) と commit tid = 最大版 + 1 の帰結であって必然ではない)、第 5 項 (形の一致は (ii) 固有の証拠ではない); C §3.4 B2/069 (差 2 の 1 件); R1 (20 / 21) | 20 / 21 件の pattern として書く |
| S-58 | A §1 項 4 (witness は publish 直後・unlock 前に S 行を挟み、R の 2 load が跨ぐべき区間を伸ばす) | |
| S-59 | A §1 項 1 (実行順序の直接観測なし)、§1 項 5 (診断効果・寄与・根因は判定できない); D §3 項 9 (窓の短縮量は未実測) | |
| S-60 | A §10 (job dir の再現資料); C §6.2; D §5.1 (`W.bundle`、manifest、result.json) | |
| S-61 | L1 / L2 (verifier の所在 `orchestrator/verifier/`); A §2 / §10 と C §1.4 / §6.2 (runner `t2774_probe.py` v4 / `t2779_probe.py` v5 の原本は repo 外 job dir、repo 内は `verbatim/` の逐語写し); K4 (`include/trace.hh`); F (`include/trace.hh` が形式を明記) | runner は repo 外の archive、repo 内は写し |
| S-62 / S-63 | D2148 項 13 (報告まで); A §1 項 7 (三分岐) | 事実命題は S-24 の再掲のみ |

## 2. draft に書かなかったこと (依頼の「書かないこと」と、出所が無い事柄)

- 根因の確定、修正提案 (診断 patch は「観測」として D 節に置き、提案しないと同段落で書いた)。
- 機体の CPU model・memory (J4 の bindings に無い)。
- 上流 master の後続 commit との差分、master 実走の結果 (どちらも無い)。
- witlight 2 走の thread id (D にも D3 / D4 の anomaly にも無い)。
- 性能値 (規律 1)。[T-1892] / [T-2774] / [T-2779] / witlight の率の合算値 (規律 7: 表では各 arm を別行に置き、S-32 の 7/120 だけは A §5.1 が自ら計算した参考値)。
