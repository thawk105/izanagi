---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-08
wave: dev-wave-t632-waiter-condition
seq: 2
---

## 新規

### {{F:qdel-deleted-peer-session-job}}. 並行 session の走行中 job を自分の孤児と誤認して qdel し、他人の受入全走を潰した [権限逸脱] [計測汚染]

- 事象: 2026-08-08 [T-632] wave。親が受入全走を背景 task として投入した直後、記録 fragment を
  1 件足すために `TaskStop` で止めた。**harness の task は終了したが、dispatch 済みの
  NQSV request `895589` は RUN のまま残った** (dispatcher の qdel guard は
  `reason=state-not-cancellable` を返し「ユーザー自身の端末で qstat を確認してください」と
  出して降りた — 背景 job には存在しない宛先で、F66 と同型)。ここまでは正しく、親は自分の
  `895589` を `qdel` した。**問題はその直後である** — `qstat` に現れた `895590` を
  「自分の残骸」と推測して `qdel` した。実際には **並行 session `dev-wave-t139-producer` の
  走行中の受入全走**であり、親はそれを潰した。相手の harness は自動で再投入し (`895591`)、
  親が誤りに気づいたのはその 2 本目を見てからだった。
- 実害: **他 session の受入全走 1 本 (十数分規模) を無駄にさせた。** repo・成果物・台帳への
  破壊はなく、相手は自動再投入で復旧している。親自身の受入結果も得られていない。
- 根本原因: **所有権を確認せずに破壊的操作を行った。** `qstat` の既定出力は RequestID と
  ReqName しか出さず、どの worktree が投げたかを示さない。親はそれを時刻の前後関係だけで
  推測した。**確認手段は最初から存在した** — request 名 `izdw-<nonce>` の nonce は、
  投げた worktree の `output/pegasus-dispatch/<nonce>/` と 1 対 1 に対応する。
  1 コマンド (`ls -d */output/pegasus-dispatch/<nonce>*`) で所有者が確定できた。
- 誘発要因: (i) 走行を止める必要が無かった。追記したかったのは fragment 1 件で、走行を
  終わらせてから 2 度目を投入すればこの連鎖は始まらなかった。(ii) `TaskStop` が計算ノードの
  job を落とさないという事実を知らず、「消えていないのは異常」という前提で急いだ。
  (iii) `DW-C00` の待ち手規約は「生産者を止めるときは待ち手も落とす」向きだけを書いており、
  逆向きの「待ち手を落としたら生産者が本当に死んだか確認する」が無い。
- 恒久対応: memory [[dev-wave-taskstop-leaves-compute-job]] —
  (1) 走行は原則止めない、終わらせる。(2) 止めた場合も `qdel` の前に nonce → worktree の
  対応で**所有者を確定**し、自分の worktree に nonce dir があるものだけを消す。
  (3) 所有者を確定できない request は消さずユーザーへ報告する。
- 再発検知: `qdel` の直前に所有者確定コマンドを実行した記録が無ければ同型。
  自分が投げた覚えのない request が `qstat` に現れたら、まず並行 session の存在を疑う
  (`/work/1/SFC/tanab/dev-wave-jobs/handoff/` の生きた handoff が一覧である)。

## 再発

### F57

- **再発: 2026-08-08 ([T-632] 受入全走)。** 48 worker の全走 (request `895587`、7,249 件) で
  `test_codex_worker_launch.py::test_check_receipt_detects_executable_identity_change` が
  1 件落ちた (7228 passed / 1 failed / 20 skipped)。落ちたのは receipt 検査の assert ではなく
  **その手前の準備段 `_run_case(tmp_path, "normal")`** で、launcher subprocess が
  rc=1 / stdout・stderr とも空を返した (`assert 1 == 0`、gw32)。同 file の単独再走
  (request `895588`) は 64 passed / 5.26 秒で再現しない。本 wave の差分は
  `.claude/commands/dev-wave.md` の **1 行 (docs のみ)** で launcher 実装にも当該 test file にも
  到達しえず、`DW-O18` により帰属しない。**新しい情報は失敗 node がまた別の node へ移ったこと**で、
  台帳既載のどの node とも異なる。**今回は親が codex 子を 1 本も起動していない全走**であり、
  「親の子 process との資源競合」という既存の説明は今回成立しない。
  恒久対応は F57 既載のとおり失敗 artifact 保存による原因分離 ([T-190]) で、本 wave では変えない。

### F66

- **再発: 2026-08-08 ([T-632] wave の立ち上げ)。** 背景 job が新規 worktree を作り
  `tools/check_wave_startup.py` を走らせたところ、2026-08-01 とまったく同じ
  `NG: submodule is not initialized ... 親セッションで submodule を初期化する` で停止した。
  対処も同じく当の worktree で `git submodule update --init` を走らせることだった
  (`--recursive` は不要で、これだけで緑になった)。**F66 の恒久対応にある「`DW-O20` への
  導線追記」は 7 日経っても未着手**であり、`docs/dev-wave/operations.md` は 8,301 / 8,400 bytes
  (残り 99 bytes) で今も入らない。[T-641] の裁定 (予算超過で撤回した恒久対応は failures 台帳と
  memory の記録で担う) に従い、本 wave でも文書側は変えず記録だけを厚くする。
