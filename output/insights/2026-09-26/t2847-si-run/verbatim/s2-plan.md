## 1. V29 patch

**案:** `patches/broken-si-first-updater-wins.patch`、裸マクロ `IZANAGI_BREAK_SI_FIRST_UPDATER_WINS`。pin C の [SI:198–206](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/external/ccbench/cc/si/transaction.cc:198) にある「snapshot 後に committed となった版を見て abort する」分岐だけを、`#if TRACE` 内の `#if IZANAGI_BREAK_SI_FIRST_UPDATER_WINS` で迂回する。SI:176–187 の inflight 分岐は残す。これが設計書 §4.5 の V29 に対応する最小変更である。

迂回後も [SI:209–213](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/external/ccbench/cc/si/transaction.cc:209) の `compare_exchange_strong` は残る。CAS 失敗時には更新された `expected` でループを再試行するため、この変更だけでループの停止条件は失われない。ただし競合が続く場合の完了は保証しない。版の解放経路には触れず、変更由来の二重解放は作らない。

診断は同じマクロの有効枝内に置く。`reached` は元の `txid_ < vertmp->cstamp_` が真になった回数、`changed` はその競合を許したうえで CAS に成功した回数、`committed` は `changed` を経験した取引が [SI:653–661](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/external/ccbench/cc/si/transaction.cc:653) で成功した件数とする。取引ごとの印は `begin()` で戻す。relaxed atomic の集計を終了時に stderr へ `T2847_FIRED slug=si-first-updater-wins reached=... changed=... committed=...` の **1 行**で出す。診断も `#if TRACE` と壊しマクロの内側に限る。

[v2 patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/patches/instr-si-trace-v2.patch) の hunk は SI:526–554 の emitter だけで、V29 の機構 hunk は SI:198–213。位置は離れており、pin C → v2 → V29 の順に重ねられる設計である。実際の `git apply --check` は未実施。

## 2. V28 patch

**素朴な案は実走用 patch にできない。** 候補名は `patches/broken-si-read-uncommitted-version.patch`、裸マクロは `IZANAGI_BREAK_SI_READ_UNCOMMITTED_VERSION`。変更箇所は [SI:153–158](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/external/ccbench/cc/si/transaction.cc:153) のループ条件で、status による inflight / aborted 除外だけをマクロ枝で外し、`txid_ < ver->cstamp_` の snapshot 条件を残す。v2 patch の SI:526 以降とは hunk が離れている。

しかしこの選択は版の寿命と payload の安全性を満たさない。`install_version()` は [SI:209–212](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/external/ccbench/cc/si/transaction.cc:209) で inflight 版を公開し、その**後**に [SI:290–292](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/external/ccbench/cc/si/transaction.cc:290) で `body_` を代入する。V28 の読者は未完成の body を [SI:126–135](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/external/ccbench/cc/si/transaction.cc:126) から使いうる。また abort した INSERT は [SI:579–586](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/external/ccbench/cc/si/transaction.cc:579) で `Tuple` を削除する。読者が保持する `Version*` は [SI:164](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/external/ccbench/cc/si/transaction.cc:164) の read set に残り、commit 時には [SI:541–544](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/external/ccbench/cc/si/transaction.cc:541) で再参照される。GC も古い版の鎖を外して再利用キューに入れる ([garbage_collection.cc:82–99](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/external/ccbench/cc/si/garbage_collection.cc:82))。この変更だけでは、削除・再利用後の参照を安全と証明できない。

abort 版の `cstamp_` は install 前に入れた**書き手の begin `txid_`** ([SI:283–285](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/external/ccbench/cc/si/transaction.cc:283)) であり、commit stamp ではない。inflight 版が後で commit すれば [SI:508–519](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/external/ccbench/cc/si/transaction.cc:508) で stamp が変わるため、R 行には**読んだ時点でなく trace 出力時の値**が載る。この経路では orphan を見逃しうる。

したがって V28 の `reached`（status が inflight / aborted の候補を見た回数）、`changed`（その版を選んだ回数）、`committed`（それを読んだ取引の成功件数）と `T2847_FIRED slug=si-read-uncommitted-version ...` は診断仕様として定義できるが、診断を足しても上記の未定義動作は解消しない。**現スコープの「status 除外だけを外す V28」は作れず、V28 build・run は投入しない**、という裁定を段 4 に返すべきである。安全な別実装には版の公開・保持・回収の契約変更が要り、ここで要求された最小 patch を超える。

## 3. 期待 (事前登録案)

verifier は巡回があれば N、巡回がなく si の証拠面もなければ I とする ([model.py:505–515](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/orchestrator/verifier/model.py:505)、[model.py:556–568](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/orchestrator/verifier/model.py:556))。**S はどの si cell にも期待しない。** L0 の v2 対照は K t1 が I・巡回 0、K t4 が N・巡回 2,443、W t1/t4 が I・巡回 0で、全 cell の framing・orphan・version dup は 0 だった ([liveness.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-si-v2/liveness.md))。

