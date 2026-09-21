# [T-2825] 段 4 裁定 (親、2026-09-21 08:4x〜08:53 JST (file mtime 08:53:39 = 追補 1 の書込み、推定時刻を 08:58 に mtime で訂正)、基準 `21641fee777d24642d54119b660a7b7880636e71`)

段 3 相談 1 本 (`codex/s3-consult-out.md`、高 3 / 中 3、修正後 GO) を裁定した。裁定 inbox の第 28 回 (08:20) に本件の項は無く、項 4
「受入門番 (leaders ≤ 1) の緩和 = (a) 据え置き」は依頼の門番と整合する。main は `21641fee7` のまま (08:47 時点)。

## 所見の裁定表

| # | 所見 | 裁定 | 反映 |
|---|---|---|---|
| 1 | P3「開始 t を観測」は過大 (report.json は worker 単位の first/last と occupancy の和だけ、JUnit は time と pairing property) | real・採用 | 開始 t は「推定 (同 worker の junit 並び順での先行 time の累積)」と明記、ΔL の読み方を事前登録 (§事前登録 5) |
| 2 | 入力の collection 一致と最新性が未証明 | real・採用、**段 4 前に親が実測で閉じた** | §入力の確定 |
| 3 | 有効走・無効対・停止の規則を参照だけに任せている | real・採用 | §事前登録 1〜3 に全列挙、launcher・系列・集計器で強制 |
| 4 | 「selected 不変」は shard 別まで不変と読める | real・採用 | 不変条件を「全 shard の受理多重集合と group / unit 境界」に限定、shard 別 selected の差を必須出力 |
| 5 | bytecode 条件の対称化が未登録 | real・採用 | 系列開始前に両 tree で計算ノード collect-only 1 走 (T-2802 形) |
| 6 | land 再生成 bytes と測定 B の照合が無い | real・採用 | §land の照合 |
| P5 | 「変異 matrix 適用外は妥当」 | **refuted** | D95 決定 2 は実装面を所在で判定し、`orchestrator/` 配下の JSON は実装面。DW-S04 は実装面差分ゼロの wave だけを免除する。§変異 matrix で 3 本登録 |

(P1) 維持 — 台帳 path は conftest (`_ACCEPTANCE_DURATION_LEDGER_PATH`) と割付器の双方で固定、env 切替は無い。固定 2 tree (D2177) を依頼の
「同一 tip」に最も近い形として採る。理由は「path 固定で同一 SHA の A/B を作る経路が scope 内に無い (env 切替の追加は scope 外)」であり、
「runner が dirty を拒否するから」ではない (相談 P1 の限定を採る)。(P2) 修正 — W_0 主指標は維持、W_max / argmax と全 W_j を併記、W_0 の
改善だけで受入全体の短縮と書かない。(P3) 修正 — 所見 1。(P4) 維持。(P5) 修正 — 軽量版 (段 2 省略、段 6 review 1 本) は維持、変異は登録する。

## 入力の確定 (所見 2、親の実測)

- 選定締切 08:47:26 JST。締切時点の受入 session のうち新しい順: `20f4f4af…` (08:44、waiter-collect-latency、shard-1 failures 1 → 緑でない)、
  `f233cd43…` (08:36、shard-2 junit 無し → 未完走)、**`9d955ce2…` (08:20、3 shard 緑、26,808 件) = 最新の適格走**。
- main collection 照合: wave 木 (HEAD = main `21641fee7`) の `python3 -m pytest orchestrator/tests --collect-only -q -p no:cacheprovider`
  (26,808 件、`main-collect-21641fee7.txt`) と入力 session の `login-collection.log` の nodeid 多重集合が完全一致 (重複 0・差 0)、
  `IZANAGI_` marker 行 (hold 情報) 53 行の多重集合も一致。
- 入力の固定: `input/SHA256SUMS` (shard-0 `ce344136…`、shard-1 `1c75c851…`、shard-2 `f11588e4…`、login-collection `319e1307…`)。
  性能値による選び直しは禁止。T-2724 8 node の入力値 (生 time / worker / rank / 新台帳値) は `input/t2724-nodes-input.json`。
  入力走では active_v2 系 3 node が 189.2 / 191.5 / 192.0 秒 (gw33 / gw47 / gw40)、他 4 node が 38.5〜47.9 秒、shared_base 0.004 秒。
  **この 1 走の値 (190 秒群と 40 秒群) が B の順位を決めること、builder / waiter の役割を所要だけで断定しないことを限界に書く。**

