# [T-1851] official 床値 campaign を 3 回実投入し、起動証明書を初めて通して真の blocker を実値で特定した

branch `worktree-dev-wave-t1851-c3c-official-floor`、base `0600887d92538b3f34d894f9674d202d0a29a578`
(着手直前の local main)。commit は `affd2a105` (段 5 実装) → `c185b9fd4` (段 6 fix) →
`cd4e9471d` (記録前の local main 取り込み)。

**試行台帳 (attempt registry) 側 gate の実値域は取得できていない。** 走行は計測段へ到達せず、
台帳の slot を 1 件も消費していない。取得できたのは **(a) 起動証明書の実値**と
**(b) 走行を実際に塞いでいる condition gate の入力の完全な実値**である。

---

## 1. 何をしたか

D1936 項14 (「項11 修正後に C3c で実値を取り、その後 D2 へ進む」) の直接の実行として、
`tools/pegasus/submit_floor.sh --confirm-official-floor-run` で official 床値 campaign を
**3 回投入した**。承認は D926 の submission nonce 束縛で運ばれ、
`qsub -v` を自作する経路は使っていない。

| # | request ID | nonce | source commit | driver_rc | Elapse |
|---|---|---|---|---:|---:|
| 1 | `998882.nqsv` | `83ec41dfcc6f43c84ee1d04c20f39fb8` | `0600887d9…` | 1 | 約 90 秒 |
| 2 | `999039.nqsv` | `acb88122c1922dc825555fd1ac5fa707` | `affd2a105…` | 1 | 約 111 秒 |
| 3 | `999102.nqsv` | `d198cec4873622e7d4aeecadf6acea4c` | `c185b9fd4…` | 1 | 約 128 秒 |

3 走行すべてで job script sha256 は
`9a7cd1f80ccec6a15b6f0e3fd842e4e5a9ad382907d4fbb5d4fdf1c94af6c62d` であり、
2026-09-09 の初回 official 走行 (`988501.nqsv`) と同一である。D926 が要求する
「`floor_campaign.sh` を literal に保つ」が効いている。この同一性は D323 違反ではない —
D323 は pilot から official を開く際の裁定であり、official 再投入ごとに script を
変える要求ではない (`docs/decisions.md` の D323 逐語で確認)。

投入は背景 job セッションの Bash tool から行った。2026-07-29 のユーザー裁定 (F49 (ii)) が
許可する経路で、直後に 3 点検査を行った — (a) 計算ノード側 marker (`checkpoint.jsonl`) の実在、
(b) `qstat` での request 可視、(c) 会計痕跡。(a)(b) は全走行で確認した。

## 2. 起動証明書を初めて通した (D2013 / D2014 の実機初検証)

2026-09-09 の `988501.nqsv` は起動証明書で
`launch certificate: freeze allowlist hash 不一致: output/s8b-freeze/floor_protocol.json`
により停止した。D2013 / D2014 がその欠陥を裁定・修正して main へ着地したが、
**実機で効いたことはこれまで観測されていなかった。**

本 wave の 3 走行はいずれも **driver stderr にその停止文言を 1 行も出していない。**
証明書 file が発行され、C3c insight §7 が「証明書 file の発行と発行後再検査には到達していない」と
書いていた面を初めて通過した。

### 発行された証明書の実値

| # | `campaign_run_id` | `clean_scan_digest` | 証明書 file の sha256 |
|---|---|---|---|
| 1 | `20260915T063232Z-2c8cf9be` | `b09b3e0d3711b84abc536e87cba01b8dea44f41253cc73e02c458fe60a65a354` | `d358161ca57a991b1128274f297dedc8f07f4751b974b69e47670bfe4613b9d2` |
| 2 | `20260915T074211Z-2c8cf9be` | `0ec8465687f7031f406128466c212920c4ee0ebbd091003a1a4b665f31b06fc9` | `4f910c9c328b26020c171f90f23adede5b138878afdcb832ae6297f107d6c1d0` |
| 3 | `20260915T075821Z-2c8cf9be` | `41ccc100933e95e68b6555bbdc6bbccd0e4b2356b5bdeecccc05992260e684bb` | `6808ea92c235e9a474840ae720053d56691bfc9befe90668af2aef647ba8590e` |

