## (P1)〜(P8) への賛否

| 項 | 判断 | 理由・修正点 |
|---|---|---|
| P1 | 賛成 | header 用の入力一式が揃った起動だけ新分岐へ進める。未指定時は現行の拒否文言を逐語で維持する。[検査器:180](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/tools/check_trace0_preprocess_identity.py:180) |
| P2 | 賛成 | 1 起動を C/C++ compiler の 1 組に限定し、GCC 11.4 と 12.3 は別々に configure する。report に両 compiler の実パスと版を記す。 |
| P3 | **条件付き賛成** | [`_v2_commands`:1949](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/orchestrator/campaign/buildcache.py:1949) は configure argv の再利用元になる。ただし `toolchain` は `{"cmake":{"realpath":…},"cc":{"realpath":…},"cxx":{"realpath":…}}` 形が必要で、返す build target は常に `ycsb_<protocol>.exe`。stock は空 flags の `Genome(protocol, {})` を渡し、返った **configure argv のみ**使う。target を production 判定の情報源と取り違えない。 |
| P4 | **条件付き賛成** | stock と、production target に consumer を持つ protocol の全 genome を選ぶ。production target の一覧は現行の固定文字列を検査器へ複製せず、実際の production 経路から導く必要がある。並走 wave が tpcc を production に加えた場合、その変更を反映する。各 configure で consumer は再列挙する。 |
| P5 | 賛成 | compile argv の単一で明瞭な `-DTRACE=0` token を依存照会時だけ `1` へ置換し、別 configure は作らない。`-dM -E` で **各 consumer・各 side の TRACE=0/1 の実効値**を確認する。token が無い第三者 entry には後付け指定だけで成功と見なさず、曖昧な指定は拒否する。 |
| P6 | 賛成 | hydrate した固定 third-party source を使い、masstree だけは side・compiler・configure ごとに複製して `masstree_build` を実行する。`config.h` は build dir でなく masstree `SOURCE_DIR` にできる。[ThirdParty.cmake:57](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/external/ccbench/cmake/ThirdParty.cmake:57) |
| P7 | **条件付き賛成** | 実 CMake・実 g++ の小型 fixture が妥当。ただし repo の `run_tests.py` を通して実行場所を判定させる。login を一律 skip する設計にはしない。1 test の秒数は未測定なので、実装後に測り 5 分枠内へ収める。 |
| P8 | 賛成 | `.cc` だけなら従来の `check()` 戻り値と JSON serialization を同じ経路で生成し、bytes を固定する。header を含む場合にだけ新 field を足す。既存 caller は引数を変えない。[mocc_trace_pilot.sh:1900](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/tools/pegasus/mocc_trace_pilot.sh:1900) |

## 実装 plan (file:line)

1. [検査器:43–65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/tools/check_trace0_preprocess_identity.py:43) に header 分岐専用の保証名・入力検証を置く。冒頭の D780 項 1 の文言は維持する。`.cc` 専用の `GUARANTEE` と `SCHEMA` は触らない。header 分岐を有効にする入力は、C compiler、CMake、offline third-party cache、dependency prefix、作業 scratch root を一組として明示させ、欠けた組合せは拒否する。header 無しでは新入力を処理経路へ流さない。

2. [検査器:180–201](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/tools/check_trace0_preprocess_identity.py:180) の diff 検証は status `M`・mode 不変・regular file という共通拒否を先に保ち、header suffix のとき「有効化入力が無ければ現行文言で拒否／あれば header path として返す」にだけ変更する。非 C/C++、A/D/R/C、mode 変更の拒否は維持する。`.cc` と header の同居は両経路の成功を要する。

3. [検査器:651–725](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/tools/check_trace0_preprocess_identity.py:651) の header 経路で、旧新 commit を **git worktree** に同じ長さの sibling path（例 `src-old` と `src-new`）へ展開する。Git tree の path・型・mode と checkout 実体を照合し、欠落・余剰・不一致を拒否する。`git archive` は export-ignore により `cc/oze` 等を落とし得るため採用しない。生死確認 driver は `git archive` 前に attributes を上書きして通した使い捨て probe であり、そのまま実装へ移さない。[driver:100–118](/work/1/SFC/tanab/tmp/t2854-d297-header-v2-20260927/driver/liveness.py:100)

4. 同 header 経路で [fetch_third_party.py:621–695](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/tools/pegasus/fetch_third_party.py:621) の `hydrate` を使い、固定 pin の masstree・mimalloc・googletest source を offline 配置する。各 configure・各 side に固有の masstree 複製と build dir を作り、configure 後 `masstree_build` を成功させ、`config.h` の存在を確認してから依存列挙する。生死確認ではこれで全 135 entry の `-MG` なし依存列挙が成功した。

5. [buildcache.py:1949–2033](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/orchestrator/campaign/buildcache.py:1949) を configure argv の生成元として呼び、`-DCMAKE_EXPORT_COMPILE_COMMANDS=ON` を加える。compiler の実パス、dependency prefix、FetchContent base と source dirs を明示する。stock は空 flags の `Genome` による Release・sanitizer OFF・`CCBENCH_TRACE=0` と定義する。[model.py:124–152](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/orchestrator/campaign/model.py:124) `CCBENCH_CCACHE=OFF` を使うなら、production argv との差分として report に明記し、compile database の compiler argv が実行可能であることを検査する。

