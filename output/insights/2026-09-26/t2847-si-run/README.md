# si の trace を v2 にして現行 verifier に通し、si の 3 行 (V36・V29・V28) を pin C で実走した ([T-2847] 残り (4)、2026-09-26)

authority: none / default_effect: no-state-change (可変状態の正本は worklog 末尾と現行 phase doc)。
wave `dev-wave-t2847-si-v2` (branch `worktree-dev-wave-t2847-si-v2`)、起点 local main `6d198ca8a` (開始 gate fresh rc 0、2026-09-26 18:5x JST)、CCBench submodule = pin C `68106660` (動かしていない)。
job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-si-v2/` (brief・Codex の prompt / 出力・起動器・計測の原本 JSON と stdout / stderr・変異 harness の記録)。
段 1〜6 の全文は `verbatim/` (依頼、段 1 brief と生死確認の要約、段 2 plan、段 3 の親の暫定見解と相談 2 本、段 4 裁定、段 5 共通契約と author・fix の報告、段 6 review 2 本と裁定)。

期待の出所は `output/insights/2026-09-22/t2847-verifier-detection-design/README.md` (以下「設計書」) の §4.5・§5.3。V 番号は設計書のもの。事前登録 (cell・期待・分類の規則・job 分割) は `verbatim/s4-ruling.md` の R3・R4。先例は mocc の実走 (`output/insights/2026-09-26/t2847-mocc-run/README.md`、D2246) と silo の実走 (D2239)。

## 1. 依頼と結論

依頼 (ユーザー直接起動の `/dev-wave [T-2847]`、逐語は `verbatim/request.md`): si の trace emitter を v2 (C 行に読み書きの件数、E 行) にし、si の変異 V28・V29・V36 を実走して検出期待表の si 行を埋める。v2 化は `cc/si/transaction.cc` の中だけで行い、共有 header を変えない。最初に、pin を動かさず patch として当てて build・verify できるかを確かめ、できなければ止める。si は X/P の証拠面が無いので上限は「巡回の検出」で、certified とは呼ばない。

結論:

1. **pin を動かさず patch として当てて build・verify できた。** `patches/instr-si-trace-v2.patch` (`#if TRACE` の内側だけを変える無条件の計装) を pin C に当てた si の trace は、現行 parser に受理され framing violation 0 で verdict が出た (§2)。1 回目の生死確認は parse error だった — si の `thid_` は `uint8_t` で、C 行の thread 番号が数字でなく文字 (thread 0 なら NUL) として出た。`std::size_t` へ変換して直した。
2. **3 行とも事前登録どおりの分類になった** (§3):
   - **V36 (無改変の si、write skew)**: 4 thread の K 条件で non-serializable、巡回 2,236 → 「無改変 si の巡回検出」。2026-06-18 の「無改変 si で 3,576 巡回」(当時の v1 trace と当時の verifier) を、現行の verifier で取り直したことになる (件数は run が違うので比べない)。
   - **V29 (first-updater-wins の abort を外す)**: 1 取引 1 key の RMW (S1) で、元コードなら abort した上書きが 17,732 回起き、その取引がすべて commit したが、巡回 0・integrity 0 の indeterminate → 「盲点」。同じ key を読んで書く取引の R 行は update で read set から消えるので (R 行 0 行)、lost update は ww の辺しか残らない。
   - **V28 (未確定の版を読む)**: 1 操作の読みと blind write が混ざる条件 (S2) で、orphan read 45 の indeterminate → 「期待した層で検出」。未確定の版を選んだ読みは 2,931 回で、その取引はすべて commit したが、orphan として trace に現れたのは 45 件だった。
   - 同じ job の対照 (無改変 si + v2 patch の同 cell) は S1・S2 とも巡回 0・integrity 0 (「対照正常」)。停止・異常終了・誤検出・帰属不能は 0。
3. **si は certified にならない。** 証拠面 (X・P・I) が evidence-absent なので、巡回が無い履歴はすべて indeterminate で、serializable には一度もならない。「盲点」も「certified として通った」ではなく「巡回として現れなかった」の意味である。
4. 計算ノードの使用 (job Elapse): 生死確認 2 job 100 秒、本走 2 job 146 秒、焦点走 146 秒、変異 matrix は §6。

## 2. 何をどう走らせたか

### 2.1 patch (3 本、どれも touch set = `cc/si/transaction.cc`)

