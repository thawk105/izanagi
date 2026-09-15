# [T-2591] 集約床値が実 issuer から公開材料レポートまで届く正例

- wave branch: `worktree-dev-wave-t2591-aggregate-material-report`
- 基底 commit: `0600887d92538b3f34d894f9674d202d0a29a578`
- 実装 commit: `9b2a3198a`
- main 取り込み commit: `81a6dbec7` (取り込んだ local main = `8c84f9239`)
- 実装子 branch: `impl-dev-wave-t2591` (worktree `.codex/worktrees/t2591-impl`)

## 何を作ったか

材料レポートの公開 builder が **集約床値の成果物 (schema `p3-b4-authoritative-floor/v2`)** を
受けて投影することを、両層とも実体を通して示す正例を 1 本足した。

`orchestrator/tests/test_p3_b4_material_report.py::test_aggregate_authoritative_floor_reaches_public_material_report`

経路はすべて実体である。

| 層 | 実体 |
|---|---|
| 集約入力の合成 | `test_p3_b4_floor_artifact_issuer._aggregate_public_sources` (無改造で import) |
| 発行 | `p3_b4_floor_artifact_issuer.issue_aggregate_authoritative_floor` |
| 解決 | `p3_b4_floor_artifact_issuer.resolve_preregistered_authoritative_floor` |
| prerun publication | `immutable_publication` fixture の実 publication root |
| raw analysis | 同 fixture 由来の実 assembly |
| 公開 builder | `p3_b4_material_report.build_material_report_document` |

production (`orchestrator/campaign/**`) は 1 文字も変えていない。編集したのはテスト 3 file だけである。

## 着手前の実測 — 既存の present-floor 経路は手書き dict だけで通っていた

`test_p3_b4_material_report.py::_write_floor_preregistration(present=True)` は authority artifact を
**その場で dict から組み立てている**。`"artifact_sha256": "1" * 64`、`"spec_sha256": "2" * 64`、
`floor_exact: [0, 1]`、schema は v1。issuer を一度も通っていない。

つまり材料レポート層の present-floor 投影は、**issuer が実際に書いた bytes で通ったことがなかった**。
依頼の「性質だけの stub で両層を通す緑にしない」はここを指している。

なお「過去に一度も実測されていない」とは書かない — 静的調査で過去全体は否定できない。
言えるのは「現行 test 集合に集約 artifact を builder へ通す node が存在しない」であり、
これは AST で canonical 関数 31 件と golden 31 件の完全一致を照合して確かめた。

## 依頼の前提の所在を直した

依頼は「合成 repo に prerun publication と raw analysis が無く、公開 builder へ渡せない」と述べる。
実測すると、無いのは**床値 issuer 側**の合成 repo であって、**材料レポート側**の
`immutable_publication` fixture には実 prerun publication と実 raw analysis がある。
よって正例は材料レポート側へ置き、集約入力の合成 helper を無改造で import する形にした。

## 段 3 が出した real な穴 — 投影値は実引数の観測ではない

レポートの `analysis.floor_argument` は `_apply_authoritative_floor_projection` が
authority から書き込む**投影値**であって、`evaluate_b4_artifacts` へ実際に渡した引数ではない。
内部検査 `_assert_authoritative_floor_projection` も同じ authority と比べるだけである。

したがって「最大床値で解析した」を assert したければ、実 evaluator の引数を観測するしかない。
正例は `evaluate_b4_artifacts` を**実物へ委譲する記録 wrapper** で包んだ (既存 m9 と同じ定型)。
差し替えではなく観測である。この穴は変異 M3 が実測で裏取りした。

## 裁定 — seam は本数でなく機構上の位置で決める

段 1 brief は「許可する monkeypatch は 3 つだけ」と本数で書いた。段 3 がこれを倒した:
指定した `immutable_publication` fixture 自身が 3 つ以上を patch している。

段 2 のプランは本数制約を満たすため、既存 helper へ keyword 引数を足して Git seam を条件化し、
一時 fixture に実 Git repository を作る案を出した。**採らなかった。**

- 制約側が誤っていた。コードを曲げて誤った制約に合わせることになる。
- 段 3 の逐語: 「Git patch は最大値計算、3 spec 閉包、source 再構成、report 投影を置換しない。
  外して増える検査は Git による入力の凍結・履歴 binding であり、集約 → report の結線そのものでは
  ない」。**機構の識別力を増やさない。**
