# 段 4 裁定 — [T-2766] 採用 wave (dev-wave-t2766-pairing-adopt)

2026-09-20 13:5x JST。軽量版 (DW-C00): 段 2・3 は省略。攻撃対象 (P1)〜(P5) は親の provisional 裁定のまま採用し、段 6 の read-only レビュー 1 本で再検査する。裁定 inbox (`rulings-inbox/2026-09-20-*`) に T-2766 の新事実なし (13:4x の控えは起動待ち一覧への言及のみ)。

## 裁定

| # | 内容 | 裁定 |
|---|---|---|
| P1 | property は残し、env 定数 / token / `_acceptance_pairing_opted_in` / allowlist 行を撤去。opt-out を足さない | 採用 (scope 内) |
| P2 | A 側 witness は取らない (A = 採用前 main を保つ) | 採用。B 側 witness は毎走検証 |
| P3 | land 条件 = 有効 3 対すべて ΔW > 0 かつ med r ≥ 10 % | 採用 (事前登録、brief §事前登録) |
| P4 | A 測定木は別 worktree (`worktree-dev-wave-t2766-pairing-adopt-a`、main 起点)、land しない | 採用 |
| P5 | 段 5 author 1 本 + 段 6 レビュー 1 本 (+ 必要時 fix) + 変異 + 受入 | 採用 |

## plan v2 (author への確定仕様)

brief §変更面の実アンカー表のとおり。追加の確定事項:

1. `_reorder_acceptance_items_by_duration(items, durations, workerid="")` の署名は保つ (G6/G10 の tracer が 2 引数で包む箇所は `workerid=""` を受ける形へ)。pairing は `ordered_units` 確定直後に無条件で `_pair_initial_distribution_units(ordered_units, unknown_cost)` を呼ぶ。unit < 96 は無変更・property 無し (関数内の早期 return を保つ)。
2. hook (`pytest_collection_modifyitems`) は分岐を畳み、常に `workerid=getattr(config, "workerinput", {}).get("workerid", "")` を渡す。controller (workerinput 無し) では `""`。
3. `_ACCEPTANCE_PAIRING_PROPERTY_PREFIX` / `_ACCEPTANCE_PAIRING_HEAD_UNITS` と property 4 種 (scope / rank / partner / worker、全 item、pairing 適用走のみ) は不変。
4. `tools/pegasus/dispatch_compute.py` と `test_pegasus_dispatch_compute.py` は main (`947fd160a`) の内容へ戻す (差分ゼロ)。
5. G12 の書き直し: (a) 正例 = env 無しで dequeue_trace[:48] 不変・[48:96] = 固定 partner 列・rest 元順・property 4 種 (期待値は fixture から独立に固定、本番 helper から算出しない)。(b) 既定 on の負例 = 旧 env `IZANAGI_ACCEPTANCE_PAIRING_V1` に任意の値 (例: 旧 token、"off"、"0") を設定しても collection 列・property が正例と同一 (env を読まない)。`_PAIRING_ENV`/`_PAIRING_TOKEN` 定数と autouse fixture は削除。(c) invalid token 負例は削除。(d) cardinality 負例、短 queue (unit < 96 → 無変更・property 無し)、worker 数非依存 (16/32/48)、junit 到達 (pytester `-n 1 --dist loadgroup`、skip にも property、worker = gw0)、hold / selected / real-repo suffix 保全 (enabled param を既定 1 本に)、配布反例は保つ。
6. G8: 不変条件「unknown は 96 位の known cost に同値で直後に置かれる、known ゼロは no-op (replacements 0)」を落とさず、pairing 後の観測順で成立する形へ (例: `_pair_initial_distribution_units` を monkeypatch で恒等にして cost 順を観測する場合は、その test が pairing を検査していないことを docstring に書く。または pairing 後の期待位置を fixture から独立に導いて固定する)。
7. 集計器 `probe-t2766-adopt/t2766_adopt_analyze.py` (unit worktree に書く、repo へ入れない、標準 library のみ、`--selftest` を持つ): 入力 = `--runs-root <dir>` (各 `runs/<NN>-<A|B>/run.json` = 親が書く {arm, tag, tested_main, tip_before, tip_tested, started, finished, rc, session_root, leaders_at_go, load1_at_go} と `session/shard-{0,1,2}/{junit.xml,report.json}` の写し) と `--ledger <台帳 json>`。出力 (`--out <dir>`: `analysis.json` + `analysis.md`) = 走表 (shard ごと W/O/F、最忙 worker items/duration、W_max と argmax)、対表 (順序どおりの隣接対、ΔW、r、D357 注記、対内 main 移動の有無)、3 種の中央値、B の witness (property 被覆、rank 48〜95 = partner 集合、head (cardinality, cost) 多重集合 / partner cost 多重集合の独立再計算)、tip / 順序 / 有効性の検算、事前登録の判定 (i)/(ii)/(iii)。item 列の全件出力はしない (compact)。

