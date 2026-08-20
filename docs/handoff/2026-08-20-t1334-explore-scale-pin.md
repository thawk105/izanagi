# [T-1334] 探索経路 (ycsb-a/b/c) 3-sink 同時 byte pin テスト新設
- 目的: 探索路 `WORKLOADS["ycsb-a"/"b"/"c"]` (records=100_000, threads=4) が3 sink
  (campaign identity・PerfConfig・descriptor projection record) 全てへ同時に反映されることを
  byte 単位で pin する回帰テストを1本新設する (worklog archive 641 / 609-613行が一次資料)。
- 状態: 作業中
- 最終更新: 2026-08-20
- 基準コミット: 9fb5216624aed75a77ed9dff9760333e2cd2b9bb (worktree: dev-wave-t1334-explore-scale-pin)

## 完了した中間成果 (段1 brief)

**scope.** `orchestrator/tests/test_p3_autonomous_workload_trial.py` へ新設テスト関数 1 本
(`test_t1334_...`) を追記する。対象は `orchestrator/campaign/p3_autonomous_workload_trial.py` の
`WORKLOADS["ycsb-a"/"b"/"c"]` (218-234行、records=100_000/threads=4) が 3 つの sink 関数
(`_campaign_for` 710-762行→campaign identity、`_perf_for` 765-777行→`PerfConfig`、
`_descriptor_for` 780-793行→descriptor + projection record) 全てへ同時に反映されることを、
1 テスト内の 1 hash (または同時アサーション) で pin する。CCBench 非改変 (D16/D18/D20 対象外、
Python 側 orchestrator のみ)。

**既存被覆 (性質で先に検索済み、DW-S01 の純増検出力要件)。**
- `test_t1333_exploratory_entries_preserve_baseline_projection_bytes`
  (test_p3_autonomous_workload_trial.py:377-396): perf + descriptor + workload_flags を
  3 workload 分 combined-hash で pin 済み。**`_campaign_for` (campaign identity) を一切呼ばない。**
- `test_no_build_campaign_identity_binds_shared_policy_context` (355-374行): ycsb-a **だけ**の
  `A.ident.campaign_id(cfg)` (8hex truncated) を pin。b/c は未 pin。`ident.canonical_preimage(cfg)`
  (module 自身が「preimage」と命名する正準 JSON 文字列全文、ident.py:150-177) は
  どのテストも直接 pin していない。
- `test_t1333_all_three_sinks_use_the_same_synthetic_scale_entry` (399-420行): 3 sink の一貫性は
  確認するが records=123_457/threads=13 という **synthetic 値**であり、本番値 (100_000/4) の
  byte pin ではない。

**純増検出力 (2点)。**
1. ycsb-b/c の campaign identity は現在ゼロ被覆。新設テストが唯一の防壁になる。
2. records/threads/perf/descriptor/campaign-identity-preimage を「同一テスト内」で同時に束ねた
   pin は現状皆無 (被覆は独立 2 テストに分断)。`_campaign_for` 単体の回帰
   (例: search_config への `"records": records` 代入漏れ) は ycsb-b/c で検出不能な状態。

**DW-G05 (成果物影響、1行)。** 実装しない場合、探索経路の records/threads scale が
`_campaign_for` 内でのみ変質する回帰 (perf/descriptor 側は無傷) は ycsb-b/c で検出試験が無く、
規律4 (record 数を無造作に大きくしない) の防壁が探索経路の campaign identity では
事実上機能しない。

**不変条件。**
- 既存緑テスト非破壊。`test_t1333_*` 系 2 本は改変しない (別 ticket の着地済みテストを反転させない、
  memory `merge-must-not-revert-landed-design-tests`)。新設は追記のみ。
- records=100_000/threads=4 という値そのものは変更しない (pin が目的、値変更は別 scope=[T-1310]系)。
- SHA256 literal は実装子が実際に pytest を走らせて得た実測値を書く。仮定・生成した値をそのまま
  書かない (DW-S01: 自己 hash / pin 対象では模擬を裁定根拠にしない)。段6 で親が独立再計算し一致を
  確認する。

**(P1) 親の provisional 裁定 (段3 攻撃対象)。** 「campaign identity の preimage」は
`A.ident.canonical_preimage(campaign)` (正準 JSON 文字列全文) を使う。module 自身が「preimage」と
命名する関数を使うのが最も文字通りの解釈であり、truncated 8hex hash (`campaign_id`) は既に
別テストで ycsb-a のみ部分的に持っているため、それだけでは純増効果が薄い。

**変更面アンカー表 (file:line、現状 → 変更方針)。**
- `orchestrator/campaign/p3_autonomous_workload_trial.py:218-234` (`WORKLOADS`) — 読むだけ、無改修
- `orchestrator/campaign/p3_autonomous_workload_trial.py:710-793`
  (`_campaign_for`/`_perf_for`/`_descriptor_for`) — 読むだけ、無改修
- `orchestrator/campaign/ident.py:150-189`
  (`canonical_preimage`/`cfg_hash`/`campaign_id`) — 読むだけ、無改修 (参照専用)
