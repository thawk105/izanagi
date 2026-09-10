指定資料はすべて読取済み。静的レビューのみで、probe・pytest・qsub は実走していない。

## blocker

1. **[blocker] R3-1 の性能要件を別の測定へ縮めている。**

   R3-1 は trace 実行、stock/variant 双方の性能差、floor 再較正要否を要求するが、brief は「同一 binary の sandbox 内外 overhead 比」へ変更している（[package.md:96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/output/insights/2026-08-09_t316-semantic-gate/package.md:96)、[s1-brief.md:41](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t316-sandbox-measure/s1-brief.md:41)）。実装も trace-disabled stock binary 1 本しか作らず、variant 入力、trace run、floor 基準・再較正判定が存在しない（[probe.py:867](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:867)、[probe.py:940](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:940)）。S7 は正の ratio が一つあれば `go` になる（[probe.py:168](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:168)）。

   **成果物影響:** このままの job ID を R3-1 発火 artifact とすると、stock/variant 差と floor 未測定のまま意味 gate 実装が解除され、選択の floor・fitness 判定値が根拠なく確定する。

2. **[blocker] S3 の write 正負制御が恒真化している。**

   outside と inside に同じ path・同じ `O_EXCL` 書込みを順番に使うため、outside が作った marker が残った状態で inside が走る（[probe.py:566](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:566)、[probe.py:618](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:618)）。特に `write_repo` と `source_read_only` は、RO bind を RW bind に壊しても inside は `EEXIST` で失敗し、`inside_blocked=true` になる。

   テストと P3 の変異対象は、観測器が作った boolean を検証せず、手書きの「良い boolean」を verdict 純関数へ注入するだけである（[test_t316_sandbox_probe.py:21](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/orchestrator/tests/test_t316_sandbox_probe.py:21)、[s1-brief.md:80](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t316-sandbox-measure/s1-brief.md:80)）。

   **成果物影響:** source が実際には writable な profile でも S3 が GO となり、生成物が source や計測入力を書き換えられる受理集合を「RO」と誤認する。

3. **[blocker] S7 の 1 回対比較は性能測定として識別不能である。**

   outside→inside の固定順で各1回だけ実行し、反復、順序反転、warm-up、中央値・分散がない（[probe.py:948](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:948)）。比は TPS ではなく process 起動・`numactl`・`perf`・bwrap を含む wall elapsed である。`perf stat` 出力、CCBench の実効 flags、実際の thread 数も検証しない。

   単独性は S1 で一度記録するだけで、S7 前後の判定に使われない。S1 verdict 自体も bwrap の存在しか要求しない（[probe.py:96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:96)、[probe.py:397](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:397)）。`Exclusive submit = OFF` という実機契約にも反する（[pegasus-runbook.md:33](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/docs/pegasus-runbook.md:33)）。

   **成果物影響:** cache 温度、実行順、同居 job の差を sandbox overhead と誤認し、floor 再較正要否と将来の variant 選択閾値を誤って変更する。

4. **[blocker] 計測 ID が実行した commit・PBS・policy に束縛されていない。**

   親が渡す4変数には expected commit/worktree がなく（[s5-impl-out.md:27](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t316-sandbox-measure/s5-impl-out.md:27)）、PBS は `$PBS_O_WORKDIR` の live Python/policy/source を直接使う（[probe.pbs:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.pbs:29)）。git metadata は実行後に記録するだけで、実行 bytes の SHA、runtime PBS SHA、policy SHA、開始時 HEAD、qsub intent を照合しない（[probe.py:996](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:996)）。

   先例は expected commit/worktree、clean tree、commit blob からの staging、runtime PBS SHA を検査している（[t139_r4_env_probe.pbs:8](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t139_r4_env_probe.pbs:8)、[t139_r4_env_probe.pbs:105](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t139_r4_env_probe.pbs:105)、[t139_r4_env_probe.pbs:145](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t139_r4_env_probe.pbs:145)）。

   raw `$PBS_JOBID` と qsub 応答 ID の正規化・束縛もない。

   **成果物影響:** DW-G04 が参照する job ID から「どの probe/profile/policy bytes を測ったか」を復元できず、別内容の測定を根拠に意味 gate の受理集合を解除できてしまう。

5. **[blocker] brief の fail-soft 契約を満たさず、部分結果を失うか、壊れた `receipt.json` を残せる。**

   S1〜S7 の結果は最後までメモリ内だけにあり、全段終了後に初めて receipt を作る（[probe.py:1004](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:1004)）。SIGTERM、walltime kill、Python crash、`_git_metadata` 失敗では S1〜S5 まで終わっていても何も永続化されない。

   書込みも最終名 `receipt.json` へ直接行い、atomic rename、directory fsync、`COMPLETED` marker がない（[probe.py:1106](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:1106)）。途中 kill では JSON が破損していても「期待 path」は存在する。

   **成果物影響:** 台帳が有効な段別結果を失うか、部分 JSON path を測定済み artifact と誤参照し、GO/NO-GO の根拠集合が実走内容と食い違う。

