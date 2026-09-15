# [T-1998] 依頼の三工程は着手前に完了済みで、着地後の main から認証判定を再現した

依頼は「既存 balanced 1job submitter で計算ノードへ投入し、結果を回収して既存 consumer で解析する」
だった。**三工程はいずれも本 wave の着手前に完了しており、結果は認証済みで main に着地していた。**
残っていたのは worklog の「次の一手」に `[T-1998]` が持ち越しのまま残っていた記帳だけである。

本 wave は再投入せず、着地後の main の consumer で保全成果物を解析し直して、認証判定が
再現することを実測した。そのうえで持ち越しを閉じた。

## 1. 三工程の済の所在 (一次資料)

| 工程 | いつ・誰が | 一次資料 |
|---|---|---|
| 投入 | 2026-09-13 13:27:23Z、[T-2557] | `output/insights/2026-09-13_t2557-balanced-stock-inline/README.md` §1 |
| 回収 | 同 wave。job `995755.nqsv` が Elapse 712 秒で完走、`.failure.json` なし | 同 §1 |
| 解析 (1 回目) | 同 wave。**consumer が拒否**。原因は測定側でなく consumer 側 | 同 §2・§3 |
| consumer 是正 | 2026-09-14、[T-2589]。commit `4d7cd40a9b125fd5bc04e2d47a980d8b772c9a31` | `output/insights/2026-09-14_t2589-consumer-real-artifact-repair/README.md` §2 |
| 解析 (2 回目・認証) | 同 wave。**再測定なし**で同じ保全成果物を `accepted` へ | 同 §1 |
| 論文側への反映 | `docs/paper-story/2026-09-14.md` に 5 標本・median・変動係数・ratio まで記載済み | 同文書 |
| 双子タスクの終了 | [T-2557] は worklog 1477 で「正式に測り、既存 consumer で認証した」として閉じた | `docs/archive/worklog-phase3-0914-1477.md` |

[T-1998] と [T-2557] は D1938 が同一の実行手番と定めた 1 つの比較であり、
worklog 1433 の [T-1998] 本文も「T-2557と同一の実行手番」と書いている。
**T-2557 が閉じた時点で T-1998 も終端していたが、持ち越しだけが残った。**

## 2. 本 wave が新たに実測したこと

[T-2589] の認証は、自分の wave branch 上で行われた。同 README §6 は
**受入全走が 3 回とも非帰属の輻輳で止まり、その時点では land できていなかった**と書いている
(その後 `4d7cd40a9` として main へ着地している)。
したがって「**着地後の main の consumer が同じ判定を再現するか**」は、本 wave まで未実測だった。

着地後の main (`0600887d92538b3f34d894f9674d202d0a29a578`) の作業木から、保全成果物
`/work/1/SFC/tanab/t1998-balanced-stock-inline-runs/t1998-balanced-stock-inline-20260913T132723Z-548740-balanced`
を `consume_balanced_stock_inline_pair` へ通した。事前登録 §8 が要求する全項目を挙げる。

| 項目 | 値 |
|---|---|
| status | **accepted** |
| reason | `preregistered-balanced-stock-inline-pair` |
| ratio | 1.1122537536191646 |
| improvement_percent | **11.225375361916456** |

| arm | genome | 5 標本 (tps) | median | 変動係数 | `unstable` |
|---|---|---|---:|---:|---|
| baseline | `BACK_OFF=0`, `BACKOFF_FIXED=-1` | 4079966 / 3891020 / 3978513 / 3859794 / 3893509 | 3893509 | 0.022721229214372803 | false |
| target | `BACK_OFF=1`, `BACKOFF_FIXED=5` | 4437166 / 4326276 / 4361949 / 4330570 / 4289164 | 4330570 | 0.012790608817328908 | false |

成果物が記録した identity:

| 対象 | 値 |
|---|---|
| repository_commit | `a551cdd3014708993475108f014aacbf32c21137` |
| CCBench gitlink | `511c9538e4e8efa54b45cda62e72389ed3b706ec` |
| 環境契約 digest | `e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01` |
| job body script sha256 | `dff913cb1044858b56f25721f2d0aac6539bbcf2a7ddb63b9e6b4bbcac7aecd8` |
| baseline の performance binary sha256 | `660543647aa9b8bf0b6ff087ec461c901fd186296dc2751cd7d1deb89ae565d9` |
| target の performance binary sha256 | `6c89ebd91efddfd6c01fa5fbff1d5d6cf16e8488b7e2fc85f98ec76e1a8dfec4` |
| campaign_id | `backoff-sweep-silo-balanced-sweep-0dd37c05` |
| lock sha256 | `ba24c65d01ce80bb17d0ae1ff8f5242078c2cb7b9a6b3c502959542b61ba0c61` |
| WAL sha256 | `154ab894a9955885036fcaff03478001153ba015c50f395cbb59b3e20dcf594e` |