3 走行で共通の値:
- `protocol_sha256` = `2c8cf9be929d83653814ecf5f2d5ed134a2af89686d796b8144da2fd45dfa58a`
  (resolver が選んだ世代別 protocol)
- `v1_freeze_sha256` = `315b1eb83d6fbdc525448c3c96c66ab6013df72487f35d8fa519c27ba34bc688`
- `started_utc` = 順に `2026-09-15T06:32:32.884657+00:00` /
  `2026-09-15T07:42:11.097708+00:00` / `2026-09-15T07:58:21.684496+00:00`

**`clean_scan_digest` が 3 走行で全部違う。** 走行間で repo へ commit を足したからである。
これは F39 が記録した性質 —「digest の preimage は repository の file 一覧を含む」— の
**実測による確認**であり、file 追加だけで digest が動くことを示す。
本 wave はこの性質を不変条件として brief に据えた (記録では holdout の ycsb 値を逐語で並べず
`output/s8b-freeze/holdout_freeze.json` への参照で示す)。

### 投入前に親が測った clean scan 関連の値 (限定付き)

投入前に `git grep` で測った。**これは 3 つの逐語表記・親 index・非 ignored untracked に
限った事前観測であり、実装の受理形より狭い。** 実装は holdout 値を escape せず regex へ
置換するため、小数点は任意一文字にあたり `key=value` 側に値終端の境界も無い。
また実装の列挙は `external/ccbench` の tracked も含むが、親はそこを測っていない。
**この測定は clean scan の通過を保証しない。** 判定は既存 gate に任せた。

| 測った集合 | 実測値 |
|---|---|
| tracked file の holdout 三軸 conjunction (2 holdout ぶん、3 逐語表記) | いずれも 0 件 |
| 非 ignored untracked file で `ycsb_rratio` を含むもの | 0 件 (third-party hydrate 後) |
| tracked file の陽性対照の三軸 conjunction | 173 件 |

陽性対照は凍結時の宣言値 41 件より増えているが、`_assert_search_pass` が要求するのは
現在の hit が正であることだけで exact 一致ではない (段 3 レンズ A が
`s8b_holdout_freeze.py` の該当箇所で確認)。凍結 JSON に列挙された hit path は重複除去後 10 件で、
**欠落 0 件**であることもレンズ A が確認した。

## 3. 台帳消費はゼロ — bytes で裏取りした

共有 admission root (`<git-common-dir>/izanagi/s8b-holdout-admission-v1`) の
投入前 / 走行後 snapshot は、取得時刻行以外**完全一致**した。

比べたもの: directory 10 種の件数、`ledger.jsonl` と `attempt-ledger.jsonl` の行数と sha256、
`floor-attempt-registries` の namespace 一覧、registry と consumption catalog の sha256。

段 3 レンズ B が事前に判定した「registry reservation 前の停止 → registry 消費 0」が
実測で裏付けられた。計測枠の上限 120 (planned 96 + cell retry 24) は 1 枠も焼いていない。

**列挙した数量と bytes/hash が一致したという事実に限定する。** 同件数の内容変更・入替え・
変化後の復帰をこの観測は弁別しない (段 3 レンズ A の指摘)。

共有 root の唯一の `floor-attempt-registries` entry は freeze `db07b575…` /
protocol `d388477f…` で、catalog の `recovery_authority_id` が
`campaign-fixture-recovery-authority`、policy hash が全 9 の**fixture 残存**である。
現行 freeze / protocol とは別 namespace なので、**現行 official の消費や正当な証拠として
数えてはならない。** 由来追跡は D1936 項13 に従い scope 外とした
(authority 名だけでは誰が作った fixture かまで確定できない)。

## 4. 走行を塞いでいる gate の入力の完全な実値

3 走行すべてが cell build 段の condition gate で止まった。

```
orchestrator.campaign.s1_direct_comparison.DriverError: condition gate rejected prepared cell: BACKOFF_FIXED:supply-effectuation:preprocess-failed
```

