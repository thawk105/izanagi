---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-20
wave: dev-wave-t2797-b5-contrast
seq: 1
---

## {{D:b5-slot-subprocess-driver}}. B-5 生成器対照の 3 arm は `p3_s4_loop` CLI の subprocess で slot ごとに評価し、slot key を identity に焼いて fresh layout・claim・B 消費点を機械化する

**決定:** D2172 項 4 (α) の残部品 (事前登録 §10) を次の形で実装した。

- **評価経路:** 3 arm とも slot (系列開始 stock 1・探索 ≤ 10 評価・endpoint 再計測 5、block stock 5) ごとに `p3_s4_loop` を subprocess で 1 回起動する
  (事前登録 §4.1 / §5.1 の逐語)。新 module `b5_generator_contrast` は系列管理 (生成器・台帳・分類・handshake・endpoint) を所有し、`run_campaign` を直接呼ばず、
  coder build authority の新 entrypoint も登録しない (登録簿 `materializer_admission` と `_DRIVER_CONTRACTS` の閉包を動かさない)。
- **`p3_s4_loop` の seam 4 点:** `--b5-slot KEY` (`search_config["b5_slot"]` へ焼き campaign identity・claim file・protocol digest を slot ごとに分ける、
  較正 + `--verify-performance` を必須にする)、`--machine-generated-proposal` (random / sweep の候補は coder authority 無しで generator receipt
  (machine-generated class、input = proposal bytes の sha256 と genome sha256) により admission、STOCK evidence は None で fail-closed)、
  `--b5-sidecar-dir` (`slot-start.json` を layout 確定直後、`pipeline-submitted.json` を `run_campaign` 直前、候補起因の前処理拒否は
  `proposal-rejected.json` + rc 3 で durable 記録)、B-5 mode の skip 拒否 (`duplicate-skip`、rc 1、`_resolve_duplicate` に到達しない) と
  `bench_max_rounds=3` の明示。既定経路の argv・identity preimage・`run_campaign` kwargs は bytes 不変。
- **A / B の消費点:** A は原提案の機会 (空出力・schema・値域・帰属不一致・文法・検疫の不通過も消費)、B は `pipeline-submitted.json` が書かれた
  attempt (投入後の build 失敗・anomaly・bench abort・walltime も消費)。分類は sidecar と WAL から決定論的に導き、CLI の rc から導かない。
  driver は subprocess 起動前に `slot-attempt-start` を台帳へ durable に書き、report は終端 event の無い attempt の sidecar から B と物理 attempt を回収する
  (job 打切り時の過少集計を防ぐ)。
- **機械故障の retry:** 同論理 slot・attempt+1 (identity も別) で追加 2 回まで、対象は pre-start failure と `{bench,verify}-{probe-error,competing-tenant}` だけ。
  verdict `indeterminate`・anomaly・品質赤・候補 build 失敗・timeout・分類不能は retry しない。上限到達は `unclassified-missing` (score None、fallback 無し)。
- **品質欠測:** WAL `bench_done` の `len(tps) != reps ∨ unstable ∨ settled is not True` を台帳側で分類 (pipeline は変えない)。B も A も返さず endpoint 資格なし。
  探索の品質欠測は当該 session の資格だけを失い系列は継続、§7.4(2) の系列単位の欠測は score / stock session に限る。
- **LLM arm の handshake:** job が `request-<a>.json` (次評価 k、期待 whiteboard、`current_perf` = 直近の certified かつ品質正常な評価か系列開始 stock) を公開し、
  親が `inputs-<a>.json` と `proposal-<a>.json` (または `proposal-<a>.rejected.json` = A 消費) を atomic に置く。job は `assert_inherited_inputs` で whiteboard の
  順序・値・全 field、`current_perf` / `baseline`、k ≥ 2 の診断の両側存在を検査する。1 機会 2700 s の無応答は `proposal-wait-timeout` (分類不能欠測、retry 無し)。
- **解析 consumer:** §6 / §7 (score・floor・exact permutation・Holm 族 6・判定順 1〜8・fallback 対の主 / 副解析・anomaly の横断失格) を実装し、試走は
  `purpose="pilot"` の記述経路 (`registered_judgment="not-applicable-pilot"`) を通す。B と評価件数・連番、certified の `fitness_tps == bench median` を検査する。
- **job body と launcher:** `IZANAGI_S4_B5_MODE` で既存 job body に B-5 mode を 1 箇所足し (既存 3 経路は bytes 不変)、login 側 launcher
  `tools/pegasus/b5_contrast_launch.py` (`local-ok`) が 4 job 固定 (53 ≤ 60 論理 session) を `qsub -v` の明示列挙で組む。

**理由:**
- 事前登録 §4.1 は LLM arm の評価を「`p3_s4_loop` の単回評価を fresh layout で 1 回呼び出す」と定め、§5.1 は 3 arm の共通経路を「`p3_s4_loop` の proposal 読込みから
  `run_campaign` まで」と定める。subprocess 案はこれを逐語で満たし、fresh layout の下では `drive_iteration` の入口 `check_stop` が発火しない (§3.4 が
  「発火しない」と書く運用契約そのもの) ので停止の不適用が機械化される。
