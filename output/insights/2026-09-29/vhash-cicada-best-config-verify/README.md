# VHash 論文の比較相手 Cicada の観測最良設定を正しさの判定器に掛けた — 実走した 32 run (異なる条件は 30)すべてで巡回なし (上限 indeterminate)、同じ設定に壊しを重ねた正例 3 本は検出・帰属 (2026-09-29)

authority: none / default_effect: no-state-change (可変状態の正本は worklog 末尾と現行 phase doc)。
wave `dev-wave-vhash-cicada-best-config-verify` (branch `worktree-dev-wave-vhash-cicada-best-config-verify`)、起点 local main `8fe87f852` (開始 gate fresh rc 0、2026-09-29 21:5x JST)、CCBench submodule = pin C `68106660` (動かしていない)。
job dir `/work/1/SFC/tanab/tmp/vhash-cicada-best-config-verify-2026-09-29/` (Codex の prompt と報告、repo 外の起動器と診断 patch、計測の raw trace と stdout / stderr、集計 script)。依頼は `/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_20.txt` (本 dir `verbatim/request-md_20.txt` に逐語)。
段 1〜6 の全文は `verbatim/` (段 1 brief、段 2 plan、段 3 相談 2 本、段 4 裁定、段 6 レビュー 2 本と焦点再レビュー、段 6 裁定、J2 の投入判断)。計測結果の原本 JSON は `evidence/` (起動器が job ごとに書いたもの)。
逐語の正規化 5 件 (`git diff --check` 抵触のため、Markdown 改行用の行末の半角空白だけを除去、可視文字不変。原文は job dir の同名元 file `consult-a.md`・`consult-b.md`・`focus.md`・`review-a.md`・`review-b.md`、復元はその file を写す):
`verbatim/s3-consult-a.md` 18 行、原文 sha256 `40ac88ef3ec38a7ae24e09520a3f5ca4b365976372e3cce9e6f3d9b0012f40f8`・5,692 byte → `f00d7bfcdc2452721b2f84a328cecbef3d8f0cdf0d9d0162291d0c279b6cb975`・5,656 byte。
`verbatim/s3-consult-b.md` 21 行、`53a3c2e3bd628ec202b4fdc7402cf9d5bb2bf62b68620aa9fdd613d115596403`・7,830 byte → `9656f0a7088642fcae92323e222c9f9e30aaf889864397efa31c6cdfacbcd356`・7,788 byte。
`verbatim/s6-focus-review.md` 6 行、`d749bdd63ddd95931188faa7dfbc5799fe01bbc271201c523f7fa37c2da28c35`・4,159 byte → `3c52c335d8611275e15d3516d737181f177c09e79962036df238c2c11c837355`・4,147 byte。
`verbatim/s6-review-a.md` 6 行、`7fc4c7ac7d2c098628a9d6cb6589efae0bff945c5063f559c7587e89da47205b`・2,263 byte → `ca10308cfc034366df19d4f8fddb06fe74f30842bc5afd2426962f7aa49c090e`・2,251 byte。
`verbatim/s6-review-b.md` 15 行、`d9fd3981864e2b280f47e4b1f503b49c45d8619d0186ff72ca91d40973e2deb7`・3,765 byte → `b1dbdf607a3625a07e4de3f4ec398939abbd7f73a0067041e7bf9392fddf473a`・3,735 byte。

**この資料は正しさの検査の記録であり、性能値を含まない。** trace を入れた build の throughput は測っていない (絶対規律 1)。

## 1. 依頼と結論

依頼 (VHash 論文の並行 wave md_20、台帳 T-2902): md_11 (`output/insights/2026-09-29/vhash-cicada-baseline-tuning/README.md`) が決めた Cicada の観測最良設定は既定より 2〜4.5 倍速いが、正しさ未検証の診断値である。論文の主比較の相手にする前に、md_3 の trace (`patches/instr-cicada-trace.patch`、D2279) を当てて判定器に掛ける。先に INLINE_VERSION_OPT=1 の経路で trace が正しく出るかを確かめる。巡回が出たら 1 軸ずつ切り分け、出なければ「その条件で巡回なし (上限 indeterminate)」と書き、certified とは書かない。

結論:

