# [T-244] P3 critic 後置 (U-8) — 段 4 裁定の訂正 (v5、v3 §2 の 2〜4 を置き換える)

## 1. 実装子が検出した第 3 の矛盾 (real、採用。親の指示の誤り)

v3 §2 の 2 は「`_finish_trial` の**全 workload 実行後のループ**で二相処理する」と書いた。
これは trial 全体を 1 バッチにする指示であり、複数 workload では順序が壊れる。

- journal: `A の P/C/A → B の P/C/A → A の critic → B の critic`
- report 平坦化: `A の P/C/A/critic → B の P/C/A/critic`
- `_check_attempt_sequence` (`autonomous_trial_completeness.py:857`) が必ず拒否し、
  既存正例 `test_fixture_trial_runs_ycsb_abc_and_binds_descriptor`
  (`test_p3_autonomous_workload_trial.py:633`) が赤くなる。
- これは v3 自身の「1 世代の受理集合は不変」と両立しない。

**判定: real / 採用。親の記述ミスである。** 段 4 の裁定表 §2 で親自身が「per-cell (workload 単位) で
`admission1 < critic1 < admission2 < critic2` になる」と実測していたのに、v3 の文面が
trial 全体のバッチになっていた。実装子の指摘どおり **workload ごとの処理**が正しい。

## 2. プラン v5 (v3 §2 の項目 2〜4 を次で置き換える。項目 1 と 5 は不変)

**二相処理 (admission 確定 → pending critic 呼び出し) は、`_finish_trial` の workload ループの中で、
その workload の `_run_workload` が返った直後に行う。**

`_finish_trial` の workload ループを次の形にする。

1. wall budget 検査 (現行のまま。cell を作らず break)。
2. `try: cell = _run_workload(...)` / `except: ...` は現行のまま。例外時は現行どおり cell を復元し
   `cells.append(cell)` して `break` する。
3. **正常系は `cells.append(cell)` の後、`try` の外で**その cell に対し:
   1. `do_build` なら `_finalize_build_cell_admission(cell, launch_admission=launch_admission)`、
      そうでなければ `cell["admission_decision"] = {"admission_status": "not-applicable"}`。
   2. cell の pending critic を pop し、**admission 確定後**に generation 順で critic を呼ぶ。
      critic digest 生成と `require_admitted_campaign` もここで行う。
   3. critic が `None` を返したら `cell["stop_reason"] = "role-invalid"` とし、
      **harness 由来の stop より優先**する。admission decision は巻き戻さない。以降の critic は呼ばない。
   - この処理は `try` の外にあるため、finalizer 由来の例外はそのまま伝播する
     (B S-01 は追加 guard なしで満たされる)。
4. **ループ後の後始末パス**: `admission_decision` を持たない cell (= 例外から復元された cell) だけを
   対象に、同じ二相処理を行う。`stop_reason` は `supervisor-error` のまま変えない
   (critic invalid でも上書きしない)。この cell は必ず最後の cell なので順序は壊れない。
5. **`status` の算出 (`:1352-1362`) は上記すべての後**へ置く。式は変えない。
6. report 構築の直前に、どの cell にも pending が残っていないことを確認し、
   残っていたら `AutonomousTrialError` を送出する。

### 得られる順序 (親の確認)

- 単一 workload・1 世代: journal `P,C,A,critic` / report `P,C,A,critic` → **一致**。
- 複数 workload・1 世代: journal `A:P,C,A, A:critic, B:P,C,A, B:critic` /
  report `A:(P,C,A,critic), B:(P,C,A,critic)` → **一致**。既存正例は緑のまま。
- 多世代 (cap を上げた場合のみ): journal `g1:P,C,A, g2:P,C,A, crit1, crit2` /
  report `g1:(P,C,A,crit1), g2:(P,C,A,crit2)` → **不一致 → report publish 前に fail-closed**。
  これが v3 §「受理集合の変更」で記録した唯一の受理集合変更である。

## 3. v3 / v4 からの他の変更

なし。v3 §2 の項目 1 と 5、§3 の 1〜7、§4 (変異事前登録)、§5 (scope 外所見)、
v4 §3 (既存 2 行の追随許可) はそのまま有効。

変異 M1 の位置は「`_finish_trial` の workload ループ内の二相処理」と読み替える。
