必須の `brief.md` / `output.md` は全文読了済みです。設計正本、D19/D25/D95/D96、hooks、現行 WAL/identity/loop/pipeline/Layer3/S8a と関連テストも静的に突合しました。

本レビューは read-only です。編集・pytest・mutation 実走は行っておらず、非実走を green 扱いしていません。終了時の worktree は clean でした。また、計画中の4実装ファイルはまだ存在しません。

### R1 — S8a 実在 pair は promotion の正例になれない

- 判定: **real**
- Severity: **Critical**
- 型: **[ドリフト] [権限逸脱] [恒真ゲート]**
- 根拠: plan は実在 S8a pair を admission し、`reproduced + multi-boot` だけで promotable とします。[output.md:74](/home/SFC/tanab/github/izanagi/.codex/dev-wave-t126-jobs/plan/output.md:74) [output.md:182](/home/SFC/tanab/github/izanagi/.codex/dev-wave-t126-jobs/plan/output.md:182) しかし D47 は、8a 由来軸を headline 対象外とし、昇格には事前登録改訂と独立の人間再命名を要求しています。[decisions.md:1685](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/docs/decisions.md:1685) 現行 S8a producer と report も同じ非対象宣言を保持しています。[s8a_trigger_sweep.py:11](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/campaign/s8a_trigger_sweep.py:11) [s8a_trigger_sweep.py:511](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/campaign/s8a_trigger_sweep.py:511)
- 攻撃: 現 allowlist には「formal headline eligibility」「人間再命名・事前登録改訂の証拠」がありません。統計的に reproduced なら、preliminary S8a pair をそのまま promotable にできます。
- 成果物影響: certified 自体は変わりませんが、headline/selected の受理集合が無断で拡大します。`promotion.json` と proof chain には D47 前提を満たす参照が残らず、ledger の統計的正しさだけで不適格候補を昇格できます。
- **裁定パッケージ候補**: (a) T-126 の当該 pair を qualification-only として構造的に promotion 不可にする、または (b) D47 を明示的に改訂し、正式 eligibility certificate の producer→loader→consumer を追加する。自己申告 boolean の追加では F14 型です。

### R2 — `layer3_promotion` は正式 report/headline consumer に接続されていない

- 判定: **real**
- Severity: **Critical**
- 型: **[恒真ゲート] [手順漏れ]**
- 根拠: 計画上の call graph は `s8a_seqstop → require_promotable` で終わり、`render()` を呼びません。[output.md:32](/home/SFC/tanab/github/izanagi/.codex/dev-wave-t126-jobs/plan/output.md:32) 一方、配置には `reports/promotion.json` を置くとしています。[output.md:127](/home/SFC/tanab/github/izanagi/.codex/dev-wave-t126-jobs/plan/output.md:127) 現行正式 Layer3 は一 campaign の材料射影だけで、promotion/series 比較を読みません。[layer3_report.py:314](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/campaign/layer3_report.py:314) CLI も単独 `render()` のみです。[layer3_report.py:420](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/campaign/layer3_report.py:420) v2 schema は閉じており promotion field を追加できません。[layer3_schema.json:5](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/campaign/layer3_schema.json:5)
- 攻撃: producer の末尾で例外を投げても、それは producer 自身の終了判定にすぎません。既存 Layer3 CLI/report 経路は gate を一度も通らず、負終端では例外が先に出て `promotion.json` 自体が生成されない可能性もあります。
- 成果物影響: 正式 report は ledger/promotion を参照せず従来どおり生成可能です。headline proof へ round refs が届かず、拒否理由もレポート化されません。
- **裁定パッケージ候補**: v2 を不変にするなら、新しい authoritative headline/report wrapper を正式入口として決定に登録し、常に `assess→render`、headline 出力時のみ `require` を通す必要があります。v3 化するなら generator/schema bytes 変更を伴う別裁定です。

### R3 — source identity と low-abort admission の閉包が不足している

