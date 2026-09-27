# [T-2854] (1) D297 検査器に header 差分の受理規則 v2 を実装し、改訂後の検査器で C 68106660 → C2' 40a7f4ac を GCC 11.4 / 12.3 とも pass と判定した。負例対照 (tpcc.hh の `#line 56` 削除) は拒否。pin は進めていない

authority: none
default_effect: no-state-change

- 日付: 2026-09-27
- wave: `dev-wave-t2854-d297-header-v2` (branch `worktree-dev-wave-t2854-d297-header-v2`)。着手時 local main `339d7c18831176d431e1f634621aa06d940ddd70` (開始 gate rc=0、`verbatim/startup-gate.log`)。記録の前に local main `19d3f2bae` を取り込んだ (merge `e46a839f`、検査器・test・buildcache・genome・model・fetch_third_party は main 側で無変更)
- 依頼: [T-2854] の残り (1)。規則 v2 の設計 = D2255、承認と実装の委任 = D2260 項 1、設計審査 = `output/insights/2026-09-26/t2854-d297-header-review/README.md`、候補 = `output/insights/2026-09-26/t2854-unit11-combined/README.md`
- 既裁定: D297、D780 (項 1 の文言を継承、項 2 を維持)、D2150 (iii)、D2207、D2212 項 4、D2244 項 4、D2255、D2260 項 1・4、D2272 項 6
- job dir (使い捨て script・生 log・Codex receipt・判定 job の全出力): `/work/1/SFC/tanab/tmp/t2854-d297-header-v2-20260927/` (= `/work/SFC/tanab/tmp/...`)

## 0. 結論

1. **実装:** `tools/check_trace0_preprocess_identity.py` に header 差分の新分岐を足した (最終実装 commit `82e9e780`)。header 用の 4 引数 (`--header-cc` `--third-party-cache` `--dependency-prefix` `--scratch-root`) を全部与えたときだけ、header の M・mode 不変の差分を規則 v2 で検査する。与えなければ従来と同じ文言で拒否し、検査順序と返り値も段 5 前と同一 (既存 caller `tools/pegasus/mocc_trace_pilot.sh` は不変)。新 test `orchestrator/tests/test_check_trace0_header_rule.py` (14 関数、実 cmake・実 g++ の小さな合成 CMake project)。
2. **判定 (計算ノード 1 job、request 31903.nqsv、Elapse 1,944 秒):** 改訂後の検査器で C → C2' は **GCC 11.4 (980 秒) と GCC 12.3 (988 秒) の両方で pass (rc=0)**。選定 configure 17 (stock + silo 8 + mocc 8)、tictoc・cicada は各 24 genome を依存列挙で調べて consumer なし。consumer 21 entry / 12 file、比較の予定 357 = 実行 357 (集約後の実比較 118)、完全展開と include 活性は全件一致。.cc 2 本 (mocc・silo の transaction.cc) も既存の 16 文脈で match。gitlink `third_party/shirakami` (fb14e659) は旧新一致として記録。
3. **負例対照:** C2' に `include/tpcc.hh` の `#line 56` を消す commit を足した入力は GCC 11.4 で rc=1、理由 = `header expanded 不一致: configure=stock entry=('<SOURCE>/cc/cicada/tpcc_cicada.cc', 'tpcc_cicada.exe')` (TPC-C consumer の完全展開の不一致、951 秒)。判定 script の欠陥 (§5.4) で job 内の末尾検査が走らなかったので、親が保存物に同じ 3 検査 (rc=1、「expanded 不一致」、TPC-C consumer の特定) を当てて全部成立を確認した。
4. **pin は C のまま。** gitlink・`CCBENCH_FULL_SHA`・`CURRENT_PIN` は変えていない。branch `izanagi-tpcc-v3-silo-mocc` の push もしていない。C2' の pin 前進は D2255 項 4 の問い 2 としてユーザー裁定へ出す (§7 に波及の実測)。この pass は規則 v2 の保証 (選定 configure 集合の compile database に載る変更 header consumer entry における、TRACE=0 完全展開と include 活性の同一性) であり、trace 完全除去の証明ではない (D780 項 1)。TPC-C の certified も名乗らない。
5. **変異:** 事前登録 V1・V3〜V11 と、fix 所見の回帰を守る追加 V13・V14 の 12 件すべて KILLED (期待 node と完全一致)。V2・V12 は単一理由の偽緑に届かない構造なので登録から外した (§6)。
6. **実費:** 計算 job の Elapse 合計 2,137 秒 (生死確認 170、焦点走 13、判定 1 回目 10、判定 2 回目 1,944) に変異 2 走 742.7 秒 (harness の所要、queue 待ち込みの上限値) で **約 0.80 node 時間以下**。受入 1 回目 (赤 1、§5.3) の 3 shard 計 848 秒を足して約 1.04 node 時間 (受入 2 回目は本 insight の後に走るので含まない)。2 node 時間の確認線の下。Codex 子 13 本 (全子 gpt-6-sol / medium、段 7 の記録レビュー 1 本を含む) で model call 199、wall 3,638.8 秒。

