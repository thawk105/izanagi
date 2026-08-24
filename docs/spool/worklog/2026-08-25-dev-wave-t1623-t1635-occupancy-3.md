---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-25
wave: dev-wave-t1623-t1635-occupancy
seq: 3
title: [T-1623]+[T-1635] 占有検査の削除済み cwd 誤判定と wrapper 偽陽性を直した (コード + テスト、branch worktree-dev-wave-t1623-t1635-occupancy、変異 matrix = baseline PASSED・14/14 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- **台帳が記録していた原因が誤っていた。** `[T-1623]` の起票文と F489 の 2026-08-24 再発追記は
  どちらも「消滅 pid 型 issue」と書いていたが、実測では **pid は消えていない**。
  犯人は cwd の指す directory が削除済みの**生存プロセス** 2 本 (`State: S`、
  cwd link は `/home/SFC/tanab/.claude/jobs/aa3f1d2b/tmp (deleted)`)。
  `os.readlink` は成功し `resolve(strict=True)` だけが `FileNotFoundError` を投げる型で、
  pid が生存しているため D705 の有界 3 再試行では構造的に解けなかった。
  誰も居ない空 directory ですら rc=2 になり、5 scan 連続で同一 pid・同一内容だった。
- **修理は login node の実測で確認した。** 着手前 rc=2 だった空 directory が **rc=0 /
  `unoccupied` / issues 0** になり、原因の 2 プロセスは `unreachable.cwd_deleted: 2` へ計上された。
  同じ file を計算ノードへ dispatch すると着手前から 89 passed で全緑だったので、
  **受入全走の緑はこの修理の証拠にならない**。判定は login node の非 pytest probe で行った。
- **偽陽性を作る wrapper は `timeout` だけではなかった。** 空 directory へ各 wrapper 経由で
  走らせた実測では `timeout` / `flock` / `/usr/bin/time` / `strace` の **4 種**が `occupied` を返し、
  `nohup` / `env` / `stdbuf` / `setsid` / `nice` / `ionice` は自分を exec で置き換えるため発火せず、
  `xargs` は対象が stdin 由来で argv に載らなかった。段 2 プランの allowlist は
  **発火する 4 種のうち 1 種しか覆わず、載っている 5 種のうち 3 種は到達不能**だった。
  修理後は 4 種すべてが rc=0 / occupants 0 になった。
- **親の provisional 裁定を段 4 で 3 つ撤回した。** (a) rc=3 新設は、受理・拒否集合が 1 bit も
  変わらないのに pin 7 群の同期を増やすため撤回し `status:"invalid-target"` + stderr にした。
  (b) 祖先鎖の exe 条件撤去は、既存負例が守る性質が「非祖先は信頼しない」ではなく
  **「親であるだけでは信頼しない」**だと段 3 の 2 子が独立に本文から示したため撤回した。
  (c) 「`DW-O28` の実運用形が偽陽性を作る」は自分の実測で取り下げた — 実運用の親 shell は
  `bash -c '<1 token>'` で対象が token 内部に埋まり一致しない。
- **段 6 のレビューが実装本体の fail-open を掘り当てた。** 厳密 suffix 要求を入れたのに、
  判定が `readlink` の生値ではなく**正規化後**の path に掛かっており、
  `/outside/gone (deleted)/child/..` が畳まれて判定を通っていた。
  段 4 で足した防壁が実装段で骨抜きになっていた形で、静的レビューでしか出ない型である
  ({{F:strict-suffix-defeated-by-normalization}})。
- **false green も 1 件見つかった。** drift 検査の `pytest.raises(match=...)` が広すぎて、
  意図した比較へ到達する前の別の早期エラーを拾って緑になっていた
  ({{F:broad-match-regex-hides-early-error}})。
- **変異は検出力ゼロがゼロだった。** A2 (対象内の削除済み cwd を非占有へ落とす fail-open) は
  実 kernel node を含む 3 件が、A3 (厳密 suffix 要求の撤去) は上記 fail-open の回帰 node が、
  A10 (exe allowlist の撤去) は spoofed-argv0 の負例が捕捉した。
  **allowlist を捨てないという裁定が変異で裏付けられた。**
- **A15 (循環停止の撤去) は意図どおり無限ループになった** — `seen` が効いている証拠である
  (`DW-M06`)。ただし harness の 900 秒 hang timeout が発火した後も計算ノード job の終端を
  確認できず orphan-hold を張ったため、本 matrix からは外し TIMEOUT 観測だけを証拠として残した。
  手動 qdel は F47 ラッチを武装させるため行わず、job の自然終端を待って dirty source を復元した。
- **変異本走の結果**: baseline PASSED、**14/14 KILLED、SURVIVED 0、MISMATCH 0**。
  期待 node は probe で観測した完全集合をそのまま登録し、本走で全件一致した。
- **本 wave 自身の作法の欠落を 2 件記録する。** (a) 変異走行中に記録 fragment を書いて
  untracked file を作り、harness を `rc=2` で中断させた。既知の規律を破って 1 回分の走行を捨てた。
  (b) 背景の待ち手が子の生存中に 3 回続けて完了通知を出した。`.done` file も成果物も無いのに
  「completed」で、`pgrep` で harness の生存を確認して発覚した。`dev_wave_wait.py producer` 版でも
  素の `until [ -f ... ]` 版でも同じで、Monitor へ切り替えて解決した。
  実測を挟まず通知だけを信じていれば、走行中の tree を land しかけていた。

## 次の一手差分

### 完了

- [T-1623] 占有検査の削除済み cwd 誤判定を直し、受入除外から cleanup テストを戻した。
  remaining: none
  base: 3ae0a7c4245d9b307e1a45aae3227d4ed8cf3c4ab0c7b069057609d425957a81

- [T-1635] cmdline 除外を祖先鎖へ広げ、不正な対象を status で区別するようにした。
  remaining: none
  base: f0abd9dce46db87d39df609c780d4c8b8034e9254538d27baa9c6d0d8f3158d0

### 新規

- {{T:occupancy-unreadable-cwd-fail-open}} **P1・新規**: 占有検査が cwd を読めない生存 process を
  非占有として数える既存 fail-open を塞ぐ。同じ uid の non-dumpable process が対象内に cwd を持つと
  `unoccupied` になり撤去されうる。**F490 / D706 で 2 度失敗している** —
  `cwd_permission>0` 拒否は実測 2,020〜2,213 で恒久不成立、comm allowlist は `nqs_shpd` で
  11 件赤。再挑戦は lease 前提の設計から始める。
- {{T:occupancy-scan-rmtree-race}} **P2・新規**: 最終 scan と `shutil.rmtree` の間に新規 process の
  参入を排除する仕組みが無い。checker 自身が「走査後に始まる process は観測できない」と明示しており、
  恒久解は lease である。
- {{T:occupancy-invoker-edge-proof}} **P2・新規**: cmdline 除外の invoker exe allowlist を、
  祖先 edge を invoker ごとに証明する条件へ置き換える。allowlist の列挙は原理的に whack-a-mole で、
  `sudo` / `chrt` / `taskset` / `unshare` / `systemd-run` / 自作 runner はいくらでも作れる。
  併せて wrapper script が対象を独立 argv token で渡す形の偽陽性も同じ根で解ける。
- {{T:mutation-hang-job-orphan}} **P2・新規**: hang 変異の timeout 後に計算ノード job の終端を
  確認できず orphan-hold が張られる。hang 変異用の走行だけ短い walltime で投入するなど、
  job を確実に終端させる経路を用意する。本 wave では A15 を本 matrix から外して回避した。
