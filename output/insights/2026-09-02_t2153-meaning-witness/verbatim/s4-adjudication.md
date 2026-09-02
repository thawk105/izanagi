# [T-2153] 段 4 裁定 (親) — プラン v2

段 2 のプラン、段 3 のレンズ A / レンズ B の所見を、親が real / refuted と採否で裁定した。
親は各所見をコードで独立に裏取りしている。

## 所見の裁定

| # | 出所 | 判定 | 採否 | 理由 |
|---|---|---|---|---|
| A-1 | レンズ A | **real (半分)** | 一部採用 | 「守られている本体を無害化しても green」は成立する。ただし本体 bytes の期待値を macro ごとに焼くのは patch の編集で常時赤になり、本 wave の scope を超える。**採用するのは入れ子の半分** — 対象の条件指令が別の条件指令の内側にあると、切り出して単体で前処理した観測は実翻訳単位の到達性を主張できない。ここは深さ 0 の要求で閉じる。 |
| A-2 = B-1 | 両レンズ | **real** | **全面採用 (BLOCKER)** | `MeaningWitnessDeclaration.__post_init__` (`:387`) は集合所属しか見ず、CLI (`:2594`) も同じ検査の後に旧型を組む。集合を広げると旧 BACKOFF 復号器が新 macro へ流用でき、D1242 が却下した形そのものになる。旧型を `BACKOFF_FIXED` に固定する。 |
| A-3 | レンズ A | **real** | 採用 (回避で閉じる) | ladder の REPORT は同伴 define の再注入で実 build と乖離しうる。**REPORT を第一群から外す**ことで本 wave では発生しない。理由を名前付きで残す。 |
| A-4 | レンズ A | **real** | 採用 (理由の訂正) | `IZANAGI_BREAK_TRIGGER_MISATTR` を外す理由は「`#ifdef` だから」ではなく、**実 build の対が「定義する / しない」であるのに gate の要求が 1 / 0 であること**、および**条件指令が `#if BACKOFF_TRIGGER_GATING` の内側にあること** (深さ 0 でない) の 2 つである。後者は本 wave の構造要求で自動的に除外される。 |
| A-5 = B-2 | 両レンズ | **real** | 採用 (第一群を絞ることで閉じる) | 意味の節を呼ぶ生産側は 21 箇所 (campaign 18 + tools 3) で、プランの 6 面では足りない。親が独立に数え直して確認した。**第一群を 8 件へ絞ると、その 8 件を要求する driver は 4 面だけになる** (`s3_lock_coverage`、`s5_permutation_coverage`、`t152_write_intent_coverage`、`screening_driver`)。この 4 面を配線すれば分裂は起きない。 |
| A-6 | レンズ A | **real** | 一部採用 | 主張境界は proof kind の名前と module docstring で明記する。新しい語彙 field は足さない (B-5 と同じ理由で重複)。 |
| B-3 | レンズ B | **real** | 採用 | fixture が生成物に寄ると実 patch との結合を検査できない。テストは**実 patch の追加側 bytes から所有 path と開始指令を独立に照合する**こと。 |
| B-4 | レンズ B | **real** | 採用 (段 7 で処理) | 新しい test node は受入所要時間台帳の node key pin へ追随が要る。親が受入実測後に add-only で更新する。 |
| B-5 | レンズ B | **real** | 採用 | registry は macro・所有 path・開始指令だけに絞る。値と同伴 define は `DefineRequest` と `_validate_define_request` の正本を再利用する。witness kind の 4 分類は判定規則が同じなので作らない。 |
| B-6 | レンズ B | **real** | **採用 (BLOCKER 相当)** | 13 件同時は依頼の「一括では扱わない」に当たる。**第一群を 8 件へ絞る。** |
| A/B の親 brief 誤り指摘 | 両レンズ | **real** | 採用 | (P1-c) 11 件は誤り。(P1-d) s1 一関数では足りない。`capture_define_inputs` が patch 適用を保証するという一般化は誤りで、保証しているのは各 driver 側である。`SS2PL_WFG_DIAG` の「5 箇所」は誤りで実際はもっと多い。いずれも親 brief を訂正する。 |
| B の「稼働 wave 重複が 0 でない」 | レンズ B | **refuted (対象が違う)** | 不採用 | 親が数えた重複 0 は `condition_meaning_gate.py` についてであり、現在も成立する。レンズ B が指した `acceptance_duration_ledger.json` は**本 wave が編集面に含めると決めたことで初めて重なる面**であり、着手時点の重複ではない。ただし**指摘は有効**なので、段 7 の台帳更新前に再確認し、land 順を調整する。 |

