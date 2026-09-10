## 所見

1. [実測] **blocker** — E1 の二重導出は理論上 D1113 と前 wave 裁定を両立できるが、固定済み API では実装できない。固定 API は `observation/failure`・`sealed_session_record`・`finished_at` しか受けず（`output/.../verbatim/s2-plan.md:332-344`）、現行 handle は receipt bytes と raw-output digest までしか保持しない（`orchestrator/campaign/s8b_attempt_registry.py:163-185`）。raw facts が揃うのは launcher の token open 後（`orchestrator/campaign/s8b_floor_attempt_launcher.py:614-628`）だが、現行 terminal call は自己申告 terminal 値しか渡さない（同`:633-644`）。

   消去判定: 現状は raw-facts gate 自体が実装不能なので、その gate を消して赤になる production node はない。

   影響: このままなら sealed 自己申告から reason を作って前 wave 裁定を破るか、canonical bytes との束縛を捨てて D1113 を破り、試行台帳の terminal 値を certified 選択・材料レポートへ正しく渡せない。

2. [実測] **blocker** — `repetition_evidence` は production launcher から到達不能で、親 brief の成果物 scope には到達化に必要な launcher が入っていない。launcher の許可引数に `rep_observations` はなく（`orchestrator/campaign/s8b_floor_attempt_launcher.py:32-46`）、`_capture()` も private sink を作らない（同`:429-441`）。既存 test はむしろ明示指定を拒否する（`orchestrator/tests/test_s8b_floor_attempt_launcher.py:600-645`）。一方、brief は production 差分を core/profile/adapter の3ファイルに限定している（`brief.md:49-53`）が、plan 自身は launcher-owned sink を必要としている（`s2-plan.md:97-107`）。

   消去判定: 現行 production 正例は0件であり、validator を消して赤になる production-path test はない。直接 helper test だけなら恒真な保証になる。

   影響: brief の scope どおり実装すると observed・partial・dispersion の v2 terminal が production から一行も書けず、試行台帳と後続レポートは空のままになる。

3. [実測] **blocker** — `S8BClassificationPolicy` を `APPROVED_REPS` と `APPROVED_SESSION_CV_MAX` だけから作る「exact singleton」は不十分である（`s2-plan.md:105`）。rep integrity は `expected_use_perf` によって `complete` と `not_required` が変わり（`orchestrator/campaign/s8b_floor_campaign.py:1891-1968`）、その値は mode と perf-preflight receipt から実行時に導出される（同`:433-453,5911-5915`）。`s8b_approved.py:41-58` に対応する単一の `use_perf` pin はない。

   消去判定: plan の正例 P2～P5 は pilot/official の丧ოფを固定しておらず、この policy 軸を落として赤になる事前登録 node がない（`s2-plan.md:235-247`）。

   影響: official の欠損 counter を有効扱いするか、pilot の `not_required` を過剰拒否し、台帳の status/reason/primary value と材料レポートの採否が変わる。

4. [実測] **blocker** — E1 の単一 `probe_outcome` は既存 canonical session の全到達形を覆わない。plan は launcher の post-probe のみを事実源にする（`s2-plan.md:91-94`）が、campaign は pre-probe competition でも session を完成させる（`orchestrator/campaign/s8b_floor_campaign.py:6077-6089`）。post-probe competition は別経路で同じ `competing_process` になる（同`:6103,6147-6153`）。session schema も `probe_before` と `probe_after` の両方を持つ（`orchestrator/campaign/s8b_ratified_freeze.py:262-269`）。

   消去判定: plan の competition 正例 P3 は post-probe だけで、pre-probe terminal の正例 node がない（`s2-plan.md:241`）。

   影響: pre-probe で除外された正当な試行が台帳から欠落するか、不正な別原因へ写像され、試行台帳と session material の対応が変わる。

5. [推測] **blocker** — M3 の単独 `KILLED` 期待と、historical replay validator の完全性は両立しない（`s2-plan.md:202-204`）。D1113 を replay 時にも守るには、core validator が `sha256(serialize_session_line(sealed_record)) == raw_output_sha256` を再確認する必要がある。そうすれば producer 側の bytes equality だけを消す M3 は core にマスクされて `SURVIVED` する。逆に core がその比較を持たなければ、現行の digest 形式検査（`orchestrator/campaign/attempt_registry_core.py:892-896`）だけでは、sealed record/raw envelope を自己整合的に差し替えて rechain した historical row を拒否できない。

   消去判定: 完全な core replay validator を実装した場合、M3 単独を消して赤になる test node は存在しない。producer と replay の両層変異が必要である。

   影響: 未修正なら mutation 台帳が偽陽性になるか、sealed canonical bytes と試行台帳 terminal の参照が切れ、後続 proof chain が別内容を証明する。