## plan v2

### 単位 L — 台帳の再生成 (Codex author、workspace-write)

- worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2825-ledger` (branch `author-t2825-ledger`、`21641fee7` から)。所有 path は
  `orchestrator/tests/acceptance_duration_ledger.json` の 1 file だけ。
- 実行: `python3 tools/update_acceptance_duration_ledger.py --refresh <job dir の input/shard-{0,1,2}/junit.xml>` (出力は既定 = 所有 file)。
- 検算 (子が実行し、出力を worktree 内 `t2825-author-l/` に書く。親が退避): stdout の件数、凍結 prefix 426 entry の値一致と該当行 bytes 一致、
  `@real-repo` 0.19、T-2724 8 node の値、`nodeid_count == len`、`--coverage-against <main-collect の nodeid 行だけ>` の被覆、
  同じ入力で 2 回目の `--refresh --check` が一致 (決定性)、所有 file 以外の変更 0 (`git status --porcelain`)、removed 140 件の名前一覧が
  main collection に 0 件であること。pytest は走らせない (login 不可、親が dispatch で走らせる)。

### 単位 P — 測定 probe (Codex author、workspace-write、repo へ入れない)

- worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2825-probe` (branch `author-t2825-probe`、`21641fee7` から)。所有 path は
  `t2825-probe/` 配下の 5 file: `run-measure.sh`、`run-series.sh`、`run-warm.sh`、`gate.conf`、`t2825_ab_analyze.py`。親が job dir へ複製して走らせ、
  repo には `.md` の逐語だけを残す。
- 下敷き: T-2802 `probe-source.md` の `run-measure.sh` / `run-series.sh` / `run-warm.sh` / `t2802_ab_analyze.py` (固定 2 tree、flock 直列、12 走上限、
  有効 3 対の固定終了、HEAD / clean 照合、成果物の sha 複製)、T-2766 `t2766_ab_analyze.py` の worker 別 item 列、T-2817 `read_shards_v2` の量の定義。
- 差分: (a) 門番 = 他 session の受入 leader ≤ 1 ∧ load1 ≤ 60。leader は argv 先頭一致
  (`ps -eo args | grep -E '^(python3|[^ ]*/python3?) [^ ]*dev_wave_wait\.py acceptance' | grep -vc <slug>`)。条件値は `gate.conf` を毎周回 source。
  周期 100〜140 秒乱数、2 回連続で開いたら 0〜45 秒乱数後に再判定、RUN dir 作成直前にもう一度判定。(b) 各走で session の `login-collection.log` も
  sha 付きで複製。(c) 一次指標は W_0 (§事前登録)。(d) 集計器は §出力の全項目を JSON + Markdown で出し `--selftest` を持つ。

### 測定手順 (親)

1. B commit (台帳 1 file、Codex author trailer) を wave 木に作る。B = その SHA、A = `21641fee7` (`.codex/worktrees/t2825-base-a`、clean、lock 済み)。
   `measurement-tips.json` に固定。`git diff --stat A B` = 台帳 1 file だけを確認。
2. warm: 両 tree で計算ノード collect-only 1 走 (`run-warm.sh`、`PYTHONDONTWRITEBYTECODE=` 空で export、HEAD / clean 前後一致、pyc 数を記録)。
3. 系列: 対 1 = A,B / 対 2 = B,A / 対 3 = A,B。launcher は job dir の flock で直列。測定中は自分の他 job を投げない (D357)。
4. 集計器で対表・判定。記録 commit は測定後。

## 事前登録 (結果を見る前に固定、2026-09-21 08:53:39 JST 以前 = s4-ruling.md の mtime、測定・変異の開始前)

1. **有効走:** 子 rc = 0、3 shard の junit / report.json / login-collection.log の複製と sha 一致、3 shard 完走で failures = errors = 0、
   投入前後の HEAD = 条件の SHA かつ clean (`--untracked-files=all --ignore-submodules=none`、`output/pegasus-dispatch/` を除く)、
   投入時の門番条件 (leader ≤ 1 ∧ load1 ≤ 60) を満たした記録、全体 collection (3 shard の testcase nodeid 多重集合と login collection) が
   入力走と一致、3 shard の skipped 集合が A / B で一致。
