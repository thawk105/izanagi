---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-11
wave: dev-wave-t657-stage0-rulings
seq: 1
title: [T-657] 段 0 残余 3 束の裁定を実施した — 失効 schema と段 6 gate は越権として実装せず裁定へ返し、段 0 完了が構造的に到達不能である新事実を見つけた (コード + docs、変異 7/7 KILLED + 事前登録一致、branch worktree-dev-wave-t657-stage0-rulings)
---

## 本文

- **裁定 5 点を実施した** (worklog 403 / `output/insights/2026-08-11_t657-stage0/package.md` §8)。
  U-A1 = 未発効 activation window / rollback = forward compensating generation /
  revocation = 下位 authority へ fallback しない fail-closed / 下位 X_f は上位 X の後 /
  §8 と §10 の矛盾 = 段 0 完了判定から段 5 を除外。設計正本の規則は正本節を一意に決めて置き、
  §12 は索引だけにした。機構側は裁定 profile 4 ID と required gate 5 件を `resolved` へ動かした。
- **段 3 の敵対 2 レンズが独立に同じ blocker を構成し、親の provisional 裁定を 2 件撤回した。**
  (a) 失効 record の namespace・schema・commit topology を本 wave で定める案 — 裁定が答えたのは
  fallback の可否だけであり、置き場と形式は設計正本 §12.3 が「親が決めない」に置いた項目のまま。
  複数の形が成立し選択で受理集合が変わるため越権。(b) 段 6 用の新 gate を `owner=user,
  status=unresolved` で起票する案 — 設計正本は新しいユーザー択一の存在を述べていない。
  台帳へ既成事実化しないため gate を作らず、扱いを裁定へ返した ({{T:cfab-stage6-completion-predicate}})。
- **裁定時点で未見の新事実を 1 件見つけた** ({{T:cfab-stage0-completion-unreachable}})。
  §10.2 の第 1 条件は先送り確定の `CFAB-S-SEAL` と `CFAB-B-SIDE-EFFECT` を数えるため、
  **先送りを維持する限り段 0 は `complete` へ到達しない。** 束 3 (a) の裁定 (段 5 除外) は
  fixture 側の要求を外すだけで、この条件に触れていない。親判断で applicability を広げて回避せず、
  §10.2 と §12.3 R2 に記録して裁定へ返した。
- **段 6 のレビューが、本 wave で新設した検査そのものの破れを 2 巡にわたって構成した** ({{F:design-literal-hidden-in-html-comment}})。
  1 巡目 = 設計正本の旧 literal を HTML comment へ隠し可視部分だけ書き換えると素通りする。
  2 巡目 = その fix (comment を除去して可視部分だけ読む) が、code fence 内の開始と外側の終了が
  対になって可視の drift 行ごと消すため、**fix 前に拒否された文書を受理する新しい抜け道**を作った。
  除去をやめ「設計正本に HTML comment が存在すること自体を拒否する」へ倒し、判定を 1 述語に閉じた。
- **変異の事前登録を 1 件外した (erratum)。** 段 4 は「却下案 `post-activation-lease` を enum へ
  戻す変異は state pin に隠れて SURVIVED」と登録したが、実測は **KILLED / 28 node** だった。
  新設した「設計 §8.1 の許容 selection 列 ↔ `_SELECTION_ENUMS`」照合が先に落とすためである。
  影響範囲が広い 2 件 (この変異と過剰拒否検出の正例) は discovery 走で失敗 node 集合を実測してから
  本走の期待へ入れた。本走は **7/7 KILLED、全件が事前登録と一致**、baseline 緑。
- **親が段 4 の変異 ID 体系を勝手に組み替えていたのをレビューが検出した。** 事前登録の意味を壊すため
  M1〜M6 の番号を戻し、期待の変更は erratum として本エントリに残した ({{F:mutation-spec-renumbered-after-preregistration}})。
- 本 wave は帳簿 (裁定 profile・gate 表・設計正本) を裁定へ整合させたもので、
  **selection literal を読む resolver は存在しない。policy を実装したのではない。**
  production (`orchestrator/campaign/**`、`tools/**`) と case file 10 件の bytes は不変。
- 段 8 の改善候補は {{D:dev-wave-waiter-pid-and-codex-coldstart}} を参照。

## 次の一手差分

### 更新

