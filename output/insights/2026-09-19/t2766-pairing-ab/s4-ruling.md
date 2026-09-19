# 段 4 裁定 — [T-2766] 段 3 相談 (2 レンズ、`codex/s3-consult.md`) の所見と plan v2

裁定直前に裁定 inbox (`/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/`) を再走査した: T-2766 / pairing に触れるのは `2026-09-18-rulings-full23-verdicts.md` の項 6 (D2148 項 6 と同文) だけで、wave 開始後の更新は無い。

## 所見の裁定表

| # | 所見 | 判定 | 採否 | scope | 処置 |
|---|---|---|---|---|---|
| A1 | 非 docs 木一致では同一 tip・同一条件にならない (`output/` を rglob する real-repo test、docs を読む test、履歴依存) | real | 採用 (親が方式を変更) | 内 | 測定走は待ち手 (`dev_wave_wait.py acceptance`、claim 直後に main を取り込む) を使わず、**同一 SHA に固定した wave worktree から `IZANAGI_ACCEPTANCE_SHARDS=3 python3 tools/run_tests.py` を直接投入**する (受入形・空 argv・Pegasus LOGIN の明示 shard mode = `tools/run_tests.py:2473-2490, 2617-2625` で 3 shard dispatch。lease / merge / receipt だけが無く、dispatch・shard child・`tools.acceptance_shards`・session dir は受入と同一経路)。全測定走の tip SHA は同一。有効対の条件 = 両走の tip SHA 完全一致 (構成上常に成立、集計器が検算)。land 用の最終受入だけ待ち手を使う |
| A2 | 判定規則の内部矛盾 (10 % の適用先、全対負・ゼロ・3 対未満の未定義) | real | 採用 | 内 | §事前登録で再定義 (対ごとの D357 注記、3 種の中央値を分けて表示、閾値は本 wave 独自の保守基準、判定不能を先に分岐) |
| A3 | rank / partner だけでは独立検証が閉じない (junit は nodeid を classname/name に変換、同値 cost の tie-break) | real | 採用 (縮約して) | 内 | property を `scope` / `rank` / `partner` / `worker` (実行 worker id) の 4 つにし全 item に付ける。独立検証は tie-break 非依存の形 (head の (cardinality, cost) 多重集合、partner の cost 多重集合 = 候補中最小 48、rank 48〜95 = partner 集合、被覆 = selected 全件) を `report.json` の `selected` + 台帳 + junit から再計算。自己申告 rank を期待値に使わない |
| A4 | 隣接対 ≠ 同 job / 同 allocation。A,B,B,A,A,B は厳密な交互でない | real | 採用 | 内 | 呼称を「逐次の隣接対比較」にし、対 ID と shard ごとの job ID・node・投入 / 実行開始 / 終了・queue 待ち・受入間隔・他 wave の並行本数を記録 (説明資料、事後選別には使わない)。順序は A,B / B,A / A,B を維持 (対内位置は 2:1) |
| A5 | W_max は妥当。O / F は同 shard で対応づける | real | 採用 | 内 | shard ごとに W_j / O_j / F_j、argmax、W_max。F は残差と明記 |
| A6 | 赤と停止規則の固定 | real | 採用 | 内 | 有効対 3 組固定 (早期停止しない、良い対が揃うまで測らない)。無効対は同順序で追加、測定走上限 12 (landing 1 走は別)。上限で 3 対未満なら「反復不足」。赤は全件の本文・arm 別件数を残し、B 固有で再現する赤は実装問題として扱う。T-2710 の「条件ごと置換 1 回」からの変更を明記 |
| A7 | 親 brief の数値の限定 | real | 採用 | 内 | README で「直近 40 session (親の集計、独立再検算なし)」「regime 一致は items 2 の一致のみ」「cost≈0 は台帳値」「collect-only は bytecode だけ」「B 緑 = 今回のB 走で順序依存失敗を観測しなかった」と書く。各 shard の候補 cost 分布を集計器が出す |
| B1 | cardinality 負例が構成不能 (realized は cardinality 降順)、M4 不成立 | real | 採用 | 内 | 負例 = 2 item unit を 49 個以上置き head 外に高 cost の 2 item unit が残り partner が低 cost singleton になる fixture → 再 sort で rest の 2 item unit が前へ戻り検算が失敗 → `UsageError`。M4 = 検算だけ削除 → 例外が出ない |
| B2 | A 不変の負例が collection 順を検査していない | real | 採用 | 内 | 未設定 / 空文字で、固定した期待 collection 列・identity・unit 内順・既存 property・group / skip marker・selected を比較 (自己比較にしない)。B 側にも hold・複数 item group・real-repo suffix を含めて「順序と追加 property 以外は不変」を検査 |
| B3 | 「49〜96 位」≠「各 worker の 2 個目」 | real | 採用 | 内 | 主張を「先頭 48 固定 + 次 48 を低 cost 化」に限定。実 `LoadGroupScheduling` + `send_runtest_some` 記録 + `mark_test_complete` で駆動する配布検査を 1 本追加し、反例 (初期 3 item の worker、2 item の worker の 3 個目) を既知の限界として README に書く |
| B4 | witness の主張範囲 | real | 採用 | 内 | A3 の `worker` property で B の実配布 (item → 実行 worker) を junit から復元。A は `worker_occupancy` のみ。新 probe 基盤は作らない |
| B5 | env 伝播は allowlist 追加で静的に成立、pin は伝播試験でない | real | 採用 | 内 | `dispatch()` の request 生成に key が載る test (`test_tests_task_env_allowlist_carries_only_recording_transport` 同型) を追加。live 確認は B 走の 3 shard witness |
| B6 | 変異の帰属固定 | real | 採用 | 内 | §変異 matrix に帰属表。fresh item、単独適用、無変異緑を先に確認 |
| B7 | 非 land の再現資料不足 | real | 採用 | 内 | README に測定 commit SHA・実装差分 (commit SHA と patch sha256)・台帳 sha256・集計 script sha256・起動手順・raw 成果物索引・残置 branch の所有者 / 用途 / 再訪条件を書く |
| nit | helper への `unknown_cost` / scope の受け渡し、アンカー訂正 | real | 採用 | 内 | plan v2 に明記 (hold property は `conftest.py:2231-2235, 2248-2253`、harness は `:1566`) |

