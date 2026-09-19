# 段 4 裁定 — plan v2 と変異事前登録 (2026-09-19)

出所: brief.md、plan-out.md、consult-a-out.md、consult-b-out.md。裁定 inbox (`/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/`) を再走査: 本 wave に触れる新裁定なし (最新は A-1 attempt-0002 認可、t2778 cleanup)。

## 所見の裁定

| # | 出所 | 所見 | 裁定 | 扱い |
|---|---|---|---|---|
| 1 | A-1, B-1 | (P1)「同一 build」を source 一致で充足と読むのは過大。configure argv は request ごとの絶対 path を含み完全一致しない。stock の `src_token` は文字列 `stock` で digest でない。binary は別 build | **real・採用** | 稿の定義を「同一候補・同一ソース条件 (genome・controlled define・toolchain・固定 configure 引数・patch 適用下の `source_bytes_sha256`) から workload ごとに別 build」に改める。比較単位は同じ arm の workload 間。binary digest は列挙し、同一 binary は主張しない。P1 を撤回・置換 |
| 2 | A-2 | 今回の adopted arm の `source_bytes_sha256` が T-1998 prereg の `678b7203…` と一致する保証は機構に無い | **real・採用** | 親の稿手順に、3 adopted arm の `source_bytes_sha256` (condition receipt / WAL `build_start`) と prereg §4.2 の全桁比較を入れる。不一致なら「fixed5 の設定を採用したが prereg の source digest との一致は未成立」と書く。新 gate は作らない |
| 3 | A-3 | A-6 の 73 分は nodes=1 の実測 (receipt の `-b 1`)。brief の「nodes=5 で 73 分」は誤り | **real・採用** | brief P4 を訂正: A-6 実測は nodes=1 で 4382 s。rr95/fixed5/nodes=5 の所要は未測定。nodes=5 の採用根拠は t2489 (rr5/rr50 で 4.17 倍短縮) と D2148 項 5 (A-2 の nodes=5 採用) |
| 4 | B-2 | (P5)(P7) 同一 attempt は arm 間隔が数分であることも同時期性も保証しない。performance 検査と bench が別々に lock を取り、他 request の処理が挟まる | **real・採用** | 稿は「同一 campaign 内に stock 対照を置く設計」と書き、各 arm の bench 時刻 (WAL `bench_done` の ts)・arm 間隔・3 workload 全体の測定期間を載せる。文字どおりの同時実行・node 同一性は主張しない。queue 分断後も機構上有効な attempt であることと同時期性の主張は分ける |
| 5 | B-3 | (P3) `effects` 欠損時の扱いが未固定 | **real・採用** | 結果を見る前に固定 (下記「判定規則 v2」)。既存出力の読み方であり新 gate ではない |
| 6 | B-4 | partial 時に「欠落明記で足りる」は成果物の約束と衝突 | **real・採用** | 1〜2 workload が落ちた場合、本 wave の予定成果は**未達**と明記し、手作業の表を collect 成果物として扱わない。再投入は下記「再投入の規則」に従う |
| 7 | B-5 | fp-* が `~/.izanagi/bench.lock` を使うという前提は現 checkout の経路から支持されない (floor_pair_driver は bench_lock を取らない) | **real・採用** | brief の当該前提を撤回。本 wave の 3 request 相互の直列化だけを前提に残す。fp-* の実経路は照合せず「未確認」に置く (所要見積りに使わない) |
| 8 | A-refuted | 3 workload 全件経路に緩めるべき固定 2-workload 境界は無い。partial 境界は不変。submitter は `S:273` と `S:365` の 2 箇所 (brief の :263 は誤り)。`-b 5` に追加変更不要。正しさ gate は同経路。A-6 先例の残り 3 file は無変更で可。A-2/A-6 の pin は現行 (`f8a77806…` / `682e0f4e…`、protocol `d99f08bc…` / `21427e71…`) | **refuted (plan 支持)** | plan v2 に採用 |
| 9 | B-refuted | 純増あり (D2044 項 3 が挙げた不足へ直接材料を足す)。P3 の直接比較はユーザー裁定に整合、√2 補正不要。P2 は「既存手順の別 study instance」の意味で支持 — protocol hash は新しくなる (preimage に study・workloads・cells を含む)、「同一 protocol hash」とは言わない。P6 の図の材料 = 表 + leaf で足りる | **refuted (brief 支持、語を訂正)** | P2 の説明を「新しい判定手順を設計しない、既存 protocol schema の別 study instance」に改める |
| 10 | plan | `M:5173` CLI help と `canonical_policy_path` docstring の「two」 | **採用 (文言のみ)** | author が「three」へ直す。受理条件は不変 |

裁定パッケージ候補: **なし** (両相談とも「なし」。「同一 build = 同一 binary bytes」「新 protocol 禁止 = 新 protocol_sha256 禁止」という厳密な語義をユーザーが要求する場合だけ再裁定。本 wave は上記 1・9 の読みで進め、稿にその読みを明記する)。

## 判定規則 v2 (結果を見る前に固定、稿にこのまま写す)

