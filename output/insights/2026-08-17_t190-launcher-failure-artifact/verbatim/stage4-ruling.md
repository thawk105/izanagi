# 段 4 裁定 — [T-190] launcher 失敗 artifact 保存による原因分離

- 日時: 2026-08-17 01:40 JST
- 入力: `brief.md`、`stage2-plan.md` (411 行)、`stage3-lensA.md` (11 所見)、`stage3-lensB.md` (16 所見)
- 段 3 は 27 所見。**real 25 / refuted 2** (親 brief の誤り 1 件を含む。うち 1 件は親が実測で refute)。

---

## 0. 親 brief の訂正 (両レンズが独立に指摘 = DW-G03 の独立 2 例)

**訂正 1 (レンズ A 所見 8 / レンズ B 所見 6、real):**
brief §4 は「診断に出るのは `limits`/`actuals` の 2 dict だけで `attempts[]` 個別は出ない」と書いたが**誤り**。
親が実測で確認した (`orchestrator/tests/test_codex_worker_launch.py:296-330`): 既存の
`_receipt_diagnostic` は既に `outcome` / `stop_reason` / `launcher_rc` と、attempt ごとの
`accepted` / `limit_trigger` / `evidence_status` / `metering_status` / `codex_exit_code` /
`validator_rc` / `process_group_residual` / `termination_verified` / `wall_clock_s` /
`failed_predicates` / stdout・stderr 抜粋を印字している。

**正しい純増の基線はこうである。**

| | 状態 |
|---|---|
| 既に 16 KiB 診断へ出ている | `outcome`、`stop_reason`、attempt 個別値、stream 抜粋 (いずれも bounded・21 件同時なら大幅に切詰) |
| **本 wave の純増** | ① `evidence_forced_stop` ② `residual=None` の 4 出所 ③ phase 別時刻 ④ latch の全成立集合 ⑤ **終了主体と送信 signal** (下記採用) ⑥ artifact の **full bytes の耐久保存** |

**訂正 2 (レンズ B 所見 10、real、親の先の実測を撤回):**
親は段 0 で「env は計算ノードへ届く」と記録したが**誤り**。`_dispatch_environment()`
(`tools/run_tests.py:930`) は dispatch 呼出しまでの話で、その先の
`tools/pegasus/dispatch_compute.py:60-72` が `tests` task の `env_allowlist` を
閉じた 6 変数の frozenset に濾す。`IZANAGI_LAUNCHER_FAILURE_ARTIFACT_ROOT` は届かない。

**訂正 3 (レンズ B 所見 13、real):** F285 §2.1 は failure 側 21 件だけの分布であり、
green 側の余裕は未測定 (同 package §5 が自認)。「常時縁に張り付いている」は
**整合する仮説**であって実証ではない。台帳へはそう書く。

**refuted 1 (レンズ B 所見 12):** 「受入は 32 worker で 48 ではない」は**誤り**。
`_NPROC_CAP=32` は `site_policy.default_test_jobs(site, cap=...)` へ渡る cap だが、
同関数 (`orchestrator/campaign/site_policy.py:122-127`) は
`is_pegasus_compute(site)` なら **cap を無視して affinity 全数を返す**。
計算ノードでは 48 worker が現行でも正しい。レンズ B は `_default_nproc` で読みを止めた。

**refuted 2 (レンズ A 所見 8 前半):** brief に書いた grep の逐語 (`"A|B|C"` に `-E` 無し) は
確かに brief 本文の誤記だが、**親が実際に実行したのは `\|` (BRE 選択) を使った版**であり、
検索自体は成立していた。結論 (退避機構は不在) は変わらない。brief 本文の逐語だけ訂正する。

---

## 1. (P1)(P2)(P3) の確定

- **(P1) = プラン v1 の案を採用。** receipt schema (`_ATTEMPT_FIELDS` / `_RECEIPT_FIELDS_V*`) と
  `accepted` 式と truth table は不変。診断は独立 sidecar
  `<artifact_dir>/launcher-diagnostics.<pid>.<uuid4hex>.json` へ出す。
