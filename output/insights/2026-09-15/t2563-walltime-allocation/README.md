# T-2563 認定較正の予約式 — 配分であって逐次上限ではない

2026-09-15。branch `worktree-dev-wave-t2563-walltime-refreeze`、統合 commit `f5ba28378`。

凍結式が名乗っていた内訳が job script の実体と一致していなかった。値を 1 つも変えずに、
名と説明を実体へ合わせ、保証しない範囲を成果物の文面へ出した。
**時間式の再凍結は完了していない。** D1971 の「完了扱いにしない」を維持する。

## 何が偽だったか

旧文面は `build_cap(CCBench=900 + gflags=60 + glog=120)(1080)` と書いていた。
これは各ライブラリに一度だけ `timeout` が付くかのように数えている。実体は違う。

| 対象 | 旧内訳 | 実体 | 差 |
|---|---:|---:|---:|
| CCBench | 900 (1 command) | 1800 (configure + build) | +900 |
| gflags | 60 (1 command) | 180 (configure/build/install) | +120 |
| glog | 120 (1 command) | 360 (configure/build/install) | +240 |
| 小計 | 1080 | 2340 | +1260 |

さらに、旧内訳に**項として存在しない**処理が 910 秒ある。

| 処理 | `timeout` |
|---|---:|
| third-party copy (masstree / mimalloc / googletest の 3 回) | 360 |
| pristine source 検証 | 120 |
| attestation probe (static / pre) | 240 |
| qstat | 30 |
| binary hash + `nm` | 120 |
| perf 実体 smoke (候補 2 件 × version + smoke) | 40 |
| 小計 | 910 |

2340 + 910 = **3250 秒**。これが計測前の `timeout` 指定値の和である。
旧文面の 1080 はこれを **2170 秒過小申告**していた。

## 数え方の訂正 (親の誤り)

親は段 1 のアンカー表で計測前を **3230 秒**と書いた。20 秒足りない。
`tools/pegasus/policy.json` の `perf_candidates` は 2 件あり、
第 1 候補の version 成功 → smoke 失敗 → 第 2 候補の version + smoke という経路が到達可能なので
`timeout 10` は最大 4 回走る。親は 1 候補分しか数えていなかった。
段 2 が訂正し、段 3 luna と段 6 r2 が独立に 3250 を再導出した。

## 何を保証しないか

```
計測前の timeout 指定値の和  3250
CLI 予約 (3190 + 360p、p=5)  4990
後処理予約                    600
                             ----
                             8840  >  要求 7200
```

**最大経路の完遂を保証しない。** さらに **8840 自体も上限ではない。**
`timeout` を持たない処理が実在する。

| 処理 | 所在 |
|---|---|
| `git status` (4 箇所) | source 検査 |
| `git worktree add` | CCBench checkout |
| `/proc` 全走査 | 競合 process probe |
| worktree 削除 (2 箇所) | 起動時と終了時 |
| receipt I/O と `fsync` | CLI の公開経路 |
| submit receipt 待ちの最大 60 回の `sleep 1` | 起動直後 |

したがって 3250 も 8840 も「選んだ予約項の部分和」であり、実時間の上限ではない。
文面では「真値」「最大経路の上限」という語を使っていない。

CLI 予約式の `2*sweep_reps*120` (720 秒) は certify では走らない**予約定数**である。
`orchestrator/calibrator/sweep.py` は `certify=True` で scale 測定の前に return する。
段 3 luna が指摘し、段 6 r2 が現物で検証した。

## 打ち切りと成果物 — 親の主張が反証された

親は段 1 で「窓不足は `timeout --signal=TERM` の rc≠0 → attempt 失敗 (fail-closed) なので
誤認定は生じない」と書いた。**これは成立しない。**

`orchestrator/calibrator/cli.py` の順序は次のとおり。

1. 計測・事後観測・品質判定の後に `status="accepted"` を決める。
2. `attempts/<id>/candidate.json` を書く。
3. 材料レポートへ `quality: accepted` を書く。
4. `registered/calibration-<digest>.json` を公開する。
5. 公開後の自己比較・rename・`publish.json` 書き込みを行い、最後に正常終了する。

**4 と 5 の間で TERM を受ければ、`accepted` な公開物が残ったまま wrapper は非ゼロ終了しうる。**
wrapper の失敗記録も終了時の清掃も公開物を撤去しない。下流の
`calibration_verify.py` と `collect_receipt.py` は wrapper の終了コードを必須にしていない。