## 変異 matrix (DW-M01、位置と帰属)

| # | 変異 (1 理由) | 位置 | kill を帰属させる検査 |
|---|---|---|---|
| M1 | partner 選択の sort key を昇順 → 降順 | `_pair_initial_distribution_units` の `sorted(候補, key=(cost, pos))` | G12 正例: 固定 partner 列の不一致 |
| M2 | head 幅 48 → 47 | 同関数 `width = _ACCEPTANCE_PAIRING_HEAD_UNITS` | G12 正例: head の完全一致と partner 境界 |
| M3' | pairing 呼び出しを削除 (常に off) | reorder 関数の `ordered_units = _pair_initial_distribution_units(...)` | G12 正例 / junit 到達: 既定で発火しない |
| M4 | cardinality 検算を削除 | 同関数の検算 `if` | G12 cardinality 負例: `UsageError` が出ない |
| M5 | property 付与を削除 | reorder 関数の `if "pairing_rank" in unit:` | G12 正例 / junit 到達: property 4 種の欠落 |

runner = `python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_acceptance_schedule_order.py -q -rf` (計算ノード)。独立 clone (D1009)。各変異は単独適用、baseline 緑を先に確認。

## 段 5 / 6 / 受入の構成

- 段 5: author 1 本 (workspace-write、unit worktree `.codex/worktrees/t2766-adopt-unit-impl`、X1 = main + cherry-pick `0eabe67ba` 起点)。親: patch 抽出 → wave 木へ適用 → 焦点走 (計算ノード: schedule_order / dispatch_compute / hold_inventory / run_tests_shards / real_repo_serialization / run_tests_preflight) → 実装 commit (X2)。
- 段 6: read-only レビュー 1 本 (受理集合不変・test 弱体化・G8 の不変条件保持・変異帰属・集計器の独立性) → 必要時 fix → 変異 matrix → A/B 実受入 3 対 (待ち手経由、門番 loop) → 判定。
- land: (i) 成立時だけ。B の最終走の receipt を使う。A 木は撤去 (land しない)。

## 追補 (段 6 レビュー後、測定結果を見る前に固定、2026-09-20 14:1x JST)

レビュー A (過剰・削除) は must-fix 2 / should 4、レビュー B (正しさ・整合) は must-fix 1 / should 2。**本番 patch (X2 `2404642c3`) への must-fix は両レビューとも無し** (受理集合不変・env 非読取・G8/G12 の検出力・M1〜M5 の帰属は静的に成立)。code fix は投じない。裁定と追補:

