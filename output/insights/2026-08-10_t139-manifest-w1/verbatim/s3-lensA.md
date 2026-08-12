# 判定: NO-GO

blocker 5 件、must-fix 3 件、nit 0 件です。指定資料と既存実装 4 ファイルはすべて読めました。ファイル変更・pytest 実行はしていません。

親 brief の実測値（`F_e` の祖先性、core の digest/450 行、221 行目の digest、既存実装 881 行、erratum 対象行）は再計算結果と一致しました。問題は実測値ではなく、そこから導いた承認・canonicality の一般化です。

## Blocker

### B1 — record-items 再発行版は `F_e` に承認されていない

D262 は現行 `record-items.md` の digest `1957026c…8fd3` を明示的に「approved_blobs」としています（[decisions.md:12125](/work/1/SFC/tanab/izanagi/docs/decisions.md:12125)）。一方プランは、新しい再発行版を artifact commit `A` に作りながら、manifest の `approval_fold_commit` に旧 `F_e` を使い、旧版を manifest 自身の `superseded_blobs` に落とします（[s2-plan.md:18](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-w1/s2/s2-plan.md:18)、[s2-plan.md:29](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-w1/s2/s2-plan.md:29)）。

これは承認ではありません。`F_e` より後に生まれた blob を `F_e` が digest-level で承認することはできず、manifest は canonical decision を上書きする権限を持ちません。

追補 A の先例では、D262 自身が再発行版を承認し（[decisions.md:12113](/work/1/SFC/tanab/izanagi/docs/decisions.md:12113)）、旧版を非承認と明記しています（[decisions.md:12133](/work/1/SFC/tanab/izanagi/docs/decisions.md:12133)）。今回は旧 record-items が既に承認済みなので、同じ先例ではありません。

必要な順序は `A → 新しい承認 decision の fold F_r → manifest M → gate G` です。現行の「同一 land」では `F_r` が post-land にしか生まれず、その前にある `M` は `F_r` を literal に書けません。wave/land 分割の再裁定が必要です。

**成果物影響:** D262 を読む validator は旧仕様を、manifest を読む resolver は新仕様を採用し、同じ receipt の適格 cluster 集合・レポート上の schema 参照が二分します。

### B2 — caller が binding・環境経由で trust root を選べる

提案された `PreregBinding` は manifest、errata、schema をすべて保持し（[s2-plan.md:418](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-w1/s2/s2-plan.md:418)）、`verify_receipt` はその binding を caller から受け取ります（[s2-plan.md:437](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-w1/s2/s2-plan.md:437)）。

`@dataclass(frozen=True, init=False)` は private constructor ではありません。caller は `PreregBinding()` を作り、`object.__setattr__` で任意の manifest/schema/errata を設定できます。「private factory invariant」だけでは生成元を証明できません。下位 API も schema ref を直接受けます（[s2-plan.md:212](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-w1/s2/s2-plan.md:212)）。

さらに既存 Git 層は `PATH` を継承し（[blobref.py:21](/work/1/SFC/tanab/izanagi/orchestrator/preregistration/blobref.py:21)）、`git` を名前解決して起動します（[blobref.py:162](/work/1/SFC/tanab/izanagi/orchestrator/preregistration/blobref.py:162)）。`PATH=/attacker/bin` から、公開済みの正しい pinned blob を返しつつ HEAD・祖先関係・未 pin の ledger 結果だけを偽る経路が残ります。

`verify_receipt` は binding の生成元を信用せず、内部で trusted manifest から binding を再解決して exact 比較する必要があります。Git executable と validator import root も trusted entry point が固定しなければなりません。

**成果物影響:** caller-selected schema/errata/ledger で canonical verifier が拒否する receipt を accepted にでき、certified 選択と proof-chain の参照が変わります。

### B3 — pilot gate の公開正例が構成されておらず、現行 public path は恒真 deny

計画では `G` が manifest v1 を固定し（[s2-plan.md:18](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-w1/s2/s2-plan.md:18)）、`load_approval_manifest(repository_root)` も public resolver も manifest ref を受けません（[s2-plan.md:80](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-w1/s2/s2-plan.md:80)、[s2-plan.md:433](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-w1/s2/s2-plan.md:433)）。その v1 の approved set は erratum-1 だけです。

