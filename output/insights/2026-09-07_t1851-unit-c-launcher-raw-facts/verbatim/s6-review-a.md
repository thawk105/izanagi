## blocker

### 所見 1 — 検査済み capture kwargs が再利用されず、D1113 に TOCTOU 窓がある

(a) [実測] `_checked_reservation_policy()` は `use_perf` / `reps` を検査しますが、その snapshot を捨てています。その後、genesis・reserve・pre-probe の後で `_capture()` が元の `measurement.keyword_arguments` を再度 `dict()` 化します。`FloorMeasurementCapture` が frozen でも内包する `Mapping` は可変であり、状態を変える Mapping や並行変更により、検査時と実 capture 時の値を変えられます。

(b) [実測] [s8b_floor_attempt_launcher.py:474](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_attempt_launcher.py:474)、同 :564-576、:584-598、:737-758。

(c) [推測] 放置すると receipt と異なる `use_perf`、または protocol と異なる `reps` で計測でき、sink・terminal・将来の certified 選択とレポート値が変わります。遅れて不正 key を検出した場合は、reserve 済み非 terminal 行も残ります。

(d) [推測] 所有 file `orchestrator/campaign/s8b_floor_attempt_launcher.py` で、検査時に作った exact kwargs copy を `_ReservationPolicy` に保持し、`_capture()` は元 Mapping を再読せずその copy だけを使ってください。所有 test fileには、pre-probe 中に元 Mapping を変更しても capture 値が変わらない対照を追加します。

### 所見 2 — launch failure の無い `open()` 例外を `observed` として受理できる

(a) [実測] classification reason は `open()` 前に確定します。`launch_failures=()` の状態で `open()` が例外になると、`failure.stage="open"` は設定されますが reason は `None` のままです。M12 test が使う `_terminal()` は `failure` を見ず、実際に `observed`、非 null observation、primary valueを返しています。

(b) [実測] [s8b_floor_attempt_launcher.py:765](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_attempt_launcher.py:765)、同 :791-828。[test_s8b_floor_attempt_launcher.py:270](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_floor_attempt_launcher.py:270)、同 :994-1012。旧 adapter は `failure_reason=None` を渡し、core の observed null matrix はこの組を拒否しません (`s8b_attempt_registry.py:2580-2593`、`attempt_registry_core.py:1021-1039`)。

(c) [推測] production caller 接続後は、decode failure や全 rep の open failureを、caller が作った throughputを持つ observed terminalとして台帳・レポート・certified 候補へ混入できます。現時点では production caller 0 件なので潜在経路です。

(d) [推測] 所有 launcher で、少なくとも `failure is not None` のとき `terminal_status=="observed"` を seal 前に拒否してください。特に `failure.stage=="open" and reason is None` は旧 v1 APIでは整合した failure terminalを作れないため、C1aでは明示的に fail-closed とし、terminalize は C1b の sealed APIへ送る必要があります。M12 testも observedを正例にしない形へ変更が必要です。

## must-fix

### 所見 3 — D1522 の下層直接検査に同一 test 内の正例対照がない

(a) [実測] `_checked_reservation_policy()` の直接 test は拒否例だけ、`_post_probe()` も不正例だけです。`_pre_observation_failure_reason()` は pre競合だけで、launch / None の直接対照がありません。`_external_evidence_sha256()` は両 probe の差だけを見ており、schema v2 と `capture_failure` の束縛を固定していません。marker の callable は source上に式がありますが、先行する marker 非 None gate により実行不能です。

(b) [実測] [test_s8b_floor_attempt_launcher.py:867](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_floor_attempt_launcher.py:867)、同 :875-895、:909-943。実体は launcher :413-451、:495-581。

(c) [推測] 放置すると下層 gateや evidence payload が弱体化しても別 testの緑で覆われ、classification receiptの参照や将来の terminal evidence digestが変わります。

(d) [推測] 所有 test fileで、各 helperの有効入力を同じ test内で成功させてから負例を与えてください。external evidenceは v2 literalを含む期待 payloadからdigestを計算し、`capture_failure` だけを変えた差も固定してください。

### 所見 4 — M5 は単一理由ではなく、後続 reps gateによる false KILLED になる

(a) [実測] M5 nodeは protocolを `{"reps": 3}` から `{"reps": 4}` へ変えています。この入力は protocol digestだけでなく、measurementの `reps=3` とも不一致です。digest gateを削除しても後続 reps gateが拒否し、pytestの message不一致によって testは赤になります。

(b) [実測] [test_s8b_floor_attempt_launcher.py:867](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_floor_attempt_launcher.py:867)、launcher :540-576。裁定の単一理由要件は `s4-adjudication.md:133`。