- 判定: **real**
- Severity: **High**
- 型: **[ドリフト] [恒真ゲート]**
- 根拠: series canonical list は pair の12桁 IDと BENCH_DONE/COMMIT refs を束縛しますが、full `src_token`、BUILD_START、provenance SHA、high-abort 基準点を列挙していません。[output.md:100](/home/SFC/tanab/github/izanagi/.codex/dev-wave-t126-jobs/plan/output.md:100) full `src_token` は BUILD_START にだけ存在し、BENCH_DONE/COMMIT にはありません。[wal.jsonl:19](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/output/campaigns/p3-s8a-trigger-sweep-balanced-sweep-c2d838b8/runs/wal.jsonl:19) [wal.jsonl:23](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/output/campaigns/p3-s8a-trigger-sweep-balanced-sweep-c2d838b8/runs/wal.jsonl:23) D25 は consumer が確定済み src identity を追従することを要求します。[decisions.md:493](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/docs/decisions.md:493)
- 追加の欠落: plan は low-abort class を admission に使いますが、その判定は pair 以外の `ident_all.abort_rate` と `HIGH_ABORT_FACTOR` に依存します。[output.md:78](/home/SFC/tanab/github/izanagi/.codex/dev-wave-t126-jobs/plan/output.md:78) [s8a_trigger_sweep.py:608](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/campaign/s8a_trigger_sweep.py:608) これらは series identity にありません。
- 攻撃: source WAL/provenance が置換されても、派生 ref から新しい series IDを作って受理できます。元の Layer3 report が pin している source WAL SHAとの一致も読みません。[layer3_report.json:1](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/output/campaigns/p3-s8a-trigger-sweep-balanced-sweep-c2d838b8/reports/layer3_report.json:1)
- 成果物影響: ledger が別 source mutation や別 high-abort 基準を同じ意味の系列として記録し、proof refs が実装 identity まで到達しません。誤った low-abort admission は最終 promotion を変えます。
- 必須修正: trusted source certificate に、期待 source WAL SHA、provenance SHA、full resolved ccbench OID、full src tokens、BUILD_START/VERIFY/BENCH/COMMIT refs、`ident_all` refと係数を束縛してください。

### R4 — 実 WAL field は boot・時間窓・実行契約の証明として不十分

- 判定: **real**
- Severity: **High**
- 型: **[恒真ゲート] [ドリフト]**
- 根拠: brief 自身が、現行 WAL field と「実在 boot-id」を同一 seam としています。[brief.md:7](/home/SFC/tanab/github/izanagi/.codex/dev-wave-t126-jobs/plan/brief.md:7) しかし現行 WAL record に boot-id はなく、`ts` は identity 外の provenance です。[model.py:90](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/campaign/model.py:90) WAL は hash chain/authenticity を持たず、`ts` の明示注入も可能です。[wal.py:14](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/campaign/wal.py:14) [wal.py:499](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/campaign/wal.py:499)
- 実行契約の断線: series ID は env tag だけを含み、contract SHA、calibration ref、`allow_resume` を含めません。[output.md:109](/home/SFC/tanab/github/izanagi/.codex/dev-wave-t126-jobs/plan/output.md:109) `_eval_one` は hardcoded ENV/clock/NUMA で `run_campaign` を呼びます。[s8a_trigger_sweep.py:84](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/campaign/s8a_trigger_sweep.py:84) [s8a_trigger_sweep.py:371](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/campaign/s8a_trigger_sweep.py:371) `run_campaign` は `env_contract` を受け渡しません。[loop.py:43](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/campaign/loop.py:43)
- 攻撃: 同じ env tag の契約改訂前後を同一 series に混ぜられます。`round_started` の boot-id は、各 BENCH/COMMIT record がその boot で生成されたことを WAL 内では証明しません。WAL `ts` は30分の運用ヒントには使えても、独立時間窓の proof にはなりません。
- 成果物影響: multi-boot/reproduced の promotion、レポートの α/β 表示、ledger の環境帰属が偽陽性になり得ます。
- 必須修正: contract SHA・isolation policy・calibration refを series identity に入れ、既存 execution receipt の発行・再検証を各 round に束縛してください。[execution_guard.py:67](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/campaign/execution_guard.py:67)
- **裁定パッケージ候補**: BENCH/COMMIT record 自体への boot/receipt 束縛を要求するなら、no-touch の `loop/pipeline/WAL` を越える変更です。そこまで行わない場合は「trusted driver が観測した session provenance」に主張を縮小する必要があります。

