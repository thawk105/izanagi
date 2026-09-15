# t316 の条件関門と build 木の不一致を解消し、実経路で S6 を go まで到達させた

日付: 2026-09-15 / wave: `dev-wave-t2607-t316-gate-tree`
対象: [T-2505] / [T-2519] / [T-2607]

## 一行で言うと

t316 probe は素の CCBench 木を build しながら patch 由来の define を要求していた。
patch を当てた使い捨て木を関門と両 build で共有する形へ変え、実経路で
`stock-inert-preprocess-root-location-only` の緑と S6 の go に到達した。

## 直した欠陥は 2 つある

### 欠陥 1 — 要求する条件を、その条件を供給しない木へ渡していた

`_execute_ccbench_build` は `external/ccbench` (patch 未適用) を build しながら、configure へ
`-DCCBENCH_BACKOFF_FIXED=-1` を渡していた。条件関門は requested 側で必ずこの define を足すので、
素の木では CMake が未使用変数警告を stderr へ出す。`condition_meaning_gate._run_process` は
rc=0 でも stderr 非空を `configure-failed` にするため、関門は fail-closed で正しく拒否していた。

**この欠陥には 2 つの原因があり、どちらも単独で赤にする** (D1994)。patch を materialize しても、
CCBench が参照しない 3 変数 (`RULE_LAUNCH_COMPILE`、`IZANAGI_GFLAGS_SRC_HEAD`、
`IZANAGI_GLOG_SRC_HEAD`) は両アームで警告を出し続ける。F855 の恒久対応「driver から未使用変数を
除去」が t316 へ未適用だったためである。**したがって木を揃えるだけでは閉じない。**

親が共有 configure の `-D` 20 件を引き直したところ、CCBench (patch 適用後) が参照しないのは
この 3 件だけだった。特に `CMAKE_C_COMPILER` と `CMAKE_C_COMPILER_LAUNCHER` は、CCBench 本体が
`LANGUAGES CXX` であっても、`ThirdParty.cmake` が FetchContent で取り込む mimalloc が
`project(libmimalloc C CXX)` であるため C が有効化されて使われる。

### 欠陥 2 — 使い捨て木の置き場が sandbox から見えない場所だった (実走で発見)

欠陥 1 を直すと、新しい配線検査が別の赤を出した。sandbox は
`--ro-bind <scratch>/empty-tmp /tmp` で `/tmp` を空 directory の read-only bind に置き換えるが、
`patchharness.checkout` は `os.environ.get("TMPDIR", "/tmp")` の下に木を作る。

**本番でもこれは発火する。** `tools/pegasus/probes/t316_sandbox_backend_probe.pbs` は
`SCRATCH_ROOT=${TMPDIR:-/scr}` を使い、`TMPDIR` をどこでも export しない。実際、修正前の受領証
`output/env/pegasus/t316-sandbox-backend/0:996644.nqsv/receipt.json` の scratch は
`/scr/t316-0_996644.nqsv-jvuhehpn/...` であり、`SCRATCH_ROOT` が `/scr` 直下になっている。
つまりその job で `TMPDIR` は未設定であり、checkout は `/tmp` へ落ちる。inside build は
requested 木を読めない。

`TMPDIR` が未設定または `/tmp` 配下なら `scratch.parent` の下へ木を作る形にした。
scratch の兄弟なので writable bind に覆われず、`/tmp` の置き換えにも隠れない。

## 採った形と、採らなかった形

採った形は A-2 の先例 (`orchestrator/campaign/paper_story_a2_certification.py`) と同型である。
`patchharness.checkout` で使い捨て木を作り、**patch を当てる前に**その木の基底 identity を検査し、
`patchharness.applied` の内側で outside と inside の両 build を行う。関門と両 build は同じ木を使い、
control は素の submodule を直接渡す。`patchharness` の docstring はこの
`with checkout(pin) as sub: with applied(patch, pin, sub):` を正規形として逐語で定めている。

**「関門ごと落とす」形は採れない。** D1625 (ユーザー裁定) が t316 の条件関門について
「許可するのは … どちらか 1 つに exact 一致することだけ」「それ以外の緩和はしない」と定め、
却下欄で「probe の exact 一致検査を外す — 受理集合を gate の表より広げる」を明示的に却下している。
加えて `verdict_s6` の拒否枝 4 本 (family 欠落 / evaluator 未発行 record / 受領証不一致 /
非 inert pair) は inert 要求の有無と独立した現行契約であり、define を消しても外さなければ go にならない。

**この択一は実測では決まらなかった。** 案の不成立は契約上の帰結であって経験的事実ではない。
段 2 のプランと段 3 の 2 レンズが独立に同じ結論へ達している。実測は択一の決定ではなく、
採った案が目的状態へ到達するかの確認に使った。

## 実測

### t316 実経路 (計算ノード)

request `0:999027.nqsv`、queue gen_S、Elapse 98 秒。受領証は
`output/env/pegasus/t316-sandbox-backend/0:999027.nqsv/receipt.json`。

| 項目 | 値 |
|---|---|
| supply-effectuation | green / `stock-inert-preprocess-root-location-only` / comparison `stock-inert-root-location-only` |
| runtime-meaning | unestablished / `meaning-witness-undeclared` |
| family-admission | admitted=true / use_class `raw-measurement` |
| S6 | go (`S6_SANDBOX_BUILD_SUCCEEDED`) |
| S6 の内訳 | `outside_success`・`inside_success`・`trace_disabled`・`source_identity_valid` がすべて true、`failure_stage` は null |
| S7 | go |
| overall | no-go |

