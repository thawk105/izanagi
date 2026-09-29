# 段 4 裁定 (2026-09-29 23:45 JST、親)

入力: brief.md、codex/consult-out.md (段 3 相談 1 本、check_codex_output rc=0)。裁定 inbox は wave 開始後の新着なし (最新 22:23)。

## 所見の裁定
1. 高 (login の温めを `python3 -m pytest` 直叩き) — **real・採用**。AGENTS.md:52「pytest・build を自分で直接起動しない。必ず tools/run_tests.py を通す」。login の `run_tests.py --collect-only` は dispatch されうる (memory: request 11867) ので温めに使えない。→ **brief §5 (ii) の明示的な温めを撤回**。温めは受入自身の login collection (`tools/run_tests.py` の `_collect_login_universe`、正規経路) に任せ、雛形からは export 行を外すだけにする。
2. 高 (温めた木と検査する木の不一致、温め待ち) — **real・(1) の撤回で解消**。login collection は launcher 内の post-claim merge の後の木で走るので、書く pyc は検査対象の木のもの。温め待ちの工程は存在しなくなる。残る限界: 待ち行列が login collection (冷で約 50 秒) より短い走では shard が冷のまま始まる (中間 12 走の型、仮説)。
3. 中 (雛形の行を消しても呼出元 env に値が残る) — **real・採用 (記録で対処)**。作用点は login 側 cache 作成のみと明記。対照の各走で login collection の実効 env と dispatch request.json の env を記録する。呼出元が自分で export する wave は効果が出ない、を限界に書く。
4. 中 (約 60 秒は因果未確定) — **real・採用**。「約 60 秒」は観測差 (別 wave・別の木) と書き、効果は下の対照で判定する。
5. 中 (fixture・割付は未評価分がある、md_2 の完了としない) — **real・採用**。割付の差 0 秒は試算した台帳置換案に限る。fixture 共有は本 wave で実装せず、shard-0 の最忙 worker (実測 207 対 s1/s2 約 157) を作る成分を次の一手として一次資料に数値つきで残し、最終報告で「md_2 の fixture 項は未実施」と明記する。理由: 対照で効果を測る計算予算と、状態共有の検証 (段 3・6) を要する別単位であり、主因 (pre +60 秒) の是正を先に着地させる (DW-G05)。
6. 中 (対照の判定条件不足) — **real・採用**。下の事前登録。
7. 低 (中央値の和は分解式でない) — **real・採用**。「各指標の中央値」と表記。
8. 低 (pyc は撤去の証拠収集・land の ignored 衝突では見える) — **real・採用**。「通常の pyc は受入の clean 判定に出ない。撤去は ignored file を証拠化し量が増えうる」と限定して書く。

## plan v2
- U1 (Codex author): 共有雛形の新版 = 旧版から `export PYTHONDONTWRITEBYTECODE=1` の 1 行を除き、冒頭コメントに 1 行「PYTHONDONTWRITEBYTECODE は立てない (受入の login collection が投入元 worktree の pyc を温める。9/26〜29 の冷の原因、acceptance-critical-path)」を足す。他の行 (門番の閾値・周期・再投入) は byte 不変。子は worktree 内 scratch (`scratch-acp/`、untracked) に書き、親が差分を監査して旧版を job dir へ退避のうえ配置、scratch は削除。
- U2 (Codex author): 対照の runner と集計器 (同じ scratch)。runner は下の事前登録どおりに 1 対を起動し記録する bash、集計器は shard dir から判定量を出す python。
- repo 内の実装面差分ゼロ → 変異 matrix 免除 (DW-S04)。受入全走は land 用に 1 回 (新雛形で投入)。
- 記録: 一次資料 `output/insights/2026-09-29/acceptance-critical-path/README.md`、spool fragment (worklog / decisions / failures)。

## 対照の事前登録 (結果を見る前に固定)
- 木: 同じ commit C (投入直前の local main) の fresh worktree 4 本 (K1, H1, K2, H2)。作成直後は `orchestrator/tests/__pycache__` の pyc が無いことを数えて記録 (0 でなければその木を使わない)。submodule は `tools/dev_wave_submodule_init.py` で初期化。
- 条件: K = 旧雛形相当 (`PYTHONDONTWRITEBYTECODE=1` を export して `IZANAGI_ACCEPTANCE_SHARDS=3 python3 tools/run_tests.py`)、H = 新雛形相当 (同 env を unset して同 command)。PYTEST_ADDOPTS 等は空。lease・receipt は使わない (計測走)。門番は置かない (login の load は条件にしない)。
- 対: 対 i は K_i と H_i を同時刻 (起動差 5 秒以内) に投入。対 1 の終端後に対 2 を投入。H_i は各々 fresh (初回受入の条件)。
- 記録 (各走): commit、起動・終了時刻、rc、投入前と終了後の pyc 数 (tests/__pycache__ と全体)、login collection の実効 env (`PYTHONDONTWRITEBYTECODE` の有無)、各 shard の request.json env、hostname、confirm→開始の待ち行列、pre、W、最大 worker 占有、login-collection.log の mtime、同時刻の他の受入 leader 数。
- 判定量: 対ごとに Δpre_s = pre_s(K) − pre_s(H) (shard s = 0,1,2)、ΔW = W_max(K) − W_max(H)。
- 判定: 「雛形の変更で shard の collection が縮む」は 2 対とも、H の shard のうち login collection 完了後に始まった shard すべてで Δpre ≥ 30 秒のとき支持とする。ΔW は値と符号を報告し、2 対とも正のときだけ「W_max が縮んだ観測」と書く (有意差とは言わない)。H の shard が login collection 完了前に始まった場合はその shard を別に数え、判定から外した旨を書く。
- 無効条件: いずれかの走が赤 (rc≠0) か shard 欠落なら、その対は対ごと無効とし 1 回だけ取り直す (上限 2 回、超えたら判定不能と書く)。K の投入前 pyc が 0 でない、または H の env に値が残った走は無効。
- 計算: 4 走 × 約 0.25 node 時間 = 約 1.0、取り直し最大 +0.5、最終受入 約 0.25 → 最大約 1.75 < 2 (確認不要)。実績は dispatch の Elapse で記録。
