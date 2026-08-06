# 段 4 裁定 — dev-wave-t244-p3-8c-wiring

段 2 プラン (`s2/plan.md`)、段 3 敵対 2 レンズ (`s3/lensA.md` / `s3/lensB.md`) を親が全件
real / refuted に裁定した。**結論は「実装しない」**であり、`DW-S04` に従い `4→7→8→9` とする。

---

## 1. 結論

**[T-244] P3 の 8c wiring は、本 wave では実装しない。設計メモと裁定パッケージだけを返す。**

根拠は `DW-G04` (条件付き機能は、発火条件を満たす既存 artifact path か計測 ID を brief に
書ける場合だけ実装する) の不成立である。親は段 1 の brief (P6) で「fixture store 上の実 ledger +
8c の `--provider fixture --no-build` 経路」を発火 path として書いたが、**この 2 つを結ぶ経路は
存在しない**と段 3 で判明し、親が現物で確認した。

これは U-6 (worklog (236)) の裁定を親が不採用にするものではない。`DW-S04` に従い、
**裁定時点で未見だった新事実を付けてユーザー再裁定待ちへ戻す**。

## 2. 親が現物で確認した blocker (レンズの主張の裏取り)

### K1 — authority は 1 batch あたり最低 2 member row を強制する (レンズ B の最重要指摘、real)

`reflux_origin_ledger.py` の `_budget_from_object` は
`batch_member_row_count_min` を `minimum=2` で読む。`BudgetPolicy` を作れる値域そのものが
2 以上であり、`_apply_event` の `BatchReserved` は
`member_row_count < budget.batch_member_row_count_min` を拒否する。
**したがって `member_row_count=1` の batch は、どの authority 値を選んでも作れない。**

一方 8c は 1 generation につき `drive()` を 1 回だけ呼ぶ (N4)。承認上限は 1 generation (D114)。
**「1 回の実行」と「最低 2 member row」が構造的に噛み合わない。**

この事実は台帳に未記録である。`docs/decisions.md` に記録されているのは
`batch_distinct_candidate_count_min <= batch_member_row_count_min` の関係だけで、
下限 2 そのものではない。設計パッケージは floor 式の文脈で `max(2, Bmin) ≤ F` と書いていたが、
U-6 (結線先) の裁定文はこの制約と 8c の実行回数を突き合わせていない。
**よって U-6 裁定時点で未見の新事実である。**

### K2 — no-build の `drive()` は実行せず `dry-pass` を返す (レンズ A/B、real)

`p3_s4_loop.py` の no-build 経路は `{"outcome": "dry-pass", "variant": None}` を返す。
ledger の seal outcome は `accepted` / `rejected` / `tombstoned` の 3 値だけで
(`_result_evidence_preimage`)、`dry-pass` はそのいずれでもない。
`accepted` / `rejected` は `evidence_digest` を必須とし、`rejected` はさらに
`constraint_sha256` を必須とする (`_validate_result_matrix`)。

**現行 `drive()` の戻り値には、この 3 つのどれの正本も存在しない。**
`auditor.diff_digest` 等で代用すれば捏造になる (規律 2)。
したがって配線しても書けるのは **tombstone 行 (= 未実行行、D166)** だけであり、
`sealed_queries` は 0 のまま、query floor も満たさない。
すなわち「oracle query を予算で束縛した」とは名乗れない。

### K3 — binding を供給する経路がどこにも無い (レンズ A、real)

- production authority は `origins: []` の 71 bytes (N1)。U-10 未決で entry を書けない (D183)。
- CLI は origin 束縛引数を持たず、プランも新設しないと明記した。
- `claude-headless` provider への caller 注入は拒否する設計である。
- 非 production の ledger store seam は private `_fixture_store_for_test` だけ (N2)。

**残る発火 path は「本 wave が新しく書くテストが `_run_workload` を直接呼ぶ」だけ**であり、
これは `DW-G04` の言う「既存 artifact path」ではない。(257) が origin-proofs sidecar と
report v3 を却下したのと同型の判定である。

