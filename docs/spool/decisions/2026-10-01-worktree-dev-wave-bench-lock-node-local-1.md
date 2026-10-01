---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-10-01
wave: worktree-dev-wave-bench-lock-node-local
seq: 1
---

## {{D:bench-lock-node-local-default}}. bench_lock の既定 path を node ローカル固定名 /tmp/izanagi-bench-<uid>.lock にする

**決定:**

1. `orchestrator/campaign/lock.py` の `default_lock_path()` は、非空の `IZANAGI_BENCH_LOCK` をそのまま返す (不変)。
   未設定・空文字なら `/tmp/izanagi-bench-<uid>.lock` を返し、`~/.izanagi` を作らない。計算ノードと login で同じ規則とする。
2. `bench_lock()` は flock 取得直後に `os.utime(fd)` で lock file の mtime を更新する (OSError は無視して lock は保持)。
   open flags・blocking・`BenchBusy`・unlock は変えない。`O_NOFOLLOW` は入れない。
3. **保証範囲:** 既定 lock が排他するのは「同じ node で既定 path を使う同じ uid の process」どうしだけである。次はこの排他の外にあり、
   pipeline の取得直後の競合検査 (`competing_bench_pids`) が残りの防壁になる。
   - fan-out worker の task 固有 lock (`verify_fanout_worker.py`)
   - `$TMPDIR/bench.lock` を明示する job body 3 本 (b10_backoff_grid・a5_second_boot_backoff_sweep・p3_s4_loop_pegasus の B-5 分岐)。job 固有なので同じ node の別 job を排他しない (D2209 の既知の縮小)
   - `bench_lock()` を取らない calibration (`certify_calibration.sh`)
   - 移行期の旧 SHA の job (home の旧 lock を見る)
   - 他 user
4. **運用条件:** fan-out を含む実走 (A-2 など) を並走させるときは、job 間で head と兄弟の node 集合が交わらないことを前提にする。
   旧 SHA の job と新 SHA の job を同じ node に混在させない (旧 job の終了後に新 checkout の job を流す)。
5. login で lock の置き場が login host ごとになることは、login での計測を許すものではない。pipeline は計測の入口
   (`_require_measurement_site`) で login を拒否する。

**理由:**
- lock の目的は同一マシン上の CPU・cache・メモリ帯域の奪い合いによる測定汚染の防止である (lock.py の docstring、D36 決定 4-(4)
  「並行セッションの計測汚染防止」)。repo 全体の排他は意図されていない。home は全 node 共有の Lustre なので、旧既定は別 node の job
  まで 1 本に直列化していた。D2199 (2026-09-21) が B-5 試走で同じ症状を推定記録し、D2209 が B-5 分岐だけを job 固有 lock で対策した。
  2026-10-01 の A-2 R2 で、性能検証 3 本と bench 3 本が 1 列に並ぶ再発が起きた (依頼資料の実測報告: 待ち rr5 604/592 s・rr50 479/465 s・
  rr95 34/34 s、実消費 6.39 node 時間)。独立 2 例目なので、job body ごとの設定ではなく既定側を直す。
- `$TMPDIR` と `tempfile.gettempdir()` は job 固有で、pipeline と fan-out worker が書き換える。同じ node の別 job を排他しないので既定に使わない。
  `/scr` は login に無く job 終了で消える。
- flock は mtime を変えないので、長く使われなかった固定名は保持中でも `/tmp` の age 掃除 (login は tmpfiles 10 日) の対象になりうる。
  取得時の mtime 更新で、使用中の file が age で消える窓を open〜utime の間まで縮める。完全な防壁とは主張しない。
- 計算ノードの smoke (request 40909/40910.nqsv、bnode043 と bnode042) で次を観測した。
  - 別 node の既定 lock の保持区間は 5.0 秒重なり、両者が保持中に相手の取得を観測した
  - 各 node 内の 2 process は排他された
  - 共有 FS 上の対照 lock は別 node でも直列だった
  - `/tmp` は専用 mount を持たず、ローカル NVMe 上の xfs root FS だった。自 uid 以外の entry が 12 件あり
    (generic dispatch の userns では 65534 に見える)、job 専用の空の tmpfs ではない
- 未確認として残すもの:
  - 同じ node の別 job が同じ file を見ること (mount 情報からの推論)
  - job 終了後の lock file の残存
  - 実 bench の WAL 時刻での並行化 (次の A-2 実走で確認する)
  - 約 3.3 node 時間という効果 (依頼資料の未実測試算。wall 効果も未確認)

**却下した選択肢:**
- fan-out worker も node 共通の既定 lock にする。2 job の node 集合が交差すると、job A の head が X を保持して Y の worker を待ち、
  job B の head が Y を保持して X の worker を待つデッドロックになる (head は rep0 と兄弟待ちを bench_lock 内で行う)。
  現行の「競合を検出したら verify-competing-tenant で拒否」を維持する。
- `O_NOFOLLOW` を全取得に足す。明示 override の受理集合を変える。脅威 (他 user の symlink 先置き) の帰結は可用性側で、計測汚染ではない。
- A-2 を workload × cell の別 job に割る。現行は workload ごとに 1 job で、2 cell が campaign・WAL・claim を共有する契約である
  (`paper_story_a2_certification.py` の `len(cells) != 2` ほか)。rr95 は 1 rep 約 7.7 分で、cell 単位でも 5 分目安に届かない。
  correctness を cell 別 job、性能を pair job に分ける案は契約変更を伴うので backlog とする。
- job body ごとに `IZANAGI_BENCH_LOCK` を足す。未設定の job body は 32 本中 29 本ある (直下 19 本中 16 本、`probes/` 13 本中 13 本)。
  既定変更なら、bench_lock() に到達する経路すべてに 1 箇所の変更で効く。
