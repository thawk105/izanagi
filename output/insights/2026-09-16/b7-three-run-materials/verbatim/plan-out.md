## 配置と単位の判断

**採るのは、新しい 3 走行併記稿を results 系列へ足す案。ただし P2 の単位の説明を修正し、一次資料の不足を補ってから起草する。** 配置は妥当だが、現在の射影だけでは「生標本を含む一次資料全体からの再導出」まで完了できない。

根拠は次のとおり。

- `verbatim-d1631.md:3–8` は「完走した 1 つの protocol または campaign 群の結果」を単位とする。
- `docs/paper-story/README.md:163–164` も「1 protocol または 1 campaign 群の完走」と定める。
- **同 README:158 は、B-7 の「全 workload」の集合を、別 attempt の記録を保った報告単位として既に明示的に登録している。** 単一の正式実験を意味しない併記稿という扱いは、親 brief だけの解釈ではない。

したがって、新稿の単位は次のように指定する。

> B-7 の結果節材料として、名指しした A-2・A-6・T-1998 の完走済み記録群を、それぞれの protocol・事前登録・判定単位を保持して併記する。単一の横断実験を新設するものではない。

P2 の「全 workload の集合 + balanced の 2 度目」という説明だけでは、集合への追加と独立な追試を混同させる。「**3 workload、3 走行、4 対比較、8 arm/cell の掲載枠**」と区別する。T-1998 は A-2 balanced の同一 protocol での第 2 attempt ではない。

| 案 | 判定と理由 |
|---|---|
| 親 P1：3 走行の新稿 | 採用。README:158 の報告単位を引き継げる。ただし既存稿へ T-1998 の段落を足しただけの再発行にはしない。 |
| (a) T-1998 単独稿だけ | D1631 には適合するが、3 走行の正負・異質性・限定を一緒に読める材料にする依頼には不足する。単独稿の禁止を意味しない。 |
| (b) 既存稿と版で材料化済み | 不採用。既存稿:43–46 は T-1998 を明示的に除外する。版の要約は、生標本・出所・限定を持つ統制稿の代わりにならない。 |
| (c) 差分改訂禁止に抵触 | **新稿を置くこと自体への反論としては不採用。** 全対象を一次資料から再導出すれば抵触しない。ただし親の一次資料表だけで既存稿の全数値をコピーする実装には、この反論が成立する。 |

以下の行番号は**今回の計画の根拠位置**である。新設ファイルの行番号は未確定なので節アンカーを指定する。実際の稿から既存文書へ張る参照は、README:177 に従い basename と節名にする。

## 節構成

対象は `docs/paper-story/results/2026-09-16-b7-three-run-materials.md`。

既存稿の「位置づけ→条件→結果→限定→一次資料」という骨格は使える。ただし、既存稿の「共通設定」「全 6 cell certified」を 3 走行へそのまま拡張してはならない。