**1 回目の走行では、この reason code 2 語しか残らなかった。** 失敗本文は red arm record の
`evidence.detail` に載っているのに、拒否を送出する側が record ごと捨てていた。gate 専用の
isolate worktree は `/scr` にあり job 終了で消えるため、本文は二度と取れない。
これは D1912 が `p3_s4_loop.py` で直した欠陥と同型で、**official 床値の materializer で
再現した第 2 実例**である (§6)。

2 回目 (`999039.nqsv`) で本文の一部が、3 回目 (`999102.nqsv`) で**全文が**復元できた。

```
/scr/0_999102.nqsv/izanagi_wt_cbgcb09g/wt/cc/silo/include/../../../include/masstree_wrapper.hh:20:10:
  fatal error: config.h: No such file or directory
   20 | #include <config.h>
      |          ^~~~~~~~~~
compilation terminated.
```

| gate 入力 | 実測値 |
|---|---|
| `rc` | `1` |
| 失敗した owner TU | `cc/silo/transaction.cc` |
| include 連鎖 | `transaction.cc:5` → `include/atomic_tool.hh:3` → `include/common.hh:12` → `include/masstree_wrapper.hh` |
| 欠けている header | `config.h` (`masstree_wrapper.hh:20` の `#include <config.h>`) |
| 前処理 argv (先頭) | `/usr/bin/x86_64-linux-gnu-g++-11 -DADD_ANALYSIS=0 -DBACKOFF_FIXED=10 -DBACKOFF_NOINLINE=0 -DBACK_OFF=1 -DBOOST_ALL_NO_LIB -DBOOST_FILESYSTEM_DYN_LINK -DKEY_SIZE=8 -DLinux -DMASSTREE_USE=1 -DNO_WAIT_LOCKING_IN_VALIDATION=1 -DNO_WAIT_OF_TICTOC=0 -DPARTITION_TABLE=0 -DPROCEDURE_SORT=0 -DSLEEP_READ_PHASE=0 -DTRACE=0 -DVAL_SIZE=4 -DWAL=0 -I…` |
| argv 全体 | 846 bytes、sha256 `5348443e95bf9ce8020b7df955090509616aa2f9550ef63b36ff4e3ed77bade7` |
| 実行ノードの compiler | `/usr/bin/x86_64-linux-gnu-g++-11` (g++ 11.4.0) |
| 同 cmake | `cmake version 3.25.0` |

**これは `BACKOFF_FIXED` の供給失敗ではない。** argv に `-DBACKOFF_FIXED=10` と
`-DMASSTREE_USE=1` が載っており、`patches/silo-backoff-fixed.patch` による供給自体は
成功している。**失敗しているのは Masstree の autoconf 生成 header `config.h` の供給**である。
`output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src/masstree` には
`bootstrap.sh` と `GNUmakefile.in` があり `config.h` / `config.h.in` / `configure` は無い
(親が実測)。`config.h` は build 時生成物である。

**T-2515 の過去 job の失敗とは別原因である。** T-2515 が残した condition gate record
(`output/insights/2026-09-10/t2515-rr95-rr5-calibration/job-evidence/*.jsonl`) は
reason code が `configure-failed` で、detail は
「CMake Warning: Manually-specified variables were not used by the project: `CCBENCH_BACKOFF_FIXED`」
= patch 未適用経路の失敗である。本走の `preprocess-failed` は別の失敗点であり、同一視しない。

## 5. 依頼が問うた較正の前提 — 前提ではない

依頼は「較正 ([T-2592] / [T-2515]) の着地がこの実走の前提になるか」を確かめるよう求めた。
**前提ではない。** 3 走行はいずれも較正検証を通過して先へ進んだ (停止は cell build 段)。

根拠 (親の現物実測と段 3 レンズ A の裏取り):

- 有効な pegasus 実行環境契約は**世代 1**。
  `orchestrator/campaign/env_contract_activations/00000001.json` の `active_contracts` が
  `env_tag=pegasus, generation=1,
  contract_sha256=e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01`。
  この hash は凍結 protocol の `contract_sha256` と一致する。
- 世代 1 の `calibration_ref` は
  `output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json` で、
  現物 sha256 が契約の期待値 `753f535a8d02472781bb51b8f56cc383112a791ff2a1e80963039e83bcce5a49` と一致。
