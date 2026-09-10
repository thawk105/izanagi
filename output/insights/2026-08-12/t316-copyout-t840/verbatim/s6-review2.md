静的レビューのみ実施した。pytest・build・性能測定は実走していない。親報告の `3 failed / 119 passed` は既知事実として使用した。

## 所見 1

- 重大度: **blocker**
- 主張: fd の通常経路には明白なリークを見つけなかったが、`os.close()` 自体が失敗する例外経路では残りの fd を閉じず、リークしうる。特に `_CopiedBinary.close()` は最初の失敗で後続 fd の close を中断し、directory traversal は親 fd の close 失敗時に直前に開いた child fd の所有権を失う。
- 根拠: [`buildcache.py:181`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:181)、[`buildcache.py:381`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:381)、同型の cleanup は [`buildcache.py:216`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:216) と [`buildcache.py:238`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:238)。
- 成果物影響: 長時間 campaign が `EMFILE` に到達すると、後続 build/cache validation が欠落し、認証済み選択・レポート・WAL/COMMIT 参照が生成されない。
- 提案: 全 fd を best-effort で閉じ、最初の例外だけを再送出する共通 helper を使う。directory traversal では child fd を cleanup 対象へ登録してから親を閉じ、close-error 注入テストで fd 数が増えないことを確認する。

## 所見 2

- 重大度: **must-fix**
- 主張: secure-FS capability 判定が `os.supports_dir_fd` の「元関数オブジェクトとの同一性」に依存しており、正当な観測用 monkeypatch を capability 欠如と誤判定する。親の赤 3 件はこの実装上の回帰であり、並行 build 固有の第二原因は静的には見つからなかった。
- 根拠: capability 判定は [`buildcache.py:86`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:86)–[`buildcache.py:110`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:110)。gate-order test は `os.rename` を差し替える [`test_buildcache_v2.py:1187`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_buildcache_v2.py:1187)、2-process test は子プロセスで `os.mkdir` を差し替える [`test_buildcache_v2.py:1336`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_buildcache_v2.py:1336)。
- 成果物影響: publish 順序と同一 digest 並行 claim の受理集合を検証できず、この wave の認証済み cache-entry 集合を承認できない。
- 提案: import 時に実環境 capability を immutable な bool として確定するか、wrapper 化されても変わらない capability probe にする。機能欠如時の fail-closed は別の負例で維持する。

## 所見 3

- 重大度: **must-fix**
- 主張: 環境契約の負例が定数欠如しか測っておらず、裁定が要求した `supports_dir_fd`、`supports_follow_symlinks`、各関数 membership を外した場合の fail-closed は証拠がない。また実装が依存する `/proc/self/fd` は事前契約に含まれていない。
- 根拠: 実装は capability を [`buildcache.py:86`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:86)–[`buildcache.py:110`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:110) で検査する一方、追加テストは定数の `delattr` のみ [`test_buildcache_v2.py:1224`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_buildcache_v2.py:1224)。procfd 再 open は [`buildcache.py:342`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:342)、`pass_fds` 使用は [`buildcache.py:1715`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:1715)。
- 成果物影響: unsupported host で初期契約を通過して途中 abort し、選択・レポート・台帳の build 結果が欠落する。静的には不正成果物の受理より over-rejection 側である。
- 提案: capability set、各 membership、`supports_follow_symlinks` を一つずつ除く負例を追加する。Linux/procfs が前提なら `/proc/self/fd` 利用可能性も初期契約として明示・検査する。

## 所見 4

- 重大度: **must-fix**
- 主張: M5 と M13 は指定された変異では単一理由へ帰属しない。別検査が先に発火するため、KILLED でも目的の防御が効いた証拠にならない。
- 根拠:
  - M5: hash 後にも fd と directory entry の identity を再検査している。v2 は [`buildcache.py:1339`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:1339) と [`buildcache.py:1355`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:1355)、legacy は [`buildcache.py:1538`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:1538) と [`buildcache.py:1550`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:1550)。
  - M13: v2 は staging を [`buildcache.py:1353`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:1353) で削除した後、clean directory を [`buildcache.py:1363`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:1363) で rename する。rename 一行を旧 staging publish に戻せば「whole-tree 漏洩」ではなく source 消滅で落ちる。
