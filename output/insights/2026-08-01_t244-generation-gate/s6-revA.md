## 総括

NO-GO。

- [致命 / must-fix] `int` サブクラスで承認予算 1 を申告したまま複数世代を実行できる。
- [致命 / must-fix] freshness 判定が非原子的で、並行する 1-generation run を同一 campaign 上で連結できる。
- [高 / must-fix] freshness テストは実ファイルも layout 束縛も検査せず、wrong-layout 変異が全テストを生存する。
- [高 / must-fix] V12 は赤になるが、`break` 削除後も attempt 数は 1 のまま。登録理由とは別の `AttributeError` で赤になる偽 KILL。
- [中 / must-fix] V1 は fixture+build の既存拒否に食われ、受理集合を変えずメッセージ差だけで赤になる。
- [中 / must-fix] V10 は下限拒否と非 int 拒否という独立した二変異を一件に畳んでおり、単一理由性がない。
- [nit] plan v2 の「新規8本」は実際に要求した node 群と矛盾する。実装は新規9関数で、詳細仕様には合致する。

## 所見

### plan v2 1〜6 の照合

| 項 | 実装との照合 | 判定 |
|---|---|---|
| 1 | `MAX_GENERATIONS = 10` を残し、`MAX_APPROVED_GENERATIONS = 1` を追加。環境変数・flag・provider 例外なし。`p3_autonomous_workload_trial.py:90-91` | 一致 |
| 2 | helper は `AutonomousTrialError` の直後。短絡評価順も bool → 非 int → 1..10 → 承認上限。メッセージは定数由来。`:180-195` | 文面どおり。ただし A-01 の型迂回あり |
| 3 | `load_loop_state(layout) is not None` を拒否。`:198-202` | 文面どおり。ただし A-02/A-03 により保証不成立 |
| 4 | `_run_workload():643`、`run_trial():883`、`main():1051` の3箇所。 | 一致 |
| 5 | CLI default は `ast.Constant(1)` になる literal。`:1040` | 一致 |
| 6 | 要求された全 node を実装し既存2本を更新。実数は新規9関数、parametrize 後10 case。 | 詳細仕様に一致、件数文言とは不一致 |

編集は裁定どおり2ファイルだけで、裁定外の production 実装はない。

### 拒否順序と副作用

- `main()` は `parse_args` が `:1050`、validator が `:1051`、fixture/build 判定が `:1052`、pinned-clean が `:1063`、競合 benchmark 検査が `:1069`、checkout が `:1074`。要求された4処理すべてより前である。

- `run_trial()` は validator が `:883`、`run_root.mkdir()` が `:897`。trial-id 検査だけが validator より前だが、artifact は作らない。

- `_run_workload()` は validator が関数本体の先頭 `:643`。freshness gate は `:658`、最初の `_invoke()` は `:701`、実際の `provider.invoke()` は `:562`。

- `_descriptor_for()` (`:464-472`) は descriptor schema を読むだけ、`_campaign_for()` (`:422-451`) と `trigger.default_cfg()` は object 構築だけ、`campaign_layout()` は path を返すだけ（`layout.py:214-217`）。この三経路に directory 作成・ファイル書込はない。

したがって静的な順序は裁定どおり。ただし freshness は外側の `run_trial()` が既に作った run-root/journal より後であり、「全 trial artifact より前」の保証ではない。裁定が保証しているのは provider 呼出し前までである。

### A-01 [致命] `int` サブクラスで generation 予算を偽装できる

何が壊れるか: validator は `isinstance(generations, int)` だけを要求する一方、loop は元 object の `generations + 1` を使う。[production](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux/orchestrator/campaign/p3_autonomous_workload_trial.py:184) `:184-191,679`。

読み取り専用の in-memory probe で、値 1 の `int` サブクラスに `__add__` が 4 を返すよう実装すると、

```text
_validate_generation_budget(x)  -> 受理
list(range(1, x + 1))            -> [1, 2, 3]
JSON generation_budget           -> 1
```

となった。3入口すべて同じ object と同じ validator を使うため、多層化では防げない。境界テスト `test_p3_autonomous_workload_trial.py:71-85` にこの入力はない。

成果物影響: campaign ID の `generation_budget` と terminal report の `generation_budget_per_workload` は 1 のまま、journal・whiteboard・WAL・certified 候補には generation 1〜3 が入り、予算と proof chain が食い違う。

判定: must-fix。exact built-in `int` へ閉じるか、安全な正規化値を以後すべての consumer が使う必要がある。その変更後は V9/V10 の変異設計も再裁定が必要。

### A-02 [致命] freshness check と state 消費の間に TOCTOU がある

何が壊れるか: build 経路の campaign ID は `run_root` を含まず、同一 trial/config は同じ layout を使う (`:422-451,655`)。一方、freshness check `:658` と `_whiteboard(layout)` による再読込 `:690` の間に reservation/lock がない。

成立する interleaving:

1. 同じ trial/config の A・B が別 run-root でともに `:658` を通過する。
2. B が default driver で state を保存する (`p3_s4_loop_trigger_gating.py:485-509`)。
3. A が `:690` で B の state を読み、過去 whiteboard を planner に渡す。
4. A の driver も同じ state を再読込し、campaign iteration をさらに進める。