| 新稿の節 | 書くこと／書かないこと | 根拠位置 |
|---|---|---|
| 冒頭 | 執筆者向け統制稿、append-only、既存稿との対象差。既存稿の誤りを直した稿とは呼ばない。 | 既存稿:3–18、README:162–171 |
| §0.1 対象と報告単位 | 3 workload・3 走行・4 対比較。T-1998/T-2557 は同一の実行手番。 | D1993:23–25、再解析 README:22–24 |
| §0.2 判定の射程 | A-1 の代替ではない、B-7 の充足を判定しない。認可据え置きは D1986 項5 に帰属させる。 | D1986:61–69、D1993:23–25 |
| §1.1 A-2 / A-6 の条件 | 両 certification の復号 policy に記録された共通設定。T-1998 まで共通とは書かない。 | 両 certification:1、`policy_bytes_base64` |
| §1.2 T-1998 の条件と固定対 | balanced、baseline/target、各腕 5 標本、v1、固定された 2 点。事後 argmax としない。 | T-2557 README:165–168、再解析 README:44–64 |
| §1.3 走行別 identity と解析履歴 | 測定 commit と再解析 main commit、測定日と認証日を分離。A-6 の公開 policy hash を投入時 hash と呼ばない。 | 既存稿:117–126、再解析 README:14–18、33–64 |
| §2.1 主表：走行別の対比較 | 下記の 4 行表。正負を同じ表に置き、共通 status・総合効果を作らない。 | D1993:23–25、41–42 |
| §2.2 生標本 | 8 arm/cell を資料内の記録順で掲載。A-2/A-6 の生標本は今回の射影では原資料未確認。 | 既存稿:172–188、320–334、T-1998 result:1 |
| §2.3 ばらつき | 出所ごとに定義を明記。共通 CV 列に押し込まない。 | 既存稿:190–216、再解析 README:44–47 |
| §2.4 正しさの記録 | A-2/A-6 の構造化 correctness と、T-1998 の consumer 受理記録を分ける。「全 8 cell certified」と書かない。 | 両 certification:1、T-1998 result:1、T-2589 README:71–80 |
| §2.5 T-1998 の完了と consumer 判定 | `complete` と `accepted` の出所・意味を説明。同じ成果物の再解析を追加走行に数えない。 | T-1998 result:1、再解析 README:7–8、28–40 |
| §3 限定 | 下記一覧。A-2/A-6 固有の限定を T-1998 の field として装わない。 | 既存稿:238–292、D1993、T-2589・再解析 README |
| §4 一次資料と転記規則 | 実測 SHA-256、JSON path、解析記録の節、未確認資料の区別。図を追加する案は含めない。 | README:163–171 |

## 値の対応表

出所の略号は以下。JSON 3 件はすべて **1 行のファイル**なので、`:1` と JSON path を組み合わせる。

- **A2**：[A-2 certification.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/output/insights/2026-09-07_t2364-paper-story-a2-certification/certification.json:1)
- **A6**：[A-6 certification.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/output/insights/2026-09-08_t2411-paper-story-a6-certification/certification.json:1)
- **R**：[T-1998 result.json](/work/1/SFC/tanab/t1998-balanced-stock-inline-runs/t1998-balanced-stock-inline-20260913T132723Z-548740-balanced/result.json:1)
- **V**：R と同じディレクトリの `reservation.json:1`
- **M**：[着地後再解析 README](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/output/insights/2026-09-15/t1998-landed-main-recheck/README.md:26)
- **C**：[consumer 是正 README](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/output/insights/2026-09-14_t2589-consumer-real-artifact-repair/README.md:9)
- **S**：[初回走行 README](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/output/insights/2026-09-13_t2557-balanced-stock-inline/README.md:11)

`cells[id=…]` は `cell_id` による選択を表す。百分率への換算・丸めは逐語転記と区別する。

