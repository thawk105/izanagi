# [T-2710][T-2273] 受入 wall の律速 b5 群 (t080 e2e) の本体と固定費を反復・対比較で分解した — replica shard-0 の同一 tip 反復で、node 所要の約 9 割は共有 base の構築 (単独 98 秒 → 受入相当の 48 worker 下で 188〜257 秒) で本体 (verify) は 24 秒、pairing は replica で −52〜−69 秒の観測差 (事前登録の 3 対条件は未達で採用効果は未確立)、最長 node 除外は wall を動かさず、分割 / 縮約は固定 duration model で利得 ≤ 7 秒 / 0 (実 wall 効果は未測定)、固定費 67 秒は warm bytecode cache での collection で cold replica は 129 秒

一次資料 (wave `dev-wave-t2710-b5-wall-decomposition`、branch `worktree-dev-wave-t2710-b5-wall-decomposition`、計測 tip `779b3ea3c` = local main `24ede1d11` + 段 1〜4 の docs commit、2026-09-18)。段 1〜4 の逐語は同 dir の `s1-brief.md` / `s2-plan.md` / `s3-lensA.md` / `s3-lensB.md` / `s4-ruling.md`、probe の逐語と sha256 は `probe-source.md`、集計の原本は `probe-outputs/`。**受入証跡ではない** (受入受領証は段 9 の land が持つ)。

## 1. 依頼・不変条件・結論

依頼 (第 22 回 /rulings 項 3、ユーザー「推奨通りで」2026-09-18): 受入 wall の律速 b5 群 (t080 e2e、225〜500 秒) の本体と固定費を D357 の反復・対比較 (同一 tip・同一条件 3 走以上、中央値) で分解し、shard 内 pairing (上限 5.8%、T-2766) と e2e の分割 / parametrize 縮約の効果を実測で持つ。受理集合は変えず (D2068 / D2128)、保留検査は復帰させず、成分粒度は変えない (D2121)、8 条件の整備 wave は起こさない。実装はしない (実装面差分ゼロ)。

不変条件を守った: 受入 runner・conftest・test・allocator は 1 byte も変えていない。probe (pytest plugin + 計算ノード runner + 集計、Codex author) は観測 wrapper (実物へ委譲)・診断用の選択 (deselect)・並べ替えだけで、job dir に置き repo へは入れない。全走 rc=0 の走だけを採用した。失敗走は 2 件 (下の §3): 主要条件 (B) の 1 件は除外して同条件を 1 回だけ置換し、追加の warm 観測の 1 件は除外して置換しなかった。

結論 (数値は §3〜§8、判定規則は `s4-ruling.md` の事前登録どおり):