各 supervisor の申告は1 generationでも、cross-generation feedback と campaign 連結が成立する。

成果物影響: 同一 campaign の WAL・whiteboard・provenance・certified 候補が複数 trial にまたがり、各 report の `campaign_root`／generation 1 と campaign iteration 2以降の参照が不整合になる。

判定: must-fix。provider 呼出し前に campaign 単位の原子的 reservation を取得し、freshness 判定から drive 完了まで競合 run を排除する必要がある。

### A-03 [高] freshness テストが実 state と layout を検査していない

既存-state テストは `load_loop_state` を任意の layout に対して常に `LoopState()` とする (`test_p3_autonomous_workload_trial.py:241-243`)。fresh テストも任意の layout に常に `None` を返す (`:264-265`)。

例えば production の `:658` を「常に空の別 layout を freshness 検査する」形に変えても、

- existing-state テストは引数を無視して state を返すので緑
- fresh-state テストは引数を無視して None を返すので緑
- 他のテストは実 campaign state を作らないので緑

となる。V4/V11 の call presence/order は検査するが、実際の `loop_state.json`、deserialize、campaign ID、layout binding は検査していない。

成果物影響: wrong-layout 回帰を通すと、既存 campaign の whiteboard が `:690` から planner に入り、後続 WAL・report・certified 選択が前 run の state を参照する。

判定: must-fix。実 layout に `save_loop_state()` した負例を追加し、現テストは V11 の provider-order poison test として責務を分離すべき。

### A-04 [高] V12 は「single attempt」を kill していない

対象 `break` は planner-invalid 分岐の `:716`。これを単純削除すると `planner is None` のまま `planner.axis` を読む `:728` に進み、`AttributeError` になる。`run_trial()` はこれを `:954-966` で捕捉し、generation 配列が空の `supervisor-error` cell に置換する。

したがって `test_invalid_role_is_single_attempt_and_stops_cell` (`test...py:176-201`) は赤になるが、planner attempt は依然1回である。赤理由は「2回目を試した」ではなく「素の例外で report 形が変わった」。

`MAX_APPROVED_GENERATIONS = 3` の monkeypatch 自体は有効である。helper は `:191` で module 属性を各呼出し時に読むため、`run_trial():883` と `_run_workload():643` の双方が3を受理する。

成果物影響: break 削除時、attempt journal には planner-invalid が残る一方、report cell はその generation を失って `supervisor-error` となり、report↔journal の参照が崩れる。

判定: must-fix。V12 は `break -> continue` に再照準し、planner invocation 数を直接 assert すべき。単純削除による report-contract 回帰は別変異として扱う。

### A-05 [中] V1 は受理集合を変えず診断差だけで赤になる

`test_main_rejects_unapproved_budget_before_build_preparation` は provider が fixture、`--no-build` なし (`test...py:366-373`)。

`main()` の validator `:1051` を削除しても、直後の fixture+build 拒否 `:1052-1055` が発火する。テストが赤になる理由は `match="承認済み上限"` と実メッセージが違うためだけで、入力は引き続き拒否され、build preparation にも到達しない。DW-M03/F28 上、これは KILL に数えられない。

成果物影響: trial report・journal の受理集合は下位 validator により不変だが、変異台帳の V1 を KILL と記録すると「main 層が pre-build admission を守る」という証拠参照が偽になる。

判定: 段6閉鎖の must-fix。provider を `claude-headless` にして competing-process/checkout poison へ到達させるなど、fixture/build の独立拒否に食われない入力へ再照準すること。

### A-06 [中] V10 は独立した二つの gate を一変異にしている

現条件 `:185-189` では個別変異を作れる。

- bool 拒否だけの削除: 最初の `isinstance(..., bool) or` を削除。`True` だけが受理されるため V9 は単一理由で成立する。
- 非 int 拒否だけの削除: 中央の disjunct を削除。`1.0` case だけが赤。
- 下限拒否だけの削除: range 条件から下限を除く。`0` case だけが赤。

ところが V10 は後二者を一件にまとめ、parametrize された二 node を同時に赤くする。単一理由性はない。

成果物影響: 下限回帰は generation 0 の空 trial を `complete` report として受理し、非 int 回帰は `range()` の素の `TypeError` を partial report/journal に変換する。両受理集合を一つの変異台帳行では個別保証できない。

判定: must-fix。V10a=`[0]`、V10b=`[1.0]` に分割すること。

### 既存テストへの波及

改名された `test_main_default_generation_budget_is_one` は、現在も明示的に `--provider fixture --no-build` を渡し、`assert_pinned_clean` sentinel まで到達させている (`test...py:378-390`)。fixture+no-build 受理の検出力は失われていない。ただし同じ node が「CLI default 1」と「fixture+no-build 受理」の二責務を持ち、名称は後者を表さなくなった。これは nit。

Python test 全体を対象に module 名・`run_trial`・`_run_workload`・両 generation 定数を検索した結果、対象テストファイル以外の consumer はなかった。`main()`、`run_trial()`、`_run_workload()` の in-repo 呼出しも同一 production module 内だけである。

