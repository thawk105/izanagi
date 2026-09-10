## real 1: calibration を 3 lock 同時に偽造できる

- **判定: real。**
- **反例:** 3 fixture 全てで `search_config.calibration.records` を `1000000` から `true` または `999999` へ変更し、inner と outer を再 canonical 化する。key 集合は不変で、3 系列の値も共通なので通る。
- **成果物影響:** provenance の calibration 値と Markdown の calibration record 数が偽造値へ変わる。
- **根拠:** calibration は key 集合だけを検査して型や固定値を検査せず dataclass 化する [b10_backoff_shape_sweep.py:3169](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:3169)。系列間では攻撃者がそろえた値同士を比較するだけである [b10_backoff_shape_sweep.py:3524](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:3524)。runtime が検査するのは `env_tag`、`clocks_per_us`、`threads` のみ [b10_backoff_shape_sweep.py:4357](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:4357)。出力は偽造された `calibration.as_dict()` と `records` を使う [b10_backoff_shape_sweep.py:4042](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:4042) [b10_backoff_shape_sweep.py:4082](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:4082)。
- 現テストは 1 系列だけを変えて系列間不一致を確認しており、同時改変を試していない [test_b10_backoff_shape_sweep.py:2728](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/tests/test_b10_backoff_shape_sweep.py:2728)。
- **最小修正:** 現物に記録された 10 field の exact literal と照合してから復元する。3 lock 全ての `records` または `sha256` を同時改変する負例を追加する。

## real 2: 別系列の実在 authority を交換して通せる

- **判定: real。**
- **反例:** `write-heavy.campaign.lock` の outer `authority` 全体を `balanced.campaign.lock` の authority に交換し、outer を再 canonical 化する。inner の write-heavy binding は変更しない。
- **成果物影響:** report は write-heavy の record/binding を保持したまま、`contract_loader_commit` を balanced の `c7ed5658...` と記録し、測定参照を矛盾させる。
- **根拠:** historical decoder は authority の schema と 24 path grammarを検査するだけである [campaign_lock.py:382](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/campaign_lock.py:382)。report 入口は渡された commit/blob 組の内部整合だけを検証し、workload や binding の analysis commit と結び付けない [b10_backoff_shape_sweep.py:3134](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:3134)。その commit はそのまま返却され [b10_backoff_shape_sweep.py:3214](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:3214)、provenance に書かれる [b10_backoff_shape_sweep.py:4033](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:4033)。両 authority は各 fixture の 1 行目に実在する。
- 現負例は存在しない `ffff...` commit と zero digest だけであり、有効な別系列 authority を試していない [test_b10_backoff_shape_sweep.py:2584](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/tests/test_b10_backoff_shape_sweep.py:2584)。
- **最小修正:** authority commit を workload 対応の `LEGACY_*_ANALYSIS_COMMIT` と exact 比較し、残る environment/activation 3 scalar も現物値へ固定する。authority 交換負例を追加する。

## real 3: `space_version` と `trial` の相関改変が通る

- **判定: real。**
- **反例:** 3 fixture 全てで `space_version` を `b10-backoff-shape/v999`、`trial` を `b10-backoff-shape-v999-9c59411476018d51` に変え、inner と outer を再 canonical 化する。
- **成果物影響:** report の measurement space が偽の `v999` へ変わる。
- **根拠:** `space_version` は stem しか固定せず、攻撃者が与えた suffix をそのまま `expected_trial` に使う [b10_backoff_shape_sweep.py:3181](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:3181)。全系列をそろえれば系列間比較も通る [b10_backoff_shape_sweep.py:3526](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:3526)。値は report へ出力される [b10_backoff_shape_sweep.py:4006](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:4006)。
- 現テストは `trial` 単独改変しか試していない [test_b10_backoff_shape_sweep.py:2620](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/tests/test_b10_backoff_shape_sweep.py:2620)。
- **最小修正:** historical `space_version` を exact `b10-backoff-shape/v2` に固定し、trial もその固定値から exact 導出する。両 field の同時改変負例を追加する。

## real 4: `search_config` の大半は削除または改変しても通る