1. **実走した 32 run (異なる条件は 30)のすべてで、stock の最良設定と既定は判定器を通った (巡回 0・integrity の数値項目 0・C 行 = commit 数・全 W の版 > 初期版)。** 最良設定 BEST (rr5・rr50・rr95 用) と BEST100 (100 操作型用)、比較のための既定 CTRL を、tuple 200 の高競合 (thread 4・48) と md_11 と同じ tuple 1M・thread 48 で走らせた (§4)。判定語は「その条件で巡回なし (上限 indeterminate)」で、certified ではない。
2. **INLINE_VERSION_OPT=1 の経路は実際に通り、trace に記録されていた。** stock の BEST 14 run では commit した読みの 5.2〜59.4%、書きの 4.7〜36.9% が tuple 内の inline slot の版だった (§3.2)。
3. **commit した読みについて、版を選んだ瞬間・登録した瞬間・commit の瞬間に比べた版の wts に食い違いは観測されなかった。** repo 外の診断 patch (trace の行は変えない) で数え、全 run で食い違い 0、読み手の基準時刻より新しい版の登録 0、md_3 の `READ_WTS_MISMATCH` も 0 だった。読んだ中身 (body) と再利用の書き換えの途中は観測していない (§3)。
4. **同じ設定に既存の壊し (read set の再検査を飛ばす) を重ねた正例 3 本は、すべて巡回として検出され、壊した経路に帰属した** (BEST rr50 の thread 4・48、BEST100 の 100 操作型 thread 4、§5)。この設定の trace と判定器に検出力があることの根拠である。
5. **したがって、この検査の範囲では BEST・BEST100 を主比較の相手から外す理由は見つからなかった。** ただし md_11 の主比較条件 (tuple 1M・thread 48・走行 3 秒) そのものは検査していない (走行は 1 秒)。trace は版への依存を記録するだけで、読んだ中身 (body) は観測していない。inline slot の取り違えを狙った正例は作っていない (§7)。
6. **trace patch は直していない。** 記録されない経路は見つからなかった。

## 2. 設定と条件

| 名前 | BACK_OFF | INLINE_VERSION_OPT | INLINE_VERSION_PROMOTION | REUSE_VERSION | WRITE_LATEST_ONLY | 出典 |
|---|---:|---:|---:|---:|---:|---|
| BEST | 0 | 1 | 0 | 1 | 0 | md_11 §6 の rr5・rr50・rr95 の観測最良 |
| BEST100 | 0 | 0 | 0 | 0 | 0 | md_11 §6 の 100 操作型の観測最良 |
| CTRL | 1 | 0 | 0 | 1 | 0 | md_11 の control (CMake 既定の正準点) |

- build: pin C + `patches/instr-cicada-trace.patch` (bytes 不変) + 診断 patch (§3.1)、正例はさらに `patches/broken-cicada-skip-read-recheck.patch` (bytes 不変)。TRACE=1、ADD_ANALYSIS=0、SINGLE_EXEC=0、target `ycsb_cicada.exe`、Release。
- **設定の束縛:** configure の引数は共通引数から `-DCCBENCH_BACK_OFF=` を取り除いてから 5 軸と SINGLE_EXEC を 1 度ずつ与え、同じ key の重複を起動前に拒否する (CMake の後勝ちに頼らない)。build ごとに CMake cache の 8 key と、`ycsb_cicada.exe` の 3 TU (transaction.cc・util.cc・ycsb_cicada.cc) の compile command の -D を期待値と照合した。全 build で一致 (`evidence/` の `builds.*.binding_valid`・`cmake_cache`・`compile_binding`)。
- **実行条件の束縛:** 全 flag を argv に明示し、stdout の `#FLAGS_*` 行と照合した (md_11 と同型)。全 run で一致 (`flag_binding.matched`)。
- 共通 flag: `ycsb_zipf_skew=0.9`・`ycsb_rmw=0`・`extime=1`・`group_commit=0`・`clocks_per_us=2100`。workload は rr5・rr50・rr95 (各 10 操作) と rr95・100 操作 (md_11 の W1〜W4)。
- gc_inter_us: BEST は md_11 の最良 GC (rr5・rr50 は 100、rr95 は 10) と 10、BEST100 は 1000 (md_11 の最良) と 10、CTRL は 10。
- 計算ノード: Pegasus gen_S (generic dispatch、repo 外の起動器を job ごとの detached checkout から投入)。login node では build も計測もしていない。

## 3. trace の網羅と忠実性

