# 段 4 裁定 — [T-809] 8c trial の workload 単位 fan-out

親が各所見を real / refuted、採用 / 不採用、scope 内 / 外に裁定する。
**本 wave は実装差分 0 byte なので、採用した所見はすべて「裁定パッケージ」または
「事実表の訂正」として閉じる。**

## 1. 親自身の誤りとして採用したもの (事実表を訂正済み)

| # | 所見 | 判定 | 親の裏取り |
|---|---|---|---|
| E1 | probe 903110 の node は `bnode033` でなく **`bnode019`** | real | `probe/job-0-903110.nqsv/env.txt` を直接確認。903102 が bnode033 |
| E2 | 「部分成功 = fail-stop」は広すぎ。`role-invalid` は次 workload へ進む | real | `:1727-1733` の break は generation loop、`:1459` で cell append 後に継続 |
| E3 | build cache の claim 衝突は process を落とさない | real | `BuildCacheError(RuntimeError)` (`buildcache.py:54`) を `pipeline.py:798` が捕捉 |
| E4 | **標準 CLI では claim 衝突自体が起きない** | real | cache identity ⊃ `admission` ⊃ `SourceEvidence.as_receipt()` ⊃ `source_root` (`build_admission.py:108-114`, `source_digest.py:149-160`, `:851`)。build 経路の `sub` は process ごとに一意な使い捨て worktree (`:2327`, `patchharness.py:288-306`, `p3_s4_loop_trigger_gating.py:599`) |
| E5 | campaign identity に execution contract は入らない | real | `ident.py:151-178` / `model.py:66-84`。preimage は spec_content + commit + search_tag + search_config + trial |
| E6 | 「workload 間に依存なし」は合成入力についてのみ | real | provider の session 相異検査・共有 wall・fatal break は跨ぐ |
| E7 | 中断証拠は journal のみではない (registered は lifecycle indeterminate) | real | `:1910-1934`, `trial_registry.py:1640-1665` |

**E4 は本 wave で最も重要な訂正である。** 親は「build cache が fan-out の最大の障害」と書いたが、
標準経路では衝突しない。**本当の代償は run 内 cache 再利用の喪失**であり、
これは禁止理由ではなくコストである。

## 2. real として採用し、裁定パッケージへ載せるもの

| # | 所見 (出所) | 判定 | 扱い |
|---|---|---|---|
| R1 | N leaf 化は「投入時刻だけ」の変更ではない。group 単位の start-once / terminal / 期待集合 / 共通 snapshot が存在しない (A1, B2, B5) | real | **採用。** 「N 回起動 = 旧 multi-workload trial と同値な 1 成果物」と呼ばない、を裁定文へ |
| R2 | `CrossRoleSessionTracker` の検出範囲が縮み、report 間の valid `child_id` 相異では旧検出力を再現できない (A2) | real | **採用。** invalid attempt の session id は valid provenance に現れない (`:961-985`、`autonomous_trial_completeness.py` の role-event shape) |
| R3 | wall 予算を N 本へ複製すると総枠が N 倍になり、「1 allocation で完遂」設計と一致しない (B3) | real | **採用。** 共有 deadline は既存 CLI に無い |
| R4 | 同一ノードで build+bench を fan-out すると計測が汚れる。`bench_lock` は bench だけ、`competing_bench_pids` は compiler を見ず、`settle()` は timeout で `settled=false` を返すだけ (A4, P2) | real | **採用 (P2 維持)** |
| R5 | P3「8c 全体で cross-node fan-out 禁止」は過剰。no-build wiring pilot は性能値を job 間比較しない (A5, B6) | real | **採用 (P3 は分岐へ書き換え)** |
| R6 | 正式 6 trial を一 arm 一 node に置くと処置と node が完全交絡する。現 manifest に node 因子は無い (A5) | real | **採用。** RP-3 として裁定へ |
| R7 | 新 exact-six manifest は formal retry の自動許可ではない (A6) | real | **採用。** 8b の「crash 後の再走なし」を迂回しない |
| R8 | 既定 run root は repo 内 (`output/exploration/autonomous-trials/<trial-id>`) なので、外部 output root の指定が fan-out 運用の条件になる (B7) | real | **採用。** 親も probe で実際に踏んだ (`IZANAGI_EXPLORATION_OUTPUT_ROOT` が git 配下を拒否) |
| R9 | 択に「fan-out しないで律速を解く」軸が無い。worst-case envelope の 77% は role timeout (B12) | real | **採用。** RP-1 に選択肢 (e) として追加 |
| R10 | 1.69× を本番利得として使えない (A8, B10) | real | **採用。** 事実表と裁定文に限定を明記済み |
| R11 | 「実装しなければ成果物不変」は条件付き。実際に N 回起動すれば探索 report の形は変わる (B11) | real | **採用。** 「コード差分ゼロ」と「fan-out 運用をしない」を分けて書く |

## 3. real だが本 wave の scope 外 — 別項として返すもの

| # | 所見 | 扱い |
|---|---|---|
| S1 | 既存 exact-six acceptance は Layer-3 chain を必須経路で呼ばず、宣言 arm が実際に走った arm であることも認証しない (A3)。`trial_registry.py` は `assert_autonomous_trial_completeness` しか import せず、証拠契約 (`s8c_preregistration_evidence_contract.v1.json`) は acceptance 自身からの Layer-3 呼び出しを要求している | **fan-out とは独立の既存 gap。** 新規タスク候補として裁定パッケージに載せる。本 wave では実装しない |
| S2 | acceptance は 6 report 間で `measurement_head` の一致を検査しない (B5) | 同上。S1 と同じ項へ束ねる |
| S3 | 8c trial を走らせる job の運用事実 2 件 (PBS_JOBID のコロン / exploration root の git 祖先拒否) | runbook への追記候補。段 8 の自己改善 routing で扱う |

## 4. refuted

| # | 所見 | 理由 |
|---|---|---|
| F1 | 「別 workload が同じ genome を合成すると cache claim が衝突し、後着が hard error で落ちて手動回収が要る」(親の初稿 C-2、s2-plan `:31`、A4 の一部) | **refuted。** E4 のとおり標準経路では digest が process ごとに異なる。衝突は `ccbench_dir` を共有した場合にのみ起き、そのときも当該 variant の abort へ隔離される |
| F2 | P3「8c は workload 間比較そのものだから cross-node fan-out を現行 protocol で許さない」(親 brief) | **refuted (過剰)。** 現 A/B/C は `scientific_claim=false` の配線 pilot で job 間の性能比較をしない。worklog 418 で撤回した「未測定量を根拠に広く禁止する」の再発である |

## 5. 変異事前登録 (DW-M01)

**免除。** 実装差分ゼロの「実装しない」裁定であり、`DW-S04` の免除条件に該当する。
受入は免除されないので、docs 変更に対する検査 (`check_docs.py` と関連テスト) は段 7 で実走する。

## 6. 段の遷移

`4 → 7 → 8 → 9`。実装面が無いため段 5 / 6 は行わない。
