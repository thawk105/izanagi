---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-26
wave: dev-wave-t1858-chain-shared-setup
seq: 2
---

## 新規

### {{F:flaky-hold-remediation-blocked-by-ownership}}. 非帰属 flake の規定の是正経路 2 本が、どちらも並行 wave の所有で塞がれ land が止まった [手順漏れ] [資源競合]

- 事象: 本 wave の受入全走が 2 走続けて `test_codex_worker_launch.py::test_sigterm_ignoring_child_is_killed`
  1 件だけで赤になった (17392 passed / 1 failed / 64 skipped、2 走とも同一 node・同一 assertion)。
  assertion 本文は `child.pid was not registered before deadline; stderr=''` で、
  子 process が 2 秒の期限内に pid file を書けなかったという時間依存の主張である。
  同 node の単独走は 1 passed / 7.15 秒で再現しない。本 wave の差分は s8c 事前登録の
  test 2 file だけで、この経路へ到達しない。**非帰属である。**
- `DW-O18` は再赤に対して「main 既存の F を証拠に Codex `role=author` が
  `orchestrator/tests/flaky_test_holds.py` へ登録」を規定する。証拠は F57 が満たしており、
  検証器の要求 (evidence section が test 関数名と failure signature を逐語で含むこと) も
  実測で確認した。**それでも登録できなかった。**
- 根本原因: 是正経路 2 本がどちらも並行 wave の所有下にある。
  (a) `orchestrator/tests/flaky_test_holds.py` は 3 wave が触っており、うち
  `dev-wave-flaky-holds-20260826` は**登録済み hold を全撤去する wave** である。
  ここへ新しい hold を足すのは所有違反であるうえ、その wave の目的と正面から衝突する。
  (b) 期限そのものを直す `orchestrator/tests/test_codex_worker_launch.py` も 2 wave の所有下にある。
- **これは 2 段依存とは別の塞がり方である。** F57 が既に記録している 2 段依存
  (hold は既 land の証拠を要求し、証拠の land は受入 green を要求する) は証拠側の問題だが、
  本件は証拠が揃っているのに**編集面の所有**で塞がる。並行 wave 数が増えるほど、
  規定の是正経路が特定の wave に占有されて他の全 wave が land 不能になる確率が上がる。
- 恒久対応: 下記 3 案のいずれかをユーザー裁定で選ぶまで、本 wave は land を止めて報告する。(1) 是正経路の file を編集面重複検査の
  例外にし、hold 登録だけは所有に関わらず追記を許す。(2) hold registry を wave ごとの
  fragment + fold 方式にして行の奪い合いをなくす (docs/spool と同じ構造)。
  (3) 当該テストの 2 秒期限を負荷分布から導いた値へ上げ、flake そのものを消す。
  (3) は coverage を落とさない唯一の案だが、所有と受理集合の両方に触れる。
- 再発検知: 受入が非帰属赤で 2 走連続して落ち、かつ是正経路の file が別 wave の所有下にある状態。
