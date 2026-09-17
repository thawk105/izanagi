# 段 4 裁定 — [T-2706] per-command 上限の実測選定

裁定 inbox 再走査 (段 4 直前): main は `b4631a92e` のまま、spool は空。D2104 項 24 以外に本件を止める裁定なし。

## 所見の裁定

| id | 判定 | 採否 | scope | 理由・反映 |
|---|---|---|---|---|
| A1 | real | 採用 | 内 (記述) | 不変なのは「決定的証拠 → verdict の受理条件」。時間制約込みで確定できる入力集合は変わり、観測層 (`cherry`) の待ちが延びて終端 ref 確認が予算切れになる逆向きもあり得る。brief の不変条件を書き直す (下記)。 |
| A2 | real | 採用 | 内 (記述) | 「観測は verdict に触らない」→「観測結果は判定根拠にしないが、実行時間は確定可能性に影響する」。 |
| A3 | refuted | 採用 (説明) | 内 | any-path 探索の完走で出る `not-landed` は closed-world の負証拠による判定 (D922 項 4)。上限は証拠の取得可否を左右するだけ。 |
| A4 | real | 採用 | 内 (記述) | 捕捉は 10 箇所。brief の 8 は誤り。 |
| A5 | real | 採用 (記録) / OSError は不採用 | 記録のみ | timeout の入口は `TimeoutExpired` 以外に残余予算検査 6 箇所 (`:214,748,1144,1216,1243,1246,1535〜1541`)。`OSError` 未捕捉は偽判定経路ではなく本 wave 外 (carry に記す)。 |
| A6 | real | 採用 | 内 (記述) | 「重いのは path log だけ」「中央値に 5 秒」「30/30 は決定的」を撤回。10 件時点: path log 中央値 3.5 秒 / p95 8.2 / 最大 10.1、find-object 13.6 / 19.5、cherry 最大 9.1。 |
| A7, B4, B5 | real | 採用 | 内 | 模擬は「記録した command 列を無中断で再現できる推計」と呼ぶ。観測層 `cherry` は上限まで待って続行に直した (簡略)。実測完走率は新定数で 30 件を再実走して出す。 |
| A8, B10 | real | 採用 | 内 (記述) | test は「実 TimeoutExpired の変換」「proof / any-path からの伝播」「既定値と定数の一致」「有界」を示す。「受理集合不変の証明」とは呼ばない。負証拠経路 (any-path) の timeout test を足す (下記 plan v2)。 |
| A9 | refuted | 採用 (方式維持) | 内 | 偽 git は PATH で効く。selector 誤実装対策に到達回数・実 `TimeoutExpired`・phase を検査。 |
| A10 | refuted (scope 逸脱なし) / 字義は real | 採用 | 内 | 「製品の動作変更は定数 1 行」と書き直す。docs・fragment は仕様拡張でない。 |
| B1 | real | 採用 | 内 | 倍率は候補生成則。採用値は「上限超過 0 本」「反復点検」「予算内の完走率」の 3 点で決める (下記規則)。 |
| B2 | 根拠不足 → 採用 | 採用 | 内 | 30 件完了後、重い 3 操作 (`log -- <path>` 最大例、`log --find-object` 各例、`cherry` 最大例) を固定引数で各 3 回反復し、分散を点検する。cache 排除はしない。 |
| B3 | real | 採用 | 内 (記述) | 「有界」= `0 < c ≤ DEFAULT_TIMEOUT_SECONDS (60)`。実効上限は `min(c, B − 経過)`。CLI 300・rescue 8/60 は別物。 |
| B6 | refuted (強すぎ) | 採用 (記述) | 記録 + carry | rescue 内部予算 8 秒では 5 → 8 超の変更は「残余 5 秒超の操作」にだけ効く。rescue の実用性は本 wave で解消せず、内部予算と外側 timeout の配分は裁定パッケージ候補として記録。 |
| B7 | real | 採用 | 内 (記述) | 60 秒で判定可能な範囲 = 「各必須操作が cap 内、必要な探索 + 観測待機 + 終端 ref 確認の合計が 60 秒内」。unit 数だけでは定義しない。 |
| B8 | real | 採用 | 内 (記述) | 「この repo で 1 件も判定できない」→「対象 30 件・観測条件で 0 件」。完走率と確定判定率を別に報告。 |
| B9 | real | 採用 | 内 | 専属 killer とは書かない。主担当 node と全検出 node を分けて登録。 |
| B11 | real | 採用 | 内 | 集計器を nearest-rank・打切り区別・同一 OID 重複検出に直した (済)。 |

