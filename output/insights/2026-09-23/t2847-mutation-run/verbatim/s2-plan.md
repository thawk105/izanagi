## 判定 (P1〜P5)

| 項目 | 判定 | 根拠と計画への反映 |
|---|---|---|
| P1 | **部分的** | SI の C 行は旧形式で E 行もなく、現 parser は 5 field の C を明示的に拒否する。したがって V28・V29 は現状 E である（`external/ccbench/cc/si/transaction.cc:539-553`、`orchestrator/verifier/parse.py:355-365`）。mocc の素の pin に X/P emitter がなく、巡回なしでは certified に届かない点も正しい（`patches/instr-mocc-lock-coverage.patch:20-40,65-116`、設計書 §2.3）。ただし **V25 の停止そのものは計装なしでも観測可能**。計装が必要なのは「完走した prefix が S」という期待の検証である。V34 も素の pin では S を期待できず I になる。両者を今回の scope から外す判断は妥当だが、「V25 は何も観測できない」は言い過ぎ。 |
| P2 | **real、ただし実装時の条件付き** | 既存の登録形は `DefineSpec(ROUTE_CMAKE_CXX_FLAGS, _SILO_OWNER, "ycsb_silo.exe", patch)` と条件枝の証人である（`orchestrator/campaign/condition_meaning_gate.py:201-215,273-297`）。14 patch をそれぞれ一つの裸マクロで囲み、未定義側を元コードそのものにすれば成立する。現時点では patch がないので inert は未実証。 |
| P3 | **部分的** | `_run_once` は指定 flag を渡せる（`orchestrator/campaign/s2_verify_calibration.py:149-163`）。ただし V24 は YCSB では対象の scan/insert に届かず、V21 の「最後」は時刻境界の schedule に依存する。V26・V27 は同一 key の再抽選により到達可能だが、有限の走での発生保証はない（`external/ccbench/include/ycsb.hh:55-74,102-143`）。各 job の stock 対照は新たに起動器へ足す必要がある。 |
| P4 | **real、差し込みが必要** | driver は `_verifier_run(tdir, commits)` の直後に trace を削除する（`orchestrator/campaign/s2_verify_calibration.py:329-334`）。起動器で `_verifier_run` の局所参照を包み、元の証人あり実行を保存した後、同じ `tdir` に対し `--expected-commits` を付けない verifier を追加実行すればよい。driver/verifier の判定は変更しない。 |
| P5 | **real、運用規則** | 設計書も期待を静的推定、schedule 依存と明記している（設計書 §4 冒頭、§4.6）。初回結果を保存し、source 上の実装誤りだけを直す。期待と違うという理由だけで条件を差し替えない。 |

## patch 設計 (14 本)

以下の位置はすべて pin `e9e477ca` の `external/ccbench/cc/silo/transaction.cc`。ファイル名は `patches/broken-silo-<slug>.patch` に統一し、対照だけ `patches/control-silo-<slug>.patch` とする。各 patch は **表のマクロ一つだけ**を新設し、`#if IZANAGI_BREAK_*` の `#else` に元の文を置く。未定義時に前処理後の実行コードが pin と一致することを patch ごとに確認する。V18 と V35 は同じ代入を別 patch で置換し、同時適用しない。