事前登録の版は **v1**。成果物側の sha と解析規則側の sha はどちらも
`464e3af59a1ef0f776cad022a52ab87e1fdf2709abfc2062c058203bc813719c` で一致した。
本 wave は事前登録の bytes を 1 byte も変えていない。

**値は [T-2589] の記録と全桁一致した。** 着地によって判定は動いていない。

**事前登録前の生値 (2026-09-07 の 2 値) は本記録に書いておらず、推定量にも入れていない** (D1874)。

## 3. 再投入しなかった理由

事前登録 §7 は「投入は `tools/pegasus/submit_t1998_balanced_stock_inline.sh` を **1 回だけ**使う」と
凍結している。認証済みの試行が既に 1 本ある状態で 2 本目を出すと、**どちらを主張へ使うかの規則が
事前登録に無い。** 事後にどちらかを選べば prospective の看板が下りる。これは D1874 が
「事前登録の前に取れた値を後から主張へ入れない」と定めて守ろうとしたものと同じ性質の毀損である。

したがって投入器は起動しなかった。**新しい対照を測りたい場合は、新しい事前登録が要る。**

なお本 wave は provenance 監査の過程で保全成果物の生の `result.json` を読んでおり、
再投入しないという判断を下す前に効果量を見ている。**判断の根拠は値ではなく事前登録 §7 の
凍結文言だけである**が、見た事実は隠さず書く。

## 4. 投げ文の前提のうち、実測で覆ったもの

- **「sizing は `orchestrator/tests/test_paper_story_a1_balanced_sizing.py`」は本測定の sizing ではない。**
  同 test が検査する `tools/size_paper_story_a1_balanced.py` は A-1 の 3 workload 横断実験
  (paired-mean・block 設計) 用の sizing certificate を作る。balanced の腕対応は
  `{"variant": "fixed5", "baseline": "no-backoff"}` で T-1998 と同じ対だが、**D1993 項 6 が
  「A-2 / A-6 / balanced stock-inline 対の 3 走行を 1 つの横断実験として集計しない」と明記**しており、
  protocol も事前登録も別である。T-1998 の sizing は事前登録 §6 と consumer の
  `EXPECTED_SAMPLE_COUNT = 5` が正本 (各腕 5 標本の median)。
  A-5 job body は A-1 sizing を一切参照しない (対象語の走査で 0 件)。

- **「job body の global prune が別 invocation と干渉しうる」は現況では成立しない。**
  `tools/pegasus/a5_second_boot_backoff_sweep.sh` に `prune` の文字列は **1 件も無い**。
  T-2354 が 2026-09-09 に `git worktree prune --expire now` を撤去しており、事前登録 §4.1 が
  固定する digest `dff913cb…` はまさにその撤去後の bytes の値である。
  D1804 の「限界」節が残した競合経路は、現行 job body には存在しない。
  なお 2026-09-13 の実測済みの試行もこの撤去後の job body で走っている。

## 5. 本記録が閉じないもの

- **他の成果物での欠陥不存在。** 言えるのはこの成果物で追加の拒否に遭遇しなかったことだけである
  ([T-2589] §5 と同じ限定)。
- **compiler の同一性。** 事前登録 §9 の但し書きはそのまま残る。`source-identity-unbound` に
  落ちなかったことは、計算ノードの `g++` が事前登録の腕別 source digest を再現したという
  **2 回目の観測**にすぎない (同じ成果物の再解析なので独立な観測ではない)。
- **write-heavy と read-heavy。** 事前登録の対象外であり、本 wave も測っていない。
- **[T-2589] が残した非保証範囲。** 両腕の toolchain digest を同じ別値へ置換した改竄は
  この層では拒否できない。本 wave はこの穴を塞いでいない。
- **非帰属受理経路の不通。** [T-2589] §6 が記録した `dev_wave_wait.py` の `red_check` が
  無条件 `None` である件は、本 wave でも直していない。