### R5 — round WAL の lifecycle state machine が未規定

- 判定: **real**
- Severity: **High**
- 型: **[恒真ゲート] [テスト代表性] [手順漏れ]**
- 根拠: plan は median、legacy+S2、tps数などを列挙しますが、expected variant ごとの完全 event topology を規定していません。[output.md:163](/home/SFC/tanab/github/izanagi/.codex/dev-wave-t126-jobs/plan/output.md:163) 現行 WAL parser は payload schema と event topology を明示的に consumer 責務とします。[wal.py:172](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/campaign/wal.py:172) `replay()` は順序を検査せず、`records_by_stage()` は最後勝ちです。[wal.py:566](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/campaign/wal.py:566) [wal.py:586](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/campaign/wal.py:586) 重複 COMMIT の最後勝ちは現行テストにも固定されています。[test_campaign.py:1111](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/tests/test_campaign.py:1111)
- 攻撃: COMMIT 後の BENCH/COMMIT、二重 terminal、別 BUILD_START、legacyだけの VERIFY、BENCH と COMMIT の交差対応を混ぜた WALから、都合のよい最後の値を選べます。
- 成果物影響: `x`、LLR、reproduced 判定、promotion report の source refsが変わり、偽 headline を作れます。
- 必須修正: 新 round に限定した exact lifecycle automatonを定義し、duplicate/post-terminal/extra variant/wrong full src token/VERIFY tag重複・欠落を拒否してください。これらの負例を mutation matrix に追加する必要があります。

### R6 — private `_eval_one` 直呼びは S8a の production preflight を継承しない

- 判定: **real**
- Severity: **High**
- 型: **[手順漏れ] [テスト代表性]**
- 根拠: plan は `_eval_one` を直接2回呼びます。[output.md:82](/home/SFC/tanab/github/izanagi/.codex/dev-wave-t126-jobs/plan/output.md:82) 現行 public `run_sweep` はその前に single-tenant、pinned-clean、isolated checkout、layout/cache を組み立てます。[s8a_trigger_sweep.py:240](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/campaign/s8a_trigger_sweep.py:240) `_eval_one` 自身はそれらを行わず、呼び手から `sub/patch/cache_root` を受け取るだけです。[s8a_trigger_sweep.py:346](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/campaign/s8a_trigger_sweep.py:346) 既存契約は driver 冒頭と pipeline genomeごとの二段 admission です。[p2_2.py:71](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/campaign/p2_2.py:71)
- 攻撃: 新 driver が preflight/worktree lifecycle を一つでも落とすと、共有 submoduleや競合状態で部分 WALを書き始めます。設計が主張する「round ごとの campaign 冒頭 admission」も成立しません。[sequential design:144](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/output/insights/2026-07-15_sequential-stopping-design.md:144)
- 成果物影響: round WAL/ledger は partial・汚染・wrong sourceへ倒れ、レポートは indeterminate または誤った proof参照になります。
- 必須修正: 新 driver の production steps に preflight、pinned checkout、worktree cleanup、typed layout、round全体の lock spanを明記し、公開 CLIからその経路を踏むテストを置いてください。
- **裁定パッケージ候補**: S8a 側に正式 public adapter seamを追加する案は freeze source no-touch を越えます。

### R7 — series writer と repair の path/concurrency 防壁が prose のまま

