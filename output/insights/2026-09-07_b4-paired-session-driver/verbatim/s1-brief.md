# 段 1 brief — B-4 対照対 driver を「候補と参照を 1 session」へ直す

## scope

D1699 に従い `orchestrator/campaign/floor_pair_driver.py` を、**candidate と reference が
1 つの低水準 session に入る**形へ直す。あわせて **reference の個数と D の式を凍結**する。
変更面は `orchestrator/campaign/floor_pair_driver.py` と
`orchestrator/tests/test_floor_pair_driver.py` の 2 file だけ。
事前登録文書 `docs/phase3-b4-reflux-ablation-preregistration.md` は編集しない
(D1699 が「§5 の値セルは sentinel のままで本書はまだ発効していない」と書いており、
凍結手続きの費用がかからないため。同文書は別 wave `[d2dd9f]` が触る)。

**scope 外 (依頼が明示):** 仮想リスク向けの gate・検査・台帳・一般化の追加。
`candidate_floor` を exact 有理数へ変える件も scope 外 (consumer 側が変換する)。

## 成果物影響 (DW-G05)

放置すると、候補と参照の比が走行間のドリフト帯を跨いだまま床値 `candidate_floor` が生成される。
床値は tie 判定の閾値なので、値がずれると **B-4 の受理集合 (どの block を tie と数えるか) が直接変わる。**
B-4 は床値の主張そのものなので、実走前に閉じる必要がある。

## 確定済みユーザー裁定

- **D1699** — 3 role を役割ごとに別 session で測る形は「3 role の組を同一セッションと読む」
  用語訂正では正当化しない。設計を直し、reference の個数と D の式を実走前に凍結する。
- **D1641 第 3 項「共通参照点と対照対」** — byte 単位で同一の候補の対を、独立した 2 セッションで
  順序を事前に無作為化して測る。参照点は対ごとに同一セッション内で測る。
- **規律 2** — 正しさゲートを緩める変異を許さない。
- Codex author = D95。実装面は Codex 実装子が書き、親は docs だけ編集する。

## 不変条件 (弱めない)

1. **測定実体の身元。** 測定関数の差し込み口を権威経路へ作らない。T-2166 の敵対レビューが
   暴いた実欠陥 #1 がこれで、偽関数が対の両側へ同じ値を返すと D=0 → 床値 0 →
   tie 判定が消えて受理集合が最大に広がる。**2 binary を 1 session で測るために
   injection seam を足さない。**
2. 競合検知 argv は driver 定数 `COMPETING_PROBE_ARGV` のまま。spec の自由 field に戻さない。
3. candidate と reference は別 artifact。宣言 sha256 の一致検査と trace symbol 不在検査は残す。
4. fail-closed の status 群と、落とした標本の 5% 会計 (`MAX_DROPPED_FRACTION`) を残す。
5. 1 session に pre_probe / post_probe が 1 対。どちらかが不確定・競合なら標本を落とす。
6. `NOT_PROVEN` の「証明していないこと」は減らさない。形が変わって増える項があれば足す。

## 割れうる前提 (P1 — 親の provisional 裁定、段 3 の攻撃対象)

- **(P1-a) 「1 つの低水準 session」の実体。** `measure_point` は binary を 1 個しか取らない
  (runner.py:1057、`capture_measure_point` も同じ、親が現物で確認)。したがって
  「1 回の呼び出しで 2 binary」は実現不能。**1 つの pre/post probe 区間の中で candidate と
  reference の両方を測る**形とし、これを 1 session と呼ぶ。
- **(P1-b) reference の個数 = pair-sample あたり 2** (side ごとに 1)。
  `D = |gain_1 - gain_2|`、`gain_i = median(candidate_i) / median(reference_i) - 1`。
  すなわち `D = |c1/r1 - c2/r2|`。両側とも同じ reference artifact を測るが、
  **測定値は side ごとに別**である。これが D1699 の「比がドリフト帯を跨がない」を満たす形。
- **(P1-c) session 内の実行順** (candidate が先か reference が先か) も HMAC rank で
  事前に無作為化し、plan へ固定する。現行が 3 role の順を無作為化しているのと同じ方式。
- **(P1-d) schema 版。** `SPEC_SCHEMA` を v2→v3、`SUMMARY_SCHEMA` を v2→v3 へ上げる。
  値の**意味**が変わるため (同名の床値で意味の違う値を流さない)。
  `candidate_floor` の field 名・値域 (0 以上 1 未満)・`status` の語彙は据え置く
  (唯一の consumer `p3_b4_material_report` 系がこの 3 点に依存。peer `[d92888]` と調整済み)。
- **(P1-e) 凍結の置き場所。** spec の `statistics` ブロックへ凍結識別子を足す
  (現行の `session_reducer` / `stratum_upper` / `closed_strata` / `final_combiner` と同じ形)。
  reference の個数と D の式をこの exact 一致で束縛する。

## 緑を保つ既存 gate

- `orchestrator/tests/test_ccbench_spawn_sites.py:115-117` — driver の subprocess 起動点を
  `_git_head` / `_git_show_head` / `_run_probe` の各 1 に固定。**起動点を増やさない。**
- `orchestrator/tests/test_official_perf_closure.py:53` — reviewed perf file 台帳。

## 分割方針

実装子 1 本。2 file は plan / 実行 / 束縛 / 導出 / 成果物が一続きで、分割すると整合が壊れる。
段 3 の敵対相談は 2 本 (レンズ: 規律 2 の攻撃面 / 凍結と受理集合の整合)。