scope 外 real 所見: なし。refuted: なし。(P1) 支持、(P2) 支持、(P3) 条件付き → A3/B4 で充足、(P4) 反証 → A1 の方式変更で解消、(P5) 条件付き → 段 6 に実装レビュー 1 本 (実配線・変異・集計器) を置く。

## plan v2 (author への確定仕様。`s2-plan.md` からの差分)

1. **conftest** (`orchestrator/tests/conftest.py`):
   - 定数: `_ACCEPTANCE_PAIRING_ENV = "IZANAGI_ACCEPTANCE_PAIRING_V1"`、`_ACCEPTANCE_PAIRING_TOKEN = "t2766-min-cost-partners"`、`_ACCEPTANCE_PAIRING_PROPERTY_PREFIX = "izanagi_acceptance_pairing_v1"`、`_ACCEPTANCE_PAIRING_HEAD_UNITS = _ACCEPTANCE_INITIAL_DISTRIBUTION_UNITS // 2` (48)。
   - `_acceptance_pairing_opted_in()`: 未設定 / 空 → False、exact token → True、他 → `pytest.UsageError`。
   - `_pair_initial_distribution_units(ordered_units, unknown_cost)`: `_reorder_acceptance_items_by_duration` の `ordered_units` 確定直後に opt-in 時だけ呼ぶ。unit dict には既存の `index` / `items` / `known` / `cost` があるので scope は `_acceptance_loadgroup_scope(str(unit["items"][0].nodeid))` で得る。realized = `sorted(ordered_units, key=lambda u: -len(u["items"]))`。`len(realized) < 96` → `ordered_units` をそのまま返し property を付けない (B 発火と数えない)。head = realized[:48]、候補 = realized[48:]、partner = 候補を `(effective_cost, realized 位置)` 昇順の先頭 48、rest = 残り (realized 順)、paired = head + partner + rest。検算 `sorted(paired, key=-len)` の scope 列 == paired の scope 列、不一致は `pytest.UsageError("acceptance pairing infeasible: ...")`。返り値 = paired (unit dict に `pairing_rank` と `pairing_partner` を付ける)。
   - property (opt-in で pairing を適用した走だけ、全 item): `("izanagi_acceptance_pairing_v1_scope", scope)`、`("izanagi_acceptance_pairing_v1_rank", str(rank))`、`("izanagi_acceptance_pairing_v1_partner", "1" | "0")`、`("izanagi_acceptance_pairing_v1_worker", workerid)` (`config.workerinput.get("workerid", "")`、controller では付けない)。hold の `user_properties.extend` (`conftest.py:2231-2235, 2248-2253`) と同型。
   - opt-in off の経路は現行と完全一致 (返り値・順序・property・副作用)。
