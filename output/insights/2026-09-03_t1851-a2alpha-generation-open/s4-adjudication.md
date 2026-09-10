# 段 4 裁定 — [T-1851] 台帳配線 3 task 閉包 / 実装単位 A の後半 A2'

2026-09-03 JST。branch `worktree-dev-wave-t1851-unit-a`、HEAD `27e93b911` (local main `dc9a060d3` 取り込み後)。
材料 = 段 2 plan (266 行)、段 3 レンズ A (所見 16 + 総括)、レンズ B (所見 10 + 総括)。

裁定 inbox 再走査: wave 開始後に main が `431e0d6d8` → `dc9a060d3` へ進み、D1517〜D1557 が着地した。
**このうち 2 件は本 wave の設計を拘束する新事実である** (D1522、D1530)。下記 4 節で扱う。
承認済み裁定 (D1113 / D1193 / D1194 / D1337 / D1340 / D1341 / D1342) を覆すものは無い。

## 結論 — 実装する。ただし A2' を A2α と A2β へ分割し、本 wave は A2α だけを積む

`4→5→6→7→8→9` で進む。**段 9 で land しない** (D1341)。

**A2α = E3 + E4 の構造面 (path 世代分岐 / create-only publish / claim v3 / capability 消費 / v2 resume)。**
**A2β = E1 + E2 + sealed terminal API 2 本 + 起動層の証拠 carrier。ユーザー裁定を先に要する。**

依頼は E3 を必須と名指した。A2α はそれを含む。E1 / E2 を本 wave から外すのは、**下記 4 件の
blocker が承認済み裁定の前提を覆したためであり、規模を理由に縮めたのではない。**

## 1. (P1-a) は反証された — 1 wave に収まらない

[実測] 両レンズが独立に測り、plan と合わせて 3 者が一致した。A2' 全体は
**1,380〜1,900 changed LOC / 新設 110〜145 node / 既存回帰 487 node** である。
既存回帰の内訳は直接 176 (profile 86 + adapter 74 + equivalence 16) + trial_registry 225 +
launcher 12 + holdout 72 + scheduler 1 + campaign helper 1 の union である。

親 brief の「約 800〜1,000 LOC / 1 実装子」は過小で、A1' の実績 900 LOC より確実に大きい。
**(P1-a) refuted。採用する。**

## 2. 親候補の分割 (E1+E2+E3 / E4) は反証された。境界を作り直す

[実測] plan が現物で反証した。E3 が v2 を受理した後も `create_attempt_registry()` は
`_assert_profile` の後に protocol を渡さず `_entry_paths()` を呼ぶ
(`s8b_attempt_registry.py:1343-1350`)。v2 profile の root は `{protocol_sha256}` を含む 2 段 path
である (`s8b_attempt_profile.py:516-523`)。**E3 を E4 の path 分岐より先に開けば v2 が誤った
1 段 destination へ進む。**

[実測] レンズ B はさらに `_assert_state_path()` 内の `_entry_paths()` 呼出し
(`s8b_attempt_registry.py:522`) を plan が数え落としていたことを掴んだ。全 handle 使用時に走る
ので、これも同じ変更単位に入る。`_entry_paths()` の呼出しは全 11 件
(`:508,522,1346,1378,1428,1583,1808,1922,1973,2027,2115`)。

**したがって E3 は E4 の path 分岐と同じ変更単位でしか開けない。** これが新しい境界の主軸である。

## 3. A2α の scope (本 wave が実装する)