- **(P2) = プラン v1 の反対案を採用し、さらに親が縮める。**
  退避は環境変数 opt-in にせず**常時**とする (設定漏れが恒真化するため)。
  **ただし環境変数による root 上書きは本 wave から落とす** (訂正 2 のとおり計算ノードへ届かず、
  黙って効かない knob は恒真面を増やすだけ)。既定 root 固定とする。
- **(P3) = 親 provisional を採用。** `limit_trigger` の値・優先順位・受理経路は不変。
  全成立集合は sidecar にだけ出し、`control_limit_trigger` と `conditions_met` で名前を分ける。

---

## 2. 所見の裁定

### 採用 (must-fix・scope 内)

| # | 所見 | 裁定 | DW-G05 成果物影響 |
|---|---|---|---|
| A1 | hook が死んでも新設テストが緑 | **採用。** 子 pytest を起動して未処理 mismatch を実発火させ、外側から bundle 生成を確認する live wiring test を必須にする。`tryfirst` 属性も固定する | 入れないと退避層が丸ごと死んだまま「観測可能にした」と台帳へ書くことになる |
| A3 | 専用例外を経由しない rc 判定が残る (`test:1917`, `:2333`) | **採用。発火条件を広げる** — 専用例外に限らず、**当該 test module の未処理 call-phase 失敗すべて**で退避する。緑走では 0 件なので容量増はない | 入れないと F57 の一部の落ち方 (生 assert / 生 TimeoutExpired) で artifact が残らない |
| A4 | TimeoutExpired 時は生存中の source をコピーし一点整合しない | **採用 (縮小形)。** launcher の kill/drain は行わない (harness の挙動変更になる)。代わり に metadata へ `source_live=true` / `snapshot_consistency="incomplete"` を必ず記録する | 入れないと不整合 bundle を完全 snapshot と誤読して誤った原因へ帰属する |
| A5 | 計装が late wall gate より前に実時間を消費する | **採用 (不変条件の言い換え + 実装規律)。** 不変条件 1 は「値と述語の不変」であって「実時間上の受理集合不変」は**保証しない**と brief を訂正する。実装は (a) 監視中は既存 `now_ns` の再利用と in-memory 更新だけ、(b) sidecar の write は receipt 公開と全 late gate の後、(c) **fsync しない** (診断であり耐久性が要件ではない。共有 FS の stall を外側 10 秒 timeout へ持ち込まない) | 入れないと計装自身が F57 を悪化させ、観測したい現象を計装が作る |
| A6 | receipt SHA-256 は同一 run の証明にならない | **採用。** 自分が receipt を公開できた run だけ `status:"sealed"`、敗者は `status:"foreign"` とする | 入れないと別 run の receipt と診断を組み合わせて誤帰属する |
| A7+B9 | 退避 root の source 内包・コピー量無制限・原 failure の上書き | **採用。** (a) resolve 後に destination が source の祖先/子孫なら拒否、(b) file 数・総 bytes の上限と省略理由を manifest へ、(c) **コピー例外は必ず捕捉して原 failure を上書きしない**、(d) 完了時に `.complete` marker | 入れないと退避が元の失敗を internal error へ変え、受入全走を丸ごと失う |
| A9 | sidecar テストが positive-only | **採用。** 負例を必須にする — 正常 run で `evidence_forced_stop=False`、閾値未満で `conditions_met` 空、exact-limit 境界、判定 site ごとに異なる値 | 入れないと誤診断 (全 run を強制停止と記録する等) が生き残り、次の再発で誤った原因へ導く |
| A10 | residual reason が normal reap 経路しか検証されない。既存 monkeypatch consumer (`test:2692`) が改名一覧から漏れ | **採用。** evidence forced stop → `_terminate` → sidecar までの統合テストを必須にする。既存 consumer も明示更新する | 入れないと F57 の実経路 (強制停止) で reason が消え、②が空振りする |
| B2 (部分) | `-9` は外部 SIGKILL と識別不能 | **採用 (最重要の追加)。** **launcher は自分が TERM/KILL を送ったかを知っている。** `termination_initiated_by_launcher` と送信 signal と送信時刻を sidecar へ記録する。これで「外部 OOM/scheduler の SIGKILL」と「launcher 自身の強制停止」が初めて分離できる | F285 が「原理的に事後判定できない」とした最大の曖昧さを、launcher が既に持っている情報だけで閉じる |
| B5 | malformed `/proc` stat が黙って無視され `residual=0` になる | **採用 (診断のみ)。** `proc_stat_malformed` を sidecar へ記録する。**count の意味は変えない** (変えると受理集合が動く) | 入れないと「残留ゼロ」と「観測できなかった」が区別できないまま `termination_verified=true` が保存される |
| B7 | preflight failure / launcher 外部 kill では sidecar が無い | **採用 (縮小形)。** sidecar を preflight 前へ移すことはしない。退避 metadata へ `diagnostics_present:false` と理由を記録する | 入れないと「sidecar が無い」を「計装が壊れた」と誤読する |
| B8+B15 | 退避後の receipt は絶対 path が古くなる | **採用。** receipt の exact bytes は不変のまま保存し、bundle 内に `path-map.json` (元 path → bundle 相対 path) を併置する | 入れないと保存はされるが機械的に読めず、1 時間以内の原因到達が保証できない |
| B11 | run 単位の索引が無く 21 leaf を辿れない | **採用 (縮小形)。** bundle 生成ごとに run 直下の `index.jsonl` へ 1 行 append (nodeid / worker / PBS jobid / bundle 相対 path / 時刻)。**reader CLI は作らない** | 入れないと 21 件が散らばり、受入結果から辿れない |
| A11 | 計装だけで T-190 を閉じてはならない | **採用。** 台帳の記録は「次回再発を観測可能にした」に限定する。**[T-190] と F57 は閉じない。** 実 bundle を得て原因を帰属するまで open に残す | 依頼文自身が「scope は原因分離まで」と書いており一致する |

