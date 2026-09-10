# [T-1222] 成長比例テストの棚卸し — REAL_REPO_SERIAL_NODES の外へ広げた回

wave: dev-wave-t1222-growth-hold-sweep / 2026-08-16 / base main 64808422

対象は `orchestrator/tests` の top-level test node と、本文に列挙した探索 primitive・
既存 2 台帳に限定した候補分析である。数値はこの対象内の候補数を示す。
hold inventory の `completeness` は `registered-layers-only` であり、未知の hold 層は自動発見しない。

## 判定式 (本 wave が固定したもの)

D335 は「repository の成長に比例して実行コストが増える構造」を対象とする。
**秒数の閾値では判定しない。入力集合の性質で判定する。**

node t が実 ROOT を読み、その入力集合 F(t) について

- **比例**: F(t) が repository の通常運転で単調に増える集合。
  (a) tip 側の commit 履歴、(b) tracked file 総数または repo 全走査、
  (c) docs / archive の総量、(d) output artifact corpus。
- **非比例**: F(t) が固定 path・固定 byte 上限・**固定された歴史 commit の集合**であるもの。

**「設計上限のある固定用途 directory」は独立の第 3 区分とし、比例と認めたうえで
登録しない理由に磁束を置く** — 段 3・段 6 の敵対レビュー 2 本が、親の当初の
「非比例」分類を実測で反証したためである (下記「親が撤回した 2 件」)。

## 親の実測 (すべて repo 外 probe、2026-08-16、本 worktree)

| 測定 | 値 |
|---|---|
| `enumerate_repository_files(ROOT)` | 1.58 秒 / 13,062 file |
| `search_repository(ROOT, files=全列挙)` | 15.93 秒 |
| `tools/check_docs.py` 単発 | 5.33 秒 |
| s8c `_candidate_commit` (`git add -A` + write-tree + commit-tree) | 14.02 秒 / 12,659 path |
| `validate_condition_freeze_at(ROOT, HEAD)` | 0.628 秒 / 到達 commit 4,005 |
| `check_ai_provenance --range <固定 sha>^!` | 3.78 秒 |
| うち policy epoch の pickaxe (`git log -S … -- docs/ai-provenance.md`) | 0.046 秒 (tip 依存) |
| copytree: `.claude/agents` 13 file | 0.016 秒 |
| copytree: `.codex/role-adapters` 13 file | 0.009 秒 |
| copytree: `orchestrator/codex_roles` 8 file | 0.007 秒 |
| copytree: `tools/task_runs` 7 file | 0.008 秒 |

### 部分木の成長 (`git ls-tree -r -l` を各時点 commit へ適用)

| 部分木 | 30 日前 | 14 日前 | 7 日前 | 現在 |
|---|---|---|---|---|
| repo 全体 | 845 file / 15,941 KiB | 4,448 | 10,585 | 12,685 / 408,089 KiB |
| docs | 56 file / 1,968 KiB | 121 | 304 | 510 / 14,097 KiB |
| output | 544 file | 3,833 | 9,709 | 11,451 |
| orchestrator/tests | 67 file | 187 | 219 | 308 |
| `.claude/agents` | 13 file / 82 KiB | 13 | 13 | 13 / 81 KiB |
| `.codex/role-adapters` | 13 file / 167 KiB | 13 | 13 | 13 / 167 KiB |
| `orchestrator/codex_roles` | 8 file / 225 KiB | 8 | 8 | 8 / 229 KiB |
| `tools/task_runs` | 0 (未作成) | 7 | 7 | 7 / 135 KiB |

repo が 30 日で 15 倍、docs が 7 倍になる間、copytree 対象 4 部分木は
**作成時の 1 回の段差を除いて file 数が変わっていない** (14 日前から現在まで完全に同数)。
ただし `tools/task_runs` は 0 → 7 の段差を持つので「1 file も増えていない」とは書けない。

