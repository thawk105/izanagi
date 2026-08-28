# T-1933 resume 2026-08-28 段1 brief

- scope: main 現物の `test_s8b_oracle_driver.py` t080 系、`test_s8b_floor_campaign.py`、両者の直接 fixture/helper だけを所有する。
- scope 外: duration ledger、runner、conftest、production、他の上位 file、T-1934 の残差、T-1938 の共通 helper 分離。
- 確定裁定: 前 wave の optional rules 注入案は棄却済みで、旧 plan/consult は流用しない。本項にユーザー裁定待ちはない。
- 禁止: 削除、skip/xfail/deselect、parametrize/case 縮小、assertion変更、正しさ判定の共有、独立 oracle の値源共有。
- 禁止: D104 が棄却した worker/session 跨ぎ T-080 base cache を再導入しない。
- 不変条件: 受理 nodeid の集合・順序・pytest argv・計算ノード条件を変更前後で一致させる。
- 不変条件: 変更前 baseline が `tools/run_tests.py --force-dispatch` で child-green になるまで段5へ進まない。
- 不変条件: 最大1原因だけを共有化し、live repo の再観測と独立 oracle の検出力を維持する。
- main `61b92342b` の duration ledger では全体最長が scope 外の 140 秒 node、scope 内最長が floor snapshot 79 秒、t080 最長が55秒である。
- (P1) T-1933 の「受入の最長」は現在も scope 内 node を意味し、有益な短縮余地が残る。親の provisional 裁定であり、全体最長のscope外化を含め攻撃対象とする。
- (P2) rules注入以外に、repo snapshot・fixture build の重複を正しさ値源を共有せず除ける境界がある。親の provisional 裁定であり、D104との衝突を含め攻撃対象とする。
- 段2/3: read-only Codex plan 1本と、correctness / effectiveness の敵対相談2本を fresh artifact で再実行する。
- 段5: 安全な共有境界と baseline green の両方を証明できた場合だけ、隔離 D95 Codex author 1本へ2 test file内の最小差分を渡す。
- 成果物: 採用時は test-only 最小差分、同一 argv の前後 timing、変異 matrix、関連検査、受入全走、spool記録、D95 commit。
- 成果物: 不成立または実益なしなら実装面0 byteで閉じ、理由とscope外の新最長を記録する。
- DW-G05: scope内79/55秒 nodeを短縮できれば受入 critical path候補を下げるが、scope外140秒が支配する限り全体最長値は変わらない。
- 実測環境: Pegasus login `pegasus02` から wrapperを必ず force-dispatchし、直接 pytest/build/性能走は行わない。
- freeze/oracle: 凍結 bytes・producer出力は変更しない。実 freezeを読む oracle testの検出力と受理集合を不変に保つ。

## dev-wave 改善候補

- 前回候補を継続観測: T-1934 の開始 inventory が既存 T-1933 owner を見落とした。段8で現行 occupancy 契約への統合要否を裁定する。
