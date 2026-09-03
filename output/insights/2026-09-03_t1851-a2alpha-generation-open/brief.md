# 段 1 brief — [T-1851] 台帳配線 3 task 閉包 / 実装単位 A の後半 A2'

2026-09-03 JST。branch `worktree-dev-wave-t1851-unit-a`、HEAD `afeb43e6f` (local main
`431e0d6d8` 取り込み後)。前段の成果は同 branch の未着地 checkpoint に B1 と A1' が積んである。

## scope

A1' が固定した境界 signature (`output/insights/2026-09-02_t1851-unit-a-registry-generation/s4-adjudication.md`
3 節) の E1〜E4 を実装する。plan の群でいえば A4 (理由語彙 / projection)、A5 (sealed record /
raw bytes)、A6 (capability / claim v3) の残り全部に、A1' の inventory が 0 件扱いで落としていた
E3 (`_assert_profile` の schema 別 exact validator 化) を加えたものである。

- **E1** `derive_s8b_terminal_projection(...)` を境界 signature どおり新設する。status / reason /
  primary value は **launcher 所有の生の事実** (probe / classification receipt / throughputs /
  exec failures / rep evidence) からだけ導出し、`sealed_session_record` は比較専用にする。不一致は拒否。
- **E2** v2 profile の台帳専用 retryable 理由語彙 4 語を active にする。**E1 の validator と同じ
  commit でしか active 化しない。**
- **E3** `_assert_profile()` を schema 別 exact validator へ変える。exact 比較に新 field
  `terminal_row_validator` と `retryable_terminal_opens_next_attempt` を含める。
- **E4** v2 generation の create-only publish、B1 capability の消費経路、claim v3、v2 resume、
  sealed terminal API。plan `verbatim/s2-plan.md:282-374` の 8 signature を境界とする。

## 確定済みユーザー裁定 (覆さない)

- **D1113** — 新軸の retryable 理由は呼び手が選べてはならず、封じられた session の canonical bytes
  から機械導出する。凍結 4 語 (`competing_process` / `launch_failure` /
  `nonfinite_or_partial_output` / `performance_anomaly`) を再利用せず、台帳専用の閉じた語彙を持つ。
- **D1193 / D1340** — 予算の集約単位は凍結単位のまま、台帳の名前空間だけ世代ごとに分ける。
  予算は世代別台帳を横断して数える。
- **D1194** — proof chain 束縛は新規成果物へ前向きにだけ掛ける。既存 certified を遡及しない。
- **D1341** — 台帳の配線と proof chain 束縛は同じ変更単位で land する。**本 wave は land しない。**
- 前 wave 段 4 A2-5 / B2-5 — sealed terminal は launcher 所有の生の事実から再導出し、
  自己申告 field は比較対象にだけ使う。

## 不変条件

1. 既存 v1 (canonical 1 段) の public API と受理集合を変えない。`load_attempt_registry()`、
   `assert_registry_rows()`、legacy `record_attempt_terminal()`、legacy marker 経路、v1 claim v2、
   v1 resume は signature も戻り型も不変。
2. 受理集合を広げるのは承認済みの面だけ (v2 の 4 retryable 語、v2 の 2 段 path と 5 軸 slot)。
   E2 単独 active 化は禁止 — E1 の `terminal_row_validator` と同じ変更単位でだけ有効にする。