**限定 (段 3 sol / luna が独立に一致):** 計測完了前に打ち切られた実行が、部分標本から
新たに `accepted` を組み立てる経路は無い。`accepted` 判定は計測終了後である。
certify は `require_all_reps=True` と `require_complete_metrics=True` を渡し、
runner の fatal は CLI の拒否へ伝播する。
したがって残るのは、**中身の妥当な較正が失敗記録の job から公開されうる**という帳簿上のずれである。

これは既存の限界であり本変更が作ったものではない。ユーザー scope
(「仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」) に従い関門は足さず、
文面の包括保証を撤回して新規項として起票した。

## 採らなかった 2 案 (どちらも親の provisional 裁定)

### 要求枠を 7200 → 10800 へ上げる

D1936 の該当項が指示していた形。**採らない。**

- 3250 は各 command の**打ち切りスイッチ**の上限和であって所要ではない。2026-09-11 の
  2 job (991694 / 991727) の実測では、job 開始 → static probe が 6 秒、static → pre attestation が
  33 / 29 秒。計測前の実所要は **35〜39 秒**で、上限和の 1.2% である。実績 186 秒で終わる job のために
  共有クラスタへ 3 時間を要求するのは絶対規律 4 の「無造作に大きくしない」に当たる。
- 旧窓で打ち切られていた実行が新窓で完走して受理されるので、**受理集合が広がる**。
- 後続の D1971 が増枠を既定解から外している。恒久禁止と読む必要はないが、積極的に認める根拠にもならない。

**この実測を「だから 7200 で足りる」という保証の根拠には使っていない。** 意図は
「だから枠を増やす必要はない」であって「だから最大経路も収まる」ではない。

### `required_s` を配分 5590 へ再定義する

**採らない。受理集合を狭めるため。**

`reservation_budget()` は点数 `p` に対し `3190 + 360p` を返す。受理条件は
`budget.required_s + reserve_s ≤ walltime.required_s`。

| 呼び出し | p | 必要値 | 現行 6610 | 案 5590 |
|---|---:|---:|---|---|
| 既定 (100 万 → 1600 万) | 5 | 5590 | 通る | 通る (等号) |
| 開始 50 万 / 上限 1600 万 | 6 | 5950 | 通る | **拒否** |
| p=7 | 7 | 6310 | 通る | **拒否** |

段 3 luna が指摘し、親が独立に検算して一致を確認した。
公式 wrapper は既定値しか渡さないが、CLI 直接呼び出しでは点数が可変である。

D1986 の項 3 / 9 / 10 は「閉じるのに新しい関門が要るなら閉じず、保証の限界を文面へ出す」という
形の前例だが、各項の対象は別タスクであり、前文は「各実装は名指しの変更に限定」と定める。
`required_s` の意味を変える授権にはならない (段 3 sol)。

### 依存物のコピー・build の並行化

D1971 で 1 対比較の実測により効果を帰属できず全撤回済み。再提案していない。

## pin 閉包

| 対象 | 結果 |
|---|---|
| `tools/pegasus/policies/calibration_v1.json` の bytes を sha256 で pin する test | **無し**。byte pin は `transport_v1.json` だけで、calibration は registry の path 一覧に載るのみ |
| `output/env/pegasus/calibration/attempts/**` を現行式で再計算する consumer | **0 件**。JSON 59 件を実読、`walltime.formula` を持つ 6 件はすべて旧式・`required_s=6610`・要求 7200 |
| `orchestrator/tests/conftest.py` の `requested_s = 7200` | 合成 fixture。policy を読まない。certify policy の consumer ではない |
| `orchestrator/tests/test_backoff_requested_us.py` の `WALLTIME_SECONDS=7200` | 別 job の凍結成果物に対する pin。本件と無関係 |
| `test_pegasus_policy_registry.py` の当該定数 | key の存在検査ではなく**移設済み key 名の集合定義**。値の pin ではない (段 3 luna が親の説明を訂正) |

## 不変であることの実測 (段 6 r1)

変更前 HEAD とのバイト比較で、差分は 3 箇所だけ — script の冒頭コメント、formula 文字列、
test の逐語 pin。ほかに空白・改行・encoding の変更は無い。

