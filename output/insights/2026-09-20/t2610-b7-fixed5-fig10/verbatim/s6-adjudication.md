# 段 6 裁定 — レビュー A (過剰・削除) / B (正しさ境界・整合・実効性) の所見 (2026-09-20 08:08 JST)

レビュー対象 = wave tip `04ae82a1c` (実装 `35bfe1cfb` + 図・docs `04ae82a1c`)。A: must-fix 1 / should 3 / nit 1、NO-GO。B: must-fix 0 / should 3、GO。
両レビューとも値の照合 (30 標本・6 median・effects・floors・判定・caption・README・着地 hash) は全件一致。

| 所見 | 判定 | 採否 | 処置 |
|---|---|---|---|
| A-1 / B-2: `CAPTION_SCOPE` が稿を床値判定の出所から除外するが `RECORDED_JUDGMENT` は稿 §2.1 の転記 | real | 採用 (must-fix) | 生成器の `CAPTION_SCOPE` を「記録判定の転記元 + 限定・条件の言い方の出所。測定値・効果の一次権威ではない」へ。README「入力」の authority_scope 説明も同旨に。図は再生成 |
| A-2: caption の床の説明が session-median の CV・下限・同一性未証明を落とし、correctness の「workload argv 独立記録なし」も無い | real | 採用 (should) | 固定文 2 を「per-session medians … recorded as a lower bound; identity of binary, toolchain and node with this attempt is not established」に、固定文 6 に「the correctness workload argv was not independently recorded」を足す (稿 §4 項 3・12、certification `independent_observation_limits`) |
| A-3: `effect < -cv` の評価は「判定計算をコードに入れる」に当たる。述語照合と負例を削れ | partially refuted | 不採用 (検査は残す)、文言のみ採用 | 述語は判定の出所でなく転記の整合検査であり、D2162 が禁じる「追加 gate」(certification 経路の判定手順) ではない (B も同判断)。削ると転記誤りが図に出ても止まらない。README の「生成器は判定を作らない」を「判定の出所は稿の転記で、述語は整合検査にだけ使う」へ正確化 |
| A-4: README「区間推定を含めない」が描いている t95 CI と矛盾 | real | 採用 (docs) | 「効果・median・床値判定の区間推定を含めない (標本の t95 CI は標本の記述として描く)」へ |
| A-5: README 間の重複 | nit | 不採用 | fig9 と同じ構成。値・受理集合に影響なし。backlog にもしない |
| A 削除候補 `DF = 4` 未使用 | real | 採用 | caption の `(df 4)` を `(df {DF})` にして使う |
| B-1: 着地 closure が provenance の標本を raw / 稿の標本と結ばない | real | 採用 (should) | 着地 test に provenance `cells[].samples_tps` / `median_tps` と稿 §2.2 (`_document_values()`) の一致検査を足す (durable root 不要) |
| B-3: 境界 test (`effect == -floor` は退行なし、correctness 記録の `trace_enabled=False` は拒否) が無い | real | 採用 (should) | test 2 本追加。対応する変異 m13 (`<` → `<=`)、m14 (correctness `trace_enabled is True` 検査の恒真化) を fix 前に事前登録 |

fix は Codex 実装子 1 本 (unit worktree に fix branch、所有 = 生成器 + test)。docs (README 3 箇所) は親。図は親が再生成し README の hash 3 行を実値化。
fix 後: 焦点走 → 焦点再レビュー 1 本 (DW-O16) → 変異 (anchor 更新、login probe 再走 → dispatch 本走) → 受入。

## 追加の変異事前登録 (fix 前、DW-M01)

| id | category | 位置 | 期待 |
|---|---|---|---|
| m13-strict-to-nonstrict-predicate | negative | `computed = "regression" if effect < -cv else "no-regression"` の `<` を `<=` に | KILLED: 境界 test (`effect == -floor` → no-regression) |
| m14-drop-correctness-trace-enabled-check | negative | raw correctness 記録の `row["trace_enabled"] is True` を恒真化 | KILLED: correctness trace-disabled 拒否 test |

login probe (anchor `04ae82a1c`、fix 前) の観測: m0 SURVIVED、m1〜m12 KILLED (m1 = hash drift test 4 本、m9 / m10 / m11 = 2 本、他 = 1 本)。fix 後に anchor を更新して再 probe する。