| # | 内容 | 受理集合の方向 |
|---|---|---|
| S1 | core の `DomainProfile` へ `terminal_row_validator: Callable[[Mapping], None] \| None = None` (kw-only)、`TransitionPolicy` へ `retryable_terminal_opens_next_attempt: bool = True` (kw-only) を足す。既存 production constructor 3 件ずつ (v1 factory / v2 factory / S8C) は text 変更ゼロ | 不変 (default が現行挙動) |
| S2 | core の terminal 経路 (`attempt_registry_core.py:1310` 付近) で null matrix と classification equality の後に `terminal_row_validator(row)` を呼ぶ。`None` は完全な no-op | 不変 (v1)、狭まる (v2) |
| S3 | core の次 ordinal 経路 (`:1106-1144`) で `retryable_terminal_opens_next_attempt is False` なら retryable terminal が次の attempt を開かない | 不変 (v1)、狭まる (v2) |
| S4 | **`_assert_profile()` を schema 別 exact validator 化する (E3)。** 比較本体を `_assert_exact_profile(profile, expected)` へ機械抽出し、`profile.schema is S8B_SCHEMA_PROFILE` / `is S8B_V2_SCHEMA_PROFILE` で factory を分ける。それ以外は fail-closed。exact 比較に S1 の 2 field を含める | 広がる (v2 のみ)、v1 不変 |
| S5 | **v2 factory の `terminal_row_validator` を fail-closed stub にする。** v2 の terminal 行を無条件に拒否し、署名は `[s8b-v2-terminal] v2 terminal requires the sealed evidence API` とする。A2β がこれを E1 の raw-facts validator へ差し替える | 狭まる (v2 terminal を全拒否) |
| S6 | adapter の legacy terminal 入口でも v2 profile を明示拒否する。**S5 と S6 は別層であり、片側変異は SURVIVED、両層同時は KILLED として対で事前登録する** | 狭まる (v2) |
| S7 | `_entry_paths()` の protocol 分岐を全 11 呼出しへ通す。v2 は state に保存した generation path を使い、1 段 path を再計算しない | 不変 (v1)、狭まる (v2) |
| S8 | `_publish_registry_generation_create_only(*, root, path, payload)` を新設する。既存 destination・64 hex symlink・非 directory・不完全世代を拒否する | 狭まる |
| S9 | `_slot_address_payload_v3(*, binding, slot)` と claim v3 の schema / key set / reader / writer を新設する。address は freeze / protocol / schedule binding、freeze-holdout / configuration / repetition / measurement / attempt ordinal、schedule-row digest を含める。**v1 claim v2 の reader と filename digest は 1 byte も変えない** | 広がる (v2)、v1 不変 |
| S10 | `_assert_consumed_marker` を `_assert_legacy_consumed_marker` へ rename し内容不変。v2 は capability path へ分岐する | 不変 |
| S11 | `_atomic_update_with_consumption_marker(...)` を境界 signature どおり新設する。prelock hook は lock 取得前にちょうど 1 回。`_atomic_update_locked` に lock 生存 guard を置く | 狭まる (v2) |
| S12 | `reserve_attempt_slot(..., consumption_marker=None)` と `resume_attempt(..., consumption_marker=None, ...)` を境界 signature どおり拡張する。**v1 は `None` で受理し、v2 は marker 必須で拒否する** | 不変 (v1)、狭まる (v2) |

**本 wave では E1 (raw facts projection)、E2 (4 語 active 化)、`record_sealed_attempt_terminal`、
`record_sealed_classified_failure_terminal` を実装しない。** v2 の retryable 集合は空のまま置き、
A1' が書いた空集合 pin (`test_attempt_registry_core_s8b_profile.py:2172-2216`) も変更しない。

## 4. 新しい裁定 2 件の適用 (main 側で本 wave 開始後に着地)

- **D1522 を全面採用する。** 上流の層で受理集合を縮めた結果、下層の防壁を検査していた既存テストが
  その防壁へ到達しなくなる場合、**テストを上流の拒否期待へ移設してはならない。** 下層の実体を
  名指しする直接検査へ作り直し、差し替えが実際に呼ばれたことを assertion で固定し、
  差し替えなしで成功する正例対照を同じテストに置く。
  本 wave で該当するのは S2 / S5 / S6 (core validator と adapter 入口の二層)、S7 / S8
  (symlink 防壁の多層)、S11 (lock 生存 guard と admission 側再検査の多層) である。
  **上流が拒否するから下層は検査しない、という形を実装子に許さない。**
- **D1530 を A2β の裁定材料として採る。** 「未接続の interface の権威束縛は、本番の呼び手を
  繋ぐ変更と同じ単位で行う」。E1 の raw-facts validator は起動層の carrier が無ければ到達不能で
  あり、carrier は単位 C の所有である。**E1 を carrier と別単位で先に建てると、D1530 が却下した
  「使われない防壁を先に建てる」に当たる。** これが E1 を A2β へ送る 2 つ目の根拠である。