## 登録した 3 件 (56 → 59)

| node_id | 軸 | 実測 | 失う固定検査 |
|---|---|---|---|
| `test_check_docs.py::test_real_repo_clean` | docs_bytes | 5.33 秒 | rc=0・違反なし・Pegasus admission drift ゼロ |
| `test_check_docs.py::test_dev_wave_model_pins_accept_current_docs_contract` | docs_bytes | 5.33 秒 | 現行 model pin の過剰拒否正例 |
| `test_check_docs.py::test_normative_exact_section_pins_accept_real_repo` | docs_bytes | 5.33 秒 | normative section pin の過剰拒否正例 |

成長源は `docs/archive/worklog-*.md` の glob (rotation ごとに単調増加、現在 380 file 超)、
`ARCHIVE_DIR.iterdir()`、handoff glob、列挙 living docs、skill / command / reference / provenance の rglob。

**残る経路と、それぞれが走らない条件**:
land の `_validate_generated_docs` は non-noop fold の後に `--expect-active-transaction` 付きで走り、
noop fold では検査の手前で return する。wave checker は check-docs の exactly-once を要求するが、
実行は completed かつ passive-green の走行に限る。引数なしの `tools/check_docs.py` は
クラス 2 / 3 完了検査の義務として残る (他クラスでは要求されない)。

**付随損失**: `orchestrator/tests/test_check_docs.py` は素の `python3` 実行が file 全体で
拒否されるようになった (解除は `IZANAGI_RUN_GROWTH_HELD_TESTS=explicit-user-command`)。
module docstring を同 commit で訂正した。

**受入時間について**: 観測条件下で約 16 秒ぶんの subprocess elapsed 総和を pytest 選択集合から
除いた。受入 critical path と net wall 差は未測定であり、**wall 短縮は未確認**である。

## 登録しなかったもの (理由つき)

| 分類 | 対象 | 理由 |
|---|---|---|
| `d451_last_runner` | 段 2 が挙げた 148 件、s8c 共有 fixture consumer 3 件 (`:125,:190,:206`)、s8c negative control 1 件 (`:257`)、provenance 2 件 | 同じ拒否条件を発火させる独立した既定走行が無い |
| `growth_real_bounded_step` | `test_codex_agents.py` 21 / `test_dev_waves_checker.py` 10 / `test_dev_waves_integration.py` 40 / silo 2 本目 1 | 入力は実 subtree だが、設計上限のある固定用途集合で、14 日間 file 数不変。保留しても除ける費用は合計約 2.8 秒で、失う検出力は 112 pytest item |
| `guard_binding_blocked` | `test_s8b_floor_campaign.py` 2 件 | 同 file を `spec_from_file_location` で再読込する正規 consumer がある |
| `guard_binding_blocked` | `test_dev_waves_integration.py` (上と重複) | `:2050-2058` が fresh subprocess で同 module を package import し、保留対象外の `test_socket_roundtrip_works_beyond_108_byte_repository_path` (`:2165`) を既定で赤にする |
| `already_default_skipped` | T-080 stub-free 6 function (11 node) | `IZANAGI_T080_E2E=1` 必須で既定 skip |
| `already_default_serial` | floor の direct call | `REAL_REPO_SERIAL_NODES` 登録済み |
| `refuted` | `test_s8b_ratified_verify.py` 全 node、silo 1 本目 | 実 ROOT からは固定 1〜2 file のみ |

## 親が撤回した 2 件

段 6 の敵対レビュー 2 本が、親の裁定文の誤りを 2 件突いた。どちらも real で撤回した。

1. **「copytree 対象 4 部分木は 1 file も増えていない」は誤り。** `tools/task_runs` は
   30 日前 0 file → 現在 7 file である。正しくは「作成時の 1 回の段差の後、14 日以上不変」。
   分類も「非比例」から「比例だが設計上限のある固定用途集合」へ改めた。
