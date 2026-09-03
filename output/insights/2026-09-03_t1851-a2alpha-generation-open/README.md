# [T-1851] 実装単位 A の後半 A2α — v2 世代を path・claim・capability で開き、terminal は封印 API まで閉じる

2026-09-03。branch `worktree-dev-wave-t1851-unit-a`。**land していない (D1341)。**

- 実装 tip: `9df7105f6`
- 本 wave の commit: `69497db66` (実装) / `a5d9c8bcd` (fix 1) / `c785bd628` (fix 2) /
  `3ca1622b2` (fix 3) / `b648d3cd4` (fix 4) / `9df7105f6` (fix 5)
- local main 取り込み: `afeb43e6f` (431e0d6d8) と `27e93b911` (dc9a060d3)
- 実装面の差分: 5 file、+1,671 / −97 行

## 中身

前 wave (A1') が固定した境界 signature の E1〜E4 のうち、**E3 と E4 の構造面を A2α として積んだ。**
E1 (生の事実からの terminal projection)、E2 (台帳専用理由語彙 4 語)、sealed terminal API 2 本、
起動層の証拠 carrier は **A2β へ送り、2 件を裁定パッケージとしてユーザーへ返す。**

積んだもの (段 4 裁定の S1〜S12)。

- core の `DomainProfile` へ `terminal_row_validator`、`TransitionPolicy` へ
  `retryable_terminal_opens_next_attempt` を keyword-only default で足し、terminal 経路と
  次 ordinal 経路へ配線した。既存 production constructor 3 件ずつは text 変更ゼロで通る。
- `_assert_profile()` を schema identity で分岐する exact validator にし、比較本体を
  `_assert_exact_profile()` へ抽出した。新 2 field も exact 比較に含める。
- v2 の terminal を core validator と adapter 入口の二層で無条件に拒否する。
  署名は `[s8b-v2-terminal] v2 terminal requires the sealed evidence API`。
- `_entry_paths()` の protocol 分岐を全 11 呼出しへ通した。
- 世代の create-only publish、claim v3 の address / schema / reader / writer、
  legacy marker validator の rename と v2 の capability 経路分岐、marker 所有の atomic update と
  lock 生存 guard、reserve / resume の marker 引数。

v1 (canonical 1 段) の public API・戻り型・受理集合・claim v2・legacy marker は不変である。
v2 の retryable 理由集合は空のまま置き、A1' が書いた空集合 pin は 1 byte も変えていない。

## 1. A2' は 1 wave に収まらなかった。分割の向きを plan とは逆にした

[実測] 段 2 plan と段 3 の敵対レンズ 2 本が独立に測り、3 者が一致した。A2' 全体は
**1,380〜1,900 changed LOC / 新設 110〜145 node / 既存回帰 487 node** である。
既存回帰の内訳は直接 176 (profile 86 + adapter 74 + equivalence 16) + trial_registry 225 +
launcher 12 + holdout 72 + scheduler 1 + campaign helper 1 の union。

**plan は A2α = `E1+E2+carrier` / A2β = `E3+E4` を提案したが、親は逆にした。**
plan の順序では blocker がすべて前半に集中し、前半はユーザー裁定なしに着手できない。
**裁定待ちの部分を先に置く分割は wave を空回りさせる。**

[実測] 親が段 1 で立てた分割候補 (`E1+E2+E3` / `E4`) も plan が現物で反証した。
E3 が v2 を受理した後も `create_attempt_registry()` は protocol を渡さず `_entry_paths()` を
呼ぶ (`s8b_attempt_registry.py:1343-1350`) 一方、v2 の root は `{protocol_sha256}` を含む
2 段 path である (`s8b_attempt_profile.py:516-523`)。**E3 を path 分岐より先に開くと
v2 が誤った 1 段 destination へ進む。** よって E3 は E4 の path 分岐と同じ変更単位に置いた。

## 2. 前 wave が固定した境界 signature は、前 wave 自身が承認した要求を実装できない

[実測] 3 者 (段 2 plan、レンズ A、レンズ B) が独立に同じ結論へ達した。

前 wave 段 4 は E1 の 2 つの sealed terminal API を
`observation/failure`・`sealed_session_record`・`finished_at` だけを受ける形で固定した。
一方、同じ裁定が「status / reason / primary value は**起動層所有の生の事実から再導出**し、
sealed record の自己申告 field は**比較にだけ**使う」を要求している。

- 現行 handle が保持するのは classification receipt bytes と raw-output digest までである
  (`s8b_attempt_registry.py:163-185`)。
- 生の事実が揃うのは launcher の token open 後である
  (`s8b_floor_attempt_launcher.py:614-628`)。
- その後 adapter へ渡す既存 terminal call は自己申告 terminal 値だけである (`:633-644`)。

**固定 8 signature のままでは二重導出を実装できない。** 裁定パッケージ 1 として返す。

## 3. `repetition_evidence` は production 起動層から到達不能である

[実測] 起動層の許可引数に `rep_observations` は無く (`s8b_floor_attempt_launcher.py:32-46`)、
`_capture()` も private sink を作らない (`:429-441`)。既存 test はむしろ明示指定を拒否する
(`test_s8b_floor_attempt_launcher.py:600-645`)。

`DW-O13` は「field の実在では足りない。その field が実環境で取りうる値を実測し、要求する値が
到達可能か確かめてから述語を採用する。到達不能なら採用せず、測った値域を裁定へ書く」と定める。
**到達不能な入力を要求する validator は、謳うだけで発火しない保証になる。** 実装しない。

到達化には起動層の変更が要り、それは単位 C の所有である。**D1530 (未接続 interface の権威束縛は
本番の呼び手を繋ぐ変更と同じ単位で行う) が本 wave 開始後に main へ着地しており、これが
E1 を A2β へ送る 2 つ目の根拠になった。**

## 4. 変異走が、静的レビュー 4 本が見落とした「消しても誰も気づかない防壁」を 3 つ暴いた

**これが本 wave で最も価値のある実測である。**

段 3 のレンズ A・B と段 6 のレビュー C・D、計 4 本が実装を静的に検査した。そのうえで変異を
実際に注入して走らせたところ、次の 3 箇所は**防壁を消しても赤になる test が 1 件も無かった。**

| 箇所 | 静的レビューの判定 | 実走の結果 |
|---|---|---|
| marker 経路の prelock hook の位置 (M12) | 4 本とも言及なし | **SURVIVED。** 既存の rendezvous 検査と locked-update seam 検査はどちらも別の関数を見ていた |
| claim v3 の protocol 世代束縛 (M9 / M9b) | レビュー D が「v2 lifecycle node の protocol tamper が kill する」と明示的に判定 | **単層も両層も SURVIVED。** その node は赤にならなかった |
| resume の回復序数 gate (M14) | 4 本とも言及なし | **SURVIVED** (後に冗長 gate と判明。7 節) |

いずれも**実装は正しく、足りないのは検査だった。** claim v3 の protocol 束縛が pin されていない
状態は、別 protocol 世代の admission claim が v2 予約に通る受理集合の穴である。

**静的レビューの kill 判定を実走の代わりにできない。** レビュー D は M9 について kill する
nodeid まで名指ししていたが、その node は実際には赤にならなかった。

## 5. 親自身の段 6 裁定 2 件も実測が覆した

- **M6**: レビュー D が「早期拒否を消しても `_publish_create_only` が再度拒否するので
  診断差でだけ赤になる」と判定し、親も SURVIVED と裁定した。**実走では単層でも実効的に
  殺されていた。** fix 1 巡目が入れた直接検査が効いていた。
- **M10a**: レビュー C 所見 16 が「`_atomic_update_locked` の下層 guard は直接検査されて
  いない」と判定し、親も SURVIVED と裁定した。**fix 1 巡目の直接検査がこれを閉じており、
  実走では単層で殺される。**

どちらも、fix を入れた**後**の状態を静的に再評価しないまま裁定した結果である。
**fix が閉じた穴を、fix 前の判定のまま登録すると変異台帳が事実と食い違う。**

## 6. codex の子は 1 度も pytest を走らせられず、赤は必ず親まで遅れて出た

[実測] 段 5 の実装子と段 6 の fix 子 5 巡、合わせて 6 者すべてが
`qstat -Q preflight rc=1` により runner `rc=16`、`child_started=false` で終わった。
親からの同じ投入は D612 の opt-in 上書き
(`IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE=3600` /
`IZANAGI_DISPATCH_OVERALL_GRACE_OVERRIDE=600`) で通る。

結果として **baseline の赤が 2 回、親の変異走まで漏れた。** どちらも fix 子が新設した test の
fixture の作り方の誤りで、実装の誤りではない。

- 1 回目: 共有 helper へ存在しない中間 directory を渡していた (`FileNotFoundError`)。
- 2 回目: 2 つ目の repo を新規に作り protocol 文書を手作りしたため必須 key が 10 個欠けていた。

**6 巡目で「実走できないなら module を import して対象 test 関数を直接呼び、fixture が
成立するか確かめよ」と指示したところ、子は `DIRECT_CALL_PASS` を得たうえで、実行時に検査を
除去して `DID NOT RAISE` になることまで確かめて返した。** これは pytest 緑の代わりにはならないが、
fixture の成立と変異の反実仮想は取れる。**同型の漏れは以後この確認で防げる。**

## 7. resume の回復序数 gate は冗長 gate だった

fix 3 巡目に「受理集合が実際に変わる負例 (分類行を持つ `attempt_ordinal != 0`)」を作らせようと
したところ、**公開経路ではその状態へ到達できないと報告して停止した。**
`reserve_attempt_slot()` の同じ gate が先に拒否するためである。

したがって resume 側の gate を消しても、赤の実体は拒否署名の差にとどまり受理集合は変わらない。
`DW-M03` の「診断文字列だけの赤を kill にしない」「過剰決定なら冗長 gate と明記して単独変異の
証拠から外す」に従い、**M14 は診断感度の pin として別枠に記録し、kill 16 件の内訳に含めない。**

**子が実装を変えずに「作れない理由」を書いて止めたのは正しい判断である。**

## 8. D1522 を全面適用した

本 wave 開始後に main へ着地した D1522 (上流で受理集合を縮めた結果、下層の防壁へ既存テストが
到達しなくなる場合、上流の拒否期待へ移設せず下層の実体を名指しする直接検査へ作り直す) を
3 組へ適用した。

- terminal の二層 (core の `terminal_row_validator` と adapter 入口)
- symlink 防壁の四層
- lock 生存 guard と admission 側再検査の三層

段 6 のレビュー C は symlink と lock の 2 組が不充足と判定し、fix 1 巡目で作り直した。
**その作り直しが M6 と M10a を単層で殺せる状態にした** (5 節)。

## 9. 変異 matrix — 21 変異、本走 rc=0、21/21 一致

**KILLED 17 / SURVIVED 4 / MISMATCH 0。baseline PASSED。**
kill として数えるのは **16 件**である (M14 は 7 節により別枠)。

意図した SURVIVED は 4 件。

- M4a / M7a / M13 — 単層変異が他層に mask される。多層同時版 (M4b / M7b / M13b) は KILLED。
- **EQ — 等価変異。** harness の SURVIVED 検出が生きていることの正例対照であり、本物の
  SURVIVED が出たときに「等価変異か実在の穴か」の切り分けを 1 往復減らす。

台帳と spec は同 directory の `mutation-spec-*.json` と `mutation-ledger-*.json`。
erratum と登録の訂正は `parent-measurements.md` に逐語で残した。

## 10. 規模の見積りは 2 wave 連続で下振れした

| wave | 見積り | 実績 |
|---|---|---|
| A1' | 600〜850 changed LOC (前 wave plan) | 約 900 |
| A2α | 740〜1,030 changed LOC (段 4 裁定) | 1,329 (段 5 のみ)、fix 込みで 1,768 |

段 5 単独でも 299 行超過した。超過はほぼ test 側 (production 710 / test 619) で方向は正しいが、
**見積りが下振れするのは 2 回連続である。** 次 wave の見積りはこの傾向を織り込む。

## 11. 閉じていない窓

- **v2 の分類 claim / row と回復 row は marker capability に束縛されていない。** 予約と観測は
  marker 経路だが、これらは素の `_atomic_update()` を通る。前 wave が固定した境界 signature は
  これらの束縛を要求しておらず、v1 も同じ形なので v2 が v1 より広くなるわけではない。
  **束縛される側とされない側を exact に pin する検査を置き、非束縛の集合をここに明記する。
  閉じたと書かない。** 分類・回復まで囲むかは裁定パッケージへ送る。
- **journal の TOCTOU 窓** は A1'/B1 から引き継いだまま閉じていない。
- **`marker.use(action=...)` の例外時に unlink 自体が失敗すると staging が残りうる。**
- **A1' が返した合成 2 段 v1 残骸の受理**は fail-closed 拒否のまま。受理側へ戻していない。

## 12. A2α は最終成果物へ発火しない

`launch_floor_attempt()` の production caller は現に 0 件、result はまだ v4 である。
**A2α は certified 選択・材料レポート・proof chain のいずれにも台帳束縛を発火させない。**
発火するのは B2 / D1 / C / D2 が揃ってからで、これは意図どおりである。
**「効いている」と書いてはならない。**

D1114 (発火する path を名指しできない gate は部分実装でも land しない) に触れないのは、
D1341 により本 wave が land しないからである。

## 13. ユーザーへ返す裁定パッケージ

1. **E1 の境界 signature を補正してよいか。** 2 節の理由により、前 wave が固定した 2 つの
   sealed terminal API のままでは前 wave 自身が承認した要求を実装できない。選択肢は 3 つ。
   **受理面と public API 面を広げる方向なので親だけでは選べない。**
   - (推奨) 起動層が生の事実を snapshot して発行する **evidence-bound handle** を第 9 の境界として
     追加し、resume 可能な durable evidence digest も持たせる (レンズ A の推奨)。
   - 2 つの sealed API へ `probe_outcome` / `throughputs` / `execution_failures` /
     `repetition_evidence` の keyword-only 引数を直接足す (plan の推奨)。実装は短いが、
     呼び手が値を選べる形になりやすく D1113 の主旨から遠い。
   - 境界を変えず、E1 を単位 C と同じ変更単位へ丸ごと送る (D1530 の形)。

   併せて `record_sealed_classified_failure_terminal()` は現在 production / test とも呼び手 0 件。
   単位 C で呼び手を名指しできるか、API を落とすかを land 前条件にする。
2. **E1 の分類 policy の権威をどこに置くか。** 3 点とも起動層 (単位 C) の所有面である。
   - `expected_use_perf` を verified mode / perf-preflight evidence へ束縛するか、v2 台帳を
     単一 mode に限定するか (レンズ A の推奨は前者)。
   - `probe_outcome` を計測前・計測後の組へ広げるか、計測前 probe の session を v2 台帳の
     対象外と明示するか (レンズ A の推奨は前者)。
   - `repetition_evidence` を到達可能にする起動層の sink をどの変更単位に置くか。
3. **v2 の分類 claim / 回復 row を marker capability で囲むか** (11 節)。前 wave の境界は
   要求していない。囲まないなら、非束縛の集合を成果物へ明記し続ける (D1533 の形)。
4. **A1' が返した裁定パッケージ 1 (合成 2 段 v1 残骸の受理) は未裁定のまま持ち越す。**
5. **B1 が返した 5 件は未裁定のまま持ち越す** (旧世代 token の capability 発行入口、
   分類権限の宣言 object 駆動化、計測前 probe 除外の権限層、crash 回復の再取得層、
   journal TOCTOU 窓)。

## 14. 次 wave の出発点

- **A2β から続ける。** ただし**上の裁定パッケージ 1 と 2 が先である。** E1 の境界 signature が
  確定しないと着手できない。
- E2 (台帳専用理由語彙 4 語) は E1 の validator と同じ変更単位でしか active にできない。
  literal は親裁定で確定してよい (D1113 は語彙が閉じていることと機械導出だけを定め、綴りを
  凍結していない)。候補は `measurement_environment_conflict` /
  `measurement_execution_unavailable` / `measurement_sample_incomplete` /
  `measurement_dispersion_exceeded`。`excluded_reason -> ledger reason` の辞書を権威にしない。
- A2β が supersede すべき pin は 2 箇所。
  `test_terminal_validator_direct_replay_and_producer_mapping_keep_v1_positive` の v2 拒否部分と、
  `test_v2_marker_claim_v3_resume_and_legacy_terminal_fail_closed` の adapter 拒否部分。
  v1 正例、forged profile の拒否、validator が non-`None` である pin は supersede 対象ではない。
- A1' が書いた v2 空集合 pin の supersede に追加のユーザー裁定は要らない
  (段 3 の両レンズが独立に確認した)。
- 6 段すべてを積んだ後に、D1341 に従って 1 変更単位で land する。
- 本 wave の worklog / decisions / failures fragment は `docs/spool/` に置いてある。
  その land 時に fold される。
