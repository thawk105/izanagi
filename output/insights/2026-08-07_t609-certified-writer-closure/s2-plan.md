# T-609 段 2 実装プラン

親 brief は全文確認済み。以下は HEAD `bb824d8b` に対する静的調査結果であり、read-only sandbox のため pytest・shell 実行テストは行っていない。

結論を先に述べると、(P1) の「既存 `env_contract` を全 caller に渡す」案は、その引数が `pipeline.evaluate()` の build-v2 selector も兼ねているため、受理集合を双方向に変える。規律 2 により、そのままでは採用できない。

採用候補は、必須の authorization 用 contract と、既存の任意 build-v2 selector を分離する案である。

## 1. 現行挙動の逐語確認

### 1.1 `None` bypass と `certified` までの経路

現行の [_authorize_measurement](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/loop.py:62) は次の逐語である。

```python
actual_site = site_policy.current_site()
if env_contract is None:
    return None
```

したがって、[Pegasus compute の exact contract 検査](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/loop.py:71)、[型・env_tag・clock・numactl 検査](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/loop.py:76) は発火しない。

[run_campaign](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/loop.py:101) の現行 default は逐語で、

```python
env_contract=None
```

である。authorization は [layout.ensure() より前](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/loop.py:139)だが、`None` なら素通りする。

さらに [loop.py:248-250](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/loop.py:248) は、

```python
evaluate_options = {}
if env_contract is not None:
    evaluate_options["env_contract"] = env_contract
```

なので、`None` は [pipeline の legacy build 枝](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/pipeline.py:745)、非 `None` は [build_v2 枝](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/pipeline.py:758)へ進む。これは docstring でも「contract は v2 consumer 専用 opt-in」と明記されている（[pipeline.py:515-518](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/pipeline.py:515)）。

build・verify が成功すれば [res.certified = True](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/pipeline.py:1009) となり、bench なしでも [COMMIT](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/pipeline.py:1013)、bench ありなら [通常 COMMIT](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/pipeline.py:1060) に到達する。

login/suspect は pipeline の site gate で拒否されるが、`OTHER` と `PEGASUS_COMPUTE` は許可される（[pipeline.py:254-256](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/pipeline.py:254)、[buildcache.py:441-451](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/buildcache.py:441)）。

### 1.2 production caller の再集計

実数は「12 module、15 個の `campaign.loop.run_campaign()` call expression」である。brief の「14 caller」は一致しない。

| production caller | call site | 実効 `env_tag / clocks_per_us / numactl` | 現行 `env_contract` |
|---|---:|---|---|
| `backoff_repro.py` | [108](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/backoff_repro.py:108) | `linux-baremetal / 1800 / ["numactl","--interleave=all"]`。値は [p2_2 から import](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/backoff_repro.py:34) | `None` |
| `backoff_sweep.py` | [163](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/backoff_sweep.py:163) | 同上。値は [p2_2 から import](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/backoff_sweep.py:34) | `None` |
| `demo.py` | [52, 60](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/demo.py:52) | [linux / 1800 / list](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/demo.py:29) | `None` |
| `p2_2.py` | [139](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/p2_2.py:139) | [linux / 1800 / list](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/p2_2.py:40) | `None` |
| `p3_kickoff.py` | [103, 109](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/p3_kickoff.py:103) | [linux / 1800 / list](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/p3_kickoff.py:43) | `None` |
| `p3_s4_loop.py` | [905](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/p3_s4_loop.py:905) | [linux / 1800 / list](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/p3_s4_loop.py:86) | `None` |
| `p3_s4_loop_sort.py` | [249](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/p3_s4_loop_sort.py:249) | [linux / 1800 / list](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/p3_s4_loop_sort.py:92) | `None` |
| `p3_s4_loop_trigger_gating.py` | [565](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/p3_s4_loop_trigger_gating.py:565) | `OTHER`: linux/1800/list。`COMPUTE`: pegasus/2100/`[]`。値は [lookup contract 由来](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/p3_s4_loop_trigger_gating.py:318) | [compute のときだけ非 None](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/p3_s4_loop_trigger_gating.py:560) |
| `p3_s4_red.py` | [151, 160](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/p3_s4_red.py:151) | [linux / 1800 / list](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/p3_s4_red.py:57) | `None` |
| `s6_sort_sweep.py` | [353](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/s6_sort_sweep.py:353) | [linux / 1800 / list](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/s6_sort_sweep.py:74) | `None` |
| `s8a_trigger_sweep.py` | [457](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/s8a_trigger_sweep.py:457) | [linux / 1800 / list](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/s8a_trigger_sweep.py:93) | `None` |
| `sanity_silo.py` | [52](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/sanity_silo.py:52) | [linux / 1800](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/sanity_silo.py:29) / **`numactl=None`**、`do_bench=False` | `None` |