### 不採用・scope 外 (実装せず裁定パッケージへ返す)

| # | 所見 | 理由 |
|---|---|---|
| A2 | setup phase / KeyboardInterrupt / xdist worker crash の salvage | worker crash の salvage は controller 側 hook (`pytest_testnodedown` / `pytest_handlecrashitem`) を要し、対象 file の外。**代わりに「対応範囲は未処理 call-phase 失敗に限る」と明記して記録する** (A11 と同じ誠実さの規律) |
| B1 | supervision 内の処理別時間・I/O・cgroup/PBS 情報 | phase 分解の更なる細分と外部資源の観測は別機構。本 wave の phase 境界 10 点で第 1 歩を取る |
| B3+B16 | `tools/dev_waves/worker.py` の termination helper 計装 | 所有ファイルの外。F285 C の完全な帰属には要るが、本 wave の scope 外 |
| B4 (残り) | 外部 kill / resource evidence (cgroup・PBS) | 同上。B2 の採用部分で「launcher 自身が送ったか」までは分離できる |
| B10 (残り) | dispatch env allowlist への root 変数追加 | `dispatch_compute.py` は sanctioned control plane (D251 が変更コストを明記)。本 wave は env 上書き自体を落とすことで回避する |
| B11 (残り) | archive の reader CLI・retention/GC | `index.jsonl` までで止める |
| B14 | env transport の変異 | B10 で env 上書きを落としたので対象が消滅 (moot) |

---

## 3. 不変条件 (確定版・段 5 へ渡す)

1. production の `--max-wall-clock-s` / `--evidence-grace-s` / `--termination-grace-s` /
   `--poll-interval-s` の**値も判定条件も**変えない。parser 既定 (`5` / `2`) を触らない。
2. `accepted` 式、`_LIMIT_REASONS`、`limit_trigger` の値・優先順位、`_writer_truth`、
   `_ATTEMPT_FIELDS`、`_RECEIPT_FIELDS_V*`、checker の rc を変えない。
3. test fixture の予算値 (wall=`3` / evidence=`1.0` / termination=`0.05` / poll=`0.01`) と
   harness 外側 timeout `10` を変えない。