2. **dispatch_compute** allowlist 1 行 + comment。**pin** `test_tests_task_env_allowlist_is_exact` 更新 + request 生成に key が載る test 1 本。
3. **test** (`test_acceptance_schedule_order.py`、G12 群): 正例 (dequeue_trace[48:96] = 期待 partner 列を非同値 cost で独立に固定、[:48] 不変、rest 元順、property 4 種)、負例 1 (未設定 / 空文字で固定期待 collection 列・identity・marker・selected・property 不在)、負例 2 (別値 → UsageError)、負例 3 (B1 の到達可能 fixture → UsageError)、境界 (unit < 96 → 無変更・property 無し; nproc 16/32/48 で collection 同一)、配布検査 (実 scheduler + 完了通知駆動で「pending ≤ 2 の worker の 2 個目が partner」を示し、3 item 初期 unit の worker が飛ばされる反例を明示)。fresh item を作り A/B で property を共有しない。
4. **集計 script** `probe-t2766/t2766_ab_analyze.py` (unit worktree に書き、親が job dir へ退避、repo へ入れない): 入力 = 走ごとの `run.json` (親が書く: 条件 / tip SHA / 投入・完了時刻 / session dir / env 記録 / 他 wave の並行本数 / load) + session dir の 3 shard `junit.xml` `report.json` `dispatch/receipt.json` + 台帳。出力 = 対表 (shard ごと W/O/F/最忙 worker items・duration、argmax、W_max、ΔW、率)、3 種の中央値、witness 検証 (被覆、head / partner の多重集合、rank 48〜95 = partner、B の worker 別 item 列と最長 unit の worker の 2 個目、A の最忙 worker)、tip 一致、除外表、事前登録の判定。JSON + Markdown。標準 library のみ。
5. **測定手順** (親): (a) 実装 commit 後の tip を測定 tip とし `impl-t2766-pairing-optin` branch を同 SHA に作る。(b) login で `python3 tools/run_tests.py --collect-only -q -p no:cacheprovider` 1 回 (bytecode)。(c) 他 wave の受入 leader ≤ 1 かつ load1 < 30 を確認してから、launcher `.sh` (A: env 無し、B: `IZANAGI_ACCEPTANCE_PAIRING_V1=t2766-min-cost-partners`、共通: `IZANAGI_ACCEPTANCE_SHARDS=3`) を detach で投入。1 走ずつ、完了後に次走 (順序 A,B / B,A / A,B)。(d) 各走の直前後に `git status --porcelain --untracked-files=all --ignore-submodules=none` が空 (job dir へだけ書く) と HEAD SHA を記録。(e) 走行中は worktree に書かない、自分の他 job を走らせない。

## 事前登録 (結果を見る前に固定)

