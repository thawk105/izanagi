# 段 4 裁定 — [T-2650]

## 所見の判定 (real / refuted、採用 / 不採用、scope 内 / 外)

### レンズ A (sol)

| # | 所見 | 判定 | 採否 |
|---|---|---|---|
| A1 | 「受理集合不変」の表現が不正確。正しくは「判定規則は不変、依存欠落による検査不能を解消」 | real | 採用 (記録の文言) |
| A2 | `preprocess-failed` 全件を同一原因と扱えない | real | 採用 (射程を観測 3 走行に限る) |
| A3 | plan の argv 比較 test は恒真の罠に落ちない。実 CMake の負例を足すなら base と source を分離する | real | 採用 (下記 C の必須条件) |
| A4 | 凍結波及なし。ただし `condition_meaning_gate.py:3718-3726` は root-location-only 分岐限定で、一般検査ではない | real | 採用 (記録の訂正) |
| A5 | (P1-a) real だが床値の token は 5 本でなく 4 本 | real | 採用 |
| A6 | (P1-b) real だが「D424 に gate の明文免除がある」とは書けない | real | 採用 (引用精度) |
| A7 | (P1-d) refuted | real | 採用 → must-fix |
| A8 | 親の「12 cell / sort_best 2 件」から過去 3 走行の prebuild 実行を一般化できない | real | **採用し、親が実測で閉じた** (下記) |
| A9 | `CMAKE_PREFIX_PATH` は job script が環境変数で供給する。「prefix は供給されない」は誤り | real | 採用 |

### レンズ B (luna)

| # | 所見 | 判定 | 採否 |
|---|---|---|---|
| B1 | config.h の生成先と gate へ渡す dir は一致する。実機での生成先は `/scr/<job>/izanagi-floor-fetchcontent/masstree-src/config.h` | real | 採用 (確認) |
| B2 | prebuild → cell ループの順序は保証され、resume にも抜け道がない | real | 採用 (確認) |
| B3 | prebuild 後の pristine 再検査は `tracked_only=True` なので config.h で赤にならない | real | 採用 (親の独立確認と一致) |
| B4 | 他 `prepare_cell` consumer への波及なし | real | 採用 (親の独立確認と一致) |
| B5 | 非 sort 単独 campaign には同じ欠落が残る | real | **scope 外** → 裁定パッケージ / 次の一手へ |
| B6 | gflags/glog 無しで生死確認できる。既存の実 compiler / 実 CMake fixture がある | real | 採用 → must-fix の実現手段 |
| B7 | (P1-d) refuted、重大度 高。完了判定の must-fix | real | 採用 |

### 親が実測で閉じた点 (A8 への回答)

sol の反証は正当な提起なので、親が現物で確かめた。

- `git diff --stat c185b9fd4 262c2993e -- output/s8b-freeze/holdout_freeze.json output/s8b-freeze/floor_protocol.json`
  は **差分ゼロ** (3 走目の source commit と現行 main で freeze bytes が同一)。
- `git show c185b9fd4:orchestrator/campaign/s8b_floor_campaign.py` の 4259-4260 行は現行と同一の
  `if production_floor_path and any(cell.get("configuration_id") == "sort_best" for cell in cells):`。
- 現行 worktree で `enumerate_cells(holdout_freeze.json, stock_configuration=floor_protocol.json)`
  は **12 cell、sort_best 2 件**。

したがって走行時も条件は成立しており、traceback が `_build_cells_impl` の
`_prepared_binding` 行に到達している事実と併せ、**prebuild ブロックは例外なく通過していた**。
一般化は成立する。ただし「prebuild が成功裏に masstree を build し終えた」ことの**直接の受領証**
(`sort-swo-oracle-dependency.json` 等) は job 終了で消えており未照合である。これは記録に書く。

## 裁定 (プラン v2)

plan を**採用する**。ただし scope を 3 点に確定し、完了判定を訂正する。