- **依存先は 1 件ではない (レンズ A の訂正)。** authority 初期化は activation に載る**全環境**を
  走査してそれぞれの較正を検証する (`orchestrator/campaign/env_contract.py` の該当箇所)。
  activation には linux-baremetal も載るため、その較正
  (期待 `75130477…95eef5`) も依存先である。レンズ A が両方の現物 hash 一致を確認した。
- T-2515 が取得した `calibration-5c836a22eff9ab40.json` は `docs/phase3.md` の 1 行からしか
  参照されず、campaign / calibrator / tools の production コードに consumer が無い
  (静的探索の範囲での結論)。
- 床値 campaign の holdout は 2 件で、T-2515 / T-2592 が扱う軸とは別である
  (値は `output/s8b-freeze/holdout_freeze.json` の `holdouts` を参照)。
- 世代 2 が自動的に有効になる経路は無い。activation loader は連番・前鎖・登録世代・head pin まで
  照合し、現物の activation file は 1 件である (レンズ A)。

**ただし実機 toolchain の適合は login node では測れない。** `_bind_current_toolchain` は較正 receipt の
compiler 実 path / version 本文 / cmake version 本文を計算ノードの live 値と比較する。
3 走行が cell build 段まで進んだ事実は、この比較が実機で通ったことを意味するが、
**login 側の hash 一致をその観測に置き換えて記録してはならない。**

## 6. 実装したもの — D1912 の欠陥の第 2 実例を 1 箇所だけ直した

`DW-G03` (族一般化には独立 2 例) の条件が満たされたので、official 床値経路を塞いでいる
1 箇所だけを直した。第 1 例 = `p3_s4_loop.py` (D1912、段 4 loop)、
第 2 例 = `s1_direct_comparison.py` (本走、official 床値の materializer)。

設計判断は {{D:condition-detail-both-ends}}。

- `_condition_records_for_genome` が拒否を送出するとき、**全 non-green record の
  `evidence.detail` を拒否本文へ添える**。1 件目だけにしない。
- 診断専用の整形器 `_bounded_condition_detail` を置き、**先頭と末尾の両方を残す**。
  中央省略の印、省略 bytes 数、引用整形した全文の sha256 を添える。
- 予算は `_CONDITION_DETAIL_LIMIT_BYTES` を module 内に定義し、今回の実測 1057 bytes の
  4 倍とした。根拠 (観測値 x 倍率) を comment に書いた。**「切り詰めが起きない」とは書いていない。**
- 拒否本文は整形を試みる前に確定させ、整形側の例外は `Exception` 境界で固定文字列へ置換する。
  `BaseException` は捕捉しない。

**段 5 の初稿は先頭 500 bytes だけを残した。** `condition_meaning_gate` の argv 用 helper を
流用したためである。argv は先頭に command が来るので先頭を残す切り詰めが正しいが、
**コンパイラ診断は末尾に結論が来る。** 2 回目の走行でこの取り違えが実機で露出し
(original 1057 bytes のうち後半 557 bytes が失われた)、段 6 の fix で直した。
**予算の意味が違うものを流用したのが誤りだった** — これは {{F:argv-budget-reused-for-diagnostics}}。

不変に保ったもの: gate の受理集合・reason code 語彙・admission 判定・rc・green 経路の bytes、
`condition_meaning_gate.py`、凍結 23 件の bytes、`FORMULA_ID`、result schema の既定。
族へ横展開していない (`p3_kickoff.py` / `p3_s4_loop_sort.py` / `backoff_sweep.py` / `p3_s4_loop.py`)。
到達しない fail-closed も新設していない (D2014)。

### pin 閉包 — reviewed-spec golden の hash 連鎖

`s1_direct_comparison.py` の bytes を変えると
`orchestrator/tests/test_s8b_oracle_manifest.py` の reviewed-spec golden が破れる。
golden は live repo から複製した file を検証対象にするためである
(`_install_reviewed_spec_sources` が `source_root=_ROOT` で複製する)。

