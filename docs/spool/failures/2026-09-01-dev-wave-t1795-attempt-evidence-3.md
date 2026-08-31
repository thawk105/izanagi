---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-01
wave: dev-wave-t1795-attempt-evidence
seq: 3
---

## 新規

### {{F:pinned-external-session-vanished}}. repo 外へ pin した過去 session が定期削除で消え、全 wave の受入が決定的に赤になった [テスト代表性] [ドリフト]

- 事象: 受入全走が `orchestrator/tests/test_codex_reasoning_ab.py` の 26 node
  (5 failed + 21 error) で赤になった。起票した wave は同 file を 1 byte も変更していない。
  現行 main (`24014bdb259d971571f22b54a8f10a49352b825f`) 単独の probe worktree で
  **同じ内訳 (5 failed + 21 error) が再現した**ので非帰属である。並行する 5 セッションが
  独立に同じ診断へ到達し、この機体の全 wave が受入で踏む状態だった。
- 根本原因: `tools/codex_reasoning_ab.py:196-209` が `~/.codex/sessions` 配下の
  **過去 session 5 件を ID と SHA-256 で pin して後日読む**。pin 先は全て 2026-07-29 のもので、
  実測時点で `~/.codex/sessions/2026/07/` が丸ごと存在しない (現存は `2026/08/01` 以降、
  同 root には rollout が 7138 件)。`~/.codex` 配下に 7 月分の退避も無く、**pin 先は復元不能**。
  4 セッションが独立に全探索して 0 件だった。
- **削除は事故ではなく運用である。** 会話ログはストレージ上限のため定期的に削除される
  (2026-09-01 に中継されたユーザー指示)。したがって同じ pin は今後も再び落ちる。
- **被覆の喪失はこの機体では恒久である。一時的ではない。** 消えた 26 node は
  「緑になった」のではなく「実行されていない」。受入の総数だけを見ると通ったように読めるので、
  読み手はここを取り違えてはならない。
- 失われる検出力は実在する (独立相談が file:line で確認)。production の reject 述語は弱まらないが、
  2026-07-29 の実 corpus そのもの、独立 golden 二経路の実 patch 合成、実 prompt の置換数、
  実 snapshot から完全 replay までの結合被覆には完全な代替が無い。登録済みの M1 / M2 / M3
  mutation killer も止まる。合成 fixture 側 (`同 file:7154-8010`、`:8366-8491`) に部分的な代替はある。
- 影響: 受入全走が緑にならない間は `tools/dev_wave_land.py` が受領証を発行せず、
  **どの wave も land できなかった。**
- 恒久対応: 単独の unblock wave が同 file の可用性判定を実依存の粒度へ直す
  (再導入タスクは当該 unblock wave が起票する)。述語は
  「`rollout-*-<escaped session id>.jsonl` の候補が 0 件のときだけ skip」に限定し、
  **候補が存在するのに SHA 不一致・malformed・session 所有不一致・重複・読取不能なものは
  従来どおり赤のまま**にする。既存の guard は root directory の有無という粗い粒度
  (`orchestrator/tests/test_codex_reasoning_ab.py:788-790`) で、実際の依存である
  特定 5 session を捉えられなかった。
- 再発検知: skip 理由の文言へ不在 label を明記し、`historical root unavailable` で済ませない。
  **受入 receipt は skip node ID を保持せず red と flake だけを持つ**ため
  (`tools/dev_wave_land.py:102-130`、`tools/task_runs/pytest_stats.py:18-20`)、
  receipt と総数だけでは「どの検査が走っていないか」を後から復元できない。
- 射程: tracked な実行コードと test を `git grep` で走査した範囲では、
  「repo 外の可変 root から固定した過去 identity と SHA を後日再読する」同型の経路は
  この 2 file 以外に見つからなかった。repo 外・untracked・ignored file は未検査である。