| 掲載値 | 出所 file | JSON path または節名 | 逐語の表記 |
|---|---|---|---|
| §0/§1 A-2 attempt | A2:1 | `$.attempt_id` | `t2364-20260907b` |
| §0/§1 A-6 attempt | A6:1 | `$.attempt_id` | `a6-20260908b` |
| §2 A-2 / A-6 status | A2:1 / A6:1 | `$.status` | `observed-positive` / `reject` |
| §2 rr5 median 対 | A2:1 | `cells[id=rr5-stock/rr5-fixed10].performance.median_tps` | `2438295.0` / `3987794.0`。表では `2,438,295` / `3,987,794` tps |
| §2 rr50 median 対 | A2:1 | `cells[id=rr50-stock/rr50-fixed5].performance.median_tps` | `3756230.0` / `4297929.0`。表では桁区切り整数 |
| §2 rr95 median 対 | A6:1 | `cells[id=rr95-stock/rr95-fixed2].performance.median_tps` | `10088796.0` / `9505248.0`。表では桁区切り整数 |
| §2 rr5 効果 | A2:1 | `$.effects.rr5` | `0.6354846316791036`。主表は `100 × effects` を丸めて `+63.5485%` |
| §2 rr50 効果 | A2:1 | `$.effects.rr50` | `0.14421348000521794` → `+14.4213%` |
| §2 rr95 効果 | A6:1 | `$.effects.rr95` | `-0.057841193339621455` → `−5.7841%` |
| §1/§2 genome | A2:1 / A6:1 | `$.cells[].genome` | stock は `BACKOFF_FIXED=-1, BACK_OFF=0`。adopted は `BACK_OFF=1`、fixed は rr5=`10`、rr50=`5`、rr95=`2` |
| §2 correctness | A2:1 / A6:1 | `$.cells[].correctness` | 6 cell とも `status=certified`、`disposition=pass`、`legacy=pass`、`performance=pass`、反復数 `1` / `5` |
| §1 source binding | A2:1 / A6:1 | `$.cells[].source_binding_status` | 全 6 cell `bound` |
| §1 src_token | A2:1 / A6:1 | `$.cells[].src_token` | stock は `stock`。adopted は `955b452a332d…` / `21def77c944b…` / `0b3abbe62a60…`。省略表示と明記 |
| §1 共通設定〔A2/A6 のみ〕 | A2:1 / A6:1 | 復号 policy の `performance_common` | `records=1000000`、`threads=48`、`skew="0.9"`、`rmw="0"`、`max_ope="10"`、`extime=3`、`reps=5`、`ccbench_protocol="silo"` |
| §1 CCBench pin〔A2/A6〕 | A2:1 / A6:1 | `$.current_pin` | `511c953`。この field から完全長 SHA を補わない |
| §1 source commit | A2:1 / A6:1 | `$.source_commit` | `31ec382a7841e188e46f93e8de4261c964facfb2` / `ae8a767eb60118c3f9791141603fa01ad4f28406` |
| §1 protocol SHA-256 | A2:1 / A6:1 | `$.protocol_sha256` | `136b823e60a4b43e07dbbb4e3f8b5be48964226c955e143d59955325f0e0d9f4` / `21427e71793ea744777d11bd90429ce2db1a8d3333ea9e2e0f227ecf377c25dc` |
| §1 公開 policy SHA-256 | A2:1 / A6:1 | `$.policy_sha256` | `67dce5a785dfc52d5df9b773f7a65905a030b7bd61ab7706704e2ed8e85a0487` / `96ed47d0ea72811aa8ee8ced6740fa58c5896e026cb24fa4420a31919d12384a` |
| §1 request | A2:1 / A6:1 | `$.request_ids` | rr5=`981476.nqsv`、rr50=`981477.nqsv`、rr95=`982234.nqsv` |
| §3 床値・最小性 | A2:1 / A6:1 | `a4_noise_floor_status` / `global_minimality_established` / `smallest_observed_sufficient_in_this_two_point_protocol` | `open` / `false` / `null` |

T-1998 は次を独立の対応表として持たせる。

