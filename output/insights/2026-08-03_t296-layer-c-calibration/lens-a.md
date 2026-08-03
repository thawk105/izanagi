判定は **NO-GO**。ただし「今すぐ実測せよ」ではない。正しい scope は、取得を現 wave では行わず、floor を `[T-011] → [T-096] → [T-088]` に接続し、較正点の扱いは「現行 8b freeze では再較正不要」に限定し、F-4 は既存 `[T-333]` へ統合することだ。

### 所見 1 — F-1 は現行 freeze に限って real だが、P2 の恒久却下は過剰

- 主張: H1/H2 を共通の 1m records / 48 threads で走らせることは承認済みだが、そこから read ratio 非依存を一般化して rr80/rr20 較正を恒久却下することはできない。
- 根拠: [docs/phase3-8b-descriptor-design.md:6](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t296-layer-c-calibration/docs/phase3-8b-descriptor-design.md:6) は H1/H2 の共通動作点を明示する一方、[docs/decisions.md:220](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t296-layer-c-calibration/docs/decisions.md:220) と [orchestrator/calibrator/model.py:10](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t296-layer-c-calibration/orchestrator/calibrator/model.py:10) は calibration を `(env, thread, representative workload)` に束縛し、[orchestrator/calibrator/cli.py:135](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t296-layer-c-calibration/orchestrator/calibrator/cli.py:135) は署名に rratio も含める。登録済み Pegasus artifact も rr50 を明記する (`output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:1685-1690`)。さらに既存監査は無条件再走でなく reuse qualification を要求している (`output/insights/2026-07-16_s8b-ruling-prep-consultations.md:195-201`)。
- 物理的反論: read ratio により abort 率や throughput は変わり得るが、scale 選択基準は LLC miss と maxrss 下限であり (`docs/roadmap.md:293-311`)、実証済み依存は skew と thread である。したがって物理論だけで「今すぐ再較正必須」とも言えない。
- 深刻度: **BLOCKER**
- 親 brief: **F-1 は現行 8b について real、P2「恒久却下」は refuted**。

### 所見 2 — 親の 2 / 2 / 316 は規約上の hit 数ではない

- 主張: 規約どおりの現行再走は rr80=0 files、rr20=0 files、positive control rr50=67 files であり、親の 2 / 2 / 316 は行数を混ぜた誤計数である。
- 根拠: freeze は file-level conjunction と `output/s8b-freeze/` 除外を明記する (`output/s8b-freeze/holdout_freeze.json:17-37`)。実装もファイル単位で三軸連言を数える (`orchestrator/campaign/s8b_holdout_freeze.py:270-294,297-315`)。実 repository の期待値も rr80/rr20 とも空集合 (`orchestrator/tests/test_s8b_repo_scan_invariant.py:21-35`)。静的再走では対象 4932 files、rr80/rr20 の rratio 軸自体が各 0、positive conjunction が 67 だった。
- 深刻度: **MINOR**
- 親 brief: **F-2 の数値 2 / 2 / 316 は refuted、「実測値ファイル 0」は real**。監査中に出現した親の後続 draft は 0 / 0 / 67 へ訂正済み (`output/insights/2026-08-03_t296-layer-c-calibration/ruling.md:47-55`)。

### 所見 3 — 測定自体は holdout を壊さず、closure 外の測定が launch を壊す

- 主張: 2026-07-16 の snapshot は後続測定で遡及的に壊れないが、v1 launch 直前には live zero-hit scan が必要であり、official floor 後は measurement closure と完全一致する hit が許容される。
- 根拠: v1 verifier は snapshot 整合と現時点有効性を分離し、実測後の live scan failure を意図した挙動とする (`orchestrator/campaign/s8b_holdout_freeze.py:683-699`)。official floor は発行直前に 0 hit を要求する (`orchestrator/campaign/s8b_floor_campaign.py:1600-1620`)。一方 v2 は post-floor の 0 件要求を外し (`orchestrator/campaign/s8b_ratified_freeze.py:1403-1406`)、closure から導いた hit と repository の hit の完全一致を要求する (`:3077-3118`)。
- 深刻度: **MAJOR**
- 親 brief: **F-2「calibration/floor を測ること自体が holdout を壊す」は refuted**。ただし official certificate 前の ad-hoc calibration、または closure 外成果物が launch を塞ぐという狭い主張は real。

### 所見 4 — F-3 は所有者と先行依存を落としている

