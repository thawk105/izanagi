# [T-471] `_restore_targets` 所要時間の実測 — 事前登録 (実測前に凍結、2026-08-05)

- `authority: none`
- `default_effect: no-state-change`
- 本文書は計測 job を投入する**前**に凍結する。実測後に定義・語彙・arm・代入規則・判定を変更しない。
  変更が必要になったら erratum を別ファイルで追記し、初回の値と結論を消さない
  ([T-399] `verdict-preregistration.md` と同型)。

## 0. 本 wave が測るもの・測らないもの (最重要)

**測るもの:** `tools/mutation_harness.py` の `_restore_targets(repo, originals)` 1 回の
呼出しに要する wall-clock 時間の**観測分布**。以下これを `R_restore_observed` と呼ぶ。

**測らないもの:** その**上限**。非定常な Lustre の wall-clock に対し、有限標本の最大値は上限では
ない。したがって本 wave は [T-399] `verdict-preregistration.md` の凍結記号
`R_restore_bound` (= 上限) を**確定しない**。`R_restore_bound` は `null` のままとする。

この 2 つを別名にするのは同名識別子の二義化を禁じる規律 (D75) に従うためである。
`R_restore_observed` を `R_restore_bound` として台帳・下流へ渡してはならない。

## 1. 計測区間の定義 (凍結)

区間は `_restore_targets` の呼出し直前から復帰直後まで。含むもの:
`_defer_cleanup_signals` の mask/handler 操作、全 target の `write_text`、`_purge_pycache`、
`_verify_originals`。

含まないもの: 変異の適用、pytest の実行、`_stop_process` の待ち、復元直後の `_assert_head`
(git subprocess)、ledger 書き出し、scratch の構築・検査・hash・JSON 出力。

計測は `time.perf_counter_ns()` を用い、`time.get_clock_info("perf_counter")` を証拠に残す。

## 2. 測る case の凍結 (literal、driver に探索させない)

commit `24f3f12df1ab3ee4dd6cddea768fdf745228b253` (実測直前に local main を取り込んだ tip) 時点で、
`output/` 配下の `schema == "izanagi-dev-wave-mutation-spec/v1"` を持つ JSON は **46 本**である
(取り込み前の `f009da34` 時点では 43 本。増えた 3 本を含めても下表の最大 case は変わらない)
(basename ではなく schema 一致で走査した。`.../driver/spec.json` や
`2026-08-04_t325-trial-registry-mutation-spec.json` のように `mutation-spec*` に
一致しない名前も含む)。その全 mutation を走査した結果、次の 2 件が各次元の最大である。

| case | 出所 spec | mutation ID | n | target (HEAD blob) | B_original |
|---|---|---|---|---|---|
| `C2` | `output/insights/2026-08-04_t244-p5-injection-gate/mutation-spec-v2.json` | `MX4-MX6-both-layers` | 2 | `orchestrator/campaign/autonomous_trial_completeness.py` (`ce7c9ef0`), `orchestrator/campaign/claude_projected_provider.py` (`deb2aaae`) | 69,659 |
| `C1` | `output/insights/2026-08-04_t399-t400-signal-mitigation/mutation-spec.json` | `G1` | 1 | `output/insights/2026-08-03_t361-t362-cluster-probes/driver/run_probes.py` (`9ca9da28`) | 240,600 |

**driver はこの 2 case を定数として持ち、spec を走査・順位付けしてはならない。**
実行前に各 target の実体と `HEAD:<path>` の blob が一致することを検査し、
一致しなければ attempt を `valid=false` とする。計測に使う harness 自身
(`tools/mutation_harness.py`) も同じく HEAD blob との一致を実行前に検査し、
通常 file (非 symlink) であることを確認してから source を load する。

## 3. arm (凍結、5 本 × 各 100 trial)