## 1. 完了条件と状態

| 完了条件 (依頼) | 状態 |
|---|---|
| 規則 v2 を D297 検査器へ実装 (Codex author) | **済** — 段 5 実装子 1 本 + 段 6 fix 3 巡 (fix 1 は親の依頼文誤りで即停止、§5.3) |
| 最初に計算ノードで生死確認 | **済** — §4.1 |
| 検査込みの job 合計が 2 node 時間以上なら見積りを示してユーザー確認 | 見積り 1.2〜1.75 node 時間 (段 4 裁定 §5) で線の下。実費 ≈ 0.80 以下 (受入前) |
| 改訂後の検査器で C → C2' を GCC 2 版で判定 | **済** — 両方 pass (§3) |
| 結果・実費・pin 波及を記録 | **済** — §3・§0 の 6・§7 |
| pin 前進・gitlink 更新・push をしない | 守った |
| D780 項 2 の維持、規律 1・2 を緩めない | 守った (保証名と文言は D2255 項 2 と D780 項 1 のまま。header 無効時の拒否・.cc の比較は不変) |
| 仮想リスク向けの gate・検査・台帳・一般化を足さない | 守った (§5.2 の F9・F10 は不採用) |

## 2. 実装 (検査器の新分岐)

規則 v2 (D2255 項 1) の実装。段 4 裁定 `verbatim/s4-ruling.md` の S1〜S12 と、段 6 裁定 `verbatim/s6-ruling.md` の F1〜F8・F11 に従う。

- **起動 (S1):** 4 引数が全部あるときだけ header 分岐。1 つも無ければ段 5 前の検査器と同じ順序・文言・返り値。一部だけは拒否。
- **source (S8、F11):** scratch の bare clone に `info/attributes` (`* -export-ignore` `* -export-subst`) を置いて旧新を `git archive` し、tree の regular file 集合と全 blob の sha1 を照合。gitlink は展開・照合から除外し、旧新で (path, commit OID) の集合が一致することを確かめて report に列挙する。symlink と他の非 regular は拒否。
- **configure (S3):** production の `orchestrator.campaign.buildcache._v2_commands` を呼び、返る configure argv に `-DCMAKE_EXPORT_COMPILE_COMMANDS=ON` と `-DCCBENCH_CCACHE=OFF` (production argv との差分として report に記録) を足す。stock は genome define なし。third-party は `tools/pegasus/fetch_third_party.py hydrate`、masstree は configure ごとに複製して `masstree_build` で `config.h` を作る (config.h は masstree の SOURCE_DIR 側に生成されるため)。test は configure argv の供給と genome 空間だけを差し替え、依存列挙以降は実物を通す。
- **選定 (S4、F3):** production target は genome 空間を持つ各 protocol について `_v2_commands` の build argv の `--target` から取る (`ycsb_<protocol>.exe` 以外の形は拒否)。stock で production target の entry が変更 header を読む protocol はその空間全体を選ぶ。読まない protocol は全 genome を「production target の entry だけ」の依存列挙で調べ、見つけた時点で選ぶ。
- **依存列挙と TRACE (S5):** 選定 configure ごとに全 entry を旧新 × TRACE 0/1 で `-E -dM -MD -MF` の 1 回実行により依存と macro 状態を同時に取り (`-MG` なし、失敗は拒否)、`#define TRACE <要求値>` が無い entry は拒否。`-DTRACE=` token は 1 個なら置換、無ければ追加、2 個以上か 0 以外なら拒否。`@file`・`-Wp,`・`-MG` を含む argv は拒否。変更 header ごとに consumer 0 件なら拒否。
- **database と比較 (S6・S7、F1):** 照合済み root を論理名へ置換した (file, target, argv) の多重集合が旧新で一致しなければ拒否。比較の予定 (configure, consumer entry) を実行前に固定し、同じ比較の集約鍵を (entry、正規化 argv、旧新それぞれの TRACE=0 依存閉包の全 file の正規化 path と内容 sha256) とする。実行済み集合は比較結果 (集約鍵に属する configure) から作って予定と厳密一致を求める。`-E -P -dD` と `-E` の入退場 file 列を比べ、`__DATE__` 等が完全展開に現れたら拒否 (probe argv にだけ `-Wno-builtin-macro-redefined`、F2)。
- **返り値 (fix 3):** `check()` は 1 つの辞書 literal を返す形を保ち、header があるときだけ `**` で `header_rule` を足す (既存 consumer test `test_mocc_trace_binding_f7_synthetic_fixture_keys_match_checker_contract` の AST 固定)。