### 3.1 何を確かめたか

md_3 の trace は、read set に登録した版の wts を R 行に、自分の wts を W 行に出す。INLINE_VERSION_OPT=1 では版の 1 つが tuple 内の固定 slot (inline slot) にあり、GC が返した slot を次の書き手が再利用する。段 2・3 の検討で、次の 2 つの窓が静的には否定できないと分かった (`verbatim/s2-plan.md` §1、`verbatim/s3-consult-a.md` A1〜A3)。

- 読み手が scan で版を選んでから read set に登録するまでの間に slot が再利用されると、登録時の wts が「選んだ版」と違う値になりうる。
- validation の再検査は版を pointer で比べるので、slot の再利用は ABA として検査を通りうる。md_3 の `READ_WTS_MISMATCH` (登録時と commit 時の比較) は、登録前に再利用された場合を見逃す。

そこで repo 外の使い捨て診断 patch `diag-cicada-inline-fidelity.patch` (Codex author、job dir の `launcher/`、sha256 `d08966ad3f4e556ab92911052a4330d399b3eee1dfbe5b3924dbfd50bca2cae9`) を、この wave の全ての検査 build に重ねた。追加は `#if TRACE` の内側だけで、trace の C / R / W / E 行の中身と順序は変えない (Codex author が instr patch 単独と diff で確認)。stock の版選択の判定・分岐は変えず、比較に使った値を変数に受けるだけにした。数えるのは commit した txn の読み書きについて:

| 名前 | 意味 |
|---|---|
| `R_INLINE` / `W_INLINE` | 登録した版 / 新しく作った版が inline slot だった件数 (OPT=1 の build だけ) |
| `SEL_REG` | 選んだ瞬間の wts (scan の最後の比較に使った値) ≠ 登録時に保存した wts |
| `SEL_COMMIT` | 選んだ瞬間の wts ≠ commit 時にその版から読み直した wts |
| `REG_FUTURE` | 登録時の wts > その読みの基準時刻 (書く txn は自分の wts、読むだけの txn は rts) |

wts は書き手ごとに一意で、slot の再利用は wts を上書きする。したがって `SEL_COMMIT` = 0 は、各読みについて「選んだ瞬間から commit までの間に、その版の object が別の版へ再利用されなかった」ことを示す。md_3 の `READ_WTS_MISMATCH` (登録時 ≠ commit 時) も併せて記録した。

### 3.2 結果

32 run (異なる条件は 30)の stock と 3 本の正例、計 35 run のすべてで `SEL_REG`・`SEL_COMMIT`・`REG_FUTURE`・`READ_WTS_MISMATCH` が 0 だった (§4 の表、`evidence/` の `diag_fidelity`・`read_wts_mismatch`)。BEST の run の inline slot の件数 (R 行・W 行に対する割合):

| run (BEST) | R 行 | R_INLINE | W 行 | W_INLINE |
|---|---:|---:|---:|---:|
| rr50・tuple 200・t4・GC 10 | 1,718,001 | 441,071 (25.7%) | 1,825,607 | 443,942 (24.3%) |
| rr5・tuple 200・t48・GC 10 | 315,450 | 24,349 (7.7%) | 6,028,926 | 428,199 (7.1%) |
| rr95・tuple 200・t4・GC 10 | 5,916,399 | 2,313,424 (39.1%) | 351,919 | 129,714 (36.9%) |
| rr95・tuple 1M・t48・GC 10 | 9,601,071 | 5,698,612 (59.4%) | 509,032 | 143,712 (28.2%) |
| rr50・tuple 1M・t48・GC 100 | 6,034,267 | 2,428,804 (40.3%) | 6,062,541 | 1,937,491 (32.0%) |

stock の BEST 14 run の範囲は R 行で 5.2〜59.4%、W 行で 4.7〜36.9% (原本 JSON の `diag_fidelity` から親が job dir の `check_ratios.py` で計算。正例 2 本を含めても同じ範囲)。inline の版の読み書きは記録されており、記録されない経路は見つからなかった。**trace patch の修正は要らなかった。**

### 3.3 この確認の限界

