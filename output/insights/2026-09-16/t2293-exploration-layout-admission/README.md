# [T-2293] Q1 — 起点試行の証拠発行器の受理型に探索 layout を加え、維持する拒否述語を負例で固定した

authority: none
default_effect: no-state-change

可変状態の正本は `docs/worklog.md` 末尾と現行 phase doc である。本書は wave の一次資料で、
子の出力と親の裁定の逐語は `verbatim/` に、変異の spec と台帳は `mutation/` に凍結してある。

- wave: `dev-wave-t2293-exploration-layout-admission` / branch `worktree-dev-wave-t2293-exploration-layout-admission`
- 起点: local main `8f17db598`。
- 実装 commit: `ef5491bf8` (Codex author 1 本 + fix 1 本の統合)
- 裁定: D2044 項 2 (2026-09-16 ユーザー裁定)。Q2〜Q4 は D1875 の整合が決まるまで着手しない。

## 1. 何を変えたか

`orchestrator/campaign/reflux_result_evidence.py` の exact-type gate 2 箇所 (`_ordered_attempt_materials` と
`issue_campaign_result_evidence`) の受理集合を、`CampaignLayout` だけから
`CampaignLayout` **または** `ExplorationCampaignLayout` へ広げた。判定は identity (`type(layout) is not A and
type(layout) is not B`) であり、`isinstance` にも tuple 所属 (`type(x) not in (A, B)`) にも落とさない。
`_context_roots` の型注釈を union にした。production の差分はこの import 1 行・述語 2 箇所・注釈 1 箇所だけである。

これは前 wave (insight `2026-09-14/t2293-origin-producer` §3) が結線障害 B1 として構造化したもの
(`loop` は `ExplorationCampaignLayout` を作るが発行器の exact-type gate が拒む) の解除である。
ただし **Q2〜Q4 は未着手なので 33 本を実行する executor は依然存在せず、発行 3 条件は 0/3、本番 authority は
0 件、certified 選択・材料レポート・試行台帳の現在値は 1 つも変わらない。**

## 2. 維持する拒否述語 (ユーザー裁定が同時確定を求めたもの)

| 入力 | 拒否する検査 | 負例 (nodeid、`orchestrator/tests/test_reflux_result_evidence.py::`) |
|---|---|---|
| 両型の subclass | 型 gate (発行入口 / projection 入口) | `test_campaign_producer_refuses_layout_subclasses_before_writes[official\|exploration]`、`test_ordered_wal_projection_refuses_layout_subclasses[official\|exploration]` |
| metaclass の `__eq__` が対象型と等しいと答える別型 (impostor) | 型 gate | `..._refuses_type_equality_impostor_before_writes[official\|exploration]`、`test_ordered_wal_projection_refuses_type_equality_impostor[official\|exploration]` |
| `root` / `wal_file` を持つ duck typed object (frozen dataclass / SimpleNamespace) | 型 gate | `..._refuses_duck_layout_before_writes[frozen\|namespace]`、`test_ordered_wal_projection_refuses_duck_layout[frozen\|namespace]` |
| `str` / `Path` / `None` | 型 gate | `..._refuses_non_layout_values_before_writes[str\|path\|none]`、`test_ordered_wal_projection_refuses_non_layout_values[str\|path\|none]` |
| exact な探索 layout だが physical root が evidence root の外 | `_context_roots` の既存包含検査 | `test_campaign_producer_refuses_exploration_root_outside_evidence_root_before_writes` |

負例はいずれも、有効な exact layout で実 WAL (同一 attempt の 5 frame) を先に作り、layout object だけを置き換える。
context・capability・contract・receipt は正例と同じ有効な組合せなので、型以外の理由で落ちない。
発行入口の負例は呼出し前後の evidence root の file snapshot が同一で record が書かれていないことも assert する。

**impostor 負例の由来。** 段 2 plan は `type(layout) not in (CampaignLayout, ExplorationCampaignLayout)` を提案したが、
段 3 レンズ A が「tuple 所属は `is` **または `==`** なので、metaclass の `__eq__` を持つ別型が通る」と指摘した。
親が最小再現で real と確認し (tuple 所属は impostor を True、identity gate は False)、述語を identity へ改め、
この穴を狙う負例と変異 M5 を加えた。

正例: 単体 `test_campaign_producer_issues_real_wal_projection_and_resolves_interval[official|exploration]`
(既存正例の両 layout 化。探索側は exact 型と namespace marker の実在も assert)、
`test_ordered_wal_projection_accepts_exact_layouts[official|exploration]` (projection 入口の受理)、
統合 `orchestrator/tests/test_reflux_campaign_issuer.py::test_real_run_campaign_exploration_issues_rejected_record`
(`loop.run_campaign(declared_use_class="exploration", result_evidence_context=...)` を stub 無しで通し、
探索 physical root 配下に source-WAL / projection / provenance が置かれ、record が resolve できることを確認)。