## 5. real / refuted の裁定

### real・採用 (A2α の scope に入れる)

- [レンズ B 所見 3] `_assert_state_path()` の `_entry_paths()` 呼出し `:522` の数え落とし。**S7 に含める。**
- [レンズ A 所見 6 / レンズ B 所見 6] symlink 防壁は二層でなく四層 (`_read_regular_bytes`、
  `_ensure_durable_directory`、`_write_staging`、admission の guarded writer) で過剰決定される。
  **変異は多層同時変異へ組み直す (DW-M04)。M7a 単層 = SURVIVED、M7b 全層 = KILLED を対で事前登録する。**
- [レンズ A 所見 8] marker capability へ渡す `measurement_generation_claim_digest` の供給規則が未定。
  **裁定: adapter が v2 claim payload から導出する。公開 API の呼び手から受け取ってはならない。**
  D1113 の「呼び手が権威値を選べてはならない」と同じ形である。S9 / S11 に含める。
- [レンズ A 所見 10] E3 は v1 の受理集合を保存できる。**確認として採用する。**
  保証は (i) 旧 comparator 本体を再実装せず抽出する、(ii) 既存 14 変異 + 新 field 2 変異の
  exact matrix、(iii) 既存 adapter 74 node の 3 つで固定する。
- [レンズ B 所見 10] 新規 test file を作るなら `test_plain_runner_coverage.py:44-93` の
  file 集合列挙 meta-test が焦点走に入る。**採用。実装子へ明示する。**
- [レンズ B 所見 7 / レンズ A 所見 5] KILLED 期待の変異に exact nodeid が割り当てられていない。
  **採用。事前登録表で全変異に kill する node を名指しする。**

### real・A2β へ送る (本 wave は実装しない。境界だけ固定する)

- [レンズ A 所見 1 / レンズ B 所見 1] **E1 の固定 8 signature は生の事実を運べない。**
  2 つの sealed API は `observation/failure`・`sealed_session_record`・`finished_at` しか受けず、
  現行 handle は receipt bytes と raw-output digest までしか保持しない
  (`s8b_attempt_registry.py:163-185`)。生の事実が揃うのは launcher の token open 後
  (`s8b_floor_attempt_launcher.py:614-628`) だが、現行 terminal call は自己申告値しか渡さない
  (`:633-644`)。**前 wave が固定した境界 signature のままでは、前 wave 自身が承認した
  「生の事実から再導出する」を実装できない。裁定パッケージ 1。**
- [レンズ A 所見 2 / レンズ B 所見 1] **`repetition_evidence` は production 起動層から到達不能。**
  許可引数に `rep_observations` が無く (`s8b_floor_attempt_launcher.py:32-46`)、`_capture()` も
  private sink を作らない (`:429-441`)。既存 test はむしろ明示指定を拒否する
  (`test_s8b_floor_attempt_launcher.py:600-645`)。**DW-O13 に従い、到達不能な入力を要求する
  validator は採用しない。** 到達化には起動層の変更が要り、それは単位 C の所有である。裁定パッケージ 1。
- [レンズ A 所見 3] `S8BClassificationPolicy` を `APPROVED_REPS` と `APPROVED_SESSION_CV_MAX` だけ
  から作る案は不十分。rep integrity は `expected_use_perf` により `complete` と `not_required` が
  変わり (`s8b_floor_campaign.py:1891-1968`)、その値は mode と perf-preflight receipt から実行時に
  導出される (`:433-453,5911-5915`)。対応する単一 pin は `s8b_approved.py:41-58` に無い。裁定パッケージ 2。
- [レンズ A 所見 4 / レンズ B 所見 1] **単一 `probe_outcome` は既存 session の全到達形を覆わない。**
  campaign は計測前 probe の competition でも session を完成させ (`s8b_floor_campaign.py:6077-6089`)、
  計測後 probe の competition は別経路で同じ `competing_process` になる (`:6103,6147-6153`)。
  session schema は `probe_before` と `probe_after` の両方を持つ (`s8b_ratified_freeze.py:262-269`)。裁定パッケージ 2。