- 3 点比較は「選んだ瞬間」と「commit の瞬間」の 2 時点で版 object の同一性を見る。再利用の書き換えの途中 (wts と body の書き換えの間) に中身を読んだ場合は区別できない。
- trace は版の ID を記録し、読んだ中身 (body) を観測しない。同じ txn 内の再読は R 行を増やさない (read set から返す)。
- 診断 patch 自身が各読みで数語の store と commit 時の数回の比較を足すので、診断なしの TRACE=1 build と完全に同じ実行ではない (どちらも性能値には使わない)。

## 4. 判定 — stock の 32 run (異なる条件は 30)

合否は結果を見る前に段 4 で固定した (`verbatim/s4-ruling.md` R6): rc 0・timeout なし・build と flag の束縛一致・判定器 error なし・巡回 0・integrity の数値項目 (md_3 の 11 項目) 全 0・C 行 = stdout の commit 数・全 W の版 > initial_wts・`READ_WTS_MISMATCH` 0・診断 3 値 0。32 run すべてが合格 (`stock_pass` true)。判定器の上限は indeterminate (Cicada に X / P / I の証拠面が無い、D2279)。

| job | build | workload | tuple | thread | GC µs | commit (= C 行) | trace 行 | 巡回 | 判定器 s |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| L0 | BEST | rr50・10 操作 | 200 | 4 | 10 | 391,481 | 4,326,570 | 0 | 10.7 |
| L0 | BEST100 | rr95・100 操作 | 200 | 4 | 1000 | 52,609 | 3,043,561 | 0 | 5.3 |
| L0 | CTRL | rr50・10 操作 | 200 | 4 | 10 | 175,110 | 1,935,160 | 0 | 4.6 |
| L0 | CTRL | rr95・100 操作 | 200 | 4 | 10 | 32,949 | 1,906,303 | 0 | 3.3 |
| J1-W1 | BEST | rr5・10 操作 | 200 | 4 | 100 | 328,956 | 3,561,556 | 0 | 9.4 |
| J1-W1 | BEST | rr5・10 操作 | 200 | 48 | 100 | 703,203 | 7,615,393 | 0 | 17.1 |
| J1-W1 | BEST | rr5・10 操作 | 200 | 4 | 10 | 323,219 | 3,499,217 | 0 | 9.2 |
| J1-W1 | BEST | rr5・10 操作 | 200 | 48 | 10 | 718,553 | 7,781,482 | 0 | 18.1 |
| J1-W1 | CTRL | rr5・10 操作 | 200 | 4 | 10 | 178,161 | 1,928,893 | 0 | 4.9 |
| J1-W1 | CTRL | rr5・10 操作 | 200 | 48 | 10 | 435,023 | 4,709,466 | 0 | 10.1 |
| J1-W2 | BEST | rr50・10 操作 | 200 | 4 | 100 | 394,421 | 4,359,896 | 0 | 10.9 |
| J1-W2 | BEST | rr50・10 操作 | 200 | 48 | 100 | 313,084 | 3,460,458 | 0 | 5.9 |
| J1-W2 | BEST | rr50・10 操作 | 200 | 48 | 10 | 313,035 | 3,460,568 | 0 | 5.9 |
| J1-W2 | CTRL | rr50・10 操作 | 200 | 48 | 10 | 325,651 | 3,598,706 | 0 | 6.1 |
| J1-W3 | BEST | rr95・10 操作 | 200 | 4 | 10 | 709,197 | 7,686,712 | 0 | 18.0 |
| J1-W3 | BEST | rr95・10 操作 | 200 | 48 | 10 | 1,374,444 | 14,897,731 | 0 | 21.4 |
| J1-W3 | CTRL | rr95・10 操作 | 200 | 4 | 10 | 388,130 | 4,206,838 | 0 | 9.5 |
| J1-W3 | CTRL | rr95・10 操作 | 200 | 48 | 10 | 218,019 | 2,362,505 | 0 | 3.1 |
| J1-W4 | BEST100 | rr95・100 操作 | 200 | 48 | 1000 | 19,701 | 1,141,564 | 0 | 1.0 |
| J1-W4 | BEST100 | rr95・100 操作 | 200 | 4 | 10 | 54,602 | 3,158,998 | 0 | 5.5 |
| J1-W4 | BEST100 | rr95・100 操作 | 200 | 48 | 10 | 20,193 | 1,168,433 | 0 | 1.0 |
| J1-W4 | CTRL | rr95・100 操作 | 200 | 48 | 10 | 34,182 | 1,977,130 | 0 | 1.6 |
| J1-POS | BEST | rr50・10 操作 | 200 | 48 | 10 | 304,636 | 3,366,331 | 0 | 5.8 |
| J1-POS | BEST100 | rr95・100 操作 | 200 | 4 | 1000 | 53,543 | 3,097,307 | 0 | 5.4 |
| J2 | BEST | rr5・10 操作 | 1M | 48 | 100 | 1,268,397 | 15,109,669 | 0 | 41.6 |
| J2 | BEST | rr50・10 操作 | 1M | 48 | 100 | 1,218,163 | 14,533,134 | 0 | 34.6 |
| J2 | BEST | rr95・10 操作 | 1M | 48 | 10 | 1,019,920 | 12,149,943 | 0 | 19.8 |
| J2 | BEST100 | rr95・100 操作 | 1M | 48 | 1000 | 101,991 | 9,794,845 | 0 | 11.5 |
| J2 | CTRL | rr5・10 操作 | 1M | 48 | 10 | 975,684 | 11,623,353 | 0 | 31.4 |
| J2 | CTRL | rr50・10 操作 | 1M | 48 | 10 | 670,809 | 8,003,215 | 0 | 18.0 |
| J2 | CTRL | rr95・10 操作 | 1M | 48 | 10 | 1,690,052 | 20,133,024 | 0 | 34.8 |
| J2 | CTRL | rr95・100 操作 | 1M | 48 | 10 | 64,147 | 6,161,454 | 0 | 6.8 |