## 3. 名乗りの上限

- D2017 の上限は不変: 唯一 writer 性は trusted harness の運用前提であり、本 wave が与える保証ではない。
- record schema (`result-evidence/v1`、`execution-provenance/v2`) と既存入力に対する生成規則は不変。
  発行器は use class を record に書かない。**official と探索で出力 bytes が同一とは主張しない** —
  physical root が違えば content ref の path・projection・record bytes は違う (段 3 レンズ A の訂正)。
- 消費側 (D1747) は `exploration_campaign_layout(planned_identity, campaign_output_root)` で root を計算する。
  producer が探索 layout を受理したことで、**同じ output base と `cid == planned_campaign_run_identity` なら**
  producer の physical root と consumer の計算 root は `<base>/exploration/campaigns/<identity>` で一致する。
  33 本の planned identity と実行 identity の結線、lock 内の origin binding、sealed member との対応は Q2〜Q4 側であり、
  本 wave の統合正例はそれを証明しない。

## 4. 段 3 / 段 6 が覆した親の記述

- 「`_context_roots` の root 包含は探索 layout でも維持される」は brief の probe では観測できていない
  (型 gate が先に発火)。実装後の負例 `..._exploration_root_outside_evidence_root_before_writes` で初めて発火を観測した。
- 「record bytes 不変」は無限定にできない (§3)。
- pin 閉包の hit 無しは probe の帰結ではなく `git grep` (path 検索 + module 名検索) の申告で、間接参照の全否定ではない。
- brief (P4) の「発行入口だけを緩めても subclass 負例が単独で kill する」は不成立 — 内側 gate が同じ入力を拒否する。
  段 2 plan が projection 直呼び負例 (内側 gate だけを通る経路) へ再照準し、親が採用した。
- brief の probe 実測 (「探索 layout は WAL 5 frame まで通る」) は test helper が WAL を作ったことであって、
  producer 内で WAL を消費できたことではない (段 3 レンズ B)。統合正例が到達性を担保した。
- 段 6 レビュー B: 負例 helper `_assert_layout_projection_rejected` に `layout=real` の正例が同居していたため、
  変異 M3 で負例 node 2 件が「正例の過剰拒否」という別理由で赤化する。fix で正例を独立 test
  `test_ordered_wal_projection_accepts_exact_layouts` へ分離し、M3 の期待集合を 3 件へ改訂した (実走前)。

## 5. 変異

runner = `python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_reflux_result_evidence.py orchestrator/tests/test_reflux_campaign_issuer.py -q -rf`
(`tools/mutation_harness.py --runner-mode dispatch --detached`)。spec は job dir (checkout 外) に置き sha256 で束縛した。

事前登録 (段 4、実装前) は `mutation/mutation-spec.v1.json`。段 6 の fix に伴い M3 の期待集合だけを改訂したものが
`mutation/mutation-spec.v2.json` (改訂理由は §4 末尾と `verbatim/s4-plan-v2.md` 末尾)。

| id | 位置 | 変異 | category | 期待 node |
|---|---|---|---|---|
| M1 | 内側 gate | `not isinstance(layout, (A, B))` | negative | projection subclass ×2 |
| M2 | 内側 gate | `not hasattr(layout, "wal_file")` | negative | projection subclass ×2 + duck ×2 + impostor ×2 |
| M5 | 内側 gate | `type(layout) not in (A, B)` (tuple 所属) | negative | projection impostor ×2 |
| M3 | 内側 gate | `type(layout) is not CampaignLayout` (旧 gate) | positive | 発行正例[exploration] + projection 正例[exploration] + 統合 exploration 正例 |
| M4 | 外側 gate | `type(layout) is not CampaignLayout` (旧 gate) | positive | 発行正例[exploration] + 統合 exploration 正例 + root 外負例 |
| M6 | 内側 gate | 2 節の順序入替え (等価変異) | positive | SURVIVED (空) |

M4 の root 外負例は「型エラーが root エラーより先に出て match が外れる」赤であり、拒否地点の前移動であって
受理拡大ではない (DW-M03 の意味で kill の根拠は正例 2 件の過剰拒否)。期待集合の完全一致契約のため node には含める。

登録しない: 外側 gate だけの isinstance / hasattr / tuple 緩和 (内側が同じ入力を拒否し観測 0 件)、両 gate 一括緩和、
`_context_roots` の root 包含除去 (loop 側と content path 側が重複拒否、別文言の赤は実効 gate の kill ではない)。