(c) [推測] 放置すると protocol digest gateを削除する変異が KILLED と誤記録されますが、`reps` を変えない別 protocolの未束縛受理を検出できず、台帳の protocol参照が変わり得ます。

(d) [推測] 所有 test fileで `reps=3` を維持したまま別 fieldだけを変更し、digest不一致だけを踏ませてください。冗長 gateに遮られる事前登録 nodeはM5だけです。

## 裁定 4節の逐条照合

| 項目 | 判定 |
|---|---|
| 1 reservation / marker forwarding | [実測] closed。必須4 field、4軸または5軸 slot、marker転送あり。 |
| 2 副作用前 policy | [実測] partial。呼出位置は副作用前だが、実 captureが検査済み snapshotを使わない。 |
| 3 v2早期 gate | [実測] closed。profile singletonまたはmarker非 Noneを専用署名で拒否し、v1 + Noneの全経路正例あり。 |
| 4 classification authority | [実測] closed。public引数なし、launcher定数とcanonical policy digestを使用。test seam注入だけ残る。 |
| 5 実行順序 | [実測] partial。指定順序、capture例外時post-probe、skip分岐は実装済み。open例外のobserved化が残る。 |
| 6 `OpenedFloorAttempt` | [実測] closed。exact 10 field、frozen、`open_error` / `post_probe`残骸なし。 |
| 7 私有 sink | [実測] closed。callerの `rep_observations` は拒否し、open成功後だけcopy snapshot。 |
| 8 test | [実測] partial。指定nodeは存在するが、D1522、M5、M12の正当性が未閉鎖。 |

## 変異 M1〜M12

| ID | 判定 |
|---|---|
| M1 / M2 / M3 / M4 | [実測] closed。指定nodeが対象分岐、snapshot、早期gate、public authorityを直接観測。 |
| M5 | [実測] partial。reps gateが冗長に遮る。 |
| M6 / M7 / M8 / M9 / M10 / M11 | [実測] 登録された対象変異についてclosed。なおM8/M10はcapture failureのdigest束縛までは観測しない。 |
| M12 | [実測] snapshot変異自体は観測するが、test terminalがopen failureをobserved化しており、他入力validの条件を満たさない。 |

## 段3採用所見

| 所見 | 判定 |
|---|---|
| A2 / B2 authority | [実測] partial。classification authorityとreceipt由来導出はclosedだが、capture kwargs再読によりD1113の等値が未閉鎖。manifest束縛は契約どおりC2/D2へ延期。 |
| A9 skip分岐 | [実測] closed。captureなし、post-probeなし、failureなし、launch failure空、terminalまで進む。 |
| B4 v2早期gate | [実測] closed。genesis / reserve / subprocess前に拒否。 |
| B9 fake契約 | [実測] C1a分はclosed。tokenは指定3属性を持ちopen時にsink更新。production seal検査は契約どおりC1bへ延期。 |

## 自己申告との照合

- [実測] 行数 `+220/-35`、`+400/-37`、新設17 node、総数29 nodeは現物と一致します。
- [実測] patchと統合済み2 fileのdiffは同一SHA-256です。
- [実測] 「use_perf / repsを一括検査」は所見1の再読により実 captureの束縛としては過大申告です。
- [実測] 「nested callableの下層直接検査」はprotocol / receiptにはありますがmarkerにはありません。
- [実測] M1〜M12の指定名は全て存在しますが、M5の単一理由性とM12のvalid入力主張は成立しません。
- [実測] pytestと自走harnessが未実走という申告は一致します。29/4件の独自direct-call、py_compile、checker実行はログやnodeidが添付されず、本reviewでは裏付け不能です。
- [実測] C1a patchの所有外変更は0 byteでした。ただしreview中に別時刻の `test_official_perf_closure.py +15` がlive worktreeへ追加されたため、最終時点のworktree全体は3 file modifiedです。C1a patch由来とは判定しません。
- [実測] `_CERTIFIED_MEASUREMENT_KEYWORDS`、probe argv / timeout / spawn symbol、capability封印、adapter / core / profileはC1a patch内で不変です。

## 総括

- [実測] blocker 2件、must-fix 2件、nit 0件。
- [実測] 主要な正順序、v2早期gate、launcher-owned authority、private sinkは実装済みです。
- [実測] D1113のactual capture束縛とopen failureのfail-closedが未達です。
- [実測] pytestは未実走です。
- [推測] 判定は **NO-GO**。blocker修正とD1522 / M5再固定後に再reviewが必要です。