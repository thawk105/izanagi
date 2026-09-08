## 前提の確認

採用案は、対象 test だけを変更し、32 回の `run_trial` を固定 4 thread で実行する案である。production file、反復数、assert、受理処理には触れない。

静的検査で以下を確認した。

- [対象 test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/tests/test_p3_autonomous_workload_trial.py:1836) は現行 1845-1940 で 32 wire を逐次実行している。
- 横断 assert の実際の範囲は現行 1942-1961 であり、brief の「1941-1955」は末尾 6 行を含まない。性質自体は依頼記載どおり存在する。
- 列挙された 5 個に加え、現行 1870 の `assert do_build is False` もある。これを含む全 assert を維持する。
- 1 反復では test helper の現行 213-216 と、最終 critic の [3363-3366](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/campaign/p3_autonomous_workload_trial.py:3363) から `require_admitted_campaign` が 2 回呼ばれる。32 反復で 64 回という profile と一致する。
- 各 admission は [artifact_admission.py:1479-1490](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/campaign/artifact_admission.py:1479) から、記録済み binding の検証と [capture_contract_loader_binding](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/campaign/contract_loader_binding.py:518) に到達する。
- 閉包は実際に 63 path で、`contract_loader_binding.py` 自身も [campaign_lock.py:49-68](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/campaign/campaign_lock.py:49) に含まれる。一方、`artifact_admission.py:73-76` の説明文字列はまだ「exact 62 path」であり、ここだけが現状と食い違う。本 wave では変更しない。
- 待ち比率の「96%」は、`user + sys` を CPU 時間とするなら正確には約 91.5% である。方向性は変わらず、強い I/O・subprocess 待ち律速である。
- D1795 の cache・memo 禁止、production file 変更禁止、parametrize 分割禁止をそのまま守る。

pytest や性能測定は実行していない。

## thread 安全性の判定

結論は「対象 test が使う exact な `run_trial` 構成は thread 安全」である。ただし、`run_trial` 一般が任意の引数で thread 安全という意味ではない。同一 `run_root`、共有 provider、registered/build lifecycle を並行使用する一般化は対象外である。

- module 大域状態:
  - `WORKLOADS`、`FORMAL_WORKLOADS` は [225-249](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/campaign/p3_autonomous_workload_trial.py:225)、`PARSERS` は現行 667-672 にある可変 dict だが、対象経路では読み取りだけである。
  - run scope は [534-536](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/campaign/p3_autonomous_workload_trial.py:534) の `ContextVar`。各 worker が [5156-5162](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/campaign/p3_autonomous_workload_trial.py:5156) で設定し、例外時も現行 5224-5225 で reset するため、thread 再利用でも scope は漏れない。
  - `env_contract` の process cache は `env_contract.py:553-577` に存在するが、初期化・更新は同 748-758、775-786、860-878 の lock 下で行われる。
  - `artifact_admission.py:95-144` には replay capability の process 内 `issued` dict がある。対象の各 admission は新しい `object()` key に一度だけ書き、同じ key の capability だけが読む。現在の CPython 3.10.12 では GIL 下の独立した dict 挿入であり、競合する共有 slot はない。free-threaded interpreter に移行する場合は再監査が必要である。
  - `layout.py:259-265` の process-wide output-root pin は、対象の `do_build=False` 経路では使われない。明示 `run_root` に対する `ensure_exploration_namespace` だけが現行 5004-5019 で呼ばれる。
  - `trial_registry.py:429-430` の lifecycle capability dict は registered launch 用であり、対象は `binding=None` の exploratory admissionなので到達しない。unregistered admission は [trial_registry.py:4047-4110](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/campaign/trial_registry.py:4047) で read-only に導出される。
  - `build_admission.py:54-55` の authority nonce set は `coder_authority=None` のため変更されない。同 480-504 では独立した context nonce を生成するだけである。

- cwd と環境:
  - 調査した対象経路に `os.chdir` はない。
  - contract root は `__file__` から固定された [contract_loader_binding.py:16](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/campaign/contract_loader_binding.py:16) を [98-131](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/campaign/contract_loader_binding.py:98) で検証する。Git も現行 293-305 で `git -C <root>` と明示環境を使い、cwd に依存しない。
  - `os.environ` は Git allowlist の現行 273-290、site 判定の `site_policy.py:66-79`、reservation の `p3_autonomous_workload_trial.py:3033-3041` で読むだけで、変更しない。
  - signal handler の登録・変更・送信は対象経路にない。