- 判定: **real**
- Severity: **High**
- 型: **[権限逸脱] [恒真ゲート] [手順漏れ]**
- 根拠: `series-run.lock` は配置だけで、取得方式・保持範囲がありません。[output.md:127](/home/SFC/tanab/github/izanagi/.codex/dev-wave-t126-jobs/plan/output.md:127) append単位の `flock` は、`load→reconcile→measure×2→observe` 全体の競合を防ぎません。さらに plan の writer は leaf `O_NOFOLLOW` を列挙しますが、approved durable root・親 directory identity・path capability を規定していません。[output.md:150](/home/SFC/tanab/github/izanagi/.codex/dev-wave-t126-jobs/plan/output.md:150) 現行にはそのための capability APIがあります。[layout.py:51](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/campaign/layout.py:51) [layout.py:107](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/campaign/layout.py:107)
- 防護限界: hooks は `runs/` 直接編集を拒否しますが、Python script内部の書込みは見えず、Codexにも未配線です。[hooks/README.md:41](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/hooks/README.md:41) [hooks/README.md:163](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/hooks/README.md:163)
- 攻撃: 二重起動が同じ round を並行実測し、duplicate start/混合 child WALを作れます。誤った pathを渡せるAPIなら、source campaignの `runs/` に新 ledgerを作る、または repair対象を取り違える経路も残ります。
- 成果物影響: ledger破損、promotion report拒否、source campaignのartifact-set汚染。既存 WAL schemaを直接弱めるわけではありませんが、新 protected writer の権限境界が成立していません。
- 必須修正: computed coordinator identityからのみ pathを導出し、durable capabilityを必須化、source campaign ID拒否、全 transaction中のexclusive lock、repairも同じ lock、repair receiptのpromotion proof参照を要求してください。

### R8 — P2 の実 WAL fixture と mutation は production activation を証明しない

- 判定: **real（plan自身も一部認識済み）**
- Severity: **High**
- 型: **[テスト代表性] [恒真ゲート] [手順漏れ]**
- 根拠: 設計 §8 は actual positive control を要求します。[sequential design:187](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/output/insights/2026-07-15_sequential-stopping-design.md:187) plan も tracked WALでは driver、時間分離、boot、full pipeline連続運用を検査できないと認めています。[output.md:205](/home/SFC/tanab/github/izanagi/.codex/dev-wave-t126-jobs/plan/output.md:205) 現行実 WAL test は既存 producer schemaと uncertified値隔離を検査するだけです。[test_bench_first_real_wal.py:46](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/tests/test_bench_first_real_wal.py:46)
- mutation帰属: `_eval_one` no-op、boot-id削除、legacy+S2削除などは、別の先行 schema/reconcile gateでも赤になり得ます。[output.md:255](/home/SFC/tanab/github/izanagi/.codex/dev-wave-t126-jobs/plan/output.md:255) F28 は公開経路で、先行拒否なし・赤理由一意を要求します。[failures.md:371](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/docs/failures.md:371)
- 成果物影響: mutation台帳が偽 KILLED、受入記録が driver E2Eを覆ったように見えます。実 promotion の信頼性は上がりません。
- 必須修正: full-valid fixtureを使い、公開 CLI→driver→real `_eval_one` scaffolding→real `run_campaign`→fake deepest measurement leaf→actual round WAL→ledger→reportまで一本通してください。各 mutation は期待する拒否 status/reasonを一意に固定します。
- **裁定パッケージ候補**: production activation用の実測 positive control。plan の `implemented-but-unqualified` 表示は妥当で、これを T-126 完了や operational headline gateへ格上げしてはいけません。

### R9 — freeze closure は plan の列挙より広い

- 判定: **real**
- Severity: **Medium**
- 型: **[ドリフト] [手順漏れ]**
- 根拠: plan は S8a/axis source hash と23 artifactを主に列挙します。[output.md:305](/home/SFC/tanab/github/izanagi/.codex/dev-wave-t126-jobs/plan/output.md:305) しかし known-axes は S8a の歴史 hash `3e947…` を保持し、read-only `sha256sum` での現行 S8a は `8c3abd…` でした。[known_axes_freeze.json:46](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/output/s1-freeze/known_axes_freeze.json:46) この歴史 pin は T080 migration specs、holdout freeze、oracle testsへ展開されています。[t080_freeze_migration.py:87](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/campaign/t080_freeze_migration.py:87) 23件 manifestは artifact bytesの別層です。[test_frozen_artifacts.py:38](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/tests/test_frozen_artifacts.py:38)
- 攻撃: 「現 source hashが freezeと一致する」前提で live verifierを走らせると既知 migration driftを新回帰と誤帰属し、fixtureへ現 hashを差してF27を再発させかねません。
- 成果物影響: certified選択は直ちに変わりませんが、freeze proof、oracle trust chain、受入記録の帰属が壊れます。
- 必須修正: source campaign全既存ファイル、historical source pins、T080 closure、holdout/oracle goldens、Layer3 v2 generator/schemaを別々にpre/post hash監査してください。repinはしないこと。