- **有効走**: rc=0 (child-green 相当 = junit の failures/errors 0、全 shard 完走)、3 shard の report.json 実在、tip SHA = 測定 tip、B ではさらに witness 検証 (被覆 100 %、多重集合一致、rank 48〜95 = partner) 通過。
- **有効対**: 隣接 2 走 (A,B または B,A) が両方有効。無効対は同順序で追加。有効対 3 組で固定終了 (早期停止も追加もしない)。測定走上限 12 (landing 除く)。3 対未満 → 「判定不能 (反復不足)」で終える。
- **指標**: shard j の W_j (JUnit testsuite time)、O_j (worker_occupancy 最大 duration)、F_j = W_j − O_j (残差)、W_max = max_j W_j と argmax。対 k: ΔW_k = W_max(A_k) − W_max(B_k) (正 = B が短い)、r_k = ΔW_k / W_max(A_k)。各対に D357 注記 (|r_k| < 10 % は 1 走比較として「変化なし」)。
- **集計**: (1) med_k ΔW_k、(2) med_k r_k、(3) 条件別中央値差 med(W_max(A)) − med(W_max(B))。3 つは別量として併記し、足し合わせない。
- **判定** (有効 3 対が揃った場合のみ): (i) 全対 ΔW_k > 0 かつ med_k r_k ≥ 10 % → 「方向一致・閾値以上」→ 採否の裁定パッケージをユーザーへ返す (本 wave は採用しない、実装は impl branch)。(ii) 全対 ΔW_k > 0 かつ med_k r_k < 10 % → 「方向一致・閾値未満」→ 見送りとして諮る。(iii) それ以外 → 「効果未確立」。副分類: 符号混在 / ゼロを含む / 全対 ΔW_k < 0 (退行の観測)。閾値 10 % は本 wave 独自の保守基準 (D1260 の採用条件と同型) で D357 からの導出ではない。3/3 一致を有意差判定にしない。
- **witness の主張範囲**: property = collection 変換の発火 + item → 実行 worker の対応 (B のみ)。「最長 unit の worker の 2 個目が partner か」は B の junit から復元して記述する。「全 worker の 2 個目が最小」は主張しない。
- **赤**: 全件の本文と arm 別件数を残す。F945 型でも「型」だけで非帰属と断定せず本文で判定。B 固有で再現する赤は実装問題として fix へ回す (測定は fix 後に取り直し、取り直し前の走は表に残す)。
- **記録**: 対表・中央値・判定・除外表・witness・各 shard の候補 cost 分布・job ID / node / 時刻・他 wave 並行本数を README に。効果の有無にかかわらず実装は main に入れない。

## 変異 matrix (DW-M01、位置と帰属)

| # | 変異 (1 理由) | 位置 | kill を帰属させる検査 |
|---|---|---|---|
| M1 | partner 選択の sort key を昇順 → 降順 | `_pair_initial_distribution_units` の `sorted(候補, key=(cost, pos))` | 正例: 非同値 cost で独立に固定した期待 partner 列 (dequeue_trace[48:96]) |
| M2 | head 幅 48 → 47 | 同関数の `realized[:48]` | 正例: head の完全一致と partner 境界 |
| M3 | opt-in 判定を恒真 | `_acceptance_pairing_opted_in` | 負例 1: 未設定 / 空文字で固定期待 collection 列が変わる |
| M4 | cardinality 検算を削除 | 同関数の検算 `if` | 負例 3: B1 fixture で `UsageError` が出ない |
| M5 | property 付与を削除 | reorder 関数の `user_properties.extend` | 正例: property 4 種の欠落 |
| M6 | allowlist の key を削除 | `dispatch_compute.py` `TASKS["tests"].env_allowlist` | exact pin + request 生成 test |

各変異は単独適用、無変異の緑を先に確認 (harness baseline)。テスト側で期待値を本番 helper から算出しない。

## 段 5 / 6 の構成

段 5: author 1 本 (workspace-write、unit worktree `.codex/worktrees/t2766-unit-impl`)。親: 焦点走 (login、`test_acceptance_schedule_order.py` + `test_pegasus_dispatch_compute.py::test_tests_task_env_allowlist*`) → 実装 commit → 測定 (§5 手順) → 集計。段 6: 実装レビュー 1 本 (read-only: A 不変・受理集合・xdist 整合・env 配線・変異帰属・集計器の独立性) → fix (必要時) → 焦点再レビュー → 変異 matrix (計算ノード) → 記録。
