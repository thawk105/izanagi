# 段 1 brief — [T-1434][T-189] adjudication 層の task-specific oracle 対応

wave: `dev-wave-t1434-adjudication-oracle` / branch `worktree-dev-wave-t1434-adjudication-oracle`
base: `dd66213978d3d30eed567484ec013216bff6926b` (着手直前の local main)

## scope

事前登録文書 `docs/phase3-t189-model-routing-preregistration.md` の残余 (b) を実装する。

**実装面 (Codex author が書く。親は書かない):**

1. `tools/codex_reasoning_ab.py` の `_load_adjudication`。現状、verdict 行の
   `equivalent_to` は `_validate_verdict_row` の既定経路で **task manifest 全体の union**
   (`known_finding_ids_for_manifest(task_manifest)`、引数なし) に対して検査される。
   この関数は revealed mapping を読んだ**後**に走り、`mapping[packet_id].run_id` →
   `slot_by_run` → schedule slot の join を既に持つ。したがって packet ごとに task が
   同定できている。その task 自身の `known_finding_ids` に対して検査する形へ狭める。
2. 同じ join で得た `oracle_kind` を、adjudication が返す verdict 行へ束縛する。
   下流 (`_aggregate_verified`) が `slot_dimensions` から独立に導く `oracle_kind` と
   食い違ったら fail-closed で reason を出す。

**docs 面 (親が書く。同じ commit に入れる):**

3. 到達度記述の**全複製箇所**を揃える。実測した複製箇所は次の 5 つ。
   - §5.2 表の `_load_adjudication` 行 (`:197`)
   - §5.2 表の `append_verdicts`/`freeze_verdicts`/`reveal_mapping` 行 (`:200`) の
     「意味的な受理条件は依然 §8 待ち」
   - §5.3 の「`_load_adjudication` の task-specific oracle 対応も未実装のままである」(`:259`)
   - §14 limitation の「残余は adjudication の oracle 対応 (§8 待ち)、…」
   - 総括 (4)(b)「adjudication 層の task-specific oracle 対応 (§8 待ち)」
   §6.1 の `oracle_finding_count` → §8 未実装 (`:367`) と、末尾の「§8 の独立 oracle ledger は
   依然として未作成」は**真のまま**なので動かさない。

## 確定済みユーザー裁定・既裁定

- D95: 実装面の author は Codex。親は直接編集しない。
- D931: 外部 task manifest の CLI 入力口は digest 連鎖と対でしか実装しない。その理由文は
  「交換できる対象には verdict の受理集合 (`known_finding_ids`) と positive/negative の分類が
  含まれる。これは正しさゲートの受理集合そのもの」と書く。本 wave は受理集合を**狭める**側なので
  同じ向きである。
- D767: stage5 replayer の `task_acceptance_status` は exact `unbound` 固定。動かさない。
- D932: 費用は記述統計に留め certified な判定を動かさない。本 wave は費用に触らない。
- D674: power simulation を実施しない。したがって §13 の lock 手続きは停止したままで、
  **run は開始していない。** §13 の「run 開始後は oracle、margin、task 除外規則、判定表を
  変更しない」は本 wave を拘束しない (前提を実測で確認した)。

## 不変条件 (違反したら停止)

- **規律 2。** 受理集合を広げる変更を一切含めない。union → task 別集合は真部分集合であり、
  狭める向きだけを実装する。`equivalent_to` の許可、reason の抑制、既存 fail-closed の緩和を
  伴う案は採らない。
- **§8 の独立 oracle 台帳は作らない。** 本 wave が閉じるのは装置側の束縛だけである。
  到達度は `実装済み` ではなく `部分実装` とし、閉じていない面 (独立 oracle 台帳が未作成、
  acceptance は `unbound` のまま) を必ず名指しする。名指しできないなら `部分実装` を使わない
  (§5.2 の語彙規定)。
