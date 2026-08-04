結論は **NO-GO** です。原所見 12 件は closed 11 / partial 1 ですが、fix 起因の must-fix 回帰 2 件と、変異検証の blocker 1 件があります。

## 所見対応表

| 所見 | 判定 | fix 後の実コード照合 |
|---|---|---|
| reviewA-1 resolve 前 walk の早期終了 | **closed** | `..` は resolve より前に拒否されています（[layout.py:307](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:307)）。raw walk が missing で break しても、resolve 後に両 suffix を再 walk します（[layout.py:318](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:318)、[layout.py:321](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:321)）。既存 resolved base の directory 型も検査済みです（[layout.py:328](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:328)）。 |
| reviewA-2 8c suffix 未検査 | **closed** | `exploration/campaigns` と `exploration/autonomous-trials` の双方が resolve 前後の対象です（[layout.py:311](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:311)、[layout.py:315](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:315)、[layout.py:321](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:321)）。 |
| reviewA-3 二重 module identity の pin 分裂 | **closed** | state は `sys.__dict__.setdefault()` の process singleton です（[layout.py:226](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:226)）。両 import 順で module object は別、state は同一、両 module の reload 後も同一であることを軽量 probe でも確認しました。 |
| reviewA-4 compare-and-set の競合 | **closed** | env 読取、admission、比較、pin は同じ lock 区間内です（[layout.py:292](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:292)、[layout.py:293](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:293)、[layout.py:342](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:342)）。reset も同じ lock を取ります（[layout.py:233](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:233)）。reset は既返却 root の利用終了までは待ちませんが、production caller はなくテスト境界だけなので原所見の製品競合は閉じています。 |
| reviewA-5 `ensure()` を迂回する materializer | **partial** | `append/log`、`write_lock`、`acquire_lock_atomic` は gate 済みです（[wal.py:310](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/wal.py:310)、[wal.py:782](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/wal.py:782)、[wal.py:807](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/wal.py:807)）。しかし公開 `repair_truncated_tail()` は gate なしで receipt を `O_CREAT` し WAL を truncate します（[wal.py:430](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/wal.py:430)、[wal.py:469](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/wal.py:469)、[wal.py:507](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/wal.py:507)）。`ident.ensure_resumable_wal()` から到達します（[ident.py:185](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/ident.py:185)）。また公開 `ensure_exploration_namespace()` 自体も直接 directory/marker を作れます（[layout.py:369](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:369)、[layout.py:379](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:379)）。通常 production caller は手前で gate 済みですが、公開 API 契約としては残っています。 |
| reviewA-6 8c legacy default bytes | **closed** | env 未設定分岐は旧式と同じ `ROOT / "output" / "exploration" / "autonomous-trials" / trial_id` に戻っています（[p3_autonomous_workload_trial.py:1767](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/p3_autonomous_workload_trial.py:1767)）。ただし下記 new-2 の別回帰があります。 |
| reviewA-7 `os.geteuid` global mutation | **closed** | layout-local seam（[layout.py:239](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:239)）だけをテストが差し替えています（[test_campaign.py:3725](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/tests/test_campaign.py:3725)）。 |
| reviewB-1 二重 identity の process pin | **closed** | reviewA-3 と同じ。alias テストも state object の同一性と drift 拒否を固定しています（[test_campaign.py:3774](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/tests/test_campaign.py:3774)）。 |
| reviewB-2 8c default の文字列互換 | **closed** | reviewA-6 と同じ。旧 `ROOT/output` 式と byte 同一です。 |
| reviewB-3 F98 WAL replay 契約 | **closed** | fake evaluator は同じ `build_attempt_id` の receiptless `build_start → abort` を書きます（[test_dev_wave_land.py:2733](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/tests/test_dev_wave_land.py:2733)）。これは pre-build abort の topology 契約（[wal.py:694](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/wal.py:694)）と整合し、policy 付き replay 成功も固定しています（[test_dev_wave_land.py:2775](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/tests/test_dev_wave_land.py:2775)）。 |
| reviewB-4 拒否診断 | **closed** | env 名、絶対 path、job 専用、base 形式を含みます（[layout.py:362](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:362)）。ただし official へ誤適用された場合は復旧不能な案内になります（new-1）。 |
| reviewB-5 `sys.path` 復元 | **closed** | import scope がリスト全体を保存・復元します（[test_dev_wave_land.py:75](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/tests/test_dev_wave_land.py:75)）。 |

## new 所見

### new-1. WAL gate が official campaign を過剰拒否する

