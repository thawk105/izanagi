---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-21
wave: dev-wave-t2817-acceptance-bottleneck-3
seq: 1
title: [T-2817] 受入律速の再同定 (第 3 回) と collection 差の分解診断 — pairing 後の最遅 shard の wall は ledger 未収載の active_v2 系 node を後方 rank で直列に抱えた別 worker で決まり (現行 tip の replica 1 走 + 参照受入で同構造)、受入 pre 61 秒と温 collection の差 約 45 秒は shard plugin を載せた段で worker の modify 複合区間に現れ、早期 memo prewarm は並走して隠れる (診断のみ・実装 0 行、branch worktree-dev-wave-t2817-acceptance-bottleneck-3)
---

## 本文

- ユーザー依頼 (2026-09-21、dev-wave 引数の逐語は insight `verbatim/T-2817-origin.md`) の範囲で 1 wave。対象 = [T-2817] + 持ち越し [T-2273] / [T-2444] / [T-2495] / [T-2560] (D2148 項 6、D1936 項 35)。診断だけで改善実装は 0 行。
  数値・判定・限界・効果量の見込みはすべて一次資料 `output/insights/2026-09-21/t2817-acceptance-bottleneck-3/README.md` (機械集計 `job-out-aggregate.*` / `raw/job-out-b/analysis-A.*` / `ledger-model.*`、生記録 `raw/`、逐語 `verbatim/`) にあり、ここには再掲しない。
  decisions fragment は無し (新しい設計判断を作らない)。failures fragment も無し (計装の穴 1 件は段 5 の fix で閉じ、既存 F の再発ではない)。専用 handoff は job dir (repo 外)。
- 起点 local main `285477c00` (fresh worktree、HEAD == main、開始 gate rc 0)。投入直前に local main `2afb39768` (docs のみ前進) を ff-only で揃え、その tip で Job A / Job B を測った。参照受入 (README commit の前、同 code) は post-claim merge で main `b880449bb` を取り込んだ `9ad14946e` で走った (child-green、`orchestrator/` `tools/` の diff 0 行)。
- 段構成: 軽量版 + 診断 wave の型 (段 1 → 段 3 相談 1 本 → 段 4 → 段 5 author 2 本並列 + fix 1 本 → 親の login 生死確認 → 計算ノード Job A (段階載せ collection 診断、bnode009) と Job B (現行 tip の A 条件 replica + 観測 wrapper、bnode008) を別 node へ並行投入 → 参照受入 1 走 → README (親) → 段 6 read-only review 1 本 + 焦点再レビュー → 7 → 8 → 9)。段 2 は省いた。
- **段 3 相談 (gpt-6-astra / medium、6 分) は所見 11 件 (高 6 / 中 5) を出し、全件 real・採用、refuted 0。** 高 6 件: scheduler の no-op 化は collection 一致検査を消す → 検査と失敗通知を残し配布だけ省く; S1 でも controller の同期 memo prewarm が発火 → S1 の名と段差の読みを訂正; 計時区間 (ledger 読込は configure 段、wrapper 順序) → 列を分離; S2/S3 の report.json は create-only → 走別 dir; (P1)「L の内訳の取り直しは省く」は依頼 (1) を満たさない → Job B (A 条件 1 走) を追加; offline 並びから O_max の変化は導けない → 仮説のまま、model 値に限定。
- **brief 前の前提実測 (login の read-only 観測、保存済み受入成果物の pairing property あり 21 session) が依頼の前提 (entry 1676 の式) を覆す新事実を出した:** 最遅 shard-0 で L の worker の相方は 21/21 で 0 だが、最大占有 worker は 21/21 で L の worker と別 (README §2b)。これを段 4 で再裁定し (P1) を条件付きに変えた。
- **段 5 の生死確認で計装の穴 1 件** (probe plugin が ledger 属性の有無しか記録せず、conftest は読まない場合も空 dict を置くため S2/S3 の ledger 有無を弁別できない) → fix 子 1 本で `ledger_entries` / `ledger_should_load` / worker の payload 有無を足し、narrowed `-n 2` で S1 形 / S3 形の弁別を確認した。
- **Job A の最初の投入は同一 worktree の pending orphan hold (Job B) で `orphan-hold` rc=16 (子は起動せず)** → 同一 worktree からの dispatch は直列 (DW-C00) なので、同 SHA の別 worktree `dev-wave-t2817-joba` (submodule 初期化・pyc 温め済み) から投入した (runbook §7.5 の並行投入)。
- **段 6 レビュー (gpt-6-astra / medium、read-only 1 本) は数表 251 件を照合 (247 一致) し、must-fix 2 / should 6 / nit 1 で NO-GO → 全件 real・反映。** must-fix = ledger model は「8 node」でなく中央値のある未収載 333 node 全部を更新していた (親の登録と実装の食い違い、model 値 19.5 秒を 8 node の効果として掲げない)、約 45 秒の shard plugin / `Path.resolve()` への帰属が計器の分解能 (modify 複合区間・process 群の sys 時間) を超えていた → 「複合区間に現れた、path 正規化 (全 item に 2 回) が有力な解釈」に統一。焦点再レビュー 2 巡目は `verbatim/s6-review2-out.md` (結果は README §7)。
- probe 7 file (bash 184 行 + python 6 本) は Codex author の子 branch `author-t2817-probe-a` (`f1a1e8eb0`) / `author-t2817-probe-a-fix1` (`a028857a6`) / `author-t2817-probe-b` (`ed461aa4f`) に実体があり、repo には `.txt` の逐語だけを置いた (land しない)。前提実測の読み取り script と生記録の整形は親が repo 外に書いた read-only の整形で、逐語を verbatim に置いた。Job B の replica session `69dcbd57434a3a0c176c98f0f222a969` は受入共有 root にあり受入ではない (受入成果物の読み取りから除外する)。
- 事故 (自分起因、実害小): (1) Job A の最初の投入が orphan hold で不発 (上記、4 分の損失)。(2) 段 5 author A の計装の穴 (上記、fix 1 本 5 分)。(3) README 初稿の帰属の言い過ぎ (段 6 must-fix 2、T-2243 §7 と同型の「計器より細かい帰属」)。(4) ledger model の登録 (8 node) と実装 (333 node) の食い違いを親が気づかず README に書いた (段 6 must-fix 1)。
- 焦点再レビュー 3 巡目 (上限) は README の残 3 件を closed とし、本 fragment に must-fix 2 (並走条件を「両方の短縮が必要」と断定、ledger 再登録の実効果を model 差と観測差で囲った)・should 2・nit 1 を出した。DW-O16 の上限に達したので親が全件 real と裁定して反映し (本 fragment の該当文)、4 巡目は行っていない。
- **非帰属赤の判定 (DW-O18):** 記録 commit 4 (`79c32e0b4`) 後の最終受入 1 走目 (02:59〜03:09 JST、tested tip `0d132aa00` = post-claim merge、session `f70466a8…`) は shard-1 の `test_codex_worker_launch.py::test_t2620_orphan_mixed_is_rejected` 1 件が赤 (`residual_observation.final_unknown_source=proc_stat_read_error`、`process_group_residual=None`; 3 shard 26,407 件中 1 件)。本文は harness の `/proc` 走査が無関係 process の消滅と競走する既知の型 (entry 1724 の T-2620 fix 巡で同じ `proc_stat_read_error` を観測) で、本 wave の差分は insight と本 fragment (docs のみ) なので到達不能。同一 tip で当該 test を単独再走 (login local、`run_tests.py … -k test_t2620_orphan_mixed_is_rejected`) → 1 passed (4.9 秒) で非再現 → lease を release して受入を再走 (2 走目、本 fragment のこの追記を commit した tip)。hold 登録簿には登録しない。
- 工数: codex 7 本 (consult 1、author 2、fix 1、review 1、focus 2、gpt-6-astra / medium)、計算ノード job 2 (Job A 442 秒 + PRR 7 分、Job B 425 秒 + PRR 17 分) + 参照受入 1 走 (child-green) + 単独再走 1 + land 用の最終受入 2 走 (1 走目は上記の非帰属赤 1 件、2 走目は本追記の commit の後に投入)。

