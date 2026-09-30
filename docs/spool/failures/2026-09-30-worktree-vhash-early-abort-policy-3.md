---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-30
wave: worktree-vhash-early-abort-policy
seq: 3
---

## 再発

### F273

- **再発: 2026-09-30** — VHash md_31 で、親が fix1 commit 後の full-history provenance 監査 (計算ノードへ自動 dispatch する) と焦点走 2 を同一 worktree からほぼ同時に投入し、焦点走 2 の qsub 中の pending orphan hold を監査が検知して rc=16 (`child_started=false`、`reason=orphan-hold`) になった (`DW-C00` の「同一 worktree の dispatch は全種直列」違反、親の操作ミス)。焦点走 2 は request 37897 で走り切り、hold はその終端で自然に解除、監査は単独の再投入 (37907) で rc=0。qdel も hold の手動削除もしていない。既存の恒久対応に直すべき新事実はない。

### F722

- **再発: 2026-09-30** — VHash md_31 で、実装子が推測で組んだ fixture と login のテスト・段 6 のレビュー 2 本では捕まらない欠陥が、実機で 1 巡に 1 件ずつ 3 件出た。smoke 1 で新 subcommand の起動枠が target-run の流れを写さず依存物 build を抜かし、条件 gate の前処理が `config.h` 無しで停止 (レビュー B は「起動枠の再記述」を nit として挙げていた)。smoke 2 で計器なし build の計数専用の変数が未使用になり `-Werror` で停止 (子の環境には gflags と生成 config.h が無く、構文検査が走らなかった)。検査 1 で repo 外起動器が hb の腕の GC V1 行 (`no_room` を持たない) にも `no_room` の分割照合を当てて落ちた。直した後、abort-run の順序を検査するテストを足し、変数と macro の組の表を子に出させた。md_21 の再発と同じく、新しく build・解析する経路は smoke を最初の fix 巡の前に出すのが最も安い。