6. stock の compile database を起点に全 entry の依存を旧新 × TRACE=0/1 で列挙し、変更 header を読む entry から production target の protocol を決める。現行 `ycsb_<protocol>.exe` は `_v2_commands` の target 定義にあるが、tpcc 追加を見落とさないよう production 経路の更新を参照する。[buildcache.py:1961–1963](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/orchestrator/campaign/buildcache.py:1961) 該当 protocol の [SPACES:208–220](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/orchestrator/campaign/genome.py:208) を全列挙して configure 集合を固定する。各 configure では **全 entry の依存を取り直し、全 consumer** を比較する。別 protocol の argv だけが変わる場合もここで拾う。

7. compile database は `file`・target・argv を鍵に、確認済みの source/build/masstree prefix **のみ**対応する論理 prefix へ置換して旧新の entry 集合と argv を厳密照合する。単純な任意部分文字列置換、重複 entry の集合化、片側にだけある entry の無視を避ける。依存出力は `-MG` を使わず全 entry・両 TRACE 値・両 side で成功を要求し、変更 header ごとの選定集合全体の consumer 0 件を拒否する。

8. 依存・前処理 argv は compile database の `arguments` を優先し、`command` しかない場合は明瞭に分解できる形だけ受ける。出力用の `-c`、`-o`、`-MF` 等を除き、`@file`、`-Wp,`、複数・欠落・衝突する TRACE 指定など不透明な argv は拒否する。`-dM -E` で各 consumer の実効 `#define TRACE 0` と `1` を確認する。生死確認で TRACE token が無かったのは third-party の 18 entry（2 値で 36 照会）だけで、consumer 21 entry は確認可能だった。[driver:25–42](/work/1/SFC/tanab/tmp/t2854-d297-header-v2-20260927/driver/liveness.py:25)

9. 比較予定集合 `(compiler, configure, entry)` を **実行前に固定**し、各要素の旧新 `-E -P -dD` 完全展開と `-E` の line marker から得る入退場 file 列を byte 比較する。実行済み集合は重複・過不足なく予定集合と一致させ、0 件を拒否する。正規化は照合した prefix のみ。`__DATE__`、`__TIME__`、`__TIMESTAMP__` 等が出力に入り再現条件を固定できなければ拒否する。line marker の行番号全体や診断位置の同一性は保証に含めない。[設計審査 §4 R5–R7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/output/insights/2026-09-26/t2854-d297-header-review/README.md:63)

10. [検査器:516–648](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/tools/check_trace0_preprocess_identity.py:516) の `.cc` 比較には手を入れない。そこは include を除去した `_cpp_normalize` と 16 文脈の方式であり、header consumer の実 compile argv 比較へ流用できない。[source_digest.py:1647–1714](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/orchestrator/campaign/source_digest.py:1647) header report に configure 集合、compiler、consumer と予定・実行件数、比較 digest を追加する。`.cc` だけの report は既存 object と [CLI の sort_keys serialization:746–755](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/tools/check_trace0_preprocess_identity.py:746) を通し、bytes を変えない。

生死確認は 48 core node で、1 side あたり configure 0.69–0.80 秒、masstree 10.56–10.59 秒、135 entry × TRACE 2 値の依存列挙 10.93–11.05 秒（48 並列）、consumer 21 件の TRACE 確認 1.89–2.10 秒、旧新 42 比較 5.36–5.78 秒（8 並列）だった。1 configure の旧新対は約 54 秒。17 configure × 2 compiler = 34 対を直列なら約 31 分、約 **0.52 node 時間**。この実測の並列度を上限候補とし、configure 自体を大量同時起動して masstree build と前処理を競合させる設計は避ける。[親の生死確認要約](/work/1/SFC/tanab/tmp/t2854-d297-header-v2-20260927/s1-live-summary.md)

## test plan

[既存 test:623–635](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/orchestrator/tests/test_check_trace0_preprocess_identity.py:623) の「入力無し header 拒否」は文言を含め維持する。[同:219–240](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-d297-header-v2/orchestrator/tests/test_check_trace0_preprocess_identity.py:219) の `.cc` 決定的 report に、既存 caller 相当の stdout bytes 回帰を足す。

header 用 fixture は小型 Git repo の CMake project とし、`ycsb_silo.exe`、`ycsb_mocc.exe` と別 protocol target を作る。`include/changed.hh` を直接読む TU と `wrapper.hh` 経由でしか読まない TU を用意する。custom target が `generated/config.h` を生成し、その先の include が変更 header に届く形を作る。`CCBENCH_KEY_SORT` 相当の CMake option が **他 protocol consumer の compile argv だけ**を変える fixture を入れる。実 `cmake`・実 `g++` を用い、依存解析や前処理の中核は stub にしない。stock と選定 genome の集合は fixture 用に小さく保ち、1 test の秒数を実装後に測る。全 suite の 5 分上限を超えるなら fixture の構成数と重複起動を減らし、必要な経路の実行は残す。テスト実行は `tools/run_tests.py` 経由とし、login で実行可能かは同ツールの量・場所判定に従う。今回、テストは実行していない。