1. **b5 群の node 所要は「共有 base の構築 (固定部)」が支配し、「本体 (verify_receipt)」は小さい。** 単独走 (S1、`[ccbench-current]` 1 node) の call 125.7 秒 (中央値) = base 構築 98.3 + base→test の copytree 2.3 + verify 5 回 23.0 (1 回 4.5〜5.3) + その他 2.1。受入相当の replica (A、48 worker) では同じ node が 261〜287 秒で、増分はすべて base 構築 (builder なら build 232〜236 秒、待ち手なら flock 待ち 188〜257 秒) に入り、verify は 1 回 4.5〜5.3 秒で単独走と同じ。A の各走で他成分を固定して verify 約 24 秒だけを差し引くと約 238〜263 秒が残る (算術であり、verify 除去後の実測値ではない)。
2. **base 構築の内訳 (S 条件、別 key の比較による推定)**: 発行あり build (既定 key) 98〜102 秒に対し発行なし build (g7 の key、`issue_receipt=False`) は 42.3 秒 → 発行 (production の発行 subprocess) ≈ 60 秒、repo 実体化 (orchestrator 1,049 file + 可視 output 24,612 file の複製、submodule 追加、`git add -A` + commit) ≈ 42 秒。発行 subprocess 単体の直接計時ではない (発行なし分岐の後にも runtime source の配置等がある)。48 worker 下 (A) では発行なし build が 172〜198 秒 (S の約 4 倍)、発行あり build が 232〜236 秒で、両者の差は 40〜60 秒と S と同程度 → 伸びの大部分は実体化側に入ると推定 (実体化・発行の各寄与は未分離)。
3. **shard 固定費 (wall − 最大占有) は cold cache の replica で 128〜131 秒、受入の 93 session では 65〜103 (中央値 67.2)。** login で collect-only により test module の bytecode cache を温めた replica (補助観測、別 job の成功 2 走、cold/warm の同 job 交互比較ではない) は F 66.4 / 66.4 で歴史受入の F と近く、「fresh worktree の cold cache が cold replica の開始前費用の大部分を説明する」仮説を支持する。host・時期の差は分離しておらず、差全体が cache だけに由来すること、node 所要へ影響しないことは未確定 (§4)。受入の固定費 ≈ 60 秒は「warm cache での collection + worker 起動」で、現存 77 worktree はすべて warm (過去 session の起動時状態は未確認)。
4. **pairing (B、T-2766 の形) は replica で観測差 −52〜−69 秒**: 有効な同 job 対は 2 組 (短縮 52.0 / 65.1 秒、対差中央値 58.6 秒)、置換 B を含む条件別中央値差 69.0 秒 (16.6 %)。観測した 2 対の方向は一致し、B 全 3 走が A 全 3 走より短い (補足) が、**事前登録の 3 対条件は満たさず、採用効果は未確立**。相方 19.9〜20.0 秒が 0.0 になった (48 worker 全部で意図順が反映、3 個目の unit なし) ことは配布として確認済み。最長 node 自身も 30〜45 秒短かった (B では builder の担当が別 worker へ移った) が、その原因は未同定 (同時実行負荷の変化は説明仮説)。**実受入での効果は未確認**。
5. **最長 node の除外 (C) は wall を動かさない** (A−C = +2.7 / −7.1 / −3.7 秒、同 job 3 組): 同じ base を待つ次点 (`draft_finalize`、別 key) が同じ長さで最長に立つ。分割 (2+3 call) は固定 duration model で利得 6.3〜6.8 秒 (cold A 3 走。warm では 7.0)、3 param 縮約は 0 — 実装時の競合・配布変化による実 wall 効果は未測定 (D2121 と同じく「下限 model 不変」から「実 wall 効果ゼロ」は導かない)。分割は同一複製での正例→変異後再検証を失い、縮約は 3 欠陥型の stub-free 検出を失う (受理集合を縮める)。
6. 諮り直しの裁定パッケージ案は §9。推奨は「本体 (verify) 側の改善・分割・縮約は採らない案として残す (検出を失い、300 秒目標への改善も実証されていない)、pairing は実受入で同一 tip 反復 (A/B 各 3 走以上の逐次対比較) の効果確認を条件に採否を諮る、律速は共有 base 構築の 48 worker 下での 2 倍化 (主に実体化側と推定) にあり、D2068 の却下 3 案とは別の面 (構築の並行度・順序、実体化 / 発行 / 待ちの内訳) として次の調査対象にする」。

## 2. 実行条件と replica の忠実度

| 面 | 受入 shard-0 child (`tools/run_tests.py` 1470〜1530) | 本 wave の replica (A/B/C) |
|---|---|---|
| argv | `python3 -m pytest orchestrator/tests -n 48 --dist loadgroup --junitxml=<shard>/junit.xml -p tools.acceptance_shards -p no:cacheprovider` | 同じ + `-p t2710_probe_plugin` (末尾)、interpreter は `python3.10` (受入と同じ 3.10.12) |
| 選択 | env `IZANAGI_ACCEPTANCE_SHARD_PLUGIN_V1` + production `allocate` → shard-0 | 同じ (`create_session(repo, 3)` で session を作り、走後に job dir へ退避、corpus 集計から除外) |
| 並べ替え | conftest の台帳 cost 降順 + xdist の unit cardinality 安定 sort | 同じ。B だけ worker の `pytest_collection_finish(tryfirst)` で 49〜96 位を最小 cost の 48 unit に入れ替え (xdist の送信前) |
| env | `tests` task = login env 継承 + `PYTHONDONTWRITEBYTECODE=1` (`_job_run` 1853)、TMPDIR 無し → `/tmp` (node local xfs) | generic = clean env (`HOME PATH USER …`) + `PYTHONDONTWRITEBYTECODE=1`、TMPDIR 無し → `/tmp`。`PYTHONPATH` に probe dir |
| bytecode cache | 受入 worktree は親の login 焦点走で `orchestrator/tests/__pycache__` が warm (現存 77 worktree すべて) | fresh worktree で **cold** (compute では書かれない) → §4 |
| 同時 3 shard | shard-1/2 が別ノードで同時に走り lustre を共有 | shard-0 だけ 1 ノード |
| 観測 | production report.json (`worker_occupancy`) | 同じ report.json + probe の controller.json / spans (両者の最大占有は一致、`O_difference` 0.0) |

