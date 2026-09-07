# [T-2228] 残り 3 driver の関門を実測した — 通ったのは 1 箇所だけで、通らなかった 3 箇所はすべて同じ原因だった

日付: 2026-09-07 / wave: `dev-wave-t2228-driver-gate-liveness` / branch `worktree-dev-wave-t2228-driver-gate-liveness`
基点 main: `d19d2182f`、記録前に `e28dfe2c5` を取り込み。authority: none / default_effect: no-state-change。

## 要点

1. **`backoff_sweep` の driver 段の関門は緑で通った。** inert 経路 (`BACKOFF_FIXED=-1`、
   `stock_comparison=True`) の supply 腕が `stock-inert-preprocess-root-location-only`、
   meaning 腕が `declared-meaning-observed`、family が `admitted=true`。
   関門が inert 経路まで通ったことを実体で確認できたのは、A-2 経路に続いて 2 例目である。
2. **同じ driver の screening 経路にある 2 つ目の関門は赤だった。**
   `screening_driver._run_condition_gate_for_genome` が
   `BACKOFF_FIXED:supply-effectuation=red/preprocess-failed` を返す。
3. **`backoff_repro` の関門は赤だった。** 歴史 pin `dff0f1e` の木で 3 request すべてが
   supply 腕で `preprocess-failed`。さらに現行 pin `511c953` の木では、関門に到達する前に
   `patchharness.assert_pinned_clean` が pin 不一致で止める。
4. **`s1_direct_comparison` は関門へ到達しない。** `load_verified_freeze` が
   generator の sha256 不一致で失敗し、`prepare_cell` (関門の所在) より前で止まる。
   加えて凍結入力の 18 cell に `BACKOFF_FIXED=-1` は 1 件も無く、**inert 経路は
   production の入力からは構築されない**。緑でも赤でもなく、到達不能である。
5. **通らなかった 3 箇所の原因は 1 つに揃う。** いずれも関門の CMake configure へ
   準備済みの FetchContent base を渡さない呼び出しであり、owner TU の preprocess が
   `masstree_wrapper.hh:20:10: fatal error: config.h: No such file or directory` で落ちる。
   通った 2 例 (A-2 と `backoff_sweep` の driver 段) はどちらも
   `buildcache.prepare_masstree_fetchcontent` を呼び `-DFETCHCONTENT_BASE_DIR` を渡している。

## 実行 identity

- 実測 commit: `c3447612e62ec7ec93d1662bfca45c594ff0a31b` (probe と PBS はこの HEAD に束縛)
- 実測 1 回目 (レビュー前の probe): request `980554.nqsv`、`bnode018`、
  evidence `/work/1/SFC/tanab/izanagi-job-evidence/t2228/attempt-20260907a/`、
  投入 HEAD `e2df24048a1b8a16085d91a36d82a81e3011fbdc`
- 実測 2 回目 (段 6 レビューと fix の後): request `980676.nqsv`、`bnode020`、
  evidence `/work/1/SFC/tanab/izanagi-job-evidence/t2228/attempt-20260907b/`、
  run id `836ca45dacc74efd840e1fee65495432`
- **2 回は別ノードで同じ結果を出した。** 本 README の値は 2 回目 (レビュー済み probe) を正とする。
- compiler `x86_64-linux-gnu-gcc-11`、cmake 3.22.1、外部 network 不通
  (`github.com:443` が `Temporary failure in name resolution`)
- CCBench pin: 現行 `511c9538e4e8efa54b45cda62e72389ed3b706ec`、repro の歴史 pin `dff0f1e`
- 3 driver は 1 job・1 process で s1 → repro → sweep の順に走った。
  `drivers_completed_before_publish` が厳密な前置鎖を成すことで同一 process 由来を機械的に示す。
- production 4 file の sha256 は実測時点の main と一致し、production は 1 byte も変えていない
  (`backoff_sweep.py` `1b64f897…`、`backoff_repro.py` `6aede5cf…`、
  `s1_direct_comparison.py` `049642ca…`、`condition_meaning_gate.py` `2fc0d490…`)。

## 1. driver ごとの結果

| driver | 関門呼び出し | configure 引数 | 結果 |
|---|---|---|---|
| `backoff_sweep` (driver 段) | `backoff_sweep.py:378-392` の `_require_backoff_condition_gate` | `-DFETCHCONTENT_BASE_DIR=<準備済み base>` | **緑** (`admitted=true`) |
| `backoff_sweep` (screening 段) | `screening_driver.py:166-206` の `_run_condition_gate_for_genome` | `genome.cmake_defines()` だけ | **赤** `preprocess-failed` |
| `backoff_repro` | `backoff_repro.py:72-83` (共通 helper) | 無し | **赤** `preprocess-failed` × 3 request |
| `s1_direct_comparison` | `s1_direct_comparison.py:916-921` の `_condition_records_for_genome` | 無し | **到達不能** (freeze 検証で停止) |

