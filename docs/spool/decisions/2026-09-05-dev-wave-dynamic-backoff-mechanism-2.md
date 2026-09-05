---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-05
wave: dev-wave-dynamic-backoff-mechanism
seq: 2
---

## {{D:dynamic-backoff-count-window-design}}. Cicada 型 adaptive backoff の動的化は「最小間隔で間引いた計数窓・整数 µs の適応刻み・下限 50 µs の動的上限」を stock 同値の既定で重ね、診断計器は別 macro の `#if` で perf build から消す

**決定:** `patches/cicada-adaptive-params.patch` (A、bytes 不変) の上に `patches/cicada-adaptive-dynamic.patch` (B) を重ね、
CMake option 7 つ (`CCBENCH_BACKOFF_COUNT_WINDOW` / `_COUNT_CAP_US` / `_STEP_ADAPT` / `_STEP_MIN_MILLI` / `_STEP_MAX_MILLI` /
`_DYN_CEILING` / `_TRACE`、既定はすべて stock 同値) で 3 定数を動的化する。意味論は次で固定する。

- **計数窓:** K>0 のとき、leader は経過が `UPDATE_US` (最小間隔) に満たない間は counter を読まない。読んだ後は
  「commit 数 ≥ K または経過 ≥ cap (最大間隔)」で更新する。時刻は counter 走査の**後**に取り (stock と同じ端点)、
  走査は 1 窓に 1 回だけ起こる。K=0 は stock の時間判定を逐語で残す。
- **適応刻み:** 勾配符号が前回と同じなら刻みを ×2 (上限 STEP_MAX)、反転または 0 なら ÷2 (下限 STEP_MIN)、当該更新に使う。
  **刻みは整数 µs に限る** — `last_backoff_` は stock どおり `uint64_t` であり、sub-µs の刻みは偽ゼロ勾配を作る
  (T-2216 §3、D1576)。
- **動的上限:** `Backoff_` が上限に当たったとき、負勾配なら上限を整数半減 (下限 50 µs = T-2187 の既測点)、正勾配なら倍増
  (上限 `MAX_US`)。上限を更新してから一歩を踏み、新上限へ clamp する。
- **診断計器 `BACKOFF_TRACE`:** D14 の数値 `#if` 契約で、verifier 用 `CCBENCH_TRACE` とは別 macro。leader の更新ごとに
  12 field (窓の経過・commit 数・発火理由・前後の `Backoff_`・勾配符号・刻み・上限・上限変更・parity 分岐) を
  64-byte aligned の ring (65,536 件) に溜め、static 記憶域オブジェクトのデストラクタで stdout へ流す。
  **`#include` 行を 1 行も足さない** — `source_digest.assert_includes_match_head` が `include/backoff.hh` の include 行を
  HEAD と逐語比較するため。perf build (`BACKOFF_TRACE=0`) には診断 symbol (`izanagi_backoff_trace` 接頭辞) も
  文字列 (`IZANAGI_BACKOFF_TRACE`) も残らないことを probe が `nm` と `strings` で fail-closed に検査する。
- **時刻 seam:** `check_update_backoff_at(now, committed)` / `update_backoff_at(now, committed)` を本体にし、production の
  `check_update_backoff()` / `update_backoff(committed)` は `rdtscp()` を渡す wrapper とする。遷移 test
  (`orchestrator/tests/test_dynamic_backoff_transitions.py`) が g++ で A+B を compile し、K 境界・cap・間引き・刻みの上下限・
  上限の単調と floor・既定値での stock 同値 (`Backoff_` 列の一致) を合成入力で固定する。

**理由:**
- D1505 の候補機序 (10 µs 窓に入る commit が少なく勾配符号がノイズに支配される) を直接狙うのが計数窓である。ただし
  D1576 のとおり更新は leader の試行先頭でしか評価されないので、K 到達の検知は次の試行まで遅れる。それでよい。
- counter 走査を毎試行にすると 48 counter の acquire load が leader の全試行に入り、計数窓の効果と走査費用が交絡する
  (段 3 相談)。最小間隔で間引くと走査は 1 窓に 1 回になり、`UPDATE_US=2560` の腕では tuned と同じ頻度になる。
- 走査前の時刻を update に使うと、走査時間の変動が throughput 推定に混入する (段 6 レビュー)。stock は走査後に時刻を取る。
- login node の実 build で、A 単独と A+B 既定の `ycsb_silo.exe` はアドレス注記を除いた `objdump -d` の命令列 60,242 行が
  完全一致した (差は rip 相対のデータ位置のみ)。既定値 stock 同値の直接証拠である。