- 成果物影響: 同一 fd 防御や copy-out allowlist が壊れても、別理由の KILLED を根拠に承認され、異なる inode または禁止 member の SHA が BUILD_DONE/COMMIT 参照へ入る。
- 提案:
  - M5 は `verify_destination_entry()` を無効化し、hash 後 swap が fd-entry binding 喪失だけで生存する変異へ変更する。
  - M13 は staging rename 一行ではなく、代表的な非許可 member 一つを clean directory へコピーする変異、または candidate selector を一か所で切り替える coherent mutation にする。

## 所見 5

- 重大度: **nit**
- 主張: gate-order test は production gate の意味を測らず、差し替えた no-op callback の呼出順だけを測る。複数の追加テストも `_run`、`source_digest`、`_assert_no_trace_symbols` などを差し替えているため、「実 C++ publish 経路」の証拠にはならない。
- 根拠: gate 群の monkeypatch は [`test_buildcache_v2.py:1164`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_buildcache_v2.py:1164)–[`test_buildcache_v2.py:1196`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_buildcache_v2.py:1196)。2-process 子も `_run`、`source_digest`、nm を差し替える [`test_buildcache_v2.py:1286`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_buildcache_v2.py:1286)。coder 正例は cache build を止める seam を入れる [`test_p3_build_authority_cli.py:417`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_p3_build_authority_cli.py:417)。
- 成果物影響: 直ちに受理集合を変えないが、production call-site の gate 欠落や実 toolchain との不整合を見逃す。
- 提案: 順序テストは補助証拠と明記し、親が legacy/v2 の実 build canary と oracle prepared-cell test を走らせる。

gate を外しても緑のままになりうる主な追加テストは以下。

- `test_copyout_gate_order_is_exact_through_rename[legacy/v2]`: gate 自体を monkeypatch している。
- `test_no_trace_symbols_*`: helper 単体なので production call-site から呼出しを削除しても通りうる。
- coder 六正例、AST closure、registry projection: runtime の `require_registered_coder_entrypoint()` を外しても通る。M9 の実効的負例は unregistered caller test。
- secure-environment 定数テスト: `supports_dir_fd` 等の検査を外しても通る。
- cache-hit compatibility、stale cleanup、relative-path helper テスト: fresh publish gate を外しても設計上そのまま通る。

一方、`[legacy]` / `[v2]` は見かけだけの parametrization ではなく、それぞれ旧 `build()` と `build_v2()` へ分岐しているため、別経路を通っている。

## 所見 6

- 重大度: **nit**
- 主張: clean candidate と最終 rename は同一 fd 群で結ばれているが、staging/source build は絶対 pathname を production subprocess に渡し、後で pathname から source を開く。したがって実装子 A の「staging/source も一貫して dir-fd traversal」という説明は過大である。
- 根拠: source tree 作成後に staging fd を保持せず、build へ pathname を渡す [`buildcache.py:1278`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:1278)–[`buildcache.py:1325`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:1325)。一方、copy 後の destination は held fd と entry を比較する [`buildcache.py:364`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:364)。
- 成果物影響: host namespace 攻撃を仮定した場合は入力 source inode の取り違え余地があるが、今回の認証済み copy-out inode 契約では scope-out であり、現行受理集合への直接影響は未確認。
- 提案: 今 wave の claim を「copy-out destination の inode binding」に狭めて記録する。staging anchor の fd-to-exec 化は別 wave とする。

## 所有外 consumer と API 互換性

静的追跡では、上記 false-red 以外の明白な caller break は見つからなかった。ただし実走確認ではない。

- `pipeline.py` は既存の `build()` / `build_v2()` 引数と戻り値をそのまま使用しており、例外は既存経路で変換される。
- `s8b_floor_campaign.py`、calibrator、qualification、oracle driver 群の build 呼出 signature は維持されている。
- `_assert_no_trace_symbols(binary, *, binary_fd=None)` と `_read_completion_manifest(path, *, directory_fd=None)` は keyword-only 引数の追加であり、既存 positional caller は維持される。
- `full_sha256` の public signature は不変。
- `MaterializerRegistration` の追加 field には default があり、既存二引数構築は維持される。
- receipt/WAL の永続 key は依然 `run_id` と `authority_kind` のみで、site は書き込まれない [`build_admission.py:421`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/build_admission.py:421)。cache identity、COMMIT、freeze hash を変更する差分もない。実装子 B の申告は静的には正しい。
- `durable_root.py` は root fd を保持せず、`Path.resolve()` と pathname open を使う [`durable_root.py:63`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/durable_root.py:63)、[`durable_root.py:95`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/durable_root.py:95)。編集なしでは今回の openat-style traversal に再利用できないという実装子 A の申告は正しい。
- working-tree hash、timestamp、pid、絶対 path を固定 golden expectation に焼き込んだ追加テストは見つからなかった。PID/nonce は一時名・同期用、digest は固定 fixture payload から独立計算されている。