| 掲載値 | 出所 file | JSON path または節名 | 逐語の表記 |
|---|---|---|---|
| §1 workload | R:1 | `$.workload` | `balanced` |
| §1 固定待機量 | R:1 | `$.target_fixed_us` | `5`。本文は `5 µs` |
| §1 genome 対 | M:46–47〔C:22–23 と一致〕 | §2 arm 表 | baseline=`BACK_OFF=0, BACKOFF_FIXED=-1`、target=`BACK_OFF=1, BACKOFF_FIXED=5` |
| §2 baseline 生標本 | R:1 | `$.no_backoff_tps` | `[4079966.0,3891020.0,3978513.0,3859794.0,3893509.0]`。掲載は同順の整数 tps |
| §2 target 生標本 | R:1 | `$.target_tps` | `[4437166.0,4326276.0,4361949.0,4330570.0,4289164.0]`。掲載は同順の整数 tps |
| §2 baseline median | R:1 | `$.no_backoff_median_tps` | `3893509.0` → `3,893,509` tps |
| §2 target median | R:1 | `$.target_median_tps` | `4330570.0` → `4,330,570` tps |
| §2 ratio | R:1 | `$.ratio` | `1.1122537536191646`。全桁 |
| §2 improvement | R:1 | `$.improvement_percent` | `11.225375361916456`。本文は `+11.225375361916456%` |
| §2 標本数 | R:1、M:44–47 | 両配列の長さ／§2 arm 表 | 各腕 `5`。独立な 5 走行とは呼ばない |
| §2 baseline CV | M:46〔C:22 と一致〕 | §2「変動係数」 | `0.022721229214372803` |
| §2 target CV | M:47〔C:23 と一致〕 | 同上 | `0.012790608817328908` |
| §2 unstable | M:46–47 | §2 arm 表 | 両腕 `false` |
| §2 producer 完了状態 | R:1 | `$.status` | `complete` |
| §2 consumer 判定 | M:39〔C:15 と一致〕 | §2 判定表 `status` | `accepted` |
| §2 consumer reason | M:40〔C:16 と一致〕 | §2 判定表 `reason` | `preregistered-balanced-stock-inline-pair` |
| §1 結果 schema | R:1 | `$.schema_version` | `a5-second-boot-result/v1` |
| §1 測定 source commit | R:1 | `$.repository_commit` | `a551cdd3014708993475108f014aacbf32c21137` |
| §1 CCBench gitlink | R:1 | `$.ccbench_commit` | `511c9538e4e8efa54b45cda62e72389ed3b706ec` |
| §1 campaign | R:1 | `$.campaign_id` | `backoff-sweep-silo-balanced-sweep-0dd37c05` |
| §1 host | R:1 | `$.hostname`、`$.fqdn` | いずれも `bnode024` |
| §1 job | R:1 | `$.pbs_jobid` | `0:995755.nqsv`。S:18 の scheduler 表記 `995755.nqsv` と区別 |
| §1 boot | R:1 | `$.boot_id`、`$.boot_epoch` | `a58d5461-525d-48b5-a442-e13f18b5d5d8`、`1788999892` |
| §1 投入・実行日時 | S:17–18 | §1 実行表 | 投入 `2026-09-13 13:27:23Z`、開始 `13:27:36Z`、終了 `13:39:23Z`、記録された Elapse `712 秒` |
| §1 job body digest | V:1、M:56 | `$.binding.script_sha256`／§2 identity 表 | `dff913cb1044858b56f25721f2d0aac6539bbcf2a7ddb63b9e6b4bbcac7aecd8` |
| §1 環境契約 digest | M:55 | §2 identity 表 | `e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01` |
| §1 baseline binary digest | M:57 | §2 identity 表 | `660543647aa9b8bf0b6ff087ec461c901fd186296dc2751cd7d1deb89ae565d9` |
| §1 target binary digest | M:58 | 同上 | `6c89ebd91efddfd6c01fa5fbff1d5d6cf16e8488b7e2fc85f98ec76e1a8dfec4` |
| §4 lock digest | R:1 | `$.lock_sha256` | `ba24c65d01ce80bb17d0ae1ff8f5242078c2cb7b9a6b3c502959542b61ba0c61` |
| §4 WAL digest | R:1 | `$.wal_sha256` | `154ab894a9955885036fcaff03478001153ba015c50f395cbb59b3e20dcf594e` |
| §1 事前登録版と digest | M:63–64 | §2 事前登録 | `v1`、`464e3af59a1ef0f776cad022a52ab87e1fdf2709abfc2062c058203bc813719c` |
| §1 consumer 是正 commit | M:17 | §1 工程表 | `4d7cd40a9b125fd5bc04e2d47a980d8b772c9a31` |
| §1 再解析 main commit | M:33 | §2 | `0600887d92538b3f34d894f9674d202d0a29a578` |
| §1 perf の記録 | R:1 | `$.perf_counter_statuses`、`$.perf_preflight.status/reason/available` | `["not_required"]`、`unavailable` / `nonzero-rc` / `false`。これだけで性能全走の perf 不使用を独立証明したとは書かない |
| §1 toolchain | R:1 | `$.toolchain.{cc,cxx,cmake}.version_first_line` | GCC/G++ は `11.4.0` を含む記録全文、CMake は `cmake version 3.22.1`。独立した compiler 同一性保証にしない |
| §2 correctness 欄の有無 | R:1 | JSON 全 key の静的確認 | **`correctness` 欄なし**。`certified`、`pass`、反復数を補完しない |

§2.5 に置く文面の指定：

> `result.json` のトップレベル `status=complete` は producer の走行完了状態である。consumer の `status=accepted` と `reason=preregistered-balanced-stock-inline-pair` は、同じ保全成果物を解析した記録にある。後者を前者の field として扱わない。

