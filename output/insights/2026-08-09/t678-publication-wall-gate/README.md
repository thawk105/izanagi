# [T-678] 最終 publication 後の wall gate 再評価 — 一次資料と逐語

dev-wave `worktree-dev-wave-t678-publication-wall-gate` (base `bcda1c02`) の全逐語。
本文の正本は worklog エントリで、ここは逐語と実測値の凍結先である。

## 依頼と、実装できた範囲

**依頼**: launcher が最終 publication 後に wall gate を再評価しないため、receipt の staging /
publication が 10〜20 秒級で停滞しても `accepted` で通る。publication 完了後にも再評価する形へ直す。

**実装できた範囲 (段 4 で正式に縮約)**: receipt は create-only 公開のため、字義どおりの
「publication 完了後の再評価」は**実装不能**である。final path が可視化された瞬間に別 consumer が
`accepted` を読めるので、その後の再評価は受理を取り消せない。取り消せない再評価で process rc だけを
変えれば「receipt=accepted かつ rc≠0」という矛盾を作る。そこで次へ縮約した。

> output publication、published output を含む audit、**公開する exact bytes の write + fsync** を
> すべて終えた後、receipt final path の可視化直前 — 最後の可逆点 — で wall gate を再評価する。

**塞げない残余** (記録の正直さのために全列挙する):

| 残余区間 | 位置 |
|---|---|
| `os.link` / `os.replace` 自体 | `_atomic_create_json_reserved` |
| final path 可視化から durability 確定まで | 同上 |
| 親 directory の `_fsync_parent` | 同上 |
| staged temp cleanup | 同上 |
| receipt lock の unlock / close | `_reserve_receipt_slot` |
| `_run_supervised` の return から process 終了まで | `_run` / `main` |

**この残余は 10〜20 秒に限定されず任意に長くなり得る** (レンズ A の指摘)。字義どおりの保証には
commit protocol の再設計 (schema v3 / 2 段 receipt / 可視化と admission の分離) が要り、
これは受理契約と consumer を変える設計択一なので**裁定パッケージ候補としてユーザーへ返す**。

## 親の実測

| 何を | どうやって | 結果 |
|---|---|---|
| 穴の実在 (段 1) | `_stage_receipt_write` 先頭へ `time.sleep(4.0)` を一時挿入 (tracked file 一時変異 → `git checkout --` 復元、復元後 tree clean) | fixture `max_wall="3"` に対し実経過 ~4.4 秒でも `accepted` / `completed` / rc=0。`test_positive_p1_normal_job_is_accepted` は **1 passed in 5.04s** (dispatch request `896677`)。外側 timeout 10 秒も赤にしない |
| 実装後の焦点走行 | `tools/run_tests.py orchestrator/tests/test_codex_worker_launch.py --force-dispatch` | **77 passed** (request `896765` ほか) |
| 変異 matrix | `tools/mutation_harness.py --runner-mode dispatch --detached` (固定 HEAD = 統合 commit) | baseline 緑、**MT1〜MT4 すべて KILLED・期待 node と完全一致** |
| 受入全走 (1 走目) | `tools/run_tests.py` (lease `acquired` 後、背景投入) | **7660 passed / 20 skipped** (1324 秒) |

受入 lease は 68 回目の `claim` で `acquired` になった (10 秒間隔、先行 holder の age は最大 1875 秒)。

## 段 3 が倒した親 brief の主張 (撤回済み)

- **「accepted receipt の `actuals.wall_clock_s` と limit が矛盾したまま通る」は誤り。**
  checker は accepted receipt の `actuals.wall_clock_s > limit` を拒否する。
  実際の欠陥は **staging / publication の時間が `actuals` に入っていない**ことである。
- **「受理集合は狭まるだけ」も不正確。** 採用した P1′ は receipt temp の二度目の write を
  除去するため、「一度目は成功し二度目だけが失敗する」冗長な失敗面が消える。これは拡大ではなく
  重複の解消として意図的に受け入れ、不変条件を「publication I/O が成功した**論理 job** について
  狭まるだけ」へ書き換えた。
- **成果物影響の一般化も縮約した。** `tools/codex_worker_launch.py` の **production caller は
  repo 内に存在しない** ([T-595] 実測)。現行 `DW-O01` は raw `codex exec` を起動し `.done` と
  exit code だけを見る。したがって本 gate が効くのは (a) dogfood receipt と
  (b) [T-665]/[T-662] の「`DW-O01` を launcher 経由へ集約」案が採られた場合の 2 つだけである。

## 主張しないこと

- 実障害で 10〜20 秒級の停滞が起きる頻度・実在。親実測は 4 秒の論理的注入であり、
  `write` / `fsync` / `os.link` / lock 競合と同じ機序ではない。
- F57 の原因がこの穴であること。F57 は launcher / git timeout / PBS walltime / 並行 wave 競合の
  複数 producer が混在し、本 wave はそれを閉じない。
- 「負荷フレークが消えた」こと ([T-680] の別裁定事項)。

## 実装の骨子

