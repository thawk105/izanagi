静的照合のみ（pytestは未実行）です。

- [real] 実測根拠が過大です。briefは `stage1-brief.md:13-14` で「7時間・実テスト8分44秒・98%超」を引用しますが、対象READMEは `README.md:132-136` で queue timeout と15以上の並行waveを示すだけです。別の実測READMEでは claim競合32〜74分、queue待ち38〜806秒、pytest207〜283秒です（`output/insights/2026-08-20_t870-acceptance-lease-timing/README.md:31-60`）。lease競合は実在しますが、98%という定量根拠は未確認です。

- [real] 案1はD239の目的とD270を実質的に変更します。D239はclaim取得者だけが受入全走を行う設計です（`docs/decisions.md:11174-11187`）。D270も「claim→main再取得→merge→再検査→受入」を明示しています（`docs/decisions.md:12433-12456`）。planはこれをmerge・受入後claimへ反転します（`stage2-plan-output.md:70-88`）。15 waveが同じmainを試験すれば、最初にlandしたwave以外は全量再受入になり、D239が防いでいた受入投資の廃棄を再導入します。

- [unclear] 総wall-clockが改善するかは立証されていません。試験を並列化できればlease待ちは減りますが、既にcompute queueも混雑しています（`README.md:132-157`）。D432のlock保持時間はmedian 6秒、p99 18秒、max145秒で、15 waveが同時到達すると単純計算でもp99級の直列尾部は14×18=252秒となり、180秒capを超え得ます（`docs/decisions.md:17972-17989`）。D432自身もprovenance監査の同時流入を最大13×480秒として未解決にしています（`docs/decisions.md:18003-18007`）。

- [real] `lock-busy`時にleaseを保持したままになる現行契約と、planの「fresh contextへ返しleaseを保持しない」が衝突します。`lock-busy` は `retryable_same_request=True` です（`tools/dev_wave_land.py:3067-3086`）。land側は `release_safe and not retryable_same_request` の場合だけreleaseするため、通常はleaseをretainedにします（`tools/dev_wave_land.py:3629-3668`、`docs/decisions.md:19483-19503`）。planの `stage2-plan-output.md:62,76` の方針を実現するには、D469の裁定・release条件・親側の明示releaseを別途変更する必要があります。

- [real] FIFOの公平性が変質します。D253のFIFOは待ち札作成時点の到着順で、後着が先着を追い越さないことだけを保証します（`docs/decisions.md:11616-11621,11664-11670`）。claimをテスト後へ移すと、重いwaveは軽いwaveに恒常的に先行され得ます（`stage2-plan-output.md:88-89`）。D253が明示的に禁止しているとは言えませんが、D239/D270が想定した「受入を始めたい順」とは異なるため、保存されたFIFOとは報告できず、裁定が必要です。

- [refuted] 案1がD619の数値変更を必須にする、という懸念は当たりません。planはTTL=2400、queue timeout=900、grace=300、walltime=3600を変更していません（`stage2-plan-output.md:143`、`docs/decisions.md:24829-24838`）。

- [real] ただしTTLの運用意味は変わります。現行実測はTTLが実際のacquired時点から始まると説明しています（`output/insights/2026-08-20_t870-acceptance-lease-timing/README.md:43-51`）。案1では重いmerge・受入中はTTL時計が動かず、claim後の短いlandだけを覆います。これは数値変更ではありませんが、D253の「TTL境界・acquired意味論不変」（`docs/decisions.md:11649-11651`）やD469の「lease TTLの意味論不変」（`docs/decisions.md:19502-19503`）に対する明示的な設計変更です。

- [real] `--max-wait-seconds` の意味も暗黙に変わります。deadlineは `run_acceptance()`入口で開始します（`tools/dev_wave_wait.py:4551-4569`）。現行ではclaim待ちループがdeadlineを使い、launcher実行はその対象外です（`tools/dev_wave_wait.py:3073-3086`、`output/insights/2026-08-20_t870-acceptance-lease-timing/README.md:81-83`）。claimを受入後へ移すと、同じdeadlineがmerge・監査・テスト後のclaimに適用され、成功した全量テストが最後にclaim-timeoutになる経路が生じます。deadline再設定は別の契約変更です。