追加で、旧新 database の片側 entry・argv 差、TRACE macro の未確認、`@file`／`-Wp,`、consumer 0、依存失敗、予定件数の欠落、header と `.cc` の同居、export-ignore のある tree、同じ長さの source root と照合済み prefix だけの正規化を、それぞれ一つの失敗理由が見える fixture で確認する。

## 変異の対応表

| §6 | 変異 | 殺す test・期待 |
|---|---|---|
| 1 | 間接 include consumer の TRACE=0 値変更 | `test_header_indirect_consumer_value_change`：依存閉包で選ばれ、展開不一致。直接 include 列挙への劣化を殺す。 |
| 2 | `#if !TRACE` 内の値変更 | `test_header_trace_zero_value_change`：展開不一致。 |
| 3 | 必須 include を `#if TRACE` 内へ移動 | `test_header_include_activity_change`：入退場 file 列の不一致。 |
| 4 | 生成 header 不在で依存探索が途中停止 | `test_header_generated_dependency_required`：生成工程を欠かす／`-MG` に劣化させる変異を、依存列挙の失敗または consumer の欠落として拒否。 |
| 5 | 選定 configure で他 protocol consumer の argv だけ変更 | `test_header_cross_protocol_consumer`：その entry も予定集合に入り、旧新展開差で拒否。 |
| 6 | consumer 0、または予定集合から 1 件欠落 | `test_header_zero_consumer` と `test_header_missing_planned_comparison`：それぞれ 0 件拒否、予定／実行集合不一致。 |
| 7 | 実 CCBench の H-line、`tpcc.hh` の `#line 56` 削除 | 計算ノードの `test_real_ccbench_h_line_negative`：TPC-C consumer の完全展開不一致。 |

単一理由性は、各 fixture の他の条件を正常に保ち、期待した拒否箇所と最初の失敗理由を確認する。#4 は「生成失敗」と「`-MG` による偽緑」を別に観測する必要があり、同一 test にまとめると単一理由性が弱い。

## 実 CCBench 判定 job

計算ノード **1 job** に C `68106660686232781bca3be792a750d3e19d7a8a` → C2′ `40a7f4acb174ca43cb590f40d13847216a1564bc` の旧新 Git object、offline third-party cache、dependency prefix、GCC 11.4 と 12.3 を渡す。job 内で compiler ごとに改訂後の検査器を 1 回ずつ起動し、各々 stock＋選定全 genome を走査する。両 report と rc、構成一覧、予定／実行件数、所要秒、node 時間を job dir に保存する。片方でも失敗なら C2′ を D297 pass と呼ばない。両方 pass しても pin 前進は別のユーザー裁定であり、実費と gitlink・`CCBENCH_FULL_SHA`・`CURRENT_PIN` への波及を提示する。[D2260 項 1](/work/1/SFC/tanab/tmp/t2854-d297-header-v2-20260927/verbatim/D2260-item1.md)

見積りの判定本体は約 0.52 node 時間。wave 全体の中央見積りは約 1.4 node 時間、再走込みの上側は約 2.1 node 時間。**1 タスクの job 合計が 2 node 時間以上となる時点**では、D2260 の条件どおり投入前にユーザー確認を取る。

## 未確定と親への問い

1. **production target の単一の出所。** 現状の `_v2_commands` は `ycsb_<protocol>.exe` 固定で、tpcc production の追加を表現しない。並走 wave が入った後、どの production target 定義を参照するかを実装時に確定したい。推奨はその wave の production 経路を直接参照し、検査器内に target 名の固定リストを作らないこと。
2. **stock の protocol 引数。** `_v2_commands` には `Genome` が必須だが、空 flags なら configure argv の genome define は空になる。推奨は既存 protocol 名の空 flags `Genome` を使い、返る build target を stock の意味付けに使わないこと。
3. **TRACE token 不在 entry の扱い。** 生死確認では third-party 18 entry のみ不在だった。推奨は全 entry の依存列挙成功を要求しつつ、consumer となった entry で TRACE 実効値を確認できなければ拒否すること。無関係な third-party entry に仮の TRACE を注入して保証対象を増やしたとは主張しない。

## scope 外候補

選定外 genome、Debug・opt-in target、GCC 以外、compile database に載らない TU、admission build・link object・symbol/data・receipt の結合は今回の実装範囲外。後者は [D780 項 2](/work/1/SFC/tanab/tmp/t2854-d297-header-v2-20260927/verbatim/D780.md) の別防壁として維持する。

## 総括

実装の要点は、既存 `.cc` 経路を bytes ごと保ち、header だけを実 compile database の依存閉包と全 consumer の旧新比較へ分岐させることにある。生死確認は必要な生成物と 34 対の費用を示したが、使い捨て driver の `git archive` と簡易正規化は規則 v2 の実装には転用できない。今回は指定どおり静的検査のみを行い、ファイル変更・テスト実行・判定 job 投入はしていない。