3. `sealed_session_record` を status / reason / primary value の導出入力に使わない (比較専用)。
4. 到達不能な防御 guard を置かない。`_atomic_update_locked` の lock 生存 guard は marker 経路と
   同時に入れる (A1' が意図的に見送った項目。DW-M01)。
5. 凍結成果物の bytes を 1 byte も変えない。`FROZEN_MANIFEST` は 23 件で試行台帳を 1 件も含まない
   ([実測] `orchestrator/tests/test_frozen_artifacts.py:41-115`)。
6. 絶対規律 2 を緩めない。正しさ gate を通すために validator を甘くする変異は採用しない。

## 成果物の形

`orchestrator/campaign/{attempt_registry_core,s8b_attempt_profile,s8b_attempt_registry}.py` の
production 差分 (見積り約 800〜1,000 changed LOC) と、`orchestrator/tests/` の新設 test。
insight (逐語・変異台帳)、`docs/spool/` の worklog / decisions / failures fragment。**land はしない。**

## 分割方針

**1 単位 1 実装子。** E1 の validator と E2 の語彙 active 化は同じ変更単位でしか成立せず、
E3 は E4 の全 5 call site の前提であり、E4 の claim v3 は E1 の sealed API を消費する。
producer/consumer 契約が単位を跨ぐので並列に分けると契約が壊れる (A1' と同じ判定)。

## (P1) 親の provisional 裁定・攻撃対象

- **(P1-a) A2' 全体 (E1〜E4) が 1 wave に収まる。** 根拠は plan の群別見積り A4 155 + A5 305 +
  A6 340 = 約 800 行に E3 の追加分を足しても A1' の実績 (約 900 行 / fix 1 巡で収束) と同程度である
  こと。ただし A1' 自身が前 wave 見積りの約 2 倍になった前科がある。**parametrize 展開後の node 数と
  consumer 参照閉包を数えて攻撃せよ。** 収まらないなら E1+E2+E3 を先、E4 を後へ割る境界を提案せよ。
- **(P1-b) 台帳専用 4 語の literal は本 wave で確定してよい。** D1113 は「台帳専用の閉じた語彙を持つ」
  ことだけを裁定しており、literal 自体を凍結した裁定は repo に無い ([実測] `docs/decisions.md` の
  `台帳専用` は D1113 の 2 行だけ、`dispersion` 等の候補語は 0 件)。plan は
  `sealed-measurement-dispersion` を [推測] として挙げただけである。**literal を親が決めてよいか、
  それとも凍結 4 語との 1 対 1 対応が新しい受理面を作るのかを攻撃せよ。**
- **(P1-c) E1 は「生の事実から再導出」と D1113 の「封じられた session の canonical bytes から
  機械導出」を両立できる。** 親の読みは「reason の値域は sealed record 由来でよいが、status と
  primary value と最終判定は raw facts から再導出し、sealed record は比較にだけ使う」である。
  **この 2 裁定が実は非同値でないかを攻撃せよ。**
- **(P1-d) E1 の入力 5 種は実在し、値が到達可能である。** [実測] session record schema は
  `throughputs` / `exec_failures` / `excluded_reason` / `valid` / `session_median` / `session_cv` /
  `rep_integrity_failures` / `reps_expected` を持つ (`s8b_ratified_freeze.py:265-267`)。launcher は
  `post_probe` (exact boolean `competing` 必須) と `launch_failures` と `ClassificationAuthority` を
  所有する (`s8b_floor_attempt_launcher.py:25,226-320,363-381,553-597`)。**DW-O13 に従い、各 field が
  実環境で取りうる値を実測し、要求する値が到達可能かを確かめよ。到達不能なら採用せず値域を書け。**
- **(P1-e) 受入・実測は login node の焦点走 + 受入全走。** 新規 Pegasus 実行体を要する実測は無い。

## 変更面のアンカー表 ([実測])

| 群 | file:line | 現行の事実 |
|---|---|---|
| E1 | `attempt_registry_core.py:168-195,891-930,1215-1290,1814-1897` | terminal 行の生成と null matrix。`derive_s8b_terminal_projection` / `S8BTerminalProjection` / `S8BClassificationPolicy` は repo に 0 件 (未実装) |
| E1 | `s8b_attempt_registry.py:1512-1713` | adapter terminal。sealed API 未実装 |
| E1 | `s8b_floor_attempt_launcher.py:25,226-320,363-381,553-597` | 生の事実の所有層。`POST_PROBE_COMPETING_REASON`、`_owned_post_probe`、`_terminal_*`、`ClassificationAuthority` |
| E2 | `s8b_attempt_profile.py:533` | `S8B_V2_RETRYABLE_FAILURE_REASONS = frozenset()` |
| E2 | `attempt_registry_core.py:934-983` | `_assert_null_matrix`。空集合だと retryable 分岐が恒真に拒否し、terminal-failure 分岐が恒真に通す |
| E3 | `s8b_attempt_registry.py:316-451` | `_assert_profile`。`make_s8b_domain_profile` (v1) を再構築して exact 比較する |
| E3 | `s8b_attempt_registry.py:519,1343,1376,1410,2082` | call site 5 件 (全部) |
| E3 | `s8b_attempt_profile.py:629-672` | `make_s8b_v2_domain_profile` は A1' で実装済み |
| E4 | `s8b_attempt_registry.py:52-68,163-183,811-967,1109-1205,1289-1593,1765-2071` | capability / claim / publish / resume |
| test | `test_attempt_registry_core_s8b_profile.py` 50 関数 78 node、`test_s8b_attempt_registry.py` 35 関数 59 node、`test_attempt_registry_core_equivalence.py` 9 関数 16 node | 直接 153 node。consumer 参照閉包で 172 node |

**[実測] E3 は現物で赤である。** v2 profile を `_assert_profile()` へ渡すと
`S8BAttemptRegistryError: [s8b-attempt-registry-profile] domain profile differs from frozen 8b
semantics` を出す (親が repo 外 probe で実走、2026-09-03)。模擬ではない。

## DW-O09 / DW-O10 (pin 閉包と write-path)

- [実測] `FROZEN_MANIFEST` (`test_frozen_artifacts.py:41-115`) は 23 件で、s1-freeze 2 / s8b-freeze
  protocol・holdout・selector 16 / insights 5 である。**試行台帳の artifact は 1 件も無い。**
  `HELD_FROZEN_MANIFEST_KEYS` 4 件と `KEEP_FROZEN_MANIFEST_KEYS` 19 件の分割も試行台帳に無関係。
- [実測] path 側の pin は直接 test の root path pin だけ。claim filename は slot payload の SHA-256、
  capability digest は schema と binding の SHA-256 から導出される (A1' の DW-O09 訂正どおり)。
  **A2' は claim v3 の payload を変えるので filename digest が変わる。これは pin ではなく導出値なので
  凍結 bytes を変えないが、`_slot_address_payload_v3` を pin する test を新設閉包で確認せよ。**
- [実測] adapter が書くのは registry / claim / receipt / staging。consumption marker は adapter でなく
  admission の `consume_attempt_ticket()` が書く。provisioning 経由で `ledger.lock` と
  `attempt-ledger.jsonl` も共有 root に生じる。**A2' が足す write-path は v2 generation directory と
  その `registry.jsonl` の create-only publish、および claim v3 file である。**
- A1' が新たに止めた `db07b575…` live freeze 直下の正規 1 段 v1 mutation は本 wave でも止まったままで、
  受理側へ戻す裁定はユーザー手番のまま。**A2' で勝手に戻さない。**

## DW-O13 (gate 入力の実在)

E1 の 5 入力について (P1-d) の実測を段 2 で完了させる。field の実在では足りず、実環境で取りうる値の
実測が要る。到達不能な入力を要求する validator は採用しない。

## DW-G05 (成果物影響)

放置すると **v2 protocol 世代の台帳が 1 行も書けない** — E3 が塞いでいるので v2 profile は
path 処理より前に 5 箇所で全拒否され、E1/E2 が無いので v2 terminal 行が作れない。結果として
D1193 が要求する「protocol を版上げして同じ cell を測り直す」経路が塞がったままになり、
D1194 の proof chain 束縛も掛ける対象が生まれない。

**ただし A2' 単体でも最終成果物 (certified 選択・材料レポート・proof chain) には発火しない。**
`launch_floor_attempt()` の production caller は現に 0 件、result はまだ v4 である。発火するのは
B2 / D1 / C / D2 が揃ってからで、これは意図どおりである。**「効いている」と書いてはならない。**
D1114 に触れる形 (発火 path を名指しできない gate の単独 land) にならないのは、D1341 により
本 wave が land しないからである。
