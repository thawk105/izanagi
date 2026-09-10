# [T-2273] 受入全走の最遅 shard の最大 worker 占有を分解し、その 59〜64% を占めていた 1 node を削った

wave: `dev-wave-t2273-accwall-maxocc` / branch `worktree-dev-wave-t2273-accwall-maxocc`
統合 commit: `fa733057de473d9dd440046821486f2d29828d4f`

## 1. 依頼の前提が実測で覆った

依頼と [T-2495] は「受入の現在の床は `test_t080_*` 群」と同定していた。D1894 はその上で
「着手前に、床が `test_t080_*` 群へ移ったことを実測で確かめる」を要求していた。

親が直近 9 走を repo 外の shard 成果物 (`/work/1/SFC/tanab/.izanagi-acceptance-shards/<run>/shard-N/`
の `junit.xml` と `report.json`) から測った結果は **否**である。

| run (先頭 10) | 時刻 | shard-0 wall | shard-1 wall | shard-2 wall | 最遅 |
|---|---|---|---|---|---|
| db1f8a4e51 | 09-09 22:55 | 388.51 | 132.43 | 365.94 | shard-0 |
| c5225d4e83 | 09-09 21:21 | 253.16 | 154.22 | **327.76** | shard-2 |
| 1ed124767f | 09-09 17:27 | 311.90 | 128.17 | **318.18** | shard-2 |
| 74311f5d5e | 09-09 16:47 | 321.00 | 130.56 | **325.17** | shard-2 |
| a90c6db7b4 | 09-09 14:22 | 257.14 | 140.25 | **314.71** | shard-2 |
| 1d756ac3ba | 09-09 14:05 | 253.97 | 194.85 | **315.18** | shard-2 |
| 5c8a9df078 | 09-09 14:00 | 265.46 | 161.53 | **313.29** | shard-2 |
| ff001f8cb3 | 09-09 13:49 | 290.67 | 137.66 | **315.15** | shard-2 |
| 9b1084d42d | 09-09 13:35 | 261.46 | 204.76 | **313.27** | shard-2 |

- 最遅 shard は 9 走中 8 走で **shard-2** である。
- **shard-2 の wall は 9 走すべてで 300 秒を超えた** (313.27〜365.94 秒)。
- t080 群を持つ shard-0 は 253.16〜388.51 秒で、9 走中 3 走だけが 300 秒超だった。
- t080 は shard-0 の最大 worker 占有の担い手ではあるが、**最遅 shard の床ではない。**

## 2. 最遅 shard の最大 worker 占有の分解

`report.json` の `worker_occupancy` より。

- shard-2 の最大 worker 占有は **gw0 の 256.93〜308.57 秒** で、wall の 78〜84% を占める。
  2 番目に忙しい worker は 94.6〜148.3 秒しかない。
- gw0 が背負う 49 item は xdist group `p3-b4-material-report` そのものである
  (`group_to_workers` は shard-2 でこの 1 群だけ)。
- group の内訳 (9 走目、合計 308.57 秒):
  - `test_normal_path_assembles_binds_evaluates_and_builds_document` = **198.48 秒 (64.3%)**
  - 次の 8 node = 10.76〜12.72 秒 (計 89.86 秒)
  - 残り 40 node = 計 20.23 秒
  - 同じ比は 21:21 走で 160.36 / 270.96 = 59.2%。9 走では 57.3〜64.3% に動く。
- その node が最初に触る module scope fixture `immutable_publication`
  (`orchestrator/tests/test_p3_b4_material_report.py`) の構築費用がここに載る。
- 構築の実体は `EXPECTED_BLOCK_COUNT = 201` に対する **replica 200 組の逐次生成**で、
  各 replica が bootstrap launch を通していた。段 2 の静的な数え上げでは
  Git subprocess 約 6,000 回、live projection の file read/hash 約 15,200 回、
  捨てられる 201-row bootstrap publication 400 個である。

`wall = 最大 worker 占有 + 残余` は D1830 が示すとおり**定義上の恒等式**であって独立な構造下限ではない。
本 wave が主張するのは「観測 9 走で shard-2 の wall が一度も 300 秒を切らなかった」までである。