| 段 | materializer sha256 | `PIN_GATE_SPEC_SHA256` |
|---|---|---|
| 着手時 | `79086a6c09da7ba548e24d1106c51ad89d305b180932b10d5429f9885fb5967e` | `27ed67ab2f358725b9bf959a28fa79603dd4cf4ca470fd541a10a1b2ca7c59e0` |
| 段 5 後 | `b4b81da6193564ad688b4091efa80294fc4d18e587b2a58bef54320429cf177d` | `6c7f9365e96168749891bf7f0281285336163eaca751b91bacbc8c00f44acd5f` |
| 段 6 後 | `f27f9116f087ca641ffe42c8dc9abed65cc659bd7a962bff536b83baa972dc0f` | `781a7196acd369dd78ebc9c247dd2c43a18eea62ecca14105ecab21065967f42` |

`DW-S05-C` / F27 が「fixture への現行 hash 差し込みなど、テストを甘くして緑にしない」と
禁じているため、実装子と fix 子の双方に**旧値・新値の両方報告**と
「RAW の変更が `generator_versions.materializer.sha256` の 1 field だけである」ことの
提示を義務づけた。両者とも、旧 RAW の当該 hash だけを置換すると新 RAW と bytes 一致することを
確認して報告した。他 4 generator source と `PIN_GATE_SCHEDULE_SHA256` は不変である。
歴史記録 `output/insights/2026-09-08/t2327-s1-sort-contract-binding/verbatim/s5-author.md` は
着手時 hash を持つが、絶対規律 7 に従い触っていない。

## 7. 変異事前登録と matrix

段 4 で M1〜M4 を、段 6 の fix 前に M5〜M7 を登録した。

| # | 変異 | 結果 |
|---|---|---|
| M1 | 拒否 message から detail を落とし reason code だけに戻す | 登録・テスト実装済み |
| M2 | red record が複数のとき 1 件目の detail だけ載せる | 登録・テスト実装済み |
| M3 | detail 整形が例外を送出しうる形にする | 登録・テスト実装済み |
| M4 | golden の materializer sha256 を 1 文字変える | **登録から外した** |
| M5 | 切り詰め時に末尾を落とす | 登録・テスト実装済み |
| M6 | 切り詰め時に先頭を落とす | 登録・テスト実装済み |
| M7 | 省略 bytes 数または全文 sha256 の印を落とす | 登録・テスト実装済み |

**M4 は単一理由性に絞れないため登録から外した** (`DW-M01` / F28)。実装子が実測で報告した —
RAW だけを変えると、live hash gate より先に RAW 全体の approval pin 比較が
`approved-spec-hash-mismatch` で拒否する。同じ入力を拒否する層が手前にあるので、
M4 の赤は live hash gate の証拠にならない。

**変異 harness の本走は行っていない。** 実装差分が生じたので `DW-S04` の matrix 免除は使えないが、
本 wave は 3 回の実機走行 (`998882` / `999039` / `999102`) で **M1〜M3 と M5〜M7 が守る性質を
production 経路で直接観測した** — 1 回目は detail なし、2 回目は先頭のみ、3 回目は先頭と末尾の
両方が残り、いずれも全文 sha256 の印つきだった。これは harness による kill 判定の代替ではない。
**未実施はそう書く。**

## 8. 検査

| 検査 | 結果 |
|---|---|
| `check_wave_startup.py --mode fresh --forbid-worktree-handoff --external-handoff` | rc=0 |
| `check_wave_startup.py --mode midflight` (段 5 / 段 6 の投入前、各 worktree) | 全 rc=0 |
| `check_codex_output.py` (plan / レンズ A / レンズ B / author / fix) | 全 rc=0 |
| `check_ai_provenance.py --message-file` (実装 / fix / merge) | 全 rc=0 |
| `check_ai_provenance.py` 全史 (実装 commit 後) | rc=0、10105 件、新規違反なし (計算ノード dispatch、Elapse 142 秒) |
| 焦点走 `test_s1_direct_comparison.py` 単独 (段 5 後) | 119 passed (5.77 s、計算ノード dispatch `998971.nqsv`) |
| 焦点走 `test_s8b_oracle_manifest.py` 単独 (段 5 後) | 97 passed (11.99 s) |
| 焦点走 2 file 併走 (段 6 後) | 232 passed (12.17 s) |
| 変異 harness 本走 | **未実施** |