したがって、

- `OTHER` では15 call site 全てが `env_contract=None` で certified に到達しうる。
- `PEGASUS_COMPUTE` では trigger-gating 以外の14 call site が、linux 値のまま `None` bypass を通り到達しうる。
- brief 実測 3〜4 の「残る12本すべて NUMA list、registry と完全一致」は誤り。`sanity_silo.py` は `numactl` を渡していない。
- trigger-gating は compute ではすでに contract を渡しているため、brief の「contract を渡すのは2本だけ」も誤り。

brief が挙げた次の2本は `loop.run_campaign()` caller ではない。

- [t126_driver.py:524-545](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/qualification/t126_driver.py:524) は `pipeline.evaluate()` の直接 caller。
- [s8b_oracle_driver.py:1352-1388](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/s8b_oracle_driver.py:1352) も injected `evaluate_fn()` の直接 caller。

両者はそれぞれ [line 540](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/qualification/t126_driver.py:540)、[line 1381](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/s8b_oracle_driver.py:1381) で contract を渡している。

## 2. Python 層の変更骨格

### 2.1 採用候補: authorization と build-v2 selector の分離

[loop.py:62-98](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/loop.py:62) を次の責務に限定する。

1. `_authorize_measurement()` の引数を `authorization_contract: ExecutionEnvironmentContract` とし、`Optional` を外す。
2. 関数入口で exact type を検査し、`None` は `TypeError`。
3. 現行の compute exact-Pegasus 検査、実行値完全一致、required attestation を維持する。
4. `attestation_mode="none"` の receipt 永続化は別設計判断とし、この wave で無断追加しない。

[run_campaign の signature](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/loop.py:101) には、`*` 以降の必須 keyword-only 引数として、

```python
authorization_contract: ExecutionEnvironmentContract
```

を追加する。

一方、現行の `env_contract=None` は当面「pipeline の contract build-v2 selector」として残す。[loop.py:248-250](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/loop.py:248) は変更しない。この分離により、

- authorization は全 run で必須。
- legacy caller は従来どおり legacy build。
- trigger-gating compute は従来どおり v2。
- v2 cache namespace への一斉移行を起こさない。

`env_contract` という名称が二義的に見えるため、docstring では「build materialization contract」と明記する。将来の rename は既存 API・テスト期待を伴う別タスクにする。

### 2.2 caller 配線

上記12 module全てで registry contract を解決し、`authorization_contract=contract` を渡す。

- 11本の固定 linux callerは `env_contract.lookup(ENV_TAG)`。
- trigger-gating はすでに [contract を解決済み](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/p3_s4_loop_trigger_gating.py:624)なので、[run_campaign call](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/p3_s4_loop_trigger_gating.py:565)へ無条件に `authorization_contract=contract` を加える。既存の「compute のときだけ `env_contract=contract`」は維持する。
- `sanity_silo.py` は local contract を解決し、[call site](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/sanity_silo.py:52)へ `numactl=list(contract.numactl)` も渡す。これをしないと authorization の完全一致検査で拒否される。

既存 trigger テストは `OTHER` で `env_contract is None` を意図的に固定している（[test_p3_s4_loop_trigger_gating.py:489-510](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/tests/test_p3_s4_loop_trigger_gating.py:489)）。分離案ならこの期待値を変えずに、新しい authorization contract だけを追加できる。

### 2.3 却下案: (P1) の直接配線

`env_contract=lookup("linux-baremetal")` を全 legacy caller に直接渡す案は却下する。

理由は [build_v2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/buildcache.py:575) が legacy と異なる namespace、toolchain manifest、claim、completion manifest、fsync/publish を持つためである。これは authorization の追加ではなく、build protocol の移行である。

特に [stale `.building` の拒否](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/buildcache.py:674) と [v2 entry validation](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/buildcache.py:680) は legacy に存在しない。

## 3. 受理集合の差分

