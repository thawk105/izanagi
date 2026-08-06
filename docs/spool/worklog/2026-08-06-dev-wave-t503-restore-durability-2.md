---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-06
wave: dev-wave-t503-restore-durability
seq: 2
title: [T-503] 変異復元耐久化の第一 slice を凍結せず 6 択一を返す — 木へ触る process は arm より後に生まれると実測 (docs のみ、branch worktree-dev-wave-t503-restore-durability、実装差分がないため変異 matrix と受入全走は対象外)
---

## 本文

- **生死確認 GO を受けた実装 wave だが、コードを書かずに止めた。** 基盤 3 単位
  (WAL primitive の抽出・原子的 target 置換・journal 記録層) を配線せずに作る案を起草し、
  敵対相談 2 レンズを経て段 4 で「実装しない」と裁定した。ユーザー裁定を不採用にしたのではなく、
  **裁定時点で未見だった新事実**を添えて再裁定へ戻す。判断は {{D:no-issuerless-capability-freeze}}。
  裁定パッケージと逐語は `output/insights/2026-08-06_t503-restore-durability-implementation-ruling/`。
- **決定的だった新事実は「木へ実際に触る process は arm より後に生まれる」。** 変異 harness は
  target を書いた後に runner を新しい session で起動し、dispatch ではその先に job も生まれる。
  したがって arm 時点の単一 writer identity を持つ record では quiescence 束縛を満たせない。
  設計が要求する identity のうち worktree incarnation nonce は実在せず、`PBS_JOBID` は
  login shell では unset である。いずれも親が一次資料で確認した。
- **段 3 の 2 レンズは独立に「安全な部分集合は無い」へ到達した。** 抽出だけ先行すると稼働中の
  durable 経路を触る risk だけを負い、原子的置換だけでは caller がおらず、journal だけ残すと
  検証を caller の callback へ逃がして no-op 復元でも terminal を書ける。
- **親の provisional 裁定は 2 件が縮小・否定された。** 「pin が無いから proof chain は不変」は
  一般化として refuted で、成立するのは列挙した regression に対する現行挙動不変までである。
  「root 非依存 library なら後で被せても壊れない」も refuted — caller が自前構築できる root は
  canonical にならない。receipt の code identity が leaf-only である盲点は**既存**であり、
  抽出が作るものではないため、T-503 と独立の新規項目として起票した。
- **L-B (物理ノード死) は `UNKNOWN` のまま据え置く。** 本 wave は何も活性化しておらず、
  [T-486] は `deferred`、D130 条件 3 も closed にしない。次 wave の受入条件として
  「syscall 順序であって物理永続性ではない」を test 名・docstring・完了記述へ残すことを明記した。
- 記録は docs のみ。**実装差分がないため変異 matrix と受入全走は対象外**であり、
  `tools/check_docs.py` と影響テストだけを走らせた。

## 次の一手差分

### 更新

- [T-503] **P1・ユーザー裁定待ち**: 変異復元の耐久化。生死確認は GO
  ((255)) だが、第一 slice は凍結せず 6 択一 (V-1〜V-6) を返した。骨格を決めるのは
  (1) 活性化まで配線しない多 wave program で層を積むか、設計 §7.1 が示唆する
  「使い捨て専有 worktree 方式」を第一 slice にして族一般化と consumer 契約を回避するか、
  (2) arm より後に生まれる runner / job を runner 登録 record で束縛するか
  全 child を包含する exclusive lease で束縛するか、
  (3) `clean` の発行を production verifier だけが持つ sealed capability にするか。
  残る 3 件は canonical root と incarnation nonce の発行者、metadata の accepted set、
  抽出と receipt closure の関係。親の推奨は択一表に併記した。
  正本 = `output/insights/2026-08-06_t503-restore-durability-implementation-ruling/` と
  `docs/mutation-restore-durability-design.md` §9 / §9.1 / §9.2
  base: 265a14237bbaeb268c1b0ca5bb233f92aeb7ab817ca8bcbd84f807675d931ace

### 新規

- {{T:proof-receipt-code-closure}} **P2・新規**: admission receipt の `validator.sha256` と
  oracle の `generator_versions` は leaf source の hash だけを記録し、判定に使う被 import module の
  意味論を閉じていない。`artifact_admission` は自分自身を hash しながら WAL の
  strict reader へ判定を委ねており、reader 側が変わっても receipt は不変のまま受理集合が変わりうる。
  T-503 とは独立に成立する穴で、versioned transitive source closure を新設するか、
  盲点を明示的な限界として記録するかの択一を含む。
- {{T:clean-tracked-ignored-blindness}} **P2・新規**: 変異 harness の入場 gate が
  ignored file を見ていない。`git status --porcelain=v1 --untracked-files=all
  --ignore-submodules=none` は `--ignored` が無いと ignored を報告しないため、
  `*.o` / `build/` / `*.so` のようなテスト結果を左右する生成物と skip-worktree entry に盲目である。
  設計 §10 が実測済みで、T-503 の活性化とは独立に実装でき、汚染木で得た値が台帳へ載るという
  成果物影響を書ける。