- 段 3 相談 2 本が独立に指摘した 3 点 — BUILD_START の不在は未投入の証拠にならない (投入後・最初の WAL record 前の中断)、同 slot の subprocess retry は
  残存 claim (`<identity>.claim` は O_EXCL で解放されない) に拒否される、45 分無応答は機械故障の証拠にならない — を sidecar・attempt identity・分類不能欠測で閉じた。
  peer (K2 同 job pair、D2183) の実走で同 campaign の stock が claim 衝突で rc=1 になった事実がこの設計の追加根拠。
- generator receipt (machine-generated class) は既存 driver (backoff_extended_sweep) と T-2795 の stock resolver の先例に同型で、D2186 項 4 (stock-baseline class を要求しない)
  と整合する。

**却下した選択肢:**
- 新 module を coder entrypoint として登録し in-process seam で評価する — `EXPECTED_CODER_SITES` / `_DRIVER_CONTRACTS` の閉包へ driver contract 一式を足す費用と、
  private 名 (`_run_one_iteration_resolved` 等) を十数個跨ぐ結合が増える。
- 評価ごとに fresh submit-tree を切る (K2 round 2〜3 の運用) — identity だけで slot を識別できず、checkout・receipt・WAL 所在の管理が評価数だけ増える。
- 別 job body file — 300 行の preamble (env 衛生・python 解決・prebuild・reservation) の複製と新 job body の登録が増える。
- 無応答 timeout を機械故障として retry する — §3.3 の限定列挙に無く、消費済みの生成機会を無料で返す。
- verdict `indeterminate` を機械故障に含める — 認証できなかった事実は通信・node 喪失・供給障害を証明しない。
- 純 verifier 秒の計時 adapter・hash8 衝突の事前網羅・汎用 retry / 再配置・108 系列 launcher・発効 gate — 依頼にも §10 にも無く、試走に不要。

## {{D:b5-pilot-execution-facts}}. B-5 試走 (β) の運用事実 — guard は main の登録簿を読む、並列 job の performance verify pass と bench は home 共有の 1 本の lock で job を跨いで直列化される

**決定:** 試走の投入と実測で判明した運用事実を、本走の launcher 設計と費用裁定の前提として記録する。

- `hooks/guard_bash.py` は main checkout の `tools/pegasus/admission_registry.json` を読むため、wave 内で登録した login 側 launcher は land まで Bash から直接起動できない。
  試走は job dir の投入 script が launcher の API (`validate_submit_tree` / `pilot_jobs` / `launch`) を import して同一 argv を組み、dry-run → submit の順で投入した。
- `p3_s4_loop_pegasus.sh` は `IZANAGI_BENCH_LOCK` を設定しないので、bench lock は既定の `~/.izanagi/bench.lock` (home = 共有 FS) になり、
  同 user の並列 job (別ノード) が 1 本の lock を取り合う。lock は bench 本体だけでなく **performance tag の verify pass 全体 (`fullscale_isolated`、
  5 rep の trace 走行 + verifier) も囲む** (`pipeline.py` の `_run_one_pass` 呼出し)。試走の台帳ではこれが「performance verify の初回 rep だけ
  215〜913 s、2〜5 回目は 34〜91 s」「bench の周辺 wall が本体 17 s に対し最大約 1060 s」として現れ、lock を即時に取れた session (sweep arm の
  評価 2〜5) には初回 rep の固定費が無い。B-10 / A-5 の job body は `IZANAGI_BENCH_LOCK="$TMPDIR/bench.lock"` (node-local scratch) を設定して
  この直列化を避けている (先例)。本 wave では job body を変えず (試走中の変更は所要の比較可能性を壊す)、本走の launcher / job body 設計の
  再提示項に載せる。flock の待ち時間そのものは計測していない (code 読みと台帳の型からの帰属)。
- 1 session の subprocess wall は 642〜1521 s (10.7〜25.4 分)。lock 待ちを除いた固有費は build 15 s + legacy verify 7〜16 s + performance pass
  5 × (34〜91) s + bench 17 s ≈ 4〜8 分で、事前の外挿 (12〜14 分) は lock 待ち込みの値としては下限側、固有費としては上限側だった。
- 1 つの submit-tree から 4 job を同時に走らせても、系列開始 stock の同一 genome build は cache 公開の競合で落ちなかった (先着の公開を後続が cache hit)。
  ただし同時 build の一般保証ではなく、本走の launcher 設計では job ごとに submit-tree を分けるか、cache 公開の競合を検査する。

**理由:** いずれも試走でだけ観測できた事実で、本走の総実行 wall 上限 (§11)・費用上限 (D2172 項 4 (γ) 4) と発効束 (§12) の再提示に必要。lock の帰属を誤ると、本走の所要見積りが 2〜3 倍過大になる。

**却下した選択肢:** guard の登録簿参照先を wave 側へ変える — hooks は main の防壁であり、wave 内の編集で防壁が変わる設計にしない。試走中に job body へ `IZANAGI_BENCH_LOCK` を足す — 走行中の 4 job の所要が前後で比較できなくなり、本走用の変更は裁定パッケージの範囲。