### R10 — D96 の「新しい D」が plan に明記されていない

- 判定: **real**
- Severity: **Medium**
- 型: **[手順漏れ] [権限逸脱]**
- 根拠: plan は `docs/decisions.md` の「更新」と境界テスト候補を別々に列挙するだけです。[output.md:287](/home/SFC/tanab/github/izanagi/.codex/dev-wave-t126-jobs/plan/output.md:287) [output.md:249](/home/SFC/tanab/github/izanagi/.codex/dev-wave-t126-jobs/plan/output.md:249) D96 は、受理集合変更に既存 D追記でなく新しい Dと境界テストを同じ変更単位で要求します。[decisions.md:4271](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/docs/decisions.md:4271)
- 成果物影響: headline allowlist変更の理由・射程・却下案が proof chainから落ち、将来の report/selection consumerがどの決定に従うか不明になります。
- 必須修正: D47との関係、qualification/activation二段階、正式 consumer、acceptance boundaryを新 Dとして同一 commitに含めてください。

### Refuted A — D95 owner分離そのもの

- 判定: **refuted（条件付き）**
- Severity: **Informational**
- 型: **[権限逸脱]**
- 根拠: brief は実装面を Codex author worker 1本へ所有させ、managerの直接編集を禁止しています。[brief.md:17](/home/SFC/tanab/github/izanagi/.codex/dev-wave-t126-jobs/plan/brief.md:17) これはD95と一致します。[decisions.md:4244](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/docs/decisions.md:4244)
- 条件: `layer3_promotion_schema.json` も機械設定としてworker所有です。review後fixも同workerへ戻し、managerはdocs、統合、実走、commit、統合後の一時mutationだけを担当する必要があります。
- 成果物影響: 条件を守ればなし。

### Refuted B — 既存 WAL/schema bytes を直接弱めるという攻撃

- 判定: **refuted**
- Severity: **Informational**
- 型: **[ドリフト]**
- 根拠: plan は `model/ident/loop/pipeline/wal/layer3 v2/S8a` を変更対象外とし、source campaignへ書かないと明記しています。[output.md:291](/home/SFC/tanab/github/izanagi/.codex/dev-wave-t126-jobs/plan/output.md:291) [output.md:307](/home/SFC/tanab/github/izanagi/.codex/dev-wave-t126-jobs/plan/output.md:307)
- 成果物影響: この境界を守れば既存 COMMIT、WAL record、Layer3 v2 generator/schemaのbytesは変わりません。ただしR5/R7の新 consumer/writer契約は別問題です。

### Refuted C — P2 を無条件の production-ready とした、という output planへの攻撃

- 判定: **refuted（briefには成立、output planは訂正済み）**
- Severity: **Informational**
- 型: **[テスト代表性]**
- 根拠: brief P2はtracked fixtureをwave受入としますが、output planはコードlandingとproduction activationを明確に分離し、positive controlなしを `implemented-but-unqualified` としています。[brief.md:15](/home/SFC/tanab/github/izanagi/.codex/dev-wave-t126-jobs/plan/brief.md:15) [output.md:5](/home/SFC/tanab/github/izanagi/.codex/dev-wave-t126-jobs/plan/output.md:5)
- 成果物影響: この格下げを維持すれば、非実走をproduction証明として記録する過大表現は避けられます。

## 総括

現 plan は **production-ready / T-126完了として NO-GO** です。

最大の blocker は、実在入力が D47 により headline 不適格であること、`layer3_promotion` が正式 report/headline consumerへ到達しないこと、そして boot/time/env・full source identity・round WAL topologyの proof closureが不足していることです。新規ファイルを三点並べ、driver末尾で例外を投げるだけでは production pathにはなりません。

段4では少なくとも次の択一が必要です。

- qualification-only のコードlandingに縮小し、S8a pairを構造的に promotion不可、状態を `implemented-but-unqualified` のままにする。
- または、D47/D96を含む新裁定、正式 headline consumer、eligibility certificate、実行receipt/WAL束縛、実測positive controlまで含む**裁定パッケージ候補**へ拡張する。

pytest・mutation・実測は未実施であり、本レビューは静的判定のみです。