模擬 / 実の差: replica は「受入 shard-0 の値」ではなく「replica shard-0 の同一 tip 反復」。93 session との照合 (§3) で W・O・L は分布の内側、F は cold cache のため外側 (§4 で説明)。

## 3. 反復結果と 93 session との照合

計測 tip `779b3ea3c` (test tree は `24ede1d11` と同一)。計算ノード job は逐次 (D357)、job 内も逐次。

| job | request | node | 条件列 | 時刻 (JST) | 結果 |
|---|---|---|---|---|---|
| 1 | 5522.nqsv | bnode027 | S1,S,S1,S,S1,S | 11:41〜11:55 | 6/6 緑 |
| 2 | 5554.nqsv | bnode016 | A,B,C | 11:56〜12:16 | 3/3 緑 |
| 3 | 5601.nqsv | bnode021 | B,C,A | 12:17〜12:37 | 3/3 緑 |
| 4 | 5620.nqsv | bnode017 | C,A,B | 12:43〜13:07 | C,A 緑、**B は rc=16 で除外** (t1259 の `git ls-files --others` 30 秒 timeout ×22 = F945 型 + real-repo flock deadline の worker internal error。差分到達不能。同時刻 (12:48〜12:55 作成) に他 wave の受入 session 4 本が別ノードで並行しており lustre の共有負荷が疑われる = F945 と同型) |
| 5 | 5650.nqsv | bnode014 | B (置換 1 回) | 13:19〜13:25 | 1/1 緑 |
| 6 | 5663.nqsv | bnode014 | A,A,A (warm cache、補助観測) | 13:38〜13:56 | 2/3 緑、**3 走目は rc=1 で除外** (t1259 の setup error ×4 = F945 型、同時刻に他 wave の受入 4 session)。置換はしない (補助観測、n=2) |

shard 表 (W = JUnit testsuite time、O = worker の phase 合算の最大、F = W − O、L = 最長 node、P = O − L、D = 全 phase 合算):

| 条件 | 走 | W | O | F | L (node) | P | D | D/48 |
|---|---|---|---|---|---|---|---|---|
| A | job2 | 414.7 | 285.2 | 129.4 | 265.3 (ccbench-current) | 19.9 | 8904.5 | 185.5 |
| A | job3 | 410.7 | 281.4 | 129.3 | 261.5 (ccbench-current) | 20.0 | 8691.0 | 181.1 |
| A | job4 | 435.3 | 306.5 | 128.7 | 286.6 (ccbench-current) | 19.9 | 9730.5 | 202.7 |
| **A 中央値** | | **414.7** | **285.2** | **129.3** | **265.3** | **19.9** | | |
| B | job2 | 362.6 | 232.1 | 130.5 | 232.1 (ccbench-current) | 0.0 | 7740.5 | 161.3 |
| B | job3 | 345.6 | 217.1 | 128.5 | 217.1 (ccbench-current) | 0.0 | 7433.9 | 154.9 |
| B | job5 | 344.4 | 216.4 | 128.0 | 216.4 (ccbench-current) | 0.0 | | |
| **B 中央値** | | **345.6** | **217.1** | **128.5** | **217.1** | **0.0** | | |
| C | job2 | 412.0 | 283.8 | 128.2 | 263.4 (draft_finalize) | 20.4 | 8909.2 | 185.6 |
| C | job3 | 417.8 | 288.8 | 129.0 | 268.8 (draft_finalize) | 20.0 | | |
| C | job4 | 438.9 | 309.8 | 129.1 | 289.8 (draft_finalize) | 20.0 | | |
| **C 中央値** | | **417.8** | **288.8** | **129.0** | **268.8** | **20.0** | | |
| A (warm、補助) | job6-1 | 346.9 | 280.5 | 66.4 | 260.6 (ccbench-current) | 19.9 | 8532.7 | 177.8 |
| A (warm、補助) | job6-2 | 345.8 | 279.4 | 66.4 | 259.5 (ccbench-current) | 19.9 | 8419.4 | 175.4 |

93 session との照合 (記述的診断、`s4-ruling.md` の I / percentile): cold の A 3 走は W (310.8〜677.1)・O (243.8〜578.0)・L の範囲内 (W の percentile 75.3〜76.3 %、O 25.8〜61.3 %) だが **F は 3 走とも範囲外** (65.0〜103.3 に対し 129) で I = False。warm の A 2 走 (補助) は F 66.4 で範囲内、W 346〜347 は中央値 369.0 より短い側 (percentile 22.6 %)。同等性の合格判定ではない。