6. [実測] **must-fix** — M8b は第三の symlink 防御を落としておらず、`KILLED` にならない。plan は新 helper と `_read_regular_bytes` の二層だけを消す（`s2-plan.md:209-210`）が、`_publish_create_only()` は `_write_staging()` を呼び（`orchestrator/campaign/s8b_attempt_registry.py:933-968`）、後者は `_ensure_durable_directory()` を介して親 component を再検査する（同`:840-895`）。

   消去判定: M8b 後も generation symlink test は `_ensure_durable_directory()` で赤のまま、すなわち変異は `SURVIVED` する。三層同時変異へ直す必要がある。

   影響: 二層だけで防壁を証明したと誤認すると、残る一層の将来退行時に registry publish path が外部へ向き、試行台帳の参照先が変わりうる。

7. [実測] **must-fix** — v2 retryable 集合の空集合 pin を更新するための追加ユーザー裁定は不要である。前 wave 裁定は A1' では空のまま、A2' で E1 validator と同時に4語を active 化すると明示している（`s4-adjudication.md:71-77`）。現行 test の空集合 assertion（`orchestrator/tests/test_attempt_registry_core_s8b_profile.py:2172-2216`）は A1' の暫定状態を固定したものにすぎない。plan の「裁定がなければ既存 test green 不可能」（`s2-plan.md:38-40,264-265`）は誤りである。

   影響: 放置すると承認済み E2 が人工的に停止し、v2 retryable terminal と後続測り直し台帳が開かない。

8. [実測] **must-fix** — marker capability へ渡す generation claim digest の供給規則が未記載である。固定 helper は `measurement_generation_claim_digest` を必須とする（`output/.../verbatim/s2-plan.md:292-311`）一方、公開 `reserve_attempt_slot()` の追加引数は `consumption_marker` だけで、残る digest は `admission_claim_digest` しかない（同`:313-330`）。marker の `use()` は generation digest を内部 identity と exact 比較する（`orchestrator/campaign/s8b_holdout_admission.py:322-368,5185-5217`）。

   影響: 両 digest の同一性規則を固定しないと、v2 reserve が恒常拒否されるか、誤った世代 claim に束縛された台帳行を作る。

9. [実測] **must-fix** — `record_sealed_classified_failure_terminal()` は既存 production/test caller とも0件であると plan 自身が認めている（`s2-plan.md:180-182`）。現行 launcher は classified failure も observation handle へ進め、legacy terminal 一箇所だけを呼ぶ（`orchestrator/campaign/s8b_floor_attempt_launcher.py:620-644`）。A2' は land しないため直ちに D1114 違反ではないが、C での具体的 caller か API 削除を land 前条件にする必要がある。

   消去判定: 新設 direct unit test 以外では、この API を丸ごと消して赤になる既存 node はない。

   影響: 呼び手なしで land すると classified-failure session が試行台帳へ反映されず、材料レポートとの terminal 参照が欠落する。

10. [実測] **nit（修正不要の確認結果）** — E3 を plan どおり実装する限り、v1 の既存受理集合は保存できる。新 field は keyword-only default `True`/`None`（`s2-plan.md:111-125`）、v1 factory と S8C constructor は既存引数のまま構築できる（`orchestrator/campaign/s8b_attempt_profile.py:577-626`; `orchestrator/campaign/trial_registry.py:2113-2164`）。`_assert_profile()` は s8b adapter 内だけの gate である（`orchestrator/campaign/s8b_attempt_registry.py:316-449`）。現行 production constructor は v2 を含めると `DomainProfile`/`TransitionPolicy` 各3件で、plan の数え直し（`s2-plan.md:161-165`）が正しい。

   影響: helper 抽出時に既存条件を変えなければ、v1 registry・claim v2・legacy marker・return type は不変である。

## 受理集合と4語

E1 の equality は新設 v2 candidate 集合を狭め、E2 は raw core では混合変更、E3/E4 の v2 profile・2段 path・sealed API は拡大である、という `s2-plan.md:218-233` の方向は概ね正しい。特に空集合から4語への E2 は `attempt_registry_core.py:953-977` のため拡大であり、前 wave の取り違えは残っていない。

ただし、固定 sealed API への raw-facts 引数追加または第9 API の追加（`s2-plan.md:82-87`）は、前 wave が固定した8 signature を広げる新しい public 面であり、受理集合表に載っていない。D番号または既裁定で直接承認された変更ではないため、plan が総括で返しているとおりユーザー裁定前には実装できない。

4 literal は、raw cause から独立導出し、`excluded_reason -> ledger reason` の辞書を権威にしない限り、凍結4語を capability として復活させるものではない。factory/profile/genesis/null-matrix の exact set が実装されれば閉集合も機械強制できる（`orchestrator/campaign/attempt_registry_core.py:690-702,953-977`; `s2-plan.md:48-63`）。したがって literal の綴り自体は親裁定で確定可能で、(P1-b) は real と判定する。ただし `measurement_execution_unavailable` の原因範囲と policy の不足は所見3・4を先に閉じる必要がある。

## 親 brief の誤り

