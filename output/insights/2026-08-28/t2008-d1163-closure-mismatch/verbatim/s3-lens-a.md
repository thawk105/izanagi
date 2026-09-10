## 所見

### A-01

- **ID:** A-01
- **判定:** real
- **scope:** scope 内
- **反例:** v2 lock が記録 commit A と正しい 24-path digest を持ち、現在は clean な commit B に進んでいる campaign を作る。WAL は build receipt・attempt topology を満たす一方、同じ attempt に `verify_done(certified=False, anomalies=1)` と、その後の `bench_done` / `commit` を置き、commit verification receipt は持たせない。`_inspect_campaign()` は verify verdict、anomaly 数、commit receipt を検査せず、撤去後は E1 の `CertifiedCampaignView` を発行する。さらに `s6_sort_sweep.py:453` と `s8a_trigger_sweep.py:554` は `commit is not None` だけで `certified=True` とする。現行比較を戻せば A/B mismatch で拒否されるため、受理集合の拡張で新たに開く経路である。
- **成果物影響:** anomaly variant の TPS が certified row、S6/S8A レポート、ランキング・選択集合へ入る。

### A-02

- **ID:** A-02
- **判定:** real
- **scope:** scope 内
- **反例:** `verifier_assessment_basis` を読む計画は Layer3 の `build_report()` だけである。歴史 consumer の `p2_2_report._epoch_provenance()`、`critic.digest.render_text()` / `online_digest_text()`、`tools/plotting/plot_backoff.py`、`tools/plotting/plot_s1_9pair.py` は property を読まず、従来の epoch と `HISTORICAL_RAW` だけを出す。特に `plot_s1_9pair.py:834-837` は出力上で「certified accepted evidence」と表現し続ける。
- **成果物影響:** Layer3 以外の Markdown、critic 入力、plot provenance、図キャプションには「当時の verifier 判定」が届かず、現行検証済みとの誤読面が残る。

### A-03

- **ID:** A-03
- **判定:** real
- **scope:** scope 内
- **反例:** D1163 の5検査のうち、変更対象の certified read 経路で必ず走るのは #1 だけである。#2 は `assert_trial_registry_acceptance()` 配下、#3 は `load_ratified_freeze()` 配下、#4 の anomaly 即 reject は live `pipeline.evaluate()` 配下、#5 は 8b `launch_validate()` 配下であり、`require_admitted_campaign()`、S6/S8A、backoff consumer からは呼ばれない。各関数自体は恒真ではないが、「certified read 全体の保持検査」という一般化は成立しない。
- **成果物影響:** preregistration、freeze、live trace receipt、current contract compatibility のいずれも通っていない campaign が、別 consumer の certified report 入力になり得る。

### A-04

- **ID:** A-04
- **判定:** real
- **scope:** scope 外
- **反例:** 正しい campaign A に対し、現在 closure の1ファイルへ未commitの1 byteを加えると `capture_contract_loader_binding()` が失敗し `current-closure-unavailable` で拒否される。同じ bytes を commit しただけで撤去後は受理される。成果物の束縛も意味も変わらず、Git working-tree 状態だけが拒否理由である。
- **成果物影響:** dirty 中は certified report、digest、selection が全消失し、commit 後に同じ成果物が復活する。

### A-05

- **ID:** A-05
- **判定:** real
- **scope:** scope 外
- **反例:** E1 の `HistoricalCampaignView` の field と公開されている module attribute `_CERTIFIED_VIEW_TOKEN` を使えば、exact `CertifiedCampaignView` を直接構築できる。これは `require_certified_campaign_view()` を通り、S6/S8A の exact-type check も通る。replay receipt 経路は追加 capability で拒否するが、S6/S8A はそれを要求しない。既存テスト自身もこの token による forged view を構築している。
- **成果物影響:** historical records を certified rows として集計でき、レポートの参照元・選択集合が型境界を越える。

### A-06