**(A) 配線** — `orchestrator/campaign/s8b_floor_campaign.py`
prebuild が使った `fetchcontent_base_dir` と 3 依存の staged source dir から、既存生成器
`p3_s4_loop._condition_gate_offline_configure_args` で configure 引数を作り、
`_FloorOracleDependencyBinding` の内部搬送 field で持ち回し、`floor_prepare` から
`prepare_cell(condition_configure_args=...)` として**全 cell へ**渡す。
`cache_receipt()` / `private_dict()` には足さない。`4332` の分岐は維持し sort 判定の内側へ移さない。
`4434-4473` の sort 限定 build 注入は変更しない。

**(B) 配線 pin test** — `orchestrator/tests/test_s8b_floor_campaign.py`
gate の configure argv の offline token が prebuild の入力と一致することを pin する。
**床値は 4 本** (`FETCHCONTENT_BASE_DIR` + `FETCHCONTENT_SOURCE_DIR_{MASSTREE,MIMALLOC,GOOGLETEST}`)。
先例の「ちょうど 5 本」を写さない。値・本数・名前集合・重複の有無まで見る。
全 cell へ渡ること、非 sort の build binding が広がっていないことも pin する。

**(C) 生死確認の正例・負例 (本 wave の完了判定)** — 同 file
既存の `orchestrator/tests/condition_gate_test_support.py` の実 compiler / 実 CMake fixture
(`condition_gate_compilers()`、`install_condition_gate_build_fixture()`) を使い、
gflags/glog を要さない最小 project で次の対照を取る。

- 正例: owner TU が `#include <config.h>` を持ち、`config.h` を実在させた source dir を
  `FETCHCONTENT_SOURCE_DIR_MASSTREE` 相当で include path に載せると supply arm が緑になる。
- 負例: その SOURCE_DIR を落とす / `config.h` の無い dir へ向けると `preprocess-failed` になる。
- **必須条件 (A3)**: base dir と source dir を**別 path**に置く。一致させると CMake の既定命名
  `<BASE_DIR>/<name>-src` が拾い、負例が baseline から恒真に緑になる。
- compiler / cmake が無い環境では skip してよい (既存 fixture の作法に従う)。

**不採用 / scope 外:** 非 sort 単独 campaign への prebuild 新設 (B5)。`tools/pegasus/*.sh` の編集。
新しい `cmake --build` 起動点。materializer 登録簿の変更。

## 完了判定の訂正 (P1-d refuted を受けて)

本 wave の完了は **(A)(B)(C) が緑** までとする。
**「official 床値 campaign が cell build 段を越えた」は本 wave では未確認**であり、
実機再投入を要する別タスクである。記録にそう明記し、緑を実機通過と読み替えない。

## 変異事前登録 (DW-M01、実装前登録)

位置で登録する。単一理由性は実装後に確認し、満たさなければ登録せず実効 gate へ再照準する。

| ID | 位置 | 変異 | 期待 |
|---|---|---|---|
| M1 | `floor_prepare` の `prepare_fn(...)` 呼び出し | `condition_configure_args` の実引数を `()` へ置換 | KILLED |
| M2 | binding へ格納する引数生成の呼び出し | `masstree_source_dir` と `googletest_source_dir` を入れ替え | KILLED |
| M3 | prebuild 後の binding 格納 | 搬送 field への格納を削除し既定の空 tuple のままにする | KILLED |
| M4 | `floor_prepare` の適用条件 | `condition_configure_args` を `sort_best` cell のときだけ渡す形へ退行 | KILLED |

期待 node は実装確定後に確定させ、`DW-M08` に従い完全集合で pin する。

## 段 5 の分割

実装子 1 本。所有 = `orchestrator/campaign/s8b_floor_campaign.py` と
`orchestrator/tests/test_s8b_floor_campaign.py` の 2 file のみ。新しい test file を作らない。