- L0 は fix 後の起動器で取り直した run (§6)。J1-POS の stock 2 run は正例の同 job の対照で、BEST rr50・t48・GC 10 は J1-W2 と、BEST100 rr95・100 操作・t4・GC 1000 は L0 と同じ条件を別 job でもう 1 度走らせたもの (4 run とも合格)。このため 32 run のうち異なる条件は 30。
- 事前登録した W4 の第二尺度 (commit < 1,000 なら tuple 1,000 を追加) は、W4 の commit が最少でも 19,701 だったので発動していない。
- 巡回が出た条件は無いので、1 軸の切り分け (CTRL から B0 だけ・O1 だけ・R0 だけを動かした build) は走らせていない (起動器には登録済み)。

## 5. 正例 — 同じ設定に壊しを重ねた 3 本

壊し: 既存の `patches/broken-cicada-skip-read-recheck.patch` (md_3。validation の read set 再検査で、読んだ版が今の可視版と違っても abort しない)。md_3 は既定に近い設定でしか確かめていなかったので、BEST と BEST100 の build に重ねて取り直した。

帰属規則 (段 4 裁定 R5): 壊しの事象 (`tx_wts`・key・読んだ版 `a_wts`・再検査が見た版 `b_wts`) ごとに、判定器の代表 witness の巡回の中に、C 行の版が `tx_wts` の txn から出る key 上の rw 辺で、読んだ版 = `a_wts`、かつ辺の終点の txn がその key に版 `b_wts` の W 行を持つもの (raw trace で照合)。分類「期待した経路で検出」= non-serializable かつ帰属する組が 1 以上、かつ正例 run 自身の integrity 数値項目 0・C 行 = commit 数・異常終了なし・flag 一致・事象行を打ち切らず全件保存、かつ同じ job の同じ条件の stock 対照が合格。

| 正例 | 判定 | 巡回 | reached / changed / committed | 帰属した (辺, 事象) の組 | 自身の integrity・C = commit | 対照 | 分類 |
|---|---|---:|---|---:|---|---|---|
| BEST rr50・tuple 200・t4・GC 10 (L0) | non-serializable | 45,195 | 1,868,574 / 85,818 / 83,430 | 21 | 全 0・409,884 = 409,884 | 同 job の BEST 同条件 (合格) | 期待した経路で検出 |
| BEST rr50・tuple 200・t48・GC 10 (J1-POS) | non-serializable | 63,273 | 6,699,765 / 756,427 / 308,387 | 18 | 全 0・681,099 = 681,099 | 同 job の BEST 同条件 (合格) | 期待した経路で検出 |
| BEST100 rr95・100 操作・tuple 200・t4・GC 1000 (J1-POS) | non-serializable | 17,548 | 4,095,595 / 131,589 / 124,379 | 49 | 全 0・74,507 = 74,507 | 同 job の BEST100 同条件 (合格) | 期待した経路で検出 |

