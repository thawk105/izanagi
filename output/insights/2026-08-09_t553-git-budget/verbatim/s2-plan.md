read-only で全指定資料と対象コードを全文確認した。変更・commit・pytest 実行はしておらず、緑は主張しない。推奨実装は「stdin の LF-framed 実要求数から `_git` 内部で算出する単一予算」である。ただし rate の校正には `--batch-check` だけでなく blob bytes を返す `--batch` の実測が必須となる。

## 1. 予算算出関数

対象は [s8c_preregistration.py:87](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/campaign/s8c_preregistration.py:87) と同ファイル現 `:880` の直前。

- 名前: `_git_timeout_budget_seconds`
- 置き場所: 現 `parse_preregistration_worktree():875-877` の直後、現 `_git():880` の直前
- signature:

```python
def _git_timeout_budget_seconds(stdin: Optional[bytes]) -> float:
```

- 実要求数:

```text
R(None) = 0
R(b"") = 0
R(x) = x.count(b"\n") + int(not x.endswith(b"\n"))
```

末尾 LF のない fragment も 1 要求として数え、過小予算にしない。`bytes.splitlines()` は LF 以外も separator とみなすため、Git の LF-framed protocol には使わない。

- 予算:

```text
B(R) = min(
    GIT_TIMEOUT_SECONDS + R × GIT_TIMEOUT_RATE_SECONDS_PER_REQUEST,
    GIT_TIMEOUT_CAP_SECONDS,
)
GIT_TIMEOUT_CAP_SECONDS
    = GIT_TIMEOUT_SECONDS
      + MAX_BATCH_REQUESTS × GIT_TIMEOUT_RATE_SECONDS_PER_REQUEST
```

これにより `R=MAX_BATCH_REQUESTS` でちょうど cap、以降は一定となる。`stdin is None` と `R=0` は現行 15 秒を維持する。

### blob bytes の判断

[`_batch_blob_bytes():1133-1179`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/campaign/s8c_preregistration.py:1133) は、同じ R でも `cat-file --batch` の payload が最大 `MAX_TOTAL_BLOB_BYTES = 64 MiB` まで変わる。したがって、行数は所要時間の物理モデルとしては不十分である。

ただし実行前の `_git` が知る stdin は OID 行だけで、実 blob size は分からない。次の案は採らない。

- `_batch_blob_bytes` から `sum(sizes)` を渡す: caller-controlled な予算入力となり条件①に反する。
- `_git` が別の `batch-check` を先行実行する: subprocess の失敗機会と reason-code 境界を増やし、条件②に反する。
- stdin byte 数を使う: OID/path の長さであって blob payload を表さない。
- `--batch` を常に CAP にする: 実要求数比例ではなくなり、R1 の裁定より広い緩和になる。

したがって、production の runtime 量は R のみとする一方、rate 校正の実測量には output bytes `S` を必ず含める。既存の per-blob 16 MiB と total 64 MiB 上限（`:1153-1159`）を固定 envelope として、R-only 式へ byte-cost の最悪観測を織り込む。結論は「行数比例は bounded envelope として採用可能だが、`--batch-check` だけの実測では不足」である。

### RATE の決定式と手順

親が取得する各計測 cell を `c=(mode, R, S, cache状態, contention条件)`、同一 logical invocation の wall time を `t(c,j)` とする。

```text
U(c) = max_j t(c,j)
RATE_raw = max_{c:R(c)>0} U(c) / R(c)
RATE = probe の固定 decimal precision へ上向き丸めた RATE_raw
CAP = BASE + MAX_BATCH_REQUESTS × RATE
```

`(U-BASE)/R` にはせず `U/R` を使い、既存 BASE 15 秒を観測値に対する余裕として残す。timeout で打ち切られた観測は捨てず、probe 自身の観測上限だけを上げて uncensored な値を取る。

必須 cell は以下。

- competing compute node 上の `cat-file --batch-check`: `R=7,002` と `R=50,000`
- 同条件の `cat-file --batch`: 現実の unique-OID集合、および `S` が実上限近傍となる合法 fixture
- 特に「少数 R・大きい S」を含め、bytes 支配を rate に反映
- 48 同種並列だけを full-suite 混合負荷の同値物とは主張せず、first/cold 側と warm 側を別記録

`--batch-check` の結果しか得られない場合は RATE を確定せず、段 4 へ「blob cell 不足」と返す。

## 2. `_git` の改造

[`_git():880-906`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/campaign/s8c_preregistration.py:880) は signature を一切変えない。

1. 現 `:881-882` の `git-input-limit` を最初の処理としてそのまま残す。
2. その直後に `timeout_seconds = _git_timeout_budget_seconds(stdin)` を一度だけ計算する。
3. 現 `subprocess.run():885-893` は一回のまま、`:892` のみを `timeout=timeout_seconds` にする。
4. tempfile、入力、出力収集、`check=True` は変更しない。chunk 化もしない。
5. 現 `:895-906` の出力検査・例外節は byte-identical に保つ。

