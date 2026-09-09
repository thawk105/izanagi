# [T-2535] 段 1 brief — 認定経路へ offline の FetchContent 供給を配線する

作業 worktree: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch`
(branch `worktree-dev-wave-t2535-certify-offline-fetch`、base `7f17e1c63`)

## 研究前進

認定較正 record は 2026-09-09 時点で 1 件も生産できていない (worklog entry 1405、
`output/insights/2026-09-09_t2224-certify-protocol-axes/README.md` §5.6)。止めているのは計算ノードから
github.com を解決できず CCBench の configure が masstree の FetchContent で落ちることである。
これを解くと、within-run floor を公式成果物へ入れる前提である較正 record が初めて 1 件出る。
**完了判定 = 計算ノードの job 1 本が configure と build を通し、`acquisition-receipt.json` と較正 record を書いて終わる。**

## scope

- (S1) `tools/pegasus/certify_calibration.sh` の CCBench configure へ offline FetchContent 供給を足す。
- (S2) `tools/pegasus/submit_certify.sh` が供給元 (pinned-clean な三者 source root) を検査し job へ渡す。
- (S3) 上記で契約が変わる既存テストの更新。
- (S4) 計算ノードで 1 本実測し、較正 record を得る。

## scope 外 (実装しない)

条件関門 F934 の是正、`-DCCBENCH_BACKOFF_FIXED=-1` の R1/R2 裁定 (ユーザー裁定待ち)、
`tools/pegasus/admission_registry.json` の変更、他 launcher (`floor_campaign.sh` 等) への水平展開、
仮想リスク向けの gate・検査・台帳・一般化の新設。

## 確定済み裁定と不変条件

- D95: 実装面 (コード・テスト・script) は Codex `role=author` が書く。親は直接編集しない。
- 規律 2: 判定式・受理集合・既定値・stock 比較を緩めない。受理集合は `{silo,mocc,tictoc}` のまま。
- D1863: protocol → CCBENCH define の静的 `case` 表と、shell を実際に parse して `SPACES` と
  突き合わせるテストの形を変えない。
- 条件関門は silo 限定のまま (`gate_calls` = silo 1 / mocc 0 / tictoc 0)。
- D1666 / D1784 の限界を継承する: 関門が見た masstree `config.h` と計測 build の `config.h` の
  bytes 同一性は束縛しない。これを新たに主張しない。

## 親が段 1 で取った実測 (すべて 2026-09-09、login node)

1. login node は github.com を解決する (`socket.gethostbyname` → 20.27.177.113)。
   計算ノードは解決しない (T-2224 が bnode122 / bnode013 の 2 ノードで実測)。
2. 永続 cache `/work/1/SFC/tanab/izanagi-thirdparty-cache` は masstree / mimalloc / googletest の
   3 本とも `tools/pegasus/policy.json` の `silo_ladder_rung1.third_party_sources` の pin と HEAD が
   一致し、汚れなし (`python3 tools/pegasus/fetch_third_party.py verify --cache-root <上記>` rc=0)。
   **offline 供給の材料は既に存在する。**
3. staging root `output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src` は主 checkout に未展開。
   `fetch_third_party.py hydrate` が作る。
4. `certify_calibration.sh` (dispatch-required) / `submit_certify.sh` (local-ok) /
   `fetch_third_party.py` (local-ok) はいずれも admission registry に登録済み。
   **新規実行体を足さなければ registry 変更は不要**で、同 file を編集中の稼働 wave
   `dev-wave-t2417-policy-arm-perf` と編集面が重ならない。同一 wave 内で実測できる (F660 を踏まない)。
5. `orchestrator/calibrator/cli.py:424-437` は configure argv のうち `-DCCBENCH_` で始まる token
   だけを見て genome を復元し、他の token を無視する。供給 define を足しても receipt からの
   genome 復元は壊れない。

## 変更面アンカー表 (分類でなく実アンカー)

| anchor | 現状 | 想定する変更 |
|---|---|---|
| `tools/pegasus/certify_calibration.sh:576-580` | `configure_argv` に FetchContent 供給が無い | BASE_DIR / SOURCE_DIR_×3 / FULLY_DISCONNECTED を足す |
| 同 `:389-403` (`run_condition_gate`) | `configure_argv[@]:5` を `--configure-arg` へ素通し | 変えない。供給が自動で関門へ届く (D1666 と同型) |
| 同 `:584-589` | silo のときだけ `run_condition_gate` | 変えない |
| 同 `:600` | `timeout 900` で configure | 変えない |
| 同 `:651-733` | receipt 候補の `ccbench.build_argv` へ configure argv を焼く | 値が変わる (field 追加はしない) |
| `tools/pegasus/submit_certify.sh:190-196` | `qsub -v` に nonce / rratio / protocol | 三者 source root を足す |
| `tools/pegasus/paper_story_a2_certification.sh:166-178, 343-375` | 認定経路の先例 (検査 → scratch へ `cp -a` → `<name>-src`) | 参照のみ |
| `orchestrator/campaign/screening_driver.py:189-206` | screening 側の base 供給 (D1784) | 参照のみ |
| `orchestrator/tests/test_pegasus_calibration_workload.py:113-169` | shell fragment を fixture 変数つきで実行して argv を観測 | 新しい fixture 変数が要る |
| 同 `:318-347` | `configure_argv` の exact pin | 新契約へ更新 |
| 同 `:250-264` | `-DCCBENCH_` で始まる token だけ filter | 変えない (供給 define に対する負例として効く) |

## 割れうる前提 (親の provisional 裁定・段 3 の攻撃対象)

- **(P1) 供給元の選び方。** provisional: submit 側が永続 cache root (または hydrate 済み staging root) を
  pinned-clean 検査し、job へ絶対 path で渡す。job は `$TMPDIR` へ `cp -a` してから
  `FETCHCONTENT_SOURCE_DIR_*` で指す (A-2 と同型)。攻撃点: cache root 直参照が pristine 契約を壊さないか、
  hydrate 済み staging root を使うべきか、`cp -a` の所要が walltime 式に収まるか。
- **(P2) 実測 protocol。** provisional: mocc。理由は条件関門を通らないので F934 を踏まない。
  攻撃点: 較正 record として silo でなくてよいか、mocc の genome が `SPACES` の制約を満たすか。
- **(P3) walltime 式。** provisional: 変えない。攻撃点: `cp -a` と offline configure の所要が
  `frozen_required_s` の build_cap(900) に収まるか。収まらないなら式の改訂が要り、
  `certify_calibration.sh:686-693` の凍結式と `walltime_formula` 文字列に触れる。

## 成果物の形

コード 2 file (`certify_calibration.sh`、`submit_certify.sh`) + テスト
(`orchestrator/tests/test_pegasus_calibration_workload.py`)、計算ノード job 1 本の
`acquisition-receipt.json` と較正 record、insight
`output/insights/2026-09-09_t2535-certify-offline-fetch/`。

## 並列分割方針

段 5 は 2 単位。所有 path は素集合にする。
- 単位 A: `tools/pegasus/certify_calibration.sh` (job body の供給配線)。
- 単位 B: `tools/pegasus/submit_certify.sh` (供給元の検査と受け渡し)。
テストは `orchestrator/tests/test_pegasus_calibration_workload.py` が両方に掛かるので、
単位 A が所有し、単位 B は自分の面のテストを別 file に足さず A の完了後に fix 段で寄せる —
または段 4 で 1 単位に畳む。段 4 で確定する。