## 次の一手差分

### 完了

- [T-2817] 受入 `pre` 61 秒と温 collection の差を同 job・同 node・同 checkout の段階載せ (S0 独立 48 process → S1 xdist → S2 +shard plugin → S3 +ledger) で分解し、増分 45.9 秒が S2 (shard plugin) の段で worker の modify 複合区間に現れ、早期 memo prewarm (44〜54 秒) は並走して隠れること、S3 の `pre_junit` 61.45 秒が同 code の参照受入 shard-0 の `pre` 61.76 秒を再現することを insight に記録した。削減可能量は書いていない。改善実装は行っていない。
  remaining: none
  base: d8b777229c166465cf2e3b5e008b45a2ba4d5432e29bc5dabd86157a1927ccca

### 更新

- [T-2273] **P1・律速を再同定 (第 3 回)、次の実測は ledger 再登録の隣接対**: pairing 既定 on 後の最遅 shard-0 の wall は L の worker ではなく、ledger 未収載 (T-2724 追加) の active_v2 系 node を後方 rank で直列に抱えた別 worker で決まる (最大占有 worker ≠ L の worker は保存済み 21 session で 21/21; rank 423〜424・t ≈ 55 秒からの直列は現行 tip の replica 1 走 (W 353.3 = O_max 281.0 + F 72.3) と参照受入 shard-0 の観測で、21 session の item 列は session ごとに異なり rank は 420〜430 / 374〜382)。L の内訳 (base 構築待ち 182 + copytree 4.6 + verify 27.1) は取り直したが wall を決めていない。式は `wall ≈ max(L の worker, 後方 rank の active_v2 系 key を建てる worker の列) + 固定費 (pre + post)` に書き直す。効果は {{T:acceptance-ledger-refresh-effect}} で先に測る (D1936 項 35)。5 分上限超過を受容しない。一次資料 `output/insights/2026-09-21/t2817-acceptance-bottleneck-3/README.md`。
  base: 409dc282d16b4e6c58070ae8827a2947fcb44278eebdaf34a7e3404bb29a1d72
