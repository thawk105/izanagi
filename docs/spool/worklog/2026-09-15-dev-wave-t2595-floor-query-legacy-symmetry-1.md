---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-15
wave: dev-wave-t2595-floor-query-legacy-symmetry
seq: 1
title: [T-2595] 床値 retry query が使用済み trigger の recovery 候補を数えずに legacy 認可を返す非対称を閉じた (コード + テスト、branch worktree-dev-wave-t2595-floor-query-legacy-symmetry、変異 matrix = baseline PASSED・4/4 KILLED・SURVIVED 0・MISMATCH 0・期待 node 完全一致)
---

## 本文

- ユーザー裁定: 「実在する不整合の解消に限定し、一般的な retry framework は作らない。規律 2 を緩めない。
  Codex author = D95。本題の修正だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」。
  この裁定どおり、変更は `floor_retry_trigger_for_round` の `if legacy:` ブロック内に閉じた 8 行と、
  既存 test file への正例 1 本・負例 1 本 (3 parameter) だけである。設計判断は
  {{D:floor-query-counts-recovery-before-legacy}}。
- **段 3 の敵対 2 本が、親 brief の成果物影響の主張を独立に否定した。** 親は現物で全部検算した。
  混在履歴は `_replay_cut6_start` → `_assert_retry_start_authorized_locked` が query より前に拒否し、
  consume は測定 callback より前に走り、production に registry recovery 行の writer が無い
  (`record_attempt_recovery` の非テスト参照は内部委譲のみ)。したがって現時点の成果物の値・受理集合・
  参照は変わらない。閉じたのは公開 query API と消費ゲートの判定不一致である。この誤りは
  F591 の再発として台帳へ記録した。実装方向は訂正後も変わらなかった。
- 段 6 の敵対レビュー 2 本はいずれも must-fix ゼロで、fix 子は起動していない。所見ゼロを緑と数えず
  `DW-M02` に従って変異で裏取りした (4/4 KILLED)。
- 段 2 plan はもう 1 本、campaign resume 全体を回す正例を提案したが段 4 で不採用とした。
  新しい拒否の production 到達性を証明できないうえ、局所的な保存性は追加した正例が撃ち、
  legacy の retry / resume 退行は既存の `test_s8b_floor_campaign.py` の 3 本が既に撃っているため。
- 段 6 の中間受入は 2 回投入し、いずれも 23665 passed / 68 skipped / error 1 で受領証は出なかった。
  2 件とも非帰属である。1 回目は `/tmp` の real-repo 共有 lock を他の受入 4 本が READ 保持したことによる
  write 取得の 245 秒 deadline 超過 (対象 `test_s8c_preregistration_predicates.py`)、2 回目は
  未追跡走査 `git ls-files --others` の 30 秒 timeout (対象 `test_t1259_qsub_env_delivery_probe.py`)。
  どちらも単独再走で非再現 (前者 rc=0、後者 3 passed / 18.61s)。投入時の同時受入は 7〜10 本だった。
  **land 対象 tip への最終受入は `DW-O12` に従い本 commit と段 8 の後に投入する。**
- 工数: codex 子 6 本 (plan 1、敵対相談 2、実装 1、敵対レビュー 2)。いずれも rc=0 で
  `check_codex_output.py` 受理。逐語は `output/insights/2026-09-15_t2595-floor-query-legacy-symmetry/verbatim/`。
- 段 3 が scope 外の real 所見を 3 件返した。2 件を新規項として起票し、3 件目は事実として本文へ残す —
  registry recovery writer が production 未接続であり、recovery 機構一式をいつ live にするか
  (scheduler collector の接続) は本 wave の外の優先順位判断である。

## 次の一手差分

### 完了

- [T-2595] 床値 retry の query 側で、recovery 収集は使用済み trigger を除外するのに legacy 集合は
  除外しない非対称を閉じた。legacy 認可を返す前に同じ trigger の recovery 候補を使用済み除外なしで
  数え、非空なら消費側と同じ文言で拒否する。
  remaining: none
  base: 9c39115fb34e7df18395610a790e6bde538f86b41df5bf152e1ea1f12120c45e

### 新規

- {{T:floor-legacy-completion-round-asymmetry}} **P3・新規**: 床値 retry の消費側 canonical 判定は
  legacy 完了行の `round` を検査しないのに、query は検査する逆向きの非対称を閉じる。
  `start P(round=1)` に対し `session P(round=2, kind=planned, valid=false, 同じ cell)` を置くと、
  round=1 の query は legacy 候補から外すが、P を trigger とする retry の消費側は受理する。
  [T-2595] の敵対相談が現物で示した既存差であり、同 wave では scope 外として実装しなかった。
- {{T:floor-registry-hash-type-leak}} **P3・新規**: 床値 registry の recovery 行で
  `start_event_sha256` が list / dict のとき、候補判定の集合 membership が `TypeError` を送出し
  admission 例外へ変換されずに呼び手へ漏れる。canonical JSON であることだけでは防げない。
  query と消費側が共有する既存挙動であり、[T-2595] では scope 外とした。