| # | 所見 | 裁定 | 対応 |
|---|---|---|---|
| A1 / B1 | 集計器の入力が段 4 §plan v2 項 7 の略記 (`arm / tip_tested / started / leaders_at_go …`) と一致しない | real だが親の生成器 (`write_run_json.py`) と集計器は author prompt §4 の契約で一致している。段 4 の略記が古い | 契約を本追補で確定 (下記)。親が前 wave の A session を流用した接続確認 (`contract-test/`) で有効走・W_max 454.716 を再現し、事前登録の判定枝 (反復不足) まで通した |
| A2 | `PYTHONDONTWRITEBYTECODE_SET != "no"` の除外が事前登録に無い | real | 事前登録に **launcher の env 契約**として追加: 両 arm とも `run-acceptance.sh` が `PYTHONDONTWRITEBYTECODE` を unset して投入し (計算ノードの bytecode cache を両 arm で同じ warm 状態にする、前 wave §4 と同じ)、その記録 `PYTHONDONTWRITEBYTECODE_SET=no` を有効走の条件に含める。unset 漏れは launcher の欠陥で、その走は無効 (測定条件違反) |
| A3 | main 移動を許す運用と「B = A + 採用 commit」の説明が一致しない | real (should) | A/B を「各走の tested_main に対する採用前 / 採用後」と定義し直す。対内で tested_main が異なる対も有効だが `main_moved` を対表に出し、親が両 tip の差分 (採用 commit 以外に main 側で何が入ったか) を README に書く |
| A4 / B2 | 門番・他 wave の干渉の記録 | real (should) | 投入時 (`other_leaders` / `load1`) に加え完了時 (`other_leaders_at_finish` / `load1_at_finish`) を launcher が記録、門番 loop の `series.log` (100〜140 秒周期の leader / load / pigz) を条件差の一次記録にする。走行中の干渉は連続観測ではない (未観測と明記) |
| A5 | 測定量の限定 | real (should) | 測定量 = 最遅 shard の JUnit testsuite time (W_max)。queue 待ち・claim・merge・receipt を含む受入総経過時間ではない。前 wave の 101.7 / 112.9 / 144.3 秒 / 24.2 % は同じ量の限定的観測で、総経過時間へ換算しない |
| A6 | P1 の費用「数百 KB」 | real (should) | 「数百 KB / shard は前 wave の概算、時間費用・consumer 全体への影響は未実測」と限定。本 wave の走から junit.xml の byte 数を A/B で記録する (追加計測はしない) |
| B3 | cardinality 検算の完全性は nodeid 一意性が前提 | real (should、X1 からの既存境界) | README に「受入 collection の nodeid が一意」という前提を明記。重複 nodeid の反例 (レビュー B の fixture) は既知の境界として記録し、gate は足さない |

### run.json の契約 (親 `write_run_json.py` → 集計器 `t2766_adopt_analyze.py`)

`runs/<NN>-<A|B>/run.json`: `run` (NN)、`condition` (A|B)、`pair_slot`、`tip_sha` (= receipt の `tested_tip`)、`tip_before`、`tip_after`、`tested_main` (receipt)、`main_sha_at_launch`、`submitted_at` / `finished_at` (`%Y-%m-%dT%H:%M:%S%z`)、`session_dir` = "session"、`session_dir_origin`、`copy_ok`、`env.IZANAGI_ACCEPTANCE_SHARDS` = "3"、`env.PYTHONDONTWRITEBYTECODE_SET` ("no" が有効条件)、`other_leaders` / `load1` (投入時)、`other_leaders_at_finish` / `load1_at_finish`、`rc`、`verdict` ("child-green" が有効条件)、`child_rc`、`red_nodeids`、`dirty_lines_before` / `dirty_lines_after` (0 が有効条件)、`receipt_file`。`session/shard-{0,1,2}/{junit.xml,report.json}` + `SHA256SUMS`。CLI: `--runs-root --ledger --out --a-tips <sha,…> --b-tips <sha,…>` (親が git で検証した各 arm の許容 tip 集合: A = main の履歴上の commit または A 木の merge commit、B = X2 を含む commit)。

### 変異 (段 6 で確定、probe 走で観測 node を集めてから final を登録)

M1〜M5 は段 4 のとおり。M3' の期待 node はレビュー B の予測 10 node (G12 の 9 test + legacy env 4 値) を probe の観測と照合して登録する。runner は `test_acceptance_schedule_order.py` 1 file (dispatch_compute の変異 M6 は撤去に伴い無し)。
