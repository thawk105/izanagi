静的追跡の結論として、実装案は `QUEUE_TIMEOUT` を持つ台帳 v5 が妥当です。ただし、親 brief には重要な到達性の見落としがあります。

`tools/mutation_harness.py:1822-1831` は status 算出 `:1841-1843` より先に `_dispatch_orphan_stop` を呼び、同関数 `:278-304` は dispatch timeout を無条件で `OrphanHoldStop` にします。既存テスト `orchestrator/tests/test_mutation_harness.py:900-970` もこの停止を固定しています。これは D454 `docs/decisions.md:18982-19003` の契約です。

従って、D454 を維持する限り、dispatch subprocess の外側 timeout は通常台帳へ `TIMEOUT` も `QUEUE_TIMEOUT` も書かず、別の orphan-stop sidecar で止まります。以下はこの防壁を緩めず、分類を防御的に正すプランです。段 4 は「逐次実経路の既存欠陥を直した」とは記録せず、D454 の後段にある潜在的な誤分類を閉じた、と裁定すべきです。

## 1. 分類関数

### 配置と責務

- `tools/mutation_harness.py:1494-1537`
  - `_recover_dispatch_request` の返却 shape は変更しない。
  - 直後へ `_inspect_dispatch_timeout(repo, before)` を追加し、request identity と timeout evidence を別々に返す。
  - `_recover_dispatch_request` は inspector の request 部分だけを返す薄い互換 wrapper にできる。
  - 理由は、request が `ATTEMPT_REQUEST_FIELDS` `:123-125` と fan-out の `_REQUEST_FIELDS` `tools/mutation_fanout_contract.py:128-130` で exact 固定され、既存テスト `orchestrator/tests/test_mutation_harness.py:1651-1659` も exact dict を要求するため。ここへ分類欄を混ぜると attempt schema まで不要に巻き込む。

- `tools/mutation_harness.py:1589-1592`
  - dispatch inventory の取得条件から `attempt_recorder is not None` を外す。
  - `runner_mode == "dispatch"` なら逐次 harness 単体でも必ず before snapshot を取る。これがないと既存 submission と新規 submission を区別できない。

- `tools/mutation_harness.py:1631-1634`
  - local timeout では receipt recovery を呼ばず、`source="local-runner"` の evidence を作る。
  - dispatch timeout では inspector を一度だけ呼び、従来の `result["request"]` と新しい `result["timeout_evidence"]` を埋める。

- `tools/mutation_harness.py:1646-1662`
  - `_observed_status` に省略可能な `timeout_evidence` 引数を追加する。既存の非 timeout 呼出しはそのまま動かす。
  - `timed_out=True` でも、local または receipt の肯定的 RUN 証拠がある場合だけ `TIMEOUT`。それ以外は `QUEUE_TIMEOUT`。

### record に残す evidence

`MUTATION_RECORD_FIELDS` `tools/mutation_harness.py:79-105` に `timeout_evidence` を追加し、非 timeout record では `null`、timeout record では次の exact object とする。

- `source`: closed enum
- `receipt_path`: 文字列または null
- `receipt_sha256`: SHA-256 または null
- `receipt_schema_version`: 文字列または null
- `queue_wait_observed`: bool または null
- `state_history_run_observed`: bool または null
- `final_scheduler_state`: 文字列または null
- `outcome_reason`: 文字列または null

`tools/mutation_harness.py:1844-1870` で record に写し、`tools/mutation_harness.py:2123-2179` で receipt bytes の hash、再読結果、source と各欄の整合を再導出する。保存 object の自己申告だけから status を決めてはいけない。

### 分類表

| 条件 | status | evidence source |
|---|---|---|
| local runner の timeout | `TIMEOUT` | `local-runner` |
| `queue_wait_observed is True` | `TIMEOUT` | `receipt-run-field` |
| 同欄が無い旧 receipt で `state_history` に exact `RUN` | `TIMEOUT` | `receipt-run-history-legacy` |
| `queue_wait_observed is False`、RUN なし | `QUEUE_TIMEOUT` | final state に応じて `receipt-no-run-queued` または `receipt-no-run-unknown` |
| 同欄なし、RUN なし | `QUEUE_TIMEOUT` | `receipt-legacy-no-run` |
| receipt 不在 | `QUEUE_TIMEOUT` | `receipt-missing` |
| JSON 読取不能、root 不正、submission 束縛不正 | `QUEUE_TIMEOUT` | `receipt-invalid` |
| 新規 submission が 0 件または複数 | `QUEUE_TIMEOUT` | `submission-unresolved` |
| `queue_wait_observed is False` なのに history に RUN | `QUEUE_TIMEOUT` | `receipt-conflict` |
| `queue_wait_observed` が `1` など bool 以外 | `QUEUE_TIMEOUT` | `receipt-invalid` |

