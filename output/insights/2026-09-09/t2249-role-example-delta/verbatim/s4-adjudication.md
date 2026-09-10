# 段 4 裁定 — [T-2249] role 入力例の `delta_pct: -1.2`

裁定 inbox 再走査: local main は wave 開始時の `cbcdb6c91bd2eced76bd6a82650204c357c1b299` から動いていない。
wave 開始後に着地した裁定は無い。

## 裁定 1 — (P1) を撤回する。planner も削除ではなく `null` にする

**lens A 所見 #2 = real。親が独立に検算して確認した。**

`git grep -n last_delta_pct -- docs/` の実測:
- `docs/phase3-s4b-runbook.md:45` — `"current_perf": {..., "last_delta_pct": null}`
- `docs/phase3-s5-sort-runbook.md:44` — 同じ

つまり `last_delta_pct` は**存在する field** である。メインセッションが段 4b / 段 5 / 段 8a の手作業射影で
`null` として渡す。`D118` 残余 (b) が「存在しない `last_delta_pct`」と書いたのは、その後 runbook 側へ
`null` が入ったため**現在は誤り**である (親の当初の検索は `docs/` を範囲外にしていたので同じ誤りを継いだ)。

したがって行削除は role を 2 本の live runbook と乖離させ、runbook の同時編集まで scope を広げる。

**確定: `.claude/agents/planner-v4.md` の `"last_delta_pct": -1.2` を `"last_delta_pct": null` にする。**
行は削除しない。`:34` の comma も触らない (plan の 2 行編集案は不採用)。

これで (a) 本題の `-1.2` は消える、(b) role と runbook の射影形が一致する、(c) 不正 JSON の risk が消える、
(d) 兄弟 role の `null` と対称になる。

**帰結 — plan と lens が計算した planner 側の hash literal は全部無効である。**
`523b83...` (source)、`8721278d...` (semantic_digest)、`1b0949...` (adapter file)、byte 数 8501 は
いずれも「行削除」前提の値である。coder 側の `ba6c9c11...` は `-1.2`→`null` 前提なので生き得るが、
**実装子は 5 値すべてを自分で計算する。他文書の literal を写してはならない。**

## 裁定 2 — pin 閉包の件数を訂正する

**lens B 所見 = real。** `git grep -c` は巨大 1 行 JSON を 1 hit としか数えないため、親の「6 hit」は誤り。
実際の literal 出現は coder 旧 sha 3 件、planner 旧 sha 10 件 (adapter 2 + ledger 1 + originless baseline 7) の
**計 13 件**。baseline 内訳は `journals/*/*/provenance/role_file_sha256` に 6、
`reports/*/cells/*/generations/*/roles/planner/provenance/role_file_sha256` に 1。

閉包はこの 4 系統で閉じる。lens B が独立に走らせた探索 (旧 source sha / 旧 semantic digest /
現 adapter 全体 sha の grep、role 名・対象 4 path・`last_delta_pct`・`delta_pct` の検索、
`xdist_group` 検索、現 byte 数と行数の検索) で追加の bytes pin は hit 0。
`FROZEN_MANIFEST` 23 key は全て `output/` 配下で対象を含まない (lens B が検算)。

## 裁定 3 — scope を 6 file に確定する

| # | file | 実装面 (D95) | 変更 |
|---|---|---|---|
| 1 | `.claude/agents/coder-v4-autonomous.md` | 否 | whiteboard 例の `delta_pct` を `null` へ |
| 2 | `.claude/agents/planner-v4.md` | 否 | `current_perf.last_delta_pct` を `null` へ |
| 3 | `orchestrator/codex_roles/review_ledger.py` | **是** | `SOURCE_FILE_SHA256` の 2 entry |
| 4 | `.codex/role-adapters/coder-v4-autonomous.json` | **是** | 期待 bytes へ再生成 |
| 5 | `.codex/role-adapters/planner-v4.json` | **是** | 期待 bytes へ再生成 |
| 6 | `orchestrator/tests/test_reflux_originless_compatibility.py` | **是** | T-2249 追随 helper (planner 7 leaf) |

実装面 4 file があるので段 5 の Codex `role=author` は省略不可。親は実装面を直接編集しない。

## 裁定 4 — (P2) は分類を訂正して維持する。新規 semantic test は採用しない

**lens A #5 / lens B = real。** 全 surface を協調して旧 bytes へ戻すと既存検査は通る。
既存検査は例の `delta_pct is None` / `last_delta_pct` の値を独立に pin していない
(`tools/check_codex_agents.py:169-173` の shape 検査は open object の内部を見ず、coder の
`whiteboard` schema は items 定義を持たない)。

分類は「等価変異」ではなく **`SURVIVED / non-equivalent / semantic guard absent`** とする (lens A の訂正を採用)。

**lens B が提案した新規 semantic test 2 本は採用しない。** 依頼が
「仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」と明示している。real 所見として
裁定パッケージへ返す。

**この SURVIVED は既に実測済みである。** wave 開始時、未変更の worktree で
`tools/check_codex_agents.py` が rc=0 だった。旧 bytes の協調状態が全検査を通ることは
その 1 走で観測されている。追加の変異走行は要らない。

**記録の義務:** worklog と insight に「独立 semantic gate は無く、人間 review pin に依存する」と書く。
材料レポートで「例の不変を durable に certify した」と主張しない。

## 裁定 5 — 研究前進の主張を限定する

**lens A #1 / #3 = real。** brief の書き方は過大だった。訂正して段 7 に記録する。