- `_stage_receipt_write` は fsync 済み temp の `Path` を返し、削除しない。
- `_atomic_create_json_reserved` は呼出側が用意した temp を公開する形へ変え、
  **temp の所有権は helper へ渡した時点で移る** (成功時も例外時も helper が後始末する)。
  これで gate の後に同じ bytes をもう一度書く経路が消えた。
- accepted 経路 = output 公開 → hash 照合 → audit(published) → staging → **再評価** →
  まだ accepted なら同一 temp を公開。
- flip 時 = staged temp 破棄 → output unlink → **親 directory の fsync** → flag 復元 →
  `_receipt` 再構築 → audit(False) → 再 staging → `not_accepted` / `max_wall_clock_s` / rc=1。
  flip 判定は `receipt["outcome"]` でなく `attempts[-1]["accepted"]` を見る
  (`_receipt` は attempts を深いコピーしないため)。
- launcher-error fallback の output 削除にも親 directory の fsync を入れた。
- launcher 局所の `_monotonic_ns()` seam を新設 (テストが共有 `time` module を汚さないため)。
- `schema_version=2`、closed field 集合、`wall_clock_scope` literal、writer / checker の真理値表は不変。
  `actuals.wall_clock_s` が receipt object 構築時点の値であり late gate の観測時刻とは別だと
  docstring へ明記した。

## 段 6 レビューと fix

- R1 (不変条件・例外経路): must-fix 0、nit 1、backlog 1、条件付き GO。
- R2 (検出力・正直さ): **must-fix 1** — 追加 node N3 の「変更前赤」が意図した inode 検査ではなく
  観測器の `AttributeError` に依存していた。これを kill と数えると、二重 temp write へ戻った変異を
  検出済みと誤認する。
- fix はテスト観測器のみ (production 無変更)。`_write_json_temp` を receipt path 限定で記録し、
  「temp 作成 1 回 + final receipt の inode が同一」という production から見える形へ置換した。
  R1 nit も併せて閉じ、helper 丸ごとの差し替えをやめて receipt path の `os.link` だけを失敗させ、
  helper の例外時 cleanup を実際に通す形にした。
- 焦点再レビュー: 2 件とも **closed**、残 must-fix 0、MT1〜MT4 は全件 KILLED 予測 (実測と一致)。

## 変異 matrix

| ID | 変異 | 期待 | 実測 |
|---|---|---|---|
| MT1 | staging 後の `_latch_final_job_limit` を削除 | N1, N2 が赤 | **KILLED** (一致) |
| MT2 | staged temp を捨て公開時に新 temp を書く | N3 が赤 | **KILLED** (一致) |
| MT3 | flip 時の published output unlink を削除 | N1, N2 が赤 | **KILLED** (一致) |
| MT4 | flip 時の `_receipt` 再構築を省く | N1, N2 が赤 | **KILLED** (一致) |

**`DW-M01` の「過剰拒否を検出する正例」は変異として登録しなかった。** 理由は手順の制約である —
`tools/mutation_harness.py` は失敗 node 集合の**完全一致**で KILLED を判定するが、過剰拒否 (late gate が
常に発火する変異) の波及は受理経路の 23 test 関数以上に及び、期待集合を正確に予測できない。
予測を外した `MISMATCH` は情報量がないため、正例の義務は
**baseline 緑 + MT1〜MT4 の各走で `test_positive_p1_normal_job_is_accepted` が緑のまま**であることで
担保した。この乖離は `DW-O12` に従って記録し、段 8 の改善候補にも回した。

## 裁定パッケージ候補 (scope 外・ユーザー手番)

worklog の新規項として起票した。要点だけ再掲する。

- **S-A**: create-only 制約下で「publication 完了後」の字義を満たす commit protocol 再設計の要否。
- **S-C**: atomic create 後の例外 (`_fsync_parent` 失敗・lock unlock 失敗) で
  `accepted receipt / process rc=2` が併存しうる既存欠陥。
- **S-E**: `_atomic_publish` に output の rollback が無く、partial output と launcher-error receipt が
  併存しうる既存欠陥。
- **S-F**: `KeyboardInterrupt` / `SystemExit` で receipt の rc と process rc が分離する。
- **S-G**: staged temp を Path で保持する間の置換窓 (同 UID 単一 writer 前提の明文化 or fd/inode 束縛)。
- **replace_invalid pin**: `os.replace` 経路の所有・inode が回帰テストで固定されていない (R1 backlog)。

既出との重複は起票しない。`DW-O01` を launcher 経由へ集約する論点は [T-665]/[T-662]、
publication 失敗時に receipt が残らない論点は [T-679] が既に持つ。

## エージェント工数

Codex 7 session (段 2 plan 1 / 段 3 相談 2 / 段 5 実装 1 / 段 6 レビュー 2 / fix 1) +
焦点再レビュー 1 = 8。親 = brief・実測 probe 1 本・裁定・統合 commit・変異・受入・記録。

## ファイル

`s1-brief.md` / `s2-plan.md` / `s3-lensA.md` / `s3-lensB.md` / `s4-adjudication.md` /
`s5-impl.md` / `s6-R1.md` / `s6-R2.md` / `s6fix.md` / `s6focus.md` と各 prompt、
`mutation-spec.json` / `mutation-ledger.json`。