2. **「provenance の 2 node は固定歴史なので非比例」は誤り。** `_audit_history` は毎回
   `_scope_policy_commit()` / `_implementation_policy_commit()` を呼び、これは現在の HEAD に対して
   `git log -S … -- docs/ai-provenance.md` を走らせる (`tools/check_ai_provenance.py:1122-1136,1552`)。
   親は `_commit_range` と `_build_ancestry` だけを見ていた。tip 依存の項は実在し、実測 0.046 秒である。
   比例と認めたうえで、既知違反の正例を守る最後の走行なので D451 で見送った。

## 変異 matrix

anchor commit `949b7f16` の使い捨て worktree (`tools/mutation_worktree.py --runner-mode dispatch`)。
runner 範囲は `test_growth_test_holds_contract.py` + `test_hold_inventory.py`。

| ID | 変異 | 結果 | 期待赤 node |
|---|---|---|---|
| M1 | 登録した row (`test_real_repo_clean`) を `_HOLD_ROWS` から削除 | KILLED | contract の count/digest pin、contract の inventory 出力検査、hold inventory の 2 件 (計 4) |
| M2 | `test_check_docs.py` の `enforce_held_functions(...)` 呼出しを削除 | KILLED | guard binding 検査、call-time wrap 検査 (計 2) |
| M3 | 同呼出しの `plain_runner` を `manual` → `pytest-delegating` | KILLED | guard binding 検査 (AST runner 不一致、1) |
| M4 | 登録 row の `hold_axis` を `docs_bytes` → `commits` | KILLED | contract の digest pin、hold inventory の 2 件 (計 3) |

**4/4 KILLED、MISMATCH 0、SURVIVED 0。baseline は rc=0 / 47.30 秒。**

初回登録 (`mutation-ledger-probe.json`) は 4 件中 3 件が MISMATCH だった。
**変異が検出されなかったのではなく、親が挙げた期待 node が不完全だった** —
1 つの registry 変異が contract 側 2 node と inventory 側 2 node を同時に赤にする。
probe の実測から完全集合を再導出して本走した (DW-M08 の「期待 node は完全集合」)。

M1 は **wave 前の実コードの形そのもの**である (3 node が台帳に無い状態)。
M2/M3 の anchor は wave 前に存在しないため、変更前 HEAD への同一変異は適用不能であり、
旧 HEAD 走は「新テストだけが検出する差分」を示す形にならない。この事実を記録して代える。

## 母集合は閉じていない

段 2 の全件走査は 230 件を挙げたが、少なくとも次を落としていた。

- `load_role_specs(ROOT)` 経由の `test_codex_agents.py` 7 件 (レンズ A)
- `test_dev_waves_integration.py` の subprocess 閉包 1 件 (レンズ A)
- `test_s8c_preregistration_invariant.py:257` の in-process `check_docs.main()` 1 件 (親・レンズ B が独立に検出)
- `test_check_ai_provenance.py` の実 repo 2 件 (レンズ B)

**既知漏れは少なくとも 11 top-level node である。** 落ちた理由は構造的で、
primitive の文字列検索 (`(?:check_docs|check_ai_provenance)\.py` など) は
**production の重い関数を同一プロセス内で呼ぶ形**を拾えない。
次に同種の棚卸しをするときは、subprocess 検索とは独立に
`module.func(ROOT)` 形の呼び出し閉包を探す必要がある。

## scope 外の real 所見 (起票する)

- `tools/hold_inventory.py:107-141` は plain runner・`--noconftest`・`--confcutdir`・direct call を
  `known-unresolved-bypass` と報告するが、現在の実装は import 時 (`growth_test_holds.py` の
  `enforce_held_functions`) と call 時 (`_wrap_held_function`) の二層でこれらを拒否する。
  `test_hold_inventory.py` が古い表現を固定しているため、誤報が検査で守られている。
  **本 wave が作った穴ではない。**