| V | slug / 裸マクロ | 変更位置と有効枝の内容 |
|---|---|---|
| 17 | `read-lock-check` / `IZANAGI_BREAK_READ_LOCK_CHECK` | `:465-473` の `check.lock && !searchWriteSet(...)` による abort だけを飛ばす。`:453-460` の版一致検査は残す。 |
| 18 | `no-write-tid-max` / `IZANAGI_BREAK_NO_WRITE_TID_MAX` | `:567` の `tid_a = std::max(max_wset_, max_rset_)` を `tid_a = max_rset_` にする。`:572-582` の worker/epoch 最大化は維持。 |
| 19 | `fixed-commit-version` / `IZANAGI_BREAK_FIXED_COMMIT_VERSION` | `:579-582` で `maxtid` の epoch/tid を非 genesis の固定値にし、既存の lock/latest 処理を保つ。C/W と tuple 公開は同じ `maxtid` を使う（`:602-616,660`）。同じ key の二度目の write で version dup を狙う。 |
| 20 | `published-version-mismatch` / `IZANAGI_BREAK_PUBLISHED_VERSION_MISMATCH` | `:660` の tuple への `storeRelease` に限り、C/W に出した `maxtid` と異なる未使用版を公開する。`:602-616` は変えない。次の取引の R（`:606-609`）だけがその版を読むため orphan を狙える。版の衝突がないことは実装と trace で要確認。 |
| 21 | `tail-commit-omission` / `IZANAGI_BREAK_TAIL_COMMIT_OMISSION` | `:706-709`、validation 成功後、`loadAcquire(quit_)` が真なら `writePhase()` を飛ばして true を返す。`quit_` は executor に渡され（`cc/silo/include/transaction.hh:52,68-69`）、runner が計測終了時に立てる（`common/runner.hh:294-299`）。**1 thread 限定**なら発火した取引の後に次の取引は始まらず、末尾欠落になる。ただし quit が取引間に立つと発火しない。一定件数ごとの省略は中間欠番を作るので、証人なし S という §4.2 の期待を保たず、代替にしない。 |
| 22 | `stale-read-payload` / `IZANAGI_BREAK_STALE_READ_PAYLOAD` | `:269-277` の二度目の TID を採用してループを抜けるが、`:263` で複写した payload は取り直さない。記録される R の版と payload の対応だけを壊す。 |
| 23 | `corrupt-write-payload` / `IZANAGI_BREAK_CORRUPT_WRITE_PAYLOAD` | `:658-659` の memcpy で書く payload の一部だけを改変する。`:602-616` の C/W、`:660` の版公開は元のまま。値は trace に出ない。 |
| 24 | `skip-node-validation` / `IZANAGI_BREAK_SKIP_NODE_VALIDATION` | `:477-485` の node map 検証だけを飛ばす。scan と insert の node 登録（`:298-302,733-740`）は残す。YCSB は read/update のみ（`external/ccbench/include/ycsb.hh:121-143`）なので、S の run は**機構未到達**と記録する。盲点の動的実証とは呼ばない。 |
| 26 | `stale-read-own-write` / `IZANAGI_BREAK_STALE_READ_OWN_WRITE` | `:216-219`、write set にある key の read で buffer `we->body_` の代わりに旧 tuple payload を返す。read set 優先の `:211-215` は変えないため、**blind write → read** が必要。 |
| 27 | `repeat-update-buffer` / `IZANAGI_BREAK_REPEAT_UPDATE_BUFFER` | `:529` の二度目の update 枝で既存 write buffer を誤った値で扱う。既存の一回目 `write_set_.emplace_back`（`:547`）と一取引一版の構造は保つ。元コードは二度目を飛ばすため、枝を有効時だけ展開する。 |
| 35 | `no-read-tid-max` / `IZANAGI_BREAK_NO_READ_TID_MAX` | `:567` を `tid_a = max_wset_` にする。V18 と逆方向で、read の最大値だけを外す。`:572-582` は維持。 |
| 31 | `double-abort-backoff` / `IZANAGI_BREAK_DOUBLE_ABORT_BACKOFF` | `:42-52` の `#if BACK_OFF` 内、`:47` の後に二度目の `Backoff::backoff(...)`。CC 判定を変えず待機だけ増やす。`STOCK_G` は `BACK_OFF=1`（`orchestrator/campaign/s2_verify_calibration.py:70-71`）。 |
| 32 | `reverse-write-order` / `IZANAGI_BREAK_REVERSE_WRITE_ORDER` | `:408` を `sort(..., [](const auto& a, const auto& b){ return b < a; })` にする。全 worker 共通の逆向き全順序で、要素数・pointer multiset と lock 手順（`:145-193`）は保つ。 |
| 33 | `conservative-abort` / `IZANAGI_BREAK_CONSERVATIVE_ABORT` | `:383-388`、lock 前に決定的な一部の入力（例: write set の要素数が偶数）だけ `status_=aborted; return false`。残る取引は既存の validation/commit を通す。全 abort による空 trace を避ける条件を事前に固定する。 |

V19 は **C/W と tuple の版を一緒に変える**。V20 は **tuple の公開版だけを変え、C/W は一致させる**。V23 は **payload だけ**を変える。この区別が層の帰属に必要である（`:602-616,658-660`）。

## 登録

各マクロについて `orchestrator/campaign/condition_meaning_gate.py:201-260` に `DefineSpec(ROUTE_CMAKE_CXX_FLAGS, _SILO_OWNER, "ycsb_silo.exe", "patches/<名>")`、`:273-350` に `("cc/silo/transaction.cc", "#if <マクロ>")` を追加する。複数 site に同じ `#if` を置く実装なら `:351-376` の site 数も正確に追加する。`#ifdef` を採る場合は期待の contrast が `None` となるので、今回は `#if` と未定義 contrast `0` に揃える（`:379-381`）。