- `instr-si-trace-v2.patch` (裸マクロなし): C 行を `C <txid> <thid> 1 <cstamp> <read_count> <write_count>` にし、R/W の後に `E <txid>` を出す。件数は R/W 行と同じコンテナ (`read_set_`・`write_set_`) の `size()` で、独立 witness ではない。`#if TRACE` の外は pin C とバイト一致 (Codex author が枝除去で確認)。`trace.hh` の v1 helper `emit_commit` は残る (silo の v2 化と同じ形、`cc/silo/transaction.cc` の v2 frame の注記)。
- `broken-si-first-updater-wins.patch` (V29、`IZANAGI_BREAK_SI_FIRST_UPDATER_WINS`、site 7): `install_version()` の「snapshot の後に commit された版を見たら abort」だけを外す。inflight の版の分岐と CAS の再試行は残す。
- `broken-si-read-uncommitted-version.patch` (V28、`IZANAGI_BREAK_SI_READ_UNCOMMITTED_VERSION`、site 5): `read_internal()` の版選択で status (committed / deleted 以外を飛ばす) の除外だけを外し、snapshot 条件 `txid_ < cstamp_` は残す。未完成の値や回収後に再利用された版を読みうる (段 4 で承知のうえ実走、異常終了も結果として記録する規則)。
- 壊し 2 本は pin C → v2 patch → 壊し patch の順に厳密適用する。裸マクロ 1 個の `#if` 枝に閉じ、macro 未定義なら v2 適用後の file と枝の外でバイト一致。条件 gate の許可ドメインへ mocc と同形で登録した (si の owner `cc/si/transaction.cc`、target `ycsb_si.exe`)。判定基準・供給経路は変えていない。
- 発火診断 (壊し 2 本だけ): process 終了時に stderr へ `T2847_FIRED slug=<slug> reached=<n> changed=<n> committed=<n>`。V29 は reached = 元コードなら abort した条件が真になった回数、changed = その条件を越えて版を公開した回数、committed = changed を含む取引の commit 数。V28 は reached = 元コードなら飛ばした版 (status が未確定で snapshot 条件を満たす) に出会った回数、changed = その版を選んだ回数、committed = それを含む取引の commit 数。**V28 は出会えば必ず選ぶ作りなので reached と changed は構造上つねに等しい** (段 6 レビュー RA-01)。status と cstamp を別々に読むので、並行 commit の境目では「元コードなら必ず飛ばした」とまでは言えず、版選択の時点の観測値である (RA-02)。診断は verifier の判定に使っていない。

### 2.2 起動器と経路

repo 外の起動器 `launch_si_run.py` (Codex author、job dir。本走版 sha256 `5a24d38962ab3151bbe3b9f234220af517850b527548cc30dca1f60dbe776619`、生死確認版は `launch_si_run.L0.py` sha256 `2eb71e7284419feb1eba6aecde1a7d21e30878946fd0375d586f007e12fb9700`)。si の driver は repo に無く、既存 driver は protocol・target を mocc / silo に固定しているので、mocc の起動器と同じく driver の部品を import した局所版で組んだ:

- policy・toolchain・依存物は `s3_mocc_lock_coverage._load_policy` / `_resolve_toolchain` / `_prepare_dependencies` のまま (mocc の起動器と同じ)。build ごとに `patchharness.checkout(C)`・`assert_pinned_clean`、patch は touch set 検査つきの厳密適用。
- build は mocc の `_build_variant` と同じ configure (TRACE=1) で target を `ycsb_si.exe` にした局所版。macro 付き build は mocc の `_require_condition_gate` と同じ手順 (capture → request → 供給と意味 → admission) を通してから `-DCMAKE_CXX_FLAGS=-D<macro>=1` を足す (V29・V28 とも admission 成功)。
- run は mocc の `_run_trace` と同じ argv 形・cwd・`IZANAGI_TRACE_DIR`・120 秒 timeout・rc 規則の局所版で、stdout / stderr を全文保存。完走した run だけ `python -m verifier --protocol si` (証人なし) に掛けた。
- 投入は `tools/pegasus/dispatch_compute.py --task generic`、job ごとに専用の計測用 checkout (detached worktree、submodule 初期化、lock)。toolchain は 4 job とも policy の compiler (g++ 11.4.0) と一致。

### 2.3 cell と job

共通 = `ycsb_tuple_num=200 ycsb_zipf_skew=0.9 extime=1 -clocks_per_us=2100`。