6. **[blocker] S4 は「子孫が残らない」を検査していない。**

   escaped child の PID file を作るが、その PID の消滅を一度も検査せず、1.5秒後に marker が無いことだけで containment 成功とする（[probe.py:641](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:641)）。負荷で child が遅延した場合や、marker 書込みだけ失敗した場合にも `inside_blocked=true` になりうる。

   **成果物影響:** timeout 後も生成 binary の子孫が残る profile を受理し、後続 run・trace・性能値を攪乱できる実行を「process-tree containment 済み」と記録する。

## must-fix

7. **[must-fix] S6 の失敗を sandbox 起因と識別できず、入力 source も pinned-clean ではない。**

   S6 は sandbox 内 build だけを行い、対応する outside 正例がない。それでも任意の build failure を `no-go` にする（[probe.py:156](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:156)）。

   gflags/glog/third-party/CCBench は HEAD だけを照合し、dirty/untracked、replace refs、実際に build した tree SHA を拒否しない（[probe.py:808](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:808)）。先例の tracked-only snapshot 契約を落としている。

   **成果物影響:** source/toolchain の破損を backend NO-GO と誤認して設計案を棄却するか、dirty source 由来 binary の値を stock 性能として台帳へ入れる。

8. **[must-fix] SSH agent の正例は login node の socket path 転送では成立する保証がない。**

   qsub は login の `$SSH_AUTH_SOCK` 文字列を渡すだけで、PBS は絶対 path かしか確認しない（[probe.pbs:8](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.pbs:8)）。node-local socket が計算ノードに無ければ outside 正例は必ず失敗する。計算ノード内で controlled UNIX socket を作る仕組みが必要である。

   `qsub -v` は comma 区切りなので、値の comma/引用問題を job 側で拒否しても投入時の分解は防げない。cache/dependency path には comma 検査もない。

   **成果物影響:** agent socket 項目が恒常的に inconclusive となり、R3-1 完了 IDを作れず、credential 非到達に依存する production profile の受理判断が保留のままになる。

9. **[must-fix] PBS 外側で整えた toolchain 契約が sandbox 内へ保存されない。**

   PBS は Python 3.10 shim を作るが（[probe.pbs:45](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.pbs:45)）、sandbox はその shim を bindせず、PATH を `/usr/bin:/bin` に戻す（[probe.py:443](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:443)）。CMake の孫が `python3` を呼べば、runbook が警告する古い interpreter を再び拾いうる。

   module list、cmake/compiler version・binary hashも残さない。さらに既存 Pegasus 契約は「numactl なし」だが（[pegasus-runbook.md:680](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/docs/pegasus-runbook.md:680)）、S7 は `numactl` が PATH に無ければ即 blocked で、module/load・代替経路がない（[probe.py:934](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:934)）。

   **成果物影響:** sandbox 非互換でなく PATH/module 差による失敗を NO-GO/blocked とし、backend 選択や floor 再計測要否を誤る。

## nit

10. **[nit] `network_dns` は DNS 検査にならない場合がある。**

    `HTTPS_PROXY` の hostname が数値 IP なら、`network_dns` と `network_direct_ip` は同じ proxy IP への接続になる（[probe.py:539](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:539)）。

    **成果物影響:** R3-1 の network connect 自体は別項目で測れるため受理集合は直ちに変わらないが、receipt のカテゴリ名を DNS 遮断証拠として引用できない。

11. **[nit] receipt の profile 記述が観測結果でなく無条件の自己申告である。**

    `runtime_hides_bin_shell=true`、`source_mount=read-only` 等を stage verdict と無関係に固定出力する（[probe.py:1072](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:1072)）。

    **成果物影響:** structured verdict を正しく読む限り値は変わらないが、profile 節だけを参照する後続レポートは失敗した保証を成功済みと誤記しうる。

## 反証済み（件数外）

- **[refuted] S7 が意図的に trace-enabled build を使う。** 現実装は `CCBENCH_TRACE=0`、cache gate、同一 binary SHA を要求する。ただし compile argv を検証せず live source を許すため、「trace-disabled の証明強度」は所見7・9のとおり不足している。
- **[refuted] S6/S7 の通常 skip が黙って GO になる。** `attempted=false` は `blocked`、aggregate も GO にしない。問題は hard termination 時に receipt 自体が無い点である。
- **[refuted] 宣言された直列 cap が必ず90分を超える。** 900+2700+180秒と300秒 reserveの算術自体は5400秒内。ただし S1〜S5 の900秒 capは実装上強制されず、部分永続化もない。
- **[refuted] 同じ PBS job ID の既存 directory を黙って再利用する。** `mkdir(exist_ok=False)` で拒否する。問題は新規 directory 内の部分 `receipt.json` の扱いである。
- **[refuted] production の意味 gate・DSL/IR・SandboxProfile を変更している。** 差分は probe、計測policy、テスト、実行 admission 登録に限られ、production の生成 variant 受理集合には触れていない。

## 総括

- blocker: **6件**
- must-fix: **3件**
- nit: **2件**
- refuted: **5件（件数外）**
- 実走: **なし**
- 判定: **NO-GO**

この probe を現在の形で R3-1 の計測として計算ノードへ投入してはいけない。探索的デバッグとして走らせてもよい水準ではあるが、その job ID／receipt を `DW-G04` の発火 artifact、意味 gate 実装の解除条件、または floor 再較正判断へ使用してはならない。