プランが示す通過例は、private helper に synthetic v2 object を渡す例にすぎません（[s2-plan.md:274](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-w1/s2/s2-plan.md:274)）。repository に v2 を置いても、`G` が v1 を pin している public resolver は選びません。

したがって停止性の判定は次のとおりです。

- public `resolve_effective_preregistration`: **(i) 現行 G の全入力で停止**
- `verify_receipt`: B2 を直さない限り **(iii) forged binding で迂回可能**
- public signature を通る承認後の正例: **未構成**

D264 が棄却した「gate API の恒真 deny stub」（[decisions.md:12201](/work/1/SFC/tanab/izanagi/docs/decisions.md:12201)）と区別するには、新 approval fold、manifest v2、gate commit G2 の rotation 契約と、G2 の public resolver を通る正例が必要です。

**成果物影響:** 安全側では binding が永久に得られず pilot・receipt・certified 選択が全件不在になり、迂回側では未承認 erratum で投入できます。

### B4 — Q-A 第三分岐は厳密な受理拡大で、marker 無し attempt を捏造できる

旧仕様は `post_performance_failure` に marker または performance raw を要求します（[record-items.md:130](/work/1/SFC/tanab/izanagi/output/insights/2026-08-08_t139-addendum-a/record-items.md:130)）。新案はそこへ `a03_environment_observation` を追加します（[s2-plan.md:93](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-w1/s2/s2-plan.md:93)）。

したがって受理集合は、

```text
R_new = R_old ∪ {a03 failure observation を持つ receipt}
```

という厳密な拡大です。次の markerless receipt が新たに受理候補になります。

- `reason_code = post_performance_failure`
- `performance_started_marker = null`
- `actual_runs = []`
- preflight observation、`run_id_or_null = null`
- 7 列の `/proc/stat` 相当 bytes、負差分、または窓長逸脱を示す producer 作成 raw

プランは `stat_before[]` / `stat_after[]` / malformed state から再計算するとしていますが（[s2-plan.md:108](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-w1/s2/s2-plan.md:108)）、これらも producer の申告です。追補 A 自身が、producer が書く stdout/scheduler 出力は trust root にならないと説明し（[addendum-a-reissue.md:268](/work/1/SFC/tanab/izanagi/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:268)）、緩和には producer 権限外の collector が必要だとしています（[addendum-a-reissue.md:300](/work/1/SFC/tanab/izanagi/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:300)）。

固定 `J` の完全性 gate が正しければ、この捏造だけで false positive certification にはできません。しかし不利な実 run を markerless failure に変え、結果を reject/non-certifiable から `design_not_feasible` へ隠すことはできます。

**成果物影響:** certified 値を直接上げなくても、レポートの attempt 理由・観測値・「結果なし」という最終状態、および試行台帳の実行有無が偽造可能になります。

### B5 — `a13` の lock は canonical ledger を作らない

実装済み lock は Git common dir 内に作られ（[dev_wave_land.py:1365](/work/1/SFC/tanab/izanagi/tools/dev_wave_land.py:1365)）、`flock` で協調 land を排他化します（[dev_wave_land.py:1272](/work/1/SFC/tanab/izanagi/tools/dev_wave_land.py:1272)）。

これが防ぐのは次だけです。

- 同じ Git common dir を共有する linked worktree
- `dev_wave_land` を使う協調 writer
- 同じ local main 上での fold/append 競合

防げないものは次です。

- 独立 clone の別 common dir
- `dev_wave_land` を通らない直接 commit
- remote ref 間の競合や破棄された fork
- 過去の予約行を削除した後の再利用
- caller が `repository_root` で選んだ別 ledger

プラン自身も独立 clone を防げないと認めています（[s2-plan.md:384](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-w1/s2/s2-plan.md:384)）。「trusted consumer は一つの canonical main だけを見る」という運用境界は、固定された repository capability・remote/ref identity・append-only 全履歴検査として機械化されない限り、追補 A の「producer が選べない canonical な台帳」（[addendum-a-reissue.md:925](/work/1/SFC/tanab/izanagi/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:925)）を満たしません。

