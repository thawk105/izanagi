# [T-2750][T-2273] 受入 shard-0 の連結成分粒度 (file → node) は実装せず閉じる — 20 走の同時刻対照と offline 割付 simulation で「固定 duration model では最遅 shard の下限不変・実 wall 改善は未実証」、素直な案は real-repo の跨ホスト排他を外す

authority: none / default_effect: no-state-change (プロセス監査・逐語凍結。可変状態の正本は worklog 末尾と現行 phase doc)

- wave branch: `worktree-dev-wave-t2750-shard0-component-granularity`
- 基準 commit: `38353207f` (local main、wave 開始時 HEAD==main、乖離 0)
- 実装 commit: なし (docs-only、実装面差分ゼロ → 変異 matrix は DW-S04 により免除。受入全走は免除せず land 前に 1 回投入し、結果は land の受領証に残る)
- 起票: T-2750 は worklog archive 1603 (2026-09-17)、T-2273 は archive 1231 (2026-09-03) の P1
- 設計判断: 本 wave の decisions fragment (slug `shard0-component-granularity-no-wall-gain`、D 番号は land の fold が付ける)
- 一次資料 (起票の根拠): `output/insights/2026-09-17/t2236-ledger-refresh/README.md`
- job dir (prompt・log・親 script の原本): `/home/SFC/tanab/.claude/jobs/155c16ed/tmp/` (wave artifact は `wave-t2750/`)。親の解析 script は repo へ入れない (実装面の path 規約) — sha256 は末尾の表
- codex 子: plan 1 本 (240 秒)、consult 2 本 (レンズ A 正しさ境界 / レンズ B 実効性)、全部 `gpt-6-astra` / `medium` / read-only、3 本とも accepted。author / review / fix は起動していない (実装なし)

## 依頼と採用条件

受入の最新律速 = shard-0 の連結成分 (`campaign-repository-scan` / `real-repo` / `s8c-predicate-snapshot` / `s8c-preregistration-candidate` の 4 xdist group が 1 成分、`conftest.py` の `REAL_REPO_RESOURCE_NODES` が `real-repo` を動的付与、台帳予測 7502 秒 / 実測 8569 秒 / 均等なら 6053 秒) を `tools/acceptance_shards.py` の `allocate` で解く — 案 (a) 成分単位を file から node へ (順序依存の検査が先)、案 (b) 大 file の real-repo node を別 file へ分離。D358 と受理集合は変えない。**採用条件 = 検出力維持と D104 の効果実証 (同時刻対照つき、n=1 の前後比較で主張しない)。** 実装面は Codex author、変異事前登録要。本題の分割改善だけ、追加 gate・検査・台帳は scope 外。

## 結論

**採用条件は成立しない。実装せず、T-2750 を閉じる。** 理由は強い順に 3 つ。

1. **素直な案 (a) (file union の削除) は検出力維持を満たさない — real-repo の跨ホスト排他の防壁 (規律 2) を外す。** `orchestrator/tests/test_s8c_preregistration_predicates.py::test_repository_candidate_uses_real_s8c_budget_module` は xdist group 無し・`REAL_REPO_RESOURCE_NODES` 外だが、function fixture `repository_candidate_commit` (parent write lock 下) の helper `_candidate_commit_with_worktree` が実 repo root を cwd に `git read-tree` / `add` / `write-tree` / `commit-tree` を実行し実 object store へ書く (`GIT_INDEX_FILE` の分離は object store の分離ではない)。この node が衝突成分と同じ shard (= 同 host) に留まる理由は**同 file の group 付き node との file 閉包だけ**で、`test_real_repo_serialization.py` の fixture-owned golden は「The only consumer shares its file component with this retained group」と明記している。file 閉包を外すと別 host の shard へ配置可能になり、`/tmp` の flock (同一 host 限定) では閉じられない。安全に実装するには明示 affinity の補完 (ItemRecord / parser / closure gate)、D711 gate 4 の裁定改訂、衝突閉包 (resource node + fixture-owned consumer + 明示 affinity) の独立検査の新設が要り、後 2 者は依頼が scope 外とした「追加 gate・検査」に当たる。inventory golden は実 repo アクセスの網羅的検出器ではない (宣言済み inventory 内の分類一致 + golden 列挙 fixture の consumer 一致 + resource node と交差する module/session fixture を seed にした閉包であり、seed の無い fixture・function fixture・import 副作用は全探索外)。案 (b) も real-repo marker 付き関数だけを移すと同型の取り残しを生み、nodeid の変更で台帳 key と golden の file 名 pin に触れる。
2. **固定 duration model では最遅 shard の下限は不変で、負荷の均等化は最大値を動かさない。** 48 worker では shard の wall は「最長 node + 相方 + 固定費」で決まっている (下の実測 1〜3)。案 (a) の offline 割付 simulation (下の 4) では負荷が完全に均等化されるが、最遅 shard の予測は 3 通りとも 306.1 秒で同値。予測 wall の合計は 690.2 → 748.3 (hybrid) / 838.3 (node) 秒へ増える (b5 群が別 shard へ散り床を作る)。
3. **実 wall 改善の経路は「同 host 競合の低減で最長 node 自身が速くなる」だけで、未実証・期待値未数値化。** 既存 99 session からは分離できない (下の 5)。上限の目安は相方 約 20 秒 (中央値 347.7 秒の 5.8%) で D357 の「変化なし」域に入る。decisions 項35「効果を先に測り、未確認のまま実装しない」と D104 決定 3「効果を示せない機構は land しない」に従い、paired 実測 (D104 決定 4) へ投資しない。

