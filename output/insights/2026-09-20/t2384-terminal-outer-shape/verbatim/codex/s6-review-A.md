## 所見一覧

| id | must-fix／should／nit | 対象 | 所見 | 放置時の成果物影響 1 行 |
|---|---|---|---|---|
| — | — | 実装・追加 test・事前登録 | 指摘事項なし | 裁定外の受理集合・reason・receipt の変化、変異帰属の誤りは確認されなかった。 |

## 各所見の根拠

以下、`C` は `orchestrator/campaign/reflux_formal_consumer.py`、`T` は `orchestrator/tests/test_reflux_formal_consumer.py`、`E` は `orchestrator/campaign/reflux_result_evidence.py` を指す。pytest・変異走は実行していない。

**1. 裁定との逐語一致**

- `C:1133` の helper は `s4-ruling.md` §2 のコードと改行・空白を含め一致。
- `C:1165` の呼出しも逐語一致し、`terminal = wal_records[-1]` の直後、`attempt` の前にある。
- patch は consumer 23 行、test 96 行の追加だけ。consumer から helper と呼出しを取り除いた全文は、`2579b4638^` と一致した。したがって `_wal_trigger`、`_wal_field`、既存判定式、reason code、import に変更はない。
- 両ファイルの worktree 実物は `2579b4638` と一致した。

**2. production の受理境界**

| producer | 根拠 | 新 gate |
|---|---|---|
| commit | `pipeline.py:2566`、`wal.py:415` の exact 5 key 化 | 通過 |
| prebuild abort | `pipeline.py:1775`。abort を emit して return | 通過 |
| 通常 abort | `pipeline.py:1917`。payload に reason／attempt を入れ、abort 後 return | 通過 |
| recovery abort | `wal.py:2426`。文字列 variant／env_tag、`time.time()`、dict payload。`:2627` で active attempt にだけ追記 | 通過 |

`wal.py:2355` は terminal を見た attempt を active 候補から除く。通常の終了経路と合わせ、対象 attempt の terminal 1 件という条件に整合する。

DW-O13 の exact 490/490、float ts 490/490 と矛盾しない。件数条件の実測根拠は attempt 世代の commit 16/16 までであり、abort の実測へ一般化していない。

これは**新しい外枠 gate の通過判定**である。prebuild／recovery abort 等が既存の reason／verify 条件も満たすという意味ではない。過剰拒否の実例は確認されなかった。

**3. 負例 12 node の判定順**

共通経路は次のとおり。

`T:468` の再ハッシュ・参照更新 → `E:1608` の resolver → `C:1466` の FC05C → FC06 → `C:1165` の新 gate。

resolver は records が非空の dict 列で、各 attempt が一致し、source bytes と一致することを確認する。canonical-list 経路の `E:1580` は `parse_line` を通さず、terminal の外枠を検査しない。変更された outer field は FC06 の入力でもない。

| node（`test_fc07_` 以下） | test 行 | 新 gate で最初に失敗する条件 |
|---|---:|---|
| `rejects_terminal_root_attempt_shadow` | 1682 | exact keys |
| `rejects_terminal_extra_root_key` | 1691 | exact keys |
| `rejects_terminal_missing_root_key[env_tag]` | 1699 | exact keys |
| `rejects_terminal_missing_root_key[ts]` | 1699 | exact keys |
| `rejects_terminal_missing_root_key[variant]` | 1699 | exact keys |
| `rejects_terminal_invalid_outer_type[ts-bool]` | 1711 | ts の exact type |
| `rejects_terminal_invalid_outer_type[ts-str]` | 1711 | ts の exact type |
| `rejects_terminal_invalid_outer_type[variant-int]` | 1711 | variant の exact type |
| `rejects_terminal_invalid_outer_type[env-tag-none]` | 1711 | env_tag の exact type |
| `rejects_payload_only_terminal_stage` | 1720 | exact keys |
| `rejects_duplicate_abort_terminals` | 1728 | terminal_count = 2 |
| `rejects_commit_before_abort_terminal` | 1735 | terminal_count = 2 |

root shadow では `T:475` が root attempt を正値にして `continue` するため、payload の異値は保存される。`E:1573` も root を優先するので attempt 混在では落ちず、新 gate に到達する。

