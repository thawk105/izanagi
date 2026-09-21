# [T-2842] / [T-2843] 第 29 回 /rulings 項 4 (1 job 内の複数 pytest invocation) と項 9 (焦点走から漏れる exact 目録 test) の診断 — 計算ノード焦点 job の置換で満たせない単独走は延べ 11〜20、別 job 7 本の固定費は 1,208 秒 (うち 1 本が 1,066 秒)、runner 改修は設計仮説で本番 250〜450 行級、項 9 の 2 例は既裁定 [T-2820] が覆う (dev-wave 診断、2026-09-21)

台帳 ID: 項 4 = [T-2842] (D2206 項 4、[T-2832] (i) の実現手段の材料)、項 9 = [T-2843] (D2206 項 9)。軽量版 + 診断 wave の最小
(段 2 plan 1 本、段 3 相談 1 本、段 6 独立 read-only レビュー 1 本、実装面 0 行、変異免除 = DW-S04、受入全走は免除しない)。
段 6 の Codex 子は利用上限で出力 0 (不受理) だったので、段 6 は Claude の read-only 子 1 本で行った (§9)。
branch `worktree-dev-wave-r29-items4-9-diagnosis`、起点 local main `d99c556df`、開始 gate rc 0 = **2026-09-21T14:06:02+09:00** (`startup-gate.log`、標本の as-of)。
計測は起点 `d99c556df` の木で行い、記録前に local main `bea98c67d` へ `--ff-only` で揃えた (本 wave の commit 0 の時点、衝突 path 0)。
job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-r29-items4-9-diagnosis/` (brief・裁定・codex の prompt / 出力・計測 log の原本・親専用 script)。
逐語の写しは `verbatim/` (行末空白と末尾空行の可逆正規化は `verbatim/NORMALIZATION.md`、repo に入れない親専用 script 4 本は `verbatim/scripts.sha256`)。

## 0. 結論 (再提示の要点)

- **項 4 (a) 残件数:** 07:38 固定の 12 wave で、変更 test file は延べ 22、計算ノード焦点 log で単独走 (別 process) を確認できたのは 2、未確認 20。
  既存の計算ノード集合走 1 本を単独走 1 file に置き換える形 (追加 job 0) で覆えるのは構造上 **最大 9**。**置換で満たせない残件は延べ 11〜20** (各置換の可否は証明していないので上端寄り)。
  この上下限は計算ノード焦点 job を既存走とした値で、親の login 実走・author 実走は標本外 (含めると上限は増え、下限は下がりうる)。
- **項 4 (b) 最小改修範囲:** runner (`tools/run_tests.py`) に焦点走専用の複数 invocation 入力を足す案で、dispatcher の task 追加・DW-O26 の pin 変更は不要。
  費用の中身は parser ではなく **invocation ごとの env・rc・結果記録・途中失敗の扱い**。規模は設計仮説で本番 250〜450 行 + test 200〜400 行 (未検証の概算)。
- **改修なしの既存経路は 2 つ実在する:** (G) `dispatch_compute.py --task generic` の 1 job 内で runner を複数回起動できる (ただしその命令列は実装面で、Codex author の launcher が要る)。
  (L) login の bounded local で単独 file を dispatch せずに走らせられる — **D325 の理由欄「Pegasus では実行を伴う焦点走は必ず計算ノードへ dispatch」は現行コードでは成り立たない** (別 process 義務は残る)。
  ただし pegasus02 には他ユーザーの `/tmp/.git` が残り (§3.2)、login local の layout 系 test は偽赤になる既知型 (F457) がある。
- **項 4 (c) 同条件の効果 (1 試行):** t2797 の変更 test 7 file を既存 runner で「単独 1 file = 1 job」として直列に投げると、**wall 合計 1,336 秒のうち RUN は 128 秒、
  固定費 (投入前 + ノード開始前の待ち + collection) は 1,208 秒**。1 job に束ねる手段 (R2 / G) が消せるのは最大でこの固定費で、単独 process の起動・collection・test
  (pytest 合計 120.42 秒〜RUN 128 秒) はどの手段でも残る。**固定費の 88 % (1,066 秒、うち待ち 1,050 秒) は 1 本 (S07)** で、他の 6 本は 1 本 18〜26 秒 (wall で見ると S07 は 1,336 秒の 81 %)。
  束ねた job 自身の待ち・内側 RUN の変化・wave 完了時間への寄与は測っていない。
- **項 9:** 2 例 (受入赤 5 node) はすべて `orchestrator/tests/test_ccbench_spawn_sites.py` の node で、現行 DW-O26 の module 名探索では fix 前の tip で引けない。
  **既裁定・未実装の [T-2820] (D2194 項 8、DW-O26 inventory 群 4 → 6) が両 wave で発火し、同 file を集合に載せる。新しい択は不要。**
  しかも 1 例目 (T-2737) は D2194 項 8 の理由欄が挙げる entry 1695 (受入赤 3 件) そのもので、既裁定の根拠例だった。
  追加実行時間 (1 試行): 21 file の集合に [T-2820] の 2 file を足すと、同じ計算ノードで連続した対で RUN +13 秒 (pytest +11.58 秒、+78 passed / +2 skipped)。
  同 file 単独の RUN は 80 秒 (pytest 78.84 秒)。

## 1. 依頼と標本

依頼 (控え `verbatim/origin-rulings-full29.md`、D2206): 項 3 = [T-2832] (i) (D325 の字面 = 変更 test file の別 process 単独走に運用を戻す、実現手段は項 4 の結果で決める)、
項 4 = R2 は今回決めず AI が (a) 既存走の置換で満たせない残件数 (b) 最小改修の範囲 (c) 同条件での効果 を測って再提示 (相談 A 原文 `verbatim/rulings29-consult-a-out.md` 項 2)、
項 9 = (b) 2 例を既存探索で拾う局所策と追加実行時間だけ。新しい harness・一般化した目録基盤・仮想リスク向けの gate / 検査 / 台帳は作らない。

- (a) の標本は前回診断 (`output/insights/2026-09-21/focus-run-count-diagnosis/`) と同じ **12 wave (2026-09-21 07:38 JST 固定)**。再提示の対象がその数字だからで、現時点の「直近 12 wave」ではない。
  as-of (14:06:02) までに 07:38 以後に land した 12 wave (dwm08-selfrun-probe ほか、`verbatim/parent-notes.md` 8) は母集団から外した。
- (c) と項 9 の計測は as-of の後に本 wave が新しく投げた計算ノード job 10 本 (§4、14:35:24〜15:23:31 JST)。

## 2. 項 4 (a) 置換で満たせない残件数

D325 の決定は「既に回す走行のうち 1 本を単独走に」(追加 dispatch 原則 0 本)。現行 runner は 1 job = 1 pytest invocation なので、置換 1 本で覆えるのは単独 file 1 つ。
各 wave は DW-O26 の集合走を最低 1 本残す必要がある。本節の「既存走」は**計算ノード焦点 job** に限る (前回診断の抽出範囲)。したがって wave ごとに

- 置換の構造上の上限 = min(k − s, 集合走 job 数 − 1)
- 置換で満たせない残件の下限 = max(0, (k − s) − (集合走 job 数 − 1))、上限 = k − s

(k = 変更 test file 数、s = 計算ノード焦点 log で単独走を確認できた file 数、集合走 job 数 = 計算ノード焦点 job から既存の単独 job と held 診断 job を除いた数。
前回 `verbatim/focus_runs_table.md` と `changed_files.txt`。t2803 の単独 job 3 本 (focus-2 / 7 / 8)、t2344 の f4、t2810 の focus-held-1 は集合走から除く)。

| wave | k | s | 集合走 job | 置換上限 | 残件 下限〜上限 |
|---|---:|---:|---:|---:|---|
| t2804 | 3 | 0 | 2 | 1 | 2〜3 |
| t2803 | 1 | 1 | 4 | 0 | 0 |
| t2344 | 6 | 1 | 3 | 2 | 3〜5 |
| t2814 | 1 | 0 | 2 | 1 | 0〜1 |
| t2810 | 2 | 0 | 2 | 1 | 1〜2 |
| residue | 2 | 0 | 4 | 2 | 0〜2 |
| t2797 | 7 | 0 | 3 | 2 | 5〜7 |
| 変更 test なしの 5 wave (t2243 / abstract / story21 / walldecomp / t2817) | 0 | 0 | — | 0 | 0 |
| **計** | **22** | **2** | | **9** | **11〜20** |

- t2810 の focus-held-1 は held opt-in (`IZANAGI_RUN_GROWTH_HELD_TESTS`) の下で 2 file の `-k` 選択を走らせた診断 (9 passed、2 file のうち `test_s8b_binding_driftguards.py` は t2810 の変更 test ではない) で、
  DW-O26 の集合走ではなく、単独 1 file 走では兼ねられないので置換対象から外した (段 6 レビュー 所見 3。数えると上限 10・残件 10〜20 になる)。
- 上限 9 は「置き換える走の用途 (初回診断・fix 確認・契約追随) を単独走が兼ねられ、失う集合被覆を残る走が満たす」と**仮定した**ときの値で、
  各置換の可否 (tip・当時の file の有無・赤の入力関係) は証明していない (相談 所見 1〜3)。事後に緑だった走も、単独にしたら緑だった証拠ではない
  (D325「全走の緑はその file 単独の緑を含意しない」)。**事前には冗長と分からないので、運用上の残件は上端の 20 寄り**。
- 親の login 実走・author 実走は置換元にも s にも入れていない。標本内にも例がある (t2797 は各 fix 後に login で変更 test file を実走、同 wave の insight
  `output/insights/2026-09-20/t2797-b5-contrast/README.md` §4。別 process の単独走だったかは未確認)。これらを既存走に含めると上限は増え、下限は下がりうる (段 6 レビュー 所見 4)。
- 前回の「最大 +20 job」は置換 0 の上端。k が大きい wave (t2797 の 7、t2344 の 6) が残件の大半を占める。
- 置換で確実に使える形は D325 の想定どおり「fix が test file だけを変えた巡の再走をその file の単独走にする」(t2803 focus-8 型) で、これは事前に分かる。

## 3. 項 4 (b) 最小改修範囲と、改修なしの既存経路

### 3.1 runner 改修 (R2) の最小案 — 設計仮説 (段 2 plan §1、相談 所見 5・6、段 6 レビュー 所見 2)

現行: file 指定の非受入 `--force-dispatch` は 1 起動 → 1 job → 1 pytest invocation (`tools/run_tests.py:231` で flag を外し、`:2620` → `:2302` → `:1307` が 1 つの argv を tests task へ渡す)。
計算ノード側は `tools/pegasus/dispatch_compute.py:1880` で runner を 1 回起動する。runner は login 側 `_dispatch_environment` (`run_tests.py:1296–1299`) が付けた
`IZANAGI_TASK_RUN_AUTO_RECORD=0` (tests の allowlist `dispatch_compute.py:123–126` で転送) を受け、`run_tests.py:2682` で組んだ 1 つの pytest command を
`:2690–2694` の `subprocess.call` で実行する。空 argv の受入形だけは shard 経路 (`:267–297`、`:2309–2352`) を持つ。行番号は起点 `d99c556df` の値 (以後の main の差分は docs のみ)。

| 層 | 最小案 | 現行の該当箇所 |
|---|---|---|
| 入力 | 焦点走専用の複数 invocation 入力 (例: 要素 = argv と held 可否の 2 field だけ)。受入形・shard 指定・入れ子を混ぜない | `_consume_runner_options` `run_tests.py:231`、`_normalize_args` `:456`、`_is_acceptance_run` `:692` は変えない |
| dispatch | tests task を 1 回だけ呼ぶ。`TASKS["tests"]` (argv_policy=passthrough、`dispatch_compute.py:117–135`) は変えない | `_default_dispatch` `run_tests.py:1307` |
| 計算ノード実行 | 要素ごとに新しい runner subprocess を逐次起動 (同一 process 内の `pytest.main()` 反復は D325 の別 process を満たさない) | `run_tests.py:2682`、`:2690–2694` |
| env 分離 | 要素ごとに base env を複製し、held 要素だけ exact token を設定、隣へ持ち越さない (held env は tests の allowlist に既存 `dispatch_compute.py:130`)。複製で `AUTO_RECORD=0` の marker を保つ | `orchestrator/tests/conftest.py:1936–1948` の token 検査 (`_growth_holds_opted_in`) |
| rc | 個別 rc を全件保持し、赤の後も独立要素を走らせるか・infra 16 の優先・集約値を固定する (最後の rc だけ返すと途中赤を隠す) | — |
| 記録 | 要素ごとに argv identity・開始終了・rc・stats を返し、login 側で個別記録する。既存 `_RecordingSession` (1 観測、`:1024–1042`) と `_suite_identity` (1 argv / env、`:976–995`) を共用しない | `_dispatch_and_record` `:1570` は「親 wall と最終 rc を一度だけ」 |

- 規模 (未検証の概算): runner の既存 5〜7 関数と新規 3〜5 関数、本番 250〜450 行、test 200〜400 行。dispatcher 共通処理は原則 0 行。
  **未見積りの費用:** 要素の中断・timeout・未実行要素の表現 (相談 所見 6)。計算ノード側の自動記録との二重記録は、既存の marker (`AUTO_RECORD=0` の転送、
  `dispatch_compute.py:123–124` のコメント) が既に防いでおり、要るのは要素ごとの env 複製でこれを保つことだけ (段 6 レビュー 所見 2 (c))。
- 追随候補の test: `rg -l 'run_tests|dispatch_compute' orchestrator/tests --glob 'test*.py'` で 36 file (参照候補であって編集必須件数ではない)。
  設計上の優先 8 file = `test_run_tests_nproc.py` / `test_run_tests_preflight.py` / `test_run_tests_shards.py` / `test_run_tests_task_run.py` / `test_run_tests_testops_observation.py`、
  `test_pegasus_dispatch_compute.py`、`test_growth_test_holds_contract.py`、`test_t2337_dispatch_timeout_overrides.py`。
- docs pin: `tools/check_docs.py` に `run_tests` / `force-dispatch` の literal は無い。DW-O26 全文の pin (`check_docs.py:618–628`、`test_check_docs.py:178`、`:9534`、`:9549`) は、
  DW-O26 と task 集合を変えない R2 なら書き換え不要。
- 相談 A の「単なる flag 追加ではない」の中身 = 上表の env・rc・記録・途中失敗の 4 層。held の env 分離 (前回 K3、t2810 focus-held-1 の固定費 735 秒) も同じ機構で扱える。

### 3.2 改修なしの既存経路 (段 2 plan §2、相談 所見 8・9・12・14)

| 経路 | 実在 | できること | 制約・失うもの |
|---|---|---|---|
| **G** `dispatch_compute.py --task generic` | 実在 (argv_policy `generic-v1` は非空 string list を受理 `dispatch_compute.py:1566–1576`、D895 登録) | 1 job 内で runner を複数回起動 | env は clean (HOME / LANG / PATH / TZ / USER 等だけ保持、`:354–364`、`:1661`)。PATH 正規化は generic も通る (`:1128`、`:1851–1853`) ので D130 決定 (4) の写し漏れ型ではない。site は hostname で compute と判定 (`orchestrator/campaign/site_policy.py:30–46`)。receipt と NQSV footer は job 1 本分が残るが、invocation ごとの dispatch 証拠と login 親の記録形は失う。**複数回起動・計時・rc 集約の命令列は、inline の `bash -c` でも新しい実装 (harness) に当たる** (相談 所見 12) ので、運用手段に採るなら Codex author の launcher とそのレビューが要る (D2092 の先例)。guard の許可は live 未確認 |
| **L** login bounded local | 実在 (`run_tests.py:2496–2585`、`orchestrator/campaign/login_headroom.py:31–32` の既定上限 4 GiB / 下限 1 GiB) | dispatch 0 本で単独 file を別 process で走らせる | 余裕不足・観測失敗で queue 可なら dispatch へ退避、CAP_OOM 後は tree 指紋不変の時だけ dispatch 退避。通常の test 赤を dispatch で再試行する経路ではない。pegasus02 の `/tmp/.git` により layout の「repository 外」検査 (`_has_git_ancestor`) が `tmp_path` 配下で赤になる既知型 (F457) がある。本 wave 中の観測: `ls -ld /tmp/.git` = `drwxr-xr-x 2 makiart KASYS 6  9月  7 18:07 /tmp/.git` (15:2x JST、親)、段 6 レビューも 15:42:07 JST に同じ dir を再観測。本 wave では login 走を実測していない |

## 4. 項 4 (c) 同条件の効果 — 1 試行の実測 (`verbatim/measure/`)

**設計 (段 4 裁定 `verbatim/s4-ruling.md` plan v2 C):** 本 worktree (tip `d99c556df`) から既存 runner `python3 tools/run_tests.py --force-dispatch <files> -q -rf` を 10 本直列に投げた
(env は t2797 の焦点走 launcher と同じ `IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE=3600` / `IZANAGI_DISPATCH_OVERALL_GRACE_OVERRIDE=600`、nproc は既定、held は設定しない)。
集合 21 file は t2797 の launcher (`dev-wave-t2797-b5-contrast/focus/run-focus.sh`) の既定 argv で、件数は同 wave の焦点走と一致するが focus-3 と同一 argv とは主張しない
(同 log は argv を記録していない)。単独 7 file は t2797 の変更 test file (前回 `changed_files.txt`)。
段 3 相談 (所見 10〜13) を受け、generic 1 job に束ねた腕との対比較は行わなかった — inline の命令列も新 harness に当たり、また D289 決定 (2) の node の
block / randomization を満たさない 1 対では束ねの効果を識別できないため。4 区間の定義は前回診断と同じ (投入前 = launcher の start 行 → NQSV Created、
待ち = Created → Started、RUN = Started → Ended、collection = Ended → launcher の end 行)。計算ノード名は dispatch の `compute-visible.json` (`verbatim/measure/compute-visible/`)。

| job | request | node | 投入前 s | 待ち s | RUN s | collection s | wall s | pytest 集計 |
|---|---|---|---:|---:|---:|---:|---:|---|
| S01 集合 21 | 15194.nqsv | bnode024 | 2 | 1,064 | 151 | 14 | 1,231 | 2582 passed, 10 skipped in 149.02s |
| S02 単独 `test_b5_contrast_launch.py` | 15281.nqsv | bnode021 | 1 | 11 | 6 | 14 | 32 | 38 passed in 4.85s |
| S03 単独 `test_b5_generator_contrast.py` | 15284.nqsv | bnode021 | 1 | 9 | 6 | 11 | 27 | 108 passed in 5.21s |
| S04 単独 `test_b5_generator_contrast_report.py` | 15286.nqsv | bnode013 | 2 | 11 | 6 | 13 | 32 | 70 passed in 5.17s |
| S05 単独 `test_ccbench_spawn_sites.py` | 15289.nqsv | bnode013 | 2 | 8 | 80 | 15 | 105 | 72 passed, 2 skipped in 78.84s |
| S06 単独 `test_hooks.py` | 15297.nqsv | bnode013 | 1 | 7 | 9 | 10 | 27 | 483 passed, 1 skipped in 7.24s |
| S07 単独 `test_p3_s4_loop.py` | 15300.nqsv | bnode020 | 1 | 1,050 | 15 | 15 | 1,081 | 609 passed in 13.40s |
| S08 単独 `test_p3_s4_loop_job_contract.py` | 15312.nqsv | bnode020 | 1 | 11 | 6 | 14 | 32 | 185 passed in 5.71s |
| S09 集合 23 (21 + [T-2820] の 2 file) | 15313.nqsv | bnode020 | 1 | 8 | 137 | 14 | 160 | 2660 passed, 12 skipped in 135.09s |
| S10 集合 21 (再走) | 15314.nqsv | bnode020 | 1 | 20 | 124 | 15 | 160 | 2582 passed, 10 skipped in 123.51s |

10 本すべて rc 0 (赤 0)。chain 全体は 14:35:24 → 15:23:31 JST の 2,887 秒 (= 10 本の wall の和)。

- **単独 7 本 (S02〜S08):** wall 合計 1,336 秒 = RUN 128 秒 + 固定費 1,208 秒 (投入前 9 + 待ち 1,107 + collection 92)。pytest 秒の合計は 120.42 秒で、RUN との差 7.6 秒は
  job 単位の起動・probe import・結果の fsync 等。固定費は S07 の 1,066 秒 (待ち 1,050 秒) を除く 6 本で 142 秒 (1 本 18〜26 秒)。
- **束ねる手段 (R2 / G) が消せるのは最大でこの 1,208 秒**。どの手段でも残るのは単独 process の起動・collection・test で、pytest 合計 120.42 秒〜RUN 128 秒 (RUN との差の一部は束ねれば消える)。
  束ねた job 自身の待ち (集合 job の 1 回分に吸収されるはず) と、同じ node で続けて走らせたときの内側 RUN の変化は測っていない。
  変異走の先例 (D130 決定 (2)) では束ねの前後で内側の pytest 所要合計が 0.15 % しか変わらなかったが、焦点走への転移は主張しない。
- **待ちは二峰:** 10 本中 8 本が 7〜20 秒、2 本 (S01 1,064 秒 = 14:35:26 → 14:53:10、S07 1,050 秒 = 14:59:39 → 15:17:09) が 17 分半前後。
  前回診断では ≥ 300 秒の待ちが 27 本中 12 本 (337〜1,020 秒) あり、そのうち 17 分前後の 3 本 (1,007 / 1,020 / 1,020 秒) と本試行の 2 本は近い値にある (観察。原因は本 wave の資料から帰属できない)。
  混合比の推定・将来の待ちの予測はしない。
- **完了時間:** 同一 worktree の dispatch は直列 (DW-C00、orphan hold) なので、別 job で払う単独走の wall はその wave の待ち時間にそのまま足される。
  ただし親が並行して別の作業 (codex review 等) を進める場合の critical path への寄与は測っていない。

## 5. 項 9 — 2 例を既存の探索で拾う局所策と追加実行時間

- 受入赤: T-2737 `dev-wave-t2737-noninert-codex/acceptance-child-final-1.log` = 3 failed, 25276 passed, 69 skipped (`test_define_sink_cross_product_classifies_t2155_production_sinks_exactly`、
  `test_define_sink_cross_product_t2520_certify_entry_removal`、`test_patch_define_inventory_matches_condition_gate_registry`)。T-2797 `dev-wave-t2797-b5-contrast/acceptance-child-final-1.log` = 2 failed, 26725 passed, 69 skipped
  (`test_reviewed_ccbench_measurement_launches_use_bounded_sites`、`test_reviewed_process_launch_inventory_is_recursive_and_exact`)。**5 node すべて `orchestrator/tests/test_ccbench_spawn_sites.py`。**
- 現行 DW-O26 の consumer 探索 (変更 production の module 名で `orchestrator/tests/` を grep) は fix 前の tip で同 file を引けない:
  `git grep -n -e run_ss2pl_lock_study -e ss2pl-lock-protocol-study '134ea235c^' -- orchestrator/tests/test_ccbench_spawn_sites.py` と
  `git grep -n -e b5_generator_contrast -e b5_contrast_launch -e p3_s4_loop '517fd5451^' -- orchestrator/tests/test_ccbench_spawn_sites.py` はともに hit 0 (段 2 plan §5 (ii)。
  段 6 レビューは変更関数の symbol (`build_target` / `prepare_masstree_fetchcontent`、`default_runner`) でも hit 0 を確認)。
  同 file は名前参照でなく directory 列挙 (`rglob("*.py")`、`patches/*.patch` の glob、build source 列挙) で production を検査するため。
- **既裁定 [T-2820] は両 wave で発火する。** D2194 項 8 (2026-09-21、未実装) の決定は、DW-O26 の「production file を変えた wave は inventory test 4 群を参照関係に依らず焦点走に含める」の集合に
  `orchestrator/tests/test_ccbench_spawn_sites.py` と `test_check_subprocess_bytecode_guard.py` を足す (4 群 → 6 群) というもの。
  T-2737 は commit `0bd0895da` が `tools/pegasus/run_ss2pl_lock_study.py` と `patches/ss2pl-lock-protocol-study.patch` を変更、T-2797 は production 4 file を変更。
  同 file の赤は静的目録の exact 照合なので集合に載れば同じ tip で同じ赤を出すはずだが、本 wave は過去 tip の再走をしていない (「集合に載る」までを主張する)。
- **1 例目 (T-2737) は D2194 項 8 自身の根拠例だった。** 同項の理由欄は「entry 1695 (`test_ccbench_spawn_sites.py` の受入赤 3 件) で再発」と書き、entry 1695 は T-2737 の受入赤である
  (`docs/archive/worklog-phase3-0920-1695.md` の見出しと 1 項目)。第 29 回の材料 (索引 `rulings-all-20260921c/final-index.md`) には T-2820・D2194・1695 の hit が無く、既裁定の根拠例を
  別の択として出していた。**再提示は「新しい択は不要、既裁定 [T-2820] の実装で 2 例とも覆える」。** これは本 wave による新たな DW-O26 改訂ではない ([T-2843] の「DW-O26 の改訂はしない」と両立)。
- **追加実行時間 (§4 の表):** 同じ bnode020 で連続した S09 (集合 23 = 21 + 2 file) と S10 (集合 21) の差は **RUN +13 秒、pytest +11.58 秒** (+78 passed / +2 skipped)。
  順序は S09 → S10 の 1 通りだけで、順序効果は分離していない。S01 (集合 21、bnode024、chain の先頭) は RUN 151 秒で、S10 (bnode020、chain の末尾) との差 27 秒は
  node・時刻・順序が交絡した値で、どれにも帰属できない。いずれにせよ追加分 13 秒より大きい揺れがある。
  [T-2820] の 2 file のうち `test_ccbench_spawn_sites.py` だけの寄与は分離していない (`test_check_subprocess_bytecode_guard.py` は 6 test)。
  同 file の単独走は RUN 80 秒 (pytest 78.84 秒、bnode013)。21 file 規模の集合では追加分が単独の所要より小さく出た。集合が小さい wave (例: T-2737 の焦点走は 2 file) では
  同 file が所要の大部分を占めうる (推論、未測定)。
- 別の既存探索 (production を列挙する test を拾う運用) は 369 file 中 130 file を選ぶ (`grep -lE "\.rglob\(|\.glob\(|\.iterdir\(|os\.walk\(" orchestrator/tests/test_*.py`、
  所要台帳の直列合計 13,519 秒 = 全体の 74.8 %) ので局所策にならない。
- 所要台帳 (`orchestrator/tests/acceptance_duration_ledger.json`) の同 file = 47 entry / 直列 224.5 秒は、生成器が有効数字 2 桁に丸めた node 所要の和で
  (`tools/update_acceptance_duration_ledger.py:124–143`)、file 起動費・xdist 配置を含む wall 差ではないので追加実行時間の代わりに使わない。
  現行の同 file は 74 node (72 passed + 2 skipped、S05)。

## 6. 再提示 — [T-2832] (i) の実現手段の択一 (裁定パッケージ、実装しない)

いずれも D325 の字面 (変更 test file ごとの別 process 単独走を受入前に 1 度) を満たし、受理集合・DW-O26・規律 2 を変えない。費用欄の数値は §2 (12 wave 固定標本) と §4 (1 試行) の値。

| 択 | 改修 | 追加 job | 費用 (実測・資料) | 制約 |
|---|---|---|---|---|
| M1 置換 (D325 の本来形: 既存走 1 本を単独走 1 file に) | 0 | 0 | — | 覆えるのは計算ノード焦点 job の範囲で最大 9 / 20、事前に確実なのは「fix が test file だけを変えた巡の再走」だけ |
| M3 別 job (置換で覆えない分を 1 file = 1 job) | 0 | 残件分 (標本で 11〜20 / 12 wave) | t2797 型 7 本で wall 1,336 秒 (RUN 128 + 固定費 1,208)。短い待ちなら 1 本の固定費 18〜26 秒、長い待ちに当たった 1 本 (S07) は固定費 1,066 秒 (待ち 1,050 秒)。前回標本の ≥ 300 秒の待ちは 337〜1,020 秒 | 同一 worktree で直列、wave の待ちへそのまま足される |
| L login bounded local | 0 | 0 (余裕不足時は dispatch へ退避) | 未測定 (計算ノードの単独 RUN は 6〜80 秒) | pegasus02 の `/tmp/.git` が残る間は layout 系 test の login 結果を判定に使えない (F457) |
| G generic 1 job + launcher | runner 0、launcher は実装面 (Codex author + レビュー) | 0 (集合 job に同居) | 未測定 (内側で単独 process の所要は残る) | invocation ごとの dispatch 証拠と login 側記録を失う。repo 外の harness を常用する形になる |
| R2 runner 改修 | 本番 250〜450 + test 200〜400 行 (設計仮説) | 0 | 同上 | 実装 1 wave。held の env 分離 (K3) も同じ機構 |

**推奨:** [T-2832] (i) は **M1 + M3 で今すぐ運用に戻す** (改修 0、fix が test file だけを変えた巡は M1、残りは M3)。**R2 は今は実装しない (P3)。**
理由 = 本試行では単独 job 7 本中 6 本の固定費は 1 本 18〜26 秒で、固定費の 88 % (wall では 81 %) は長い待ちに当たった 1 本で決まった。長い待ちの頻度は
本試行で 10 本中 2 本 (17 分半前後)、前回標本で 27 本中 12 本が ≥ 300 秒 (うち 17 分前後は 3 本) と、定義と標本で大きく違い、混合比は推定していない。
したがって R2 の実装費用 (1 wave + 記録設計) を上回る節約も、見送りの費用が小さいことも示せておらず、**これは見積りの無い状態での判断である**。
改修 0 で (i) を今日から満たせる側を先に取り、R2 は実害が見えてから入れる、という順序の推奨である。L は F457 型の偽赤が残るので第一手段にしない。G は repo 外 launcher の常用になるので採らない。
蹴った帰結 = M3 の単独 job が長い待ちに当たるたびに、その分 (前回標本の ≥ 300 秒の待ちは 337〜1,020 秒、本試行は 1,050 秒) がその wave に足される (本試行では k = 7 の wave 相当で 1 回)。
R2 を再提示する目安: M3 の単独 job の待ちが ≥ 300 秒になった例が 2 wave 以上で出たとき、または held 診断 (K3) を同じ job に入れる需要が再発したとき
(いずれも各 wave の焦点走 log の NQSV footer で分かる。新しい台帳は作らない)。

## 7. 言わないこと

- (a) の上限 9 は置換の可否を証明した数ではない。各 wave の当事者の判断の当否は評価しない。改訂前の走に現行契約を遡及適用しない。login / author の実走は数えていない。
- (b) の行数は設計仮説で、実装してみた値ではない。
- (c) は 1 試行で、束ねた腕を走らせていない。待ちの二峰分布の混合比・将来の待ち・wave 完了時間 (critical path) の短縮は推定しない。
  17 分半前後の待ちの原因 (QUE / PRR / staging の内訳、scheduler の判断) は本 wave の資料から帰属できない。
- 項 9 の局所策が exact 目録 test 一般を覆うとは言わない (対象は既知 2 例だけ)。過去 tip での再現走はしていない。
- G / L の運用上の可否 (guard の live 許可、login 偽赤の頻度、login の所要) は本 wave で実測していない。

## 8. 段 2 plan・段 3 相談・段 4 裁定 (`verbatim/s2-plan.md`、`verbatim/s3-consult.md`、`verbatim/s4-ruling.md`)

- 段 2 plan (codex read-only、reasoning medium): (b) の層別最小案、G / L の実在、残件表 (証拠で確定する置換 0 → 残件 20)、項 9 の git grep を起草。
  「21 file の argv は資料から特定不能」は、親が t2797 の launcher 既定 argv (件数一致) で補った (`verbatim/parent-notes.md` 9)。
- 段 3 相談 (codex read-only、lane luna、reasoning medium、レンズ = 契約解釈・算術・同条件性 + 過剰・削除): **20 所見 (real must-fix 7、real should 5 (うち所見 7 は一部 refuted)、refuted 7、判定不能 1)。総括「現状のまま再提示は不可」。**
  must-fix = P2 が狭い、「残件 16〜20」は未証明、事後の緑 ≠ 単独でも緑、腕 S の cwd、腕 C / S は同条件にならない、inline `bash -c` も新 harness、21 対 22 (集合差と順序の限定)。
- 段 4 裁定: 全 real 所見を採用。腕 C と 2 本目の worktree を取りやめ、既存 runner だけの直列 10 job に縮めた。親の事後試算「残件 16〜20」は撤回し、§2 の構造上の上下限に置き換えた。
  集合差は 21 対 23 ([T-2820] 適用後の形) とし、集合 21 を前後 2 回走らせた。

## 9. 段 6 レビュー (`verbatim/s6-review-claude.md`)

段 6 の Codex review 子は起動直後に利用上限で終了した (出力 0、`f45_missing_output`、停止本文 `try again at Sep 26th, 2026 7:35 PM`)。D582 に従い自動再試行せずユーザーへ通知し、
先例 (entry 1800) と同じく独立 context の Claude 子 1 本 (general-purpose、model=opus、read-only) に同じ依頼 (`verbatim/prompt-s6-review.md`) を実施させた。

**判定 NO-GO、must-fix 1 / should 6 / nit 6 / refuted 3。** 派生値の検算表は §4 の 10 本・4 区間・wall・pytest・rc・node、単独 7 本の分解、比率、S09 − S10、§2 の k / s / 集合走、
§3 / §5 の件数・引用・正規化 (S*.log 10 本と s3-consult.md) がすべて一致し、不一致は引用 2 件 (plan 由来) と contract/ の未記録の正規化だけ。全 real 所見を採用して次のとおり訂正した (docs のみ)。

| 所見 | 判定 | 処置 |
|---|---|---|
| 1 fragment の工数行が段 6 を codex と書く | real must-fix | closed: fragment の工数行と本節を「codex review 子は利用上限で不受理、Claude 子が代行」に訂正 |
| 2 plan 由来の引用 (`conftest.py` の path、計算ノード側 `:1260`) と二重記録の費用 | real should | closed: `orchestrator/tests/conftest.py:1936–1948`、計算ノード側は `AUTO_RECORD=0` を受けて `:2690–2694` の `subprocess.call`、二重記録は既存 marker が防ぐと §3.1 を訂正 |
| 3 t2810 の held 診断 job を集合走に数えた | real should | closed: 置換対象から外し、上限 9・残件 11〜20 に改めた (§0・§2・§6・fragment・題名) |
| 4 上下限が計算ノード焦点 job に閉じていることの明示 | real should | closed: §0・§2・fragment に「login / author 実走は標本外、含めると上限増・下限減」を明記 |
| 5 T-2737 は D2194 項 8 自身の根拠例 (entry 1695) | real should | closed: §0・§5・fragment に追記 (親が entry 1695 の見出しと D2194 理由欄で裏取り) |
| 6 「88 %」の分母 | real should | closed: 「固定費の 88 % (1,066 秒、うち待ち 1,050 秒)、wall では 81 %」に訂正 |
| 7 長い待ちの帯の定義の混在、再提示の目安が未定義、見送りの根拠の強さ | real should | closed: ≥ 300 秒 (前回 12 / 27、337〜1,020 秒) と 17 分前後 (前回 3 本) を分け、目安を「≥ 300 秒が 2 wave 以上」と定義、「見積りの無い状態での判断」と明記 |
| 8 S01 − S10 の 27 秒をノード差と書いた | real nit | closed: node・時刻・順序が交絡した値と訂正 |
| 9 contract/ 7 file の末尾空行削除が未記録 | real nit | closed: `verbatim/NORMALIZATION.md` に追記 |
| 10 `/tmp/.git` 現存の根拠 | real nit | closed: `ls -ld` の出力と F457 を §3.2 に記載 |
| 11 D2194 項 8 の「」引用が逐語でない | real nit | closed: 引用符を外し、決定文の要旨として書き直した |
| 12 「どの手段でも残る分 = RUN 128 秒」 | real nit | closed: 「pytest 合計 120.42 秒〜RUN 128 秒」、「消せるのは最大この固定費」に訂正 |
| 13 fragment title に [T-2843] が無い、[T-2832] の状態文 | real nit | title は closed ([T-2843] を追加)。[T-2832] の状態文「実現手段の決定待ち ([T-2842] の計測後)」は計測後も偽にならず、再提示は [T-2842] の更新が運ぶので、base の競合を避けて触らない |
| 14 [T-2843] の完了条件、15 §4 の表・派生値、16 過剰なし | refuted | 維持 (§5 に「本 wave による DW-O26 改訂ではない」を 1 文追記) |

焦点再レビュー 1 本 (DW-O16、同じ Claude 子、`verbatim/s6-focus-claude.md`) を訂正後の README・fragment・正規化記録に掛けた: **GO、must-fix 0**。前段所見 1〜13 は
closed 11 (1〜8、10〜12) / partial 1 (9) / 13 は title closed + [T-2832] を触らない判断は妥当、regressed 0。訂正で足した派生値 (置換上限 9、残件 11〜20、t2810 の 2 / 1 / 1〜2、
wall 比 81 %、固定費比 88 %、120.42〜128 秒、前回の 12 / 27 と 3 本、contract/ の sha256・bytes 28 値、entry 1695 と D2194 項 8 の理由欄) と引用したコード行は原データと一致した。
新規の nit 4 件 (正規化記録の冒頭文、`dispatch_compute.py` の行番号 123–124、レビュー写しの曲線引用符、fragment の段 6 段落の長さ) と §9 の [T-2832] の理由の書き方を直した
(レビュー写しの 2 か所は親が転記時に直線引用符へ変えていたので原文の曲線引用符へ戻した)。

## 10. 検査 (記録 commit 前の実測)

本節を書き足す前の訂正後の tree で測った (本節の追加は散文のみ)。

- `python3 tools/check_docs.py`: 違反なし (rc 0)。`python3 tools/spool_fold.py --dry-run`: rc 0 (本 wave の fragment 2 本 = worklog 1 + failures 1 を畳む計画)。
- 三軸語走査 `python3 -m orchestrator.campaign.s8b_holdout_freeze search`: rc 1 だが holdout hit は既存の official 成果物
  (`output/env/pegasus/calibration/s8b-floor-official/20260916T111925Z-2c8cf9be/` の journal / manifest / result の 3 file) だけで、本 wave の file の hit は 0。
- `git diff --cached --check` rc 0 (行末空白・末尾空行は `verbatim/NORMALIZATION.md` の可逆正規化で解消)、NFC 違反 0 (46 file)。
- AI provenance: 初回の記録 commit `64b148b21` の後の全史監査は rc 0 (12,382 件、新規違反なし)。本訂正の commit も同じ手順 (`--message-file` → commit → 全史監査) で確かめる。
- 受入全走は記録 commit を含む最終 tip に land 前に 1 回投入し、受領証は job dir と land の記録が持つ。