| 行・cell | 事前期待 verdict | 主に見る層 |
|---|---|---|
| V36＝V2 対照、K t1 | I | 巡回 0。異常の未観測 |
| V36＝V2 対照、K t4 | N を期待、schedule 依存で I も許容 | 残った R と W による巡回 |
| V36＝V2 対照、W t1/t4 | I | R が消えるため巡回 0 を期待 |
| V29、K t1/t4 | N または I。N の必然性は事前登録しない | 巡回を主に集計。orphan・version dup・framing は 0 を期待 |
| V29、W t1/t4 | I を期待 | 同じ key の R が消え、lost update は通常 ww 辺だけになる |
| V28、全 cell | **実走対象外** | 安全な patch が成立した場合に限り別途事前登録 |

[SI:239–247](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/external/ccbench/cc/si/transaction.cc:239) と [SI:361–365](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/external/ccbench/cc/si/transaction.cc:361) は update / delete した同じ key の R を消す。V36 の write skew は**別 key を読む K**で観測する。V29 の同一 key lost update は W で機構を発火させても R による巡回には結び付きにくい。V28 も、仮に安全に実装できた場合、汚れた版の R が後続 update で消えれば orphan は出ない。版番号の producer が trace にない非 genesis R だけが orphan となる ([dsg.py:260–269](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/orchestrator/verifier/dsg.py:260))。version dup は同一 `(key, commit version)` を複数取引が書いた場合であり、V29 の単なる上書きからは導けない ([dsg.py:454–474](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/orchestrator/verifier/dsg.py:454))。

分類は D2239・D2246 を si に写し、**verdict、期待層の counter、発火診断を別々に記録**する。V29 で `changed>0` かつ `committed>0`、期待層の counter が 0 なら「発火したが観測できない盲点」とする。ただし si では *certified* と呼ばない。診断が 0 なら「未発生」、診断がなく I の場合は「発火未確認の I」とする。N と integrity が併発すれば期待層を主分類、併発を別欄に記す。timeout は verdict なしの「停止」、同 job の V2 対照が異常なら「帰属不能」。V36 は無改変で発火診断を持たないため、K の巡回正なら「無改変 si の巡回検出」、0 なら「巡回未観測」と記し、変異の盲点・未発生に数えない。

## 4. cell と job

[L0 起動器:24–32](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-si-v2/launch_si_run.py:24) の K（200 tuple、zipf 0.9、read 50%、`rmw=false`、max_ope 10、1 秒）を write skew 用、W（同じ規模、read 0%、`rmw=true`、max_ope 5、1 秒）を同一 key 読み書き用として固定する。各々 1・4 thread。K t4 は L0 で巡回を観測し、W は両 thread とも R=0 だった。V29 の同一 key 条件は W で機構の発火を調べ、K で残存 R による巡回を調べる。

投入可能な本走は **J1: V2 対照＋V29 の 2 build、K/W × t1/t4 の各 4 run** とする。V28 を安全に実装できる別裁定があった場合だけ J2: V2 対照＋V28 の 2 build、同じ 4 cell を加える。各 job の対照を同一 job・同一 cell に置き、壊し patch は対照 build に適用しない。1 job は 2 build＋run であり、必要なら K と W を別 job にしても各 job に V2 を置く。

L0-b は **1 build＋4 run で Elapse 64 秒**、L0-a は同構成で 36 秒だった。2 build＋8 run の J1 は実測単価から概ね **1～3 分**を投入見積りとするが、build と verify の固定費があるので比例換算は上限保証ではない。V28 の仮の J2 を含めても同型 2 job で概ね **2～6 分**。性能値ではなく job Elapse の資源見積りである。

## 5. 条件 gate への登録

[condition_meaning_gate.py:76–79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/orchestrator/campaign/condition_meaning_gate.py:76) に `_SI_OWNER = ("cc/si/transaction.cc",)` を置き、登録する壊し macro ごとに `DefineSpec(ROUTE_CMAKE_CXX_FLAGS, _SI_OWNER, "ycsb_si.exe", "patches/broken-si-….patch")` を追加する。対応する `#if IZANAGI_BREAK_SI_*` の witness を [同:347–388](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/orchestrator/campaign/condition_meaning_gate.py:347) に、patch 内で実際に置いた同名 directive の個数を [同:473–502](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/orchestrator/campaign/condition_meaning_gate.py:473) に登録する。V29 は機構分岐・診断の file scope・`begin`・commit の配置に応じた**実 patch の個数**を数える。V28 を作れない現計画では V28 macro を先行登録しない。

gate の owner TU と target の照合は request の tuple と compile command の `CMakeFiles/ycsb_si.exe.dir/` を使える ([同:1186–1188](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/orchestrator/campaign/condition_meaning_gate.py:1186)、[同:2030–2055](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/orchestrator/campaign/condition_meaning_gate.py:2030))。一方、`make_define_request(..., protocol="si")` は [同:1105](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/orchestrator/campaign/condition_meaning_gate.py:1105) で拒否される。今回の新 macro は登録済み `DefineSpec` から owner と target を引くため、既存 mocc driver と同じ **既定の `protocol` 引数**で request を作ればよい。`PROTOCOL_CMAKE_REL = "cc/silo/CMakeLists.txt"` ([同:533–536](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/orchestrator/campaign/condition_meaning_gate.py:533)) はこの新規 macro の owner/target 宣言に使わない。判定ロジックは変えない。