固定表は `orchestrator/tests/test_condition_meaning_gate.py:36-62,73-92,3392-3433` のマクロ集合・枝期待・件数、`orchestrator/tests/test_p3_s4_loop.py:8360-8468` の `patches/<名>: frozenset({"<マクロ>"})`、`orchestrator/tests/test_ccbench_spawn_sites.py:645-735` の patch 由来 define 探索とその期待表を更新する。後者は glob から追加枝を独立発見するので、登録名との照合を残す。ほかの glob は `orchestrator/tests/test_mocc_template_proof.py:94-110` にあるが、silo patch に mocc marker を加えない限り期待表の追加は不要。既存の受理条件、供給判定、実行意味判定は変更しない。

## workload と期待表

共通の小構成を `tuple=200, zipf=0.9, extime=1` とし、表の `t` は thread 数、`r` は rratio、`m` は rmw、`o` は max_ope。`S/N/I` は設計書 §4 の符号。多 thread の N は schedule 依存であり、未発生時 S も事前登録する。

| V | 最小候補 `t/r/m/o` | 事前期待と層 |
|---|---|---|
| 17 | `4/50/false/5` | N・巡回。発生しなければ S |
| 18 | `4/0/false/5` | N・版順由来の巡回、または I・version dup。未発生なら S |
| 19 | `1/0/false/1` | I・同じ key の version dup。key の再選択が必要 |
| 20 | `1/50/false/5` | I・orphan。書き後に別取引の read が必要 |
| 21 | `1/50/false/10` | 発火すれば証人あり I・commit 件数不一致、同一 trace の証人なしは S になりうる。未発火は両方 S |
| 22 | `4/50/false/5` | S・値と版の不整合は盲点。別の依存異常が出れば N |
| 23 | `1/0/false/1` | S・payload の盲点 |
| 24 | `1/50/false/5` | S・**未到達対照**。YCSB だけで node 機構の盲点とは認定しない |
| 26 | `1/50/false/10` | S・read-your-writes の盲点。blind write → 同 key read を確認 |
| 27 | `1/0/false/10` | S・多重 update 値の盲点。同 key の二度目を確認 |
| 35 | `4/50/false/5` | S 見込み・読んだ版より小さい commit TID。別の異常との複合時は N/I も記録 |
| 31 | `4/50/true/5` | S・abort 発生を確認。待機のみ |
| 32 | `1/0/false/5` | S、X/P=0。異なる二 key 以上を確認 |
| 33 | `1/50/false/5` | S・非空 trace と abort 増加を確認 |

key は各操作で `zipf() % tuple_num` により再抽選される（`external/ccbench/include/ycsb.hh:55-74`）。従って 200 tuple、5/10 操作でも V26・V27 は**到達可能**であり、特に 10 操作・高 skew は同一 key を引きやすい。ただし V26 は read set が write set より先に検索される（`external/ccbench/cc/silo/transaction.cc:211-219`）ため、`rmw=true` の反復だけでは該当枝の発火証明にならない。V27 は元コードが二度目を飛ばす（`:529`）。両者とも発火のカウンタまたは独立の入力事実がなければ「未確認」とする。

各 job で同じ flag の **patch なし、TRACE=1 stock** を先に一度走らせ、S/certified、X/P=0、非空履歴を確認する。停止・crash・rc 非ゼロは `_run_once` が例外にする（`orchestrator/campaign/s2_verify_calibration.py:149-196`）。その場合は verdict を捏造せず、「run failure / verdict なし」と初回結果を保存し、後続 patch は job 単位の例外捕捉で続ける。

## 起動器

前回の repo 外 `launch_patch_verify.py` を写し、mode `s8a` と `mutations` を追加する。既存の依存物供給、compiler 解決、job dir、verifier 出力の受動保存は維持する（前回起動器 `:18-23,95-140,182-304`）。

