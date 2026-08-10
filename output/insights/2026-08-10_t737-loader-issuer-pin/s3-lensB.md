## 判定

静的レビューのみ。pytest・mutation・新規 node は未実走で、緑は主張しない。指定関数の呼び元は次のとおり。

- `load_activation_state`: `env_contract.py:524`、`ident.py:217`
- `validate_activation_records`: `env_contract_activation.py:488`、`ident.py:304`、issuer `:206`
- `current_activation_state`: issuer `:180`、定義 `env_contract.py:631`
- `_validate_activation_transition`: leaf 内 `:396` のみ（既存テストの直叩きは別）

`execution_guard.py:74` は検証済み receipt の state を消費するだけで、activation record を再読しない。`silo_ladder_rung1.py:1942` などは `env_contract.lookup()` → `REGISTRY` → `_authority_snapshot()` に入る同一 loader 経路である。したがって両者は独立した追加層ではないが、現 plan はその loader 自体を通せていない。

### B-01 — [real] 「層1」が production loader ではなく leaf 直呼び

- file:line: `s2-plan.md:51`, `s2-plan.md:67`, `env_contract.py:524`, `test_env_contract_activation.py:1544`
- 問題: plan の新規 node は `activation.load_activation_state()` を直接呼び、`env_contract._load_authority_snapshot()`、cache、`lookup()`、`authorize()` を通らない。既存 identity test も head と predicate は検査するが、`registered_contracts` identity は検査していない。
- 成果物影響: leaf pin が通っても、production loader の catalog/path wiring が誤っていれば certified lock が別の active state を参照し、certified 選択・proof chain の activation hash が変わり得る。
- 修正案（実装しない）: 実 loader を通す方法を採るか、「層1」を leaf integration と呼び直して production loader を scope 外の裁定パッケージへ返す。catalog identity の扱いも親裁定にする。

### B-02 — [real] `ident` が別の production activation 経路として漏れている

- file:line: `ident.py:217`, `ident.py:304`, `ident.py:467`, `artifact_admission.py:572`, `artifact_admission.py:661`
- 問題: `ident._load_current_activation_state()` は `env_contract` wrapper を経由せず leaf を直接呼ぶ。新規 campaign lock の作成・既存 lock の再検証・`artifact_admission` の certified admission がこの経路を使う。
- 成果物影響: transition gate の縮退がこの経路で通ると、`campaign.lock` の activation serial/state hash/contract hash が未承認 transition に束縛され、最終的に `admission_status="admitted"` の受理集合へ入る可能性がある。
- 修正案（実装しない）: `ident` 経路を production-loader 層へ明示的に含めるか、別層として pin する。含めないなら「certified admission までは閉じない」と裁定パッケージへ返す。

### B-03 — [real・条件付き] t720 の import topology と plan の monkeypatch が衝突する

- file:line: t720 `tools/issue_env_contract_activation.py:160`, t720 `tools/issue_env_contract_activation.py:163`, 現行 test `test_env_contract_activation.py:33`, `test_env_contract_activation.py:1986`
- 問題: t720 は issuer を `orchestrator.campaign.*` で読む一方、現 T-737 test は `campaign.*` の `ec` を patch する。`issuer.__file__` の patch は issuer の root 計算だけを変え、既に import 済みの `ec` や canonical module の `__file__` は変えない。
- 成果物影響: patch が別 module object に空振りし、issuer node が rc 期待に到達しない、または tmp ではなく実 authority の `00000002.json` を publish してテスト台帳を汚染する可能性がある（未実走）。
- 修正案（実装しない）: t720 の canonical import 変更と test 側変更を先行する atomic prerequisite とするか、T-737 をその snapshot へ再基底化する。`__file__` patch だけを seam とみなさない。

### B-04 — [realな計数、runtimeは未実走] M=65 のコスト見積りが過小

- file:line: `s2-plan.md:15`, `s2-plan.md:18`, `s2-plan.md:161`, `s2-plan.md:196`, `env_contract.py:219`
- 問題: 65 env・最後だけ g3 なら `validate_generations()` の隣接 edge は 65 ではなく 66。factory を5 nodeで毎回作るなら、factoryだけで `is_valid_successor` 66×5=330回、各 P/正例の実走査が260回、計590回になる。
- 問題: `is_valid_successor()` は `_leaf_json_pointers()` を predecessor/successor に各1回呼ぶ。linux base の構造では再帰呼び出しは約26回/判定なので、約1,180回の top-level、約15,340回の再帰呼び出しになる。計画上の record は5 node合計で約12本、65 row換算で780 row。
- 成果物影響: session 時間、受入 report の passed/time、台帳の試験件数が plan の「pin 1本 10^-2秒」「2 record×65 row」より増える可能性がある（runtime未実走）。
- 修正案（実装しない）: 実装後に runner 経由で増分を測り、N=64を要求するなら M=65を維持、N≤63まででよいなら M=64以下へ落とす択一を親が裁定する。