CV は M/C の**consumer 記録値**として載せる。今回読める記録には計算式の明記がないため、数値から式を逆算して確定しない。

§4 には、今回 bytes から計算した次の SHA-256 を載せられる。

| 掲載値 | 出所 file | JSON path または節名 | 逐語の表記 |
|---|---|---|---|
| A2 転記元 SHA-256 | A2 全 bytes | SHA-256 実計算 | `e74d0f870497941b95ac4d1e244634188813e249f2821d571178e4854a3ed671` |
| A6 転記元 SHA-256 | A6 全 bytes | 同上 | `3a9505b009f4d0aa2161bcac8e50dada6712fc214d03d7d68d705060e6d92cab` |
| T-1998 転記元 SHA-256 | R 全 bytes | 同上 | `354ecd5f6c71f26bec3adf6ba95dd3d82142d5c9deb70849180fcec19306c183` |
| consumer 再解析記録 SHA-256 | M 全 bytes | 同上 | `2c7a5a9063f53e8aa26c7001da3ab61839f77b8a6aab86112a13a9856edba881` |
| consumer 是正記録 SHA-256 | C 全 bytes | 同上 | `d01e374f90299071d60f7bb7f0bea7ab48bc9a745403791f00daa44f913958c9` |

**未確定の転記欄がある。** A2/A6 の certification は生 5 標本・abort 率・ばらつきを持たない。既存稿:324–334 が挙げる原資料は今回の読取対象外なので、その数値を既存稿から埋めない。

- A-2：`fig6_a2_certification_observed_positive.provenance.json` の `cells[]`。具体的な field 名と値は未確認。
- A-6：attempt 記録、raw JSON、campaign WAL。既存稿:331–350 は所在を示すが、原資料の値は未確認。
- 両 raw manifest・WAL・A-6 policy 変更前後の記録も、全体再導出の確認対象として親の資料表へ補う必要がある。

これは新規測定の要求ではなく、**既存 bytes の転記元確認が残る**という指摘である。

## 3 走行の異質性の出し方

主表は **1 行＝1 対比較**とする。A-2 は 2 行を占めるが、判定単位は同じ attempt であるとセル内に書く。

| 所属走行・登録の単位 | workload | 比較対 | baseline / target median〔tps〕 | その対の記録効果 | 出力の種類・対象範囲・値 |
|---|---|---|---:|---:|---|
| A-2 `t2364-20260907b`、A-2 policy | rr5 | stock / fixed10 | 2,438,295 / 3,987,794 | +63.5485% | A-2 outer〔rr5 ∧ rr50〕=`observed-positive` |
| A-2 `t2364-20260907b`、同上 | rr50 | stock / fixed5 | 3,756,230 / 4,297,929 | +14.4213% | **上行と同じ A-2 outer 判定** |
| A-6 `a6-20260908b`、A-6 policy | rr95 | stock / fixed2 | 10,088,796 / 9,505,248 | −5.7841% | A-6 outer〔rr95〕=`reject` |
| T-1998、stock-inline 事前登録 v1、上記 campaign | balanced | baseline / target fixed5 | 3,893,509 / 4,330,570 | +11.225375361916456% | consumer〔登録済み balanced 対〕=`accepted` |

表直前に、A-2/A-6 の効果は `effects` の百分率表示、T-1998 は `improvement_percent` の直接転記と書く。判定式は別注記に分離する。

- A-2：復号 policy の `certification_composition.outer_certification` は `logical conjunction in policy workload order`。rr5/rr50 個別の status を作らない。
- A-6：別 study・別 protocol digest による rr95 の判定。共通 schema は共通実験を意味しない。
- T-1998：S:165–168 に記録された固定 2 点・各腕 5 標本・median・ratio・unstable 時 `inconclusive`・事後 argmax 禁止という規則に帰属させる。**`ratio>1` を accepted の判定式として新設しない。**
- A-2/A-6 の詳細な判定閾値は今回の JSON にない。D1993 と出力から推測して補わない。

避ける表の形は明確にする。