## 3. 入れた変更 (test 側 2 file、production 差分ゼロ)

`orchestrator/tests/test_p3_b4_raw_record_producer.py` の
`_clone_arm_evidence_with_writers` に既定 `False` の `replay_non_commit_sidecar` を足し、
`orchestrator/tests/test_p3_b4_material_report.py` の `clone_abort_evidence` だけがこれを選ぶ。

replay 分岐は seed の launch-sidecar bytes を production の exclusive writer で target へ書き、
既存 WAL writer で attempt を replay する。`live_commit_receipt is None` かつ source が
non-COMMIT のときだけ選ばれ、崩れたら明示的に `AssertionError` で落ちる。
generic clone の既定経路と raw producer の正負 2 node は不変である。

### 採らなかった短縮

段 2 の plan は 9 項目を提案したが、段 3 の敵対相談 2 レンズと親の独立検証が一致して
**7 項目を不採用**にした。いずれも「速くするために検査を消す」形だったためである。

- **`_assert_replicas_match_real_except_identity` の除去** — 呼び手は全部で 3 箇所しかなく、
  raw producer 側の 2 本は `terminal="absent"` と `"commit"` を覆うが、
  material fixture が検査しているのは `abort` seed → `absent` clone + loop state 変異という
  どちらも作らない形である。「別 node が独立に検査済み」はこの shape については成立しない。
  さらにこの assert は**新設 replay 経路の唯一の exact oracle**であり、外すと sidecar の
  `launch_context_sha256` を別の有効な 64 hex へ書き換える変異が material 経路を通過する。
- **fixture 内の即時 assembly の除去**、**production helper の抽出と `_document` の inputs 再利用** —
  「同一入力だから後段だけ残す」は process 内状態を入力に含めておらず、
  「N 回目だけ壊れる」変異が消える。抽出は normal path の public 統合も弱める。
  不採用にした結果、**production コードの差分はゼロ**になった。
- **単位 B (t080 base の collection prewarm)** — §5 に理由を書く。

## 4. 効果

### paired 焦点走 (material module 単独、同一 command、計算ノード)

| 版 | 結果 | 総所要 |
|---|---|---|
| baseline (`git checkout --` で復元) | 49 passed | **241.06 秒** |
| candidate | 49 passed | **134.10 秒** |

差 **106.96 秒 (−44.4%)**。裁定の達成条件は「shard-2 の group を 65.94 秒以上縮める」
(9 走目基準: 308.57 + 57.37 = 365.94 を 300 未満へ) であり、焦点走の条件下では上回る。

別に、変更 2 file + consumer (`test_p3_b4_producer_auth_experiment.py`) +
golden (`test_real_repo_serialization.py`) の 4 file 焦点走は
**205 passed, 1 skipped, rc=0** (142.66 秒) で、同走の
`test_normal_path_...` の setup は **14.46 秒**だった。

### 主張の範囲

焦点走 2 本は host も選択 node 集合も違うため、D104 決定 4 が求める同一 allocation の
paired A-B / B-A には届かない。**言えるのは「同じ command で baseline より 106.96 秒短い走が得られた」
までで、恒常的な短縮量や因果の一般化は主張しない。** 受入全走の結果は §6 に記す。

## 5. 単位 B (t080 base の collection prewarm) を本 wave で実装しなかった理由

t080 の 11 consumer は 5 key に分かれ、process 内 memo (`_T080_E2E_BASE_CACHE`) は worker を
跨げないので 48-worker 形では 11 回 base を構築している。D1708 が唯一残した未検証の方向は
「collection 中の prewarm」だったが、段 3 レンズ B が次を示した。

- prewarm を `pytest_xdist_node_collection_finished` から起動しても、collection と重ねられるのは
  **最初と最後の worker の collection 完了時差だけ**で、約 51 秒の collection 全体ではない。
  はみ出しは dispatch (= 残余) へ載る。11 → 5 は work 回数の削減であって critical path の短縮ではない。
- t080 21 node の所要を**全部**消したという不可能に近い楽観条件でも、9 走目の shard-0 の床は
  `84.95 + (12439.6 − 3181)/48 = 277.84 + P` 秒である。目標には追加 dispatch tail
  `P < 22.16` 秒が必要で、これは未立証である。