発火条件の保存は次の構造で担保する。

- `git-input-limit`: subprocess と予算計算より前に `len(stdin) > MAX_GIT_INPUT_BYTES`
- `git-output-limit`: subprocess 成功後の `stdout.tell() > MAX_GIT_OUTPUT_BYTES`
- `git-timeout`: `subprocess.TimeoutExpired` のみ。R2 により時間閾値だけが裁定済み変更
- `git-failed`: `OSError` または `CalledProcessError` のみ

`_git_text():909-913`、全 caller、`validate_condition_freeze_at():1310-1426`、`prepare_revision():1650-1730` には引数を追加しない。

## 3. 定数

現定数群 `s8c_preregistration.py:87-94` を次の形にする。

- `GIT_TIMEOUT_SECONDS = 15.0` — 秒、BASE。名前は残す
- `GIT_TIMEOUT_RATE_SECONDS_PER_REQUEST` — 秒/request、親実測後に投入
- `GIT_TIMEOUT_CAP_SECONDS` — 秒、上式で `MAX_BATCH_REQUESTS` から導出

RATE/CAP は現 `MAX_BATCH_REQUESTS:94` の直後、現 `_DOMAIN_FIELD_NAMES:95` の前へ置く。BASE を `GIT_TIMEOUT_BASE_SECONDS` へ改名すると互換 alias と二重正本が生じるため、既存名を BASE として維持する。

[`test_s8c_preregistration_core.py:947-984`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/tests/test_s8c_preregistration_core.py:947) の既存テスト、特に `:981` の `M.GIT_TIMEOUT_SECONDS` は一字も変更しない。新テスト側で `15.0`、裁定済み RATE literal、導出 CAP literalを独立 golden として pin するため、期待値を緩めない。invariant 側の [`GIT_TIMEOUT_SECONDS = 180:28`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/tests/test_s8c_preregistration_invariant.py:28) は candidate commit 構築用の別 timeout なので不接触とする。

## 4. stdin を持たない呼び出し

P1 の「本 wave では 15 秒据え置き」は支持する。ただし「15 秒で安全」という主張は支持しない。

- `_commit_graph():1063-1085` の `rev-list`
- `_history_namespace_paths():1088-1099` の `log --name-only` と `ls-tree`
- `read_blob_at():956` の blob 実体読み出し
- repository safety / `rev-parse`

これらには `_git` 起動前に得られる実 cardinality がなく、R1 は stdin の実要求数による予算化だけを裁定している。未実測の command-specific 緩和を同 wave へ混ぜないのが最小変更となる。

一方、2334 commit に対する `log --format= --name-only --diff-merges=separate` の contended 所要は未知である。親 probe でこの command も観測専用 cell とし、15 秒超過が出た場合は P1 の前提を覆す新事実として段 4 を停止・再裁定する。今回の RATE へ無理に換算しない。

## 5. テスト計画

追加先は [test_s8c_preregistration_core.py:986](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t553-git-budget/orchestrator/tests/test_s8c_preregistration_core.py:986)（現 timeout テスト直後、input-limit テスト直前）。

| nodeid | 検査 |
|---|---|
| `...::test_git_timeout_budget_constants_match_preregistered_measurement` | BASE=`15.0`、RATE の裁定済み literal、CAP の独立 literalを exact pin |
| `...::test_git_timeout_budget_from_request_count[no-stdin]` | `None → 15.0` |
| `...::test_git_timeout_budget_from_request_count[r-0]` | `b"" → 15.0` |
| `...::test_git_timeout_budget_from_request_count[current-r-7002]` | `b"x\n"*7002` が exact 線形式 |
| `...::test_git_timeout_budget_from_request_count[max-r-50000]` | `R=MAX_BATCH_REQUESTS` で CAP |
| `...::test_git_timeout_budget_from_request_count[above-cap-r-50001]` | CAP を超えて増えない |
| `...::test_git_uses_one_internal_budget_and_preserves_timeout_reason` | fake `subprocess.run` の call 数が1、`timeout` が helper 値、`TimeoutExpired → git-timeout` |
| `...::test_git_failed_reason_is_preserved_with_computed_budget` | `CalledProcessError → git-failed` |
| `...::test_git_budget_has_no_caller_override` | `_git`、`validate_condition_freeze_at`、`prepare_revision`、activation/effective API に `timeout` / `budget` / `deadline` 引数なし |

既存の次の期待値は変更しない。

- `test_git_timeout_generation_commit_and_blob_limits_fail_closed`
- `test_git_input_limit_stops_before_subprocess`
- `test_git_output_limit_stops_repository_probe`
- `test_batch_request_limit_stops_before_git`
- `test_total_blob_limit_stops_before_blob_batch`

