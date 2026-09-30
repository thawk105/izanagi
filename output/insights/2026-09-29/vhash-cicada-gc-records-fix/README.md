# stock Cicada の TPC-C (Delivery を含む並行走行) が落ちる欠陥を、原因を実測で確かめてから直した — gc_records の ERR は abort した後発の削除版が版鎖に残るため。修理後に scan の空 key という 2 つ目の既存欠陥が見え、これも直した。修理版で並行下の削除を含む trace が初めて判定器に通った (巡回 0・存在履歴違反 0) (VHash 論文の前提 G0 の続き、T-2908、2026-09-29〜30)

authority: none / default_effect: no-state-change (可変状態の正本は worklog 末尾と現行 phase doc)。
wave `dev-wave-vhash-cicada-gc-records-fix` (branch `worktree-dev-wave-vhash-cicada-gc-records-fix`)、起点 local main `8fe87f852` (開始 gate fresh rc 0、2026-09-29 21:5x JST)。izanagi の CCBench gitlink は pin C `68106660` のまま (動かしていない)。
job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-gc-records-fix/` (brief・plan・相談・裁定・Codex の prompt と報告・repo 外起動器・使い捨て patch・計測の原本 JSON と raw・CCBench の bundle)。段 1〜6 の文書は `verbatim/` に逐語。
**依頼の正本:** 起動時に読んだ `/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_23.txt` (21:43 JST に読んだ版)。この file は 21:59 に VHash 親セッションが別の依頼 (hot 配置、構成 B) で上書きした (親セッションが誤りを認め、本 wave の継続を確認)。読んだ本文は `verbatim/request-md_23.txt` に逐語。
分担: 並走 wave md_19 (cicada build issues fix) の依頼は同じ欠陥を項目 3 に含んでいたが、md_19 と合意して本 wave が専任した (md_19 は build 不具合 2 件だけ)。
前段は `output/insights/2026-09-29/vhash-cicada-verifier-ext/README.md` (md_17、D2294) §5。

## 1. 結論

1. **原因 (実測):** 2 本の Delivery が同じ NewOrder 行を削除し合い、後発 (wts が大きい側) が先発の削除版 D1 の上に自分の削除版 D2 を install した後、validation の read set 再検査で abort する。`writeSetClean()` は install 済みの版を aborted にするだけで版鎖に残すので、D2 が最上段に残り、D1 を commit した thread の `gc_records()` が「最新版が deleted でない」と見て `ERR` する。使い捨ての診断 patch で ERR の直前の版鎖を出した結果、10 回中 10 回がこの形だった (表 = NewOrder、aborted の版は全部 op DELETE・abort 段は全部 read set 再検査、最初の非 aborted 版は ERR した thread 自身が commit した削除版、1 回は aborted が 2 段重なっていた) (§3)。md_17 の仮説どおりで、仮説の「(b) の deleted 検査で abort」の経路は観測されなかった。
2. **修理 1 (gc_records):** `gc_records()` が最上段から続く aborted の版を何段でも読み飛ばし、到達した版が deleted なら従来どおり回収、それ以外 (null・pending・committed) は従来どおり `ERR`。最上段の wts による待機判定は変えない。validation・commit・abort の経路は変えない (§2)。
3. **修理 2 (scan の key):** 修理 1 で走行が最後まで進むと、`scan()` が結果の key を最新版の body から取るため、最上段に body の無い削除版がある行で key が空になる既存欠陥が表に出た (trace の R 行の key が空で判定器が parse error、read set の key 照合も誤りうる)。key を tuple 作成時に複写される `Tuple::body_` から取り、それが空なら従来どおり最新版から取る (§2)。
4. **完了判定 (事前登録どおり、最終 patch の V4):** 修理版は F cell × 4 thread 10/10・8 thread 10/10 が完走し、同じ job の無修理版は 4 thread 5/5・8 thread 4/5 が `gc_records` の ERR で落ちた。修理版 + md_17 の計装の F cell × 4 thread の trace 3 本は、判定器で巡回 0・integrity の数値項目 12 個 (存在履歴違反を含む) すべて 0・C 行 = commit 数・READ_WTS_MISMATCH 0、削除 (W op D) は 890〜3,570 件を 4 thread 全部が出し、修理 1 の読み飛ばし回収は同じ走行で 179〜607 回発火した。**md_17 で取れなかった「並行下の削除」の履歴を初めて判定器に通した。** 削除を含まない M・R2 cell は修理前後とも合格で判定は変わらない (§4)。
5. **判定器の検出力:** read set 再検査を壊した既存の patch を修理版に重ねると、同じ F cell × 4 thread で判定器が non-serializable (巡回 386 件、V3 では 586 件) を返した。削除を含む並行 TPC-C の履歴でも異常を検出できる (§4)。
6. **絶対規律 1:** (F + 修理 2 本) と (F + 計装 2 本 + 修理 2 本) の TRACE=0 は tpcc の 3 TU で compile command・命令列・前処理が一致した。計装が `#line 909`・`#line 934` を固定値で置いていても、修理で増えた行の後ろに `__LINE__` を使う行が無いので命令列は変わらない (§4)。
7. **置き場:** CCBench の local branch `izanagi-cicada-gc-records-fix` = F `25898d00` → `dd6ea5144fc0…` (修理 1) → `81fc4a84cc85…` (修理 2)。pin C のうちに使えるよう、同じ差分を `patches/fix-cicada-gc-records.patch`・`patches/fix-cicada-gc-records-scan-key.patch` として置いた (pin C・C1'・F とその計装の後に厳密適用できる)。上流 CI の 2 本を手元で CI と同じ手順で通した: format は clang-format 14 の 2 通りで 213 file・rc 0、build は CI image `:ci` の Release・全 protocol で rc 0・CCBench 本体の警告 0 (§5)。push・PR・pin の前進は人間の手番 (§7)。
8. **修理と無関係の既存欠陥 U (記録のみ):** `abort()` が insert した tuple を `delete` した直後に `writeSetClean()` が同じ tuple に書く use-after-free を ASan が検出した (削除の無い M cell の stock でも出る)。本 wave では直さず次の一手に置いた (§6)。

## 2. 修理の中身

`cc/cicada/transaction.cc` だけを変える (pin C = F の cc/cicada)。

- 修理 1 (`patches/fix-cicada-gc-records.patch`、sha256 `2c9cb880fee86fc67c04cb34a1a44456e13f72f2bdcd9d17c0e7b75892d102d5`、`gc_records()` の +5 / −1 行):
  `if (latest->ldAcqStatus() != VersionStatus::deleted) ERR;` を、aborted を next で読み飛ばす while と「null または deleted 以外なら ERR」に置き換える。最上段の `latest->ldAcqWts() >= MinRts` の break はそのまま。
- 修理 2 (`patches/fix-cicada-gc-records-scan-key.patch`、sha256 `9e397f397eda710ae90e2da123c0e1e4f18f1fa28e7d468326bbb795e6b02cda`、`scan()` の +5 / −3 行):
  key を `itr->body_.get_key()` (Tuple::init が作成時に最初の版の body を深く複写したもの、以後変わらない) から取り、空なら従来の `itr->latest_->body_.get_key()`。
- どちらも新しい `#if`・`#define`・`IZANAGI_` の語・診断出力を足していない (全 patch を走査する既存テストの対象外)。
- **受理集合:** 修理 1 は回収の判定だけで、どの tx が commit / abort するかを変えない (観測した設定 = INLINE_VERSION_OPT=0・SINGLE_EXEC=0・WRITE_LATEST_ONLY=0・REUSE_VERSION=1・group_commit=0)。修理 2 は key が空でない通常の行では同じ key で、空 key だった行だけ正しい key になる。
- **修理 1 の安全性の論証 (静的):** (i) 削除版より上に install された版は commit しない — 後発の tx は read set 再検査か (b) の検査 (自分の版の下を辿って deleted なら abort、transaction.cc:576-593) で abort する。(ii) 回収可と判定する時点 (最上段の wts < MinRts) で版鎖に実行中の tx の版は無い — thread ごとの wts は単調増加 (time_stamp.hh の localClock_ は減らない)、各 thread の公開 rts = その時点の MinWts − 1 < その thread の wts、MinRts は公開 rts の最小なので実行中の tx の wts より小さい (group_commit=0 の場合)。(iii) 読み飛ばす aborted 版と D1 はどこからも解放されない (aborted 版は gcq に積まれない、D1 の GC は D1 の next を切るだけ) ので、辿る版は生きている。tuple を他の thread がまだ指している場合の `delete rec` の危険は、最新版が deleted の既存経路と同じで、修理で増えない (未解決の既存の論点、§6)。
- **修理 2 の限界:** INLINE_VERSION_OPT=1 の insert 経路では `Tuple::body_` が空 key になりうる (inline 版の空 body を複写する既存の経路。その経路は insert の新版を tuple に繋がない別の既存欠陥の上にある、md_17 §2.3)。そこで最上段が削除版だと予備も空になり、空 key は残る (修理前と同じで悪化はしない)。空文字列を正当な key に使う workload では予備が最新版の key に落ちうるが、CCBench の TPC-C・YCSB・BoMB の key は固定長で空にならない。

## 3. 原因の診断 (D1)

使い捨ての診断 patch (Codex author、job dir `diag/diag-cicada-gc-records.patch`、sha256 `568ce542527ab063331edacd0cb469740b37edaa164acc83c9ab296577fe996b`、CC の判断を変えず stderr へ出すだけ) を F の TRACE=0 build に当て、F cell × 4・8 thread を各 5 回。同じ job に無 patch の対照を置いた。request 36143.nqsv、bnode023、Elapse 62 秒。要約 `verbatim/d1-result-summary.md`。

| build | 4 thread | 8 thread |
|---|---|---|
| 診断 patch | 5/5 が ERR | 5/5 が ERR |
| 無 patch (対照) | 5/5 が ERR | 4/5 が ERR (1 回は完走) |

ERR の直前の dump 10 件を、起動器が版の pointer で「install 済みで abort した版」の事象と「削除の commit」の事象に照合した結果、10 件すべてが `aborted-delete-over-deleted` (上の §1 の 1)。副次の観測: scan の node 版検査で abort した削除版が committed の版の上に aborted で残る事象 (`DELETE|node_set|committed`) が 1 走行 23〜276 件あり、これが修理 2 の空 key の出どころの 1 つになる (§4 V2)。

## 4. 確かめたこと (事前登録と結果)

事前登録は `verbatim/s4-ruling.md` の R3 と `verbatim/s4-ruling-addendum-1.md` の V3 表。起動器は md_17 の起動器を写して拡張した repo 外の `launch_gcfix_run.py` (Codex author、最終版 sha256 `056fca8c7274b166c85c2c39e4fa14e3613b48fe82044f0f629beac2b004cf40`)。build ごとに期待 (expect) を持たせ、外れたら起動器 rc=1。計測木は main `8fe87f852` の detached checkout 2 本。

| job | 内容 | 結果の要約 (原本の要約 file) |
|---|---|---|
| V1 (36317.nqsv、Elapse 143 秒) | 修理 1 だけの TRACE=0・ASan・変異 M2 | 修理版 20/20 完走、無修理 t4 10/10・t8 10/10 ERR、pin C + 修理 3/3 完走。M2 (1 段だけ読み飛ばす) は t4 10/10・t8 3/10 が ERR → **KILLED** (何段でも読み飛ばす必要)。ASan は既存欠陥 U で判定不能 (`verbatim/v1-result-summary.md`) |
| V2 (36318.nqsv、204 秒) | 修理 1 だけの trace | M・R2 は修理前後とも合格・identity 一致。F は完走したが空 key の R 行 (12 file で計 1,142 行) で判定器が parse error → 新事実 S = 修理 2 の発端。修理 2 を外した構成がこの形で落ちることは変異 M4 の記録を兼ねる (`verbatim/v2-result-summary.md`) |
| V3 (36402・36403.nqsv、126・157 秒) | 修理 2 初版 | F の trace 3/3 合格、壊した版は巡回 586 件 (`verbatim/v3-result-summary.md`) |
| **V4 (36425・36426.nqsv、129・171 秒)** | **最終 patch** | 下表 (`verbatim/v4-result-summary.md`) |

V4 (最終 patch = 修理 1 → 修理 2):
| 事前登録の項目 | 結果 | 判定 |
|---|---|---|
| 修理版 F × t4 × 10、F × t8 × 10 が全部完走 | 20/20 rc=0 | 満たす |
| 同じ job の無修理版は thread ごとに既知 ERR ≥ 1 | t4 5/5・t8 4/5 が gc_records の ERR | 満たす |
| pin C + 修理 2 本の F × t4 × 3 | 3/3 rc=0 | 満たす |
| 修理版 trace (F × t4 × 3): 巡回 0・integrity 数値 0・存在履歴違反 0・C = commit 数・READ_WTS_MISMATCH 0・W op D > 0・D の thread ≥ 2・読み飛ばし回収 > 0 | 全 run 満たす。C = 34,829 / 33,447 / 18,608、D = 3,020 / 3,570 / 890 (各 4 thread)、読み飛ばし回収 555 / 607 / 179 | 満たす |
| M・R2 (削除なし) の判定が修理前後で同じ | 修理版 4/4 合格 (V4)、無修理版 4/4 合格 (V2) | 満たす |
| M3: read 再検査の壊し + 修理で巡回 > 0 | non-serializable、巡回 386 | 満たす |
| identity: (F + 修理) 対 (F + 計装 + 修理) の TRACE=0 | 3 TU で compile command・命令列一致、nm・strings 一致 | 満たす |
| ASan: 修理 2 本 + U の回避 (使い捨て) の F × t4 × 3 で rc=0 かつ ASan 報告 0 | 3/3 とも実行中の AddressSanitizer 報告 0・gc_records の ERR 0 で完走 (commit 6,684〜9,140)、終了時に LeakSanitizer が解放しない領域を報告して rc=1 | **文言は満たさない** (rc≠0 は終了時の leak 報告)。実行中のメモリ誤用の報告 0 という実質は満たす。ASan build で修理 1 の分岐が何回発火したかは測っていない |

判定の上限は indeterminate (Cicada に X / P / I の証拠面が無い、md_3・md_17 と同じ) で、serializable の証明とは呼ばない。範囲読みの phantom・不在の読みは trace に表れない (md_17 §7)。

## 5. 上流 CI

- **format:** CCBench の branch tip `81fc4a84` の clean checkout (bundle から clone) で、CI の step (`git ls-files -- cc include common | grep -E '\.(cc|hh|cpp)$'` の全 file に `clang-format --dry-run --Werror`) を T-2854 の検査 script で回した。213 file、login の clang-format 14.0.0 で rc 0、CI image `:latest` の clang-format で rc 0 (job dir `format-ci-fix.log`)。
- **build:** 計算ノード (request 36483.nqsv、bnode031、48 core、Elapse 32 秒) で CI image `:ci` (SIF sha256 `cb8cd1c3…`、GCC 13.3.0・cmake 3.28.3・ccache 4.9.1) を apptainer (`--userns`) で動かし、bundle から clone した tip `81fc4a84` を CI と同じ `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DENABLE_SANITIZER=OFF` (+ ccache launcher) と `cmake --build build` で build した。configure rc=0 (2 秒)・build rc=0 (22 秒)。実行 file 38 本 (CMake の検出用 4 本を除く CCBench の 34 本、T-2854 の F と同数)。警告 13 件はすべて第三者の masstree 内で、CCBench 本体 (`cc/` `include/` `common/`) の警告・error は 0 件。依存は手元 cache から pin (masstree・mimalloc・googletest) を取り出して渡した (CI との差は T-2854 §3 と同じ)。build script は T-2854 の `run_ci_build.sh` を写し、親の検査を「F が祖先で F..tip が 1〜2 commit・merge なし」に直した版 (Codex author、job dir `stage7/run_ci_build.sh`、sha256 `535ae4d0…`)。証跡 job dir `ci-evidence/build-1/report.json`。
- GitHub Actions の緑ではない (push していない)。

## 6. 確かめていないこと・限界

- **既存欠陥 U (abort の use-after-free):** `abort()` (transaction.cc:747-751) が INSERT した tuple を delete した後、`writeSetClean()` (include/transaction.hh:345) が同じ要素の `rcdptr_->continuing_commit_` に 0 を書く。insert を含む tx が abort すれば起きる (ASan で M cell の stock 2/2、修理版 3/3 で検出)。Release では解放直後の同じ thread の 8 byte の書き込みで、実害は小さいと見込む (推測) が未定義動作。本 wave では直していない。ASan の確認は U を避ける使い捨ての回避 patch (job dir `stage7/asan-abort-uaf-workaround.patch`、CCBench にも patches/ にも入れていない) を重ねて取った。
- `delete rec` と、tuple をまだ指している他の thread (実行中の scan・read set、他 thread の gcq) の寿命は、既存の正常経路と同じ問題として残る。ASan の 3 走行では検出されなかったが、証明ではない。
- 観測した設定以外 (INLINE_VERSION_OPT=1、SINGLE_EXEC=1、WRITE_LATEST_ONLY=1、REUSE_VERSION=0、group_commit>0)、warehouse 数 > 1、F 以外の削除を含む cell、YCSB・BoMB での修理の効果は測っていない。
- 修理は性能を変えうる (完走するようになった以外に、回収の遅れ・空 key での read-own-reads の誤一致の解消)。性能値は取っていない (規律 1: 取るなら trace を外した build で同時刻の対照を置く別 wave)。
- D297 (TRACE=0 命令列の同一性の pin 間判定) は取っていない。修理は transaction.cc の意図した変更で、pin を進める wave が新しい tip で判定を取り直す。
- GitHub Actions の結果ではない (push していない)。
- delete の意味を壊した正例は作っていない (単一 site の壊しは他の検査に止められ巡回を作らない、md_17 §4 と段 2 plan の読み。代わりに read 再検査の壊しで削除を含む履歴での検出を確かめた)。

## 7. push と pin の前進 (人間の手番)

1. CCBench の local branch `izanagi-cicada-gc-records-fix` (tip `81fc4a84cc855a3f98374e40e2ba7e3330c2614d`、親鎖 F `25898d00` → `dd6ea5144fc06bc63cf741b1bb212376bbe8b6e2` → tip) を別名の branch として push する (同名への force push はしない、D16)。主 checkout の submodule git dir へは本 wave の land 後に非 force で fetch する (bundle = job dir `fix.bundle`)。F の branch `izanagi-tpcc-v3-silo-mocc-fmt` が先に上がっていれば、差分は修理 2 commit だけになる。
2. GitHub の CI (build・format) が緑であることを確かめる。
3. 並走 wave md_19 (同じ F の上の別 branch、transaction.hh の inlineVersionPromotion と transaction.cc の WORKER1_INSERT_DELAY_RPHASE) と 1 本にまとめるかは人間の判断。本 wave の変更 (transaction.cc の scan 432 付近と gc_records 849 付近) と行は重ならない (静的)。
4. pin の前進 (gitlink・`CCBENCH_FULL_SHA`・`CURRENT_PIN`・patch の厳密適用・D297) は push と CI 緑の後の別 wave。前進したら `patches/fix-cicada-gc-records*.patch` は不要になる (新 pin に含まれる)。

## 8. 計算と工程

計算ノード: D1 62 秒、V1 143、V2 204、V3a 126、V3b 157、V4a 129、V4b 171、CI build 32 秒。合計 1,024 秒 ≈ 0.28 node 時間 (受入全走を除く) (2 node 時間の線の下、ユーザー確認の対象外)。性能値は取っていない。
Codex (gpt-6-sol、reasoning medium): 段 1 の診断 author 1、段 2 plan 1、段 3 相談 2、段 5 author 1、段 6 レビュー 2・fix 2・焦点再レビュー 2。