4. 既存テストの期待値を反転・緩和・skip・削除しない。赤なら実装側が誤り。
5. 制御フローを変えない。break 位置、terminate/normal reap の選択順、receipt 公開順は不変。
   監視中は in-memory 観測のみ。sidecar I/O は receipt 公開と全 late gate の後、**fsync なし**。
6. **(新規・A5 由来)** 不変条件 1 は「値と述語の不変」を意味し、**実時間上の受理集合不変は
   保証しない**。実装は追加 clock 取得と dict/set 更新を最小にし、監視ループ内で
   ファイル I/O を一切増やさない。
7. `_group_member_count` の**数値の意味を変えない**。`end <= 0` / 短い fields / malformed を
   新たに `None` にしない。reason は診断側にだけ出す。

---

## 4. 変異事前登録 (DW-M01 / DW-M08)

テスト強化を含む wave なので、**新テストと変更前 HEAD 版の双方**へ走らせ、
新テストだけが検出する差分を示す (DW-M08)。

| ID | 変異 (production / harness を壊す) | 期待して落ちる node の性質 | 単一理由性 |
|---|---|---|---|
| M01 | `AttemptState.evidence_forced_stop` の既定を `True` にする | 正常 run の負例 (`evidence_forced_stop is False`) | 他層に同入力を拒む gate なし |
| M02 | `conditions_met` の計算を常に `list(_LIMIT_REASONS)` にする | 閾値未満で `conditions_met` が空である負例 | 同上 |
| M03 | 全 phase boundary を終了時に一括サンプルする | phase ごとに固有の duration を exact assert する node | 同上 |
| M04 | `_terminate` が `on_unknown` を `_wait_for_group_exit` へ渡さない | 強制停止経路の reason 伝播統合テスト | normal reap 経路は別 node |
| M05 | 退避 plugin の `tryfirst=True` を `trylast=True` にする | live wiring test (子 pytest で実発火) | 直接呼出しの単体 node は緑のままなので単一理由 |
| M06 | 退避のコピー呼出しを no-op にする | root 不在から始めて bundle 数と sentinel bytes を見る node | 同上 |
| M07 | leaf directory を固定名にして再利用する | 同一 nodeid で 2 回発火させる衝突回避 node | 同上 |
| M08 | receipt binding を常に `sealed` にする | receipt race の敗者側で `foreign` を要求する node | 同上 |
| M09 | `path-map.json` を書かない | bundle 内 path 解決 node | 同上 |
| M10 | コピー例外を捕捉せず伝播させる | 原 failure が保持されることを見る node | 同上 |
| M11 | `termination_initiated_by_launcher` を常に `False` にする | 強制停止時に `True` を要求する node | 同上 |
| M12 | `proc_stat_malformed` を記録しない | malformed stat の診断 node | count の意味は不変なので単一理由 |
| M13 | `index.jsonl` へ append しない | run 単位索引 node | 同上 |
| M14 | natural-exit 診断の `>` を `>=` にする | exact-limit 境界の負例 | receipt 側は不変なので sidecar node だけが落ちる |

**正例 (受理集合不変の対照、`category: positive`):**

| ID | 内容 | 期待 |
|---|---|---|
| P01 | sidecar writer を強制的に `OSError` にする | 正常 run の rc / `accepted` / receipt bytes が不変 (**落ちない**ことを確認する対照) |

---

## 5. 段 5 の分割

**単一単位とする。** 理由: 単位 A のテストと単位 B の退避 harness が同じ file
(`orchestrator/tests/test_codex_worker_launch.py`) に載るため所有を素集合にできない。
新規 test file へ分ければ素集合にできるが、file 集合を列挙するメタテスト
(`test_plain_runner_coverage.py`) への追随が第 3 の所有点を作り、かえって競合が増える。
`DW-S06-B` の「一枚岩なら理由 1 行を handoff へ残す」に従う。

実装子は `--max-model-calls` を上げる (既定 100 では報告ゼロで SIGTERM になる)。