- [T-657] **P1・段 0 の裁定 5 点を実施済み。新たなユーザー裁定待ちが 3 件 (R1〜R3)**:
  設計正本 §12.1 に裁定済み 9 行、§12.3 に R1 (失効 record の namespace と schema。候補 2 案と
  親の推奨 (a) を併記) / R2 (段 0 完了の到達可能性。先送りを維持する限り `complete` は到達不能。
  親の推奨は (b) = S と B の裁定後まで待つ) / R3 (段 6 の完了 predicate。親の推奨は構造部分と
  policy 依存部分への分割) を記録した。他者手番 gate 2 件
  (`FREEZE-CONFORMANCE-LITERAL` / `FREEZE-AX-TOPOLOGY`) は不変。段 0 status は `incomplete`、
  `pending` 5 件も不変。正本 = `docs/calibration-freeze-authority-bundle-design.md` §12
  base: 72bfd65af56cf07a653d2fe51981513254b127d1e7e21fa8c8bf526fe1d18146
- [T-772] **P2・帰属が確定した (peer の実測)**: [T-665]/[T-662] の wave は原因ではなく
  **発火確率の増加要因**である。同 wave は `tools/codex_worker_launch.py` の終了観測経路
  (`termination_verified` / `process_group_residual` / `_terminate` / `_normal_reap`) を
  1 件も変更しておらず、落ちた 2 test も終了予算 `0.05` も base に既存だった。変わったのは
  同 test file の `_run_launcher_subprocess(` 呼び出しが 10 → 21 に増えたことで、xdist 並列下の
  launcher subprocess spawn が倍増し、負荷依存の既存 flake が発火しやすくなった。
  base: 566300a227ba18c97003653802a045918ea211a6c9f03b957317cf20bab5b72f

### 新規

- {{T:cfab-stage0-completion-unreachable}} **P1・ユーザー裁定待ち**: [T-657] 段 0 の完了 status が
  構造的に到達不能である。§10.2 の第 1 条件が先送り確定の S と B を applicable な `unresolved` として
  数えるため、先送りを維持する限り `complete` にならない。(a) §8-2 の applicability を段 0 status
  へも及ぼす (先送り確定項目を算入から外す) / (b) 段 0 の完了を S と B の裁定後まで待つ /
  (c) 現状維持で後続段は段 0 完了を前提にしない。親の推奨は (b) — (a) は「決めなくても完了できる」
  経路を作り、§8-2 が発効 X に課した要求を段 0 側で空洞化する。
  正本 = `docs/calibration-freeze-authority-bundle-design.md` §12.3 R2
- {{T:cfab-revocation-record-schema}} **P1・ユーザー裁定待ち**: [T-657] の失効 record の
  namespace と schema と commit topology。2026-08-11 の裁定は fallback の可否だけを答えた。
  (a) `revocations/<bundle_digest>.json`・exact 7 key・束当たり 0/1 件・UTC 秒 int /
  (b) `revocations/<record raw sha256>.json`・承認 record 単位・RFC 3339。どちらでも
  「fallback しない」は成立する。親の推奨は (a) — 束を単位にすると同一束への 2 通りの失効が
  構造的に置けず、resolver の解決不能条件が単純になる。
  正本 = `docs/calibration-freeze-authority-bundle-design.md` §12.3 R1
- {{T:cfab-stage6-completion-predicate}} **P2・ユーザー裁定待ち**: [T-657] 段 6 の完了 predicate。
  段 6 の判定式も段 5 の裁定 (先送りの S / B) に依存する。段 5 の除外を段 6 へ広げるか、
  段 6 を構造部分 (X の形状・ancestry) と policy 依存部分へ分割して前者だけ段 0 で固定するか。
  親の推奨は分割。**本 wave では gate を新設していない** (裁定の無い択一を台帳へ既成事実化しない)。
  正本 = `docs/calibration-freeze-authority-bundle-design.md` §12.3 R3
- {{T:cfab-design-row-extraction-declared-form-only}} **P3・新規**: 設計正本 §11.2 の row 抽出が
  宣言形 (`row ID = ...`) だけを拾い、表形式で足した行を fixture 閉包から取りこぼす。
  本 wave 由来ではない既存の穴で、単発事例のため族一般化しない (`DW-G03`)。
  正本 = `orchestrator/tests/calibration_freeze_authority_contract.py` の row 抽出器
