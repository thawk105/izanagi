# 親が段 3 の前に自分で検算した実測 (逐語)

これは親が worktree HEAD 9c1951179 の現物に対して実行した結果である。plan の [実測] を上書きする。

## V1. campaign_record は exact 30 key (plan が正しい。親の 29 と裁定の 27 は誤り)

`orchestrator/campaign/s8b_floor_campaign.py` の `_finish_session` を AST で解析した結果:

```
def at line 6346 end 6383
dict at 6361 nkeys 30 const 30
['attempt_id', 'binary_sha256_at_measure', 'cell_id', 'configuration_id', 'duration_s',
 'event', 'excluded_reason', 'exclusion_class', 'exec_failures', 'holdout_id', 'kind',
 'notes', 'probe_after', 'probe_before', 'records', 'rep_integrity_failures',
 'rep_observations', 'reps_expected', 'retry', 'retry_ordinal', 'round', 'run_cmd',
 'seq', 'session_cv', 'session_median', 'threads', 'throughputs', 'trigger', 'valid',
 'workload']
```

## V2. 契約表の field は 23 (plan が正しい)

`refs/c1a-s4-adjudication.md` の 3 節の表は 22 行あり、うち 1 行が
`report_sha256` / `observation_sha256` の 2 field を 1 行に書いている。したがって
distinct な field 名は 23 で、見出しの「exact field (24)」と 1 つ食い違う。

## V3. holdout writer が塞ぐ原因は `workload` ではなく `run_cmd` (plan の帰属は誤り)

plan は「`workload` を含む最小 canonical record が rr80 / rr20 に hit する」と書いたが、
親が `holdout_conjunction_hits` を直接呼んだ結果は次のとおりで **hit 0 件**だった。

```
入力: {"schema_version": "...", "campaign_record": {30 key の record, workload="rr80", threads=64, records=100000}}
結果: {'rr80': [], 'rr20': []}
入力: {"workload": "rr80"}          結果: {'rr80': [], 'rr20': []}
入力: campaign_record(workload="rr20") 結果: {'rr80': [], 'rr20': []}
```

走査器が見るのは `workload` ではなく次の三軸 literal である
(`s8b_holdout_freeze.py:64-79`、`holdout_conjunction_hits :698-711`)。

```
RRATIO_KEY = "ycsb_rratio";  SKEW_KEY = "ycsb_zipf_skew";  RMW_KEY = "ycsb_rmw"
HOLDOUTS: rr80 = {'ycsb_zipf_skew': '0.9', 'ycsb_rratio': '80', 'ycsb_rmw': '0'}
          rr20 = {'ycsb_zipf_skew': '0.9', 'ycsb_rratio': '20', 'ycsb_rmw': '0'}
```

実際に塞ぐのは `campaign_record.run_cmd` である。CCBench の argv がこの三軸をそのまま含む。

```
入力: {"campaign_record": {"run_cmd": ["./ycsb","-ycsb_rratio=«80»","-ycsb_zipf_skew=«0.9»","-ycsb_rmw=«0»","-thread_num=64"]}}
結果: {'rr80': ['te.json'], 'rr20': []}          <- 三軸 conjunction が成立し拒否される
入力: 同じ argv を space 連結した生テキスト   結果: {'rr80': ['te.json'], 'rr20': []}
入力: rratio を 0.8 と書いた argv           結果: {'rr80': [], 'rr20': []}   <- 値の字面が違うと当たらない
```

gate の位置は `s8b_attempt_registry.py:1172-1176` (`_write_staging` の冒頭で
`admission.assert_holdout_safe_bytes(logical_name, payload)`) と `:2290` の 2 箇所であり、
実体は `s8b_holdout_admission.py:1237-1269`。

したがって「full campaign_record は現行 writer で公開できない」という plan の結論の向きは
正しいが、**原因 field の帰属が誤っている**。この差は救済案を変える
(`workload` を落としても解決せず、`run_cmd` と `notes` の扱いが争点になる)。

## V4. issuer の 3 digest 不足は事実だが、運び手はすでに存在する (plan の第 3 案を親が特定)

親が現物で確かめた結果、plan の主張 3 は正しい。

- `FloorAttemptReservation` (`s8b_floor_attempt_launcher.py:61-79`)、`OpenedFloorAttempt` (`:125-136`)、
  `FloorAttemptTerminal` (`:140-157`) のいずれも `classification_receipt_sha256` /
  `classification_event_sha256` / `observation_start_event_sha256` を持たない