- [T-2444] **P2・裁定パッケージ候補 (事実追記)**: 受入 `pre` の controller 側は早期 receipt memo prewarm (= 実 repo の `verify_receipt`、44〜58 秒) だが、worker 側の modify 複合区間 (shard plugin を載せた段で 45 秒) と並走して隠れており、`pre` は 2 本の長い方で決まる (T-2817 README §結論 3・§5 (b))。(a)〜(c) の verify 側の候補は memo prewarm の短縮に対応するが、D2185 で早期起動は現行維持。他方の所要・開始時刻を固定した場合、片方の短縮は他方の長さに達したところで頭打ちになる (構造の記述、両方の短縮が必要という断定ではない。worker 側は {{T:shard-plugin-modifyitems-cost}})。費用の増加だけでは D1728 を再訪しない。
  base: 456a2002cd39478f936a1b1cb0ff7c813c62d3e89f420ed09ea4944ef319bea8
- [T-2495] **P2・訂正の追記**: 最遅 shard (shard-0) の床は `test_t080_*` 群の L でも t080 の 11 consumer でもなく、ledger 未収載の active_v2 系 node を後方 rank で直列に抱えた worker の列 (T-2817 README §結論 1・§3.2)。短縮対象の優先度は {{T:acceptance-ledger-refresh-effect}} の実測に従って決め直す。
  base: fccc1fe2edf35873a3db7399be5e3620def99556c1b937211ff6f0ce68a6557c
- [T-2560] **P1・追認済み、第 3 回の実測を記録、次の実測待ち**: D1936 項 35 のとおり実測で律速を選んだ (T-2817 README)。次も実測で律速を選ぶ: ledger 再登録 ({{T:acceptance-ledger-refresh-effect}}) と modify 複合区間 ({{T:shard-plugin-modifyitems-cost}}) は効果を先に測り、未確認のまま実装しない。
  base: 9bf7e886b7d8d550a42ba5c874f147e6a1858bc793e2a2d805510870d56e8732

### 新規

- {{T:acceptance-ledger-refresh-effect}} **P1・新規**: D2107 の refresh mode で `acceptance_duration_ledger.json` を最新の緑走 1 走の JUnit から再生成し (T-2724 追加 node を含む未収載 334 unit の再登録)、同一 tip の実受入で隣接対 (A = 旧 ledger / B = 新 ledger、3 対以上、D357、T-2766 の事前登録の形) の shard-0 W / O_max / `O_max − L` / 最大占有 worker の item 列を測ってから land する (D1936 項 35)。参考値は別々に持つ: T-2817 README §5 (a) の model 差 19.5 秒 (固定所要 model、中央値のある未収載 333 node 全部を更新、実 wall の予測ではない) と、観測の `O_max − L` (保存済み 21 session の中央値 62.7 秒、Job B 65.0 秒 = 最大占有 worker と L の差であって再登録の効果ではない)。実効果は未測定で上下限も置かない。active_v2 系 key の base 構築が t=0 の 5 本と同時に走ると copy 配置が 100 秒級になり L 自身が伸びる可能性 (未測定) を対の判定に含める。
- {{T:shard-plugin-modifyitems-cost}} **P1・新規**: 受入 `pre` の worker 側 45 秒 (shard plugin を載せた段で現れる modify 複合区間、process 群の sys +2027 秒、Lustre `intent_lock` 11.7 倍) の内訳を関数別に計時する (probe は job dir、Codex author; 対象 = `tools/acceptance_shards.py` の `records_from_items` / `_canonical_item` の `Path.resolve()` (全 item に 2 回) / `allocate` / 選択、conftest の `_validate_real_repo_shard_state`)。同 job の段階載せ (T-2817 の S2/S3 形) で内訳が閉じてから、`records_digest` / `selected_digest` と受理集合を byte 不変に保つ縮約 (例: path 解決の回数を減らす) を設計し、効果は同 job 段階載せ + 実受入 隣接対で測ってから実装する。早期 memo prewarm (44〜54 秒) が並走しているので、`pre` は 2 本の長い方で決まる (T-2817 README §5 (b): 他方を固定した場合、worker 側の短縮は memo の長さに達したところで頭打ちになる) — 判定の読み方にこの構造 (`pre` ≈ max の 2 本) を事前登録し、worker 側の短縮量と `pre` の変化を別々に測る。
- {{T:shard0-post-ten-seconds}} **P3・新規**: shard-0 だけ終了後 (最後の test 終了 → session 終了) が約 10 秒 (保存済み 21 session で 10.0〜10.1、Job B replica 10.03、参照受入 10.03)、shard-1/2 は 3〜4 秒。候補 (xdist shutdown、shard plugin の `pytest_sessionfinish` の report 作成、conftest の memo session 終了、共有 base の atexit cleanup、JUnit 書出し) を計時で分ける診断。観測のみで実装なし。