2. **無効対と停止:** 対内のどちらかが無効なら対全体を同順序で取り直す (slot を消費しない)。有効 3 対で固定終了 (早期停止も追加もしない)。
   測定投入の上限 12 (未投入の abort は数えない、投入後の無効走は数える)。12 に達して有効 3 対未満 → 「判定不能 (反復不足)」。
3. **赤:** 全件の本文と条件別件数を残し、親が本文で infra / impl / unclassified に分類する。infra (例: memo publication timeout、F945 型で本文が
   合致するもの) は走の無効化だけ。impl / unclassified は系列を停止し、DW-O18 で原因を切り分ける (台帳だけの差で B 固有に再現する赤は impl)。
4. **指標:** shard j の W_j (junit testsuite time)、O_j (report `worker_occupancy` の duration 最大、所要の和であって実時間ではない)、
   L_j (最長 testcase の time) とその nodeid・worker、`O_j − L_j`、F_j = W_j − O_j、`pre` (`session_timeline.collection_finished_epoch_s` − junit timestamp)、
   `post` (timestamp + W − 最後の test 終了)。一次は W_0。対 k の ΔW_k = W_0(A_k) − W_0(B_k) (正 = B が短い)、r_k = ΔW_k / W_0(A_k)、
   |r_k| < 10 % の対は D357 注記「1 走比較として変化なし」。集計は med ΔW、med r、条件別中央値差 med W_0(A) − med W_0(B) の 3 つを別量で併記。
5. **判定 (有効 3 対が揃った場合のみ、W_0 について):** (i) 全対 ΔW > 0 かつ med r ≥ 10 % → 方向一致・閾値以上。(ii) 全対 ΔW > 0 かつ
   med r < 10 % → 方向一致・閾値未満。(iii) それ以外 → 効果未確立 (副分類: 符号混在 / 0 を含む / 全対 ΔW < 0 = 退行の観測)。10 % は保守基準で
   D357 からの導出ではなく、3/3 一致を有意差と書かない。**L の読み:** 各対で ΔL = L(B) − L(A) と L の nodeid の交代を記録し、固定した旧 L 候補
   (`test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[...]`) の所要も両条件で併記する。全対 ΔL > 0 かつ med(ΔL / L(A)) ≥ 10 % なら
   「L の伸長を観測」と書く。ΔL > 0 と `O_max − L` の減少が同じ対で起きたら「L 増大を伴う差の縮小」と記述し、改善の判断は `O_max − L` 単独で
   行わず W_0 の正味差 (上の判定) で行う。copy 配置・builder / waiter の因果は計器が無いので主張しない。
6. **W_max:** 同じ規則を W_max に当てた結果を「補助」として併記し、argmax shard が 0 でない走を明記する。W_0 が (i) でも W_max が (i) でなければ
   「shard-0 の短縮であって受入全体の短縮とは言わない」。
7. **参考値:** model 差 19.5 秒 (T-2817 §5 (a)、未収載 333 node 全部更新の固定所要 model) と観測 `O_max − L` 中央値 62.7 秒 (21 session) /
   Job B 65.0 秒は別欄に置き、閾値・上下限・期待値に使わない。
8. **必須出力 (走ごと・条件ごと):** 全 W_j / O_j / L_j / F_j / pre / post、W_max と argmax、shard-0 の最大占有 worker の item 列 (nodeid、pairing rank、
   partner、time、junit 並び順、推定開始 = 同 worker の先行 time 累積)、L の worker と相方、T-2724 8 node の (shard、worker、rank、time、推定開始)、
   shard 別 selected の件数と sha256、A / B 間の shard 間移動 node (件数・time 和)、台帳予測負荷 (shard 別、走った node の台帳値和、未登録 1.0)、
   門番値・node・投入 / 完了時刻・job ID。
9. **land の照合:** land 時に main の台帳が `21641fee7` から進んでいたら、main 現物を base に同じ入力で `--refresh` を再走し (Codex author)、
   bytes を測定 B と照合する。一致しなければ差分を insight に記録し、測定結果の主張を測定 B の台帳に限定する。落ちた node は名前と件数を記録。

## 変異 matrix (DW-M01、実装前に登録)

実装面差分 = 台帳 1 file (D95 決定 2)。守るのは「refresh 後も既存 test が凍結 pin と被覆を束縛する」こと (規律 2 の pin を緩めない)。
変異は新台帳 (B commit) に対して独立 clone で当て、runner は
`python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_update_acceptance_duration_ledger.py orchestrator/tests/test_acceptance_schedule_order.py -q -rf`。