`s8a` は `s8a_trigger_coverage.main()`（`orchestrator/campaign/s8a_trigger_coverage.py:334-420`）をそのまま呼ぶ。差し替える名前は `buildcache.DEFAULT_CC/DEFAULT_CXX`、`source_digest.resolve_evidence(cxx=...)`、`repo_output_root`、`ENV_TAG="pegasus"`、`CLK`（計算ノードで較正した値を明記）、verifier 保存用の `subprocess`。`_build` は buildcache を通らず `DEFAULT_CC/DEFAULT_CXX` を直接 CMake に渡すため、compiler 名の差し替えが効く（`:183-201`）。`PIN` は axis 定数由来（`:60-61`）なので現 pin との一致を preflight で確認する。既定の `_one_run` は三 run、二 build、checks を持つ（`:353-420`）。

`mutations` は起動器で `s2.PIN=pin.CURRENT_PIN`、`s2.buildcache.DEFAULT_CC/DEFAULT_CXX`、verifier 保存用 `s2.subprocess` を差し替え、stock trace build/run と `_broken_build_and_verify(patch_name, macro, workloads)` を呼ぶ。同関数が `applied()`、condition gate、`-DCMAKE_CXX_FLAGS=-D<macro>=1`、run、証人あり verifier を保つ（`orchestrator/campaign/s2_verify_calibration.py:295-339`）。V21 に限り `s2._verifier_run` を包み、元関数を呼んだ後、trace 削除前に証人なし CLI を追加実行して両結果を保存する。patchharness の `git apply`、gate の受理条件、verifier の判定は差し替えない。

## 投入と見積り

14 本を **3・3・3・3・2 本の 5 job** に分け、各 job に stock 1 build を置く。加えて s8a を 1 job。新規側は計 14 patch build＋5 stock build、s8a は 2 build、合計 **21 build / 6 job**。V21 と停止しうる条件は単独に近い組へ置き、失敗で他の結果を失わないよう patch ごとに結果を保存する。

前回は s3/s5 が 134〜140 秒、s2 の **2 patch×2 workload が 209 秒**だった（前回 insight §2.2）。今回は一 job 3 patch＋stock、原則各 1 秒 run なので **約 250〜420 秒/job**、2 本組は約 200〜320 秒、s8a は約 140〜240 秒と推測する。6 job 合計は概ね **0.4〜0.7 node 時間**。焦点走、変異 matrix、受入二回に **0.4〜0.7 node 時間**を見込み、総計 **約 0.8〜1.4 node 時間**。これは未実測の見積りであり、段 4 で build 単価を再計算し、2 node 時間以上なら brief の条件どおり投入前に確認する。性能値は取らない。

## 段 5 分割と変異候補

並列 author は、組 A が V17〜V21・V35 の **6 patch のみ**、組 B が V22〜V27・V31〜V33 の **8 patch のみ**を所有する。互いに同じ `transaction.cc` を元に patch を作るが、repo に置く成果物の patch ファイル名は重ならない。その後の author が `condition_meaning_gate.py`、上記三つの test、`patches/README.md`、repo 外起動器を所有する。macro 名と site 数は二組の成果を見て確定する。

実装面の変異 matrix で殺す候補は、① `DefineSpec` 登録漏れ、② branch witness 登録漏れ、③ patch と登録の macro 名不一致、④ `#if` site 数の虚偽、⑤未定義で pin と前処理不一致、⑥一 patch に二機構混入、⑦V18/V35 の代入方向取り違え、⑧V20 で C/W まで変えてしまう、⑨V21 の証人なし再検証前に trace を削除、⑩stock への裸マクロ混入。

## 未確認点

- V19 の固定版、V20 の代替公開版について、Tidword の bit layout と epoch 境界を踏まえた具体値を実装時に固定する。版衝突や genesis 化を別機構として混ぜない。
- V21 は `quit_` が取引実行中に立ったときだけ発火する。1 thread の trace と commit counter の差で発火を確認する。無発火なら「未発生」であり、件数間引きへ事後変更しない。
- V22・V26・V27・V35 の発火は trace の verdict だけでは十分に証明できない。source 上の条件と、必要なら限定した診断カウンタで実行経路を確認する。ただし診断を correctness 判定へ混ぜない。
- V24 の YCSB S は未到達を示す対照であり、範囲読みの phantom への検出力評価は別 workload が必要。
- 本回答は read-only の静的計画であり、patch 適用、build、実走、テストの結果は含まない。

## 総括

14 本は現 pin の silo `transaction.cc` に独立した out-of-tree patch として設計できる。**V21 は終了 flag による末尾省略を 1 thread で狙い、発火は schedule 依存**、**V24 は現行 YCSB では機構未到達**という二点を事前登録に明記する。s8a 1 job と変異 5 job を、既存の厳格な patch・condition gate・verifier 経路で実測する計画とする。