- 主張: authoritative floor の所有者は `[T-011]` であり、その既裁定鎖は `[T-096] → [T-088] → 段階3・4 → 実行revision束縛` なので、「T-088 段階3・4待ち」だけへの繋ぎ替えは不完全である。
- 根拠: `[T-011]` の鎖は `docs/archive/worklog-phase3-0726-12-0727-19.md:679-680` に明記される。`[T-096]` はユーザー裁定で測定前・`[T-088]` より先と確定済み (`docs/archive/worklog-phase3-0726-1-11.md:814-832`)。現行台帳でも T-096/T-088/T-011 はすべて active (`docs/worklog.md:278-287`)。
- 代替経路: 8c の12条件は正式系列の前提で、項7自身が floor 取得を要求するため floor の先行 blocker ではない (`docs/phase3-8c-preregistration.md:93-124`)。pilot は `eligible_for_refreeze=True` にできず (`s8b_floor_campaign.py:2319-2333`)、legacy driver は linux-baremetal と rr5/50/95 固定 (`between_run_floor.py:45-61`) なので authoritative な迂回路もない。
- 深刻度: **MAJOR**
- 親 brief: **F-3「今は authoritative 取得不能」は real、「所有者=T-088、先行条件は段3・4だけ」は refuted**。P1 は `[T-011]` と完全な依存鎖へ接続すべき。

### 所見 5 — F-4 は実欠陥だが既に T-333 に包含される

- 主張: linux-baremetal 固定の既定値は実欠陥だが、新規起票すると `[T-333]` の意味重複になる。
- 根拠: loader は既定を linux-baremetal に固定し env_tag を検査しない (`orchestrator/campaign/screening_driver.py:31-58`)。しかし `[T-333]` は既に「screening に env 次元がなく、loader も env_tag を読まない」と起票済み (`docs/archive/worklog-phase3-0802-117-121.md:300`) で、現行台帳にも残る (`docs/worklog.md:1957`)。`[T-331]` は兄弟 driver の COMPUTE 閉鎖であり、直接の所有者は T-333。
- 発火条件: 親が調べた `output/env/pegasus/` は calibration/floor namespace で、sweep の所在は `output/campaigns/` または `output/exploration/campaigns/` (`docs/orchestrator-design.md:108-110`)。両 campaign namespace の repo-wide 静的走査でも Pegasus 実測 ID は 0 で、D125 も live measurement 未開通を明記する (`docs/decisions.md:6141-6145`)。
- 深刻度: **MAJOR**
- 親 brief: **F-4 の欠陥と no-trigger は real、P3「新規起票」は refuted**。T-333 へ証拠を追記すべき。

### 所見 6 — P4 は既裁定の 8b floor と一般用途 floor を混同している

- 主張: 8b の対象環境はユーザーが既に Pegasus と確定しており、「Pegasus を主張 env にするか」を T-296 の先行判断へ戻すことはできない。
- 根拠: 2026-07-18 に `env_tag=Pegasus` がユーザー確定され、D59 の一般的な正本昇格とは独立と明記された (`docs/archive/worklog-phase3-0717-0718.md:589-600`)。現行 phase も floor を Pegasus 単独とする (`docs/phase3.md:102-105`)。2026-07-27 裁定は優先度低下であって廃止ではない (`docs/phase3.md:126-132`)。
- 深刻度: **MAJOR**
- 親 brief: **P1 の「今は実装しない」は real、P4 を T-296 の blocker にすることは refuted**。8b 非依存の一般用途 floor は別 scope としてのみユーザーへ返せる。

### 所見 7 — 親の固定値・一次実測は、hit 数以外は一致した

- 主張: HEAD、freeze fields、protocol fields、job 873225 の拒否文、Pegasus floor artifact 0 件は実物と一致し、主要な食い違いは hit の単位と F-3 の依存鎖である。
- 根拠: `holdout_freeze.json:4,17,620-624`、`output/s8b-freeze/floor_protocol.json:1`、`output/env/pegasus/floor/job-staging/0:873225.nqsv/floor-driver.stdout:1`、`orchestrator/campaign/s8b_floor_campaign.py:194-204,3437-3444`。開始時 HEAD は `1a3604b126c853fc98426f0dbf67b7dde96fa3da` で clean だった。
- 深刻度: **NIT**
- 親 brief: **F-3 の protocol・driver・拒否実測は real**。監査中に親が未追跡の ruling/worklog fragment を生成したため現在の dirty 状態は brief の開始時 clean 主張を反証しない。

pytest・受入テストは実行していない。実行したのは repository scanner の静的再計数だけであり、緑とは記録しない。親が生成した未追跡ファイルにも変更を加えていない。

## 総括

- 判定: **NO-GO** — 今は取得しないが、`T-011 → T-096 → T-088` への接続、P2 の現行 freeze 限定、F-4 の T-333 統合という別 scope が正しい。
- 最も重い所見 1 件: **P2 の恒久却下は、現行 8b の共通動作点を read-ratio 不変性へ一般化しており BLOCKER。**
- 親が見落としている一次資料: `docs/archive/worklog-phase3-0726-12-0727-19.md:679-680`、`docs/archive/worklog-phase3-0726-1-11.md:814-832`、`docs/archive/worklog-phase3-0802-117-121.md:300`。