- **判定: real。**
- **反例:** いずれかの fixture から `search_config.build_admission` を削除する、または `search_config.decision.alpha` を `1` に変え、inner と outer を再 canonical 化する。
- **成果物影響:** report 入口が現物とは異なる search configuration を受理し、lock の受理集合が拡大する。
- **根拠:** low-level decoder は `search_config` が dict であることしか要求しない [campaign_lock.py:304](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/campaign_lock.py:304)。report 入口が読むのは binding、spec、calibration、space、workload、path だけである [b10_backoff_shape_sweep.py:3145](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:3145)。fixture には `build_admission`、`decision`、`block_run_order`、`records`、`physical_residual` など 23 key があるが、その多くは無検査である [write-heavy.campaign.lock:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/tests/fixtures/b10_backoff_shape_locks/write-heavy.campaign.lock:1)。
- **最小修正:** exact 23-key 集合を要求し、spec/calibration/binding/module 値から導出できる重複 field を全体 exact 比較する。`build_admission` 削除と `decision.alpha` 改変を負例にする。

## refuted: 選択済み field と binding/spec の exact 性

- **判定: refuted。**
- `search_tag`、`ccbench_commit`、`spec_content`、workload、preregistration path の単独改変は exact 比較で拒否される [b10_backoff_shape_sweep.py:3190](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:3190)。
- binding は subset ではなく dict 全体の key/value equality である [b10_backoff_shape_sweep.py:3151](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:3151)。spec は top-level exact key 集合と固定 canonical digest の両方を要求する [b10_backoff_shape_sweep.py:1580](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:1580)。
- 3 系列 binding は別々の関数と literal のままで、実質的な一本化はない [b10_backoff_shape_sweep.py:3064](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:3064) [b10_backoff_shape_sweep.py:3304](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:3304) [b10_backoff_shape_sweep.py:3407](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:3407)。

## nit: 発火不能または production 候補集合で恒真な比較

- **判定: nit。成果物影響はない。**
- [b10_backoff_shape_sweep.py:3182](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:3182) で `"/" in space_version` を要求した後の `separator != "/"` [b10_backoff_shape_sweep.py:3190](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:3190) は発火不能である。
- 系列間の spec canonical JSON、`ccbench_commit`、formula、patch 比較 [b10_backoff_shape_sweep.py:3524](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:3524) は、各系列が同じ固定 spec digest、`PIN`、binding literal を既に通るため実質恒真である。calibration と `space_version` の系列間比較だけは恒真ではない。
- `_require_report_prereg_commit()` の `len(commits) != 1` [b10_backoff_shape_sweep.py:3546](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:3546) は入力でなく module literal 三つだけに依存する。
- `_assert_report_lock_binding()` の campaign ID 比較 [b10_backoff_shape_sweep.py:3107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:3107) は production では collector が直前に同じ literal を代入するため恒真である [b10_backoff_shape_sweep.py:3882](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:3882)。campaign directory と record の受理集合自体は collector と各 record validator が固定している。
- **最小修正:** 発火不能な `separator` arm と診断用の重複比較を変異防壁として数えない。削除するなら診断価値のない arm だけに限定する。

## refuted: 135 digest literal と 3 集合比較

- **判定: refuted。変更はない。**
- 現物は write-heavy、balanced、read-heavy が各 45 literalで合計 135。sorted union の meta digest はテスト literalどおり `97b0726e1dd45542be40bc9b39a76f6f739c02b1166b380a2c8a2d1b07cc4b00` だった [test_b10_backoff_shape_sweep.py:2748](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/tests/test_b10_backoff_shape_sweep.py:2748)。
- patch には 135 literal の追加、削除、置換がない。3 validator の default 集合と `_require_legacy_record_digests` 呼び出しも context のままである [s5-diff.patch:495](/home/SFC/tanab/.claude/jobs/9adfee39/tmp/t2408/s5-diff.patch:495) [s5-diff.patch:509](/home/SFC/tanab/.claude/jobs/9adfee39/tmp/t2408/s5-diff.patch:509) [s5-diff.patch:528](/home/SFC/tanab/.claude/jobs/9adfee39/tmp/t2408/s5-diff.patch:528) [s5-diff.patch:547](/home/SFC/tanab/.claude/jobs/9adfee39/tmp/t2408/s5-diff.patch:547) [s5-diff.patch:566](/home/SFC/tanab/.claude/jobs/9adfee39/tmp/t2408/s5-diff.patch:566) [s5-diff.patch:585](/home/SFC/tanab/.claude/jobs/9adfee39/tmp/t2408/s5-diff.patch:585)。
- fixture SHA-256 も宣言値と一致した: balanced `087e46df...6b9`、read-heavy `5abdfe11...80b7`、write-heavy `0a32c22b...1674`。