- [real] D402の性能改善ゲートを満たしていません。案1は同時実行数・負荷・兄弟worktree数と、main/MERGE_HEAD/indexの観測時点を変えます。D402はそのような入力文脈変更を、同値性の実測なしに採用しないと定めています（`docs/decisions.md:16889-16919`）。planはprovenance順序には触れますが、受入判定全体の同値性を示していません（`stage2-plan-output.md:119-131`）。

- [real] planのstrict `locked_main == tested_main` は現行D254/D432のaudited closureを狭めます。現コードは `current in audited` かつ祖先関係なら許可しています（`tools/dev_wave_land.py:2106-2117`）。D432もD254の二相化・receipt束縛を維持するとしています（`docs/decisions.md:17960-17965`）。案1のstrict check（`stage2-plan-output.md:76`）を無条件に入れると、既存の監査済みmain進行やalready-landed経路まで拒否し得ます。

- [refuted] reward-hackとして、部分テスト・差分テスト・古いreceipt再利用を明示的に導入している箇所はありません。briefは全量再実行を要求し（`stage1-brief.md:48-56`）、planもrace時のtemp receipt破棄と全量再受入を指定しています（`stage2-plan-output.md:74-85,145`）。

- [unclear] ただしraceのend-to-end retry契約は未完成です。現行のretryは主にno-verdict向けです（`tools/dev_wave_wait.py:4440-4596`）。land側のstale-main/lock-busyはreceipt publish後または別processで起こり得ます（`tools/dev_wave_land.py:3127-3226`）。最終receiptをどう退避・無効化して、どの親がfresh contextから全量再受入するかがplanにありません。未定義のままだと、再試行不能か、誤って古いreceiptを再利用する経路になります。

- [real] release配線も実効性の阻害要因です。land helperは `IZANAGI_WAVE_LEASE_DIR` が無ければrenew/releaseできません（`tools/dev_wave_land.py:3596-3618,3629-3689`）。実測でも現行land invocationが `lease-dir-required` でrelease不可でした（`output/insights/2026-08-20_t870-acceptance-lease-timing/README.md:120-128`）。案1の変更対象にはこの呼出し元・runbook配線が明記されておらず、leaseが残れば混雑を悪化させます。

- [real] briefの引用にも訂正が必要です。receiptは「26 field」ではなく27 fieldです（`stage1-brief.md:36-39`、`stage2-plan-output.md:13`、`tools/acceptance_launcher.py:365-397`）。また「renewはPython importでのみ利用可能」は、現行land helperがPython importで呼んでいるため不正確です（`stage1-brief.md:22-23`、`tools/dev_wave_land.py:3602-3618`）。D469後は「親が明示release」という説明も更新済みです（`stage2-plan-output.md:21-25`）。

- [refuted] planが引用するD239、D253、D299、D402、D432、D469、D595、D619はすべて実在し、見出しと主要内容は一致します（各々 `docs/decisions.md:11172,11614,13848,16887,17940,19481,23971,24827`）。ただしD432の監査増幅リスクと、D270の直接的な反対契約をplanは十分に扱っていません。

## 総括

(i) 推奨成果物は「設計提案のみ」です。案1はコード上の小変更ではなく、D239/D270の受入境界、D253のFIFO到着点、D402の入力文脈、D469のrelease条件を同時に変更します。さらに、実測されたqueue混雑下でwall-clockが改善する証拠がなく、lock-busy時のlease保持問題も未解決です。即時実装は勧めません。

(ii) 最も深刻な所見トップ3:

1. [real] `lock-busy` がD469によりlease retainedとなり、案1の「fresh context・資源なし」と正反対になる。
2. [real] D239/D270のclaim先行設計を反転し、最初のland後に他waveの全量受入を大量廃棄・再実行する。
3. [unclear] lease待ちがqueue/D128へ移るだけか、実際にwall-clockが改善するかを示す定量モデル・実測がない。