- 依頼が scope 外と明示した範囲に入る。
- `test_p3_b4_floor_artifact_issuer.py` は同時稼働の床値系 wave と最も衝突しやすい共有 helper。

## この正例が証明しないこと

- 3 本の source summary が**実 Git に凍結された**成果物であること (Git は環境 seam のまま)。
- calibration が真正であること (loader は環境 seam のまま)。
- `write_material_report` による publish の成立。publish は公開 builder を呼ばず別に組み立てており、
  出力先の拒否条件・campaign 非交差・commit marker が加わる。
- 材料レポートが certified であること。現物は `certifying=False` / `closed_world=False` を宣言し、
  報告範囲は `evidence-only`、事前登録 §5 は `not_in_effect` と表示する。

## 親の実測 — 台帳の所要は 79.0 でなく 4.8 秒

実装子は所要台帳へ `79.0` を登録した。**群全体を 1 回で走らせた JUnit で測り直して 4.788 秒へ直した。**

- 台帳の規約は `tools/update_acceptance_duration_ledger.py` が JUnit の `testcase@time` を
  そのまま採ることである。pytest の既定でこれは setup + call + teardown の合算。
- `79.0` は**新 node を単独走させた**ときの値で、module scope fixture `immutable_publication` の
  構築 (setup 71.22 秒) を丸ごと含んでいた。
- 同じ群走行で既存 `test_m9_...[True-True]` は **11.491 秒**、台帳の既存値は `11.0`。
  つまり台帳は群内走行の値であり、単独走の値ではない。
- 実運用では file 内で先に走る `test_normal_path_assembles_binds_evaluates_and_builds_document`
  が fixture 構築費を負担する (同走行で 19.114 秒)。group は shard で分割されないので順序は保たれる。

この 1 行の訂正は Codex の fix 子が行った (台帳は実装面であり親は直接編集しない)。

## 変異検査 — 新走 5/5 KILLED、旧走 5/5 SURVIVED

production は本 wave で 1 文字も変えていない。テスト強化だけの wave なので DW-M08 に従い
**新旧両走**を登録した。旧走は新 node を `--deselect` した集合 (= 変更前 HEAD の test 集合と等価。
本 wave の test 集合の差分は新 node 1 件と 2 台帳の登録だけであり、台帳登録は受理集合を変えない)。

| ID | 位置 | 変異 | 新走 | 旧走 |
|---|---|---|---|---|
| M1 | `_authoritative_floor_source` | `schema_version` を literal v1 へ | KILLED | SURVIVED |
| M2 | `_apply_authoritative_floor_projection` | `non_guarantees` を先頭 3 件へ切り詰め | KILLED | SURVIVED |
| M3 | `_load_and_evaluate` | evaluator へ渡す present 枝の floor を `Fraction(0, 1)` へ (`else None` は保存) | KILLED | SURVIVED |
| M4 | 同上 + `_assert_authoritative_floor_projection` | 投影 ratio と期待 ratio をともに `[0, 1]` へ (2 層) | KILLED | SURVIVED |
| M5 | `_render_markdown_with_authoritative_floor` | artifact path を旧 stub の literal path へ | KILLED | SURVIVED |

- 新走: `mutation-ledger.final.json`。baseline PASSED、
  `{"KILLED": 5, "MISMATCH": 0, "SURVIVED": 0, "TIMEOUT": 0, "matching": 5}`。
- 旧走: `mutation-ledger.old.json`。baseline PASSED、
  `{"KILLED": 0, "MISMATCH": 0, "SURVIVED": 5, "TIMEOUT": 0, "matching": 5}`、失敗 node 0 件。
- probe: `mutation-ledger.probe.json`。全件 SURVIVED 期待で登録して観測 node を集めた (DW-M07)。
  結果は 5 件とも MISMATCH (= 赤) で、消していない。

**原データからの検算:** 新走・probe とも、5 変異それぞれの失敗 node は**ちょうど 1 件**で、
その node は新正例そのものだった。同 file の既存 49 node は 1 つも検出していない。
旧走の失敗 node は 0 件である。したがって「5 変異すべてを新正例 1 件だけが殺した」は
台帳の生データと一致する。

### 変異設計で直した 2 点