### 1.1 `backoff_sweep` の driver 段 — 緑の中身

`write-heavy` を最小 screening (`screening_enabled=True`, `screening_fixed_us=2`) で
production の `run_workload` から走らせた。関門は 2 request を発行した。

| request | 腕 | terminal_status | reason_code |
|---|---|---|---|
| `BACKOFF_FIXED=-1` (inert、`stock_comparison=true`) | supply-effectuation | green | `stock-inert-preprocess-root-location-only` |
| `BACKOFF_FIXED=-1` | runtime-meaning | green | `declared-meaning-observed` |
| `BACKOFF_FIXED=2` | supply-effectuation | green | `requested-default-preprocess-different` |
| `BACKOFF_FIXED=2` | runtime-meaning | unestablished | `meaning-witness-undeclared` |

family admission は `admitted=true`、`use_class=raw-measurement`、
`unestablished_meaning_macros=['BACKOFF_FIXED']`。

**緑の意味の限定。** supply 腕の緑は「patch 済み木と別の stock 木で、owner TU を同じ
compile command で preprocess した結果が、置き場所由来の差だけで一致した」ことを支持する。
meaning 腕の緑は「materialized source の `-1` 枝が宣言どおり stock の適応 backoff 文を選ぶ」
ことを支持する。**実行時に適応 backoff が動いた証拠ではない。**
また admission は meaning が `unestablished` でも通るので、
`admitted=true` を「全 macro の意味が確立済み」と読んではならない。

**被覆の限定。** 測ったのは 2 点 screening の request family である。
通常の全点 sweep は `-1,2,5,10,25,50,100` の 7 値を 1 つの family として admission を取るので、
本 wave の緑は**その full family admission の代用にならない**。
なお関門呼び出しは `screening_enabled` の分岐より前にあるので、driver 段の関門結果自体は
screening の有無で変わらない。

### 1.2 通らなかった 3 箇所 — 同一の原因

赤の原文 (repro、3 request とも同じ):

```
process returned rc=1; stderr=b'... /external/ccbench/cc/silo/include/../../../include/
masstree_wrapper.hh:20:10: fatal error: config.h: No such file or directory
   20 | #include <config.h>
      |          ^~~~~~~~~~
compilation terminated.
'
```

`config.h` は masstree の autotools が生成する header で、
`buildcache.prepare_masstree_fetchcontent` が共有 base へ用意する。
CCBench の CMake は masstree / mimalloc / googletest を configure 時に GitHub から
`FetchContent` で取得する (`external/ccbench/cmake/ThirdParty.cmake:34-55`)。
計算ノードは外部 network が無く (本走で実測)、third-party は
`/work/1/SFC/tanab/izanagi-thirdparty-cache` へ事前取得して offline 配置する運用である。
関門の supply 腕は request ごとに要求側と対照側の 2 回、毎回新しい build root へ
cmake configure を走らせる (`condition_meaning_gate.py:1653-1665`)。
`-DFETCHCONTENT_BASE_DIR` を渡さない呼び出しでは、この build root が
準備済み base を参照できない。

### 1.3 `backoff_repro` の現行 pin — 関門より前で止まる

`backoff_repro.CCBENCH_COMMIT` は `dff0f1e` (歴史 pin) だが、submodule の現行 pin は
`511c9538` である。`patchharness.applied` は patch 適用前に
`assert_pinned_clean` を呼ぶ (`patchharness.py:192-195`)。実測した原文:

```
patchharness: HEAD (511c9538e4e8) が pin (dff0f1e) と不一致 — 別版の tree に patch を当てない (fails-closed)
```

driver 自身は submodule を歴史 pin へ移さず、production の投入 script も無い。
したがって **現状のまま `backoff_repro` を起動すると、関門に触れる前に止まる。**
本 wave は歴史 pin を置いた木を別に用意して、その先の関門まで測った。

### 1.4 `s1_direct_comparison` — 2 つの独立した理由で到達しない

**(a) freeze の検証で止まる。** `load_verified_freeze` の実測原文:

```
generator sha256 不一致: recorded=a7c41a8175b2edeef9e6bb7b8ad4b36991668d709e6d1f5604cd80a81287d0fa
actual=54d95622e50d991410fa273a39aa12daa634c62be11f45262dc7c2aef4dde5b5
```

