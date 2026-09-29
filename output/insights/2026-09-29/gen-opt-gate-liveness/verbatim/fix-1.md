## 所見への対応

| 所見 | 状態 | 対応 |
|---|---|---|
| F1 | closed | fix job の trace build・走行・判定後に CI 相当 build を実行。CI build の失敗は結果に記録して続行する。 |
| F2 | closed | CI configure から genome define と `CCBENCH_TRACE` を除外。全 target を build し、計算ノード用の compiler・依存物供給との差を `ci_equivalence_notes` に記録する。 |
| F3 | closed（起動器は未実走） | job・workload ごとの `prereg` に `expected`・`observed`・`match` を記録し、終了値を判定する。 |
| F4 | closed | D2b(ii) の発生条件を書きのある取引に変更。複数回の書きの件数は別に維持した。 |
| F5 | refuted | 裁定どおり変更なし。 |
| F6 | closed | 自走 test に `--repo-root` を追加し、abort 除外を主張していた test 名を変更した。Q は計装 patch で commit 成功後にだけ出力される。 |
| F7 | partial | build 所要秒の記録は維持。所要・資源の見積りは裁定どおり親の一次資料に委ねる。 |
| F8 | closed | tar.gz の sha256 取得後に trace dir を削除。file 一覧と各 byte 数を `result.json` に記録する。 |
| F9 | closed | 刻印 tag を `S` から `V` に変更し、計装 patch と照合器を揃えた。 |

## 変更 file と patch

| file | 行数 | sha256 |
|---|---:|---|
| [gate_check.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/genopt-gl-author/genopt_gl_scratch/gate_check.py) | 222 | `73a979d8553220a861c25790ccde3000869ae0361f6537c33384ecdb2f1741e1` |
| [launch_gate_liveness.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/genopt-gl-author/genopt_gl_scratch/launch_gate_liveness.py) | 298 | `7210eeb412f0452a8881e71922aace898156ebb98dcb6bb135111b1f417caf46` |
| [make_patches.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/genopt-gl-author/genopt_gl_scratch/make_patches.py) | 197 | `8c25a2a7e65eac424734dec0fbf575c5290de2376c7f927b93440f577a62f030` |
| [instr-silo-gate-witness.patch](/work/1/SFC/tanab/izanagi/.codex/worktrees/genopt-gl-author/genopt_gl_scratch/patches/instr-silo-gate-witness.patch) | 149 | `dcd7341e25cb27b0e893b4d525d1401aed94cd299966ff230fa874eb96e8d390` |
| [test_gate_check.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/genopt-gl-author/genopt_gl_scratch/test_gate_check.py) | 116 | `761620ec27395d250f23ec07f1a2083f9cb194cdfe3c3dfdc2117d843db38229` |

計装 patch の hunk 位置・数は変わらず、`include/trace.hh` の `emit_stored` 内の出力 tag だけを `S` → `V` に変更した。B1 patch と修正案 patch の hunk は変更なし。`make_patches.py` で patch を再生成した。

## 厳密適用と TRACE 枝

複製 tree での `git apply --check` は、計装 `0`、計装→B1 `0→0`、計装→修正 `0→0`、修正単独 `0`。いずれも stderr 先頭は空。計装後の `include/trace.hh`、`include/ycsb.hh`、`cc/silo/transaction.cc` は、TRACE 枝除去後に pin と bytes 一致した。

## 自走 test と tag 確認

照合器の自走 test は **13 PASS、0 FAIL**：`test_d1_a`、`test_d1_b1`、`test_d1_b2`、`test_d2b_i`、`test_d2b_ii`、`test_malformed_q`、`test_q_extra`、`test_q_missing`、`test_stamp_out_of_range`、`test_v_extra`、`test_v_missing`、`test_v_w_key_mismatch`、`test_valid_committed_transaction`。D1(b1) の比較を一時的に外すと `test_d1_b1` が rc=1、D2b(ii) を外すと `test_d2b_ii` が rc=1 で赤になった。元の照合器は変更されていない。

未使用 tag の確認 command は `rg -n -F -e '"Q ' -e '"V ' -e "'Q '" -e "'V '" orchestrator/verifier external/ccbench/include/trace.hh external/ccbench/cc`。結果は該当なし（rc=1）。比較確認では `rg -n -F -e '"S ' ...` が `external/ccbench/cc/mocc/transaction.cc:109` の既存 `S` 出力を検出した。

## 起動器と作業木

起動器は**実装済み・未実走**。終了値は [prereg()](/work/1/SFC/tanab/izanagi/.codex/worktrees/genopt-gl-author/genopt_gl_scratch/launch_gate_liveness.py:88) が条件を評価し、[main()](/work/1/SFC/tanab/izanagi/.codex/worktrees/genopt-gl-author/genopt_gl_scratch/launch_gate_liveness.py:279) が決める。build・run・判定器または CI build の失敗は `1`、照合器の到達可能性が pass でない場合は `3`、到達可能で事前登録と不一致なら `4`、全 run が完走し一致すれば `0`。stock の D2b 違反予想と B1 の発火件数対 D1(b1) 件数は診断として記録し、`match` を左右しない。

`git -C external/ccbench status --porcelain` の出力は空。変更は `genopt_gl_scratch/` 内の上表 5 file のみ。

## 総括

裁定対象の修正と login で許された検査を完了した。build・benchmark・計算ノード投入は行っていないため、起動器の実走結果はまだない。