### K4 — 提案 seam には公開の抜け道がある (レンズ B、real)

プランの拒否条件は `claude-headless` provider にしか掛からない。`provider_kind="fixture"` で
`origin_bindings` だけを渡し `origin_ledger` を省略すると、**既定解決で production ledger に
落ちる**。module の再束縛も private sentinel の持込みも要らない、公開 seam 経由の穴である。
さらに `OriginBinding` は caller が作る素の dataclass で、campaign / launch admission と
束縛されていない。正規 scope 内に未束縛の第二権限を持ち込める。

## 3. 所見の real / refuted 裁定

### レンズ A (発火 gate と恒真化)

| # | 所見 | 裁定 |
|---|---|---|
| A1 | P6 を撤回し実装を止める (`DW-G04` 不成立) | **real・採用。本 wave の結論そのもの。** |
| A2 | 正例が private `_run_workload` 直呼びだけだと forwarding を壊しても緑 (F127 型) | **real。** 実装しないため moot だが、再起票時の必須要件として記録する |
| A3 | 変異事前登録に帰属しないものが 8 件 (固定 0 の等価変異、proposal JSON の過剰決定、salt の driver-local kill 等) | **real。** 実装差分が無いため変異 matrix は対象外。再起票時の要件として記録 |
| A4 | build / headless / failure の負例が過剰決定・恒真化リスク (F126 型) | **real。** 同上 |
| A5 | 名乗りを no-build tombstone まで狭めよ | **real・採用。** 実装しないため名乗りはさらに狭い (§5) |
| A6 | N4 の早期 break は 5 でなく 6 (critic-invalid も break する) | **real・訂正した。** 親が現物で確認 (`_run_workload` の critic 呼出し直後)。nit |
| A7 | N5 の「`drive`/`preview` と同型」は構文的先例しか示さない | **real・採用。** brief P2 の根拠は弱い。origin binding には既定 producer が無い |
| A8 | N8 (liveness receipt) は 8c caller の生死ではない。R=2 の手書き probe が event を直接 commit したもの | **real・採用。** 親が N8 を過大に使っていた |
| A9 | プランの candidate commitment 式が base64 の `bytes` を JSON 値へ直接入れている | **real。** ledger 正本は `.decode("ascii")`。実装しないため moot |

### レンズ B (順序・受理集合・既定経路)

| # | 所見 | 裁定 |
|---|---|---|
| B1 | R=1 は `_apply_event` の受理集合外 (Bmin≥2 強制) | **real・確認済み (K1)。親の P3 を撤回する。** |
| B2 | committed / prepared 相の crash・receipt-loss 回収が無く、origin が永久に seal 不能になる | **real。** 既知の scope 外所見 A-8 / B-8 の具体化。裁定パッケージ V-5 へ |
| B3 | fixture caller が production ledger を使える。binding が campaign / admission に未束縛 | **real・確認済み (K4)。** 再起票時の必須要件 |
| B4 | candidate commitment の canonical bytes 誤り | **real。** A9 と同一所見。moot |
| B5 | `_finish_trial` に既定値なし引数を足すと既存 2 node が `TypeError` で赤 | **real。** 実装しないため moot。再起票時の要件 |
| B6 | byte golden は `loop_state.json` の `start_wall=time.time()` で揺れる (F81 型)。fake drive にすると campaign artifact が比較対象から消える | **real・採用。** 親の不変条件 2 (既定経路の bytes 不変) を、プランの literal golden で守る設計は成立しない |
| B7 | private sentinel 持込み・module 再束縛・同一 process 差替えは保証対象外と明記すべき。ただし fixture→production の既定解決と未束縛 binding は公開 seam なので保証対象外へ追い出してはならない | **real・採用。** 再起票時の名乗り契約に含める |
| B8 | `run_trial` は workload 例外を捕捉して partial report にするため、プランの「例外を伝播」は公開 caller までは成立しない | **real・親が現物で確認**(`_finish_trial` の `except Exception` が `supervisor-error` cell を作る)。再起票時の要件 |