一次資料 (T-2236 README) の「この成分 (7502 秒) が均等負荷 (6053 秒) を超えるので LPT はどう並べても shard-0 を軽くできない。これが shard-0 の床」は**負荷 (直列和) の命題としては真、wall への波及は未実証** (README はその因果経路を paired 実測していない)。現行の床は D2067 のとおり t080 e2e 群 (b5 系 5 本、台帳 220〜240 秒) の単体所要で、D2068 が fixture 側の高速化 3 案を却下している。

## 実測 (親、repo 外の受入成果物 `/work/1/SFC/tanab/.izanagi-acceptance-shards/*/shard-*/{report.json,junit.xml}`)

1. **最忙 worker は最長 node 1 本 + 相方で決まる。** 台帳 refresh 後 (main に `363e79b10` を含む tip) の受入 20 走 (2026-09-17 09:34〜12:26 JST、すべて他 wave の受入 = 同時刻対照) で、shard-0 の最忙 worker は **20/20 走で item 2 個**: 最長 node `orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]` (225.1〜499.7 秒、中央値 264.8) + 相方 (19.8〜20.1 秒が 17 走、7.5〜8.7 秒が 3 走)。最大 worker 占有 − 最長 node の中央値 = 19.9 秒。wall − 最大占有 (collection + worker 起動 + 集約の固定費) の中央値 = 66.1 秒 (65.0〜88.2)。shard-0 の直列和 ÷ 48 (平均 worker 負荷) = 161〜417 秒で、**20 走すべてで最長 node より小さい**。shard-1 / shard-2 も同型 (最大占有 = 最長 node + 14〜24 秒)。表は `verbatim/parent-20runs-shard0.txt`。
2. **99 session (2026-09-16 20:00 以降) の最遅 shard は shard-0 が 94、shard-2 が 4、shard-1 が 1** (例: `bda4db87` は shard-0 344.6 / shard-1 381.9)。shard-0 wall 中央値 352.9 (286.6〜690.9)、300 秒以下は 3 走。最遅 shard wall (D1620 の測定面) の中央値 359.1。表は `verbatim/parent-sessions-since-0916-2000.txt`。
3. **相方 約 20 秒は割付でなく xdist 初期配布の構造。** LoadScope/LoadGroup scheduling は各 worker に初期 2 unit を配り (#277 heuristic)、group 無し node は 1 node = 1 unit。session `5141225c` (refresh 後台帳) で最長 node は cost 順 2 番目 (台帳 240.0、1 番目と tie)、同 worker の 2 個目は `test_codex_reasoning_ab.py::test_m3_ignored_extra_and_missing` (台帳 22 秒) と同定した。最長 node が終わる頃 workqueue は空で 3 個目は来ない。ただし「worker k は cost 順 index k と 48+k を持つ」という順位説明は一般化しない (`test_acceptance_schedule_order.py` の G11 が示す mixed-scope の dequeue 順は collection 順と一致しない — レンズ B)。tail 7.5〜8.7 秒の 3 走は旧台帳割付 (nsel=9004) で cost 順が違った。
4. **案 (a) の offline 割付 simulation** (`simulate_option_a.py`: collect-only 24660 node + 現行台帳、`allocate` と同じ LPT・group 優先・tie-break、成分定義だけ変更。login の collect-only は `test_t316_sandbox_probe.py` が module-level assert で collection error → 166 node 欠け、未登録 writer の affinity 補完は含まない = 安全な候補の評価ではなく負荷の反実仮想のみ):

   | 割付 | shard 負荷 (秒) | 負荷/48 | 各 shard の最長 node (台帳) | 最遅 shard の予測 makespan (D1019 式 max(最長 node, 負荷/48) + 66.1) | 予測 wall の合計 |
   |---|---|---|---|---|---|
   | 現行 (file + group 成分) | 7523 / 5372 / 5372 | 156.7 / 111.9 / 111.9 | 240 / 140 / 100 | **306.1** | 690.2 |
   | 案 (a) hybrid (group 付き node だけ group 成分、同 file の他 node は file 成分) | 6089 / 6089 / 6089 | 126.9 × 3 | 160 / 150 / 240 | **306.1** | 748.3 |
   | 案 (a) node 粒度 | 6089 / 6089 / 6089 | 126.9 × 3 | 160 / 240 / 240 | **306.1** | 838.3 |

   衝突成分は 3929 node / 7523 秒 → 188 node / 1612 秒に縮む (均等化そのものは成立する)。出力は `verbatim/parent-simulation-option-a.txt`。この model は相方・開始遅れ・fixture 再構築・配置による duration 変化を含まない下限であり、「実 wall の期待利得 0」の証明ではない (レンズ B)。
5. **最長 node の膨らみは同じ計算ノード内の要因と結び付くが、割付を変えて速くなる証拠は無い。** 99 session で corr(最長 node 所要, (shard-0 の全占有 − 最長 node)/47 = 相方を含む他 worker の平均) = 0.993、corr(最長 node 所要, 別ノードで走る shard-1 + shard-2 の最大占有) = 0.069、corr(最長 node 所要, shard-0 の selected 数) = −0.031。旧台帳割付 (nsel > 6000、n=81) の最長 node 中央値 255.1 / 平均占有 197.1 / wall 355.1、refresh 後割付 (n=18) は 261.6 / 186.0 / 347.7。同一割付内では仕事量が一定なので 0.993 は「ノード状態 (共通の build 待ち・host 状態) が全 worker を同時に膨らませる」で説明でき、「仕事量を減らせば最長 node が速くなる」の証拠にはならない。旧/新割付の仕事量は 8852 対 8569 秒でほぼ同じで対比較にならない。出力は `verbatim/parent-contention-check.txt`。

## 段 3 の所見と段 4 裁定 (逐語は `verbatim/`)

- 段 2 plan (`s2-plan.md`): 素直な file union 削除は不可 (上の理由 1 の writer を名指し)。実装するなら明示 affinity の補完・D711 改訂・衝突閉包の独立検査・paired 測定 harness が要る。brief の平均負荷「161〜221 秒」は誤りで 161〜417 秒 (結論は不変)。推奨「今回は実装しない、docs-only は『固定 duration model で利得なし・採用証拠不足』と書き『期待利得 0 の実証』とは書かない」。
- 段 3 レンズ A (`s3-lensA.md`、正しさ境界): 所見 1 (writer の跨ホスト排他喪失) real、所見 2 (module fixture consumer が必ず失う) refuted — 確認済みの無保護例は function fixture、所見 3 (inventory golden は網羅的検出器でない) real、所見 4 (D711 の file 閉包は現状では排他の防壁も担う) real、所見 6 (brief の D358 要約は D1618 の runtime 分割を反映すべき) real。規律 2 の射程判定 = (c) 一部だけ射程内。must-fix (実装する場合) = file 由来の必要 affinity の保存、期待 affinity の独立検査。
- 段 3 レンズ B (`s3-lensB.md`、実効性): (P1) 「固定 duration model の下限不変」から「実 wall の期待利得 0」への飛躍は real (原表の訂正: tail 19.9 秒は 17/20、平均占有 161〜417)、(P2) 「2 unit 構造」と「約 20 秒を必ず払う」は別で順位説明は一般化しない (real)、(P3) 因果分離不能は妥当だが期待値 0 は導けない (条件付き)、(P4) 証明対象は正本リスト単独でなく衝突閉包全体 (条件付き)、T-2236 の床の読み替えは「wall の命題として偽」でなく「未実証」(real)。実装すべきの最強の形 = 安全な候補を試作し同一 allocation の paired 測定で採否を決める価値はある、ただし現証拠が支持するのは条件付きの試作・測定までで land すべきという結論は成立しない。
- 段 4 裁定 (`s4-ruling.md`): 所見 A1〜A7・B1〜B7 の real / refuted と採否の表。裁定 = 実装しない (4→7→8→9)、記録の言い方は上の「結論」のとおり、T-2750 完了・T-2273 更新、次の一手 2 件を P3 で起票、変異 matrix 免除・受入全走は免除しない、段 5・6 は起動しない。「やらない理由の最強の形」も同 file に記録。
- brief (`s1-brief.md`) は親の provisional 裁定 (P1)〜(P4) を含む原文のまま凍結し、訂正は本 README と `s4-ruling.md` で行う (原文は書き換えない)。親の追加実測 (`s2-plan-addendum-parent.md`) の「他 47 worker の平均」は実際には (全占有 − 最長 node)/47 で相方を含む (レンズ B 所見 4)。

## 親の実走

- 実 repo を読む検査 (DW-S04、記録 commit 前): 三軸語走査 `python3 -m orchestrator.campaign.s8b_holdout_freeze search` と `orchestrator/tests/test_s8b_repo_scan_invariant.py` の焦点走。結果は worklog fragment に書く。
- 受入全走: 記録 commit 後の最終 tip に対し land 前に 1 回投入する。結果 (session・件数・verdict) は land の受領証に残り、本 README には書けない (受入後に本 file を変えると tested tip から漏れる)。

## 残存限界・次の一手候補 (記録のみ、本 wave では実装しない)

- 最遅 shard の床 = 最長 node (t080 e2e b5 群 5 本、225〜500 秒) + 相方 約 20 秒 + 固定費 約 66 秒 ≈ 311 秒 (最良時)。5 分以内は割付では届かない。
- (a) reorder 側の pairing: 最長 unit を持つ worker の 2 個目を最小 unit にする。削れても 5.8% で D357 の「変化なし」域。実 scheduler の配布順 (G11) の確認が先。
- (b) 安全な案 (a) の試作 + 同一 tip・同一 collection・同一台帳で旧/新割付を交互 n≥3 (A-B / B-A) の paired 測定 + 機構発火の直接観測 (別 shard へ出た node 数・file 数・各 affinity が同一 host に残った事実)。費用 ≈ Codex author + 変異 + 受入 ≥6 走。安全化 (affinity 補完・D711 改訂・衝突閉包検査) を含むため本 wave の scope を超える。
- (c) b5 群 5 本の単体所要。D2068 が fixture 側 3 案を却下済み。残る候補 (e2e の分割・parametrize の縮約) は受理集合に触れるため別裁定。

## 逐語の行末空白の可逆正規化 (DW-S07)

`verbatim/` の `.md` のうち codex 出力 3 本は `git diff --check` に触れる行末空白 (Markdown 二重空白改行) を除いてある。可視文字は不変。原文 bytes は `verbatim/originals.json` (sha256 `7acf2f292e71c475f8cb554603d86e1f83bc6277b13c65338b98b0b714f77d4c`) に UTF-8 text として収め、各 text をそのまま書き出せば原文 bytes に戻る。

| file | 原文 bytes | 原文 sha256 | 行末空白を除いた行数 | 正規化後 bytes |
|---|---|---|---|---|
| `s2-plan.md` | 16323 | `25f0479618851c48…` | 10 | 16303 |
| `s3-lensA.md` | 6882 | `4e991304717fe54a…` | 13 | 6856 |
| `s3-lensB.md` | 10761 | `86008af3bd663399…` | 4 | 10753 |

## 親の解析 script (repo 外 `/home/SFC/tanab/.claude/jobs/155c16ed/tmp/`、sha256 先頭 16 桁)

| script | sha256 | 用途 |
|---|---|---|
| `list_sessions.py` | `b6831d48101e4c51` | 受入 session の shard 別 wall / span / 最大占有の一覧 |
| `tail_over_longest.py` | `f776839b5e49444f` | shard-0 の最大占有 − 最長 node (tail) と固定費の集計 |
| `t2750_group_dump_plugin.py` | `8471be34792fd54e` | collect-only 用 plugin (nodeid → xdist_group) |
| `simulate_option_a.py` | `3776c838d7c35283` | 案 (a) の offline 割付と makespan 予測 |
| `companion_check.py` | `45db9c980de8ce92` | 相方の同定 (cost 順と junit 実測) |
| `contention_check.py` | `37503f6dcd7fc074` | 最長 node 所要と同 shard / 別 shard の相関 |
| `project_decisions.py` | `0dab93270d98c8dd` | decisions.md の D を見出しで切って逐語射影 |
| `normalize_verbatim.py` | `8aebf232e869eaeb` | verbatim の行末空白の可逆正規化 |