## 4. shard 層の分解 (固定費)

既存 session (母数 95 / 97 / 97、shard-0/1/2、`verbatim/sessions-fixed-cost-breakdown-since-0917-0900.md`) の session_timeline から: 固定費 (W − O) = 開始→collection 完了 (`collection_finished_epoch_s − T0` の中央値 59.4 / 60.3 / 60.0 秒) + 実行区間内の空白 (≈0) + 最後の test 終了→終了 (7.8 / 3.4 / 3.1 秒)。すなわち受入の固定費 ≈ 60 秒は **開始前 (worker 起動 / collection / receipt memo の prewarm、未分離)** で、終了後 (shutdown / JUnit 集約 / session cleanup、未分離) は 3〜8 秒。F はこれらと実行区間内の空白を含む残差であり一定の独立作業ではない。

replica (cold A、中央値) の固定費 129.4 秒 = 開始→最初の collection 受信 115.7 + そこから最初の test 開始まで 5.2 + 実行区間内の空白 0.0 + 最後の test →終了 8.7 + JUnit 境界補正 −0.2 (各走で閉じてから中央値。cold A/B/C 9 走なら 114.6 / 8.6)。受入 (59.4) との差 (+56 秒) の原因の仮説: fresh worktree に `orchestrator/tests/__pycache__` (pytest の assertion 書換 pyc) が無く、計算ノードは `PYTHONDONTWRITEBYTECODE=1` (`tools/pegasus/dispatch_compute.py` 1853) で書かないため、48 worker が毎走 1,000 module を compile する。受入 worktree は親の login 焦点走で warm になっている (現存 77 worktree すべて warm、F 中央値 68.1)。

対比較 (job 6、login で `python3 tools/run_tests.py --collect-only -q -p no:cacheprovider` (24,934 件、47.9 秒) により `orchestrator/tests/__pycache__` を 387 file で温めてから A を走らせた。補助観測、n=2): **F = 66.4 / 66.4** (開始→最初の test の中央値 58.3 秒、終了 8.3 秒)、cold の 129.4 / 129.3 / 128.7 に対し中央値差 −62.9 秒。W = 346.9 / 345.8、O = 280.5 / 279.4、L = 260.6 / 259.5 (cold 中央値 265.3 に近い)、P = 19.9 で、最長 node と相方は cold と近い (build 231.7、flock 230.1)。すなわち固定費に約 63 秒の差を観測し、node 所要は近い (別 job の 2 走であり、cache 以外の要因を分離した対照ではない)。受入の 93 session (すべて warm) の F 中央値 67.2 と一致し、replica の忠実度の差は cache の温度で説明できる。

## 5. M 11 node の分解 (単独走 S1 / S と replica A)

単独走 (job 1、bnode027、`/tmp` = node local xfs):

| 条件 | node | call | helper | get | flock 待ち | build | copytree | verify (回数、各) | その他 |
|---|---|---|---|---|---|---|---|---|---|
| S1 (中央値、3 走) | `[ccbench-current]` | 125.7 | 100.6 | 98.3 | 0.0 | 98.3 | 2.3 | 23.0 (5、各 4.5〜4.9) | 2.1 |
| S (中央値、3 走) | `[ccbench-current]` (待ち手) | 130.5 | 105.3 | 101.7 | 101.7 | 0.0 | 3.6 | 23.1 (5) | 2.1 |
| S (job1-02) | `draft_finalize` (distinct_basis_blob の builder) | 124.0 | 105.4 | 101.8 | 0.0 | 101.8 | 3.6 | 4 回 (うち 1 回 0.0) | 4.6 |
| S (job1-02) | `g7` (issue_receipt=False の builder) | 51.5 | 44.7 | 42.3 | 0.0 | 42.3 | 2.4 | 3 回 0.0 | 6.8 |
| S (job1-02) | 既定 key の待ち手 6 node (`[ccbench-current]` を含む) | 105.4〜130.5 | 105.3 | 101.7 | 101.7 | 0.0 | 3.5 | 0〜5 回 | ≤2.1 |