### 2 レンズが逆を向いた点

レンズ A は「実装せず設計メモへ戻せ」、レンズ B は「R≥2 + binding + recovery へ再設計せよ」と
主張した。**親は A を採る。** 理由は、B の再設計を全部行っても K3 (binding を供給する経路が無い)
は解消せず、`DW-G04` は依然不成立だからである。B のレンズは発火 gate を担当していないため、
これは矛盾ではなく担当外である。B の再設計要件は、再起票時の必須要件として全件保存する。

### 段 2 プランの親 brief への不同意

プランは P4 / P5 / P6 を否定した。**3 件とも real** であり、下記のとおり撤回する。
プラン自身の「`do_build=False` 限定 + tombstone seal」案は、K2 により
「予算を消費して 1 行も実行しない記録を作る」ことにしかならないため**採用しない**。

## 4. 撤回する親の provisional 裁定

- **(P3) 撤回。** R=1 は受理集合の外 (K1)。親が段 1 で `_budget_from_object` の下限を読まずに
  「pilot は R=1」と書いたのが誤りである。
- **(P4) 撤回。** event の位置そのものは妥当だが、「`drive()` = oracle query」という一般化と
  「seal できる」という含意が成立しない (K2)。
- **(P5) 撤回。** `BatchCommitted` 後に `BatchReservationAbandoned` は受理されない
  (`_apply_event` は `BATCH_RESERVED` 相のみ)。「例外なら放棄」は FSM 上不可能。
- **(P6) 撤回。** 発火 path が存在しない (K3)。**これが実装しない直接の根拠である。**
- **(P2) 部分撤回。** seam の形は既存 pattern と同型に書けるが、それだけでは
  fixture→production の既定解決と未束縛 binding を塞げない (K4)。
- **(P1) 保留。** 「ledger を変更せず driver 側だけで閉じる」は、K1 の member 行数と
  8c の実行回数の不整合をどちらで吸収するかが決まるまで成立とは置けない。
- **(P7) 維持。** 軽量版にしなかった判断は正しかった。軽量版なら段 2・3 を省き、
  K1〜K4 のいずれも land 前に見つからなかった。

## 5. 名乗りの上限 (本 wave)

名乗ってよいのは次だけである。

> **[T-244] P3 の 8c wiring を実装可能性の観点から実測し、`DW-G04` 不成立と判定して実装せず、
> 新事実 4 件と裁定パッケージ 5 件を返した。**

名乗ってはならない — 配線の完了 / U-5 (b) 成分の実装 / U-6 の消化 / P3 の前進 /
生死の追加取得 / 予算束縛 / production provisioning / 名乗りの上限 (D179 §7) の緩和。
**D114 の cap=1、D166 の P4 FAIL、D183 は不変。**

## 6. ユーザーへ返す裁定パッケージ (5 件)