- [レンズ A 所見 9] `record_sealed_classified_failure_terminal()` は production / test とも呼び手 0 件。
  A2β で単位 C の具体的呼び手を名指しできるか、API を落とすかを land 前条件にする。裁定パッケージ 1。
- [レンズ B 所見 2] B1 の capability を v2 reserve へ渡す production handoff が無い
  (`FloorAttemptReservation` に marker field が無い)。**adapter 側 API は A2α で完成させるが、
  起動層の配線は単位 C の所有である。** A2α では「v2 は marker 必須で、無ければ拒否」までを実装し、
  呼び手を作らない。D1530 と D1341 により、これは片側 land にならない。

### refuted・不採用

- [plan 2 節] 「A2α の既存 test green はユーザー裁定待ちで満たせない」。**両レンズが独立に反証した。**
  前 wave 裁定は A1' では空集合のまま、A2' で E1 validator と同時に 4 語を active 化すると
  明示している (`s4-adjudication.md:71-77`)。現行の空集合 assertion は A1' の暫定状態を固定した
  ものにすぎず、その supersede に追加のユーザー裁定は要らない。
  **ただし本 wave は E2 を実装しないので、この論点は A2β で閉じる。**
- [plan 2 節] 分割候補 A2α = `E1+E2+carrier` / A2β = `E3+E4`。**逆にする。**
  plan の順序は、blocker がすべて前半に集中する。前半はユーザー裁定なしに着手できない。
  後半 (E3+E4) は裁定待ちが 1 件も無く、依頼が必須と名指した E3 を含む。
  **裁定待ちの部分を先に置く分割は、wave を空回りさせる。**
- [親 brief (P1-c) の解釈] 「reason の値域は sealed record 由来でよい」。**レンズ A 所見 16 が
  正しく、親の解釈は誤りである。** 前 wave 正本は status・reason・primary value のすべてを
  起動層所有の生の事実から返し、sealed record は比較専用とした。親解釈のまま実装すると
  `excluded_reason` が台帳 reason の権威へ戻り、受理集合が自己申告方向へ広がる。**訂正して採る。**

## 6. 親 brief の誤りの訂正 (両レンズが指摘、全件採用)

1. **production の変更先から `s8b_floor_attempt_launcher.py` が欠落していた。** A2β では必須。
   A2α では起動層を変更しないので、A2α の成果物は core / profile / adapter の 3 file で正しい。
2. test 規模「50/78 + 35/59 + 9/16 = 153 node、consumer 閉包 172 node」は **A1' 以前の古い値**。
   現物は profile 55/86、adapter 47/74、equivalence 9/16 の直接 176、launcher 込み 188、
   consumer union 487 である。**314 node を過少評価していた。**
3. E1 の adapter terminal アンカー `s8b_attempt_registry.py:1512-1713` は classification / claim
   publish block である。terminal の実体は `:1908-2010`。
4. E1 の core terminal アンカー `attempt_registry_core.py:1814-1897` は途中までしか覆わない。
   実体は `:1877-1960`。
5. E4 の resume アンカー `:1765-2071` は途中で切れている。`resume_attempt()` 本体は `:2053-2367`。
   claim 前半 `:1017-1108` も落ちていた。
6. 起動層アンカーに書いた `_terminal_*` は現物に無い。実体は `:114-142,614-644`。
7. DW-O09 の capability digest の入力を「schema と binding」に縮めすぎていた。実際は
   schema version、freeze id、slot identity、binding fields 全体の canonical payload から導出される
   (`attempt_registry_core.py:263-274`、`s8b_attempt_profile.py:324-348`)。
8. (P1-c) の解釈が誤り (5 節に記載)。

**誤りでなかったもの:** `FROZEN_MANIFEST` 23 件・試行台帳 0 件、E2 の null matrix の向き
(空集合は raw core で恒真拒否)、E3 の direct call site 5 件、DW-G05 の「A2' 単独では最終成果物へ
発火しない」。いずれも両レンズが現物で確認した。

## 7. 設計点の裁定