| cell | flags | 使い道 |
|---|---|---|
| K | `ycsb_rratio=50 ycsb_rmw=false ycsb_max_ope=10` | V36 (読む key と書く key が分かれる write skew の条件) |
| S1 | `ycsb_rratio=0 ycsb_rmw=true ycsb_max_ope=1` | V29 (1 取引 1 key の RMW。別 key の write skew は起きない) |
| S2 | `ycsb_rratio=50 ycsb_rmw=false ycsb_max_ope=1` | V28 (読み専用と blind write の 1 操作取引の混在。R が残り、write skew は起きない) |
| W | `ycsb_rratio=0 ycsb_rmw=true ycsb_max_ope=5` | 生死確認だけ (mocc の W と同じ) |

変異の cell に K を使わないのは、K では無改変の si 自体が write skew で non-serializable になり、変異の効果と区別できないため (段 3 相談 A-04、段 4 裁定)。

| run | request | 計算ノード | Elapse | 起動器の rc | checkout | build と cell |
|---|---|---|---|---|---|---|
| l0-a | 29768.nqsv | bnode096 | 36 s | 1 | `a68c312ef` | V2: K・W × t1・t4 (parse error、§1 結論 1) |
| l0-b | 29774.nqsv | bnode095 | 64 s | 0 | `0db1ae583` | V2: K・W × t1・t4 |
| j1-a | 29851.nqsv | bnode072 | 79 s | 0 | `d44fc3f70` | V2: K t1・K t4・S1 t4 / V29: S1 t4 |
| j2-a | 29852.nqsv | bnode093 | 67 s | 0 | `d44fc3f70` | V2: S2 t4 / V28: S2 t4 |

l0-a・l0-b は事前登録の前の探索走 (生死確認) で、分類には使わない。V36 の本走の値は j1-a で取り直した。

## 3. 観測と分類

「巡回」は verifier の `total_cycles`。integrity の他の項目 (orphan read・version dup・txid の重複と欠番・genesis への commit・版の不一致・key の不正・frame の破れ) は、表に書いたもの以外すべて 0。X・P・I は全 run で evidence-absent。全 run が rc 0 で約 1 秒で完走した (停止・異常終了 0)。

### 3.1 検出表

| V | 変異 | cell | 観測 | 分類 |
|---|---|---|---|---|
| V36 | 無改変の si (snapshot isolation は write skew を許す) | K t4 | non-serializable、巡回 2,236。C 175,043・R 722,988・W 813,764 | 無改変 si の巡回検出 |
| V36 | 同上 | K t1 | indeterminate、巡回 0 (1 thread は巡回しえない) | 期待どおり (対照) |
| V29 | first-updater-wins の abort を外す | S1 t4 | indeterminate、巡回 0。C・W 1,232,351、R 0。診断 reached 17,825・changed 17,732・committed 17,732 | 盲点 (発火し commit したが trace に現れない) |
| (対照) | 無改変 + v2 | S1 t4 | indeterminate、巡回 0。C・W 1,011,561、R 0 | 対照正常 |
| V28 | 版選択の status 除外を外す | S2 t4 | indeterminate、orphan read 45、巡回 0。C 1,395,478・R 698,372・W 697,106。診断 reached = changed = committed = 2,931 | 期待した層で検出 (orphan) |
| (対照) | 無改変 + v2 | S2 t4 | indeterminate、巡回 0、orphan 0。C 1,408,513・R 704,977・W 703,536 | 対照正常 |

### 3.2 分類の規則 (事前登録 R4 のまま、事後の変更なし)

si は証拠面が無いので S は出ない。優先順は timeout → 停止、rc≠0 → 別の層 (process 異常終了)、完走なら次のとおり。V36: 巡回 > 0 → 無改変 si の巡回検出、0 → 巡回未観測。V29: changed > 0 かつ committed > 0 で巡回 0・integrity 0 → 盲点、巡回か integrity が正 → 別の層で検出、changed 0 → 未発生。V28: orphan > 0 → 期待した層で検出、orphan 0 で他の層が正 → 別の層、全部 0 で changed・committed > 0 → 盲点、changed 0 → 未発生。対照が巡回・integrity・異常終了・停止のどれかを出したら同 job の変異 cell は帰属不能。

### 3.3 読み方

