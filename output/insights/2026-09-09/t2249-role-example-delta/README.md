# [T-2249] role 入力例の `delta_pct: -1.2` を段 4 の `None` 契約へ揃えた

- wave: `dev-wave-t2249-role-example-delta`
- branch: `worktree-dev-wave-t2249-role-example-delta`
- 起点 local main: `cbcdb6c91bd2eced76bd6a82650204c357c1b299`
- 統合 commit: `cd20f10b5049b14690ba68f041410b8ea3188c6d`

## 何を直したか

段 4 の loop (`orchestrator/campaign/p3_s4_loop.py`) は whiteboard の `delta_pct` を常に `None` に保ち、
非 `None` を `WhiteboardLeakError` で fail-closed する (`_DELTA_PCT_LIVE=False`、射影
`whiteboard_for_planner` と load 側 `state_from_dict` の二重)。ところが 2 本の role 定義の入力例には
固定値 `-1.2` が残っていた。兄弟 role (`-sort` / `-trigger-gating` / `-k2`) は T-2200 で `null` へ
直したが、bytes 凍結と K0/K1 対照のため既存 2 本は触らず裁定へ送られていた。

変更は入力例の値 2 箇所と、その bytes を pin する閉包の追随だけである。

| file | 変更 | 実装面 (D95) |
|---|---|---|
| `.claude/agents/coder-v4-autonomous.md` | whiteboard 例の `delta_pct` → `null` | 否 |
| `.claude/agents/planner-v4.md` | `current_perf.last_delta_pct` → `null` | 否 |
| `orchestrator/codex_roles/review_ledger.py` | `SOURCE_FILE_SHA256` 2 entry + Reviewed 注記 | 是 |
| `.codex/role-adapters/coder-v4-autonomous.json` | 期待 bytes へ再生成 (9719 bytes) | 是 |
| `.codex/role-adapters/planner-v4.json` | 期待 bytes へ再生成 (8532 bytes) | 是 |
| `orchestrator/tests/test_reflux_originless_compatibility.py` | T-2249 追随 helper | 是 |

新 sha256: coder `ba6c9c116fadf0d21a3e55acf1fdcaf83c412c869fcbfdf59dfad842cbfcf806`、
planner `3a3d35fafbaaeac5b63c8f36a1cd4542fba4e7cef2793c71cc59fc40884c8374`。
親が `sha256sum` で独立に検算した。

## 段 3 の敵対相談が親の裁定を 2 件反証した

いずれも親が独立に検算して確認した。

### 1. `last_delta_pct` は「存在しない field」ではない — 削除案を撤回した

親の段 1 brief と (P1) 裁定は、D118 残余 (b) の「存在しない `last_delta_pct`」を引き継いで
**field ごと削除**するとしていた。段 3 のレンズ A が反証した。

- `docs/phase3-s4b-runbook.md:45` — `"current_perf": {..., "last_delta_pct": null}`
- `docs/phase3-s5-sort-runbook.md:44` — 同じ
- 段 8a の runbook は段 5 を継承する

つまりメインセッションが手作業射影で **`null` として実際に渡している**。D118 が書かれた時点より後に
runbook 側へ入ったため、その記述は現在は誤りである。**親の当初の検索が `docs/` を範囲外にしていたため
同じ誤りを継いだ。**

削除すると role が 2 本の live runbook と乖離するので、`null` へ揃える案に変えた。副産物として
段 2 plan が指摘していた「行削除だと直前の trailing comma が残り不正 JSON になる」問題も消えた
(`tools/check_codex_agents.py` の `_source_json_example` が入力例を `json.loads` する)。

**この撤回により、段 2 plan と段 3 レンズが計算した planner 側の hash 5 値
(source sha / semantic_digest / adapter file sha / byte 数) は全部無効になった。** 実装子には
「他文書の 16 進値を写すな、自分で計算せよ」と明記して渡し、親も独立に検算した。

### 2. pin 閉包の件数が誤りだった — `git grep -c` は巨大 1 行 JSON を 1 hit としか数えない

親は「bytes を pin する箇所は 3 系統 6 hit だけ」と断定していた。レンズ B が反証した。
旧 planner sha は `orchestrator/tests/test_reflux_originless_compatibility.py:372` の
`_PRE_WAVE_ORIGINLESS_BASELINE` (物理 1 行の巨大 JSON) の中に **7 回**ある
(`journals/*/*/provenance/role_file_sha256` に 6、
`reports/*/cells/*/generations/*/roles/planner/provenance/role_file_sha256` に 1)。
literal 出現の実数は coder 3 + planner 10 = **13 件**である。

さらに親は「この凍結 baseline は `output/` 保存済み journal の中の値なので role file 編集では動かない」
と書いていた。これも誤りで、同 test は保存済み `output/` を読まず `A.run_trial()` を**実走**して
journal を作る (`:60-105`)。したがって live な `planner-v4.md` bytes の sha が baseline に届く。
T-2145 で auditor の source pin を追随させた先例が同 file `:574-595` にあり、同型の T-2249 helper を足した。