- **(P1-b) 採用。** 台帳専用 4 語の literal は親裁定で確定してよい。両レンズが独立に real と判定した。
  D1113 は語彙が閉じていることと機械導出だけを定め、綴りを凍結していない。
  **ただし本 wave は E2 を実装しないので、literal の確定は A2β で行う。** 現時点で採る候補は
  `measurement_environment_conflict` / `measurement_execution_unavailable` /
  `measurement_sample_incomplete` / `measurement_dispersion_exceeded` とし、
  `excluded_reason -> ledger reason` の辞書を権威にしない (生の原因から独立導出し、
  自己申告は比較にだけ使う)。レンズ A が付けた条件 (所見 3・4 を先に閉じる) を A2β の前提とする。
- **(P1-c) refuted as written。** 二重導出そのものは両立形として成立するが、固定 8 signature では
  運べない。裁定パッケージ 1 で返す。
- **(P1-d) refuted。** 到達不能な入力を要求する validator を実装しない (DW-O13、D1114)。
- **(P1-e) 維持。** login node の焦点走 + 受入全走。新規 Pegasus 実行体を要する実測は無い。
- **v2 terminal の暫定 fail-closed (S5/S6) について。** これは「謳うだけで発火しない保証」ではない。
  v2 に対して常に発火し、v1 に対しては発火しない。正例対照 (v1 terminal が通る) と
  負例 (v2 terminal が exact 署名で拒否される) を同じ test に置く。A2β が E1 の validator へ
  差し替えるとき、この pin を supersede することを A2α の insight に明記する。

## 8. 変異事前登録 (DW-M01 / DW-M04 / D1522)

実装前に登録する。**KILLED 期待の変異には kill する test を名指しする。**
**多層で過剰決定される防壁は、単層 SURVIVED と多層同時 KILLED を必ず対で登録する (DW-M04)。**

| ID | 変異 | 期待 | kill する検査 / 単一理由性の根拠 |
|---|---|---|---|
| M1 | `_assert_profile` の schema dispatch を消し v1 factory 固定へ戻す | KILLED | v2 profile を create / read / reserve / resume / handle の 5 入口へ渡す新設 node。v2 を受理する層は他に無い |
| M2 | `_assert_profile` の `terminal_row_validator` identity 比較を消す | KILLED | `dataclasses.replace(v2_profile, terminal_row_validator=None)` を拒否する新設 node。この無効化を止める層は他に無い |
| M3 | `_assert_profile` の `retryable_terminal_opens_next_attempt` exact 比較を消す | KILLED | 同 field を偽造した v2 policy を拒否する新設 node |
| M4a | adapter legacy terminal の v2 拒否 (S6) だけ消す | **SURVIVED (mask)** | core の `terminal_row_validator` (S5) が同じ入力を拒否する |
| M4b | M4a + core の `terminal_row_validator` 呼出し (S2) を両層同時に消す | KILLED | DW-M04。v2 の自己申告 terminal 行が受理される。**core を直接呼ぶ replay node で kill する (D1522)** |
| M5 | `_assert_state_path()` (`:522`) の protocol 分岐だけ消す | KILLED | v2 handle が classify / observe / terminal 入口で path 不一致になる新設 node。他の 10 呼出しはこの入口を通らない |
| M6 | create-only publish の既存 destination 拒否を消す | KILLED | 既存世代への再 publish を拒否する新設 node (D1533 の範囲) |
| M7a | generation publish の parent symlink 検査だけ消す | **SURVIVED (mask)** | `_read_regular_bytes` / `_ensure_durable_directory` / `_write_staging` / admission guarded writer が再検査する |
| M7b | M7a + 上記 4 層を同時に消す | KILLED | DW-M04。complete generation symlink が publish 対象になる |
| M8 | `_slot_address_payload_v3` から `measurement_ordinal` を落とす | KILLED | measurement だけ異なる 2 claim が同じ create-only path へ衝突する新設 node |
| M9 | claim v3 の `protocol_sha256` 比較を消す | KILLED | exact key gate は値を見ず、receipt / core row にも claim field との equality は無い |
| M10a | `_atomic_update_locked` の lock 生存 guard だけ消す | **SURVIVED (mask)** | `marker.use` と `_current_floor_attempt_consumption_identity_locked` が同じ lock を再検査する (`s8b_holdout_admission.py:5009,5172`) |
| M10b | M10a + admission 側の再検査を同時に消す | KILLED | DW-M04。inactive / 偽造 lock で action が実行される |
| M11 | v2 resume の marker 分岐を legacy raw marker reader へ戻す | KILLED | 現世代の正常 resume が legacy exact key set で拒否される新設 node |
| M12 | prelock hook を `_atomic_update_locked` の中へ移す | KILLED | 既存 rendezvous test が lock 前の読みを要求する |
| M13 | `reserve_attempt_slot` の v2 marker 必須検査を消す | KILLED | marker なしの v2 予約を拒否する新設 node。marker を要求する層は他に無い |