- path と I/O:
  - 各 wire は対象 test 現行 1890 の `tmp_path / f"wire-{wire}"` を使う。`run_trial` は [4807-4812](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/campaign/p3_autonomous_workload_trial.py:4807) で絶対化と新規性を検査する。
  - raw、proposal、journal、report、campaign WAL、namespace marker はすべてその wire 固有 root 以下である。report の PID 固有一時名も [2426-2436](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/campaign/p3_autonomous_workload_trial.py:2426) の親 directory が異なる。
  - test helper 現行 158-225 の書き込みも、引数の固有 campaign layout 以下だけである。repo root、closure、overlay、activation state は読み取りだけである。
  - provider と `AttemptJournal` は各 worker が個別生成する。共有 provider object はない。

-乱数と時刻:
  - trigger nonce は [trigger_gate_binding.py:167-169](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/campaign/trigger_gate_binding.py:167) の `os.urandom`、build attempt ID は [p3_s4_loop.py:727](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/campaign/p3_s4_loop.py:727) の `secrets.token_hex` である。共有 `random` seed はない。
  - `time.monotonic` と `time.time` は budget・timestamp に使うだけで、seed や共有順序の権威ではない。

したがって、対象構成に test 側の lock は不要である。lock で `require_admitted_campaign` を直列化すると主費用も直列化され、短縮目的を失う。

## 実装プラン

同時実行数は固定 `max_workers=4` とする。32 は実行総数であり、同時 thread 数にはしない。

根拠は次のとおり。

- 非 CPU wall は約 91.5%であり、4 本でも最大 4 個の独立した Git・open・fsync 待ちを重ねられる。
- 受入では 48 pytest worker が同一計算ノードに同居する。この node 自体は全受入で 1 回だけ実行されるため、4 thread は既存 1 活動に対して最大 3 活動を加える。一方、32 thread は metadata I/O と Git subprocess の瞬間的な fan-out が過大である。
- CPU 数や xdist worker 数から動的に決めない。固定 4 にすれば再現性があり、追加負荷の上限も小さい。

変更箇所は test file のみ。

1. [test file の import 群](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/tests/test_p3_autonomous_workload_trial.py:20) に `from concurrent.futures import ThreadPoolExecutor` を追加する。

2. 対象 test 現行 1845-1940 の逐次 loop を、局所 `run_wire(value)` と main thread の集約 loop に置き換える。

```python
def run_wire(value: int):
    wire = f"{value:05b}"
    providers = {
        role: _WireRecordingFixture(role, wire=wire)
        for role in ("planner", "coder", "auditor", "critic")
    }

    def preview(...):
        # 現行 1852-1864 をそのまま移動

    def drive(...):
        # 現行 1866-1883 を assert を含めてそのまま移動

    report = A.run_trial(
        # 現行 1885-1897 と同一引数
    )

    role_payloads = {}
    for role in ("planner", "coder", "auditor", "critic"):
        assert len(providers[role].payload_bytes) == 1
        role_payloads[role] = providers[role].payload_bytes[0]

    # 現行 1902-1923 の全 per-iteration assert
    return role_payloads, raw_variant, {
        # 現行 1926-1940 の 8 field
    }

with ThreadPoolExecutor(max_workers=4) as executor:
    for role_payloads, raw_variant, secret_record in executor.map(
        run_wire, range(32),
    ):
        for role in sink_bytes:
            sink_bytes[role].append(role_payloads[role])
        trusted_variants.append(raw_variant)
        secret_records.append(secret_record)

# 現行 1942-1961 の横断 assert を逐語維持
```

3. `_write_admitted_rejection_digest`、`_WireRecordingFixture`、production module は変更しない。64 回の admission と全 63-path 検査は減らさず、wall 上で重ねるだけである。

`ThreadPoolExecutor` が採用できない場合の次善案は固定 4 の `ProcessPoolExecutor` である。ただし module-level の pickle 可能 worker、結果の直列化、pytest worker 内からの process 起動が必要になり、48 worker 同居時の process・memory 負荷も大きい。`multiprocessing` も同じ問題を持つ。`asyncio` は同期 I/O と `subprocess.run` を単独では重ねられず、結局 thread/process が必要になる。

predicate、expected variant、binding の前計算は採らない。SHA-256 自体は profile 上 0.239 秒にすぎず、binding の共有は反復ごとの実 admission 経路を減らすため、今回の「被覆を消さない」に対して不利である。

## 被覆等価性の説明