| 変更案 | 変更前は受理、変更後は拒否 | 変更前は拒否、変更後は受理 | 判定 |
|---|---|---|---|
| 必須 `authorization_contract` と exact type guard | contract 省略、明示 `None`、実行値不一致、compute 上の linux contract | なし。新しい成功実行から authorization 引数を除くと、同じ build branch・同じ実行値の旧成功実行へ写像できる | 採用候補 |
| production caller に registry contract を追加し、既存 `env_contract` の有無は維持 | registry/定数が将来 drift した caller。現状では `sanity_silo` の NUMA 未修正だけが拒否 | なし | `sanity_silo` 補正込みで採用候補 |
| (P1) の既存 `env_contract` 一斉配線 | 有効な legacy cache がある一方、対応 v2 `.building` が stale な入力。旧 legacy は成功、変更後は [line 676](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/buildcache.py:676) で拒否 | **存在する。** legacy entry の admission sidecar が不正だが、同じ source/genome の有効な v2 entry が存在する入力。旧経路は [legacy sidecar 検査](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/buildcache.py:851)で拒否、変更後は v2 hit を受理 | 規律2違反として却下 |
| shell read-only preflight | wrong site、stale protocol、control/registry mismatch、calibration byte mismatchは最初の write 前に拒否 | なし。後段 gate は維持し、preflight 合格後の処理は不変 | 採用候補 |
| preflight 用 Python 不在時に stderr/非0で停止 | 従来も最終的には拒否。変更後は attempt failure marker を作らず、拒否 prefix が短くなる | なし | accepted set 不変。durable failure 記録との択一は明示が必要 |

authorization contract を「全 site で current registry object と一致必須」に強化する案も単調な縮小だが、現行は compute だけが current-Pegasus equality を要求している。OTHER 上の constructed/stale contract も新たに拒否するため、本 wave へ無断追加せず裁定へ返す。

## 4. shell 層

### 4.1 現在の最初の書込み

| wrapper | 最初の script-initiated filesystem mutation | brief との差 |
|---|---|---|
| `floor_campaign.sh` | [line 30 `mkdir "$TMPDIR"`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/tools/pegasus/floor_campaign.sh:30) | brief の line 88/200 より早い |
| `t126_qualification.sh` | [line 75 `mkdir -p "$QUAL_ROOT/job-staging"`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/tools/pegasus/t126_qualification.sh:75) | brief と一致 |

PBS 自身が job body 起動前に spool stdout/stderr を作る可能性はある。閉じられるのは「job script が開始した filesystem mutation」であり、scheduler-owned spool まで write-zero とするのは不可能である。

### 4.2 共通 read-only preflight

新設候補 `orchestrator/campaign/certified_writer_preflight.py` の予定分割は以下。

- `:1-40` — stable exit code、stderr-only 診断、duplicate-key を拒否する strict JSON reader。
- `:41-105` — submit receipt、source commit、実行 wrapper/helper hash の read-only 検証。
- `:106-140` — `site_policy.current_site() == PEGASUS_COMPUTE`、current registry contract、`load_verified_calibration()`。
- `:141-175` — floor protocol の strict parse と `_validate_protocol_against_current()`。
- `:176-220` — T126 の committed control blobを `git cat-file` で読み、`qualification.contract.validate_protocol()` と registry を照合。

helper 自身は wrapper に full SHA-256 を pin し、実行前に current bytes を照合する。T126 ではさらに [REQUIRED_CODE_IDENTITY_PATHS](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/qualification/contract.py:38) に helper path を加え、series identityへ束縛する。

preflight では [load_verified_calibration](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/env_attestation.py:1023) までに留める。これは bytes・schema の read-only 検査である。

`env_attestation.probe()` は使用しない。[TSC probe](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/env_attestation.py:579) が [一時ディレクトリ、C source、binary を生成する](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/calibrator/tsc.py:65)ため、preflight 自身が最初の writerになってしまう。

### 4.3 floor wrapper への挿入

[floor_campaign.sh:27-36](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/tools/pegasus/floor_campaign.sh:27) を次の順へ組み替える。

1. `REPO_ROOT`、output/receipt の read-only path を解決。
2. `PREFLIGHT_PY` を `python3`, `python3.10`…から `-I -B`、Python 3.10+ で選ぶ。
3. helper hashを照合。
4. nonce、submit receipt、current HEAD/source commit、wrapper identity、floor protocol、active calibration、compute siteを検査。
5. 合格後に初めて現行 line 29-30 の `/scr` TMPDIR を作る。
6. [line 88](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/tools/pegasus/floor_campaign.sh:88) 以下の attempt 作成へ進む。