| # | 択一 | 親の推奨 | 採らない場合の成果物影響 (`DW-G05`) |
|---|---|---|---|
| **V-1** | 8c wiring の発火 path をどう作るか。(a) U-10 を裁定して production authority へ entry を 1 件書き、CLI に origin 束縛引数を足す (= production provisioning 解禁) (b) 非 production の pilot ledger store を CLI から指定できるようにする (= store 差替え seam を公開する) (c) U-10 裁定まで設計メモに留める | **(c)**。(b) は `_production_store()` 固定という現行防壁を pilot のために公開 seam へ変えるもので、D147 が塞いだ穴の再演になる | 決めないと (257) が定めた順序 (8c wiring → sidecar → report v3 → completeness) の**先頭が永久に空く**。certified 選択・材料レポート・試行台帳の現在値は不変のまま、P3 は FAIL で固定される |
| **V-2** | seal の result-evidence の正本を誰がいつ決めるか。`accepted` / `rejected` は `evidence_digest` 必須、`rejected` は `constraint_sha256` も必須だが、現行 `drive()` の戻り値にどれの正本も無い | **U-10 と同じ authority 発行の裁定面に載せる。** 本 wave では決めない | 決まらないと配線しても書けるのは tombstone だけで、`sealed_queries` は 0 のまま。材料レポートが「oracle query 1 回」と誤参照すれば証拠の意味が反転する |
| **V-3** | 「1 generation = 1 drive」と「1 batch = 最低 2 member row」の不整合をどう解くか。(a) 同一 wire を R 回測る実行形へ 8c を変える (実行時間が R 倍) (b) 2 行目以降を tombstone にする (予算を消費して実行しない行を作る) (c) 8c 以外を wiring host にする | **(a) が意味的に正しい**が実行時間に効くため、U-10 の予算値裁定と同じ面で決める。(b) は U-4 が警告した恒真化に近づく | (b) を選ぶと `member_row_count=2 / sealed_distinct_candidate_count=0` の行が台帳に残り、将来の P4 consumer が「2 候補を測った」と誤読しうる。(c) は D179 §5.3 の U-6 裁定をやり直すことになる |
| **V-4** | origin binding の発行主体。(a) caller が作る素の dataclass (b) launch admission が campaign / workload / descriptor を照合して発行する capability | **(b)**。(a) だと正規 scope 内に未束縛の第二権限を持ち込め、別 campaign の origin の予算を消費できる | (a) のままだと `report.json.launch_admission` は元 campaign を指すのに ledger の `iterations_used` / `queries_used` は別 origin で増え、試行台帳と材料レポートの参照が分裂する |
| **V-5** | reserve / commit 後の crash recovery と receipt-loss reconciliation (既知 A-8 / B-8 の具体化) | 配線の**前提**として設計する。sidecar を禁じたままでは committed / prepared の 2 相を回収できない | 未設計のまま配線すると、crash した origin は I/Q を消費したまま `BATCH_COMMITTED` / `RESULTS_PREPARED` に留まり、新規予約と `OriginSealed` の受理集合から永久に外れる |

## 7. 再起票の条件と、そのとき必ず満たす要件

V-1〜V-5 が裁定されたら再起票する。そのとき次を必須要件とする (本 wave の所見の保存)。

1. **公開経路の正例を 1 本置く** — `run_trial` から実 fixture client までの forwarding を含む
   正例。private `_run_workload` 直呼びだけにしない (A2)。
2. **fixture binding では production client の既定解決を拒否する** — 完全な fixture-store client の
   明示を必須にする (K4 / B3)。
3. **binding は launch admission が発行する capability にする** (V-4 / B3)。
4. **`_finish_trial` の追加引数は originless 既定値付きにする** (B5)。
5. **既定経路の bytes 不変は、literal SHA golden ではなく別の形で守る** — 実 no-build drive は
   `loop_state.json` に `start_wall=time.time()` を書くため golden が揺れる (B6)。
6. **保証の限界を明記する** — private sentinel 持込み・module 再束縛・同一 process 差替えは
   保証対象外。ただし fixture→production の既定解決と未束縛 binding は公開 seam であり、
   保証対象外へ追い出してはならない (B7)。
7. **変異事前登録を再構成する** — 固定 0 の等価変異、proposal JSON の過剰決定、
   driver-local gate による見かけの kill を除く (A3 / A4)。
8. **ledger 失敗の公開経路の扱いを決める** — `run_trial` は例外を partial report へ変換するため、
   「伝播」だけでは公開 caller まで届かない (B8)。

## 8. 本 wave の射程 (`DW-S04`)

**実装差分が無いため、変異 matrix と受入全走は対象外である。** 差分は docs (spool fragment +
本 insight) のみで、`tools/check_docs.py` と fold dry-run を直接緑にして閉じる。