- **ID:** A-06
- **判定:** real
- **scope:** scope 内
- **反例:** 変異候補5で `trial_registry.py:1419-1420` だけを削っても、直後の `1423-1425` が同じ manifest digest/raw bytes mismatch を拒否する。指定 node は例外 message が `"manifest blob differs"` から `"loaded manifest differs"` へ変わるため赤になるだけで、受理挙動は変わらない。
- **成果物影響:** 変異前後で受理集合は不変。node の赤は束縛喪失を示さず、変異テストとして過剰決定である。

### A-07

- **ID:** A-07
- **判定:** real
- **scope:** scope 内
- **反例:** brief は「producer の出力 bytes は変わらない」とするが、plan は historical Layer3 epoch に field を追加し、`plan.md:372` で再生成 JSON bytes が変わると明記している。
- **成果物影響:** 再生成した Layer3 JSON、その SHA、これを参照する provenance は変わる。既存 `FROZEN_MANIFEST` 23件を編集しないこととは別の主張である。

## プランの誤り

- [plan.md:7](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2008-d1163-closure-mismatch/plan.md:7) — post-removal の certified view を「記録 commit 検証済み E1」とだけ説明する一方、consumer がこれを current certified として扱う境界を検査していない。A-01 の failed-verdict campaign が通る。
- [plan.md:36](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2008-d1163-closure-mismatch/plan.md:36) — #1 の呼び出し連鎖は正しい。ただし「両 purpose」は authority を持つ通常 campaign に限り、E0・overlay-denied では当該照合は走らない。
- [plan.md:52](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2008-d1163-closure-mismatch/plan.md:52) — #2 を「artifact admission と独立」と書いた時点で、post-removal certified path の保持保証にはなっていない。
- [plan.md:71](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2008-d1163-closure-mismatch/plan.md:71) — #4 は live pipeline の保証だけである。persisted reader の S6/S8A は `verify_done.certified`、anomaly、commit receipt を検査しない。
- [plan.md:94](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2008-d1163-closure-mismatch/plan.md:94) — #5 は 8b live launch surface の具体例であって、全 certified campaign consumer の意味互換性 checker ではない。plan 自身も `:108` で単一 checker 不在を認めている。
- [plan.md:112](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2008-d1163-closure-mismatch/plan.md:112) — proposed mismatch acceptance test 自体は恒真ではない。比較条件を戻せば intended exception で赤になる。ただしこれは「正常な A/B mismatch の受理」しか固定せず、規律2不変を固定しない。
- [plan.md:178](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2008-d1163-closure-mismatch/plan.md:178) — 保存済み stale evidence が ineligible のままなのは正しいが、同じ基礎 campaign を再射影すると `E1/eligible=True` へ変わる。legacy reader test だけでは producer 再分類の安全性を保証しない。
- [plan.md:208](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2008-d1163-closure-mismatch/plan.md:208) — certified consumer の列挙は受理集合の拡張先を示すだけで、各 consumer が verifier receipt/verdict を検査するかを確認していない。S6/S8A/backoff が反例。
- [plan.md:287](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2008-d1163-closure-mismatch/plan.md:287) — historical marker test は view と Layer3 だけ。P2-2、critic、plotting の出力面が無被覆。
- [plan.md:349](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2008-d1163-closure-mismatch/plan.md:349) — 変異候補5は上記 A-06 の等価変異。

変異候補の静的帰属は以下である。実走はしていない。

| 候補 | 静的判定 |
|---|---|
| 1. map比較復活 | 指定8 node は intended mismatch で赤になる。負例は恒真ではない。ただし「完全集合」は全suite未実走のため証明されない。 |
| 2. marker literal変更 | 指定2 node は赤。Layer3 側は schema `const` と exact dict の双方で落ち得るが、同じ性質の重複である。 |
| 3. Layer3 marker未伝播 | 指定1 node は exact dict 不一致で赤。schema property が optional なので schema 単独では落ちない。 |
| 4. committed binding迂回 | `classify_campaign()` は current gateを通らないため、指定24 parameter node はそれぞれ期待例外を失って赤になる。 |
| 5. manifest SHA比較削除 | 欠陥。直後の重複照合で拒否され続け、message差だけで赤になる。 |
| 6. freeze G-blob SHA削除 | 指定1 node は拒否を失って赤になる。後続 dirty/history checks は記録SHA偽装を検出しない。 |
| 7. operation比較削除 | 指定1 node は operation-only mismatch ケースで赤になる。combined test の前半には variant による過剰決定があるが、後半に単独反例がある。 |
| 8. live resolver差替え | 指定1 node は live launch が成功して `pytest.raises` を外すため赤になる。 |

