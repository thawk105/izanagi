---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-20
wave: dev-wave-t2790-t1259-scan-timeout
seq: 1
---

## supersede 追記

- F945 **supersede: 2026-09-20** — D2148 項 12 の受入 fixture 限定の再検討 (T-2790) で「I/O 要因は分離していない」「timeout 拡大は行わない」を次のとおり更新する: (1) 252e24b4f (2026-09-18 23:47 JST、T-2780 wave) より前は t1259 の nodeid から `@real-repo` 接尾が conftest で剥がされ xdist worker へ個別分散していたため、受入 shard-0 で module fixture の実走査が走ごと 42〜46 回実行されていた (受入 shard junit 18 走、fixture を含む testcase の time は n=713 で max 58.9 秒、setup error 87 件 = time ≥ 30 秒の実 timeout 74 + fixture 例外 cache の再掲 13)。同 commit で 30 関数が `REAL_REPO_PROCESS_MEMO_NODES` に入って 1 work unit になった後は走査が走ごと 1 回、24 走で max 24.5 秒、setup error 0。これは grouping 後の改善の観測であり、時刻・host・共有 FS 負荷との交絡は未分離で主因の分離ではない。(2) T-2790 は fixture 局所の待機上限 `orchestrator/tests/t1259_scan_bound.py` の `FIXTURE_GIT_TIMEOUT_SECONDS` (git 呼び出しごと、採用値 120 秒 = 接尾あり regime 26 走の in-situ max 24.5 秒の 4.9 倍・前 regime の非打ち切り max 58.9 秒の 2 倍、login sampler の呼び出し別 max 6.3 秒。他 session ≥ 3 本並走・load1 > 60 は未観測条件。根拠は `output/insights/2026-09-20/t2790-t1259-scan-timeout/README.md` §6) を導入した。production `_run_git` の 30 秒・走査 argv 4 種・`observe()` の拒否は不変。(3) fixture は取得後に `detached` / `tracked_status` / `untracked_paths` を模擬値へ上書きするので、fixture の実走査で検査力を持つのは `head` と `source_sha256` だけである (走査省略の変異は digest 束縛 test 16 件で赤)。(4) 再発時は junit の Git argv と `TimeoutExpired` の値 (30 秒なら production 経路、採用値なら fixture 経路)、nodeid の接尾、traceback の fixture 名で経路を確認する。同 module の testcase time ≥ 2 秒の件数は fixture 実行回数の補助指標であり、それだけで原因を断定しない。