- `TASK_MANIFEST` の canonical bytes を変えない (`_task_manifest_sha256` の連鎖が動くため)。
- 凍結 bytes の pin 閉包は実測で 0 件。`tools/codex_reasoning_ab.py` を bytes で pin する
  台帳・test・trust root は存在せず、事前登録文書 path を pin する consumer も
  `output/README.md` の説明行と過去 insight だけである。`DW-O10` は不成立。

## (P1)(P2) — 親の provisional 裁定であり攻撃対象

- **(P1) 「§8 の独立 oracle *台帳*」と「adjudication 層の task 別束縛 *機構*」は分離できる。**
  直近 wave (worklog 1027 の持ち越し、§5.2:197) は「(b) は §8 の oracle ledger が未作成のため
  着手条件を満たさない」と記録した。親はこれを**機構については覆る**と裁定する。根拠は
  §5.3 が「着地したのは現行 task manifest の中にある oracle 契約、すなわち `oracle_kind` と
  `known_finding_ids` とその consumer であって、**機構は着地**である」と既に書いていること、
  および `_aggregate_verified` が同じ per-task 検査を既に実装していること (`:10179-10183`)。
  台帳の**内容**が無いことと、装置が task 別に束縛**できない**ことは別の事実である。
- **(P2) 組込み `TASK_MANIFEST` の上では per-task narrowing は恒真である。**
  `_manifest_task_entry` が POS/NEG の双方へ `sorted(_LEGACY_KNOWN_FINDINGS)` を入れるため
  (`:261`)、2 task の集合は同一で、union と per-task が一致する。したがって
  **正例・負例は per-task で異なる `known_finding_ids` を持つ外部 v3 manifest でしか作れない。**
  組込み manifest だけで書いたテストは、実装を消しても緑のままになる。
  `_aggregate_verified` の既存 per-task 検査も同じ理由で組込み manifest 上は恒真である。

## 成果物の形

- `tools/codex_reasoning_ab.py` の差分 (単一関数中心)
- `orchestrator/tests/` の正例 1 本以上・負例 2 本以上。負例は
  (a) task A の finding ID を task B の packet の verdict に書くと reason が出る、
  (b) 実装を消すと (a) が緑に戻る (変異で確認)、の 2 方向。
  fixture は per-task で異なる `known_finding_ids` を持つ外部 v3 manifest。
- 事前登録文書の到達度 5 箇所
- worklog / decisions の spool fragment

## DW-G05 — 実装しない場合の成果物影響

実装しないと、外部 v3 task manifest を使う adjudication は、task A にしか存在しない
oracle finding ID を task B の packet の verdict 行へ書いても受理する。その結果、
§8 の記述的 finding coverage の分子が誤って増え、T-189 の quality 側の記述統計が
実際より良く出る。certified な選択結果そのものは動かない (§12.1 により
`routing_evidence_status` は `inconclusive` 固定) が、事前登録が要求する受理集合の定義が
装置側で守られない。

## 並列分割方針

編集面が `tools/codex_reasoning_ab.py` 1 ファイルへ集中するため**実装子は 1 本**とし分割しない。
`DW-C00` の軽量版判定は成立しない — 本 wave は受理集合を変える。したがって
段 2 プラン子 1 本、段 3 敵対相談 2 レンズ (レンズ A = 正しさゲート/規律 2、
レンズ B = 恒真化と機構の実効性)、段 6 敵対レビュー 2 本 + fix を省略しない。

## 起動時に実測した環境

- 稼働 wave (process 実測): `dev-wave-t1825-rescue-gate`、
  `dev-wave-runner-tip-equality-20260827`、`rulings-all-20260827`、
  06:24 起動の `dev-wave-t1769-b4-wiring-probe`。
- 編集面重複: 対象 2 path について全 branch の `main...<branch>` 差分 0 件、
  稼働 worktree の未 commit 差分 0 件。`dev-wave-t1769-b4-wiring-probe` は
  **B-4** 事前登録の wave であり T-189 ではない (checkout 進行中の `D`/`??` はノイズ)。
- 受入・テストは本計算ノードの login node で走らせる (§7.0.0 の既定自動判定に従う)。