## 親 brief の誤り

- [s1-brief-measurements.md:13](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2008-d1163-closure-mismatch/s1-brief-measurements.md:13) — `output/campaigns` は33 campaign dirではない。独立列挙では30 directoryと3 summary fileで、30 directoryすべてにlockがある。
- 同 `:14-18` — 30 lockが全てschema-less v1、authorityなし、したがって E0 という結論は確認した。repo全体では別に `output/insights/.../campaign-layout` に2 lockあるが、これらもE0。静的検索では保存済みE1/E1-stale JSONは見つからなかった。
- 「撤去対象が現在発火していない」は正しいが、安全性の証拠にはならない。また現在30件を読めるようにする価値もゼロである。撤去の価値は将来のv2 campaignとclosure前進後の読出しにあり、この実測からは肯定・否定どちらも導けない。
- [s1-brief.md:64](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2008-d1163-closure-mismatch/s1-brief.md:64) — 「既存 certified campaign が全件 E1-stale」は、測定した30件が全E0という事実と両立しない。別の外部E1集合を指すなら、その集合が特定されていない。repo内30件はコード変更前後ともE0拒否である。
- [s1-brief.md:39](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2008-d1163-closure-mismatch/s1-brief.md:39) — `FROZEN_MANIFEST` 23 keyがすべて`output/`であること、figure provenance内の7 epoch objectが全E0であることは確認した。ただし「producer bytesは変わらない」はplanのfield追加と矛盾する。
- [s1-brief-measurements.md:29](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2008-d1163-closure-mismatch/s1-brief-measurements.md:29) — 「現在diskを読む経路は記録時だけ」は一般化しすぎ。acceptance時の `capture_contract_loader_binding()` も全24 disk fileを読み、planはこれを残す。
- [s1-brief-measurements.md:20](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2008-d1163-closure-mismatch/s1-brief-measurements.md:20) — M3は確認できた。`_recorded_campaign_verifier_epoch()` → `_verify_committed_loader_binding()` → `verify_committed_contract_loader_binding()` が、記録commit blob SHAとauthority digestを各24 pathで実比較する。ただし保証はこのmapだけで、WAL verdict/receiptまでは含まない。
- [s1-brief-measurements.md:49](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2008-d1163-closure-mismatch/s1-brief-measurements.md:49) — consumer悉皆調査が不足。P2-2、critic/online digest、`plot_backoff.py`、`plot_s1_9pair.py` が抜けている。

## 同意した箇所

- D1163 が撤去を exact map mismatch 1条件に限定している点。
- `purpose` は引き続き必須で、既定値を持つwrapperは見つからなかった。
- exclusion decision のcoreは `_require_verifier_epoch_for_purpose()` に集約されたままである。
- committed commit/blob digest、preregistration、freeze、live capability、8b live contract checksは、それぞれのproduction surfaceでは実在し恒真ではない。
- legacy `E1-stale` enumをreaderに残す方針。
- proposed A/B mismatch acceptance testは、復活条件に対しては有効である。
- 実装・pytest・変異実走は行っていない。

## 総括

撤去条件そのものより、拡張後の `CertifiedCampaignView` を各consumerが何でcertifiedと判定するかが未防護である。
具体的にS6/S8Aはcommit存在だけでfailed/anomaly WALをcertified化できる。
historical markerはLayer3にしか届かず、主要なdigest・plot・provenance面に届かない。
5束縛検査は実在するが、共通certified read経路の保証は#1だけである。
このままのplanは規律2不変を証明していない。