- base key は 5 種 (既定 7 node / distinct_basis_blob 1 / r_trailer=codex 1 / extra_r_path 1 / issue_receipt=False 1)。S では 5 base が並行に build され、既定 key の 7 node のうち builder 1 本が build、6 本が flock で待つ。
- 発行あり build ≈ 98〜102 秒 (S1 中央値 98.3)、発行なし (g7) 42.3 秒 → 差 56.0 秒から発行 subprocess の寄与を約 56〜60 秒と推定 (別 key の比較、直接計時ではない)。
- 本体まで到達する verify_receipt は 1 回 4.5〜5.3 秒で、単独・11 並行・48 並行のどれでも変わらない (早期拒否の call は 0.007〜0.033 秒。g7 の 3 回はすべて早期拒否)。

replica A (48 worker) の `[ccbench-current]`: call 265.3 / 261.5 / 286.6 = helper 239.4 / 236.0 / 261.1 (helper = get + copytree + 微小残差。get は build 235.5 / 232.1、job4 は待ち手で flock 257.2。copytree 3.8〜3.9) + verify 23.9 / 23.4 / 23.4 + その他 2.1 (各走の分解式。中央値の成分和は call 中央値と約 0.02 秒ずれる)。B では待ち手になり flock 202.2 / 187.8 / 186.9。**48 worker 下では base 構築 (build または flock 待ち) が単独の約 2 倍 (187〜257 秒)。** これが D2121 の「最長 node 225〜500 秒」の実体で、本体 (verify 24 秒) と copytree (4 秒) は約 1 割 (9.5〜10.5 %)。

## 6. pairing (B) の配布確認と対比較

- 意図順の反映: 3 走 (job2/3/5) とも 48 worker の受信 collection の sha256 が意図 (`b-intended-*.json`) と一致 (`collection_matches` 全 true)。最長 node (`[ccbench-current]`、cost 順 2 位) の worker の初期 2 個目は cost 0.0 の unit (`test_codex_reasoning_ab.py::test_forbidden_commits_are_unreachable_in_both_cases`) で、実行 0.0 秒、3 個目なし。A では 2 個目が cost 23.0 の unit (`test_replay_forwards_only_successful_snapshot_evidence_to_adjudication`、実行 19.9〜20.0 秒)。
- 事前登録の判定 (`s4-ruling.md`): 同 job の対比較は W_A − W_B = 52.0 (job2、12.5 %) / 65.1 (job3、15.9 %) の 2 組 (job4 の B は除外、置換 B は job5 単独で 344.4 = 全 A の最小 410.7 より 66 秒短い)。条件別中央値差 = 414.7 − 345.6 = 69.0 秒 (16.6 %)。有効な同 job 対は 2 組で対差の中央値は 58.6 秒。B の 3 走 (362.6 / 345.6 / 344.4) はすべて A の 3 走 (414.7 / 410.7 / 435.3) より短い (補足)。観測した 2 対の方向は一致したが、**事前登録の「同 job 3 対が 3/3 で正」の条件は満たさず、採用効果は未確立** (集計の判定欄も「採用効果は未確立」)。相方の短縮は 20 秒だが、最長 node 自身も 30〜44 秒短い (§5: B では既定 key の builder の担当が別 worker へ移った)。原因は未同定 — 「cost 2 位以下の重い unit が base 構築と同時に走らなくなった」は説明仮説。**実受入での効果は未確認** (replica、1 ノード、同時 3 shard 無し)。
- D357 の 10 % 規則は 1 走同士の差に適用する規則で、中央値差には適用しない。T-2766 を閉じるなら「効果ゼロ」ではなく見送りとして諮る。

## 7. 最長候補除外 (C) の診断結果

W_A − W_C = +2.7 / −7.1 / −3.7 秒 (同 job 3 組、中央値 −3.7、条件別中央値差 −3.2。差は丸め前の値から計算)。`[ccbench-current]` を除くと `draft_finalize` (別 key、自分が builder) が 263〜290 秒で最長に立ち、相方 20〜21 秒も残る。**最長 node を 1 本消しても wall は動かない** — 律速は特定 node でなく「48 worker 下の base 構築 ≈ 200〜260 秒」という共通の床にある。C は診断条件で上限ではない。

## 8. 分割・縮約の model と感度

同じ式 `W_X_model = max(L_X, D_X/48) + F_A` を A・分割・縮約に当てる (下限 model。相方・配布・待ちは含まない)。job2 A: A_model 394.7 (残差 W_A − A_model = 19.9 = 相方)、3 param 縮約 394.7 (利得 0.0)、`[ccbench-current]` を正例 2 call / 欠陥 3 call に分割 → d_positive 249.5 / d_defect 255.2 → L_split 258.5 (次点 `draft_finalize`) → 387.9 (利得 6.8)。job3 / job4 の分割利得は 6.8 / 6.3、warm job6 は 7.0 (`probe-outputs/analysis-*.md`)。

