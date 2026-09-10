[実測] 静的検査のみ実施し、pytest は走らせていない。結論は、19 field 契約と plan はこのまま author 段へ渡せない。

## blocker

### 所見 1 — C1 単独では D1530 の「実際の呼び手」を繋いでいない

(a) [実測] 親 brief は「launcher を C1 に含めれば fragment 9 を満たす」とするが、fragment 9 が要求するのは launcher 自体ではなく、launcher の production caller を v2 台帳へ繋ぐ同一変更単位である。plan の C1a/C1b 後も campaign は `self.measure_fn(...)` を直接呼び、`launch_floor_attempt()` の production caller は 0 件のままである。

(b) [実測] `s1-brief.md:66-69`、`s2-plan.md:205-208`、`a2beta-decisions-fragment-9.md:13,30-45`、`orchestrator/campaign/s8b_floor_campaign.py:6213-6267`、`orchestrator/campaign/s8b_floor_attempt_launcher.py:648-670`。

(c) [推測] 放置すると C1b は terminal gate を active にした形を持ちながら、certified 選択・レポート・台帳の production 値には一度も発火しない。

(d) [推測] C1 を unlanded checkpoint として置くこと自体は可能だが、「D1530 達成」とは書かない。少なくとも C1b と C2 の production caller、journal repair、prefix capture を同じ最終 land 単位にし、C1 単独の完了判定を禁止する。

(e) [実測] (P1)。未解決なのは `mode`、`perf_preflight_receipt`、consumption marker、`campaign_record`、`finished_at`、`attempt_id`、raw-output bytes、resume 時の再読込である。

### 所見 2 — 19 field の policy 入力を campaign が選べる

(a) [実測] `protocol` は canonical digest を registry binding と照合すれば durable authority に束縛できる。一方、plan は `mode` と `perf_preflight_receipt` を `FloorAttemptReservation` へ campaign から直接渡すだけで、admission claim / manifest との等値を要求していない。

[実測] 同じ rep evidence に対し、`perf_preflight_receipt=None` なら `expected_use_perf=True`、valid な unavailable receipt なら `False` になりうる。これにより `_derive_rep_integrity()` の `complete` / `not_required` と terminal reason が変わるため、D1113 の「値を選べない」に直接触れる。

(b) [実測] `s2-plan.md:45-62,66-74,237-249`、`orchestrator/calibrator/perf_preflight.py:261-270`、`orchestrator/campaign/s8b_floor_stats.py:552-588`、`orchestrator/campaign/s8b_holdout_admission.py:1713-1725,4882-4919`、`orchestrator/campaign/s8b_attempt_registry.py:1932-1963`。

(c) [推測] receipt の差替えだけで同じ measurement が `observed` と `measurement_sample_incomplete` のどちらにもなり、terminal row、prefix head、将来の v5 report が変わる。

(d) [推測] launcher が campaign の mapping を受ける形をやめ、admission capability から再読した `mode`、manifest digest、manifest 内 receipt を使う。少なくとも receipt は manifest canonical bytes、mode は durable claim の `mode` と一致必須にする。

(e) [実測] (P1)、(P3)、契約 field `protocol` / `mode` / `perf_preflight_receipt` / `expected_use_perf`。

[実測] 追加 5 field の個別判定は次のとおり。

| 追加 field | 判定 |
|---|---|
| `protocol` | [推測] 採用。ただし full validation と `canonical_protocol_sha256(protocol) == binding.protocol_sha256` が必須。 |
| `perf_preflight_receipt` | [推測] 条件付き採用。manifest へ束縛されない現案は却下。 |
| `open_failure` | [推測] 採用。ただし capture 失敗と token-open 失敗を区別できないため、後述の stage 付き failure へ拡張する。 |
| `campaign_record` | [推測] terminal-first crash repairを採る場合だけ必要。全重複 field の等値検査が前提。 |
| `finished_at` | [推測] row 構築には必要だが、「認証済み」とする根拠は無い。launcher-owned clock または durable journal authority へ束縛する。 |

### 所見 3 — 提案された seal は `FloorPostProbeCapability` と同じ強さではない