- 3 値を持つのは adapter の `_AttemptState` (`s8b_attempt_registry.py:164-186`) だけである。
  ただし field 名は `observation_event_sha256` であり、契約 3 節の綴り
  `observation_start_event_sha256` と**一致しない** (台帳 row 側は
  `attempt_registry_core.py:1357` で `observation_start_event_sha256` を使う)

ただし plan が挙げた 2 案以外に第 3 案がある。**`CapturedObservation` (`:213-217`) は
`_state: _AttemptState` を保持しており、launcher が terminal を記録する時点でこの handle を
すでに持っている。** plan 自身が提案する adapter API `record_sealed_attempt_terminal(observation, evidence)`
は第 1 引数でこの handle を受け取る。したがって「証拠文書の attempt_binding 12 key のうち
observation 側 3 digest だけを adapter が確定させる」形なら、公開 signature
`seal_terminal_evidence(reservation, opened, terminal)` を変えずに済む。
代償は digest 計算の権威が launcher から adapter へ移ることであり、D1113 (呼び手は値を選べない)
には抵触しない (adapter は呼び手ではなく信頼される consumer)。この可否は段 4 で裁定する。

## V5. 契約 v2 は現行 core と構造的に矛盾する (親が独立に特定。plan の主張 3 より重い)

v2 の retryable terminal は、次の 2 つを**同時に**満たさなければ台帳へ入らない。

1. `attempt_registry_core.py:1388-1394` — `require_terminal_reason_equals_classification` が True の
   とき `row["failure_reason"] == classification["pre_observation_failure_reason"]`
2. `attempt_registry_core.py:1402-1406` — `_assert_null_matrix` が
   `retryable_reasons = frozenset(genesis["retryable_failure_reasons"])` で判定する。v2 では
   これが `S8B_V2_RETRYABLE_FAILURE_REASONS` (契約により E2 の 4 語) になる

ところが launcher の classification 語彙は `competing_process` / `launch_failure` に固定されている
(`s8b_floor_attempt_launcher.py:28-29`、`_pre_observation_failure_reason :436-452`)。
E2 の 4 語と**互いに素**である。したがって:

- `failure_reason` を E2 語にすると 1 で落ちる
- `failure_reason` を `competing_process` にすると 2 で retryable と認められない

**現行の契約 v2 のままでは、v2 の retryable terminal は 1 行も書けない。**
検査 (`terminal_row_validator`) は `:1407-1408` にあり、上の 2 つより**後**に呼ばれるので、
封印証拠 validator をどれだけ強くしてもこの矛盾は解けない。

裁定の選択肢は 2 つある。

- (a) **v2 では launcher の classification 語彙を E2 の 4 語にする。** 等値も null matrix も
  そのまま通り、規律 2 を緩めない。campaign 側の `excluded_reason` は
  `_REASON_COMPETING` / `_REASON_LAUNCH` (`s8b_floor_campaign.py:335-336`) のままでよく、
  契約 3 節の E1 が各枝で「E2 語」と「campaign 語」を別々に返すと定めているのと整合する。
  代償は `_CLASSIFICATION_POLICY` (`:35-39`) の `precedence` を v2 用に持つ必要があり、
  `_CLASSIFICATION_AUTHORITY` の `authority_policy_sha256` (`:253`) が変わること
- (b) core の等値検査を v2 で外す。契約 3 節が「core では**外さない** (A4)」と明記して却下済み

親の暫定判断は (a)。これは C1a が書いた launcher (本 wave の unit1 の所有面) の変更であり、
plan が「先行裁定 3 件目」と呼んだものより射程が広い。段 4 で確定させる。

## V6. 三軸を運ぶ field は 3 本ある。証拠文書は現行 root へ**一切**公開できない (plan より広い)

plan は `campaign_record.workload` 1 本だけを疑ったが、親が現物で測った結果、三軸 literal を運ぶ
経路は次の 3 本である。いずれも「証拠文書の 23 field」に**直接または内側で**含まれる。

1. **`probe_before.stdout` / `probe_after.stdout` (top-level field。plan は見落とし)**
   probe の argv は `_POST_PROBE_ARGV = ("pgrep", "-af", r"ycsb_.*\.exe")`
   (`s8b_floor_attempt_launcher.py:32`)。`-a` は**一致した process の command line 全体**を出す。
   競合していた ycsb の argv がそのまま stdout に載る。実測:

   ```
   入力: {"probe_before": {"rc":0, "competing":true, "stderr":"",
          "stdout":"812345 /path/build/ycsb_silo.exe -ycsb_rratio=«80» -ycsb_zipf_skew=«0.9» -ycsb_rmw=«0» -thread_num=64\n"}}
   結果: {'rr80': ['terminal-evidence.json'], 'rr20': []}
   ```

