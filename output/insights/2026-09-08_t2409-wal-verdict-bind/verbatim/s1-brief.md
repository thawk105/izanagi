# 段 1 brief — [T-2409] B-10 の受理経路へ WAL の正しさ判定を束縛する

- wave: `dev-wave-t2409-wal-verdict-bind`
- 投入先 worktree (子はここだけを読み書きする): `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2409-wal-verdict-bind`
- branch: `worktree-dev-wave-t2409-wal-verdict-bind`、起点 local main `cc9bba523ac7804aadb7891d686bf4c925789a3f`

## 研究前進

B-10 の 3 系列 report は「この workload でこの backoff 形が速い」という性能主張を、
**正しさ認定つき**で出す成果物である。ところが report 発行経路は block record 45 件の内容を
exact に縛る一方、同じ campaign の WAL にある正しさの判定 (`anomalies` / `certified` /
`verdict`) を一切見ない。件数と `workload.tag` だけ揃えた WAL に差し替えれば、anomaly が
出ていた走行でも同じ report を発行できる。これは規律 2 の穴であり、B-10 / A-6 が論文で使う
「certified な選択」の土台を弱くする。閉じれば、report の正しさ主張が現物 verifier 判定へ束縛される。

**完了判定:** 3 系列の現物 WAL では report 経路が通り続け、3 field のいずれかを崩した WAL では
必ず止まること (正例・負例の両方をテストで示す)。

## 確定済みユーザー裁定

- **D1772** (2026-09-08 /rulings 全件 第 14 回、相談で推奨が逆転)。WAL の
  `anomalies` / `certified` / `verdict` を既存の内容 digest へ含めて閉じる。新しい gate 機構は作らない。
- 起草時の推奨「gate を作らず限界を明記する」は **D1744 の誤引用に基づき撤回済み。採らない。**
- **本題の実装だけ。** 仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外 (ユーザー明示)。

## 着手前の実測 (完了) — 結論: 既存 literal の再発行は不要 (0 個)

| 測ったこと | 結果 |
|---|---|
| 「既存の内容 digest」の正体 | `LEGACY_{WRITE_HEAVY,BALANCED,READ_HEAVY}_RECORD_SHA256S`、各 45・計 135 literal |
| その値の出どころ | block record 本体の canonical JSON の sha256。**同じ値が現物 file 内に `record_sha256` として書かれている** (現物は `{schema_version, record_sha256, record}` の封筒形式) |
| 現物からの再計算 | 3 系列とも production 関数で読み直し、literal 集合と完全一致 (各 45/45) |
| block record に 3 field はあるか | **無い。3 系列とも 0/45。** `correctness_certified` はあるが `anomalies`/`certified`/`verdict` は無い |
| 3 field の所在 | 別 file `runs/wal.jsonl` の `verify_done` payload のみ |
| 現物 WAL の値 | 3 系列とも `verify_done` ちょうど 90 件、`anomalies=0` 90/90、`certified=true` 90/90、`verdict="serializable"` 90/90、field 欠落 0 |
| WAL の stage 内訳 | 3 系列とも `build_start` 15 / `build_done` 15 / `verify_done` 90 / `commit` 15 |
| `payload.workload.tag` | 3 系列とも legacy 15 / performance 75 |
| 系列間の形の差 | **read-heavy だけ** payload に `proof_surfaces` key が余分にある |

現物 path: `/work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape/official-output/campaigns/<campaign_id>/runs/wal.jsonl`
(`<campaign_id>` = `b10-backoff-shape-silo-write-heavy-formal-e3de15eb` /
`b10-backoff-shape-silo-balanced-formal-143a3f74` / `b10-backoff-shape-silo-read-heavy-formal-acf840c8`)

## (P1) 親の provisional 裁定 — 段 3 はここを攻撃せよ

D1772 の字義「既存の内容 digest の**対象へ加える**」は、上の実測により **そのままでは実装不能**である。
既存 digest は block record 本体の hash で、同じ値が現物 file 内に自己 hash として書かれているため、
対象を広げるには **135 個の凍結 file を書き換える**しかない。それは literal の再発行ではなく
凍結証拠そのものの改竄で、規律 7・D1597 に反する。

そこで親は、最も近い忠実な実現として次を暫定採用する:

- **(P1-採用案) 同じ legacy 受理経路に、WAL `verify_done` の 3 field の値述語を exact 条件として足す。**
  新 literal 0 個。系列非依存。`anomalies == 0` かつ `certified is True` かつ
  `verdict == "serializable"` を、legacy 3 系列の WAL の**全** `verify_done` record に要求する。