- 「workload ごとの status」列で A-2 の連言を 2 個の独立判定に見せる形。
- 「3 走行の総合 status」「平均改善率」「全体 n」「成功数」の行・列。
- balanced の 2 行を平均して 1 行へ畳む形。
- T-1998 の `complete` と A-2/A-6 の outer status を同じ階層へ置く形。
- 定義の異なるばらつきを説明なしに共通「CV」列へ置く形。
- 全 8 arm/cell に一律の `correctness=certified` を付ける形。

## 限定の一覧

既存 11 件は、件数維持のためにコピーせず、射程を再指定する。

| 既存限定 | 新稿での扱い |
|---|---|
| 1 同一 variant の workload 間比較ではない | 維持。T-1998 fixed5 を加えても rr5=fixed10、rr95=fixed2 との同一 variant 横断にはならない。 |
| 2 floor・有意差・再現性を判定しない | 維持。`a4_noise_floor_status=open` は A2/A6 の field に限定。T-1998 に同 field を補わない。 |
| 3 失敗条件 (e) の前件 | 「本稿の資料では床値超の前件を立証しない」と書く。現在の床値全体が未確定だという現況断定へ拡張しない。 |
| 4 同一 variant 横断の材料がない | 維持。既存稿の測定設計の説明は転載せず、欠けている比較の説明に留める。 |
| 5 abort 率は集約値 | A2/A6 の原資料確認後に限って掲載。T-1998 result に abort 率はなく、0 としない。S:39 の WAL abort 件数とも別物。 |
| 6 単一正式実験ではない | **3 走行**へ改める。D1993 項6を直接根拠にする。 |
| 7 D1645 の解除を再裁定しない | 版からの引写しではなく **D1993 項1**に帰属。旧 fig5 の用途制限も同項5による。 |
| 8 旧 attempt を取り消さない | 維持。T-1998 の同一成果物に対する consumer 是正とは分けて説明する。 |
| 9 最小性・一般性を主張しない | 維持。`false` / `null` は A2/A6 の記録。T-1998 は固定対の結果で、他 workload は対象外。 |
| 10 条件関門は受領証・ID まで | D1993 項3の A2/A6 に関する限定として維持。T-1998 で同じ保存構造を確認したとは書かない。 |
| 11 compile-out は source 経由 | A2/A6 の `compile_out_evidence_scope` を逐語引用。T-1998 の性能 binary hash を単独の compile-out 証明としない。 |

追加または独立した項目として必要なのは次の点。

1. **正しさの記録形式は同一ではない。** A2/A6 は 6 cell の `correctness.status=certified`、legacy 1 回・performance 条件 5 回を持つ。R には `correctness` 欄そのものがない。「R に構造化記録がない」と書き、正しさ検査が実施されなかったとは断定しない。
2. **T-1998 の accepted を correctness 欄へ移さない。** C:71–73 は認証 admission・anomaly/verdict・abort 拒否が残ると記録するが、A2/A6 と同一形式の certification を直接示すものではない。
3. **D1993 項3の限定 4 件を残す。** L01 point-key trace、correctness argv の独立記録不在、artifact hash 単独の compile-out 証明不能、supply/meaning 本体の不在。A2/A6 による但し書き解除を T-1998 の独立な certification としない。
4. **T-1998 の測定・受理・再解析は別の時点。** 初回拒否、consumer 是正後の受理、着地後 main の再解析を記録する。再解析は追加標本でも独立な再現でもない。
5. **事前登録前の生値を入れない。** D1874:3–5 に従う。A-2 の balanced と、禁止対象の事前登録前 stock-inline 生値を混同しない。
6. **T-1998 は事前固定した 2 点の比較。** producer の他 genome を事後選択した最良値として持ち込まない。
7. **toolchain 保証の穴を明記する。** C:75–84。回収成果物には全文 manifest がなく、digest 再計算と identity 射影との暗号学的対応を検証しない。両腕の digest を同じ別値へ置換した改竄はこの層で拒否できない。
8. **compiler 同一性の一般保証はない。** M:106–108 の再解析は、同一成果物に対する非独立な確認である。
9. **1 成果物の受理から consumer 全体の欠陥不存在を導かない。** M:104–105、C:132–134。
10. **数値の近さ・符号一致は再現判定ではない。** D1993 項6。旧環境の数値をこの稿の比較入力に加えない。
11. **設定の共通性を 3 走行へ無確認で広げない。** 今回の R は A2/A6 の `performance_common` に相当する設定一式を持たない。
12. **CV の定義を未確認のまま同一視しない。** T-1998 の記録値と A2/A6 の各転記資料の定義を分ける。