1. `median_w,arm` = 機構が受理した各 arm の 5 標本の `statistics.median` (certification.json `cells[].performance.median_tps`)。個々の比の median ではない。
2. `effect_w` = 機構の `effects[w]` (= `median_w,adopted / median_w,stock − 1`、未丸め)。
3. `floor_w` = 床値 JSON `between_run.cv` の全桁 (rr5 `0.009536033056996148`、rr50 `0.00725042525457718`、rr95 `0.0022283754708938273`)。
4. `regression_w` ⇔ `effect_w < −floor_w` (strict)。`effect_w == −floor_w` は退行に含めない。表示の丸めは判定の後。
5. `effect_w` が無い workload (anomaly → reject、unstable、source unbound、標本不備) は「判定不能」とし理由を書く。anomaly による reject は別欄に保持する (規律 2)。
6. 「退行なし」は「優越」でも「差が無いことの証明」でもない。床は旧 stock の session-median の変動の下限であり、本 attempt の effect の標準誤差・有意水準ではない。
7. outer status (3 workload の論理積) と `a4_noise_floor_status` は機構の出力として写すだけで、稿の床値判定で書き換えない。

## 再投入の規則 (結果を見る前に固定)

- 3 request のいずれかが**基盤要因** (queue/walltime 超過、依存供給不在、node 割当失敗、scratch 不在、`source_identity` 以外の rc=2 前段) で落ちた場合: 同じ実装 commit・同じ policy で attempt id を変えて **1 回だけ**再投入する。
- **科学的要因** (anomaly、reject、unstable、source unbound) で落ちた・判定不能になった場合: 再投入しない。そのまま報告する。
- 再投入後も欠落するなら、本 wave の予定成果は未達と明記して止める。

## plan v2 (author の所有と変更面)

plan-out.md の「変更面」「新 policy 案」「tests」を採用し、次を加える。

- `S:273` と `S:365` の 2 箇所 (plan どおり)。
- `M:359` docstring と `M:5173` help の「two」→「three」(文言のみ)。
- tests の A-2 sha pin は main 取り込み後の現行値 (`f8a77806…`) のまま。新 policy の bytes sha を test に焼く場合は literal pin として 1 箇所に置く (A-6 と同形)。
- author は `tools/run_tests.py` 経由で `orchestrator/tests/test_paper_story_a2_certification.py` と `test_paper_story_a2_job_contract.py` を実走し nodeid を報告する。

所有 (author 1 本):
- `orchestrator/campaign/paper_story_b7_fixed5_regression.v2.json` (新規)
- `orchestrator/campaign/paper_story_a2_certification.py`
- `tools/pegasus/submit_paper_story_a2_certification.sh`
- `orchestrator/tests/test_paper_story_a2_certification.py`
- `orchestrator/tests/test_paper_story_a2_job_contract.py`
所有外: job body、A-2/A-6 policy、admission_registry、plotter、docs。

## 変異事前登録 (DW-M01、単一理由; 期待 node は author の実走結果で確定し、確定できないものは初回を probe と明記)

| id | 置換 | 期待 | 単一理由の根拠 |
|---|---|---|---|
| M1-b7-adopted-genome | 新 policy JSON の `rr50-fixed5` の `BACKOFF_FIXED: 5` → `10` | KILLED (新 policy 正例 + literal pin test) | `M:609-616` の adopted 整合検査だけが拒否 |
| M2-b7-shape | `policy_shapes` の `(3, 6)` → `(2, 4)` | KILLED (新 policy を load する全 test) | `M:569-572` の shape 検査だけが拒否 |
| M3-b7-canonical-path | `canonical_paths` から新定数を外す | KILLED (CLI `--policy` 選択の正例) | `canonical_policy_path` だけが拒否 |
| M4-b7-job-name | `_qsub_job_name` の新 entry を外す | KILLED (job 名 test、submitter 契約 test) | `_qsub_job_name` の KeyError だけ |
| M5-b7-env-keys | `_qsub_environment_keys` で新 study を `IZANAGI_A2_POLICY_PATH` 不要側へ | KILLED (env 集合 test、submission receipt 検証 test) | `M:1584-1585` の env 照合 |
| M6-submitter-273 | `S:273` の条件から新 study を外す | KILLED (submitter 契約 test の env assert) | 投入 env に POLICY_PATH が乗らない |
| M7-submitter-365 | `S:365` の条件から新 study を外す | KILLED (submission receipt の環境集合検証) | receipt 再構成の env 不一致 (`M:1577-1589`) |
| M8-cli-help-text (diagnostic) | help の「three」→「two」 | SURVIVED 期待 (等価、文言のみ) | 受理集合を変えない。kill に数えない |

M2 は複数 test が同時に赤になる (完全集合を author 報告から確定)。M6/M7 は shell 側なので、契約 test が実 submitter を wrapper 越しに走らせることを author 報告で確認してから期待 node を固定する。走らせられない (bash 経路が test に無い) なら M6/M7 は登録から外し、その旨を台帳に書く。