- 「帰属した組」は、判定器が報告する代表 witness (巡回 20 件) の rw 辺と事象の一致の数で、1 つの witness が複数の事象と一致すると複数に数える。md_3 の「代表 witness 20 件中 20 件」とは数え方が違う。
- 親が各正例の例 3 件を job dir の `check_attr.py` で検算した: 事象の `a_wts`・`b_wts` を上下 32 bit に分け、witness の辺の読んだ版・次の版・key と 9 件中 9 件が一致。
- 正例 run でも診断 3 値と `READ_WTS_MISMATCH` は 0 だった (壊しは版の選択と記録を変えないため)。
- **正例が示すのは「read set の再検査を壊した履歴を、この設定の trace と判定器で検出できる」ことまで。** inline slot の再利用を狙った壊し (slot を早く返す等) は作っておらず、その取り違えの検出力は未検査である (段 3 相談 A4、段 2 plan §5)。

## 6. 工程・レビュー・修正

- 段 2 plan 1、段 3 相談 2 (A: 正しさ主張と偽の緑、B: 実効性・過剰・規模)。採用した主な修正: inline 件数だけでは忠実性の確認にならない → 3 点比較の診断 (A1・B3)、SINGLE_EXEC と実行時 flag の束縛 (A5・B2)、b_wts まで照合する帰属 (A4)、BEST100 の正例 (B4)、結論を実走条件ごとに書く (A6・B1)、TRACE=0 同一性を落とす (B6)。全文は `verbatim/s4-ruling.md`。
- 段 5: Codex author 1 本が repo 外の起動器 (md_17 の起動器の写しを拡張) と診断 patch を書いた。repo の tracked file は変えていない。
- 段 6: レビュー 2 本 (A: 正しさ主張と偽の緑、B: 過剰・削除と実行可能性)。採用 3 件を fix 1 巡で直した — A1 (判定器の後段で例外が起きたとき、合否は偽なのに分類が「巡回なし」になりうる経路)、A2 (巡回を出した stock の専用分類)、B3 (W4 の追加 run の例外が元 run の記録を消す)。焦点再レビューは 3 件とも closed、新しい所見 C1 (分類に第 5 の「不合格」がある) は偽の緑を作らないので直さず、「巡回以外の検査が外れた失格」として扱うと結果を見る前に固定した (該当 run は 0)。全文は `verbatim/s6-ruling.md`。
- 一次資料の独立レビュー 1 本 (`verbatim/s6-doc-review.md`): §3.2・§4・§5 の数値と量化は原本 JSON とすべて一致。所見 R1 (§1 の「記録が正しい」は診断の射程より広い) と R2 (§9 の Elapse の出典) に沿って本文を直した。
- L0 は fix 前の起動器 (sha256 `00070df6…daab`) で 1 度走らせ (`evidence/l0-a-result-BCV-L0.json`、stock 4 run 合格・正例は検出)、fix 後の起動器 (sha256 `895c1fa3dc6241a549c062144ad09bffe7e521d14c8290571132f34faa48fde5`) で取り直した。§4・§5 の値はすべて fix 後の版の run (`evidence/` の各 JSON の `launcher_sha256`)。
- 変異 matrix: repo の実装面の差分が無いので免除 (DW-S04、段 4 裁定 R10)。起動器の照合・帰属・分類は、Codex author が手作りの入力で正例と負例 (CMake key の重複、compile define 不一致、flag 不一致、b_wts 不一致、判定器 error、巡回 3 件、診断値の非 0) を実走して確かめ、実系の検出力は §5 の正例で示した。

## 7. 確かめたこと・確かめていないこと

確かめたこと:
- BEST・BEST100・CTRL の stock の YCSB 履歴が、表 §4 の 32 run (異なる条件は 30)で巡回 0・integrity 0・commit 数一致・全 W > 初期版。
- INLINE_VERSION_OPT=1 の inline slot の版の読み書きが trace に出ること、commit した読みについて選んだ瞬間・登録・commit の 3 時点で比べた版の wts に食い違いが観測されなかったこと (§3。body と書き換えの途中は範囲外)。
- 同じ設定に read set 再検査の壊しを重ねた 3 本を判定器が non-serializable とし、壊した経路に帰属できること (§5)。
- build の 5 軸と SINGLE_EXEC、実行時 flag が意図どおりであること (§2)。