- 分割は各 node が base 取得 (≈235 秒) と copytree を払うので、verify を 2 と 3 に割っても node は 250 秒級のまま。加えて独立 2 node へ分けると同一複製での正例→変異後再検証 (T:1843〜1903 の連続検査) を失う = 受理集合を縮める (レンズ B M2、D2128 の理由と同型)。
- 縮約 (3 param 削除) は最長 node を残すので床は下がらず、node 秒は減るが CPU / I/O の実節約とは別で、別ノードの shard-1/2 への利益は未測定。失うものは 3 欠陥型の stub-free 検出。
- 観測 overhead: monotonic 取得 70 ns、dict 追記 220 ns、JSON 1 行 4.4 µs、M node あたり span ≤ 15、controller の report 記録 ≈ 12k 件 (in-memory) → H の proxy は 0.0 秒 (小数 1 桁)。間接の I/O 擾乱は上限を証明していないが、結論が反転する幅ではない。

## 9. 次の諮り直し用パッケージ (提案。採用済み判断ではない)

前提: 受入の最遅 shard の wall ≈ 最長 node (≈ base 構築 200〜260 秒 + verify 24 + copy 4) + 相方 20 + 固定費 60 (warm)。cold replica の B は 344〜363 秒で 300 秒未達。warm かつ同時 3 shard の実受入で pairing が 300 秒に届くかは未測定 (warm B は測っていない)。構築短縮案も、全 node・平均負荷・開始遅れ・他 shard を含む再評価の前には wall 値を提示しない。5 案は排他でなく「今回どこへ投資するか」の択一。

| 択 | 受理集合に触れるか | 効果 (実測値 / model 値) | 失う検出・残る不確実性 | 300 秒目標との関係 | 費用 | 今回求める裁定 | 復旧 |
|---|---|---|---|---|---|---|---|
| (a) pairing (T-2766): collection 順で 49〜96 位を最小 cost の unit にする | 触れない (集合・unit 境界・group・hold 不変、順序だけ) | replica で W −52 / −65 秒 (同 job 2 組、対差中央値 −58.6)、条件別中央値差 −69 秒。事前登録の 3 対条件は未達で採用効果は未確立。実受入は未確認 | 実受入 (同時 3 shard、warm) での再現、順序依存の test が無いことの検査 | 相方 20 秒の除去 (確認済み) + 最長 node の短縮 (原因未同定)。cold replica では 300 秒未達 (344〜363)、warm 実受入での到達可否は未測定 | 限定試作 (Codex author、conftest の並べ替え関数の後段 1 関数) + 変異登録 + 同一 tip の実受入 A/B 各 3 走以上の逐次対比較 + 順序依存検査。投入上限は起票時に固定 | 限定試作と対比較への投資判断。効果を示せなければ land せず終了 (D104 決定 3) | 並べ替えの撤去だけ |
| (b) `[ccbench-current]` の 2+3 分割 | **縮める** (同一複製での正例→変異後再検証を失う) | 固定 duration model で利得 6.3〜6.8 秒 (cold A、warm では 7.0)。実 wall 効果は未測定 | 連続検査の喪失、改善は未実証 | model 上は届かない | 分割設計 + 同値性確認 | 採らない案として残す | test の結合 |
| (c) parametrize 縮約 (3 param 削除) | **縮める** | 固定 duration model で利得 0 (床の node は残る)。実 wall 効果は未測定 | 3 欠陥型の stub-free 検出、改善は未実証 | model 上は届かない | — | 採らない案として残す (D2068 / D2128 と整合) | param の復帰 (削除期間の未検査は遡及しない) |
| (d) 何もしない | 触れない | — | 毎受入 6〜7 分の継続 | — | 0 | — | — |
| (e) 次の調査対象 (本 wave の新事実): base 構築の 48 worker 下での 2 倍化 (主に実体化側と推定) と cold cache の collection | 観測・設計段階では触れない | 単独 98 秒 vs 48 worker 188〜257 秒 (実測)、発行なし build 42 → 172〜198 秒 (実測、別 key 比較)、固定費 cold 129 vs warm 66.4 (補助観測 n=2) | 実体化 / 発行 / 待ちの各寄与は未分離。構築の並行度・順序 (5 key の base を先に build してから他 unit を流す、builder を固定する等) の効果は未測定 | wall 値は提示しない。算術例に限れば「全体の律速が 130 秒以下・相方と固定費が不変・先行構築の追加待ちなし」を仮定して 130 + 20 + 60 ≈ 210 だが、方式から導いた予測値ではない | 調査 wave 1 本 (実測のみ、replica)。1 wave 内で実体化・発行・待ちの内訳と構築順序の影響を報告し、証拠不足なら改善値を置かず終了 | 調査の起票可否 | — |