**成果物影響:** 二つの clone がそれぞれ `(F,1)` を唯一の予約として受理でき、台帳が二値化し、primary の実効 familywise error が約 `0.0731 > 0.05` になります。

## Must-fix

### M1 — D263 の「承認済み」誤記を registry membership へ伝播させてはならない

D263 は第 2 erratum が「既に承認済み」と誤記しています（[decisions.md:12170](/work/1/SFC/tanab/izanagi/docs/decisions.md:12170)）。現在の registry は erratum-1 しか持ちません（[erratum.py:357](/work/1/SFC/tanab/izanagi/orchestrator/preregistration/erratum.py:357)）が、プランは第 2 validator を登録しつつ manifest では draft とします（[s2-plan.md:242](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-w1/s2/s2-plan.md:242)、[s2-plan.md:30](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-w1/s2/s2-plan.md:30)）。

この区別自体は正しいものの、planned decision fragment は誤記を「説明誤り」と書くだけです。新 D で D263 の当該事実文を明示的に supersede し、状態を `validator_registered / draft_unapproved / approved` の三つに分ける必要があります。第 2 erratum の `approval_fold_commit` は新しい承認 decision の fold でなければならず、`F_e` や registry 登録を承認根拠にしてはいけません。

**成果物影響:** 誤記を権威と読む実装では第 2 erratum が早期適用され composed core と pilot 受理集合が変わり、保守的実装では反対に永久停止します。

### M2 — structured reason は pass/fail の分類語に留まっている

絶対規律 3 は「なぜ壊れたか」を次の一手へ渡すことを要求します（[CLAUDE.md:73](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w1/CLAUDE.md:73)）。

提案型では `stage` が自由文字列、`json_pointer` は任意、`context` は schema のない key-value tuple です（[s2-plan.md:449](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-w1/s2/s2-plan.md:449)）。たとえば `A03_FAILURE_EVIDENCE_MISMATCH` に pointer も attempt ID も計算値も無い reason が型上有効です。また `SchemaViolation` が持つ `validator` と `schema_pointer`（[s2-plan.md:199](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-w1/s2/s2-plan.md:199)）も `ReceiptReason` では必須になりません。

reason code ごとの discriminated union とし、最低でも attempt/run/observation ID、失敗 subtype、期待値、観測値、証拠 pointer を必須化すべきです。

**成果物影響:** accepted/rejected 集合が同じでも、材料レポートの破損理由と次 iteration の修正入力が別故障を同じ値へ潰し、同じ失敗を反復します。

### M3 — manifest identity の型と parser 署名が矛盾している

三段 commit では manifest identity は `G` の定数が与えます（[s2-plan.md:16](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-w1/s2/s2-plan.md:16)）。しかし `ApprovalManifest` は `manifest_ref` を必須 field に持ち、`parse_approval_manifest(blob)` は blob 以外を受けません（[s2-plan.md:64](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-w1/s2/s2-plan.md:64)）。

parser が JSON 内の `manifest_ref` を読むなら manifest の commit/digest 自己参照になり、caller 申告にもなります。読まないなら parser 単独では型を構成できません。`ParsedApprovalManifest` と、G-pinned ref を外側から付与する `LoadedApprovalManifest` を分離すべきです。

**成果物影響:** 実装選択によって manifest ref が caller-controlled または未定義になり、同じ manifest bytes から異なる proof-chain 参照が生成されます。

## 総括

現計画は実装へ進めません。GO に必要なのは次の五点です。

- 新 record-items を exact digest で承認する新 fold と、その後に置く manifest/gate のトポロジーを裁定し直す。
- binding を capability とみなさず、`verify_receipt` 内で trusted manifest から再解決する。
- manifest v2/G2 を含む public pilot 正例を構成し、現行 v1 の停止正例と対で固定する。
- Q-A の markerless 分岐には producer 外の証拠根を置くか、偽造可能性を明示して再裁定へ戻す。
- `a13` は単一 canonical authority と append-only 全履歴を機械的に束縛する。

以上が閉じるまで **NO-GO** です。