2. **`campaign_record.run_cmd`** (V3 で実測済み)

3. **`campaign_record.notes`** — 例外文字列を 200 字で切って載せる
   (`calibrator/runner.py:966-968,979-981`、`s8b_floor_campaign.py:6293-6294`)。
   `CalledProcessError` の message は argv 全体を含むため三軸が入りうる

**現行設計はこの危険をすでに回避している。** launcher は probe payload を生のまま adapter へ渡さず、
`_external_evidence_sha256` (`:414-433`) で **digest に畳んでから** `classify_attempt` へ渡している。
つまり今日、三軸を運ぶ payload は guarded root に一度も到達しない。
campaign の journal は `_journal_append` (`s8b_floor_campaign.py:1595-1606`) の素の append であり
`assert_holdout_safe_bytes` を通らないので、全文はそちらに正当に残る。

したがって「証拠へ `probe_before` と `campaign_record` を exact に載せる」という契約 3 節の条項が、
**この wave で新たに規律を破る側**である。plan の「full record を維持するなら publish authority を
拡張する」案は trust boundary を広げるので採らない。

### 親の暫定裁定 (段 4 で確定)

証拠文書を **再導出面 (verbatim) と束縛面 (digest)** に分ける。

- probe は `competing` (と null 性) だけを verbatim に載せ、`rc` / `stdout` / `stderr` は
  canonical digest で束縛する。**E1 と cross-field 不変条件が probe から読むのは
  `competing` と `probe_after is None` だけ**なので、再導出能力は 1 ミリも落ちない
- `campaign_record` は全文を載せず、`raw_output_sha256 == sha256(serialize_session_line(campaign_record))`
  の既存束縛を正本にする。証拠には identity field と計測 field (契約 3 節が名指しした
  throughputs / exec_failures / rep_observations / rep_integrity_failures / reps_expected /
  excluded_reason / session_median / valid / probe 組) だけを載せ、`run_cmd` と `notes` は
  digest で束縛する
- これは launcher が pre-output 証拠に対してすでに使っている規律と同型であり、
  新しい逃がし道を作らない (規律 2 を緩めない)

この裁定は契約 3 節の「exact key / 型表 + 全件等値」の条項を**変更する**。C1a の裁定を
段 4 で追記訂正する形にする (規律 7: 過去の判定は追記でのみ訂正する)。

## V3 の撤回 (2026-09-07 19:10 JST。レンズ A の A-10 が正しい)

**V3 の「原因は `workload` ではない」という部分は誤りだった。** 親の probe が `workload` に
文字列 `"rr80"` を渡していたが、実型は freeze の `ycsb` mapping そのものである
(`s8b_floor_contract.py:680-692` の `_holdout_workload` が `dict(holdout["ycsb"])` を返し、
`s8b_floor_campaign.py:6361` が `cell["workload"]` をそのまま record へ載せる)。

実型で測り直した結果:

```
入力: {"campaign_record": {"workload": {"ycsb_rratio":"«80»","ycsb_zipf_skew":"«0.9»","ycsb_rmw":"«0»"}}}
結果: {'rr80': ['te.json'], 'rr20': []}          <- hit する
入力: {"campaign_record": {"workload": "rr80"}}  (親が V3 で使った誤った型)
結果: {'rr80': [], 'rr20': []}
```

したがって **plan の元の帰属 (`workload` が原因) が正しく、親の「訂正」が誤りだった。**
V6 で足した運び手 (`run_cmd` / `notes` / probe stdout) は有効であり、運び手の集合は
`workload` を含めて広がる。レンズ A は outer 側の `failure.message` /
`launch_failures[].message` / `perf_preflight_receipt.candidates[].path` も carrier だと
実測しており、こちらも採る。**結論の向き (証拠文書は現行 writer へ公開できない) は変わらない。**

## defang の erratum (2026-09-07、D88)

本 file は holdout の三軸 conjunction に当たったため、`ycsb_rratio` / `ycsb_zipf_skew` /
`ycsb_rmw` の**値だけ**を `«...»` で囲み、走査器が要求する `=<v>` および `": "<v>"` の
隣接を壊した。可逆であり、`«` と `»` を除けば原文に戻る。

- defang 前の bytes の sha256 = `8d702c1dc5a1e226a54c14be533c6be988d366dbca38b6e8b559ddf933d9b7be`
- defang 前の byte 数 = 12253
- 原文は job dir の `refs/parent-verification.md` に残る (repo 外なので走査対象でない)
- 可視文字は値を囲む 2 文字を除いて不変であり、測定の意味は変わらない