## プラン v2 (実装契約)

### 第一群 — 今回 green へ動かす 8 件

`cc/silo/transaction.cc` に、単一の `#if <MACRO>` … `#endif` を**深さ 0 で 1 箇所だけ**持つ positive control。

1. `IZANAGI_BREAK_PERMUTATION`
2. `IZANAGI_BREAK_PERMUTATION_SWAP`
3. `IZANAGI_BREAK_LOCK_COVERAGE`
4. `IZANAGI_BREAK_EARLY_UNLOCK`
5. `IZANAGI_BREAK_WRITE_INTENT_ERASE`
6. `IZANAGI_BREAK_WRITE_INTENT_FORGE`
7. `IZANAGI_BREAK_WRITE_INTENT_OPSWAP`
8. `IZANAGI_BREAK_WRITE_INTENT_PTRSWAP`

要求値 1、既定値 0。green の必要条件は「要求値で対象枝が選ばれ、既定値で選ばれず、
両方で対応 `#endif` の後ろの完了 marker が観測される」ことである。
これにより意味対応は 1/22 から 9/22 になる。

### 動かさない 13 件と、その理由 (名前付きで残す)

- `IZANAGI_BREAK_NOREAD_VALIDATION`、`IZANAGI_BREAK_HIGHKEY_VALIDATION` —
  `#else` を持ち、その内側にさらに `#if ADD_ANALYSIS` の入れ子がある。対応 `#endif` の
  深さ追跡が要る。第二群。
- `IZANAGI_BREAK_TRIGGER_MISATTR` — 条件指令が `#if BACKOFF_TRIGGER_GATING` の内側にあり
  深さ 0 でない。加えて実 build の対は「定義する / しない」であるのに gate の要求は 1 / 0 で、
  `#ifdef` は両方で真になる。要求契約の側を変える裁定が要る。
- `SORT_VARIANT`、`BACKOFF_NOINLINE` — 枝自体は単一だが、成果物へ届く driver
  (`p3_s4_loop_sort`、`s6_sort_sweep`、`paper_story_a2_certification`、
  `t1683_rr5_cost_probe`) の配線が本 wave の編集面を大きく超える。第二群。
- `IZANAGI_SILO_LADDER_RUNG1_REPORT` — 同伴 define を gate 側が再注入するため、実 build に
  `IZANAGI_SILO_LADDER_RUNG1=1` が無くても green になりうる (レンズ A の所見 3)。
  driver 境界で実引数を要求する設計が要る。
- `IZANAGI_SILO_LADDER_RUNG1`、`BACKOFF_REQUESTED_US`、`BACKOFF_TRIGGER_GATING` —
  条件指令が複数箇所に散る。代表 1 箇所だけを green にすると macro 全体の意味を過大主張する。
  全箇所を閉じた集合として宣言する別の witness が要る。
- `SS2PL_LOCK_IMPL`、`SS2PL_LOCK_KIND`、`SS2PL_DLR`、`SS2PL_WFG_DIAG` —
  selector / template 引数 / 診断が混在し、分岐の実体が CMake 側にもある。単一枝 witness では
  意味を確立できない。

### 実装するもの

**`orchestrator/campaign/condition_meaning_gate.py`**

1. 最小の registry を足す。macro → (所有 file の相対 path, 開始指令の逐語) だけを持つ。
   値・同伴 define は持たせない (`DefineRequest` と `_validate_define_request` が正本)。