- `orchestrator/campaign/s8b_descriptor.py:200-211` (`projection_record`) — 読むだけ、無改修
- `orchestrator/tests/test_p3_autonomous_workload_trial.py:63-66` (`_T530_CONTRACT`) — 再利用
- `orchestrator/tests/test_p3_autonomous_workload_trial.py:84-85` (`_no_build_context()`) — 再利用
- `orchestrator/tests/test_p3_autonomous_workload_trial.py:355-420`
  (`test_t1333_*` 2本、既存パターン) — 模写元、無改修
- **新規**: `orchestrator/tests/test_p3_autonomous_workload_trial.py` の397行目付近
  (T-1333 系 2 本の間または直後) へ `test_t1334_...` を1関数追記。fixed recipe
  (trial_id 固定文字列・generations=1・contract=`_T530_CONTRACT`・
  build_context=`_no_build_context()`) で ycsb-a/b/c 3 workload を回し、各 workload について
  `entry["records"]==100_000`/`entry["threads"]==4` の明示アサーション **と**
  `{campaign_preimage, perf, descriptor, descriptor_record}` を束ねた SHA256 pin の両方を持つ。

**並列分割方針。** 単一ファイル単一関数追記のため分割不要。実装子1本 (role=author) で足りる。

## 段2/段3 実績 (完了)
- 段2 codex plan (rc=0): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1334-explore-scale-pin/stage2-plan-output.md`。
  brief の純増検出力主張を再確認・肯定し、`test_t1334_exploratory_entries_pin_all_three_sink_bytes`
  という具体プランを起草した。
- 段3 敵対相談2レンズ (rc=0×2): `stage3-lensA-output.md` (sol、正しさ境界。real 0件、
  要ユーザー裁定1件=canonical_preimage全文 vs campaign_idのslug込み全体)、
  `stage3-lensB-output.md` (luna、整合・実効性・scope)。
  **レンズB が brief の中心主張 (ycsb-b/c の campaign identity はゼロ被覆) を反証する一次資料を発見**:
  `orchestrator/tests/test_autonomous_trial_completeness.py::test_t428_workload_campaign_epoch_and_old_root_nonwrite`
  (3578-3593行、ycsb-a/b/c を parametrize) が `_t428_descriptor_campaign_id` (228-245行) 経由で
  3 workload 全ての campaign identity を既に pin していた。
- 親が直接検証 (pytest は login ノード guard が拒否、`python3` で production 関数を直接呼ぶ
  独立 script を使用): `_CURRENT_POLICY_BOUND_CAMPAIGN_IDS` の3値 (ycsb-a/b/c) はいずれも
  ライブ計算結果と MATCH。`WORKLOADS["ycsb-b"]["records"]+1` 変異で campaign_id が変化することも
  確認 (script: `/home/SFC/tanab/.claude/jobs/3ee5bd2c/tmp/verify_t428_coverage.py`)。

## 段4 裁定: 実装しない (`4→7→8→9`)
`test_t1333_exploratory_entries_preserve_baseline_projection_bytes` (perf+descriptor) と
`test_t428_workload_campaign_epoch_and_old_root_nonwrite` (campaign identity) の和集合が、
3 workload 全てについて records/threads・campaign identity・PerfConfig・descriptor projection
record の pin を既に提供している。新設テストの純増検出力は失敗メッセージの読みやすさ以上のものが
無いと判断し、規律5 (盛らない) に照らし実装しない。詳細は worklog fragment
(`docs/spool/worklog/2026-08-20-dev-wave-t1334-explore-scale-pin-1.md`) 参照。

## 未完の作業と次の一手 (段7 続き)
1. 段7: 本 handoff・worklog fragment を commit (docs のみ、AI-Agent trailer 付き)。
2. 段8: 本 handoff の「dev-wave 改善候補」節を適用 (現時点で候補なし → 無言で通過)。
3. 段9: 受入全走が必須 (実装差分ゼロでも免除されない、DW-S04)。
   `tools/dev_wave_wait.py acceptance` で lease claim → `python3 tools/run_tests.py` を背景実行 →
   receipt 取得 → `tools/dev_wave_land.py` で local main へ ff-only land。
4. land 成功後、受入 lease を release し、`tools/collect_wave_usage.py` を実行。

## 落とし穴・気づき
- T-1283 の handoff (`docs/handoff/2026-08-20-t1283-launch-authority-design.md`) が「状態: 作業中・
  最終更新: 2026-08-20」のまま残っているが、対応する worktree
  (`.claude/worktrees/dev-wave-t1283-launch-authority-design`) は `git worktree list` に存在しない
  (branch `worktree-dev-wave-t1283-launch-authority-design` は残存)。本 wave とは編集面が
  完全に非重複 (T-1283 は受入 receipt 信頼境界の設計 docs、本 wave は探索路テスト新設) のため
  未介入。次にこの handoff を見るセッションは生死を再確認すること。
- `git worktree list` で campaign 設定 file (WORKLOADS/ycsb-a/b/c) を対象とする重複 worktree が
  無いことを確認済み (既存 worktree は t1142/t1337/t183×2/t338/t425/humble-questing-lerdorf/
  t1363-c06、いずれも無関係)。

## dev-wave 改善候補 (段8で裁定、気づき次第追記)
(現時点で候補なし)