- **M4 を 2 層にした。** 投影側 (`_apply_authoritative_floor_projection`) だけを変えると、
  内部検査 `_assert_authoritative_floor_projection` が authority から独立に ratio を作り直して
  先に拒否する。赤の理由が新正例に帰属しなくなるため、DW-M01 の単一理由性 (F820/F28) に反する。
  期待 ratio 側も同時に変える 2 層変異にして、builder が誤った床値の document を返す状態を作った。
  段 6 レビュー A も同じ位置を独立に指摘した。
- **M3 で `else None` を保存した。** 式全体を置換すると、既存 m9 の absent ケース
  (`observed_floor_arguments == [None]`) も赤になり、新正例の追加検出力の証拠にならない。
  段 6 レビュー A が同じ点を指摘した (親の spec は既にこの形だった)。

## 親が実走した検査

| 検査 | 結果 |
|---|---|
| 焦点走 (material report / real_repo_serialization / schedule_order / duration_ledger) | 237 passed, 1 skipped, rc=0 (fix 前後で 2 回、計算ノード 140 秒台) |
| 材料レポート群の単独走 | 50 passed, rc=0 |
| `check_ai_provenance.py` full (実装 commit 後) | 10105 件、新規違反なし |
| `check_ai_provenance.py` full (main 取り込み後) | 10145 件、新規違反なし |
| 変異 新走 | baseline PASSED、5/5 KILLED、matching=5 |
| 変異 旧走 | baseline PASSED、5/5 SURVIVED、matching=5 |

## 段 6 レビューの結論

レビュー 2 本 (正しさ・恒真性 / 契約・登録閉包・波及) はいずれも**実装に must-fix を出さなかった**。

- レビュー A は禁止面 1,604 file を bytes 比較して差分ゼロを確認した。所見は変異 spec 側の 2 件
  (M3 の置換範囲、M4 の実際の拒否位置) で、いずれも親の spec では既に回避されていた形だった。
- レビュー B は実装子の報告から G6 契約 (`test_g6_all_real_repo_items_stay_one_unit_and_keep_relative_order`)
  の列挙漏れを 1 件出した。登録自体は正しく、焦点走で緑を実測した。

## 編集面の重複検査 (2 回)

- 起動時: T-2293 (producer layer r1/r3) の編集面は `p3_autonomous_workload_trial.py` と同 test のみ。
  重複 0。land 済み (worklog 1501)。
- 段 5 直前: wave branch 25 本の tip を一括取得。起動直後に別 session が作った床値系 5 本
  (t2288-floor-spec-freeze, t2592-calibration-miss-floor, t2595-floor-query-legacy-symmetry,
  t1851-c3c-official-floor, t1338-floor-residual) はいずれも main tip のままで commit 0。
  commit 済み 7 本のうち重なるのは `t2515-calib-rr95-rr5` の 1 件だけで、同じ
  `test_real_repo_serialization.py` の別 frozenset (`_REAL_REPO_CLASSIFIED_NODES_GOLDEN` 行 52 付近 と
  本 wave の行 376) を触るため行競合しない。

## 運用の実測

- `git worktree add` は並行 session 多数の下で 40〜50 分かかった (24983 file、2 本作成)。
- `tools/dev_wave_submodule_init.py` は**両方の worktree で 1 回目が
  `runtime-io-failure: update-no-fetch` で落ち、同じ引数の再実行で成功した**。
  DW-O08 の「一過性に失敗しうる。1 度だけ再実行」の実例が 2 件連続した。
- 稼働 wave 25 本の下で `git status --porcelain` は 20 秒 timeout でも返らない。
  `git for-each-ref` の tip 一括取得と `git diff --name-only main...<branch>` が実用的だった。

## 工数

codex 子 7 本、すべて `tools/check_codex_output.py` rc=0・receipt `outcome=accepted`。
model は全段 `gpt-6-astra`、effort は全段 `medium`。

| 子 | 段 | wall | model call |
|---|---|---:|---:|
| plan | 2 | 296.1 s | 13 |
| consult sol | 3 | 247.6 s | 8 |
| consult luna | 3 | 356.6 s | 10 |
| author | 5 | 770.6 s | 39 |
| review A | 6 | 313.5 s | 12 |
| review B | 6 | 295.9 s | 10 |
| fix | 6 | 80.8 s | 7 |

fix 子は親が実測した台帳値の訂正のためだけに起動した。
