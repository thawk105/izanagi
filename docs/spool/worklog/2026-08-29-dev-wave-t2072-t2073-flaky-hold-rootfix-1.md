---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-29
wave: dev-wave-t2072-t2073-flaky-hold-rootfix
seq: 1
title: [T-2072][T-2073] F273 の空 stdout 経路を実測で再現し、hold 登録・根本修理・撤去を 1 wave で閉じた (code + tests、branch worktree-dev-wave-t2072-t2073-flaky-hold-rootfix、変異 3/3 KILLED・旧版 2/2 SURVIVED)
---

## 本文

- ユーザー裁定は 5 件。(1) hold は exact node 1 件だけで他 node・timeout・失敗条件を変えない、
  (2) `expected_nodes` は ASCII の parametrize id だけ、(3) 既存の受入 gate を緩めない、
  (4) 負荷仮説を原因確定として先取りせず、空になる経路を実測で特定してから直す、
  (5) hold を外すのは根本修理が検証を通ってから。
- T-2072 の前提は満たされていた。F273 の 2026-08-28 再発が canonical へ fold 済みで、
  registry validator が要求する exact function 名と failure signature が evidence 節にあった。
  前 wave (1074) を止めた fail-closed 条件は解消していた。
- 空 stdout の経路を制御実験で再現した。同一 receipt の `actuals.wall_clock_s` だけを 7 点
  変えたところ、3.0 秒までは rc=0 で 202 byte の JSON、3.001 秒からは rc=2 で stdout 0 byte、
  stderr は `NG: receipt truth table が不正` だった。閾値は
  `limits.wall_clock_admission_bound_s` = 3.0 ちょうど。
- 時間の内訳 (計算ノード、無負荷): attempt 0.211179493 秒、launcher プロセス全体 0.680921272 秒、
  差 (準備 + 後始末) 0.469741779 秒 = 全体の 69%。checker は `schema_version` が 4 / 5 の
  ときだけ準備・後始末を引くため、v1 / v2 / v3 では全体時間が 3 秒上限と比べられていた。
- 実受入負荷下の内訳を別 wave の failure archive から得た (2026-08-26、bnode033、v4 receipt)。
  準備 1.926402881 秒、後始末 0.282475858 秒、全体 5.289560073 秒で、3 秒上限を実際に超えていた。
- **原因は「確定」ではなく「再現」と書く。** T-1958 の赤の junit は残っていて stdout が
  空だったことは確定するが、`checked.stderr` と当時の receipt は残っていない。
  `NG: receipt truth table が不正` は複数述語が共有する最終例外である。当該 node の junit の
  所要は 5.368 秒で、`acceptance_duration_ledger.json` の公称 1.3 秒の 4.1 倍。上記 archive の
  減速率と一致するが、これは状況証拠にとどまる。
- 段 2 プランは「合成 receipt の `wall_clock_s` を attempt 合計へ射影する」案だったが、
  段 3 の敵対相談 2 本が独立に否定した。レンズ A は「測定値を書き換えると v1〜v3 が宣言する
  `wall_clock_scope` の意味と食い違い、fixture pipeline の入力写像が変わる」、レンズ B は
  「attempt 自身の実時間が残るので閉じていない」を real で挙げた。親は射影案を不採用にし、
  測定値を一切書き換えず露出 3 関数の fixture 上限を上げるだけの形へ差し替えた。これで
  準備・後始末・attempt の全項が同時に非拘束になり、律速は全 node 共通の 10 秒
  subprocess watchdog だけになる。
- 段 3 は親 brief の誤りも 2 件挙げ、両方を裁定で訂正した。(1) 「commit を registry のみに
  限定する」は contract test が row 数・順序・digest を exact pin するため成立しない、
  (2) 「実測で原因特定」は証拠を越えている。
- **hold の撤去も実装面であり、親の `git revert` では land できない。** 親が revert で作った
  撤去 commit を `check_ai_provenance.py` が「実装面に Codex role=author がない」で拒否した。
  当該 commit を取り消し、Codex `role=author` に撤去を書かせ直した。撤去後の両 file は
  hold 登録 commit の親と byte 一致する。
- 変異走行は環境要因で 2 回中断した。1 回目は `DispatchError: queue-wait-timeout`
  (receipt の分類は `infra`、当時 gen_S は待ち 20 本・保留 24 本)。2 回目は wrapper の rc=125 で、
  共有 checkout の untracked が並行 wave によって走行中に変化したため。`--runner-mode local` は
  login node で禁止されているため dispatch を維持し、独立 clone を `--source-repo` へ渡して
  観測 root を共有 checkout から外して解決した。
- 子は Codex `gpt-5.6-sol` / xhigh で plan 1 本、敵対相談 2 本、実装 3 本 (hold / rootfix / 撤去)、
  完成差分レビュー 2 本。実装子 3 本はいずれも Pegasus の queue preflight 拒否により pytest を
  実走できず、規約どおり「実装済み・未実走」と申告した。実走はすべて親が行った。
- 段 6 レビューの must-fix 2 件はいずれもレビュー時点の中間状態への指摘 (hold がまだ残っている、
  F273 の記録がまだ無い) で、実装そのものへの must-fix は 0 件だった。レビュー子へ渡す差分が
  commit 列の途中状態であることを prompt に書いていなかったのが原因である。

## 次の一手差分

### 完了

- [T-2072] F273 再発 node を exact node で hold registry へ登録した。
  remaining: none
  base: 98a08bdcb461f43d271624c568f0b1683d489ccf8e01db454cf221a07981c487
- [T-2073] 空 stdout の経路を実測で再現し、根本修理を検証してから hold を撤去して
  当該 node を受入母集団へ戻した。
  remaining: none
  base: c5b25f6586b393e85a922cc92a5955bb639123ef64dacdc45f3bcfdc58f8d2a8
