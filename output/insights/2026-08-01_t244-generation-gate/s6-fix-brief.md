# 段 6 所見の裁定と fix 指示 — [T-244]

親が段 6 レビュー A/B の所見を real/refuted・採用/不採用に裁定した。fix は 1 単位 (一枚岩) とする。
**単一化の理由**: A-01 が validator の型述語を変え、それが V9/V10 の変異意味論とテストを変える。
A-03 と B-01 はどちらも freshness helper とその同じテスト群を触る。所有が分離できない。

## 採用する fix (production + テスト)

### FIX-1 [致命・A-01] `int` サブクラス迂回を塞ぐ

現 validator は `isinstance(generations, int)` しか要求しないため、`__add__` を上書きした
`int` サブクラスを値 1 として申告しつつ `range(1, x + 1)` で複数世代を回せる。
report と campaign ID の `generation_budget` は 1 のまま、journal / WAL には複数 generation が入る。

**修正**: 型検査を exact built-in `int` に閉じる。判定を次の 3 段に**分離**すること
(1 つの `if` に畳まない — 変異の単一理由性のため)。

1. `type(generations) is not int` → 契約違反 (bool と int サブクラスを一括で閉じる)
2. `not 1 <= generations <= MAX_GENERATIONS` → 契約違反
3. `generations > MAX_APPROVED_GENERATIONS` → 未裁定運転

既存のメッセージ文言 (「1..{MAX_GENERATIONS} 必須」「承認済み上限」) は変えないこと。
既存テストの `match=` が依存している。

**テスト追加**: `int` サブクラスで `__add__` を上書きした値が拒否されることを固定する負例。
実際に `range(1, x + 1)` が複数要素を返す型を使い、「validator が受理してしまえば複数世代が回る」
ことをテスト内で示すこと (positive control の実質化)。

### FIX-2 [高・A-03] freshness テストが実 state を検査していない

現テストは `load_loop_state` を layout 引数を無視して monkeypatch するため、
production が「常に空の別 layout を検査する」形に退行しても全テストが緑になる。

**テスト追加**:
- 実 layout に実際の `loop_state.json` を書き (`save_loop_state` 等の正規経路を使う)、
  monkeypatch なしで拒否されることを固定する負例。
- 実 layout が本当に空のとき monkeypatch なしで受理されることを固定する正例。
- 既存の monkeypatch 版 2 本は削除せず、**provider 呼び出し順序の poison test** として責務を明示する
  (docstring かテスト名で責務が分かるようにする)。

layout の実体がどこに作られるかは production の `_run_workload` を読んで確認すること
(`do_build=False` なら `<run_root>/campaigns/<campaign-id>`)。

### FIX-3 [高・B-01] 壊れた checkpoint が素の例外で貫通する

`_assert_fresh_campaign_state` は `load_loop_state` を無捕捉で呼ぶ。壊れた JSON・schema 違反・
`delta_pct` leak では `ValueError` / `WhiteboardLeakError` が supervisor 契約の外へ漏れる
(F68 型)。

**修正**: checkpoint の読取・decode・schema 検査の失敗を捕捉し、
**cause を保持したまま** `AutonomousTrialError` に包む (`raise ... from exc`)。
**壊れた state を `None` (= fresh) と扱ってはならない。**

**テスト追加**: 実ファイルに壊れた JSON を書いた場合と、`delta_pct` が非 None の checkpoint を
書いた場合の 2 本。いずれも `AutonomousTrialError` になり、かつ `__cause__` が元例外であることを固定する。

### FIX-4 [中・A-05 / B-02 が独立に一致] V1 の期待 node を再照準

`test_main_rejects_unapproved_budget_before_build_preparation` は `--provider fixture` かつ
`--no-build` なしのため、validator を削除しても直後の fixture+build 拒否が発火する。
赤の理由は診断文字列の差だけで、受理集合は変わらない。DW-M03 が KILL から除外する型である。

**修正**: このテストを `--provider claude-headless` の正当な build 経路に差し替える。
validator を削除したとき `competing_bench_pids` / `checkout` / `assert_pinned_clean` の
poison sentinel に**実際に到達する**こと。到達すれば `pytest.fail` で赤になる。

### FIX-5 [高・A-04] V12 の期待 node が別理由で赤くなる偽 KILL

planner-invalid 分岐の `break` を単純削除すると `planner is None` のまま属性参照で
`AttributeError` になり、`run_trial` の広い except が `supervisor-error` cell に置換する。
赤にはなるが、理由は「2 回目を試した」ではない。

**修正 (テスト側のみ)**: `test_invalid_role_is_single_attempt_and_stops_cell` に
**planner provider の呼び出し回数を直接 assert** する検査を足す (呼び出しを数える planner を使う)。
`break` → `continue` の変異で呼び出し回数が増えることを検出できる形にすること。
production の `break` は変更しない。

## 採用しない (real だが scope 外) — 親が裁定パッケージへ送る

- **A-02 [致命] freshness 判定と state 消費の TOCTOU / 並行 race。**
  real と認める。ただし修正には campaign 単位の原子的 reservation (lock 取得・stale lock 処理・
  異常終了時の解放) という独立した設計が要る。並行実行は計測規律 (単独性確認) が既に禁じており、
  build 経路は `competing_bench_pids()` が部分的に覆う。本 wave では実装せず、
  **docs に「並行 start race は保証対象外」と明記**して裁定パッケージへ送る。
  fix 子はこれを実装してはならない。
- `test_main_default_generation_budget_is_one` が「CLI 既定値 1」と「fixture+no-build 受理」の
  二責務を持つ点 → nit。改名しない。
- 1 cell が stale だと同 invocation の後続 workload も止まる点 → docs に書く。実装は変えない。

## refuted

- 「改名で fixture+no-build 受理の検出力が失われた」→ refuted。レンズ A が実測で
  「明示的に `--provider fixture --no-build` を渡し sentinel まで到達している」と確認した。
- 「V2 が受理集合拡大の証拠になっていない」→ 部分的に正しいが nit。V2 は
  「artifact 作成前に拒否する」ことの証拠として登録しており、台帳にその意味で記録する。

## 変異事前登録の改訂 (親が harness を再作成させる)

fix 後に次のとおり改訂する。fix 子はこの表を実装対象としないが、
**テストがこの表を kill できる形になっていること**を満たすこと。

| ID | 改訂内容 |
|---|---|
| V1 | 期待 node を `claude-headless` build 経路版へ差し替え (FIX-4) |
| V9 | `type(generations) is not int` → `not isinstance(generations, int)`。期待 node = bool 負例 + int サブクラス負例 |
| V10a | 下限 (`1 <=`) の削除。期待 node = `0` の負例 |
| V10b | 上限 (`<= MAX_GENERATIONS`) の削除 → **等価変異 (承認上限が先に拒否するため受理集合が変わらない)。`unattributable` へ回し登録しない** |
| V12 | `break` → `continue`。期待 node = planner 呼び出し回数を assert するテスト |
| V13 (新規) | FIX-3 の `try/except` を外す → 壊れた checkpoint 負例 2 本が赤 |
| V14 (新規) | FIX-1 の型検査を `isinstance` に戻す → int サブクラス負例が赤 (V9 と重複するため V9 に統合可) |
| P4 (新規) | freshness 判定を「実 layout でなく固定の空 layout を見る」形に変更 → 実 state 負例が赤 (FIX-2) |