- 1 回目の生死確認は `-Werror=unused-parameter` で既定 build が落ちる欠陥を捕まえた (遷移 test は警告フラグ無しで compile
  していた)。以後、遷移 test は CCBench と同じ `-Wall -Wextra -Werror` で compile する。

**却下した選択肢:**
- 毎試行の counter 走査 — 走査費用が機構の効果と交絡する。
- sub-µs の適応刻み (0.25〜8 µs) — `last_backoff_` の整数切り捨てで勾配符号が壊れる。`double` 化は stock の型を変える。
- `atexit` / `<cstdio>` による flush — include 行の追加が identity gate に掛かる。
- `nm` だけの症状検査 — inline 化で symbol が消える偽陰性があるため `strings` の文字列 literal も併用する。
- `patches/ledger.json` への登録 — 同台帳は D18 第 4 類 ability probe 専用で、`silo_ladder_rung1_contract.py` が entry 数 1 を
  exact 要求する。B は第 3 類の合成 variant として `patches/README.md` と `DefineSpec` 登録簿に載せる。

## {{D:dynamic-backoff-measurement-protocol}}. 動的 backoff の実測は事前登録した 7 腕・対内 log 比・6〜7 block の欠測規則で判定し、認証は全機構 on の 1 腕を T-2189 の機構で 24 request 走らせる

**決定:** `docs/dynamic-backoff-preregistration.md` (v1.1) を正本とし、次を固定する。

- 腕は 7: `none` / `stock` (陽性対照、H6 のみ) / `tuned` / `tuned-u10240` (時間のみ 10240 µs の対照) / `cw` / `cw-as` / `cw-as-dyn`。
  基準線は D1506 の `none` と `tuned` の 2 本で、`stock` 単独比の優位は書かない。
- 判定は同一 block (job = node) 内の対内 log 比、t 分布 95% CI、等価域 ±3%、点ごとの 5 判定語と仮説単位の三値判定
  (accepted / rejected / inconclusive)。robust benefit = 全 24 点で非劣性 ∧ (write-heavy, 48) と (balanced, 48) で実用優越。
  結果を見た後に endpoint を選ばない。
- block は 7 (rep 0..6、腕の実行順は巡回)。complete block が 6 でも判定し (df=5)、点欠落は両腕のある block だけで
  対比を取り、n < 6 の点は inconclusive。hostname の重複は拒否せず記録する。
- 診断 (`BACKOFF_TRACE=1`) は別 build・別 run、rep 0 の exact 1 job、headline 不適格。「方向的中」= 更新 i の action 符号と
  更新 i+1 の窓 throughput 差の符号の一致 (action 0 は unscored) で、内部推定器の自己一致ではない。
- 認証は T-2189 の `--mode certify` (連言 10 項、陽性対照、24 request、verifier identity の事前固定) を `cw-as-dyn` 1 腕に
  対して走らせる。認証するのは「full-on build の観測 24 走行が serializable」であり、機構の各枝の被覆は認証しない。
  `cw` / `cw-as` は未認証と明記する。認証は perf の完了後 (performance artifact の path/sha を束縛する契約上)。
- 成果物 JSON は `repo_head` / `repo_status_clean` / `prereg_sha256` / patch stack / `driver_sha256` / `pbs_sha256` /
  `driver_argv` / hostname / `cell_order` / prologue と job 総時間を記録し、図の provenance へ転送する。
- 計測は wave worktree でなく、固定 SHA の detached worktree (`submit-tree`) から投入する。変異走で wave worktree が
  書き換わる間も計測は同じ bytes を読む。

**理由:**
- 腕別の生値 CI の重なりでは paired design の利点を捨てる。対内 log 比が事前登録の判定式である (段 3 相談 B)。
- `tuned-u10240` が無いと、計数窓の効果と「単に更新間隔が長い」効果を分離できない (段 3 相談)。
- 認証を perf の結果で条件付けにする案 (段 3 相談 B) は、ユーザー引数が「同じ wave で動的版にも trace-enabled + verifier を
  通す」と明示しているため採らない。
- 段 6 時点で投入していた canary 2 job は patch B の修正前の実行体で走ったため、生死確認に格下げし block に数えない。

**却下した選択肢:**
- 既定 adaptive を基準線に置く — D1506。
- 7 block の distinct-host を要求する — scheduler が同じノードへ置くと正しい測定を捨てることになる。
- perf mode の probe に exact 7 cell を焼き込む — 親の投入 script が exact 文字列を渡し、JSON の `cell_order` と図生成器の
  構成値検査で腕 identity は閉じる。
- 既発行 group receipt の再検証と trace 削除の閉包 (段 6 レビュー A) — T-2189 の既存機構で本 wave の変更外。裁定パッケージへ。