(a) [実測] `FloorPostProbeCapability` は module seal に加えて、固定 callable が `_owned_post_probe` と同一であることまで検査する。提案された `_seal_terminal_evidence(document)` は、任意 document を検証して module seal を付けるだけである。campaign が private 関数を直接呼べるなら、内部整合した偽の raw facts から正規 handle を作れる。

(b) [実測] `s2-plan.md:214-228`、`orchestrator/campaign/s8b_floor_attempt_launcher.py:270-306`。より強い既存例は `orchestrator/campaign/s8b_attempt_registry.py:258-316` の issued-token、weakref、state fingerprint 検査である。

(c) [推測] 偽造 handle が sealed API へ届けば、虚偽だが内部整合した証拠から status / reason / primary を再導出でき、受理集合が自己申告方向へ広がる。

(d) [推測] document を直接受ける sealer を作らず、launcher 私有の capture/probe state を消費する issued handle にする。issuer table へ reservation binding、probe results、captured token identity、opened measurement snapshot の fingerprint を登録し、adapter 入口で exact object identity まで検査する。

(e) [実測] (P3)、契約 field 全体、D1113。

### 所見 4 — `require_terminal_reason_equals_classification=False` は core 直呼びの受理集合を広げる

(a) [実測] core の `terminal_row_validator` は terminal row 1 件しか受けず、evidence file を読めない。等値 gate を v2 だけ外すと、allowed E2 reason と形だけ正しい digest を持つ row は `core.load_attempt_registry()` / `core.record_attempt_terminal()` の直呼びで受理できる。adapter の artifact 検査はこの経路へ効かない。

[実測] plan の「lower validator spy」は validator が呼ばれたことしか証明せず、実在 file と再導出を core の受理条件にはしないため D1522 の代替にならない。

(b) [実測] `s2-plan.md:78-94,283-325,410-417`、`orchestrator/campaign/attempt_registry_core.py:1381-1408,1971-2054`、`orchestrator/campaign/s8b_attempt_profile.py:662-683`。

(c) [推測] adapter を迂回する test・将来 caller が、存在しない証拠 digestを持つ retryable terminal を作れ、台帳 prefix と将来の certified proof が変わる。

(d) [推測] 通常の v2 profile は引き続き core で無条件拒否し、実 evidence bytesを検証済みとする process-local capabilityを伴う専用 replay/write 経路だけを開く。D1522 test は「通常 core は拒否」「専用 lower path が実 bytes を再導出」「adapter がその lower path を実際に呼ぶ」の三段にする。

(e) [実測] (P4)、D1522、契約 field `terminal_evidence_sha256`。

### 所見 5 — 再導出 policy は現状では排他・網羅でない

(a) [実測] plan の表は最後を無条件 `otherwise -> observed` にしているが、相互矛盾する raw facts を先に拒否していない。少なくとも次が未定義または campaign と不一致である。

- [実測] `0 < exec_failures < reps` かつ完全 throughput、rep-integrity 失敗なし: plan は sample、campaign は `launch_failure`。
- [実測] `rep_integrity_failures > 0` かつ `assess_session()` が performance: plan は sample、campaign は performance。
- [実測] `launch_failures` 非空かつ `exec_failures == 0`: plan は `observed` へ落ちうるが、classification は `launch_failure`。
- [推測] pre-probe 競合なのに `probe_after` または measurement facts が存在する形、open failure と measurement facts の同居、opened session で `rep_integrity_failures is None` の形も `observed` へ落としてはならない。
- [実測] open 失敗 + probe-after 競合は environment、全 exec failure + CV 超過は execution、throughput 長不一致 + rep-integrity は sample となり、これら三例の precedence 自体は一致する。

(b) [実測] `s2-plan.md:98-124`、`orchestrator/campaign/s8b_floor_campaign.py:6296-6327`、`orchestrator/campaign/s8b_floor_stats.py:127-165,471-589`。

[実測] plan の「runner は非有限値を None に落とす」も完全ではない。`_num("1e999")` は実際に `inf` を返し、`ScalePoint.throughputs` に入りうる。`_journal_append()` は `allow_nan=False` でもない。根拠は `orchestrator/calibrator/benchparse.py:39-50`、`orchestrator/calibrator/runner.py:1003-1023`、`orchestrator/campaign/s8b_floor_campaign.py:1595-1606`。

