## 1. 所見

1. **must-fix — 正常な trace を集計が拒否する。** [driver:673](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/orchestrator/campaign/vhash_cicada_hot_block.py:673) は巡回 0 の verdict を `indeterminate` に限定するが、判定器は整合性が良好で巡回 0 なら `serializable`、rc 0 を返す（[model:555](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/orchestrator/verifier/model.py:555)、[cli:105](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/orchestrator/verifier/cli.py:105)）。テストも実物と異なる `rc=0, indeterminate` を正常例にしている（[test:46](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/orchestrator/tests/test_vhash_cicada_hot_block.py:46)）。**成果物への影響:** 正常な本走から集計・図を作れず、受入が止まる。**修正案:** `rc=0 / serializable / cycles=0` を受け、rc・verdict・巡回数の対応を実際の判定器契約で検査する。

2. **must-fix — COUNT だけ測定時間が裁定と異なる。** 共通 argv は `extime=3`、trace のみ 1 秒という裁定に対し、[driver:374](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/orchestrator/campaign/vhash_cicada_hot_block.py:374) は COUNT も 1 秒にする。**成果物への影響:** 版探索・snapshot 遅れ・書き込み費用の診断値が、併記する 3 秒の性能 cell と異なる走行条件の値になる。**修正案:** `extime=1` は trace／broken に限り、COUNT は perf と同じ 3 秒にする。

3. **must-fix — 見積りで build 時間を二重計上する。** `smoke_seconds` は build を含む（[driver:834](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/orchestrator/campaign/vhash_cicada_hot_block.py:834)、[driver:881](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/orchestrator/campaign/vhash_cicada_hot_block.py:881)）のに、[driver:181](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/orchestrator/campaign/vhash_cicada_hot_block.py:181) は `smoke_wall + build` と加算する。**成果物への影響:** 7,200 node 秒の境界で不要な縮小または投入停止が起こり、図に載る cell・K・round が変わる。**修正案:** smoke 内の build を一度だけ数え、裁定 §4 の式と境界例で照合する。

4. **should — B1 は stock と同じ版でも `changed` と記録し得る。** [B1 patch:48](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/patches/broken-cicada-vhash-stale-hot.patch:48) は選択版 `ptr[i]` の状態を調べない。これが ABORTED なら、stock の第 2 段も次の確定版 `ptr[i+1]` へ進む（pin `cc/cicada/transaction.cc:108–118`）。**成果物への影響:** 壊しの `changed` 件数と発火説明が過大になり、帰属の解釈を誤らせる。**修正案:** 元の選択版が確定・非削除で、返す版と異なる場合だけ変更事象にする。

5. **should — COUNT の worker 配列は cache line ごとに分離されていない。** [patch:100](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/patches/cicada-vhash-hot-block-variant.patch:100)、[patch:138](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/patches/cicada-vhash-hot-block-variant.patch:138)。**成果物への影響:** 診断 build の競合・cycle 値に false sharing が混ざり、書き込み側費用の説明が歪み得る。**修正案:** worker 要素を cache line に整列し、配列 stride も cache line の倍数にする。性能 build には影響しない。

## 2. 裁定 §2〜§5 への適合表

| 項目 | 判定 | 根拠・留保 |
|---|---|---|
| §2.1 hot の物理先頭 K 件、初期化、writer／GC の順序 | 適合 | [patch:18](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/patches/cicada-vhash-hot-block-variant.patch:18)、[patch:295](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/patches/cicada-vhash-hot-block-variant.patch:295)、[patch:373](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/patches/cicada-vhash-hot-block-variant.patch:373) を静的確認。 |
| §2.1 seqlock の指定 memory order、reader の stock 接続 | 適合 | writer・reader の順序は [patch:25](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/patches/cicada-vhash-hot-block-variant.patch:25)、[patch:238](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/patches/cicada-vhash-hot-block-variant.patch:238) と一致。実機の寿命安全性は未検査。 |
| §2.1 WL の初回抽選と retry 維持 | 適合 | [patch:187](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/patches/cicada-vhash-hot-block-variant.patch:187)、[patch:407](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/patches/cicada-vhash-hot-block-variant.patch:407)。 |
| §2.2 B1／B2 の予測と事象書式 | 一部不適合 | B2 の分岐と書式は合う。B1 の `changed` に所見 4。 |
| §2.3 17 binary、同一 job・round・cell の対、hash、inert | 適合 | [driver:98](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/orchestrator/campaign/vhash_cicada_hot_block.py:98)、[driver:275](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/orchestrator/campaign/vhash_cicada_hot_block.py:275)、[driver:342](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/orchestrator/campaign/vhash_cicada_hot_block.py:342)、[driver:638](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/orchestrator/campaign/vhash_cicada_hot_block.py:638)。 |
| §2.3 COUNT 条件 | 不適合 | 所見 2。 |
| §3 巡回 0 の受入、壊し帰属 | 不適合 | 正常 trace を拒否する所見 1。 |
| §4 7,200 閾値と縮小順 | 一部不適合 | 閾値と順序は合うが、合計は所見 3。 |
| §5 M1〜M6 の実効性 | 未検査 | テスト本文は確認したが、指定どおり実行していない。 |

## 3. 実装子報告の主張の検算

- **成立:** U1 の「Install を hot 書き区間内で行い、GC は trim→切断→再利用」は patch と一致。K>0 の先頭からの再探索も、precheck 後に hot lock 内で現在の物理位置を求めるため、この点単独の反例は**不成立**。RMW／DELETE／`WRITE_LATEST_ONLY` は先頭 CAS と位置 0 を選ぶ。`install_count` は成功数ではなく試行数で、driver はそれを commit 分母には使っていない（[patch:356](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/patches/cicada-vhash-hot-block-variant.patch:356)、[driver:401](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/orchestrator/campaign/vhash_cicada_hot_block.py:401)）。
- **成立:** U2f の事象書式・rw witness の `from`、key、`u_ver` の照合は実物の構造と一致（[driver:491](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/orchestrator/campaign/vhash_cicada_hot_block.py:491)、[report:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/orchestrator/verifier/report.py:17)）。U3 の正確な `#if MACRO` witness 数 12／20／5 も登録と一致し、K=2/4/8 の meaning 未確立は raw-measurement の受理述語だけでは build を止めない。
- **不成立:** U2 の「trace を集計し図へ渡せる」という主張は、所見 1 により正常な判定器出力で成立しない。見積りが裁定 §4 どおりという主張も所見 3 により不成立。U1 の実走・構文確認の **rc 自体は本レビューでは再実行しておらず未検算**。

## 総括

静的レビューでは、C++ の hot 更新・reader 接続に確定的な正しさ反例は見つからなかった。受入を実際に妨げるのは正常 trace を拒否する集計条件である。COUNT の走行時間と計算見積りも裁定から外れ、診断値と実験範囲を変える。テスト・ビルド・実機走行は依頼どおり実行していない。