- **V29 の盲点は trace の作りから来る。** si の update は同じ key の読みを read set から消すので (`cc/si/transaction.cc:239-247`)、読んで書く取引の R 行は trace に残らない。S1 では R 行が 1 行も無く、lost update は「同じ key に順に書いた W」としか見えない。版は commit 順 (cstamp) で並ぶので ww の辺は前向きだけで、巡回にならない。無改変の si の W 条件 (生死確認) でも R 行は 0 だった。この観測は S1 と W の 2 条件のものである (段 3 相談 B-04)。
- **V28 の orphan は一部しか現れない。** R 行の版番号は commit 時に保持中の版から読み直す (`cc/si/transaction.cc:541-544`) ので、読んだ未確定の版を書いた取引が先に commit していれば、R 行は正常な commit 番号になる。orphan になるのは、読んだ版の番号を書いた取引が trace に無い (abort した、または未確定のまま) 場合で、2,931 回の未確定読みのうち 45 件だった。残りが「正常な番号に置き換わった」のか「偶然別の書き手の番号と一致した」のかは分けていない。
- **V36 の巡回は schedule 依存である。** 生死確認 l0-b の同 cell は巡回 2,443、本走 j1-a は 2,236 で、どちらも 1 回の 1 秒の走の値。件数を比べる意味は無い。
- **v2 frame の検査の範囲:** framing violation 0 は「出た frame の構造 (C の宣言件数と R/W 行数、E の有無) が整っていた」という意味で、件数は R/W と同じコンテナから取るので独立の完全性の証人ではない。abort した取引は emitter に届かない (段 3 相談 A-06)。

## 4. 走らせなかったもの・変えなかったもの

- 変異の K 条件 (V29・V28 を write skew の条件で走らせること): 無改変の si が N を出すので帰属できず、事前登録から外した。
- `include/trace.hh`・`include/tpcc.hh` (共有 header): 変えていない (D297 の header 受理は [T-2854] の設計審査待ち)。si の v2 化を `izanagi-trace` 枝へ移して pin を進めるのは人間の判断 (D16)。
- verifier・parser・既存 driver・policy・calibration JSON は編集していない。条件 gate への登録と表の test の追随は、新しい patch を既存の経路で build するためのもの。

## 5. 記録の置き場と束縛

- `raw/{l0-a,l0-b,j1-a,j2-a}.agg.jsonl`: 結果 JSON から親が jq で抜き出した行 (meta = hostname・checkout HEAD・build source の OID・policy・patch の sha256 と touch set・build の状態と gate の admission、run = verdict・巡回・integrity・trace 行数・発火行・stdout / stderr の sha256)。
- 結果 JSON の原本 (job dir `runs/`、repo に入れない): l0-a `f4da75563740e3883a2738e17d2ef753ad21b38bd7070b7042ac4157ddbee587` (13,021 bytes)、l0-b `9c13dca2d51ddbec9da45b241b9ef509adf9fb9b46e9382295338a984195f841` (49,452 bytes)、j1-a `3f1d59ebf72939566d46e2cedf0880bb83e9e65371f6f376d86cfc9e91a272ba` (273,470 bytes)、j2-a `2cd3503fbc83ceeed2ca66f54d721e7d02f9923ad9bb54682cffd75d56e04d7c` (234,046 bytes)。run ごとの stdout / stderr は `runs/<tag>/raw/`。
- `verbatim/s5-author-ua.md` は、patch 本文の空の文脈行 (空白 1 個だけの行) 12 行 (26・30・49・60・74・90・107・135・139・159・170・199 行) を空行にした可逆な正規化をしている (`git diff --check` のため)。原文は sha256 `9a6d3dcbf93ce83b1520bf155ef5df43eac3fa857b5e5626c3640f78ca9a2e29`・8,716 bytes、job dir `codex/s5-author-ua.md`。復元はその 12 行に空白 1 個を戻す。

## 6. 焦点走と変異 matrix

焦点走: 変更した本体 2 file (`condition_meaning_gate.py`・`screening_driver.py`) を参照する test と patch を glob する test、DW-O26 の inventory 4 群の計 33 file (先例 mocc と同じ集合) を、計測の終わった clean な計測 checkout (HEAD `d44fc3f70`) から `tools/run_tests.py --force-dispatch` で走らせた: **4,056 passed・8 skipped・失敗 0** (request 29858.nqsv、Elapse 146 秒)。その後の fix (段 6 RB-02) は `test_screening_driver.py` をこの wave の前と同じ内容に戻しただけである。

変異 matrix (実装面 = 条件 gate の登録の誤りを既存の test が殺すか): `tools/mutation_worktree.py` を独立 clone (main = `82fbb8256`、fix 後の実装の最終 commit) に当て、runner = `tools/run_tests.py --force-dispatch` で `test_condition_meaning_gate.py`・`test_ccbench_spawn_sites.py`・`test_screening_driver.py`・`test_p3_s4_loop.py::test_all_naked_izanagi_macro_patches_are_registered_or_allowlisted`。変異は段 4 裁定 R9 のとおりで、置換対象がちょうど 1 箇所・置換後の文字列が既存に無いことを投入前に確かめた。