- **「runtime leak を閉じた」と言わない。** `-1.2` は固定の説明例で、ある trial の実測 delta ではない。
  D118 決定 (3) のとおり `delta_pct≡None` の防壁は whiteboard 射影経路の `delta_pct` field だけであり、
  `current_perf.last_delta_pct` はその関所を通らない。言えるのは
  **「段 4 の `delta_pct≡None` 不変と食い違う固定例を role の入力契約から除いた」**まで。
- **「毎試行の因果入力」と一般化しない。** headless provider
  (`orchestrator/campaign/claude_projected_provider.py:150-170`) は role body を effective prompt へ
  埋めるので因果入力になる。しかし originless compatibility test の `FixtureRoleProvider` は
  role bytes の sha を記録するだけで返答は hard-code である。よって baseline 追随が必要な事実は
  「provenance consumer が実在する」ことの証拠であって、「role 本文が出力へ因果的に作用した実績」の
  証拠ではない。lens A は current planner sha を持つ保存済み `attempts.jsonl` / `report.json` を
  `output/exploration` 配下で見つけられなかった (静的検索、実走なし)。

## 裁定 6 — scope 外に出す real 所見 (裁定パッケージへ返す)

1. coder 例が 3 field で実射影が 5 field という drift (lens A #4、兄弟 `-sort` / `-trigger-gating` も同形)。
2. lens B 提案の semantic test 2 本 (裁定 4)。
3. `docs/phase3-s8c-autonomous-trial-runbook.md:233-235` の「前世代から更新した current_metrics を
   次世代へ渡す」が実装 (`_INITIAL_ROLE_METRICS` を workload ごとに freeze して後続世代へ同じ snapshot を
   返す) と食い違う (lens A #2 が発見)。別 erratum。
4. `D118` 残余 (b) の残り 2 件 (planner の「leading-indicators だけ」、coder の「入力は 5 field のみ」)。

## 裁定 7 — 変異事前登録 (DW-M01。実装前に確定)

anchor は段 6 fix 後の最終 commit で再検証する (DW-M07)。

### 主集合 (単一理由。KILLED を単独帰属できる)

| id | 変異位置 | 期待赤 node (完全集合) |
|---|---|---|
| M4-C | `.codex/role-adapters/coder-v4-autonomous.json` の `source/sha256` だけ旧値へ | `orchestrator/tests/test_codex_agents.py::test_current_sources_render_byte_exact_and_native_is_empty` |
| M4-P | `.codex/role-adapters/planner-v4.json` の `source/sha256` だけ旧値へ | 同上 |
| M5-C | `.codex/role-adapters/coder-v4-autonomous.json` の `semantic_digest` だけ旧値へ | 同上 |
| M5-P | `.codex/role-adapters/planner-v4.json` の `semantic_digest` だけ旧値へ | 同上 |
| M6 | `orchestrator/tests/test_reflux_originless_compatibility.py` の T-2249 追随 helper 呼出しを除去 | `orchestrator/tests/test_reflux_originless_compatibility.py::test_originless_default_preserves_every_nonvolatile_leaf_and_closed_key_set` |

M4 / M5 は renderer の byte parity が唯一の拒否層。M6 は baseline overlay だけが理由。

### 冗長 gate (KILLED 期待だが 2 層が同時に発火するので単独帰属しない。DW-M03)

| id | 変異位置 | 期待赤 node (完全集合) |
|---|---|---|
| M2-C | `.codex/role-adapters/coder-v4-autonomous.json` の `developer_instructions` 内の埋め込み本文だけ旧例へ | `test_current_sources_render_byte_exact_and_native_is_empty`, `test_source_body_is_embedded_exactly_once_before_product_override` |
| M2-P | `.codex/role-adapters/planner-v4.json` の同箇所 | 同上 |

### 登録しない (lens B が単一理由性を否定した。DW-M01 の証拠に使えない)

- M1-C / M1-P (source md + ledger pin の協調 rollback。3〜4 層が同時発火)
- M3-C / M3-P (adapter の `review_ledger/source_file_sha256` だけ。2 層発火だが M2 と同じ層の組で情報が増えない)

### 期待 SURVIVED (変異走行では回さない。裁定 4 の実測で足りる)

- M-SEM-C / M-SEM-P: 全 surface の協調 rollback → `SURVIVED / non-equivalent / semantic guard absent`

## 裁定 8 — 受入と実測環境

login node で `tools/dev_wave_wait.py acceptance` の全走。計算ノード job は不要。
実装子には focused 走として次を要求する (plan + lens B の consumer 拡張を採用)。

```text
orchestrator/tests/test_codex_agents.py            (file 全体)
orchestrator/tests/test_codex_role_runtime.py      (file 全体)
orchestrator/tests/test_reflux_originless_compatibility.py
orchestrator/tests/test_p3_s4_loop.py
orchestrator/tests/test_p3_autonomous_workload_trial.py
```

加えて `tools/check_codex_agents.py` と `tools/check_docs.py`。

## 不変条件 (再掲。緩めない)

- `orchestrator/campaign/p3_s4_loop.py` を変更しない。`_DELTA_PCT_LIVE=False` と
  `WhiteboardLeakError` の二重 fail-closed、`s8c_generation_projection.validate_whiteboard()` の
  exact 5-key / `None` 検査は不変。
- 既存テストの期待値を変更しない。`_PRE_WAVE_ORIGINLESS_BASELINE` の literal と既存
  `_extend_t1353_*` / `_extend_t2145_*` helper を変更しない。
- role の frontmatter、adapter の `runtime_activation` / `mode` / `consumer` を変更しない。
- 過去の trial 記録 (`attempts.jsonl` / `report.json` の旧 `role_file_sha256`) を書き換えない (規律 7)。
- `output/insights/` の歴史記録 (`-1.2` を含む 4 file) を追随編集しない。