## refuted: 例外処理と既存テストの弱体化

- **判定: refuted。**
- 新入口は decoder 例外と blob verifier 例外を error に変換して再送出し、握り潰していない [b10_backoff_shape_sweep.py:3121](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:3121) [b10_backoff_shape_sweep.py:3134](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:3134)。選択済み key の `.get()` は欠落時に拒否へ流れ、早期成功 return や fallback はない。real 4 の未検査 key は別問題である。
- 旧 v1 正例は削除されたのではなく、現物 pre-T733 fixture 正例と v1/current-v2 負例へ強化されている [test_b10_backoff_shape_sweep.py:2522](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/tests/test_b10_backoff_shape_sweep.py:2522) [test_b10_backoff_shape_sweep.py:2556](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/tests/test_b10_backoff_shape_sweep.py:2556)。期待値反転、skip、既存負例の緩和はない。
- `test_ccbench_spawn_sites.py` の差分は `_build_binary` と `run_formal` の source line を `3294 -> 3644`、`4051 -> 4460` に追随させただけで、call count や membership pin を緩めていない [s5-diff.patch:1948](/home/SFC/tanab/.claude/jobs/9adfee39/tmp/t2408/s5-diff.patch:1948)。

## nit: 7 変異の帰属

- **判定: nit。現在の成果物値は変えないが、M4 の自己申告は正確でない。**
- 以下は pytest を実走せず、call graph と test body から静的に判定した。

| 変異 | その test だけ赤か | 静的帰属 |
|---|---|---|
| M1 historical decoder を通常 decoder へ戻す | いいえ | 3 workload の raw fixture 正例に加え、fixture helper を使う calibration test [test:2719](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/tests/test_b10_backoff_shape_sweep.py:2719)、orchestration test [test:2761](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/tests/test_b10_backoff_shape_sweep.py:2761) なども赤になる。spec-drift test は期待 code も変わる。最も単一理由に近いのは workload ごとの raw fixture 正例だが、全体で単独赤にはならない。 |
| M2 blob 照合呼び出し削除 | はい | `test_report_lock_identity_rejects_recanonicalized_false_authority` だけが照合呼び出しそのものを要求する。 |
| M3 binding exact 比較削除 | いいえ | analysis drift [test:2655](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/tests/test_b10_backoff_shape_sweep.py:2655) と series exchange [test:2673](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/tests/test_b10_backoff_shape_sweep.py:2673) の 2 test が同じ比較に依存する。前者が単一理由の診断には最も適するが、単独赤にはならない。 |
| M4 collector の write-heavy binding を balanced に交換 | いいえ | exact mutation を [b10_backoff_shape_sweep.py:3884](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:3884) に入れると、指定された series-exchange 負例は collector を通らないため緑のまま。collector と orchestration の正例が先行 mismatch で赤になる。実装子の「raw write-heavy 正例も赤」は、この caller-site mutation については誤り。 |
| M5 live calibration 復帰 | はい | fail stub を持つ orchestration test のみ。 |
| M6 live prereg 復帰 | はい | 同じ orchestration test のみ。 |
| M7 fixed spec digest 削除 | はい | locked-spec-drift 負例のみ。 |

- **最小修正:** M4 の変異位置を collector の `expected_binding` callsite と明記し、2850 行より前にその callee を AST で固定する。M1、M3、M4を単独赤にするには integration 正例を意図的に弱める必要があるため、単独赤要件ではなく「主診断 test」を明記する方が安全である。

## 総括

- **real 所見は 4 件。最重は calibration の全系列同時偽造で、report が偽の calibration record 数と provenance を発行する。**
- **この差分は現状のまま採ってはならない。** 単独 field の負例は強いが、相関改変と有効な別 authority の交換に対して受理集合が閉じていない。
- 親が必ず直すべき点は、calibration の固定値照合、authority と workload/binding の exact 結合、historical `space_version` と trial の固定、未検査 `search_config` 全体の exact 化である。併せて M4 の変異位置と期待赤 test の帰属を訂正する必要がある。