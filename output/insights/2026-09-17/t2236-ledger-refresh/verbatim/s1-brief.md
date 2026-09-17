# 親 brief (段 1、dev-wave [T-2236])

## 段 1 brief (親)

- **研究前進 (土台):** 受入全走は全 dev-wave の関門で、shard 偏り (shard-0 が 344〜351 秒、他 2 つが 201〜245 秒)
  は毎 wave の待ち時間になる。台帳の陳腐化 (実測直列和 8852 / 4433 / 4519 秒に対し台帳予測 5701 / 5700 / 5700 秒)
  が原因なので、台帳を実測へ戻せば割付器 (LPT、変更なし) がそのまま均す。完了判定: 台帳が現行 collection
  24568 node の 99.2% を実測値で覆い (現状 93.6%)、T-1574 pin と被覆 gate が緑、受入 1 走で shard 別 wall を
  before / after として記録。300 秒達成の保証はしない。
- **scope:** (1) `tools/update_acceptance_duration_ledger.py` へ refresh mode を 1 つ足す — 凍結 8 prefix
  (`_ADD_ONLY_FROZEN_SUITE_PREFIXES`) の既存 entry を値ごと保持し、それ以外の entry を入力 JUnit から全再生成
  (値の置換・非凍結の旧名の削除・新名の追加)。凍結 prefix の JUnit entry は足さない。既存の `--add-only` /
  全再生成 / `--check` / `--coverage-against` は不変。(2) 同 mode の正例・負例を
  `orchestrator/tests/test_update_acceptance_duration_ledger.py` へ。(3) 台帳を同 mode で `d3ebafc0…` の
  3 shard JUnit から再生成 (Codex author、D95)。(4) 受入 1 走で shard 別 wall を記録。
- **scope 外:** scheduler / 割付器の変更、test 隔離基盤、T-1903 (pin の述語化)、閾値 0.90・凍結 prefix・除外集合の
  変更 (F902、規律 2)、`--coverage-against` が collection 出力の `IZANAGI_GROWTH_HOLD_V1` marker 行 (`::` を含む)
  で rc=2 になる件 (本 wave は marker 行を除いた nodeid 一覧を渡す。backlog として記録)。
- **確定済み裁定:** D746 (台帳は順位のみ・受理判定に使わない)、D1152 / D1219 (全再生成は却下、node 集合は基準時点
  の exact identity、所要値は述語へ = T-1903 未実施)、F684 / F902 (手編集禁止、正本 producer で作る、閾値・凍結
  prefix・除外集合は触らない)、D357 (受入 wall の主張は 3 走中央値。1 走差 10% 未満は「変化なし」)、
  D2104 (道具は受理述語を変えずに直す)。
- **不変条件:** (a) T-1574 の 8 suite node 集合 identity・12 値・removed 5 件の不在は 1 byte も動かない。
  (b) 台帳の全 entry は JUnit の `time` (量子化済) か既存台帳の凍結 entry のどちらか — 値の合成なし。
  (c) 閾値・凍結 prefix・除外集合・consumer (`conftest.py` / `tools/acceptance_shards.py`) は不変。
  (d) JSON の手編集なし。(e) 台帳は HEAD blob 束縛 (F902) なので焦点走の前に commit する。
- **割れうる前提 (攻撃対象):**
  - (P1) 「既存の生成器を使い、新設はしない」は「新しい生成器 script を作らない」の意味で、既存生成器への mode 追加は
    その内側。根拠: 既存 2 mode (全再生成 = T-1574 を壊す、`--add-only` = 既存値を保持し陳腐化を直せない) では
    主因 (既存 node の値の陳腐化 +3151 秒) を直せない実測。
  - (P2) 入力は `d3ebafc0…` (06:31、rulings-all-20260917 = main 相当、0 fail / 0 error) の 1 走 3 shard だけ。
    生成器は入力間の重複 nodeid を拒否するので 4 走の結合は不可。同走の node 集合は現行 main の collection と
    完全一致 (差 0 / 0)。
  - (P3) 凍結 8 suite の stale 18・未登録 207 は据え置く (D1152 の帰結)。refresh 後の被覆は 24379 / 24568 = 99.16%。
  - (P4) 受入 after は 1 走の観測記録に留め、改善・退行を主張しない (D357)。
  - (P5) refresh mode の出力は全再生成と同じ canonical 描画 (sort_keys)。凍結 entry は `json.dumps` の往復で
    同じ text になる (T-1574 の比較は数値等価)。add-only が先頭挿入した非 sort 順は refresh で消える。
- **成果物:** 生成器 + test (Codex author)、再生成した台帳 (Codex author が producer を回す)、insight README
  (before / after の実測、集合差、変異 matrix)、worklog / spool fragment。
- **並列分割:** 実装は author 1 本 (生成器 + test + 台帳生成は同一 file 群で分割不可)。段 6 レビュー 2 本並列。
- **変更面 (実アンカー):** `tools/update_acceptance_duration_ledger.py` `_parser` (argparse)、`_add_only_result` の
  隣に refresh 関数、`main` の分岐と print 行、`_existing_ledger` を再利用。
  `orchestrator/tests/test_update_acceptance_duration_ledger.py` の `test_add_only_preserves_existing_entry_bytes_and_excludes_frozen_nodes`
  (L515) を型として refresh の正例・負例を追加。`orchestrator/tests/acceptance_duration_ledger.json` は producer 出力。
- **受入・実測環境:** 計算ノード (Pegasus、`tools/dev_wave_wait.py acceptance --lease-optional`)。焦点走は
  `test_update_acceptance_duration_ledger.py` + `test_acceptance_schedule_order.py` (被覆 gate、F902) + `test_paper_story_a1_headline.py`。

## 段 1 で実測した事実 (handoff から転記)

- 直近の緑 4 走 (session / 投入元 / shard-0,1,2 の wall 秒):
  - `6571431e…` t2067 / 344.3, 236.3, 201.5
  - `fdcea8be…` t1449 / 348.6, 245.2, 205.4
  - `35fa0ca1…` t2723 / 348.3, 241.7, 210.7
  - `d3ebafc0…` rulings-all-20260917 (main 相当、06:31) / 351.0, 238.5, 202.7
- `d3ebafc0` を現行台帳で解析: 台帳予測の shard 負荷は 5701 / 5700 / 5700 秒で均等。実測の直列和は
  8852 / 4433 / 4519 秒。= 台帳値の陳腐化が原因で、割付器 (LPT) 自体は予測どおり均等に割っている。
- 陳腐化の主因は凍結 8 suite の外: `test_s8b_oracle_driver.py` (+2126 秒、shard-0)、
  `test_s8b_floor_campaign.py` (+1289 秒、shard-0)。凍結 8 suite 合計の差は -334 秒 (過大評価側) で小さい。
- 未登録 node は shard-0 で 459 件・実測 678 秒 (1.0 秒/件で予測 459 秒) → 未登録だけでは差の 1 割未満。
  重い未登録: `test_s1_known_axes_freeze.py::test_historical_oracle_nonadapter_reaches_current_semantics` 159 秒、
  `test_s8b_oracle_driver.py::test_t080_shared_base_builds_real_builder_once_across_processes` 153 秒。
- 生成器の既存 mode: 全再生成 (凍結 pin を壊す、D1152 却下) と `--add-only` (既存値を byte 保持・追加のみ =
  陳腐化した既存値を直せない)。**既存 2 mode のどちらでも本件の主因 (既存 node の値の陳腐化) は直せない。**