## 3. 判定 (C → C2'、計算ノード)

- job script = job dir `judge/run_judge.sh` (Codex author、gitignore 下に書かせて親が退避、sha256 `66af63ab…`)。投入 = job dir `run-judge.sh` (`dispatch_compute.py --task generic --walltime 01:30:00`)。bnode・cache・prefix・`/usr/bin/{gcc,g++}-{11,12}`・scratch 20 GiB・bundle head・裁定済み OID を事前確認してから、GCC 11.4 と 12.3 の 2 起動を並行し、正例が両方 pass のときだけ負例対照へ進む。
- **1 回目 (31898.nqsv、commit `de51469e`、Elapse 10 秒):** 両方 rc=1、`source tree に regular file 以外: b'third_party/shirakami'` (`verbatim/evidence/judge1-gcc11.stderr`)。段 4 裁定 S8 の「gitlink は拒否 (生死確認で問題なし)」が親の事実誤認だった (§5.3)。
- **2 回目 (31903.nqsv、commit `82e9e780`、20:59:38〜21:31:58 JST、Elapse 1,944 秒):** report = `verbatim/evidence/judge2-gcc11.report.json`・`judge2-gcc12.report.json`。

| 項目 | GCC 11.4 | GCC 12.3 |
|---|---|---|
| rc / result | 0 / pass | 0 / pass |
| 所要 | 980 秒 | 988 秒 |
| compiler (C++ / C) | `x86_64-linux-gnu-g++-11` / `gcc-11` 11.4.0 | `x86_64-linux-gnu-g++-12` / `gcc-12` 12.3.0 |
| 選定 configure | 17 (stock、silo 0〜7、mocc 0〜7) | 同左 |
| 未選定で調べた genome | tictoc 24、cicada 24 | 同左 |
| production target | ycsb_{silo,mocc,tictoc,cicada}.exe | 同左 |
| consumer | 21 entry / 12 file | 同左 |
| 予定 / 実行 / 集約後の実比較 | 357 / 357 / 118 | 同左 |
| .cc の単体比較 | mocc・silo の transaction.cc とも match | 同左 |
| gitlink | third_party/shirakami fb14e659 (旧新一致) | 同左 |