**過剰拒否の正例 (DW-M01)。** 次はいずれも通らねばならない。

- P1: 正規 1 段 v1 の世代だけを持つ root で、start / classify / observe / terminal / resume が従来どおり通る。
- P2: v1 の legacy consumed marker 経路が `consumption_marker=None` のまま従来どおり通る。
- P3: v2 の create / reserve / claim v3 / resume が、正しい marker と generation claim digest で通る。
- P4: freeze 直下に非 64 hex の sibling file があっても、列挙と mutation が通る。
- P5: v1 の terminal が通る (S5/S6 の v2 拒否の裏。過剰拒否になっていないことの対照)。

## 9. 実装子への分割

**1 単位 1 実装子とする。** S1 の core field を S4 の `_assert_profile` が消費し、S7 の path 分岐を
S8/S9/S11/S12 が消費し、S9 の claim v3 payload を S11 の generation claim digest が消費する。
**producer/consumer 契約が単位を跨ぐので並列に分けると契約が壊れる** (A1' と同じ判定、
レンズ B も「並列分割は不可」と独立に判定した)。

規模は約 740〜1,030 changed LOC、新設 test 60〜85 node で、A1' の実績 (約 900 行 / fix 1 巡で収束)
と同程度である。

## 10. ユーザーへ返す裁定パッケージ

1. **E1 の境界 signature を補正してよいか。** 前 wave 段 4 が固定した 2 つの sealed terminal API は
   `observation/failure`・`sealed_session_record`・`finished_at` しか受けないため、**前 wave 自身が
   承認した「起動層所有の生の事実から再導出する」を実装できない。** 3 者 (plan・レンズ A・レンズ B)
   が独立に同じ結論に達した。選択肢は次の 3 つで、**受理面と public API 面を広げる方向なので
   親だけでは選べない。**
   - (推奨) 起動層が生の事実を snapshot して発行する **evidence-bound handle** を第 9 の境界として
     追加し、resume 可能な durable evidence digest も持たせる (レンズ A の推奨)。
     呼び手の所有を機械強制しやすい。
   - 2 つの sealed API へ `probe_outcome` / `throughputs` / `execution_failures` /
     `repetition_evidence` の keyword-only 引数を直接足す (plan の推奨)。実装は短いが、
     呼び手が値を選べる形になりやすく D1113 の主旨から遠い。
   - 境界を変えず、E1 を単位 C と同じ変更単位へ丸ごと送る (D1530 の形)。
   併せて、`record_sealed_classified_failure_terminal()` は現在 production / test とも呼び手 0 件で
   ある。単位 C で呼び手を名指しできるか、API を落とすかを land 前条件にする。
2. **E1 の分類 policy の権威をどこに置くか。** `repetition_evidence` は production 起動層から
   到達不能で、`expected_use_perf` に対応する単一 pin も無く、`probe_outcome` は計測前 probe を
   覆わない。3 点とも起動層 (単位 C) の所有面である。
   - `expected_use_perf` を verified mode / perf-preflight evidence へ束縛するか、v2 台帳を単一 mode に
     限定するか (レンズ A の推奨は前者)。
   - `probe_outcome` を計測前・計測後の組へ広げるか、計測前 probe の session を v2 台帳の対象外と
     明示するか (レンズ A の推奨は前者)。
3. **A1' が返した裁定パッケージ 1 (合成 2 段 v1 残骸の受理) は未裁定のまま持ち越す。**
   本 wave も fail-closed 拒否を維持し、受理側へ戻していない。
4. **B1 が返した 5 件は未裁定のまま持ち越す** (旧世代 token の capability 発行入口、分類権限の
   宣言 object 駆動化、計測前 probe 除外の権限層、crash 回復の再取得層、journal TOCTOU 窓)。