- **(P1-対抗案) 系列別の WAL digest literal を新設する。** D1597 の「系列ごとの有限集合」の形には
  近いが、第 2 の digest 族の新設に当たり「新しい gate 機構は作らない」と逆向き。
  read-heavy だけ payload の key 集合が違うため系列別 literal が必須になる。

段 3 はこの択一と、採用案が本当に穴を塞ぐか (件数と tag を揃えた差し替えを実際に止めるか) を攻撃せよ。

## 不変条件 (破ってはならない)

1. `LEGACY_*_RECORD_SHA256S` の 135 literal を 1 個も変えない。test 側の `meta_digest` golden
   (balanced `8e5f0b48…`、read-heavy `27195442…`) も無傷のままにする。
2. 凍結 block record file (3 系列 × 45 = 135 件) を書き換えない。
3. `_legacy_write_heavy_binding` / `_legacy_balanced_binding` / `_legacy_read_heavy_binding` と
   3 つの `_validate_legacy_*_records` の**既存**受理述語には触らない
   (別セッションが T-2408 / D1771 でこの領域を担当中)。
4. 受理集合は**狭まる方向のみ**。既存の検査を 1 つも緩めない (規律 2)。
5. 現物 3 系列は通り続けること。実測で 90/90 が述語を満たすので、これは達成可能な要求である。
6. `output/` 配下の既存成果物・凍結 report を再発行しない。

## pin 閉包 (DW-O09、実測済み)

- `ANALYSIS_REL = "orchestrator/campaign/b10_backoff_shape_sweep.py"` — **編集対象 file 自身が
  解析コード**で、その whole-file sha256 が **live 経路の** `analysis_code_sha256` になる。
  `load_preregistration` は current bytes == HEAD blob を要求するので、**編集は commit 済みでないと
  live 経路が止まる**。legacy 3 系列は凍結 literal を使うので影響を受けない。
- path 検索で、この file の whole-file sha256 を literal に焼いた golden pin は他に無い。
- `orchestrator/tests/acceptance_duration_ledger.json` に既存 node が登録済み。新規 test node は
  main 取り込み後に add-only で 1 回だけ足す。

## 変更面の実アンカー (起点 commit `cc9bba523` の行番号)

| path | 行 | 何があるか |
|---|---|---|
| `orchestrator/campaign/b10_backoff_shape_sweep.py` | 3359 | `_verification_source_disclosure` — WAL を読む唯一の legacy 経路 |
| 同上 | 3390-3395 | WAL 読取。**例外を握り潰して `wal_read_error` に載せ、空 counts で返す** (gate ではなく開示) |
| 同上 | 3405-3425 | `verify_done` 走査。`payload.workload.tag` と `record.variant` しか見ない |
| 同上 | 3441 | `_verification_completeness` — counts から completeness を作る |
| 同上 | 3556-3580 | `_collect_report_inputs` の legacy 3 系列 dispatch と `_verification_source_disclosure` 呼出し |
| 同上 | 2876 / 2887 | `_require_legacy_record_digests` / `_legacy_record_content_digest` (**触らない**、参照用) |
| 同上 | 92 | `ANALYSIS_REL` (自己 hash の根) |
| `orchestrator/tests/test_b10_backoff_shape_sweep.py` | 1985-2000 | balanced の literal・`meta_digest` golden |
| 同上 | 2118-2140 | read-heavy の literal・`meta_digest` golden |
| 同上 | 2197 | `_legacy_record_content_digest` を現物へ当てる既存正例 |

## 成果物の形

コード + テスト + insight (逐語・変異台帳) + spool fragment (worklog / decisions)。
docs 3 台帳は直接編集せず fragment で書く。

## 並列分割方針

編集面が 1 実装 file + 1 test file と小さいので、**段 5 の実装子は 1 本**。
段 3 の敵対相談は 2 本 (レンズ: ①穴が本当に塞がるか・受理集合の向き、②D1772 の字義との距離と
凍結証拠への副作用)。段 6 のレビューも 2 本。正しさ防壁に触り受理集合が変わる wave なので、
段 2・3・6 の検証子は省略しない。

## 他セッションとの調整

`campaign lock identity migration [000f2b]` (T-2408 / D1771) が同一 file の 2863-3210 行付近を
担当中。実測結果 (再発行不要 → 2 本は別単位) と本 wave の編集予定面を送付済みで、先方は
順番を待つ意向。編集面が広がったら即通知する。