(c) [推測] 矛盾 facts や overflow 非有限値が、拒否ではなく `observed` または campaign と異なる E2 reason になり、primary value・report session・terminal row が分岐する。

(d) [推測] policy の前に exact cross-field invariant を置く。`exec_failures`、launch failures、qualified throughput、rep-integrity は同じ private sink から相互再導出し、不一致は拒否する。非有限値は明示タグへ正規化するか、canonical 化前に sample-incomplete へ投影する。capture 自体の失敗を表す `capture_failure`、または `{stage: "capture"|"open", ...}` を追加する。

(e) [実測] (P4)、契約 field `launch_failures` / `open_failure` / `throughputs` / `exec_failures` / `repetition_evidence` / `rep_integrity_failures` / `session_cv_max`。

### 所見 6 — evidence は attempt に束縛されず、file-only 状態も plan は受理する

(a) [実測] 19 field に freeze / schedule / exact v2 slot / classification event / observation event の binding が無い。`protocol` は protocol digestだけを束縛するが、同一 facts の証拠を別 slot の terminal rowへ流用することを durable replay で区別できない。

[実測] また、要求された四状態のうち file あり・row なしを plan は明示的に正常な orphan として扱う。したがって「四状態をすべて replay で拒否」は満たさない。

(b) [実測] `s2-plan.md:11-31,132-142,424`、`orchestrator/campaign/s8b_attempt_profile.py:155-255,445-463`、`orchestrator/campaign/s8b_attempt_registry.py:1372-1427,1684-1735`。

(c) [推測] 別 attempt の証拠流用で受理された row の参照先と prefix headが変わる。また evidence 公開直後の crash では、rowから digestを引けず、どの orphanをresumeすべきか決められない。

(d) [推測] evidence に exact `registry_binding` を追加し、freeze/protocol/schedule、全5 slot軸、attempt ID、classification receipt/event、observation eventを row・claimと比較する。file-onlyを拒否する契約なら、slot-addressed pending indexを作り、replay は recoverable failureとして停止し、resume 後だけ terminalへ昇格させる。orphanを inert debris として許すなら、今回要求との相違を裁定へ返す。

(e) [実測] (P6)、契約 field `terminal_evidence_sha256` と不足 field `registry_binding`。

### 所見 7 — `campaign_record` の crash ordering と重複検査が未定義

(a) [実測] 現在の `_finish_session()` は mapping を返す前に journalへfsyncする。一方 plan は registry terminal 済み・journal sessionなしという terminal-first cutを前提に `campaign_record` を追加している。C2で `_finish_session()` を純粋 builderへ分割する記述が無い。

[実測] さらに plan が要求するのは `raw_output_bytes == serialize_session_line(campaign_record)` だけで、top-level `throughputs`、`exec_failures`、probe、rep evidence、identityと、`campaign_record` 内の重複 fieldの等値を要求していない。

(b) [実測] `s2-plan.md:61,128-130,350-356`、`orchestrator/campaign/s8b_floor_campaign.py:6346-6383`、`orchestrator/campaign/s8b_attempt_profile.py:566-577`。

(c) [推測] ledgerは正しい raw facts、journal/reportは改変した `campaign_record` という二重の真実を持てる。crash位置によってsession重複、欠落、または拒否済みsessionの先行永続化も起きる。

(d) [推測] C2で builderを無副作用化し、順序を「純粋record構築 → evidence公開 → terminal row → journal append」に固定する。resumeは rowのdigestからrecord bytesを再取得し、attempt IDでexact-once追記する。全重複 fieldを比較する変異を追加する。

(e) [実測] (P1)、(P6)、契約 field `campaign_record` / `raw_output_sha256` / `self_report` / `finished_at`。

## must-fix

### 所見 8 — v1 方針は妥当だが、既存 v2 genesis の非互換を明文化していない

(a) [実測] v1 event keysと空の `S8B_RETRYABLE_FAILURE_REASONS`を不変にし、旧terminal APIのv2拒否を残す方針は正しい。一方、E2を genesis の `retryable_failure_reasons` に入れると、pre-change v2 ledgerは新profileで全て再読不能になる。