- 負例対照 (同じ job、C2' に `#line 56` 削除 commit `ab6143cd…` を足した入力、GCC 11.4): rc=1、951 秒、`verbatim/evidence/judge2-negative.stderr`。

## 4. 生死確認と費用

### 4.1 生死確認 (段 1、DW-G01)

使い捨て driver (Codex author、job dir `driver/liveness.py`、sha256 `63c7ecef…`) を計算ノード 1 走 (31808.nqsv、bnode009、48 core、Elapse 170 秒)。stock-gcc11・stock-gcc12・silo genome 1 点の 3 構成 × 旧新で configure (0.7〜0.8 秒)・`masstree_build` (10.6 秒)・`-MG` なし依存列挙 135 entry × 2 (11 秒、失敗 0)・TRACE 実効値 (21/21)・旧新 database 一致・前処理 42/42 一致がすべて成立 (`verbatim/s1-live-summary.md`)。この driver は tree 照合をしておらず、gitlink の有無は観測していない (§5.3)。

### 4.2 実費

| 計算 | request | Elapse |
|---|---|---|
| 生死確認 | 31808.nqsv | 170 秒 |
| 焦点走 1 回目 (commit 9ceb5519、4 file) | 31845.nqsv | 13 秒 (1 failed / 325 passed) |
| 判定 1 回目 | 31898.nqsv | 10 秒 |
| 判定 2 回目 | 31903.nqsv | 1,944 秒 |
| 変異 probe・final (各 13 走) | harness の所要 | 368.9 秒 + 373.8 秒 (queue 待ち込み) |

合計 ≈ 2,880 秒 ≈ 0.80 node 時間 (受入を除く)。判定の単価は生死確認からの外挿 (段 4 裁定 §5: 2 起動並行で wall 25〜40 分) と整合した (実測 wall 32 分)。

## 5. 経過

### 5.1 段 1〜4

- 段 1 brief (`verbatim/s1-brief.md`、provisional P1〜P8) と生死確認。段 2 plan 1 本 (`verbatim/s2-plan.md`)、段 3 相談 2 本 (A = 正しさ境界 `verbatim/s3-consult-A.md`、B = 実効性と過剰 `verbatim/s3-consult-B.md`)。受理集合を変え正しさ防壁に触る wave なので全段を回した (DW-C00)。
- 段 4 裁定 (`verbatim/s4-ruling.md`): 相談 A の must-fix 4 件 (stock だけで genome を選ぶと genome でだけ読む production target を落とす、同じ argv でも生成物が違えば集約は偽緑、TRACE token の無い entry の扱い、production target の出所) と相談 B の must-fix 2 件 (合成 fixture を production configure に縛ると新分岐に届かない、R4 の集約が plan から落ちた) を採用し plan v2 (S1〜S12) に。plan の「git worktree で展開」は、与えられた repo の管理領域を変えないため bare clone + archive + 全 blob 照合に置き換えた。

### 5.2 段 5・6

- 段 5 実装子 1 本 (1,123.9 秒、61 call)。統合 `9ceb5519`。
- 段 6 レビュー A (正しさ境界) と B (過剰・削除) はともに NO-GO。親の事前所見 5 件 (`verbatim/parent-findings-s6.md`) をすべて real と判定: P-1 予定と実行の照合が恒真、P-2 discovery が全 entry を列挙、P-3 既存の検査順序の変更、P-4 実 CCBench の `-Werror` で builtin probe が失敗 (親が login で `-Werror=builtin-macro-redefined` を実測)、P-5 V2 は構造的に偽緑へ届かない。段 6 裁定 (`verbatim/s6-ruling.md`) で F1〜F8 を採用、F9 (root 正規化の path 境界) と F10 (test 用供給で本体経路が分岐) を不採用。
- 焦点走 1 回目 (計算ノード、commit `9ceb5519`) で既存 consumer test 1 件が赤 (`check()` の辞書 literal の return を AST で固定)。実装子への「制約 meta-test を洗い出せ」が守られていなかった。既存 test を変えず実装側を戻した (fix 3、`de51469e`)。
- 焦点再レビュー F1 (`verbatim/s6-review-F1.md`): F1〜F8 と consumer test の赤を closed、F9 に反証ありで NO-GO。親は F9 を refuted のまま維持 (段 6 裁定 追補 2): 反例の文字列は旧新それぞれの root から同じ構成で作られた置き場由来の差で、同じ置き場で build すれば同じ bytes になる。root は検査器が新しい mkdtemp 下に作る固定幅の一意名で、root を含む bytes は root から構成されたもの以外に現れえないので、別の実体が同じ token に潰れない。DW-O16 の 3 巡上限に従い fix を重ねなかった。
- 判定 1 回目の gitlink 拒否を受けて fix 4 (実機 blocker、巡数上限の別枠) で F11 を実装 (`82e9e780`)。

### 5.3 親と子の失敗・near miss

- **親の事実誤認 (S8):** 段 4 裁定に「gitlink は拒否 (CCBench では生死確認で問題なし)」と書いたが、生死確認 driver は tree 照合をしておらず gitlink を観測していなかった (単位 11 の probe は gitlink を照合から除外して記録していた)。判定 1 回目で `third_party/shirakami` により拒否された。費用は 10 秒の job 1 本と fix 1 巡。
- **合成 fixture の代表性:** 段 5 の fixture は実 CCBench の consumer argv にある `-Werror` を持たず、`-U__DATE__` の probe が実構成で必ず失敗することを test が捉えなかった。親が login で実測して段 6 で直し、正例 fixture に `-Werror` と TRACE token の無い target を加えた (F7)。
- **consumer test の AST 固定の見落とし:** 実装子は制約 meta-test の洗い出しを指示されていたが、`test_mocc_trace_job_contract.py` の AST 固定に当たる返り値の組み立て方の変更を持ち込んだ。焦点走で検出。
- **fix 1 の依頼文:** 親が「親の事前所見 parent-findings-s6.md (同じ dir)」と書き、子は `out/` 配下と読んで存在しないため規定どおり即停止した (16 秒)。絶対 path に直して再投入。
- **新 test file の自走入口・allowlist の欠落 (F42 再発):** 最終受入 1 回目 (tested main `19d3f2bae`、tip `1eaf4331`、27,954 collected) が `test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted` の 1 件だけで赤 (27,879 passed / 74 skipped)。新 test は `tmp_path` fixture に依存するので `orchestrator/tests/README.md` の pytest 専用 allowlist に 1 行足した。親は DW-O26 (新規 test file を足す走は file 集合列挙のメタテストも焦点走に含める) を読みながら焦点走に入れていなかった。受入 1 回目の Elapse は 3 shard 計 848 秒。
- **判定 script の errexit:** `run_one` が関数内で `set -e` を戻してから `return 1` するため、`set +e` の中で呼んだ負例の起動が rc=1 を返した時点で script 全体が rc=1 で終わり、末尾の 3 検査が job 内で走らなかった。負例の判定自体は保存物で成立を確認した (§0 の 3)。script は job dir だけにあり repo には入っていない。

### 5.4 段 7 記録レビュー

記録 commit `9966b6bb` を独立 read-only レビュー 1 本 (`verbatim/s7-review-R.md`) が一次資料と照合した。判定・負例・実費・変異・[T-2854] の更新本文・名乗りの境界はすべて一致。指摘は failures の再発分類 2 件で、F42 (must-fix) は、F42 自身が 2026-07-27 (26) で型を「変更が meta-test (横断検査) の契約を落とす」に広げ、2026-08-28・2026-09-10 に production の変更が既存の検査 test を破った再発を積んでいるので維持した (refuted)。F819 (should) は型 (親の投げ文の path が子の解決先と食い違う) が同じで結末 (fail-closed) が違うことを本文に明記して維持した。

### 5.5 main の前進

wave 中に local main が `339d7c188` → `19d3f2bae` へ進んだ (論文ストーリー版、[T-2853]、[T-2869]、[T-2865]。peer 通知を契機に local ref を読み直して確認)。本 wave の編集面と重ならない。

## 6. 変異 (DW-M01〜M08)

- 対象 commit `82e9e780` に固定した detached worktree `.codex/worktrees/t2854-hv2-mut` で `tools/mutation_harness.py --runner-mode dispatch` を走らせた。runner は `tools/run_tests.py --force-dispatch -q -rf orchestrator/tests/test_check_trace0_header_rule.py` に限った (drift mask の層を含まない)。anchor は全 12 件が対象 file でちょうど 1 回現れることを親が照合した。
- probe (全件 SURVIVED 期待、21:02〜21:11 JST、`verbatim/spec-probe.json`): baseline PASSED、12 件とも狙いの test が赤。帰属を確認: 負例型 (V1・V5・V6・V7・V8・V10・V11) は狙いの test が「DID NOT RAISE」(拒否すべき入力が pass)、正例型 (V3・V4・V9・V13・V14) は正例 test が拒否に変わった。
- final (観測 node の完全集合を KILLED 期待、21:12〜21:22 JST、`verbatim/spec-final.json`): baseline PASSED、**12 件すべて KILLED (期待 node と完全一致)**、変異木は走行後も clean。結果の原本 = job dir `mutation/final-1-results.json` (sha256 `d6d87873…`)。

| ID | 変異 (検査器) | 狙いの test の赤 |
|---|---|---|
| V1 | consumer を「TU が変更 header を直接 include」に劣化 | 間接 consumer の値変更が pass (DID NOT RAISE) |
| V3 | 生成 target の build を飛ばす | 正例が依存列挙の失敗で拒否 |
| V4 | consumer 判定を TRACE=0 の依存だけにする | 正例の consumer 集合が不一致 |
| V5 | 未選定 protocol の genome 調査を外す | genome でだけ読む production target の差が pass |
| V6 | 比較を選定 protocol の production target の entry だけに絞る | 他 protocol consumer の差が pass |
| V7 | 集約鍵から依存閉包の内容 digest を外す | 生成 header の値だけ違う configure の差が pass |
| V8 | TRACE 実効値の確認を外す | 強制 include で TRACE=1 になった entry の差が pass |
| V9 | 予定の最後の 1 件を実行しない | 正例が予定と実行の不一致で拒否 |
| V10 | 完全展開の比較を外す | TRACE=0 側の値変更が pass |
| V11 | include 活性の比較を外す | 空 header の include 移動が pass |
| V13 (追加) | builtin probe の `-Wno-builtin-macro-redefined` を外す | `-Werror` の正例が拒否 |
| V14 (追加) | gitlink の除外を外す | gitlink を持つ正例が拒否 |

- **登録から外したもの:** V2 (依存列挙に `-MG` を足し生成 build を飛ばす 2 層変異) は、実装が `-E -dM -MD` の 1 回実行で依存を取るため未生成 header で必ず失敗し偽緑に届かない (実装子と親が確認)。V12 (header 分岐の有効化を「4 引数のどれか」に緩める) は、直後の「4 引数はすべて必要」の拒否と `None` 引数での失敗が先に落とすため単一理由にならない (DW-M01 の再照準)。
- V13・V14 は段 6 の fix 所見 (F2・F11) の回帰を守るために fix 後に足したもので、段 4 の事前登録外。

## 7. pin を C2' へ進めた場合の波及 (実測した範囲)

pin 前進はユーザー裁定の問い 2 (D2255 項 4) で、本 wave は行っていない。先例 D2150 / D2184 の同時更新に当たる箇所を、現 pin C の完全 OID と短縮形の repo 検索で列挙した (歴史記録の insight・archive・decisions・worklog・failures を除く、local main `19d3f2bae` 取り込み後の作業木)。

- **code:** `orchestrator/campaign/pin.py` (`CURRENT_PIN = "6810666"`、4 行)、`orchestrator/campaign/s8b_approved.py` (`CCBENCH_FULL_SHA`、4 行)、`orchestrator/campaign/p3_s4_loop.py` (2 行)、`orchestrator/campaign/buildcache.py` (docstring の実測記録 1 行)、`tools/pegasus/probes/t2187_adaptive_const_probe.py` (1 行)。
- **test:** 14 file (`test_p3_s4_loop_job_contract.py` 6 行、`test_s8a_trigger_sweep.py` 2 行、他 12 file 各 1 行)。
- **docs:** `patches/README.md` (3 行)、`docs/paper-story/2026-09-2{2,3,6,7}.md` (版の記録。書き換えない)。
- **凍結・登録済みの記録:** `output/env/pegasus/calibration/` の較正 record・staging・`s3_mocc_xp_pin_candidate.json` が C を束縛する。D2184 のとおり旧証拠の bytes は保持し、新 pin の系列は新しい較正を要する。
- **patch:** `patches/` の 66 本中 54 本が C2' の変える 4 file (cc/silo/transaction.cc・cc/mocc/transaction.cc・include/trace.hh・include/tpcc.hh) のどれかに当たる。C2' の上で当たるかは**未測定** (C2' の変更は writePhase の trace 出力と `#if TRACE` 領域だが、hunk の位置ずれは driver と同じ厳密適用で確かめる必要がある)。pin 前進の wave で測る。
- D2260 項 4 のとおり、この機会に si の trace v2 (`patches/instr-si-trace-v2.patch`、[T-2847]) の枝への移送と pin 前進も併せて諮る。

## 8. 主張しないこと

- trace のコンパイル時完全除去 (D780 項 1。本検査は D297 の保証の証明であり、完全除去の必要条件の一つ)。
- 選定外の文脈 (tictoc・cicada の genome 構成での比較、Debug、opt-in target、将来の production option、tpcc target が production に入った後の選定)、compile database に載らない TU、GCC 以外の compiler、admission build・link object・trace symbol / data・build receipt との結合 (D2255 項 3、D780 項 2)。
- TPC-C の certified、C2' の pin 前進の承認、patch の C2' への適用可否。
- 生死確認の consumer 21・database 一致の一般化 (選定 configure の実測に限る)。
- 受入全走の結果 (本 insight の記録 commit の後に走る。結果は land の受領証と worklog が持つ)。

## 9. 再現資料

- `verbatim/`: brief・生死確認の要約と driver の報告・plan・相談 2・段 4 / 段 6 裁定・親の事前所見・実装子と fix 子の報告・レビュー 3 本・変異 spec 2 本・開始 gate。
- `verbatim/evidence/`: 判定 2 回目の report 2 本 (GCC 11.4 / 12.3)、負例対照と判定 1 回目の stderr、job dir の実行物と結果の sha256 (`job-dir-sha256.txt`)。
- job dir: 生死確認 driver と結果 JSON、判定 job script と投入 script、変異の結果 JSON、Codex receipt、各段の prompt・log。
- 候補 branch `izanagi-tpcc-v3-silo-mocc` の bundle = `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/C.bundle` (sha256 `99882fa7…`)。