既存の operational interpreter 選定と failure marker（[lines 149-178](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/tools/pegasus/floor_campaign.sh:149)）は残す。preflight bootstrap と operational selector を別変数にすることで、既存の [interpreter failure 記録テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/tests/test_pegasus_floor_tools.py:509) の期待を変えない。

ただし、bootstrap 自体が Python 不在で失敗した場合は attempt directory が無いので durable failure marker は作れない。stderr/PBS spoolだけで停止する。bootstrap failureの永続記録も必須なら、write-zeroとは両立しない。

なお floor official core は現在 [無条件拒否](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/s8b_floor_campaign.py:204)である。ここでいう正例は「preflightを通る正例」であり、official campaign完走を意味しない。

### 4.4 T126 wrapper への挿入

[t126_qualification.sh:14-25](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/tools/pegasus/t126_qualification.sh:14) ですでに read-only interpreter selection が完了する。その後、line 75 より前へ次を入れる。

1. helper bytes pinを照合。
2. [現在の receipt/ledger strict validation](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/tools/pegasus/t126_qualification.sh:308) と同じ条件を read-only で検証。
3. receipt の `source_commit` から `orchestrator/qualification/t126_control_v1.json` blob をメモリへ読む。
4. [exact Pegasus environment](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/qualification/contract.py:140)、current registry、active calibration、compute siteを照合。
5. 合格後に line 75 の job-staging 作成へ進む。

現行 line 308-430 の後段検査は defense-in-depth として残す。これにより既存テスト期待を変えず、preflight前だけ write-zeroにできる。

### 4.5 実際に拒否・受理する入力

恒真な `lookup("pegasus")` 成功だけでは gate と数えない。

拒否例:

- floor: `floor_protocol.json` の `contract_sha256` を1 nibble変更した fixture。current registry hash `e576e9…` と不一致なので、`/scr` も attempt も作らず拒否。
- floor/T126: site injection が `PEGASUS_LOGIN` または `OTHER`。
- T126: source commit内 controlの `clocks_per_us=1800`、または `allow_resume=true`。
- 共通: active calibration bytesの1 byte改変。registry SHA-256 `753f535a…` と不一致。

正例:

- floor: compute site、現行 `floor_protocol.json` SHA-256 `261cec1c…`、contract hash `e576e9…`、現行 active calibration `753f535a…`、正しい submit receipt。
- T126: compute site、source commit内 controlの environmentが `{pegasus, 2100, [], required, true, false}`、正しい receipt/ledger、同じ active calibration。

いずれも injected pure fixtureとして実現でき、実機 probeや qsubを必要としない。

## 5. 編集ファイルの所有分割

| 実装子 | 所有 path |
|---|---|
| A — Python | `orchestrator/campaign/loop.py`、上表の12 caller module、`orchestrator/campaign/certified_writer_preflight.py`、`orchestrator/qualification/contract.py`、`orchestrator/tests/test_campaign.py`、`orchestrator/tests/test_dev_wave_land.py`、`orchestrator/tests/test_p3_s4_loop_trigger_gating.py`、新設 `orchestrator/tests/test_certified_writer_preflight.py` |
| B — shell | `tools/pegasus/floor_campaign.sh`、`tools/pegasus/t126_qualification.sh`、`orchestrator/tests/test_pegasus_floor_tools.py`、`orchestrator/tests/test_t126_pegasus_tools.py` |

所有 path は素集合。

共有されるのは A 所有の preflight helper のCLI・hashだけである。Aを先行させ、helper bytesとCLIを確定した後、BがそのSHA-256をwrapperへpinする。両実装子が同じファイルを編集する構成にはしない。

## 6. 新設・変更テスト