(b) [実測] `orchestrator/campaign/s8b_attempt_profile.py:403-503,532-533,639-683`、`orchestrator/campaign/attempt_registry_core.py:780-790`、`orchestrator/campaign/s8b_attempt_registry.py:2536-2556,2605-2615`、`s2-plan.md:327-339`。

(c) [推測] 既存 v2 generation が外部共有rootに存在すれば、reader、resume、prefix inspectorが停止する。worktree内およびtrackedな該当registryは実測0件なので、現時点の成果物値は変わらない。

(d) [推測] 実装時に共有rootも含めたv2 generation在庫を検査し、0件をland条件にする。v1 exact bytes、旧API二層拒否、pre-change v2 genesis拒否、新v2 genesis 4語を別々にpinする。自動書換えはしない。

(e) [実測] (P4)、E2、v1不変契約。

### 所見 9 — pre-probe 所有の方向は正しいが、skip branch の型と再開規則が足りない

(a) [実測] 同じ固定 capability を前後2回呼べばspawn siteは1箒所のままであり、pre-probe競合時にcaptureしない方針は現campaignと一致する。ただし現在の `_DurablyClassifiedMeasurement` は必ずcaptured tokenを要求し、planのskip branchはその後のopen/build/sealへどう進むかを定義していない。

(b) [実測] `orchestrator/campaign/s8b_floor_attempt_launcher.py:189-208,548-645`、`orchestrator/campaign/s8b_floor_campaign.py:6241-6255`、`s2-plan.md:252-282`、`orchestrator/tests/test_ccbench_spawn_sites.py:212`。

(c) [推測] 分岐が曖昧なままだと、pre-probe競合slotがstartだけで残るか、誤ってcaptureが走り、coverageとterminal prefixが変わる。

(d) [推測] `captured=None` を許す専用classified stateを定義し、`probe_after=None`、launch failures空、measurement/open failureなしをexactに要求する。raw outputをsealしてからclassified-failure observation、sealed terminalの順で閉じる。

(e) [実測] (P2)、契約 field `probe_before` / `probe_after`。

### 所見 10 — (P5) の1 wave見積りは棄却が妥当

(a) [実測] planの再見積りはproduction 573〜793追加、test込み1,600〜2,300 changed LOCであり、親のproduction +400〜700、test +40〜70 nodeを超える。さらにpolicy、artifact、launcherの三境界が結合する。

(b) [実測] `s1-brief.md:85-87`、`s2-plan.md:146-157,199-208`、`a2alpha-README.md:104-116`。

(c) [推測] 1 waveを強制すると、artifact replayやcross-field矛盾testが削られ、受理集合の穴が残る可能性が高い。

(d) [推測] planのC1a/C1b分割を採る。ただし所見1のとおり、C1bとC2を同一最終land単位から外さない。

(e) [実測] (P5)。

### 所見 11 — 実アンカー、node数、DW-O09/O13に誤記がある

(a) [実測] 親briefの誤りは次の全件である。

- [実測] launcher: `FloorAttemptTerminal :123` は実際 `:126`、`_owned_post_probe :232` は `:238`、`_external_evidence_sha256 :350` は `:362`、`_pre_observation_failure_reason :366` は `:378`、`_launch_floor_attempt :527` は `:548`、terminal call `:628` は `:637`。
- [実測] campaign `_finish_session :6345` は `:6346`。
- [実測] `contract :34` は `SCHEDULE_ALGORITHM`で、result v4定義は `s8b_floor_contract.py:35-36`。
- [実測] 7 / 75 / 68 はnode数ではなくtest関数数。parametrize展開後は12 / 111 / 108。planのこの三値は正しい。
- [実測] campaign testは14,020行だが、328 nodeではない。静的ASTでは336 test関数、485展開node。
- [実測] DW-O13の「全fieldが現物に実在」はlauncher内については誤りで、`probe_before`、private sink snapshot、protocol、mode、receiptはまだreservation/opened carrierに無い。
- [実測] `expected_use_perf` のbool自体はreceiptから導出され、modeはofficial制約の受理可否に使われる。

(b) [実測] `s1-brief.md:92-114`、`s2-plan.md:159-178`、上記各production/test file。

(c) [実測] 行番号誤記自体は成果物値を変えないが、誤ったnode数は回帰面とwave規模を過少評価する。