ts／variant の欠落は JSON として有効。`env_tag=None` も JSON null として有効で、`reflux_origin_artifacts.py:33` が許容する。いずれも resolver を通る。

全例で trigger 自体は不変。追加 commit／abort は trigger family に該当しない。手前で落ちて新 gate を検査できない node は認められない。`T:688` は FC07 に加え、receipt／evidence-root 参照がともに `None` であることも検査する。

**4. 正例 2 node**

- `T:1752`：有限 float ts は `C:1143` を通る。fixture の abort payload は不変なので、`C:1175` 以降の stage、reason、verify、witness 検査を通り、後続検査後の `C:1503` で `P6Unavailable`。
- `T:1761`：中間 `build_start` は `kind` を持たず、stage も trigger ではないため、`C:985` の family 判定に影響しない。terminal_count にも入らず、末尾 abort の外枠・payload は不変。同じ abort 枝を通って `P6Unavailable`。

**5. 変異の帰属**

consumer 全文で各 `old` の出現回数を数え、M01〜M09 はすべて一意。M02 の二つの anchor も各 1 件だった。

| 変異 | 静的判定・帰属 |
|---|---|
| M01 | 等価。exact keys に root `stage` が必ずあり、`C:1095` はその値を返す。payload に異なる stage があっても参照されない。反例なし。 |
| M02 | gate 無効化で payload-only-stage が先へ進み、M5 が payload の abort を読む。残る payload 条件は正常なので `P6Unavailable` となり、負例の FC07 期待が失敗する。 |
| M03 | root shadow／extra key が通過する。shadow の attempt は既存 `_wal_field` でも正しい root 値となるため、後段では救済されない。 |
| M04 | bool ts が通過し、既存 abort 判定は ts を読まない。ts-bool が殺す。 |
| M05 | 重複 abort／先行 commit が通過する。既存 outcome 判定は末尾を読むため、両負例が殺す。 |
| M06 | 登録どおり 11 負例が殺す。payload-only-stage は既存 `terminal.get("stage")` が FC07 にするため殺さない。 |
| M07／M08 | variant-int／env-tag-none がそれぞれ通過し、既存 abort 判定は当該 outer field を読まないため殺される。 |
| M09 | float ts 正例が FC07 に変わり、`P6Unavailable` 期待が失敗する。 |

既存 FC05C 負例は trigger 側で停止し、既存 FC07 の reason／verify 負例は変更されない判定で停止する。旧 root-kind 負例も stage 判定で拒否されたまま。M03／M05／M06／M07／M08 の登録予測に、これら既存 test の失敗を新 test 固有の kill と取り違えたものは確認されなかった。完全集合と SURVIVED／KILLED の実測確定は予定された probe／final の責務として残る。

**6. 焦点走・fixture 回帰**

[focus1.log](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2384-terminal-outer-shape/focus/focus1.log:18) は collection 1016 items、`:35` は 1016 passed。ログ単体にはファイル集合がないが、`:10` が参照する [dispatch receipt](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2384-terminal-outer-shape/output/pegasus-dispatch/08b603691cbf531dca322b92e8ccbf88/receipt.json:50) の `request.args` は、裁定の 12 file と完全一致する。`result` は `bnode007`、child rc=0。

静的にも次を確認した。

- `reflux_origin_fixture_builder.py:395`：trigger＋exact abort の 2 record。terminal 1 件、整数 ts、正常な reason／verify。
- `test_trial_registry.py:1148`：独自 terminal は payload として組み込まれ、`:1218` 付近の commit 外枠は exact、float ts、attempt ごとに 1 件。
- `test_p3_autonomous_workload_trial.py:10725`：共有 fixture の source bytes／records を保ち、参照先を移設する。
- `test_reflux_campaign_issuer.py:1231` の二重 abort は `:1250` の `result_evidence_context=None` 経路。formal consumer の正例が新 gate で拒否される例ではない。

## 総括

must-fix 0 件、should 0 件、nit 0 件。最重要の修正要求なし。
裁定との逐語一致、負例 12 node／正例 2 node の到達先を静的に確認した。
12 file・1016 passed は親のログと dispatch receipt で確認した。
**GO（実装レビュー）。変異の実測完了・受入全走の完了を意味しない。**