11. [実測] **must-fix** — 直接 test の「50関数/78 node、35関数/59 node、合計153 node、consumer閉包172 node」（`brief.md:84-97`）は current HEAD では誤りである。静的 AST 展開では profile 55/86、adapter 47/74、equivalence 9/16、直接合計176 nodeであり、trial 225等を含む union は487 nodeとなる（`s2-plan.md:1-17`）。

   影響: 回帰面を314 node過少評価し、v1受理集合や台帳 consumer の退行を見逃す。

12. [実測] **nit** — E1 の「adapter terminal」アンカー `s8b_attempt_registry.py:1512-1713`（`brief.md:89`）は classification/claim publish blockであり、terminal 実体は `orchestrator/campaign/s8b_attempt_registry.py:1908-2010` にある。

   影響: terminal 値自体は変わらないが、検査参照が分類層へずれて E1 実装を見落とす。

13. [実測] **nit** — E4 の resume アンカーは `:1765-2071` で終わっている（`brief.md:96`）が、`resume_attempt()` 本体は `orchestrator/campaign/s8b_attempt_registry.py:2053-2367` まで続く。

   影響: claim/marker 再検証と handle 再構築の後半を scope から落とし、v2 resume の参照が不完全になる。

14. [実測] **blocker** — 成果物の production 差分を3ファイルに限定した記述（`brief.md:49-53`）は、launcher-owned repetition sink/raw carrier が必要という現物（`orchestrator/campaign/s8b_floor_attempt_launcher.py:429-441,614-644`）および plan（`s2-plan.md:97-107`）と矛盾する。

   影響: その scope では E1 の production terminal が到達せず、試行台帳へ有効な行が生まれない。

15. [実測] **nit** — DW-O09 の capability digest 説明（`brief.md:108-111`）は入力を「schema と binding」に縮めすぎている。実際の digest は schema version、freeze id、slot identity、binding fields 全体の canonical payload から導出される（`orchestrator/campaign/attempt_registry_core.py:263-274`; `orchestrator/campaign/s8b_attempt_profile.py:324-348`）。

   影響: v3 pin test が measurement/recovery ordinal を落とすと claim/capability の参照衝突を見逃す。

16. [実測] **must-fix** — 親の (P1-c) 解釈は「reason の値域は sealed record 由来でよい」とする（`brief.md:72-75`）が、前 wave 正本は status・reason・primary value のすべてを launcher-owned raw facts から返し、sealed record は比較専用とした（`s4-adjudication.md:46-69`）。

   影響: 親解釈のまま実装すると `excluded_reason` が台帳 reason の権威へ戻り、試行台帳の受理集合が自己申告方向へ広がる。

FROZEN_MANIFEST 23件・試行台帳0件という記述は正しい（`orchestrator/tests/test_frozen_artifacts.py:41-88,234-248`）。DW-G05 の「A2' 単独では最終成果物に発火しない」も、`launch_floor_attempt()` の production caller が0件で result がv4のままである現物と整合する（`orchestrator/campaign/s8b_floor_attempt_launcher.py:648-688`; `orchestrator/campaign/s8b_floor_contract.py:29-36`）。

## 総括

- blocker: 所見1（raw-facts API境界）、2（repetition evidence到達不能）、3（perf policy不足）、4（pre/post probe不足）、5（M3とhistorical replayの二者択一）、親 brief 所見14。
- 親 brief の誤り: test規模/閉包、adapter terminalアンカー、resumeアンカー、launcherを欠く成果物scope、capability digest入力の省略、(P1-c) のreason権威解釈。
- (P1-a): **refuted**。1 wave 見積りは過小。
- (P1-b): **real**。literalの綴りは親裁定可能。ただし原因/policy境界の修正が先。
- (P1-c): **refuted as written**。両裁定は理論上両立可能だが、固定8 signatureでは不可能。
- (P1-d): **refuted**。`repetition_evidence` は未到達で、単一 post-probe も既存 session 全形を覆わない。
- (P1-e): **real as future acceptance**。新規性能測定は不要。ただし test の実行場所は `tools/run_tests.py` の判定に従うべきで、この consult では実行していない。
- ユーザー裁定へ返すべき択一:
  - 推奨: 自由な raw kwargs ではなく、launcher が raw facts を snapshot して発行する evidence-bound handle を第9境界として追加し、resume可能な durable evidence digestも持たせる。代案は2 sealed APIへの raw kwargs追加だが、caller ownershipを機械強制しにくい。
  - `probe_outcome` を pre/post の組へ広げるか、pre-probe session を v2台帳対象外と明示するか。推奨は前者。
  - `expected_use_perf` を verified mode/perf-preflight evidenceへ束縛するか、v2台帳を単一modeに限定するか。推奨は前者。
- ユーザー裁定へ返す必要がないもの: 4 literal の綴り、A1'暫定空集合 test を4語 exact pinへ更新すること。
- 読めなかった必読資料: なし。
- 確かめられなかった事実: pytest結果、mutation実走結果、live Pegasus上の具体的probe/throughput値、親が記したrepo外probeの実走結果、実装後の確定LOC/node数。別worktree・親repoは読んでいない。