- 種別: scope 回帰・受理集合の承認外縮小
- 深刻度: **高・must-fix**
- file:line: [layout.py:218](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:218)、[loop.py:114](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/loop.py:114)、[wal.py:310](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/wal.py:310)、[wal.py:807](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/wal.py:807)
- 壊れ方: WAL gate は layout 種別を見ないため、worktree 内の正当な official `CampaignLayout` も拒否します。`CampaignLayout.ensure()` は先に directory を作るため、new official campaign は dirt を残して identity lock 作成で停止します。official s6/s8a sweep（[s6_sort_sweep.py:240](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/s6_sort_sweep.py:240)、[s8a_trigger_sweep.py:341](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/s8a_trigger_sweep.py:341)）と s8b oracle（[s8b_oracle_driver.py:997](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/s8b_oracle_driver.py:997)、[s8b_oracle_driver.py:1159](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/s8b_oracle_driver.py:1159)）も同じ影響を受けます。診断が示す exploration env は official root を変更しないため復旧策にもなりません。
- 成果物影響: official WAL・campaign.lock・oracle proof-chain 材料を生成できず、途中作成 directory により wave clean も失います。
- grep 結果: `.claude/worktrees` / `.codex/worktrees` 様 path と campaign/WAL を組み合わせる既存テストは、新設された exploration 負例だけです（[test_campaign.py:3895](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/tests/test_campaign.py:3895)、[test_dev_wave_land.py:2811](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/tests/test_dev_wave_land.py:2811)）。official 正例はありません。
- 修正方向: WAL が layout の materialization policy を呼ぶ形にし、official は no-op、exploration だけ container gate を適用する。二重 module identity に依存する `isinstance` ではなく、両 layout class の明示 method/property にする。official-in-container 正例を追加する。

### new-2. 8c が lock 外で env 存在判定し、pin を迂回する

- 種別: root drift・TOCTOU
- 深刻度: **高・must-fix**
- file:line: [p3_autonomous_workload_trial.py:1762](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/p3_autonomous_workload_trial.py:1762)、[layout.py:292](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:292)
- 壊れ方: 8c は singleton transaction の外で `ENV in os.environ` を判定します。root A を pin 後に env を削除して同一 process で `main()` を再実行すると、resolver を呼ばず legacy root B を受理します。また存在判定と resolver の env 読取の間で変更されると、判定時と異なる branch/root が使われます。現テストは env 削除前に pin を reset するため捕捉しません（[test_campaign.py:3875](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/tests/test_campaign.py:3875)）。
- 成果物影響: 同一 process の attempts.jsonl、raw、report.json が外部 root と legacy repo root に分裂します。
- 修正方向: caller-specific legacy default を resolver に渡し、`--run-root` 省略時は常に resolver を呼ぶ。env 有無の決定、既存 pin 検査、返却値決定を一つの lock transaction にする。reset なしの「A pin → env 削除 → 2 回目 main 拒否」テストを追加する。

### new-3. M1〜M10 は現状のままでは単一理由 matrix にならない

- 種別: 変異検出力・受入証拠
- 深刻度: **中・統合前 blocker**
- file:line: [test_campaign.py:3613](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/tests/test_campaign.py:3613)、[test_campaign.py:3664](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/tests/test_campaign.py:3664)、[test_campaign.py:3930](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/tests/test_campaign.py:3930)
- 壊れ方: M8 は post-resolve walk を除いても、現 fixture の symlink は pre-walk、`..` は resolve 前拒否で止まるため赤になりません。M5 は pre/post の二重 anchor 化で登録文言が非一意です。M9 も WAL 内に独立 call site が 3 個あり、helper 自体を無効化すると ensure/8c 負例まで巻き込みます。さらに M1 は優先順位テストだけでなく F98 正例と 8c env テストにも静的に到達します。
- 成果物影響: mutation ledger に「M1〜M10 を一理由で kill」と記録できず、段6の受入証拠が成立しません。
- 修正方向: M8 用に raw walk 後・resolve 前に suffix が出現する制御可能 fixture/seamを追加する。M5 を pre-resolve walk、M8 を post-resolve walkへ明確に再 anchor する。M9 は三つの WAL call を累積変異として一意に指定し、`repair_truncated_tail` も別変異・テストに含める。

## 変異 M1〜M10 の静的判定

| 変異 | 静的 kill | 「対応テスト1本だけ」判定 |
|---|---|---|
| M1 | 優先順位テストで kill | **不成立**。8c env と F98 外部正例も失敗し得る |
| M2 | 明示引数 assertion で kill | 単一理由だが M1 と同一 test node |
| M3 | 空文字入力で kill | 単一理由だが M3/M4/M5 共用 node |
| M4 | repo ancestor 入力で kill | 同上 |
| M5 | anchor 次第 | **不成立**。pre/post のどちらを除くか非一意。suffix 正例は反対側に mask される |
| M6 | `ExplorationCampaignLayout.ensure()` call 除去で F98 負例が kill | **成立** |
| M7 | 8c env run_root assertion で kill | 単一理由だが M10/8c gate と共用 node |
| M8 | kill する fixture なし | **不成立・SURVIVE 見込み** |
| M9 | 三 call の累積除去なら WAL test で kill | **現状不成立**。単一 anchor でなく、repair route も証明外 |
| M10 | legacy-root assertion で kill | 単一理由だが M7 と共用 node |

pytest・変異は指示どおり未実走です。`git diff --check` は通過し、import 順/reload probe だけを軽量実行しました。

## 総括

- 対応表集計: **closed 11 / partial 1 / regressed 0**
- new 所見数: **3**
- 統合可否: **NO-GO — F-5 の残存 materializer、official campaign 過剰拒否、8c pin 迂回、M8 を含む変異証拠不成立を閉じるまで統合不可です。**