凍結文書が束縛する generator は `orchestrator/campaign/s1_measurement_freeze.py` で、
その最終変更は `135836be0` (2026-08-12) である。凍結文書の `frozen_at_head`
(`2066ce6b47c6…`) は現 repo に object として存在しない。
`run_role` は `prepare_cell` より前にこの検証を通るので、関門へ到達しない。

**規律 7 に照らした位置づけ.** これは「凍結された当時の測定が無効になった」という意味ではない。
過去の s1 の測定と判定は当時の事実として残る。言えるのは
**現行 main では s1 driver を新しく起動できない**ことだけである。

**(b) 凍結入力に inert cell が無い。** 親が凍結成果物を直接読み (検証 loader は上記のとおり
止まるため)、`schedule_for_role` の 4 role すべてで 18 cell を展開した。

| configuration | 関門対象 macro と値 | inert か |
|---|---|---|
| `backoff_fixed_best` | `BACKOFF_FIXED` = 2 / 5 / 10 | 非 inert |
| `system_gate`, `ident_all` | `BACKOFF_TRIGGER_GATING` = 1 (既定 0) | 非 inert |
| `sort_best` | `SORT_VARIANT` = 1 (既定 0) | 非 inert |
| `p2_2_flag_opt`, `stock_common` | 無し | request 0 件 |

`BACKOFF_FIXED=-1` の cell は 0 件である。したがって **s1 は production の入力からは
inert 経路の request を構築しない。** また 18 中 6 cell (`p2_2_flag_opt` と `stock_common`)
は関門対象 macro を持たないので、`_condition_records_for_genome` が
`s1_direct_comparison.py:272-274` で即 return し、**関門が 1 record も発行しない**。

## 2. 何が成果物に効くか

- 関門は 2026-09-01 (`0218acc61`) に driver 全体へ義務化された。3 driver の最後の
  production 走行はいずれもそれ以前である (`backoff_sweep` 2026-06-22、
  `backoff_repro` 2026-06-28、`s1_direct_comparison` 2026-07-16、各 campaign WAL の最終 record)。
  **義務化以降、この 3 本は 1 度も関門を通っていなかった。**
- したがって「関門が守るはずの命題」が、この 3 本が過去に産んだ値へ遡って適用されているわけではない。
  過去の値は当時の事実として残り、本 wave はそれを無効化しない (規律 7)。
- 一方で **今この 3 本を起動して新しい値を取ることは、現状ではできない。**
  `backoff_sweep` は driver 段を通っても screening 段で止まり、`backoff_repro` は pin で止まり、
  `s1` は freeze 検証で止まる。
- 修正 (関門の configure へ FetchContent base を供給する、pin を揃える、freeze を作り直す) は
  **本 wave では実装していない。** 関門を通すためだけの修正は規律 2 に触れるため、
  裁定パッケージへ返す (`verbatim/s4-adjudication.md` の scope 外 8 件)。

## 3. 予測と実測の対応 (予測は予測として)

段 2 plan と親の読みは「sweep 緑、repro 赤、s1 赤」を事前に予測し、後 2 者の主因を
「空の `configure_args` により実 CMake configure が準備済み FetchContent base を使えない」と
書いた (`verbatim/s2-plan.md` の事前予測節)。実測はこれを支持したが、**落ち方は予測と違った**。

- 予測: `configure-failed` または `configure-timeout` になる。
- 実測: configure は成功して `compile_commands.json` を作り、その後の
  **owner TU の preprocess** が `preprocess-failed` で落ちた。

s1 については予測が外れた。予測は「FetchContent base 未供給で赤」だったが、
実測ではその手前の freeze 検証で止まり、さらに inert 経路自体が構築されないことが分かった。
この 2 点は段 2 plan も段 3 の敵対相談 2 本も見落としており、親が凍結成果物を
直接読んで反証した (`verbatim/s4-adjudication.md` の裁定 0)。

## 4. 開発検査

- 段 3 敵対相談 2 本 (`verbatim/s3-lensA.md` / `s3-lensB.md`)。
  lens A は real 11 件 / refuted 4 件、lens B は real 16 件 / refuted 6 件。
  主な採用は「主張を seam liveness へ狭める」「`stock_comparison` は分岐スイッチでない」
  「`unestablished` は admission を通る」「恒真な検査 3 件を保証に数えない」
  「1 job 1 node にしないと driver 差を driver に帰属できない」。