| 不変対象 | 実測 |
|---|---|
| `frozen_required_s` | 代入式がバイト一致。reserve 600 を代入して 6610 |
| PBS directive | `#PBS -l elapstim_req=02:00:00` のまま |
| 両 policy | file 全体が HEAD とバイト一致 |
| `timeout` | 19 記述箇所すべて不変 |
| 標本数・cooldown | 不変 |
| `orchestrator/calibrator/cli.py` | 51035 bytes 全体一致 |
| 過去 receipt | HEAD 管理下の 335 file すべて Git blob とバイト一致 |
| `finalize_reserve\((\d+)\)` | 2 件、集合 `{600}`。600 以外は 0 件 |

## 変異 (B-057)

本 wave の production 変更は receipt へ凍結される**記述文字列**だけであり、
どの attempt が受理されるかを 1 mm も動かさない。`DW-M08` に従い、
以下はすべて **diagnostic sensitivity pin** として記録する。
**kill の数には数えない。「変異 kill を実証した」とは報告しない。**

- 対象 HEAD `f5ba283784f99364c0a5e2eab09e03c5fa713c1f`、
  spec sha256 `0aea2ad2535ddcea3d000d76ef832cce00e5c8baeca46dccdf14c45fa750c87e`。
- runner は `python3 tools/run_tests.py --force-dispatch` に焦点 5 file
  (`test_pegasus_tools.py` / `test_pegasus_calibration_workload.py` /
  `test_official_perf_closure.py` / `test_ccbench_spawn_sites.py` /
  `test_pegasus_policy_registry.py`) と `-rf`。`--runner-mode dispatch`・`--detached`。
- **2 pass で行った。** 期待 node が段 4 時点で確定していなかったため `DW-M07` に従い、
  全件 SURVIVED 期待の probe で観測 node を集め、その完全集合を KILLED 期待で本登録した。
  probe の観測と本走の観測は 4 件とも一致した。

| ID | 変異 | 観測 node | 本走 |
|---|---|---|---|
| M1 | `frozen_required_s` の代入式の `1080` → `1081` | `test_pegasus_tools.py::test_certify_uses_frozen_cli_names_and_reservation_exports` | KILLED |
| M2 | formula の「8840 は上限ではない」を「8840 は保証された上限である」へ反転 | 同上 | KILLED |
| M3 | 冒頭 comment の `finalize_reserve(600)` → `(599)` | `test_pegasus_tools.py::test_pbs_directives_match_shared_and_calibration_policies` | KILLED |
| M4 | formula の合計 `=6610` → `=6611` | `test_certify_uses_frozen_cli_names_and_reservation_exports` | KILLED |

baseline PASSED。KILLED 4 / SURVIVED 0 / MISMATCH 0 / TIMEOUT 0 / matching 4、harness rc=0。
**4 件とも観測 node は 1 件だけ**で、同じ入力を拒否する層が前後にも内側にも無い
(`DW-M01` の単一理由性)。

## 新旧両走 — 新しい文面だけが守られる範囲 (`DW-M08`)

変更前 HEAD (`main` 側 `tools/pegasus/certify_calibration.sh`) に対し、各変異の対象文が
存在するかを実測した。

| 変異の対象文 | 変更前 HEAD での出現回数 |
|---|---:|
| M2 (`8840 itself is not an upper bound`) | **0** |
| M3 (`# + reservation_allocation(1080) + finalize_reserve(600) = 6610。`) | **0** |
| M4 (`reservation_allocation(1080)+finalize_reserve(600)=6610`) | **0** |
| M1 (`frozen_required_s = 10 + 1200 + ... + 1080 + int(reserve_s)`) | 1 |
| 旧 formula の偽内訳 (`build_cap(CCBench=900+gflags=60+glog=120)(1080)`) | 1 |

**M2 / M3 / M4 は変更前 HEAD に対しては適用すらできない。** 対象の文が存在しないからである。
旧 pin はこれらを守りようがなかった — 守るべき文が無かった。
M1 の対象文だけは旧版にも在り、旧 pin (`"5 * 3 * 120 + 10 * 120 + 2 * 3 * 120 + 1080"` の
部分文字列検査) でも検出できた。これが「新しい文面だけが守る範囲」の実測である。

段 6 r1 は、旧 pin が守っていた数式断片が新しい代入式 pin に含まれ、旧 build 項に対応する
新しい配分項は formula 全体 pin が守ることを、新旧 source をメモリ上で変異させて確認した。
**今回の置換によって検出できなくなった誤変更は確認されていない。**

## 一次資料

- 段 2 plan / 段 3 sol・luna / 段 5 author / 段 6 r1・r2 の逐語は `verbatim/`。
- 変異 spec と台帳は `mutation/`。
- 親の段 1 brief・実アンカー表・段 4 裁定は `verbatim/parent/`。