2. 新しい宣言型を足す。`MeaningWitnessDeclaration` とは別の exact type とする。
3. 宣言を作る factory を公開する。registry に無い macro、registry にあるが要求値・既定値が
   対にならない場合は `None` を返す (= 従来どおり `unestablished`)。
4. 条件指令の切り出しは次を要求する。いずれかを満たさなければ赤にする。
   - 宣言された開始指令の逐語が、その file に**ちょうど 1 箇所**現れる。
   - その位置の**前処理指令の入れ子の深さが 0** である (別の条件指令の内側でない)。
   - 対応する `#endif` が深さを数えて一意に決まる。
5. 計測は要求値と既定値の**両方**で行い、観測が同じなら赤にする
   (理由コードは非識別を表す 1 つに固定する)。
6. `MeaningWitnessDeclaration.__post_init__` と CLI の旧型構築を **`BACKOFF_FIXED` に固定する。**
   `MEANING_SUPPORTED_MACROS` の拡張が旧復号器の受理を広げてはならない。
7. green の evidence schema に新 proof 用の exact な検査を足す。proof kind の名前は
   compile-time の枝選択に限定した語にする。module docstring の主張境界も同時に更新する。

**driver 4 面** — `declaration=None` を factory 呼び出しへ置き換える。
`s3_lock_coverage.py:96`、`s5_permutation_coverage.py:93`、
`t152_write_intent_coverage.py:211` 付近、`screening_driver.py` の該当箇所。

### 実装しないもの (scope 外)

- 選択された枝の本文 bytes の期待値を macro ごとに焼くこと。
- witness kind の 4 分類、`claim_scope` などの新語彙 field、新しい台帳。
- 第一群 8 件を要求しない driver (`s8a_*`、`p3_s4_loop_*`、`s6_sort_sweep`、
  `s1_verify_extime_calibration`、`silo_ladder_rung1`、`paper_story_a2_certification`、
  `run_ss2pl_lock_study`、`t1683_rr5_cost_probe`、`t316_sandbox_backend_probe`) の編集。
  成果物の値を変えないうえ、自己 hash pin を持つ面がある。
- `s1_direct_comparison.py` の編集。第一群 8 件を要求しないため不要であり、
  bytes pin の golden 2 箇所を動かさずに済む。

## 不変条件 (実装子が破ってはならない)

- **witness の無いものを established と書かない。** registry に無い macro は `None` を返し、
  従来どおり `unestablished` のままにする。
- **受理集合を緩めない。** 本 wave の変更は「これまで `unestablished` で通っていたものが
  `red` になりうる」方向だけを許す。これまで拒否されていた入力が受理されるようにしてはならない。
  特に旧宣言型の受理面を広げない。
- **恒真な witness を作らない。** 要求値と既定値の観測が同じなら必ず赤。
- **測定対象を変えない。** `patches/*.patch`、CCBench のソース、実 configure / build の引数を
  変更しない。
- gate の禁止は署名で書き、**通る正例を必ず 1 つ添える。**

## 変異の事前登録 (DW-M01)

実装前に登録する。各変異は無効化時の赤理由が 1 つに絞れることを実装後にコードで確認し、
絞れなければ登録から外して実効 gate へ再照準する。

| ID | 変異 | 期待する赤 |
|---|---|---|
| MUT-1 | 要求値と既定値の観測一致を許す (非識別を green にする) | 非識別の負例が赤 |
| MUT-2 | 入れ子の深さ 0 要求を外す | 入れ子対象の負例が赤 |
| MUT-3 | 開始指令の一意性要求を「1 箇所以上」に緩める | 指令重複の負例が赤 |
| MUT-4 | `MeaningWitnessDeclaration` の macro 固定を集合所属へ戻す | 旧型で非 BACKOFF macro を渡す負例が赤 |
| MUT-5 | factory が registry 外の macro にも宣言を返す | 未確立維持の検査が赤 |
| MUT-6 | 完了 marker の観測要求を外す | 対応 `#endif` 不整合の負例が赤 |