- probe (全件 SURVIVED 期待の観測走、spec sha256 `dc93372166916c4129fb83a1defa560b083dfdc55ea2f915d22a588743cb2c03`): 基準走 PASSED、正例 M0 は生存、M1〜M4 はすべて赤 (`raw/mutation-probe-summary.json`、原本 sha256 `ddb3747e99429917a88e24fe3fb4025b1eeccf4f5c0c824fc6b80dd9b045127e`)。
- final (観測した赤 node を期待 node に固定、spec sha256 `7dba10154156153deb68ee8a4d9b0961f90453b2cf34317e7921de105a9b528b`): 基準走 PASSED、**KILLED 4・SURVIVED 1 (正例)・MISMATCH 0** (`raw/mutation-final-summary.json`、原本 sha256 `42f19759721e7a88087cb0c4b1b527f1ff7af5d889a79f7c6f093c498f9cccf5`)。

| 変異 | 誤り | 赤 node 数 | 赤の理由 |
|---|---|---|---|
| M0 (正例) | comment 1 語の変更 | 0 | — |
| M1 | `_DEFINE_SPECS` から V29 の macro を削る | 7 | 登録簿から 1 件欠けた (在庫照合・domain 件数・branch 選択の 3 parametrize・registry の patch 束縛・screening の集合照合) |
| M2 | `_CONDITIONAL_BRANCH_WITNESSES` から V28 を削る | 5 | witness の欠落 (patch 束縛・branch 選択の 3 parametrize・domain 件数) |
| M3 | `_DEFINE_SPECS` の V28 の key を 1 字違える | 7 | 登録名と patch の macro の不一致 |
| M4 | V29 の site 数を 7 → 8 | 4 | site 数と patch 本文の不一致 |

赤 node の形は先例の mocc の登録 (`output/insights/2026-09-26/t2847-mocc-run/README.md` §7) と同じだった。各変異の赤 node は複数だが、どれも 1 つの誤り (登録の 1 件の欠落・名前違い・件数違い) から生じている。patch の中身 (未定義側の一致・1 patch 1 機構) は test では殺せないので、実装子の枝除去の照合、段 6 レビュー A の source 照合、§3 の実走 (対照正常・発火診断) で確かめた。

計算ノードの使用 (runner が報告した所要、queue 待ちを含みうる): probe 810 秒 (基準走 135 秒 + 変異 5 本 674 秒)、final 826 秒 (135 秒 + 691 秒)。probe の job 作業 dir は harness が片付けた後で job の Elapse 行が残っていなかったので、runner の値で記録した。ここまでの計算の合計 (job Elapse と runner 所要): 生死確認 100 秒 + 本走 146 秒 + 焦点走 146 秒 + 変異 1,636 秒 = 2,028 秒 (約 0.56 node 時間)。

## 7. 受入全走

受入全走と land は本書を含む記録 commit の後に走るので、本書には結果を書かない (job dir の `acceptance-*` / `land-*` が正本)。

## 8. 限界・言わないこと

- 各 cell は 1 回の 1 秒の走の観測である。V36 の巡回、V29 の盲点、V28 の orphan 45 はどれも schedule に依存し、別の走では件数が変わる。
- 「盲点」(V29) は、lost update が起きて commit したのに verifier の判定が巡回や integrity として捕まえなかったという観測で、si の直列化可能性の主張ではない (si は証拠面が無く、どの履歴も certified にならない)。
- V28 の orphan 45 は、未確定の版の読み 2,931 回のうち trace に orphan として現れた数で、残りの読みがどう現れたか (正常な番号への置き換わりか、他の書き手の番号との一致か) は分けていない。未完成の値を読んだかどうかも測っていない (YCSB は値を検査しない)。
- V28 で異常終了は起きなかったが、それは未定義動作が無いことを示さない (1 回の走で起きなかっただけ)。
- V29・V28 の効果は 1 操作の cell (S1・S2) だけで測った。write skew の条件 (K) での変異の挙動は測っていない。
- v2 frame の件数は R/W と同じコンテナから取るので、R/W の欠落を独立に捕まえる証人ではない。
- verify は証人なしの verifier (commit 件数の証人を渡していない) で、trace の末尾の取引の欠落は捕まえない (設計書 §2)。
- 性能値は取っていない。job の Elapse は計算資源の記録である。