| nodeid 候補 | 固定するもの | 既存テストとの非重複 |
|---|---|---|
| `test_campaign.py::test_run_campaign_requires_authorization_contract_before_output_creation` | 引数省略が call boundary で拒否され、output rootもevaluateも触らない | 現行 compute forwarding testはauthorizationをmonkeypatchしており、省略拒否を検査しない |
| `test_campaign.py::test_run_campaign_rejects_explicit_none_authorization_before_output_creation` | 明示 `None` の bypass消滅 | 既存0件 |
| `test_campaign.py::test_run_campaign_compute_rejects_linux_authorization_contract` | compute上のlinux contractをlayout作成前に拒否 | [既存 M12 test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/tests/test_campaign.py:4072) は gateをmonkeypatchしてforwardingだけを見る |
| `test_campaign.py::test_authorization_contract_does_not_enable_v2_build` | linux authorizationを追加しても `evaluate(env_contract=...)` を渡さずlegacy branchを保つ | [pipeline opt-in test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/tests/test_campaign.py:2706) は直接pipelineへcontractを渡す正例 |
| `test_campaign.py::test_all_production_loop_calls_bind_authorization_contract` | ASTで12 module/15 call site全件を列挙し、必須keywordを固定 | 個別runtime forwardingと重複しない閉包テスト |
| `test_p3_s4_loop_trigger_gating.py::test_other_authorizes_without_enabling_v2` | OTHERでは authorization contractあり、既存 `env_contract=None` | 既存 line 489/513 の期待を変更せず補完 |
| `test_certified_writer_preflight.py::test_floor_preflight_accepts_current_contract_fixture` | floor正例 | wrapper ordering testと非重複 |
| `test_certified_writer_preflight.py::test_floor_preflight_rejects_stale_contract_without_writes` | stale hashの具体的負例、tree snapshot不変 | 後段floor driverのprotocol validationとは書込み時点が異なる |
| `test_certified_writer_preflight.py::test_t126_preflight_accepts_exact_committed_control` | committed blob正例 | T126 driver本体のrun testとは入口が異なる |
| `test_certified_writer_preflight.py::test_t126_preflight_rejects_environment_drift_without_writes` | clocks/allow_resume drift | 後段qualification policy testと書込み時点が異なる |
| `test_pegasus_floor_tools.py::test_floor_contract_preflight_precedes_every_script_write` | helper invocationがTMPDIR mkdirより前 | line 493のinterpreter hardeningとは非重複 |
| `test_pegasus_floor_tools.py::test_floor_preflight_bootstrap_failure_is_stderr_only` | bootstrap失敗時にattempt markerを作らない | 既存 line 509はpreflight通過後のoperational selector failureを固定するため両立 |
| `test_t126_pegasus_tools.py::test_t126_contract_preflight_precedes_job_staging_write` | line 75より前の発火 | 現在該当テストなし |
| `test_t126_pegasus_tools.py::test_wrappers_pin_current_preflight_helper_bytes` | wrapper内helper hashとcurrent bytes一致 | T126 script identity全体の検査とは別の直接pin |

既存 `run_campaign()` テスト群（[test_campaign.py:3940-4616](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/tests/test_campaign.py:3940)、[6845-6888](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/tests/test_campaign.py:6845)、[test_dev_wave_land.py:2762](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/tests/test_dev_wave_land.py:2762)）には、fixture authorization contractを入力として足す。assertion・期待値は変更しない。

実装後の実行は raw `pytest` ではなく `python3 tools/run_tests.py ...` 経由とする。今回は未実走であり、緑とは報告しない。

## 7. 変異事前登録候補

### 登録候補 M1 — `None` bypass 復活

- 対象: [loop.py:69-70](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/loop.py:69)
- current old 逐語:

```python
if env_contract is None:
    return None
```

- 変異: 実装後の exact-type rejectionを上記 `return None` に戻す。
- 赤になるnode: `test_run_campaign_rejects_explicit_none_authorization_before_output_creation`
- 単一理由性: fixtureはOTHER site、実行値・build context・evaluateをすべて有効にし、explicit Noneだけを負入力にする。変異後はlegacy branchからfake certifiedへ到達し、前後に同じ入力を拒否する層はない。

### 登録候補 M2 — compute exact-Pegasus gate除去

- 対象: [loop.py:71-75](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/loop.py:71)
- current old 逐語:

```python
if (actual_site == site_policy.PEGASUS_COMPUTE
        and env_contract != env_contract_registry.lookup("pegasus")):
    raise execution_guard.ExecutionGuardError(
        "Pegasus compute では登録済み pegasus env_contract だけを受理する"
    )
```

- 変異: 条件ブロックを削除。
- 赤になるnode: `test_run_campaign_compute_rejects_linux_authorization_contract`
- 単一理由性: linux contractとlinux実行値を完全一致させる。computeはpipeline heavy-work gateでは許可され、build selectorはlegacyのままなので、当該gate以外に拒否理由がない。

### 登録候補から外す位置

- `run_campaign` default復活: 後段の explicit-None guardも同じ入力を拒否するため単一理由でない。
- production callerからkeywordを1個削る変異: 実装後の新規行であり、現時点ではold逐語と確定lineを登録できない。実装commit後に再登録する。
- shell preflightの削除・後置: stale protocol/site mismatchは後段Python gateも拒否するため、同じ入力に複数の拒否層がある。write orderingテストは有用だが、単一理由変異の候補にはしない。
- helper内のsite/contract検査: 新設ファイルで現時点のold bytesが無く、かつwrapper後段にも同じ拒否があるため除外する。