**probe 走** (spec `mutation-spec.probe.json`、sha256 `c33ca90bb10c7af667af551957b99e44babeea80657a0292b3896ba028a8e530`、全件 SURVIVED 登録)
で観測 node を集めた。台帳は `mutation/mutation-ledger.probe.json` (repo_head `ef5491bf8`)。観測 node は 6 変異すべて
spec v2 の期待集合と一致した (M1=2、M2=6、M5=2、M3=3、M4=3、M6=0)。

**本走** (spec `mutation-spec.v2.json`、sha256 `1450ebb87d10aab640f586a408be30399487ac0fb1dd56a7680067c2e45d4184`、
repo_head `ef5491bf8`) は **baseline PASSED、5/5 KILLED、等価変異 M6 は SURVIVED (登録どおり)、MISMATCH 0、期待 node 完全一致**。
台帳は `mutation/mutation-ledger.final.json`、attempt 記録は `mutation/mutation-attempt.final.1.json`。

| id | 判定 | 観測 node 数 | 意味 |
|---|---|---|---|
| M1 | KILLED | 2 | `isinstance` へ緩めると subclass が projection 入口を通る |
| M2 | KILLED | 6 | 属性検査へ緩めると subclass・duck・impostor が通る |
| M5 | KILLED | 2 | tuple 所属へ戻すと metaclass 等価比較の impostor だけが通る |
| M3 | KILLED | 3 | 内側 gate を旧形へ戻すと exact 探索 layout の正例 3 件が過剰拒否される |
| M4 | KILLED | 3 | 外側 gate を旧形へ戻すと探索正例 2 件が過剰拒否され、root 外負例は拒否地点が前へ移る |
| M6 | SURVIVED | 0 | 等価変異。harness の SURVIVED 検出の正例 |

**本 wave が足した実効的な gate は「探索 layout の受理」と「identity 同一性の維持」の 2 つ**である。前者は M3/M4 (過剰拒否の正例)、
後者は M1/M2/M5 (緩和の負例) が単一理由で担保する。register していない外側 gate 単独の緩和は内側 gate が同じ入力を
拒否するので変異で測れない (冗長 gate として残す)。

段 6 の変異登録の改訂 (M3 の期待集合 2 → 3 件) は実走前に行い、理由を `verbatim/s4-plan-v2.md` 末尾に残した。
probe の観測がその改訂後の集合と一致したので、erratum は不要である。

## 6. 検査

- 焦点走 4 file (変更 2 + consumer `test_reflux_formal_consumer.py` / `test_p3_autonomous_workload_trial.py`、
  `tools/run_tests.py -q -rf` の自動判定 → Pegasus request 1932.nqsv): **554 passed / 赤 0 / skip 0**。
- 変更 2 file の単独走: `test_reflux_result_evidence.py` 104 passed (fix 後)、`test_reflux_campaign_issuer.py` 16 passed。
  統合正例 `test_real_run_campaign_exploration_issues_rejected_record` は PASSED (skip ではない)。
- `check_ai_provenance.py --range main..HEAD` rc=0 (実装 commit)。
- 受入全走の結果は worklog に記す (本書の作成時点では未実施)。

## 7. 発行 3 条件と名乗り

**発行 3 条件は 0/3、本番 authority は 0 件のまま変わらない。** 「8c を結線した」「本番で 33 本を回した」「P6 が発火する」
とは名乗らない。certified 選択・材料レポート・試行台帳の現在値は 1 つも変わらない。

## 8. 逐語の可逆最小正規化 (diff --check 抵触)

`verbatim/` の 3 file は、Markdown の行末 2 space (改行記法) が末尾空白検査に抵触したため、
**行末の空白だけを除いた** (可視文字は不変)。復元は、下記の行の末尾に space を 2 個ずつ付け直す。
原文 (子の出力そのもの、codex receipt の `output_sha256` と一致) の sha256 と byte 数を記す。

| file | 原文 sha256 | 原文 bytes | 正規化後 bytes | 除いた行 (各 2 space) |
|---|---|---|---|---|
| `s2-plan-v1.md` | `6d8d3fcf592878fb4a326b7bc847b507b513d0fe6806a28b711e6d55107a9ba4` | 15609 | 15607 | 82 |
| `s3-consult-A.md` | `f80346548a884b9594dcbded7b00ec8670f788af2055d41c1fb8b156fcc92ab0` | 7846 | 7824 | 9, 28, 41, 64, 67, 70, 75, 78, 81, 88, 91 |
| `s5-author-1.md` | `7bdc4b68cf9374a87a009dedff46e731836df6008a17814d9633c39f2c76273b` | 5738 | 5736 | 9 |
