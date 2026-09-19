## 完了した中間成果

- クラス 3 起動手順・DW-C00/C01/STOP/S01/G01〜G05/O20・skill-self-improvement・handoff README・残 handoff (T-1998、非接触) 読了。
- worktree 作成、submodule 3 段初期化 (全行空白始まり)、`check_wave_startup.py --mode fresh --external-handoff` 緑、worktree は session lock 済み。
- 一次資料: D2148 項 12、D1877、D1936 項 43、F945 全再発記録、fixture 現物 (`orchestrator/tests/test_t1259_qsub_env_delivery_probe.py:73-97`)、
  probe 現物 (`tools/pegasus/probes/t1259_qsub_env_delivery_probe.py:133-190`、`_run_git`/`_repo_is_detached` が `timeout=30.0`)、
  conftest の real-repo memo work unit (`orchestrator/tests/conftest.py:670-700`、2161-2177 の接尾除去)。
- **前提実測 (受入 shard junit 33 走、9/18 20:00 以降、`/work/1/SFC/tanab/.izanagi-acceptance-shards/*/shard-0/junit.xml`):**
  - 252e24b4f (2026-09-18 23:47 JST、T-2780 wave が t1259 の 30 関数を `REAL_REPO_PROCESS_MEMO_NODES` へ追加) より前の tip では
    t1259 の nodeid に `@real-repo` 接尾が無く (= 非 group、xdist worker へ個別分散)、**1 shard で module fixture の実走査が 42〜46 回**
    (worker ごとに同じ worktree を同時走査)。走査所要 (junit time、4 git 呼び出しの合計) n=567 (+ error 59 件は 30 秒で右打ち切り):
    p50 20.2 / p90 33.8 / p99 47.3 / max 57.7 秒。error は 14 走で 0〜28 件。
  - 252e24b4f 以後の tip (19 走) では接尾 51 = 1 work unit、**走査は shard あたり 1 回**、所要 n=19 (打ち切り 0):
    p50 8.8 / p90 14.1 / p99 22.9 / max 24.5 秒 (max は 9/19 00:43、前 regime の他 wave 受入が並走していた時刻)。**error 0 / 19 走。**
  - shard は計算ノード (junit `hostname="bnodeNNN"`) で走り、worktree は lustre。junit `timestamp`/`time` で受入セッション間の重なりを復元可能。
- repo 内に 30 秒文字列へ依存する consumer は無い (`check_acceptance_reds.py`・`acceptance_shards.py` を grep)。probe の sha256 は
  記録済み evidence (2026-09-07) だけが持ち、test/凍結の pin は無い (規律 7: 記録は不変)。probe path の hooks 分類は「実行場所」のみ。

## 段 1 brief

- **研究前進 (土台):** CC 合成 (K2 loop、A-1/A-2 campaign) の全成果は受入 gate を通って main へ着地する。F945 (t1259 走査 timeout) は
  9/9〜9/18 に docs-only wave を含む 15 本超の受入を 2〜8 走へ膨らませ (1 走 10〜30 分)、T-2724 回収では停止まで招いた。
  本 wave の最小差分 = fixture 局所の待機上限 (production 30 秒は不変) + F945 台帳への機序・分布・採用値の記録。完了判定 = 採用値を
  実測分布と対で示し、負例 2 種で上限と走査の生存を示し、受入 child-green。
- **scope:** (1) `tools/pegasus/probes/t1259_qsub_env_delivery_probe.py` に keyword-only の git timeout 引数 (既定 30.0 = production 不変)
  を足し `_repo_snapshot` まで通す。(2) `orchestrator/tests/test_t1259_qsub_env_delivery_probe.py` の module fixture が fixture 定数
  (候補 120.0 秒) を渡す。(3) 正例 test: production 既定が 30.0 で、fixture 経路が定数を渡すことを `subprocess.run` の timeout 捕捉で
  示す (無条件版と条件版の対)。(4) Codex author が書く計測 script 2 本 (junit 集計器 = 受入セッション重なり数で層別、login 側 sampler =
  4 git 呼び出し別の所要 + load + leader 数)。(5) F945 追補 fragment、worklog fragment、insight README (一次資料)。
- **scope 外 (引数と D2148 項 12 の逐語):** 自動再投入 loop・production timeout の一律変更・新 gate・投入 slot 機構・untracked 走査の
  削減・live main 照合条件・hold 登録・門番条件値。conftest の memo 配置 (252e24b4f) には触れない。
- **確定済みユーザー裁定:** D2148 項 12 (120 秒は候補、実測で確認、走査対象・拒否能力維持、production 一律変更なし)。D1877 (混雑下の
  完了時間を測って有界に決める)。D1936 項 43 (module 単位 1 回、production timeout 維持)。D95 (実装は Codex author)。
- **不変条件:** 走査対象 (rev-parse / status --porcelain=v1 --untracked-files=no --ignore-submodules=none / ls-files --others
  --exclude-standard -z / symbolic-ref) と例外の型 (`subprocess.TimeoutExpired` を包まない = F945 署名が junit に残る) を変えない。
  負例 `test_job_start_requires_manifest_head_detached_and_clean_repository[untracked_paths-…]` は不変で緑。fixture は timeout 時に
  fail-closed (代替 snapshot を返さない)。production `observe()` の呼び出し既定は 30.0 のまま。
- **成果物の形:** 実装 commit (Codex author trailer)、変異 matrix (M1 上限 0 → 全 51 test error で kill、M2 走査省略 → digest/HEAD 束縛 test で
  kill)、insight `output/insights/2026-09-19/t2790-t1259-scan-timeout/README.md` (分布表・条件別層別・採用値・F945 再発条件)、
  spool fragment (worklog / failures F945 追補)、受入 child-green、land。
- **並列分割方針:** 軽量版 (DW-C00)。段 2・3 は省き、段 6 の独立 read-only レビュー 1 本を残す (拒否能力に触れる fixture 変更 +
  一次資料からの事実再抽出、D2148 項 11 の精神)。author 1 本 (実装 + 正例 test + 計測 script)、fix 子は must-fix 時のみ。
- **(P1) 親の provisional 裁定・攻撃対象:** F945 の主因は「非 group 化された t1259 が worker ごとに module fixture を再実行し、同一
  worktree を 42〜46 本同時走査していた」こと。根拠は前後 33 走の junit (接尾 0 ↔ 43〜46 回、接尾 51 ↔ 1 回)。時刻・負荷との交絡は
  未分離 (後 regime の max 24.5 秒は前 regime wave 並走時)。
- **(P2) provisional:** 上限は呼び出しごと (production と同じ構造) とし、合計予算は設けない。候補 120 秒は後 regime max の約 5 倍、
  前 regime の非打ち切り max 57.7 秒の 2 倍、real-repo lock deadline 245 秒未満。
- **(P3) provisional:** 採用値は、本 wave の受入 1〜2 走の in-situ 値と sampler の分布で max ≤ 60 秒なら 120 秒。超えたら値を
  上げずに報告し裁定へ (D2148 項 12「確定値にしない」)。
- **受入・実測環境:** 受入は `dev_wave_wait.py acceptance` (3 shard、計算ノード dispatch)。sampler は login node で wave worktree に対し
  実行 (shard は計算ノードなので host 差あり — in-situ 値 = junit time を主、sampler は層別の補助と明記)。
- **模擬/実の差:** junit time は 4 git 呼び出し + sha256 3 file の合計であり呼び出しごとの値ではない (30 秒超でも error でない sample
  がある)。sampler だけが呼び出し別を測る。