| arm | case | n | P | E_by_parent | cache 温度 | 意図 |
|---|---|---|---|---|---|---|
| `A-e0` | C2 | 2 | 1 | [0] | — | `__pycache__` 不在 (login 直下実行の正常路) |
| `A-e143-fresh` | C2 | 2 | 1 | [143] | trial 直前に作成 | dispatch 経路の主ケース (§4 参照) |
| `A-e143-aged` | C2 | 2 | 1 | [143] | attempt 冒頭に作成 | cache 冷却の影響 |
| `A-b240-n1` | C1 | 1 | 1 | [143] | trial 直前に作成 | bytes 次元の実 case 最大 |
| `A-p2-synth` | C2 の bytes を 2 親へ配置 | 2 | 2 | [143, 97] | trial 直前に作成 | 将来の異親 2 target (**合成 profile**) |

- `B_mutated` は当該 mutation の注入後の状態を再現する。
- arm 順は交互化する (同一 arm を連続させない)。
- 各 trial は fresh な scratch tree に作り直す。前 trial の復元済み tree を再利用しない。
- **`A-p2-synth` は実在する変異ではない合成 profile である。** 証拠にそう明記する。
- **単調性は主張しない。** 「この profile 以下のすべての構成に有効」とは言わず、
  妥当性は測った 5 arm に限定する。

### 3.1 観測者効果の遮断 (凍結)

- **計測直前に `__pycache__` を列挙してはならない。** entry 数は作成時に確定して記録する。
  列挙は dentry cache を暖め、`A-e143-aged` の冷却比較を壊す。
- `lfs getstripe` と directory 列挙は計測対象 tree に対して行わない。arm ごとに同型の
  **別 replica tree** を 1 つ作ってそこで採る。
- 公表対象の 100 trial はすべて同一の事前 access 列を持たなければならない
  (最初の trial だけ余分な access がある状態を許さない)。

### 3.2 driver の altitude (凍結)

driver は使い捨てであり、**300 行を超えてはならない** (テストで検査する)。
case 探索器・順位付け・汎用 CLI を持たない。この上限は「盛らない」(絶対規律 5) の
機械的な担保であり、複雑さが検出穴を生むことへの対策である。

## 4. arm の根拠 (実測済みの事実)

- 1 変異が触る distinct file 数の最大は **2** (commit `24f3f12` 時点で checkout 内の
  mutation spec JSON 46 本を schema 一致で全走査した結果)。`_restore_targets` の production 呼出し元は
  `_apply_mutation` の `finally` だけで、渡るのは当該変異の `touched` に限られる
  (mutation_harness.py:1330-1332, :1266-1275)。signal / resume / baseline が全 target へ
  拡大する経路はない。ただし spec parser は replacement 個数に上限を持たないため
  (:276-307)、`n=2` は**現行 inventory 条件付き**であってコード一般の上限ではない。
- `E` の値: 2026-08-05 に main checkout `/work/1/SFC/tanab/izanagi` で観測した
  `orchestrator/tests/__pycache__` = 143 entries / 7,352,533 bytes、
  `orchestrator/campaign/__pycache__` = 97 entries / 2,236 KB。
  **本 wave の worktree では両 directory は不在**であり、上の値は main checkout の観測である。
- **`runner_mode=dispatch` では `__pycache__` が書かれる。** `_run_tests` が設定する
  `PYTHONDONTWRITEBYTECODE=1` (:1130) は login 上の直下の子にしか効かない。計算ノードへ転送される
  env は `dispatch_compute.TASKS["tests"].env_allowlist` の 4 key
  (`PYTEST_ADDOPTS`, `IZANAGI_TEST_NPROC`, `IZANAGI_TEST_TRIGGER`,
  `IZANAGI_TEST_ALLOW_UNSTAGED_DELETIONS`) だけであり (dispatch_compute.py:56-66, :1336-1339)、
  計算ノード側は `child_env = os.environ.copy()` + allowlist で `-B` も付けずに pytest を起動する
  (:580-592)。したがって [T-360] が対象とする実運用経路では `E > 0` が主ケースである。

## 5. 代入規則 (凍結)

- 全 trial の生値を残す。分布や max へ縮約した値だけを保存しない。
- **fail-closed**: 1 件でも例外・事前事後検査失敗・trial 欠落・sequence 欠落があれば
  attempt 全体を `valid=false` とし、部分 max を昇格しない。失敗 trial も
  「その時点までの実所要時間」と例外型を記録する (捨てると上限が楽観側へ動く)。
