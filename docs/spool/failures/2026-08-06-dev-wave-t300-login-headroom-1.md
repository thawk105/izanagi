---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-06
wave: dev-wave-t300-login-headroom
seq: 1
---

## 新規

### {{F:refusal-path-side-effect}}. 拒否メッセージの生成が subprocess を起動した [恒真ゲート]

- 事象: `site_policy.heavy_work_refusal()` へキュー状態の診断を織り込んだ結果、拒否文を作る
  過程で `subprocess.run(["qstat", "-Q"])` が走った。`test_build_site_gate.py` の 4 node が
  固定していた「gate は subprocess を 1 つも起動する前に拒否する」を破り、受入全走で赤になった。
- 根本原因: 診断を「拒否を報告する場所」ではなく「拒否を判定する場所」へ入れた。深い gate
  (`buildcache._run` 等) から呼ばれる純関数に I/O を足したため、gate の副作用ゼロ性が壊れた。
- 恒久対応: `heavy_work_refusal()` は純粋に戻し、キュー診断は呼び出し側の最上位
  (`run_tests.py` / `check_ai_provenance.py`) と `python3 -m orchestrator.campaign.queue_state`
  でだけ合成する ({{D:login-headroom-admission}} 決定 4)。
- 再発検知: `heavy_work_refusal()` が `subprocess` を一切起動しないことを固定するテスト
  (`subprocess.run` を例外送出でパッチして到達しないことを assert する)。

### {{F:clean-tree-precondition-kills-normal-work}}. 「tree が clean なら」の条件が開発の通常状態を殺した [手順漏れ]

- 事象: 「cap 到達後の自動 fallback は working tree と submodule が clean のときだけ」という
  裁定をそのまま実装した結果、**未コミットの変更がある通常の開発状態で必ず fallback が止まり**、
  rc=16 で終了するようになった。変異 harness の本走が M1 で停止して顕在化した。
- 根本原因: 裁定の意図は「local 試行が書き散らした状態のまま計算ノードで再実行しない」で
  あったのに、実装条件を「tree が clean か」という**絶対状態**にした。守りたかったのは
  **相対変化**である。開発中の tree はほぼ常に dirty なので、絶対状態の条件は常に偽になる。
- 恒久対応: local 試行の**前後で tree と submodule の指紋を比較**し、変化していなければ
  fallback する ({{D:login-headroom-admission}} 決定 9)。指紋取得に失敗したら安全側へ倒す。
- 再発検知: 「最初から dirty な tree で、local 試行が何も変えなければ fallback する」を固定する
  回帰テスト。

### {{F:new-behavior-broke-existing-tool-contract}}. 実行場所を可変にして既存 tool の前提を壊した [ドリフト]

- 事象: `tools/mutation_harness.py --runner-mode dispatch` は runner の stdout に
  `[Pegasus dispatch] receipt を … へ保存しました (child rc=…)` が現れる前提で計算ノード側の
  stdout を集める。`run_tests.py` が余裕のあるときに local 実行するようになったため、この行が
  出なくなり、変異 matrix が baseline から `PARSE_ERROR` になった。
- 根本原因: 「常に dispatch する」という**暗黙の契約に依存した consumer** を棚卸ししないまま、
  entry point の挙動を条件付きへ変えた。契約は runner の stdout 形式として存在していたが、
  どの docs にも「dispatch されることに依存する consumer」として記録されていなかった。
- 恒久対応: 実行場所を確定させる `--force-dispatch` を設け、harness 側がこれを明示する
  ({{D:login-headroom-admission}} 決定 10)。
- 再発検知: 強制指定時に `grant_budget` / `dispatch_possible` が呼ばれないことと、
  preflight 順序・task_run の exactly-once が保たれることを固定するテスト。