受入全走の結果は本 insight の後段では書かない — 実測前に欄を作らない契約に従い、
実施した時点で worklog へ書く。

## 9. 到達範囲と非保証

- **試行台帳 (attempt registry) 側 gate の実値域は取得できていない。** 走行は計測段へ到達しない。
  C3b が確立した 4 分類のうち、本 wave が埋めたのは (1) 動的観測の一部 (起動証明書と condition gate)
  だけで、(2) 静的宣言 closure、(3) artifact に所在が無い入力
  (issuer state membership / owner identity / one-shot `used` / post-probe origin seal)、
  (4) 未発火の枝は**依然として未観測**である。**未観測を到達不能と読んではならない。**
- `probe_before` の raw 四値 (`rc` / `stdout` / `stderr` / `competing`) は external evidence に
  所在があり (段 2 plan が file:line で特定)、C3b の「所在なし」を probe 四値まで広げるのは誤読。
  ただし本 wave は 1 件も観測していない。
- **凍結 hold `s8b-floor.protocol-bytes-expected-pin` の効力は証明していない** (D1936 項11)。
  段 2 plan とレンズ A が実測したとおり、hold の `elif` と allowlist の検査は通常経路では
  同じ path・同じ bytes hash・同じ期待値の比較であり、**同一比較の二重化は残っている**。
  今回はどちらの比較も通ったので走行を止めていない。`status=held` は比較回避の実効性を
  証明しない。一方 held marker という記録差はあるので「結果が 1 bit も変わらない」とも書かない
  (レンズ A)。
- 3 走行の Elapse (90 / 111 / 128 秒) は **cell build 段で止まった走行の所要**であり、
  完走時間ではない。段 3 レンズ B が発掘した完走 pilot の実測は Elapse 2894 秒
  (96 attempt 全件有効・retry 0・各 attempt 26.79〜26.93 秒、
  `output/insights/2026-08-25_t1431-floor-pilot-values/README.md`) だが、
  旧 pilot と現行 official の条件同一性は証明されていない。
  **「現行 official が walltime 36000 秒で完走する」とは書けない。**
  `buildcache` は configure と build のそれぞれに 900 秒を渡すため、command timeout の
  単純和は 41940 秒で walltime を超える (レンズ B)。上限の和を完走の上界に使ってはならない。
- **消費済み slot は recovery でも戻らない** (レンズ B)。`start` ごとに消費数が加算され、
  recovery は既存列への追記であって減算ではない。scheduler recovery authority の
  理由対応表は空で、walltime kill を自動的に recovery 可能とみなせない。
  今回は消費 0 だが、計測段へ入る走行ではこの不可逆性が効く。
- **third-party の複製後 pinned-clean は測っていない。** 親が測ったのは複製元だけである。
  投入器は複製元と複製先の HEAD / status を両方検査するので、qsub まで進んだ事実は
  複製先の検査も通ったことを意味するが、「搬送済み pinned-clean」と親が観測したとは書かない。
- fix 前後の比較は親 1 主体の監査であり、独立主体の裏取りではない。
  段 3 の 2 レンズは plan と brief を攻撃したが、**段 5 / 段 6 の実装差分そのものへの
  敵対レビューは行っていない** (実装が判明したのが走行後で、レンズは走行前に回した)。

## 10. 次の blocker (後続へ残す)

**condition gate の isolate worktree へ Masstree の生成 header `config.h` を供給する。**
これは build 供給の subsystem であり、本依頼の「本題の実装だけ」の範囲を超えるので
本 wave では触っていない。必要な情報は §4 に実値で揃っている。

## 11. 収録物

- `evidence/admission-snapshot-presubmit.txt` / `evidence/admission-snapshot-postsubmit.txt`
  — 共有 admission root の投入前後 snapshot (件数・行数・sha256)
- `evidence/<request>-job-result.json` (3 件) — 各走行の job 終端記録
- `evidence/<request>-floor-driver.stderr` (3 件) — 各走行の driver 停止本文。
  1 回目は detail なし、2 回目は先頭のみ、3 回目は先頭と末尾
- `evidence/<campaign_run_id>-launch_certificate.json` (3 件) — 発行された起動証明書