確かめていないこと:
- **md_11 の主比較条件そのもの。** md_11 は tuple 1M・thread 48・走行 3 秒・trace なしで測った。本 wave の J2 は tuple 1M・thread 48 だが走行 1 秒で、trace build は trace の書き出しで遅くなる (commit は 1 run 6 万〜170 万)。短い走行と高競合 (tuple 200) で巡回が出なかったことを、長い走行での不在の証明とは書かない。
- **certified。** 判定器の上限は indeterminate (D2279)。「serializable と認定した」とは書かない。
- **読んだ中身 (body) の正しさ。** trace は版の ID しか記録しない。版 ID が正しくても、再利用の書き換えの途中の中身を読んだ場合は見えない (§3.3)。
- **inline slot の取り違えに対する検出力。** その型の正例は作っていない (§5)。
- **TRACE=0 の命令列の同一性 (BEST・BEST100 の CMake 値で)。** 取っていない (段 4 裁定 R7。本 wave は性能値を出さず、instr patch の bytes も変えていない)。md_3 は既定に近い値で YCSB の 3 TU の一致を確かめている。
- md_11 の他の設定 (build できた 16 点のうち BEST・BEST100・CTRL 以外)、skew 0.9 以外、YCSB 以外 (TPC-C 等)、scan と phantom、insert / delete。
- GC 間隔の範囲: BEST は 10 と md_11 の最良値、BEST100 は 10 と 1000、CTRL は 10 だけ。GC 10,000 µs は走らせていない。
- 今回の検索式と対象で見つからなかったもの (例: 記録されない読み書きの経路) は、その範囲での陰性であって全経路の不存在証明ではない。

## 8. 論文の次の版に使える結論

- 構成 A (基準 Cicada) の最良設定 BEST・BEST100 は、実走した高競合 (tuple 200、thread 4・48) と tuple 1M・thread 48 (走行 1 秒) の小走行で、izanagi の判定器で巡回なし (上限 indeterminate) だった。同じ設定に壊しを重ねると検出される。「正しさ未検証」の注記は「この範囲で巡回なし (indeterminate、certified ではない)」に置き換えられる。
- 最良設定の中心の BACK_OFF=0 は abort を増やすが、abort した txn は trace に出ないので判定に影響しない。INLINE_VERSION_OPT=1 の inline slot の版も記録され、再利用による版の取り違えは観測されなかった。
- 主比較の本番条件 (走行 3 秒以上) での検査は、評価の本走で同じ起動器を trace build に使えば追加できる (1 条件あたりの判定器所要は本 wave で最長 41.6 秒)。

## 9. 計算

計算ノードの job (Pegasus gen_S)。request ID・開始時刻・Elapse の出典は job dir の dispatch ログ `runs/<tag>.log` に dispatcher が写した NQSV の記録 (`evidence/*.json` の `started_at`・`ended_at` は起動器自身の実行時刻で、Elapse の field は持たない):

| tag | request | 内容 | 開始 (JST) | Elapse |
|---|---|---|---|---:|
| l0-a | 36209.nqsv | 生死確認 L0 (fix 前の起動器) | 22:47:54 | 122 s |
| l0-b | 36273.nqsv | L0 の取り直し (fix 後) | 23:06:37 | 120 s |
| j1-w1 | 36274.nqsv | J1 rr5 | 23:06:37 | 164 s |
| j1-w3 | 36275.nqsv | J1 rr95 | 23:06:37 | 125 s |
| j1-w4 | 36276.nqsv | J1 rr95・100 操作 | 23:09:06 | 65 s |
| j1-w2 | 36289.nqsv | J1 rr50 | 23:09:42 | 91 s |
| j2-a | 36290.nqsv | J2 tuple 1M・t48 | 23:10:46 | 330 s |
| j1-pos | 36297.nqsv | 正例 2 本と対照 | 23:16:07 | 148 s |

合計 1,165 s (約 19 node 分)。2 node 時間を大きく下回るので、ユーザー確認の対象外。J2 の投入判断 (1 run の判定器予測 600 秒未満、全 Elapse 6,000 秒未満) は結果を見る前に `verbatim/j2-decision.md` に記録した。
Codex (gpt-6-sol): 段 2 plan 1、段 3 相談 2、段 5 author 1、段 6 レビュー 2・fix 1・焦点再レビュー 1。