- **必須の環境タグ (§6) が 1 つでも取得できなければ `valid=false`。**
  `lfs getstripe` の失敗を `available=false` と記録するだけで先へ進んではならない。
- 有効な attempt について arm ごとに min / max / mean と nearest-rank の p50 / p90 / p99 を出す。
  `R_restore_observed_max` = 当該 arm の実測 max。
- **`certified` という語を使わない。**
- **計測 evidence に `planning_allowance` を出力してはならない。** これは撤回した margin 規約
  (段 4 の P4) の別名復活にあたる。参考値は warn margin 設計メモの中でだけ、
  「設計候補であって上限ではない」と併記して算出する。

## 6. 環境タグ (凍結、全部そろわなければ値を採用しない)

hostname / `PBS_JOBID` / filesystem type / mount source / kernel / python version / repo commit /
`time.get_clock_info("perf_counter")` / 開始・終了 UTC / arm profile / spec manifest
(exact path + sha256) / 実 target と scratch の `lfs getstripe` / 親 directory entry 数。

## 7. [T-399] 凍結式への当てはめ (凍結)

[T-399] `verdict-preregistration.md` の十分性判定式は
`G_usable_lower ≥ 5 s + 5 s + R_restore_bound` であり、同文書の代入規則により
T-399 authoritative attempt の左辺は `cleanup_elapsed = 5.013 s` に固定される。

本 wave は次の 2 つを**分けて**記録し、混同しない。

1. **凍結分岐による machine verdict**: 本 wave は `R_restore_bound` を確定しない (§0) ため
   `R_restore_bound = null`。凍結文の分岐どおり **十分性 = `UNKNOWN`**。
2. **R 非依存の算術事実**: `R ≥ 0` である以上 `5.013 ≥ 10 + R` は **R の値によらず偽**。
   すなわち T-399 の attempt は、R をどれだけ精密に測っても十分性を certify しない。

**どちらの読みでも運用結論は同一である** — 「T-399 の attempt では [T-360] 条件 3 の十分性を
certify できない」。これは「実 grace が物理的に不足した」ことの証明ではない (左辺は
「実際に使えた時間の下限」であり、この不等式は片側の certify 器である)。

**本 wave は [T-360] 条件 3 を閉じない。** 変異本走を計算ノードへ束ねる安全根拠は成立しない。

## 8. 適用条件と fault model (凍結)

- 適用条件: 復元中に追加の SIGINT / SIGTERM が到着しないこと。到着経路の所要時間は測らない。
- fault model: `_restore_targets` は `write_text` 後に同一 node から `read_text` するだけで、
  file の fsync も親 directory の fsync も行わない (mutation_harness.py:767-788)。
  したがって本 wave の値が支えるのは
  **「live node・Lustre client 生存・`_restore_targets` return 後に process だけが kill される」**
  という限定された契約までである。書込み途中の SIGKILL、node 障害、power loss、
  Lustre client 障害に対する durability は本 wave の値では支えられない。
  これは R の秒数の問題ではなく復元定義の問題である。

## 9. 本 wave が測っても閉じないもの (凍結、先に書く)

- `H_stop_overrun`: `_stop_process` の `wait(timeout=5)` × 2 の期限超過分。10 s は timeout 引数の
  和であって関数の wall-clock 上限ではない (:1098-1113)。
- `H_head`: 復元直後の `_assert_head` (:1332)。`_repo_head` 経由の git subprocess (:605-608)。
- `H_exit`: handler 復旧、例外 unwind、lock close、stderr write (:2084-2101)。
- `D_delivery`: PBS warn signal の要求時刻から Python parent 受信までの遅延。未計測。

これらはいずれも `5 s + 5 s + R` に**含まれていない**。合成量を書くときは
`C_repo_known_safe = H_stop_actual + R + H_head` のように**別名**を用い、
`R_restore_bound` の名前で cleanup 全体を指さない。