producer は RUN 初観測時に true を固定します (`tools/pegasus/dispatch_compute.py:1825-1837`)。一方、false は正常な scheduler 終端後に設定されます (`:1863-1866`)。実際の queue-wait-timeout は `:1852` で先に例外化するため、現行 receipt では同欄が無い場合があります。従って `False + final QUE` を queue timeout の必須形にしてはいけません。

`state_history` の RUN fallback は、欄が欠けた旧 receipt に限って使います。false と RUN が衝突する receipt は壊れている側へ倒します。

### D454 との境界

`tools/mutation_harness.py:264-304` は変更しません。外側 timeout は引き続き orphan hold が先に止めます。inspector が `_run_tests` 内で evidence を作るため、停止時にも `tools/mutation_harness.py:2476` の `active_record` へ証拠が残ります。

通常台帳へ outer dispatch timeout record を到達させたい場合は、D454 の supersede が別途必要です。この wave で暗黙に行ってはいけません。

## 2. status、summary、schema

| 場所 | 判断 | 理由 |
|---|---|---|
| `tools/mutation_harness.py:40` | `TERMINAL_STATUSES` は変更しない | `QUEUE_TIMEOUT` を completed に数えない |
| `tools/mutation_worktree.py:35-37` | `TERMINAL_MUTATION_STATUSES` は変更しない | wrapper が非 terminal 台帳を拒否するため |
| `tools/mutation_harness.py:41` | `EXPECTED_STATUSES` は変更しない | queue 待ちは変異の期待性質ではない |
| `tools/mutation_harness.py:40-42` | `NONTERMINAL_STATUSES={"PARSE_ERROR","QUEUE_TIMEOUT"}` を追加 | summary、停止、resume の判定を一元化 |
| `tools/mutation_fanout_contract.py:31-33` | `_MERGEABLE_STATUSES` は変更しない | fan-out に新 status を許可しない |

summary は新 status を黙って落とさないため、3 箇所すべてに `QUEUE_TIMEOUT` counter を追加します。

- `tools/mutation_harness.py:1924-1945`
  - `QUEUE_TIMEOUT: 0` を追加。
  - known status 判定を `TERMINAL_STATUSES | NONTERMINAL_STATUSES` にする。
  - `recorded` と `QUEUE_TIMEOUT` は増えるが `completed` と `matching` は増やさない。

- `tools/mutation_worktree.py:841-890`
  - exact `integer_fields` に追加。
  - `summary["QUEUE_TIMEOUT"] == 0` を terminal 条件へ明記。
  - terminal status count には追加しない。

- `tools/mutation_fanout_contract.py:119-122,1037-1049`
  - `_SUMMARY_FIELDS` に追加。
  - 再集計値は `QUEUE_TIMEOUT: 0`。
  - `:946-947` 付近で `PARSE_ERROR` と同様に非ゼロを明示拒否する。

### schema 推奨

`izanagi-dev-wave-mutation/v5` へ上げることを推奨します。status vocabulary、record exact shape、summary exact shapeの3点が変わるため、v4 据え置きは誤りです。

変更する4箇所は次です。

- `tools/mutation_harness.py:30`
- `tools/mutation_worktree.py:31`
- `tools/mutation_fanout_contract.py:19`
- `orchestrator/tests/test_mutation_worktree.py:137`

加えて説明文 `docs/pegasus-runbook.md:1361-1363` も v5 へ更新します。

v5 に上げた結果は明示的に次の通りです。

- resume は `tools/mutation_harness.py:2246-2257` で既存 v4 台帳を schema 不一致として拒否する。自動 migration はしない。v4 には evidence がなく、TIMEOUT の安全な再解釈ができないため。
- probe が示したゼロ件は「v4 TIMEOUT の移行対象がない」ことだけを支える。TIMEOUT を含まない未完 v4 台帳も resume 不可になる点は別の互換性影響として記録する。
- fan-out は `tools/mutation_fanout_contract.py:813-815` で旧 v4 shard を拒否する。過去 shard を再併合する場合は、その artifact を作った旧 commit の merger を使う。
- attempt sidecar は request shape を変えないため `ATTEMPT_SCHEMA` v1 のままでよい。

## 3. resume

`QUEUE_TIMEOUT` record も terminal record と同じ完全な検証を通す必要があります。