**教訓: 件数を断定する前に、`git grep -c` ではなく `grep -o | wc -l` 系で数える。
巨大 1 行 JSON を持つ file では前者が桁違いに少なく出る。**

## Codex 実装子は `.codex/**` へ書けない (実測)

`codex exec --sandbox workspace-write` の子は、作業 root が `.codex/worktrees/<name>` のときも
`.claude/worktrees/<name>` のときも、`<root>/.codex/role-adapters/*.json` への書込みを
`patch rejected: writing outside of the project; rejected by user approval settings` で拒否し、
`test -w` も rc=1 を返した。**2 つの異なる作業 root で再現したので path 依存ではなく、
codex が `.codex/` を自身の設定領域として書込禁止にしている構造的制約である。**

迂回は禁じた。実装子には「書けないなら報告して次へ進め」と指示し、実際にそう報告させた。
adapter 2 件は親が repo 自身の `expected_adapters()` の出力で render し、
`AI-Agent: product=claude; ...; role=integrator; scope=patch-and-render` で記録した
(`docs/ai-provenance.md:52` の規定と、同じ file 群を更新した先行 wave の commit の先例)。
書く前に旧版との field 単位比較で「変わる pointer が 4 件だけ・key set 不変」を検算している。
段 6 のレンズ B が expected bytes との byte 一致を独立に再計算して確認した。

## この wave が言えないこと

- **「runtime leak を閉じた」とは言えない。** `-1.2` は固定の説明例であって、ある試行の実測 delta では
  ない。`delta_pct≡None` の防壁は whiteboard 射影経路の `delta_pct` field だけを守る (D118 決定 3)。
  `current_perf.last_delta_pct` はその関所を通らない。言えるのは、段 4 の不変と食い違う固定例を
  role の入力契約から除いたことまでである。
- **「毎試行の因果入力を直した」とは言えない。** headless provider
  (`orchestrator/campaign/claude_projected_provider.py:150-170`) は role body を effective prompt へ
  埋めるので因果入力になるが、originless compatibility test の `FixtureRoleProvider` は
  role bytes の sha を記録するだけで返答は hard-code である。段 3 のレンズ A は、現 planner sha を持つ
  保存済み `attempts.jsonl` / `report.json` を `output/exploration` 配下で見つけられなかった
  (静的検索、実走なし)。
- **例の値は machine gate で守られていない。** role 本文・ledger pin・生成物 adapter の全 surface を
  協調して旧 bytes へ戻す変異を独立に拒否する semantic gate は無い。既存検査は例の値を独立 literal
  として pin していない (`tools/check_codex_agents.py` の shape 検査は open object の内部を見ず、
  coder の `whiteboard` schema は items 定義を持たない)。wave 開始時に未変更の worktree で
  `tools/check_codex_agents.py` が rc=0 だったことがその観測である。
  分類は `SURVIVED / non-equivalent / semantic guard absent`。人間 review pin に依存しており、
  durable に certify されたとは主張しない。新規検査の追加は依頼が scope 外と指定した。
- **coder 例は 3 field で実射影は 5 field** という別の drift が残る。兄弟 role にも共通する。
  裁定パッケージへ返す。

## 変異 matrix — 7/7 KILLED、期待 node 完全一致 (ただし初回は probe)

本走の台帳は `mutation-ledger.json` (`repo_head` = 統合 commit `cd20f10b5049b14690ba68f041410b8ea3188c6d`、
`summary` = KILLED 7 / MISMATCH 0 / SURVIVED 0 / TIMEOUT 0、matching 7 / registered 7)。
runner argv は `python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_codex_agents.py
orchestrator/tests/test_reflux_originless_compatibility.py -rf`。

| id | 変異 | 観測赤 node 数 | 単一理由性 |
|---|---|---|---|
| M4-C | coder adapter の `/source/sha256` を旧値へ | 4 | **なし** (冗長 gate) |
| M4-P | planner adapter の `/source/sha256` を旧値へ | 4 | **なし** (冗長 gate) |
| M5-C | coder adapter の `/semantic_digest` を旧値へ | 4 | **なし** (冗長 gate) |
| M5-P | planner adapter の `/semantic_digest` を旧値へ | 4 | **なし** (冗長 gate) |
| M2-C | coder adapter の埋め込み本文の例を旧値へ | 5 | **なし** (冗長 gate) |
| M2-P | planner adapter の埋め込み本文の例を旧値へ | 5 | **なし** (冗長 gate) |
| M6 | originless 追随 helper の呼出しを除去 | 1 | **あり** |

adapter 側 4 変異の赤 node は 4 件で**完全に同一**である。