追随箇所は [test_condition_meaning_gate.py:47–68,161–165,3467–3525,3611–3616](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/orchestrator/tests/test_condition_meaning_gate.py:47) の macro・witness・件数、[test_p3_s4_loop.py:8362,8463–8482](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/orchestrator/tests/test_p3_s4_loop.py:8362) の裸マクロ patch allowlist、[test_ccbench_spawn_sites.py:3572–3578](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/orchestrator/tests/test_ccbench_spawn_sites.py:3572) の cross product 件数、[screening_driver.py:51–100](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/orchestrator/campaign/screening_driver.py:51) の既定値 `0` の表と対応する `test_screening_driver.py` の表照合である。先例 commit `267b8992f` は同種の登録でこの 5 file を変更している。**現計画で追加する macro が V29 の 1 個なら、59 件は 60 件、CXX flags 35 件は 36 件**に更新する。V28 が成立して 2 個ならそれぞれ 61・37 件となる。

## 6. 起動器の拡張

[launch_si_run.py:23–32](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-si-v2/launch_si_run.py:23) の `BUILDS` に V29 の `[v2 patch, V29 patch]` と macro を足し、`JOBS` に §4 の表を足す。[同:105–123](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-si-v2/launch_si_run.py:105) の `build_variant` は macro がある場合、共通 configure 引数を作った**後、実 build の前**に `condition_meaning_gate` の capture → request → supply / meaning → admission を呼び、その成功記録を build JSON に保存してから `-DCMAKE_CXX_FLAGS=-D<macro>=1` を追加する。target と binary path は既存の `ycsb_si.exe` のままにする。mocc の [_require_condition_gate](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/orchestrator/campaign/s3_mocc_mutation_proof.py:126) は `driver_id` が mocc 固定だが、それ自体は非空文字の識別子であり owner 固定ではない。si 起動器で同じ手順を局所実装し、`driver_id` を si 起動器名にする。mocc の [_build_variant](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/orchestrator/campaign/s3_mocc_mutation_proof.py:166) は target/path が mocc 固定なので直接は呼ばない。

[同:277–288](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-si-v2/launch_si_run.py:277) の `NotImplementedError` を除き、build ごとに pin C checkout → v2 patch → 該当壊し patch → gate → build の順とする。dry run の [同:89–93](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-si-v2/launch_si_run.py:89) は各 patch を**未適用 pin C に個別照合する現形では 2 段目を正しく判定できない**ため、checkout に順次適用する照合へ直す。[同:215–237](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-si-v2/launch_si_run.py:215) で保存した stderr から、完走時だけ `^T2847_FIRED slug=si-first-updater-wins reached=([0-9]+) changed=([0-9]+) committed=([0-9]+)$` の 1 行を抽出して run JSON に入れる。timeout には診断欠落・verdict なしを記録し、部分 trace を verify しない。

## 7. 所有と分割

1. **V29 patch 所有:** `patches/broken-si-first-updater-wins.patch` とその説明を置く `patches/README.md`。v2 patch は既存のまま。まず機構と診断を確定し、`#if TRACE` 外および macro 未定義で pin C の挙動と一致する形にする。
2. **登録所有:** `orchestrator/campaign/condition_meaning_gate.py`、`orchestrator/campaign/screening_driver.py` と §5 の 4 test file。patch の実際の directive 数が確定してから登録する。verifier・parser・既存 driver の判定コードは所有しない。
3. **起動・実測所有:** repo 外の `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-si-v2/launch_si_run.py` と job 結果。登録後に J1 を実走する。
4. **結果所有:** si insight の事前登録・実測・分類。V28 は安全な変更範囲が決まるまで、実測済みの行として埋めない。

## 8. リスクと未確定

- V28 の status 除外だけでは inflight body の公開順、abort INSERT の削除、GC 再利用と read set ポインタの安全性を満たせない。**3 行すべてを現スコープで実走する計画は成立しない。**
- V29 の K で巡回が増えるかは schedule 依存であり、L0 の V36 K t4 の N を V29 の効果と取り違えられない。同 job の V2 対照と発火診断を併記する。
- v2 patch と V29 patch の厳密適用、条件 gate の si target での実効、V29 の動的診断値は、この read-only 段では未検証。テスト・build・benchmark は実施していない。

## 総括

V36 は L0 で現行 verifier に受理され、K t4 の巡回検出まで確認済みである。V29 は committed 後の first-updater-wins 分岐だけを外す 2 段 patch として実装・実走できる見込み。V28 は指定された最小変更が未完成 payload と失効しうる版参照を読ませるため、現行の規律を守る実走 patch としては起草できない。