- exact field 集合: `tools/mutation_harness.py:2121-2124`
- spec、registration、HEAD、tool、collection への proof link: `:2125-2143`
- artifact と stdout hash、failed nodes: `:2144-2161`
- receipt からの timeout evidence 再導出と status 一致: `:2162-2174`
- `matches_expectation is False`: `:2175-2176`
- evidence object または receipt bytes が変わっていたら runner 起動前に拒否する。

routing は次のように変えます。

- `tools/mutation_harness.py:2346-2351`
  - `status in NONTERMINAL_STATUSES` なら `nonterminal_history` へ移し、`kept` には入れない。
  - それ以外は `TERMINAL_STATUSES` のみ許可。

- `tools/mutation_harness.py:2352-2369`
  - history の exact 許可集合を現在の「`PARSE_ERROR` のみ」から `NONTERMINAL_STATUSES` へ変更。
  - 現在の exact 文言は `:2368-2369`。
  - fan-out 側にも別の exact 制限があり、`tools/mutation_fanout_contract.py:1011-1017` は現在 `PARSE_ERROR` 以外を拒否している。

- `tools/mutation_harness.py:2370-2375`
  - current mutations だけから summary を再計算する既存動作を維持する。過去 `QUEUE_TIMEOUT` は history に残し、再走後の検出力分母や completed へ混ぜない。

- `tools/mutation_harness.py:2791-2797`
  - ledger を保存した後、`status in NONTERMINAL_STATUSES` なら停止する。
  - `QUEUE_TIMEOUT` では「RUN 開始を肯定的に証明できないため再実行対象」と明示する。

## 4. consumer の到達性

### mutation_worktree wrapper

- harness argv は `tools/mutation_worktree.py:674-705` で透過的に渡され、status の変換はない。
- ledger 検証は `:802-890`。新 status は terminal 集合にないため `:874-876` で拒否され、正しい summary なら `completed < registered` でも拒否される。
- `:1154-1172` で `terminal_ledger=False` となる。
- `:950-957,1180-1215` により container は teardown されず、resume 用に保全される。
- 従って wrapper が `QUEUE_TIMEOUT` を成功として黙って無視する経路はない。

### mutation_fanout_contract merge

- 新 v5 schema は `tools/mutation_fanout_contract.py:813-815` で要求する。
- current mutations に `QUEUE_TIMEOUT` があれば、正しい非 terminal summary は `:942-945` の完走数検査で拒否される。
- completed を偽装しても、新 status は `_MERGEABLE_STATUSES` に入れないため `:964-968` で拒否される。
- resume 後に history へ入った場合は `:1011-1017` で `QUEUE_TIMEOUT` 専用の拒否理由を返す。
- 既存の TIMEOUT 全面拒否 `:965-966` と summary `TIMEOUT: 0` `:1042-1046` は維持する。
- shard の merge 本処理は `_validate_ledger` 成功後の `:1233-1244` からなので、拒否 record が index に混入する経路はない。

## 5. テスト計画

新規 test file は作らず、既存の自走 harness を持つ test file に追加します。新規 file に分けるなら、repo fixture、git 初期化、runner argv を自前で持つ必要があります。

### `orchestrator/tests/test_mutation_harness.py`

`test_timeout_request_recovery...` 周辺 `:1532-1659` に以下を追加します。

- `test_timeout_classification_requires_positive_run_evidence`
  - local、true field、旧 receipt の RUN、false、field 欠落、receipt 不在、壊れた JSON、false と RUN の矛盾、整数 `1` を parameterize。
  - status と exact `timeout_evidence.source` を固定する。

- `test_dispatch_timeout_inventory_is_taken_without_attempt_sidecar`
  - `attempt_recorder=None` でも before snapshot が取られ、既存 submission でなく新規 receipt に束縛されることを固定する。

- `test_queue_timeout_summary_is_recorded_but_not_completed`
  - `registered=1, recorded=1, completed=0, matching=0, QUEUE_TIMEOUT=1` と exact 欄集合を固定する。

- `test_queue_timeout_record_revalidates_receipt_hash`
  - record evidence、receipt bytes、RUN field のどれかを改変すると `_validate_mutation_record` が拒否することを固定する。

- `test_resume_moves_queue_timeout_to_history_and_reruns_only_that_mutation`
  - terminal record は `kept`、`QUEUE_TIMEOUT` は history、pending は当該 ID だけ。
  - 再走成功後は current mutations が terminal、history に旧 `QUEUE_TIMEOUT` が残ることを固定する。