### B-05 — [real・将来条件付き] synthetic M は実 registry の成長を追随しない

- file:line: `s2-plan.md:11`, `s2-plan.md:15`, `s2-plan.md:163`, `env_contract.py:367`, `env_contract.py:417`
- 問題: 実 registry が3 envになっても、この test は `pin-env-000`〜`064` の synthetic registry を使い続けるため直ちには壊れない。しかし実 catalog の件数・順序・dynamic bound との関係は検査しない。
- 成果物影響: 将来 `successor_rows[:len(GENERATIONS)]` や `[:65]` のような実件数依存の縮退が入ると、synthetic 65では素通りし、issuer publish と certified lock の参照が静かに弱くなる。
- 修正案（実装しない）: 実 catalog との関係を pin するか、registry 件数・量化 bound の変更を再裁定 trigger として台帳化する。

### B-06 — [realな誇張] DW-G05 の「未登録世代」は因果を言い過ぎ

- file:line: brief `:87`, activation `:378`, activation `:385`, env_contract `:537`
- 問題: `validate_activation_records()` は active env 集合と generation/hash を先に registry へ照合する。未登録 generation/hash は `:387`/`:391` で拒否され、`current_activation_state()` から返らない。G の危険は、registry に存在するが transition/predicate 上は承認されていない世代の場合に限る。さらに「envが3個以上」だけでは、g+2 が registry にあるとは限らない。
- 成果物影響: 「未登録世代が certified proof chain へ入る」という記述は誤りだが、登録済みの非 successor が通れば `campaign.lock` と certified admission がその contract hash/state hash を参照する因果自体は成立する。
- 修正案（実装しない）: 「未登録」を「registry には存在するが承認済み transition ではない世代」に改め、G と P の発火条件を分けて記録する。

### B-07 — [real] 親 brief の current-state 被覆件数が少なくとも1件ずれている

- file:line: brief `:41`, `test_env_contract_activation.py:1507`, `test_env_contract_activation.py:1554`, `test_env_contract_activation.py:1647`
- 問題: brief は `current_activation_state()` の入口を3件とするが、forward activation の historical resolution test でも直接呼んでいる。入口の呼び出し数と「遷移違反を拒否する node 数」を混同している。
- 成果物影響: coverage inventory と report の層別件数が誤り、production loader/identity path の scope 判断を誤る。
- 修正案（実装しない）: test数・呼び出しsite・遷移違反の意味的被覆を別々に数え直す。

### B-08 — [realな過一般化] 「外部 pin 0件」は literal grep の範囲に限る

- file:line: brief `:46`, `pytest.ini:12`, `test_plain_runner_coverage.py:44`, `test_plain_runner_coverage.py:60`
- 問題: `test_env_contract_activation` という文字列の外部 hit がない、という観測自体は成立する。しかし pytest の directory collection、plain-runner の全 test file 列挙、`_run()` 契約は外部 consumer であり、t720 land 後は import invariant も operational source 全体を走査する。
- 成果物影響: test file の追加 node は受入 report/台帳の件数と時間を変え、harness/import invariant 違反時は受入集合そのものが赤になる。
- 修正案（実装しない）: 主張を「直接ファイル名を参照する pin は0件」へ限定し、collection・runner・並行 import invariant を別の外部依存として記録する。

## 総括

(a) **scope不足あり。** 実 `env_contract` loader と `ident` の certified admission 経路が未被覆。`execution_guard` と `silo_ladder_rung1` は独立 gate ではないため、別 pin は不要だが、上流 loader を本当に通す必要がある。

(b) **M=65はN=64まで殺す目的なら妥当。** ただし静的計数は約590 predicate、約15,340 recursive pointer call（factory再利用時は下限約326 predicate）で、時間主張は未実走。

(c) 親は、(1) G の「2層」を実 loader＋issuerに限定するか `ident` まで閉じるか、(2) t720 canonical importを先行条件にするか、(3) N=64を維持してM=65にするか、を裁定すべきである。