## 入口 README の 1 行

`docs/paper-story/README.md:158` の次へ、既存 4 列に合わせて足す。

```markdown
| 2026-09-16 | `results/2026-09-16-b7-three-run-materials.md` | B-7 の結果節材料として、A-2 `t2364-20260907b` の rr5 / rr50、A-6 `a6-20260908b` の rr95、別事前登録による [T-1998] balanced stock-inline 対を併記する統制稿。3 workload・3 走行・4 対比較を、それぞれの記録と判定単位を保って扱う。2026-09-14 稿が対象外とした [T-1998] を含む | 単一の outer status を持たない。A-2 outer は `observed-positive`、A-6 outer は `reject`、[T-1998] consumer は `accepted`（producer の `complete` とは別）。A-1 の横断実験の代替とせず、B-7 の充足・床値超の差を判定しない |
```

## 親 brief の誤り

**確認できた不正確さ・不足は次のとおり。**

1. **brief:34 の「1 file = 1 結果」は単位の省略が大きい。**  
   D1631:4 は「1 つの protocol または campaign 群」、README:163 も同様。P1/P2 の根拠には完全な定義と README:158 の個別登録を併記する。

2. **brief:54 の引用の帰属が不正確。**  
   「一項目だけを直した差分改訂を新しい日付として置かない」は、投影された D1631 規則2の逐語にはない。**規則の正本 README:164 の逐語**である。規則自体は有効だが出所を直す。

3. **brief:58–59 の単位説明は曖昧。**  
   「balanced の 2 度目」は同一 protocol の再走と読める。別事前登録の T-1998 対比較と明示する。3 workload と 4 対比較を区別する。

4. **brief:77–83 の一次資料表では、brief:10 の生標本要件を満たせない。**  
   A2/A6 certification は median と effects を持つが、生標本を持たない。既存稿:331–334 が示す provenance・raw・WAL 等を転記元として追加する必要がある。既存稿の値を certification 由来と記載してはならない。

5. **brief:83 は「T-1998 の全数値が result.json にある」とは読めない形に分割すべき。**  
   status/reason だけでなく、CV・unstable・genome・環境契約 digest・binary digest・事前登録 digest も、今回の R にはない。consumer 記録と reservation への対応を上表どおり明記する。

6. **brief:19 の「未投入」と「認可据え置き」は根拠を分ける必要がある。**  
   D1986 項5が直接定めるのは認可据え置きである。A-1 本走未投入と探索走/pilot の `formal=false` は B-7 抜粋に記述があるが、今回の射影には対応する実行原資料がない。新稿で独立確認済みの実行状態としては書けない。

7. **brief:63–67 の前提は、確認範囲を分ける。**  
   既存稿の存在と T-1998 の対象外指定は現物で確認できた。worklog 1488 や着地履歴自体は射影外なので未検証。「results 系列に T-1998 の材料が無い」は、より正確には「入口の既存 5 行には T-1998 対象の稿が登録されていない」。

変更アンカー表の README 末尾行は現物と一致する。新稿・spool は新設予定のアンカーであり、誤りとは認めない。

## 総括

3 走行併記稿の配置は採用できる。ただし、**判定単位・正しさ記録・数値の出所を走行ごとに分離し、既存稿の全体再導出として作る必要がある。**

必読 13 ファイルはすべて読めた。T-1998 の数値対応、correctness 欄の不在、転記元 SHA-256 は静的に確認済み。A2/A6 の生標本等と原記録の照合は今回の射影外であり、そこを既存稿からコピーして完了扱いにはできない。ファイル変更・測定・テスト・commit は行っていない。