- 既存 orphan test `:900-970`
  - `ledger["mutations"] == []` と `summary["QUEUE_TIMEOUT"] == 0` を追加し、D454 が通常台帳より先に止めることを固定する。

### 既存テストを赤くしない条件

- `:881,893-894`: local hang は従来どおり `TIMEOUT`。期待値を変更しない。
- `:937-950`: dispatch timeout は従来どおり orphan hold。期待値を変更しない。
- `:1497`: local SIGTERM fixture の expected status は変更しない。
- `:1651-1659`: `_recover_dispatch_request` の exact dict を変更しない。
- `:379-477`: `_observed_status` の既存非 timeout 呼出しへ必須引数を増やさない。
- `:753-778`: `MUTATION_RECORD_FIELDS` の欠欄総当たりは新 evidence 欄も自動で検査させる。

schema bump により機械的に更新が必要な fixture は次です。挙動期待の緩和や反転ではありません。

- `orchestrator/tests/test_mutation_worktree.py:123-146`
  - v5、`QUEUE_TIMEOUT: 0` を追加。
  - nonterminal mode を追加し、wrapper rc=125、terminal false、container 保全を検査。

- `orchestrator/tests/test_mutation_fanout_contract.py:241-275`
  - terminal fixture record に `timeout_evidence: null`、summary に `QUEUE_TIMEOUT: 0` を追加。
  - `:536-588` 付近へ current mutations の `QUEUE_TIMEOUT` 拒否と、history の `QUEUE_TIMEOUT` 拒否を別 node で追加する。

## 6. 変異事前登録候補

| ID | 変異 | 期待して赤になる node |
|---|---|---|
| M1 | wave 前の形を復元する。`tools/mutation_harness.py:1649-1650` 相当を `timed_out` なら無条件 `TIMEOUT` に戻す | `orchestrator/tests/test_mutation_harness.py::test_timeout_classification_requires_positive_run_evidence` |
| M2 | `tools/mutation_harness.py:1537` 直後の新 classifier で `queue_wait_observed is True` を truthy 判定へ弱め、整数 `1` を受理する | 同 node の `invalid-integer` case |
| M3 | 同 classifier から、欄が無い旧 receipt の `state_history == RUN` fallback を削除する | 同 node の `legacy-run-history` case |
| M4 | receipt 不在、壊れた receipt、submission 非一意の fallback を `QUEUE_TIMEOUT` から `TIMEOUT` へ変える | 同 node の `missing`、`invalid-json`、`unresolved` cases |
| M5 | `tools/mutation_harness.py:2346-2350` の新 nonterminal membership から `QUEUE_TIMEOUT` を外し、resume で keep または拒否させる | `orchestrator/tests/test_mutation_harness.py::test_resume_moves_queue_timeout_to_history_and_reruns_only_that_mutation` |
| M6 | `tools/mutation_fanout_contract.py:1016-1017` を緩め、history の `QUEUE_TIMEOUT` を許す | `orchestrator/tests/test_mutation_fanout_contract.py::test_merge_rejects_queue_timeout_history` |

## 7. 親 brief の P1 から P6

- P1: 条件付き同意。非 terminal は正しい。ただし D454 により outer dispatch timeout は通常 record へ到達しない。この到達性を成果として主張してはいけない。
- P2: 一部反論。`queue_wait_observed=False` は current producer の queue timeout 証拠ではない。queue-wait-timeout は false 設定前に例外化する。true または旧 receipt の RUN だけを terminal 証拠とし、他は evidence 種別を分けて非 terminal に倒す。
- P3: 同意。local timeout は queue がないため terminal `TIMEOUT`。
- P4: TIMEOUT 再解釈対象ゼロには同意。ただし v5 bump が拒否するのは TIMEOUT record だけでなく全ての v4 resume / remerge であり、「互換性影響もゼロ」ではない。
- P5: 同意。`EXPECTED_STATUSES` に追加しない。
- P6: 同意。TIMEOUT 拒否を維持する。加えて v5 を受けるため contract の schema と exact record shape は更新し、`QUEUE_TIMEOUT` は current/history の双方で明示拒否する。

以上は静的検査のみです。pytest は未実走です。

## 総括

推奨する実装順序: D454 維持を段 4 で明記 → classifier/evidence → v5 record/summary/resume → wrapper/fan-out → fixture/docs。
最初の検査追加先: `orchestrator/tests/test_mutation_harness.py:1633-1659`。
実装子が最初に触る file:line: `tools/mutation_harness.py:1494-1537`。
通常経路の outer dispatch timeout は `tools/mutation_harness.py:264-304` の orphan stop を先に通し、ここは変更しない。