(d) [推測] briefのanchor表とP1規模を実測値へ更新する。DW-O13は「下層に素材はあるがproduction launcher carrierは未実装、fake testはproduction到達性の証拠ではない」と書き換える。

(e) [実測] (P1)、(P5)、DW-O09、DW-O13。

## nit

### 所見 12 — production非発火の記述は概ね正しいがplan総括にも必要

(a) [実測] briefはproduction caller 0、既存certified値不変、landしないことを明記しており、C2/D2を実装済みと偽る記述もない。ただしplan総括はこの非保証を繰り返さず、「launcherのv2 call切替」だけが残る。

(b) [実測] `s1-brief.md:50-52,112-123`、`s2-plan.md:205-208,350-360,478-489`、`b2d1-README.md:98-103`。

(c) [実測] 現在のcertified選択・材料レポート・v4成果物は変化しない。

(d) [推測] plan総括へ「production caller 0、v5 producer 0、C1単独では効かない、landしない」を逐語で追加する。

(e) [実測] (P1)、D1114、D1341。

### 所見 13 — pre/post共用後も名前がpost専用のまま

(a) [実測] 同じ関数を2回使う設計なら動作とspawn-site pinは正しいが、`FloorPostProbeCapability`、`_owned_post_probe`、エラー文がpost専用のため、pre-probeの所有主体を読み違えやすい。

(b) [実測] `orchestrator/campaign/s8b_floor_attempt_launcher.py:95-103,238-306`。

(c) [実測] 成果物の値・受理集合には影響しない。

(d) [推測] capabilityと内部関数をneutralなcompetition probe名へrenameし、spawn inventoryのsymbol pinだけ追随させる。

(e) [実測] (P2)。

## 裁定パッケージ候補

### 所見 14 — D1533の非保証をresult.mdへ載せる所有がbriefから落ちている

(a) [実測] 直前waveは、台帳削除後の同一bytes再作成を検出しない旨をresult.mdへ載せる所有者を単位Cとした。親briefはD1533を列挙するだけで、C2 deliverableへ入れていない。

(b) [実測] `b2d1-README.md:98-109`、`s1-brief.md:18-23,50-52`。

(c) [推測] 放置すると新v5 reportが、実際には防いでいない削除・再作成耐性を持つように読まれる。

(d) [推測] C2またはD2の明示taskとしてresult.md非保証文を追加する。所有をD2へ移すなら裁定に残す。

(e) [実測] (P1)、D1533。

### 所見 15 — D2の動的 `RESULT_SCHEMA` fixture方針が未回収

(a) [実測] 直前waveが返した `s8b_v2_freeze_fixture.py:340` と `test_s8b_ratified_verify.py:460` の選択は、親brief・planのC2/D2境界に具体化されていない。

(b) [実測] `b2d1-README.md:108-110`、`orchestrator/tests/s8b_v2_freeze_fixture.py:340`、`orchestrator/tests/test_s8b_ratified_verify.py:460`。

(c) [推測] `RESULT_SCHEMA` をv5へ切り替えた時点で、legacy fixtureが意図せずv5を名乗るか、proof欠落で拒否される。

(d) [推測] D2裁定へ戻し、legacy v4へ固定するfixtureと、実v5 proofを組むfixtureを明示的に分ける。

(e) [実測] (P1)、C2/D2境界。

## 総括

- [実測] blocker 7件、must-fix 4件、nit 2件。
- [実測] 19 field契約は未完成。`registry_binding`、manifest-bound perf authority、capture/open failure stage、exec-failureの再導出源が不足する。
- [推測] `campaign_record` はterminal-first repairを採る場合だけ必要で、現状は重複面が過大。
- [推測] (P1) 条件付き。C1はunlanded checkpointに限り可、D1530達成はC2接続後。
- [推測] (P2) 条件付き採用。skip branchのexact stateとresumeを追加する。
- [推測] (P3) 条件付き採用。document sealerではなくissued provenance handleにする。
- [推測] (P4) 却下。2状態とE2は採用できるが、core equality解除案は不可。
- [推測] (P5) 却下。planのC1a/C1b再分割を採る。
- [推測] (P6) 却下。attempt binding、file-only crash規則、全replay入口が不足する。
- [実測] 既存v1 bytesとcertified v4成果物は現時点では変わらず、production gateも0発火である。