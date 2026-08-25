---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-26
wave: dev-wave-t1726-freeze-rederive
seq: 2
---

## 新規

### {{F:mutation-observation-root-shared-checkout}}. 変異 harness の観測 root に共有 checkout が入り並行 land で落ちる [手順漏れ]

- 事象: 変異走行が 5 変異とも完走した直後、wrapper が `rc=125`
  (`source/main 共有木の観測 bytes が変化した`) で中止し、収集済みの結果が受理されなかった。
- 根本原因: `tools/mutation_worktree.py` の観測 root は
  (`--source-repo` の primary worktree, `--source-repo`) であり、既定では共有 checkout が入る。
  並行 wave の land が走行中に status bytes を変えると必ず事後検査に落ちる。走行が長いほど確率が上がる。
- 恒久対応: 検出は `tools/mutation_worktree.py` の fail-closed な事後検査
  (`_assert_shared_unchanged`) が既に担っており、欠けているのは「独立 clone を渡す」という手順である。
  `docs/dev-wave/mutation.md` の `DW-M05` へ 1 行追記したが、L1.5 層の byte 予算
  (残 21 bytes に対し追記 150 bytes) に収まらず戻した。予算値の引き上げは自己改善の範囲外のため、
  本エントリを手順の正本ポインタとし、予算側は裁定へ回した。
- 再発検知: 変異 harness が `rc=125` で止まったら、変異でなく観測 root を疑い、
  `--source-repo` が共有 checkout を指していないか確認する。
  clone の submodule url を local path にする場合は `-c protocol.file.allow=always` が要る
  (既定は `user` で submodule の file transport を拒否する)。

### {{F:mutation-collection-abort-deadlock}}. 収集段で落ちた変異走行が resume も fresh 走も塞ぐ [手順漏れ]

- 事象: 変異本走が収集段で `rc=16` (`receipt scheduler_logs.stdout.path がない`、
  同時刻の `qstat -Q` は gen_S に 101 件で scheduler 混雑) により中止した。
  復帰しようとして 3 回の起動を失った。
- 根本原因: 中止点が台帳作成より手前だと、resume の前提と fresh 走の前提が同時に満たせない。
  `--resume` は `--out` の既存 file を要求するが収集段中止では `--out` が作られない。
  一方 retained container が残るため、同じ `--scratch-root` の fresh 走は
  「container が既に存在するため所有を拒否」で止まる。
  さらに `--resume` の `--attempt-out` は**既存 file 必須**で、
  `DW-O19` の「再走は `--out` と `--attempt-out` を新 path にする」と要求が逆向きである。
- 恒久対応: 中止した走行から復帰する経路は**新しい `--scratch-root` での fresh 走**だけである。
  検出は harness の fail-closed な 2 つの拒否 (`container が既に存在する` /
  `--resume には既存の ... --out file が必要`) が担い、本エントリを手順の正本ポインタとする。
- 再発検知: 上記いずれかのメッセージで止まったら resume を繰り返さず、
  新しい `--scratch-root` を作って fresh 走で再投入する。