- 段 6 敵対レビュー 2 本 (`verbatim/s6-reviewA.md` / `s6-reviewB.md`)。
  must-fix は A が 5 件、B が 4 件 (1 件は A と重複)。すべて fix 子が閉じた
  (`verbatim/s6-fix1.md` / `s6-fix2.md`)。
- **実測はレビューと fix の後にもう 1 度取り直した。** 1 回目 (`attempt-20260907a`) は
  レビュー前の probe が出した証拠であり、2 回目 (`attempt-20260907b`) が本 README の正である。
  2 回は別ノードで同じ結果を出した。
- 焦点走: `run_tests.py` で 8 file、rc=0、**1297 passed / 4 skipped**。
  対象は新 test file、`test_plain_runner_coverage.py`、`test_hooks.py`、`test_codex_hooks.py`、
  `test_check_docs.py`、`test_ccbench_spawn_sites.py`、`test_official_perf_closure.py`、
  `test_paper_story_a1_job_contract.py`。
- 変異 matrix (`mutation-spec.json`、sha256 `5b4e7b2b9e582675e3a378a8c8368d143da92d2246832297cec421938fb7f2aa`):
  baseline 緑、**M1〜M7 の 7/7 KILLED**、SURVIVED 0 / MISMATCH 0 / TIMEOUT 0 (`mutation-ledger.json`)。
  1 巡目 (`mutation-spec-round1.json` / `mutation-ledger-round1.json`) は
  M1 が MISMATCH (期待 node 集合が不完全)、M3 が SURVIVED だった。
  **erratum:** M3 の初回照準 (`_gate_success` の `admitted is True` を外す) は、
  手前の inert request 絞り込みが同じ入力を先に弾くため単独では発火しない冗長 gate だった。
  DW-M02 に従い実効 gate (`_current_pin_control_success` の HEAD 一致判定) へ再照準した。
  M1 は KILL されていたが期待 node に `test_m5` が漏れていたので集合を完成させた。初回台帳は消していない。
- 受入全走: 記録 commit を含む最終 tip に対して 1 回だけ走らせ、receipt は land が束縛する。

## 5. 新しく分かった作法

`tools/pegasus/` へ実行体を 1 つ足すと、次の 5 箇所が同期を要求する。
1 回の投入では 1 件しか露見しない (本 wave は焦点走 2 回でようやく全部出た)。

1. `tools/pegasus/admission_registry.json` (正本)
2. `docs/pegasus-runbook.md` §7.0 の投影表 — `tools/check_docs.py` が集合完全一致を要求
3. `tools/pegasus/README.md` の inventory — 同じく `check_docs.py`
4. `orchestrator/tests/test_hooks.py::_PEGASUS_EXPECTED_CLASSES` (literal golden)
5. `orchestrator/tests/test_hooks.py::_PEGASUS_EXPECTED_ENTRIES` (literal golden、entry × 4 field)

登録すると `hooks/guard_bash.py` が login node でその path を含む実行を拒否するようになる。
これは意図どおりの防壁であり、迂回してはならない。

## 既知限界と scope 外

- 測ったのは「root を束縛して関門を呼ぶ production の seam」の生死である。
  `backoff_repro` と `s1` については、CLI 入口から関門までの**到達性**は測っていない
  (repro は `_conditioned_backoff_patch`、s1 は 1 cell の `prepare_cell` に入った)。
  s1 の結論は選んだ cell と configuration にしか及ばない。
- `backoff_sweep` の通常 7 値 family の admission は未測定。
- 関門の緑は「実行時に adaptive backoff が動いた」ことの証明ではない (§1.1)。
- network 起因の赤と driver 固有の赤を分ける policy は定めていない。
  reason code と network 観測の両方を記録するに留めた。
- 修正 (FetchContent base の供給、pin の整合、freeze の再生成、s1 の全 configuration 被覆) は
  いずれも実装せず裁定へ返した。

## 出所

- brief / plan / 相談 / 裁定 / 実装 / レビュー / fix の逐語: `verbatim/`
- 変異台帳: `mutation-ledger.json` (本走) / `mutation-ledger-round1.json` (初回、erratum)
- 実測 evidence: `evidence/attempt-20260907a/` と `evidence/attempt-20260907b/`。
  `sweep.json` は preprocess 証跡 (`evidence` field) を外した縮約版で、
  外した件数・全文の所在・全文の sha256 を各 file の `_reduction` と
  `evidence/full-file-sha256.json` に書いてある。原本は
  `/work/1/SFC/tanab/izanagi-job-evidence/t2228/` 配下。