## 8. 凍結 bytes・trust root への影響

| 対象 | pin / trust root | 影響 |
|---|---|---|
| `loop.py` | [test_frozen_artifacts.py の FROZEN_MANIFEST](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/tests/test_frozen_artifacts.py:38)には無い。[test_check_ai_provenance.py:651](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/tests/test_check_ai_provenance.py:651) はsource分類でありbyte pinではない | 凍結output bytesへの直接影響なし。commit provenance監査対象 |
| `floor_campaign.sh` | [admission_registry path key](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/tools/pegasus/admission_registry.json:40) と [exact registry test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/tests/test_hooks.py:1345)。また submitter が [committed blob hash](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/tools/pegasus/submit_floor.sh:236) を future receiptへ入れる | registry値は変更不要。future `job_script_sha256` と source commitは変わる。既発行receiptは記録済みcommit blobから検証されるため書換えない |
| `t126_qualification.sh` | [admission_registry path key](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/tools/pegasus/admission_registry.json:160)。さらに role名に相当する `script_identity` required setのkeyとして [contract.py:67-70](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/qualification/contract.py:67) に入る | wrapper変更はfuture `series_identity`、submission `job_script_sha256`、job-result chainを変える |
| T126 script identity consumers | [series_identity exact set](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/qualification/contract.py:501)、[driver preimage](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/qualification/t126_driver.py:346)、[identity consumer](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/qualification/identity.py:36)、[collector](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/qualification/collector.py:511) | brief 実測8が漏らしたkey-side pin。既存凍結outputを書き換えないが、future series IDは必ず変わる |
| 新preflight helper | wrapper内full SHA-256 pin、およびT126 `REQUIRED_CODE_IDENTITY_PATHS` | 新しいtrust root。A確定後にBがpinし、hash一致テストを置く |

従って、(P4) の「FROZEN_MANIFEST対象のoutput bytesは不変」は狭義には正しい。しかし「DW-O10に該当するidentity影響が無い」という読みなら誤りである。T126は明確にscript identity/series identityが変わる。

また brief line 51 の `calibration-94a4b79fa31bba3c.json` は登録ディレクトリには存在するが、current registryが参照しているactive calibrationではない。現行 lookup は [calibration-753f535a8d024727.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/env_contract.py:267)、SHA-256 `753f535a…` である。

## 総括

- 提案の要点:
  - 必須 `authorization_contract` を新設し、現行 `env_contract` はbuild-v2 selectorとして分離する。
  - 12 production module・15 call siteを閉じ、`sanity_silo` の実NUMA不一致も補正する。
  - 両wrapperへ、最初のscript writeより前のread-only Python preflightを置く。
  - floorはpreflight bootstrap interpreterと既存operational interpreterを分離し、既存テスト期待を維持する。
- 誤っている、または不完全な provisional 判断:
  - **P1**: caller集計が誤りで、既存 `env_contract` 一斉配線はbuild-v2移行を同時に起こす。
  - **P2**: cache namespace差により受理集合は双方向に変わる。特に「旧拒否→新受理」が実現可能なので却下。
  - **P3**: dual interpreter構成なら実現可能。ただしbootstrap failureのdurable記録とwrite-zeroは両立しない。
  - **P4**: FROZEN_MANIFEST bytes不変は正しいが、T126 `script_identity` とfuture series IDへの影響を漏らしている。
  - **P5**: 実装後もraw pytestではなく `tools/run_tests.py` を使う。今回のread-only段2では未実走。
- 実装しないほうがよい項目:
  - 既存 `env_contract` を全legacy callerへ直接渡すP1案。
  - preflightでfull hardware attestation/TSC probeを実行すること。
  - 既存テストの `env_contract=None`、interpreter failure marker等の期待を反転すること。
  - 凍結outputや既発行receiptの書換え。
- ユーザー裁定へ返すべき設計択一:
  - T-609の「契約束縛」を、writer入口でのauthorization closureまでとするか、legacy build artifact/WALまでcontract hashを永続束縛するところまでとするか。後者ならbuild protocolの追加設計と受理縮小裁定が必要。
  - preflight失敗は「script write-zero + PBS spoolのみ」でよいか、durable failure receiptを優先するか。
  - write-zeroの境界をjob script自身の書込みとするか、PBS scheduler spoolまで含めるか。後者は実装不能。