| ID | 位置 | 変異 | 期待 (赤になる node) | 単一理由の根拠 |
|---|---|---|---|---|
| M1 | 凍結 entry `test_sort_swo_oracle.py::test_masstree_manifest_rejects_one_byte_change` | 値 0.12 → 0.13 | `test_update_acceptance_duration_ledger.py::test_t1574_changed_suite_ledger_node_delta_is_exact` だけ | 値を exact に読む実台帳 test はこれだけ (g5 は key、g6 は `@real-repo` だけ、g7e は性質) |
| M2 | 凍結 suite `test_critic.py::` | key `orchestrator/tests/test_critic.py::test_t2825_mutation_stale` を値 1.0 で追加し `nodeid_count` を +1 | 同上だけ (suite node 集合の hash) | count は整合するので g7e / conftest の検証は通る、g5 は consumer key 側なので被覆は落ちない |
| M3 | 非凍結 entry | 凍結 prefix と `@real-repo` 以外の key を sorted 順の先頭から被覆 < 0.90 になる件数 (実装後に件数を確定) 削除し `nodeid_count` を合わせる | `test_acceptance_schedule_order.py::test_g5_real_ledger_covers_at_least_90_percent_of_real_collection` だけ | 凍結・`@real-repo` 不変で t1574 / g6 は通る、count 整合で g7e は通る |

`@real-repo` の値変更 (g6 と t1574 の 2 理由) と `nodeid_count` の不整合 (g7e と conftest 検証経由の g6) は単一理由にならないので登録しない。
M3 の削除件数は B 台帳と main collection から実装後に算出し、final spec に書く。

## 段 5 / 6 の構成

段 5: 単位 L と単位 P を並列 (所有 path 素)。投入直前に `check_wave_startup.py --mode midflight`。段 6: read-only review 1 本 (台帳の検算と probe の
実装を 2 レンズで)、fix は同木、変異 3 本、焦点走 (上の runner、親が dispatch)、測定系列、記録後に land 用の最終受入。

**追補 2 (段 6 レビュー後、09:17 JST、親、レビュー B 所見 1 に対する実測):** 依頼の「未収載 334 unit の再登録」は、T-2817 `ledger-model.json` の
`missing_ledger_nodes` 334 件に対し **202 件が新台帳に登録され、132 件は据え置き**になる。132 件はすべて凍結 8 suite 内
(`test_real_repo_serialization.py` 66、`test_sort_swo_oracle.py` 37、`test_p3_s4_loop_sort.py` 29) で、D2107 の「凍結 8 suite は据え置き」に従った結果である
(334 件は旧台帳に 0 件登録)。内訳は `t2817-334-split.json`。**完了報告・insight には「334 件中 202 件を登録、凍結 132 件は据え置き」と書き、「334 件を再登録した」と書かない。**
T-2817 の 334 という観測値は書き換えない (規律 7)。

**追補 3 (同、レビュー A 所見 2 に対する裁定):** 変異 M3 の実装は登録した「sorted 順の先頭から削除」ではなく、**g6
(`test_g6_all_real_repo_items_stay_one_unit_and_keep_relative_order`) が順序比較に使う key (15.0) を保護した、被覆 ≤ 0.87 を満たす最短の連続区間**
(3,265 件、先頭 `test_acceptance_schedule_order.py::test_g7_controller_reads_ledger_only_for_enabled_loadgroup`、末尾 `test_campaign.py::test_recovery_waits_for_external_exclusive_wal_lock`、
被覆 86.996419%) になった。**登録どおりではないので、この差を erratum として残す** (DW-M02)。単一理由は変更後の spec に対して確かめる (g6 の依存は
`test_acceptance_schedule_order.py:839` で実在、レビュー A が独立に確認)。probe 走の観測 node が期待どおり g5 だけであることで裏を取る。

**追補 1 (段 6 前、08:53 JST、親):** 段 6 review は `DW-S06-A` に従い 2 本並列に増やす (A = 実効性: 台帳検算と probe が事前登録を正しく実装するか、
B = `DW-S03` の過剰・削除レンズ)。測定器が判定を左右するため軽量版の省略を使わない (厳しい側への変更で、事前登録の判定規則は変えない)。
変異は `DW-M05`〜`M08` に従い `tools/mutation_harness.py` / 独立 clone (D1009) の dispatch 経路で probe → final。