overall が no-go なのは S5 (`S5_BUILD_SYSTEM_COMMAND_SIDE_EFFECT_OBSERVED`) と S3 の inconclusive
による。どちらも修正前の 2 走 (`0:996644.nqsv` / `0:996829.nqsv`) でも同じであり、本 wave の
変更面とは無関係な sandbox 封じ込めの所見である。

**時間予算の懸念は実測で解けた。** policy は `probe_deadline_s=5100`、
`s6_minimum_remaining_s=3600`、`ccbench_build_cap_s=1200` (片側) で、実走は 98 秒だった。

### テスト

`orchestrator/tests/test_t316_sandbox_probe.py` は 165 node。これに consumer 4 file
(`test_official_perf_closure.py`、`test_hooks.py`、`test_acceptance_schedule_order.py`、
`test_real_repo_serialization.py`) を足した焦点走は計算ノードで 809 passed / 2 skipped。

### 変異 — baseline PASSED、7/7 KILLED、期待 node 完全一致

台帳は `mutation/mutation-final-ledger.json` (spec は `mutation/mutation-spec-final.json`)。
summary は `KILLED=7 / SURVIVED=0 / MISMATCH=0 / TIMEOUT=0 / matching=7`。
先に全件 SURVIVED 登録の probe 走 (`mutation/mutation-probe-ledger.json`) で観測 node を集め、
その完全集合を期待値にして本走した。

| 変異 | 受理集合への影響 | 期待 node 数 |
|---|---|---:|
| M1 | 関門の admission 拒否を無効化 | 5 |
| M2 | inert exact pair 判定を恒真化 | 3 |
| M3 | reason と comparison の交差組を許容 | 2 |
| M4 | 関門は requested 木、build は素の木へ戻す | 1 |
| M5 | control を patch 済み木のコピーにすり替える | 6 |
| M6 | requested の基底 identity 検査を無条件真にする | 3 |
| M7 | 除去した未参照変数を 1 件戻す | 5 |

**M4 から M7 は本 wave で足した配線検査が無ければ KILL されない。** 段 2 と段 6 のレビュー D は
これらを「既存テストに KILL を保証するものが無い穴」として名指ししていた。
M6 の wrong-head は、probe の拒否を外しても `patchharness.assert_pinned_clean` が先に例外を出すため
帰属が成立しない。段 6 の fix はこれを受けて、wrong-head を観測した直後に pin を正しい値へ戻し、
実 harness の受理を確認したうえで probe の拒否だけを観測する検査を足した。

## この insight が保証しないこと

- **関門の緑は、確認した永続 cache の状態に限る。** t316 は
  `-DFETCHCONTENT_SOURCE_DIR_MASSTREE=/work/1/SFC/tanab/izanagi-thirdparty-cache/masstree` を
  gate と build の共通引数として直指しする。関門は configure と preprocess はするが、masstree の
  `config.h` を生む build 時 custom command は走らせない。今回はその cache に `config.h` と
  `libkohler_masstree_json.a` が実在したので preprocess が通った。**cache を掃除すれば赤へ戻る。**
  緑に到達した既知の 2 例 (A-2 と `backoff_sweep` driver 段、2026-09-07 の
  `output/insights/2026-09-07_t2228-driver-gate-liveness/README.md`) はどちらも
  `prepare_masstree_fetchcontent` で準備した base を使っており、永続 cache を直指ししていない。
  t316 へ同じ準備を入れることは本 wave の scope 外とした。
- **使い捨て木の置き場を決める helper は、同一プロセス内の並行呼び出しで壊れる。**
  `TMPDIR` を一時的に差し替えるため、2 つの呼び出しが交差すると復元順が保証されない。
  本番の呼び手は `observe_s6` の直列 1 箇所だけなので発火する経路を名指しできず、
  仮想リスク向けの機構追加は scope 外として入れていない。**限界として記録する。**
- **関門の緑は「実行時に条件が効いた」ことの証明ではない。** meaning 腕は
  `unestablished` / `meaning-witness-undeclared` のままで、これは t316 の現行契約どおりである。
- **overall の no-go は解消していない。** S5 と S3 は別の起票に属する。
- 本 wave は `orchestrator/campaign/condition_meaning_gate.py` を 1 byte も変えていない。

## 段 3・段 6 が親を訂正した点

- 親 brief は `backoff_sweep` を「案 B の先例」としたが、同 driver の `checkout` は **stock 側**に
  使われており、patch は共有の `ccbench_dir` に当たる。正しい先例は A-2 である (段 2 が訂正)。
- 親 brief は「A-2 の 2 層目 (masstree の `config.h` 不在) が次に出る」と推測したが、確認した cache
  では反証された (段 2 と段 3 レンズ B)。
- 親の暫定裁定「関門が検査していた条件が消えるので防壁の弱体化ではない」は支持されなかった
  (段 3 レンズ A、段 2)。
- 段 2 は案 A 不成立の根拠に「既存テストの契約は一切変更不可」という読みを含めていたが、
  段 3 レンズ A がこれを過剰解釈と判定した。D1625 が独立に案 A を閉じるため結論は変わらない。