```text
orchestrator/tests/test_codex_agents.py::test_any_native_discovery_toml_is_rejected
orchestrator/tests/test_codex_agents.py::test_consumer_required_field_drift_is_detected_from_source_ast
orchestrator/tests/test_codex_agents.py::test_current_sources_render_byte_exact_and_native_is_empty
orchestrator/tests/test_codex_agents.py::test_project_config_native_role_is_rejected_and_globals_are_allowed
```

M2 はこれに `test_source_body_is_embedded_exactly_once_before_product_override` が加わって 5 件。
M6 は `test_originless_default_preserves_every_nonvolatile_leaf_and_closed_key_set` の 1 件だけ。

### 初回は probe である (DW-M08 の erratum)

**段 4 で事前登録した期待 node 集合は誤りだった。** 段 3 のレンズ B が静的読解で
「M4/M5 は renderer の byte parity が唯一の拒否層」「M2 は byte parity と本文埋め込みの 2 層」と
判定し、親はそれを採って M4/M5 を 1 node、M2 を 2 node で登録した。初回走行 (`mutation-ledger-probe.json`、
spec は `mutation-spec-probe.json`) は 7 件中 6 件が MISMATCH で、実測はいずれも**期待より多く**
赤になった (M4/M5 は 4 node、M2 は 5 node)。M6 だけが 1 node で一致した。

原因は、`test_codex_agents.py` の 4 つの test が checker 全体 (`CCA.check(root)`) を呼ぶことである。
adapter のどの field が drift しても同じ 4 本が赤になるので、**adapter 側の単一 field 変異に
DW-M01 の「単一理由」は構造的に成立しない。** DW-M03 の「過剰決定なら冗長 gate と明記して
単独変異の証拠から外す」に該当する。

初回を probe と明記し、観測された完全集合で再登録して本走した (`mutation-spec.json`)。
再走では 7/7 が KILLED・完全一致になった。**単独帰属できる KILLED は M6 の 1 件だけ**であり、
残る 6 件は「adapter 閉包が検査されていること」を 4〜5 層の重なりで示す冗長 gate 記録である。

### 登録しなかった変異

- 全 surface (role 本文 + ledger pin + 生成物 adapter) を協調して旧 bytes へ戻す変異。
  既存検査を通る (`SURVIVED / non-equivalent / semantic guard absent`)。
  wave 開始時に未変更の worktree で `tools/check_codex_agents.py` が rc=0 だったことがその観測である。
  新規 semantic 検査の追加は依頼が scope 外と指定したため、real 所見として裁定パッケージへ返した。
- adapter の `/review_ledger/source_file_sha256` だけを旧値へ戻す変異 (M3)。
  M2 と同じ層の組で情報が増えないため段 4 で登録しなかった。

## 親が実走した検査 (子は dispatch 障害で pytest を 1 件も走れなかった)

| 検査 | 結果 |
|---|---|
| focused 5 file (`test_codex_agents` / `test_codex_role_runtime` / `test_reflux_originless_compatibility` / `test_p3_s4_loop` / `test_p3_autonomous_workload_trial`) | 802 passed, 4 skipped, 27.72s, rc=0 |
| focused 3 file (`test_claude_transport` / `test_effort_levels` / `test_role_session_isolation`) | 85 passed, rc=0 |
| `tools/check_codex_agents.py` | rc=0 |
| `tools/check_docs.py` | rc=0 |
| `tools/check_ai_provenance.py` (full) | rc=0、9202 件、新規違反なし |
| 変異 matrix | 7/7 KILLED、期待 node 完全一致 |

`test_claude_transport.py` は段 6 のレンズ B が指摘した must-fix である。同 file は
`FixtureRoleProvider` 経由で `planner-v4.md` の bytes を読むのに、親の焦点走集合から漏れていた
(コード修正は不要、実走の追加だけ)。1 回目の投入は `queue-wait-timeout`
(`child_started=false` = infra) で、D612 の opt-in 上書きで通した。

## 次 wave の出発点

裁定パッケージへ返した real 所見:

1. role 入力例の field 数を実射影と揃える (coder / planner とも 3 field 例、実射影は 5 field)。
   `planner-v4.md` の「leading-indicators だけ」という記述と `current_perf` の食い違いも同じ族。
2. 例の値を独立に pin する semantic 検査を作るか (ユーザー裁定待ち)。作れば全 surface 協調 rollback を
   KILLED にできる。
3. `.codex/**` の生成物を Codex author 契約の適用外と明文化するか、D105 の `AI-Agent-Waiver`
   (ユーザー裁定つき) を要求するか (ユーザー裁定待ち)。
4. `docs/phase3-s8c-autonomous-trial-runbook.md:233-235` の「前世代から更新した current_metrics を
   次世代へ渡す」が実装 (`_INITIAL_ROLE_METRICS` を workload ごとに freeze して後続世代へ同じ snapshot を
   返す) と食い違う。別 erratum。