条件⑤は既存 invariant nodeid
`orchestrator/tests/test_s8c_preregistration_invariant.py::test_candidate_freeze_matches_contract_and_generation_chain`
で満たす。同テストは `:131` で `validate_condition_freeze_at(ROOT, candidate)` を引数追加なしで呼び、`:1326 → :1113 → :880` の production 式を通る。retry、timeout 引数、xdist decorator の変更はしない。R3 の group 統合も本 wave では実装しない。

## 6. 変異事前登録候補

| # | (a) 変異 | (b) 落ちるべき nodeid |
|---:|---|---|
| 1 | `GIT_TIMEOUT_RATE_SECONDS_PER_REQUEST` を上向きに変更 | `test_git_timeout_budget_constants_match_preregistered_measurement` |
| 2 | `min(..., CAP)` を外して無界線形にする | `test_git_timeout_budget_from_request_count[above-cap-r-50001]` |
| 3 | CAP 到達点を `MAX_BATCH_REQUESTS + 1` にずらす | constants pin、および `[max-r-50000]` |
| 4 | R を LF 行数でなく `len(stdin)` から算出 | `[current-r-7002]` |
| 5 | 末尾 LF を余分な要求として数える | `[current-r-7002]` |
| 6 | `_git` が helper 値でなく固定 15 秒を subprocess へ渡す | `test_git_uses_one_internal_budget_and_preserves_timeout_reason` |
| 7 | stdin を chunk 分割し subprocess を複数回起動 | 同 nodeid の call-count assert |
| 8 | `_git` または public API に caller timeout override を追加 | `test_git_budget_has_no_caller_override` |
| 9 | `except subprocess.TimeoutExpired` を削除 | 既存 `test_git_timeout_generation_commit_and_blob_limits_fail_closed` |
| 10 | `CalledProcessError` を timeout 扱いする、または `git-failed` 分岐を削除 | `test_git_failed_reason_is_preserved_with_computed_budget` |

## 7. `DW-O09` / `DW-O10`

### DW-O09

結論として、外部 SHA pin、durable manifest、独立 trust root は見つからず、再発行不要という親 brief の帰結は維持できる。

ただし「literal path の Python hit が2件だけ」という証明は閉包として不十分だった。symbolic reference が少なくとも以下にある。

- core fixture: `test_s8c_preregistration_core.py:494,956`
- invariant の wave/prefix/holdout 検査: `test_s8c_preregistration_invariant.py:114,214,232`

これらは bytes pin ではない。`test_frozen_artifacts.py:38-114` の23件は s1/s8b のみで、s8c key はない。現 g1 の raw SHA-256 と `protected_sha256` の repo-wide検索でも、g1 自身以外の pin はない。したがって親 brief の「pin なし」という結論は正しいが、棚卸し根拠は literal path だけでなく symbolic key と実 SHA 検索を含めて補強すべきである。

### DW-O10

狭義の condition-freeze producer 棚卸しは正しい。

- `prepare_revision():1688` が既存世代を validation
- `:1713` が `gN.json` の destination を一意に決定
- `:1718-1725` が `O_EXCL` / 0644 / write / flush / fsync
- 同 module に別の condition-freeze writer はない

従って対象 namespace の production 出力種は `condition-freeze.v1.gN.json` 一種だけである。fixture の `_write` は tmp repository 用で production producer ではない。

ただし親 brief §5 の「report / ledger の値そのものは変わらない」は修正が必要である。code bytes の変更により、`_activation_report_at():1533-1536,1585` の `core_module_blob_sha256` は必ず変わり、`_activation_report_digest():1745-1749` も変わる。その digest は `trial_registry.py:1244-1246` の launch admission、`:1572-1573` の lifecycle、`:2412-2429` の acceptance receipt に焼かれる。さらに有効な prereg commit で旧 timeout false reject が解消されれば、`p3_autonomous_workload_trial.py:2348-2375` から run producerへ進み、run root・journal・raw・proposal・reportを生成し得る。

これは condition-freeze の durable manifest 再発行を要求する漏れではないが、changed-validator の全 call graph に対する `DW-G05` 成果物影響としては実在する。段 4 では「gN producer は一種」という狭義結論を保ちつつ、「下流 digest / lifecycle / receipt bytes は変わり得る」と親 brief を訂正すべきである。R1〜R3自体を覆す事実ではない。

## 総括

- `_git` の signature と単一 subprocessを保ち、stdin の LF要求数だけから内部予算を算出する。
- BASE は既存15秒、RATEはcontended compute実測、CAPは50,000要求点から導出する。
- blob bytesはruntime引数にせず、`--batch` の高byte量をRATE校正cellへ必ず含める。
- batch-checkだけの実測ではRATEを確定しない。
- stdinなしは本waveでは15秒据え置きだが、2334-commit logの安全性は未証明である。
- 既存期待値・reason code・invariant呼出し・xdist groupは変更しない。
- DW-O09のpinなし結論と狭義DW-O10のgN一種結論は維持できる。
- activation digestと下流lifecycle/receipt bytes不変という親briefの一般化は訂正が必要である。
- 書き込み・commit・pytest実行は行っておらず、緑は主張しない。