D2068 の却下 3 案 (output whitelist / alternates / 必要 blob の独立 index) と圧縮設定は再提示しない。verifier の検査省略・stub 化・hold 変更・古い判定の再利用は「本体高速化」の名で提示しない (レンズ B S3)。

## 10. 残存限界・未実測事項

- replica は 1 ノードで同時 3 shard を持たず、受入の lustre 共有負荷を再現しない。W・O・L は 93 session の分布内にあるが同等性の証明ではない。
- 実受入での pairing 効果は未確認。事前登録の 3 対条件は未達 (同 job 対 2 組)。B の最長 node 短縮 (−30〜−44 秒) の原因は未同定 (builder の担当移動は観測、同時実行負荷の変化は説明仮説)。
- warm A (job 6) は別 job の成功 2 走で cold/warm の同 job 交互比較ではない。cache 仮説を支持するが、差全体が cache に由来すること・node 所要への無影響は未確定。過去 session の起動時 cache 状態は未確認 (現存 77 worktree が warm という現況だけ)。
- 規律 2 の射程: 不変なのは production 受入の集合・hold・成分粒度。S1 / S / C の診断走は実行集合が限定される (C は `selected` 3938 に対し `executed_selected` 3937) ので、診断の緑を受入の緑と混同しない。wrapper の採用条件 = 元 callable へ同じ引数を 1 回渡し、返り値 identity と例外を保存する (`probe-source.md` の `install` / `Recorder`)。記録失敗 (`record-error`) の走は不採用 (本 wave では 0 件)。
- 発行 subprocess 60 秒の内訳 (production scan の件数依存) は未分解。base 構築の 2 倍化の内訳 (実体化 vs 発行) も 48 worker 下では未分解 (g7 の build 時刻からの推定のみ)。
- job 4 の B は F945 型 (t1259 の 30 秒 timeout ×22) + real-repo flock deadline で除外し job 5 で置換した。同時刻に他 wave の受入 session 4 本が別ノードで並行していた (lustre の共有負荷が疑われるが因果は未同定)。
- Latin square 3 job は位置効果の均衡化であり完全補正ではない。node は job ごとに違う (bnode027 / 016 / 021 / 017 / 014)。warm A は n=2 (3 走目は F945 型で除外、置換せず) の補助観測。

## 11. 再計算方法・成果物対応

- 段 6 レビュー (逐語は `verbatim/s6-reviewA2.md` / `s6-reviewB.md`、原文は `verbatim/originals.json`): A2 (数値の独立再計算) は §3 の 86 セル全部と対差・percentile・model・B の配布・除外理由を生データから再現し、must-fix 4 (pairing の判定名、§5 の copytree 二重計上、固定費 3 層の未閉と母数、O percentile) と should 5 を出した。B (解釈) は must-fix 5 (pairing 判定、成分倍率の断定、cache 因果、300 秒評価の cold/warm 混在と 210 秒 model、分割 / 縮約の「効果なし」) と should 4 を出した。いずれも本 README の文面で是正済み (数値の再計測は要らず、fix 子は起動していない)。A の 1 本目は除外走の report.json 不在で fail-closed 停止 (prompt の射影の誤り)。