- `executor.map(run_wire, range(32))` は 32 入力をすべて submit し、結果 iterator を最後まで消費する。executor context を抜ける前に全 task が終了するため、横断 assert 到達時点で 32 実走が完了している。
- 現行 1899、1909、1910-1912、1919、1921-1923 の 5 個の指定 assert、および現行 1870 の `do_build is False` は `run_wire` 内で各 wire に対して実行する。結果集約後へ移したり、例外を吸収したりしない。
- worker は共有 collection に append しない。provider payload、report、variant、secret record を局所値として返し、main thread だけが集約する。従って list append 自体の thread 安全性に依存しない。
- `executor.map` は入力順で結果を返すため、append 順も従来と同じ `00000` から `11111` になる。
- 順序が崩れても横断判定の意味は変わらない。planner、coder、auditor、trusted variant は現行 1942-1950 ですべて `set` の要素数を検査する。critic helper も [1792-1793](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/tests/test_p3_autonomous_workload_trial.py:1792) で集合を作る。secret 8 field も現行 1951-1961 の集合内包であり、sequence 比較はない。
- それでも `map` の ordered collection を使うため、将来 assertion が順序依存になっても従来順を維持できる。`as_completed` は使わない。
- production の呼び出し引数、受理目的、identity projection、WAL・lock 生成、critic 再構築は一切変わらない。production の受理集合は同一である。

## 波及

直接変更される test node は対象 1 件だけである。ただし参照関係を `orchestrator/tests/` から検索すると、次が回帰確認対象になる。

- [test_critic_relation_oracle_detects_candidate_derived_evidence_leak](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/tests/test_p3_autonomous_workload_trial.py:1796) は同じ `_critic_relation_equivalent` を使う。この helper は変更しない。
- [test_three_workload_build_positive_admission_passes_real_layer3_chain](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/tests/test_p3_autonomous_workload_trial.py:3398) は `_write_admitted_rejection_digest` を現行 3429 で使う。helper の signature や binding 前計算を変更しない理由でもある。
- [test_intermediate_critic_digest_mismatch_fails_closed](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/tests/test_p3_autonomous_workload_trial.py:5590) と [test_final_generation_critic_rebuilds_projected_digest](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/tests/test_p3_autonomous_workload_trial.py:5621) は `_WireRecordingFixture` と `_drive_with_raw_identity_digest` を共有する。どちらも変更しない。
- [test_tracked_python_coder_authority_ast_closure_is_exact](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/tests/test_p3_build_authority_cli.py:642) は対象 test file 全体を AST scan する。追加する executor import と局所 worker は coder authority issuer を増減しないため allowlist は不変である。
- 他の test file から対象関数、`_WireRecordingFixture`、`_write_admitted_rejection_digest`、`_critic_relation_equivalent` への直接参照は見つからなかった。

thread は context manager で join され、process cache の最終的な論理状態も逐次 32 回実行後と同じである。

## 変異候補

以下は段 6 で一時適用し、commit しない故障注入候補である。

| 変異 | 検出する性質 | 期待する赤の node |
|---|---|---|
| 計画後の現行 1845 相当で `range(32)` を `range(31)` にする | 32 wire 全件の収集、auditor・variant・secret の 32 cardinality | `orchestrator/tests/test_p3_autonomous_workload_trial.py::test_role_sink_bytes_vary_only_at_declared_declassifications` |
| `_WireRecordingFixture.invoke` 現行 353-361 で planner の記録 payload に `wire` を混入する | planner sink が 1 種であること | 同上 |
| 同じ seam で coder の記録 payload に `wire` を混入する | coder sink が 1 種であること | 同上 |
| `p3_autonomous_workload_trial.py:4301-4309` の auditor `correctness_digest` に `coder.wire` を加える | D pointer 以外の auditor 差異を normalized 集合が拒否すること | 同上 |
| `p3_s4_loop.py:697-700` の `diffq_variant_id` を固定値にする | per-iteration の期待値共有では見逃しても、trusted variant と secret variant の 32 種条件が殺すこと | 同上 |
| `p3_autonomous_workload_trial.py:3367-3379` で critic identity projection を RAW に戻す | raw candidate/build attempt の非混入と critic 関係等価性 | 同上。加えて `orchestrator/tests/test_p3_autonomous_workload_trial.py::test_final_generation_critic_rebuilds_projected_digest` も赤を期待 |

## 総括

対象構成の `A.run_trial` は、固有 `run_root`・固有 provider・`ContextVar` scope のため thread 実行可能である。  
実装は test file だけを変更し、固定 4 thread で全 32 wire を実走する。  
worker は局所結果を返し、ordered `executor.map` を main thread が集約する。  
全 per-iteration assert と現行 1942-1961 の横断 assert は逐語維持できる。  
production admission 64 回と 63-path 検査は削減・cache せず、待ち時間だけを重ねる。  
pytest と A/B 性能測定は未実施であり、採用時は親の単独走と 48-worker 受入全走で実測する。