## 総括

### blocker

- close-error 例外経路の fd リーク。

### 判定

**NO-GO**。

理由は、ユーザー指定で blocker 扱いとなる fd リーク経路が残り、親実測の 3 件が実装自身の capability 判定で赤く、さらに M5/M13 の帰属が成立していないため。この状態では copy-out 防御の acceptance evidence を完成扱いできない。

### 親が走らせるべきテスト

まず既知赤の修正後に再実行:

- `orchestrator/tests/test_buildcache_v2.py::test_copyout_gate_order_is_exact_through_rename`
- `orchestrator/tests/test_buildcache_v2.py::test_v2_two_real_processes_only_one_claims`
- `orchestrator/tests/test_buildcache_v2.py` 全体

焦点走の外で落ちうる consumer:

- `orchestrator/tests/test_campaign.py`
- `orchestrator/tests/test_build_site_gate.py`
- `orchestrator/tests/test_build_admission.py`
- `orchestrator/tests/test_artifact_admission.py`
- `orchestrator/tests/test_s8b_materialization.py`
- `orchestrator/tests/test_s8b_floor_campaign.py::test_slow_real_prepare_cell_to_buildcache_canary_one_configuration`
- `orchestrator/tests/test_s8b_floor_campaign.py::test_slow_real_prepare_cell_to_buildcache_v2_canary_one_configuration`
- `orchestrator/tests/test_s8b_oracle_driver.py::test_slow_oracle_prepared_cell_pipeline_uses_real_build_v2`
- `orchestrator/tests/test_t126_qualification_driver.py`
- `orchestrator/tests/test_p3_autonomous_workload_trial.py`
- `orchestrator/tests/test_p3_s4_loop.py`
- `orchestrator/tests/test_p3_s4_loop_sort.py`
- `orchestrator/tests/test_p3_s4_loop_trigger_gating.py`
- `orchestrator/tests/test_s1_direct_comparison.py`

### M1〜M13 帰属判定

| 変異 | 判定 |
|---|---|
| M1 | 帰属可能。source leaf symlink を `O_NOFOLLOW` 欠落だけで生存させられる。 |
| M2 | **一部先取り**。FIFO は有効。directory は regular-file 検査を消しても read の `EISDIR` が先に殺すため、directory case を M2 の証拠に数えない。 |
| M3 | 帰属可能。`st_nlink == 1` の単一理由。 |
| M4 | 帰属可能。anchored parent traversal を pathname traversal に戻す変異として実施する。 |
| M5 | **帰属不可**。hash/path reopen 変異が後段の fd-entry identity 再検査に先取りされる。`verify_destination_entry()` 単独変異へ再照準。 |
| M6 | 帰属可能。専用 host-metadata node を使う。broad exact-set test だけに依存しない。 |
| M7 | **証拠不足**。定数欠如だけ有効。dir-fd/follow-symlink capability と procfd の負例を追加する。 |
| M8 | **一部先取り**。binary intermediate symlink は有効。metadata symlink は旧実装の `islink` 検査でも落ちるため、新 nofollow read の単独証拠にならない。precheck 後 swap へ再照準。 |
| M9 | 帰属可能。unregistered runtime negative が flag 発行前を検査する。 |
| M10 | **構造的 KILL のみ**。scan-root equality が先に殺すため、未登録 issuer の runtime 挙動を証明しない。ledger 上も structural coverage と明記する。 |
| M11 | 帰属可能。exact exclusion の decoy case。 |
| M12 | 帰属可能。ただし通常 build の多数も同理由で赤くなるため、失敗 node 全集合を記録する。 |
| M13 | **帰属不可**。staging は rename 前に削除済みなので、旧 rename への一行変異は source missing に先取りされる。禁止 member 一つを clean candidate へ混入する coherent mutation へ再照準。 |

DW-G05 の成果物影響基準に従い、staging anchor や procfs portability のうち認証済み受理集合への直接影響を確定できない部分は nit に落とした。