- 段 3 レンズ A は、plan の cache identity が `(run ID, 5 key)` だけで実 repo bytes・HEAD・session・
  worker 環境変数を覆っていないこと、read lock が書かれていないことも挙げた。

D104 決定 3「効果を示せない機構は land しない」に従い、実装せず次タスクとして残した。

**訂正:** 親は段 1 で「t080 上位 10 node は同じ base を払っており、shard-0 の総仕事量の 25% である」
と書いたが、これは 2 点で誤りだった。(a) 上位 10 は 4 key にまたがり同一 base ではない。
(b) 25.3〜25.6% は t080 21 node の全所要比であって、除去できる base 構築費用ではない。
各 test の private copy (36MB / 2300 file の copytree) と本体は prewarm 後も残る。

## 6. 受入全走

**1 回目 (attempt 1) は走行に至らず拒否された。** `prerun-clean` rc=70。
原因は親自身で、受入投入中に本 insight と spool fragment を書いて untracked file を作った。
受入は投入前後の fingerprint 一致を要求するので、走行中に作業木へ書いてはならない。
非帰属の赤ではなく親起因である。同じ走で `claimed_main` が
`dd43fcb70d40685610f0d40b12ee098a75d10dbf` と出て、wave 開始時の `7f17e1c63` から
local main が進んでいたことも判明した。

**2 回目以降は 4 回走った。** 実走した 4 走 (attempt 2〜5) の shard 別 wall と
最大 worker 占有は次のとおり。値の源は各 shard の `junit.xml` root の `time` と
`report.json` の `worker_occupancy` である。receipt に wall 欄が無いことは D1830 の既知事実で、
本 wave もそれを変えていない。

| attempt | verdict | shard-0 wall | shard-1 wall | shard-2 wall | shard-2 の最大占有 | うち group `p3-b4-material-report` |
|---|---|---|---|---|---|---|
| 2 | 赤 (13 error) | 484.82 | 205.15 | **218.92** | 163.07 (gw2) | **146.54** (gw0) |
| 3 | 赤 (1 failed) | 367.11 | 161.76 | **277.80** | 222.01 (gw2) | **177.0** (gw0) |
| 4 | 赤 (4 failed) | — | — | — | — | — |
| 5 | **緑 (`22319 passed, 68 skipped`)** | 339.05 | 192.99 | **222.32** | 163.78 (gw2) | **153.3** (gw0) |

attempt 5 の receipt は `dev-wave-acceptance-receipt/v5`、`verdict = child-green`、
`tested_main = 960466384da56a92dd78ca8d10e50f0986496219`、
`tested_tip = 6451008c1e97c899a677fb0a59f90da4f4a4eb99`。

上の 4 走はいずれも**本節を含む記録 commit より前の tip** に対する走行である。
DW-O12 に従い、land 対象 tip への最終受入は記録 commit の完了後に別途投入する。
**その最終走の receipt が land の権威**であり、本節の数値は wall と占有の実測として読む。

**変更前後の対比 (変更前は 2026-09-09 の 9 走、変更後は実走 3 走):**

| 指標 | 変更前 | 変更後 |
|---|---|---|
| group `p3-b4-material-report` の worker 占有 | 256.93〜308.57 秒 | **146.54 / 177.0 / 153.3 秒** |
| shard-2 の wall | 313.27〜365.94 秒 (9 走とも 300 秒超) | **218.92 / 277.80 / 222.32 秒** |
| shard-2 の最大 worker が group か | 9 走すべて **はい** (wall の 78〜84%) | 3 走すべて **いいえ** |
| 対象 node の所要 | 198.48 秒 (9 走目) | **26.27 秒** (attempt 2) |

裁定の達成条件は「group を 65.94 秒以上縮める」だった。**実測の短縮は 131〜162 秒**である。
group は shard-2 の最大 worker 占有ではなくなった。

**最遅 shard は shard-0 へ移った。** 変更後 3 走の shard-0 は 484.82 / 367.11 / 339.05 秒で、
いずれも shard-2 より遅い。shard-0 は上位 worker がほぼ横並びの仕事量律速に近く、
単一 node の短縮では閉じない。**目標「最遅 shard を 5 分以内」はまだ達成していない。**
残っているのは shard-0 側であり、次の手番はそこを測り直すことである。