## plan v2 (author 1 本)

製品の動作変更は `tools/check_branch_landed.py:38` の定数 1 行だけ。

1. `tools/check_branch_landed.py:38`: `COMMAND_TIMEOUT_SECONDS = <値>`。直前 1〜2 行のコメントに「実測日 2026-09-17、pegasus02 login node、main 11,246 commit / 176k object、到達不能 commit 30 件の Git 操作別最大 (path log / find-object / cherry) と規則 (最大 × 1.5 を格子へ切り上げ、上限 60)」を書く。**暫定値は 30.0** (10 件時点の最大 19.476 秒 × 1.5 = 29.2 → 格子 {10,15,20,30,45,60} の 30)。30 件完了後に規則の出力が変われば fix 子で値とコメントだけ直す。
2. `orchestrator/tests/test_check_branch_landed.py` (`test_global_timeout_is_indeterminate_json` の直前に挿入):
   - `test_command_timeout_default_is_bounded_and_bound`: `0 < COMMAND_TIMEOUT_SECONDS <= DEFAULT_TIMEOUT_SECONDS` と `inspect.signature(Git.run).parameters["command_timeout"].default == COMMAND_TIMEOUT_SECONDS` (値の一致、`is` は使わない)。
   - `test_git_run_real_command_timeout_is_truncated`: PATH 先頭の偽 git (`exec <絶対 sleep> 2`) で `Git(tmp_path, monotonic()+60).run(["status"], command_timeout=0.05)` が `AssessmentError` (code `assessment-timeout`、outcome `truncated`、`__cause__` が `subprocess.TimeoutExpired`)、`command_count == 1`。
   - `test_assess_real_log_timeout_is_indeterminate_not_a_verdict` を `@pytest.mark.parametrize("form", ["proof-path-log", "any-path-find-object"])` × `@pytest.mark.parametrize("delayed", [True, False])` で 4 node:
     - fixture: `proof-path-log` は `_history_fixture(tmp_path, "f")` (main tip で削除済み → `:777` の path log へ到達)、`any-path-find-object` は `test_true_pure_add_is_not_landed_with_closed_world_reason` と同じ pure-add 構成 (`_init_repo` + `_topic` + `unique.txt`)。
     - 偽 git: 先頭の `-c VALUE` 群を読み飛ばして subcommand を識別し、対象 (`log` かつ `--find-object=` の有無で form を判別) だけ `delayed` なら `exec sleep 2`、それ以外は `exec <本物 git> "$@"` (全引数保持)。
     - `Git.run` を薄く包み、対象 command だけ `command_timeout=0.05` を明示 (delayed=False でも同じ上限を渡す: 本物は 0.05 秒未満で終わらないことがあるので、**delayed=False では上限を渡さず既定のまま**にする。つまり wrapper は delayed=True のときだけ明示上限を渡す)。到達回数と `__cause__` を記録。
     - 期待: `delayed=True` → decision `indeterminate` / `assessment-timeout` / `landed=None` / `conclusive=False`、`phase_outcomes["proof"] == "truncated"`、`negative_paths == []`、`branch_delete_authorized is False`、対象到達 1 回・実 `TimeoutExpired` 通過。`delayed=False` → `proof-path-log` は `landed` / `exact-state-in-main-history` (`_history_fixture` の既存期待に合わせる)、`any-path-find-object` は `not-landed` / `closed-world-negative-proof`、`negative_paths == ["unique.txt"]`。**同じ偽 git 経路で、上限に掛かるか否かだけが違い、verdict は証拠から出る** — これが本 wave の正例・負例の対。
   - 既存 test は変更しない。
3. 親: insight README (`output/insights/2026-09-17/t2706-landed-timeout/README.md` + `evidence/`)、worklog / decisions fragment。