## 変異 kill 判定表

以下は pytest を走らせず、制御フローから判定したもの。

| 変異 ID | 期待 node | 実際に赤くなるか | 他に赤くなる node | 単一理由性 |
|---|---|---|---|---|
| V1 | `test_main_rejects_unapproved_budget_before_build_preparation` | YES。regex mismatch | なし | NO。fixture+build の既存拒否で受理集合不変 |
| V2 | `test_run_trial_rejects_unapproved_budget_before_artifact_creation` | YES。下位 gate が partial report に変換し、期待した例外が出ない | なし | YES |
| V3 | `test_run_workload_direct_call_rejects_unapproved_budget` | YES。wall期限済みの空 result を返し `DID NOT RAISE` | なし | YES。ただし provider 実行ではなく direct-call admission の検査 |
| V4 | `test_run_workload_rejects_existing_campaign_state` | YES。provider poison が発火 | なし | 条件付き。call削除にはYES、実 state/layout 束縛にはNO |
| V5 | `test_generation_budget_boundary_at_ratified_launch` | YES。literal 1 が拒否される | gen1 の fixture trial、invalid-role、existing/fresh state、supervisor-error、CLI accept 3本 | YES |
| V6 | `test_main_default_generation_budget_is_one` と既存 CLI accept 群 | YES。default 2 が validator で拒否される | `test_cli_default_is_literal_one_by_ast` | YES |
| V7 | `test_generation_budget_boundary_at_ratified_launch` | YES。literal 2 が受理される | run_trial/direct workload/main の generation=2 負例3本 | YES |
| V8 | `test_cli_default_is_literal_one_by_ast` | YES。`ast.Name` となり `ast.Constant` assert が赤 | なし | YES |
| V9 | `test_generation_budget_rejects_bool` | YES | なし | YES。bool disjunctだけの削除を記述可能 |
| V10 | `test_generation_budget_rejects_zero_and_non_int[0]` / `[1.0]` | 条件付き。combined weakening なら両方赤 | 相互の parameter node | NO。下限と非 int は別変異 |
| V11 | `test_run_workload_rejects_existing_campaign_state` | YES。planner provider poison が発火 | なし | YES。provider より前という順序に限る |
| V12 | `test_invalid_role_is_single_attempt_and_stops_cell` | YES | なし | NO。2回目 attempt ではなく `planner.axis` の `AttributeError` |
| P1 | `test_generation_budget_boundary_at_ratified_launch` | YES | V5と同じ gen1 node 群 | YES |
| P2 | `test_run_workload_accepts_fresh_campaign_state` | YES | fixture trial、invalid-role、supervisor-error | YES。無条件拒否変異には有効 |
| P3 | boundary + 既存 CLI accept 3本 | YES | fixture trial、invalid-role、existing/fresh state、supervisor-error | YES |

## 試して不成立だった攻撃

- `main()` validator を fixture/build、pinned-clean、競合 benchmark、checkout より後ろだとする攻撃は不成立。実行順は `1051 < 1052 < 1063 < 1069 < 1074`。

- `run_trial()` validator が artifact 作成後だとする攻撃は不成立。`:883 < :897`。

- `_descriptor_for`、`_campaign_for`、`campaign_layout` が freshness gate 前に書き込むという攻撃は不成立。schema の読み取りと in-memory/path 構築だけだった。

- `_run_workload()` を含む通常 call pathで validator 呼出し自体を省く経路は見つからなかった。残ったのは A-01 の入力型迂回と、A-02 の「各 call は1だが並行連結」という経路。

- target module 内の `load_loop_state` 利用は freshness helper と `_whiteboard()` の二箇所だけで、後者の内部 caller は `_run_workload():690` のみ。driver 層の直接呼出しを除けば別経路はない。ただし両読込間の競合は A-02 のとおり成立する。

- boundary test は定数由来でなく literal `1` / `2` を実際に持つ (`test...py:72,74`)。F69 型の追随はない。

- `default=MAX_APPROVED_GENERATIONS` は AST test が確実に赤にする。`add_argument` を alias/helper/動的引数へ変えて該当 call が0件になっても、`:102` の `assert len(calls) == 1` で同じ node が赤になる。

- fixture+no-build の受理責務は改名後もコード上残る。他に同じ CLI 組合せを固定する node はないが、責務喪失ではない。

- `MAX_APPROVED_GENERATIONS=3` monkeypatch が片方の validator にしか効かないという攻撃は不成立。module global を呼出し時に読むため両方へ効く。

- `git diff --check` は rc=0。作業ツリーは指定2ファイルの変更だけで、レビュー中の書込みは発生していない。

## 確認できなかったこと

- pytest と mutation harness は実行していない。親確認の「19 passed」は前提として採用したが、独立再実走ではない。
- 表の赤 node は静的制御フロー判定であり、実際の pytest failure summary は採取していない。
- A-02 の並行 interleaving は、read-only 制約のため campaign artifact を作る動的再現をしていない。
- scope 外とされた injected `drive` と driver 層の直接反復については、新たな受入可否の裁定をしていない。