### 主張の範囲

- 言えるのは「観測した 3 走で shard-2 の wall が 300 秒を切り、group が最大 worker 占有では
  なくなった」までである。3 走はいずれも host が異なり選択 node 集合も 7442〜7457 と違う。
- D104 決定 4 が求める同一 allocation の paired A-B / B-A には、この受入全走は届かない。
  §4 の焦点 paired (241.06 → 134.10 秒) も host が違う。**因果はコード上の作業量削減
  (replica 200 組の bootstrap launch 除去) から論じ、受入の数値は到達事実として扱う。**

### 赤 3 走の帰属 (DW-O18)

attempt 2〜4 の赤はすべて**本 wave の差分から到達不能**で、単独再走で緑になった。

| attempt | 赤 node | 単独再走 |
|---|---|---|
| 2 | `test_t1259_qsub_env_delivery_probe.py` 13 error | 51 passed / rc=0 |
| 3 | `test_codex_worker_launch.py::test_manifest_is_appended_while_correlated_session_is_running` | 211 passed / rc=0 |
| 4 | 上記に加え `test_campaign_claim.py::test_two_real_processes_racing_acquire_have_exactly_one_winner`、`test_codex_worker_launch.py::test_sigterm_ignoring_child_is_killed`、`same::test_all_v3_stages_reject_prior_invalid_attempt[consult-sol]` | (3 と同型のため単独再走は 3 で代表) |

赤の node 集合が走ごとに移動し、単独では通る。この型は **F57** に既載であり、同 F は
「高負荷帯では赤の node が単独再走でも移動し、再走すれば緑が取れるという運用上の前提が
成り立たない」と記録している。attempt 5 で全件緑になったので hold 登録は行わなかった。
attempt 2 の 13 件は取り込んだ main の範囲にある別 wave の commit
(`f07761100` [T-2503] runtime PBS spool の束縛変更) が同じ領域を触っており、
`test_t1259_*` はその commit の対象である。

## 7. 変異 matrix

事前登録は段 4 で行った。段 3 と段 6 のレビューが SURVIVED と判定した 2 件は
DW-M01「赤理由が一つに絞れなければ登録せず実効 gate へ再照準する」に従い**走らせる前に撤回**した。

- **撤回 M2 (pair_id の `iteration` 固定)** — oracle は start/terminal receipt と consumption の
  pair_id を placeholder へ正規化し、replica 相互の pair_id を比較しない。production の
  batch 一意性も `(campaign_id, iteration, arm)` だけで pair_id を含まない。
- **撤回 M3 (`live_commit_receipt is None` guard の除去)** — material の唯一の replay 呼び出しが
  常に `None` なので単独削除は発火しない。この 2 つの guard は**現行 caller が踏まない
  fail-closed assertion** であり、保護として数えない。

走らせた 4 件はすべて baseline 緑 (rc=0) からの rc=1 で検出された。詳細は
`mutation-ledger.md`。

### harness の制約 (実測)

kill が **module / function scope fixture 由来の pytest ERROR** として出るため、
`tools/mutation_harness.py` は `FAILED ` 行しか解析せず、`rc≠0` かつ失敗 node 0 件を
`PARSE_ERROR` に分類する。oracle が fixture の中にある変更ではこの経路を避けられない。
検出そのものは rc と `errors=N` で確定しており、実装の欠陥ではない。

## 8. ユーザー裁定へ返す 2 点

1. **D1894 の対象名の読み替え。** D1894 は対象を「最大 worker 占有」と定め、前提として
   「床が `test_t080_*` 群へ移ったこと」の実測確認を要求した。実測は否だったので、
   親は決定本体 (最大 worker 占有) に従い、対象を**実測で最遅である shard の**最大 worker 占有と
   読み替えて実装した。この読み替えを追認してよいか。
2. **単位 B の扱い。** §5 の効果不成立の見積りを承知のうえで、t080 base の prewarm を
   別 wave として起票するか。起票する場合、先に測るべきは
   「重複検査除去による per-base 短縮量」と「prewarm の非重複 tail `P`」の分離である。