scope 外 (不変): CLI 追加、retry、timeout 基盤、`DEFAULT_TIMEOUT_SECONDS`、rescue の予算、探索方式、`OSError` 捕捉、gate・台帳の追加。

## 不変条件 (書き直し)
- 規律 2: **決定的証拠 → verdict の受理条件は不変** (`landed` は exact state / receipt 一致からだけ、`not-landed` は closed-world 負証拠からだけ、決定的探索の打切りは `indeterminate`)。時間内に確定できる入力集合は変わる (それが目的) — 広がる方向が主だが、観測層の待ちが延びて終端 ref 確認が落ちる逆向きも理論上あり、実測で件数を出す。
- `Git.run` の `min(command_timeout, remaining)` 構造、CLI 引数集合、JSON schema 名は不変 (`issues` / `phase_outcomes` の内容は変わり得る)。
- 製品の動作変更は定数 1 行。

## 値の決め方 (事前登録、30 件完了後に親が適用)
1. 30 件の JSONL を固定 (sha256 を README へ)。打切り・error の command は別集計 (cap 300 で打切りは無い見込み)。
2. 操作別に n / 中央値 / p95 (nearest-rank) / 最大。決定的経路と観測層を分ける。
3. 候補格子 {10, 15, 20, 30, 45, 60}。採用値 c = 格子のうち「全 command の最大 × 1.5 以上」の最小値、ただし c ≤ 60。倍率 1.5 は親の判断値であり導出値ではない。B2 の反復点検 (重い 3 操作 × 3 回) で観測した最大が c を超えたら次の格子へ上げる。
4. 各候補 × 予算 {8, 60, 120, 300} の無中断推計表 (完走 : 確定) を出す。採用 c で予算 60 の実測完走率・確定判定率を、新定数で 30 件を実走して出す (対照 = 旧 5.0 の 0/30、entry 1552)。
5. 8 秒 (rescue) 欄は「内部予算」としてだけ比較し、rescue 呼出し全体の完走率と混同しない。

## 変異事前登録 (実装後、段 6 で位置と赤理由を確認)

| id | 位置 | 変異 | 主担当 node | 他の検出見込み |
|---|---|---|---|---|
| M0 | `:38` 直前の根拠コメント | コメント文言だけ変更 | (等価、SURVIVED 期待) | — |
| M1 | `Git.run :239〜242` | `TimeoutExpired` を握り潰し空 stdout の `CompletedProcess(returncode=0)` を返す | `test_git_run_real_command_timeout_is_truncated` | assess 系 delayed=True 2 node (到達後に例外が出ず verdict が変わる / parse error) |
| M2 | `:241` | `outcome="truncated"` → `"error"` | `test_git_run_real_command_timeout_is_truncated` | assess 系 delayed=True (`phase_outcomes["proof"]`) |
| M3 | `:210` | 既定引数を `COMMAND_TIMEOUT_SECONDS` から旧値リテラル `5.0` へ | `test_command_timeout_default_is_bounded_and_bound` | — |
| M4 | `:38` | 定数を `61.0` (`DEFAULT_TIMEOUT_SECONDS + 1`) | `test_command_timeout_default_is_bounded_and_bound` | — |
| M5 | `assess` 最上位 except `:2000` 付近 | `_decision("indeterminate", code)` → `_decision("landed", code)` | assess 系 delayed=True 2 node | `test_global_timeout_is_indeterminate_json`、`test_global_exception_marks_the_active_phase` 他 |
| M6 | `_regular_decision :1354〜1355` | `any_path.incomplete` → `indeterminate` を削除し `not-landed` へ落とす | `…[any-path-find-object-True]` | (any-path timeout は最上位へ伝播するため、この変異は M5 と同時でないと発火しない可能性 → 実装後に到達を確認し、不到達なら登録から外す) |
| M7 | `history_scan :1753〜1758` | 不完全 scan でも負例 unit を `indeterminate` へ戻さない | 既存 `test_history_scan_limit_is_indeterminate_and_measured` | — |

新規 test file は無い (既存 file へ追加) ので allowlist / lineno pin には当たらない見込み。