- probe (Codex author、job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2710-b5-wall-decomposition/probe/`、repo へは入れない): `t2710_probe_plugin.py` (sha256 `a1b95dfcbc819513…`、19,683 byte)、`t2710_probe_runner.py` (`a49b61731b326885…`、25,326 byte)、`t2710_probe_analyze.py` (`622b38c2912ef221…`、27,183 byte)。逐語は `probe-source.md`。login selftest 45/45 PASS。
- 生成物: `runs/job<k>/<NN>-<cond>/{run.json, env-before.json, env-after.json, pytest.log, controller.json, spans-*.jsonl, junit.xml | acceptance-session/shard-0/{report.json, junit.xml}}`。集計: `analysis/<set>/analysis.{md,json}`。本 README の表は `analysis/job1` (S1/S)・`analysis/cold` (job 2〜5 の A/B/C)・`analysis/warm` (job 6) の `analysis.md` からの転記。`probe-outputs/analysis-{job1,cold,warm}.md` はその写し (1,200 byte を超える JSON 行だけ省略、原本は job dir)、`probe-outputs/runs-summary.md` は全走の run.json 要約、`microbench-job1.json` は overhead 単価。
- brief (`s1-brief.md`) の誤りは `s4-ruling.md` の訂正表が正本 (例外最長 node は `test_historical_oracle_nonadapter_reaches_current_semantics` で 92/93、verify 回数は 5/2/2/1、env 名は `IZANAGI_ACCEPTANCE_SHARD_PLUGIN_V1`、base key は 5 種、S1 も shared base 経路、A−S は regime 差、C は上限でない)。原文は書き換えていない。
- 93 session の表: `verbatim/` (`sessions-shard0-since-0917-0900.md`、`sessions-m11-and-shards-since-0917-0900.md`、`sessions-fixed-cost-breakdown-since-0917-0900.md`、親の inline 集計、定義は各 file 冒頭)。

## 逐語の行末空白の可逆正規化 (DW-S07)

codex 出力 6 本 (`s2-plan.md` / `s3-lensA.md` / `s3-lensB.md` と `verbatim/` の `s5-author.md` / `s6-reviewA2.md` / `s6-reviewB.md`) は `git diff --check` に触れる行末空白を除いてある。可視文字は不変。原文 bytes は `verbatim/originals.json` (sha256 `8d911422127901a031d710265136853625e4564d188746498632ced1fade0f33`、105,118 byte) に UTF-8 text として収め、各 text をそのまま書き出せば原文 bytes に戻る。

| file | 原文 bytes | 原文 sha256 | 行末空白を除いた行数 | 正規化後 bytes |
|---|---|---|---|---|
| `s2-plan.md` | 30810 | `fdf22bb43f86b746…` | 0 | 30810 |
| `s3-lensA.md` | 17257 | `44315bde2c407ce3…` | 4 | 17249 |
| `s3-lensB.md` | 16781 | `0e19f5a6f200bb64…` | 0 | 16781 |
| `verbatim/s5-author.md` | 2023 | `5f6e9a7e41f0310d…` | 0 | 2023 |
| `verbatim/s6-reviewA2.md` | 21394 | `78bc8b133b46429b…` | 2 | 21390 |
| `verbatim/s6-reviewB.md` | 15569 | `5540384b3d05f592…` | 0 | 15569 |

## 12. 総括

- 受入 wall の律速 b5 群 (t080 e2e) の node 所要は、単独走で 126 秒 (base 構築 98 + copytree 2 + verify 5 回 23 + その他 2)、受入相当の 48 worker 下で 260〜287 秒。増分はすべて共有 base の構築 (主に実体化側と推定、内訳は未分離) に入り、本体 (verify) は 1 回 4.5〜5.3 秒で不変。**「本体」を削る手 (分割・縮約) は固定 duration model で利得 ≤ 7 秒 / 0 で、受理集合を縮める** (実 wall 効果は未測定)。
- shard 固定費 67 秒 (受入) = 開始前 (warm bytecode cache での worker 起動 / collection / prewarm、未分離) ≈ 59 秒 + 終了後 8 秒。cold replica では 129 秒。warm の補助観測 (n=2) で 66.4 となり cache 仮説を支持する (因果の確定ではない)。
- pairing (T-2766 の形) は replica で観測差 −52〜−69 秒 (相方 20 秒の除去は確認済み、最長 node の 30〜45 秒短縮は原因未同定)。事前登録の 3 対条件は未達で採用効果は未確立、実受入での効果も未確認。採否は同一 tip の実受入 A/B 各 3 走以上の逐次対比較を条件に諮る。
- 最長 node を除いても wall は動かない (次点が同じ床)。律速は「48 worker 下で base 構築が 2 倍になること」であり、次の調査対象はその内訳 (実体化 / 発行 / 待ち、同時実行する重い unit の影響) と構築の並行度・順序である。D2068 の却下 3 案は再提示しない。
- 実装面差分ゼロ (probe は job dir)。受理集合・保留検査・成分粒度は不変。受入全走は段 9 の land 前に 1 回 (受領証は land が持つ)。
