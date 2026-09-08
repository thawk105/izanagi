---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-08
wave: dev-wave-t2429-verify-fanout
seq: 1
---

## {{D:verify-fanout-transport-and-authority}}. 認証の正しさ検査は単一 multi-node request 内の ssh で分割し、遠隔結果の権威は head 生成の stdin secret による HMAC に置く

**決定:** D1763 が「真偽値を返す正しさ検査は分割してよい」と裁定し、未解決として残した「実行ファイルの
同一性」を次の形で解く。

1. **輸送は単一の multi-node request。** A-6 policy の `scheduler.nodes` を 5 にし、job body が
   `PBS_NODEFILE` から兄弟ノードがちょうど `nodes - 1` 台であることを要求して
   `run-workload --verify-fanout-hosts` へ渡す。head が performance-tag の rep 0 と legacy 検査と
   bench を持ち、兄弟ノードが rep 1 以降を ssh 経由で並列に走らせる。cell の順序 (stock →
   採用版) は変えない。
2. **実行ファイルは 1 回だけ建てて配る。** 兄弟ノードは共有 `/work` の durable cache から
   trace-enabled binary を読み、ノード内蔵 `/scr` へ同一 bytes で複製して実行する。建て直さない。
   複製の sha256 が `build_done.trace_bin_sha256` と一致しなければ実行しない。
3. **遠隔結果の権威は HMAC に置く。** head が task ごとに 32 byte の secret を生成し、
   task 文書にも argv にも環境変数にも載せず ssh の標準入力だけで worker へ渡す。worker は
   result の canonical bytes (task 識別子と結果全体) の HMAC を書き、head は取り込みの最初に
   照合する。公開情報の hash を再計算するだけの受領証は権威にしない。
4. **worker は実行 bytes を照合する。** pipeline と verifier を import する前に、head が task へ
   載せた campaign lock の enforcement source closure digest と自 checkout の実測値を照合する。
5. **source snapshot は head が運ぶ。** head が local で束縛した `CompiledProtocolSourceSnapshot` を
   task へ直列化して渡し、worker は head 側の一時 worktree にある patched source tree を読まない。
6. **遠隔経路は campaign WAL sink と `BACKOFF_REPRO` generator の組だけ。** それ以外は task を
   作らず既存の local 経路で全 repetition を走らせる。
7. **欠落・不一致・ssh 非 0・`/scr` 不可は `verify-remote-unavailable` (indeterminate)。** pass に
   化ける経路を作らない。判定・reps・records・threads・extime は変えない (規律 2・規律 4)。

**理由:**

- 実測で 4 本の生死確認がすべて肯定だった。(i) A-6 が bnode031 で建てた 4 本の実行ファイルは、
  別ノード bnode012 で原本・`/work` 複製・`/scr` 複製とも sha256 が記録値と一致し、trace 版は
  rc=0 で trace を出し、perf 版は rc=0 で trace を出さなかった。動的依存は OS 標準ライブラリだけで、
  消滅した `/scr` を指す RUNPATH は解決対象を持たない。(ii) `-b 2` の要求で `PBS_NODEFILE` に
  両ノードが並び、head から兄弟へ BatchMode の ssh が通った。(iii) CLI の `-b` は job script 内の
  `#PBS -b` に優先する。(iv) 1 ノード要求でも `PBS_NODEFILE` は実在し自ノード 1 行なので、
  `nodes=1` の A-2 でも同じ nodefile 契約が成立する。
- 遠隔の verifier capability は発行 process に束縛されており、そのままでは COMMIT へ渡せない。
  一方、公開情報の hash だけを再計算する受領証は、task を読める同 uid の process が偽造できる。
  head しか知らない使い捨ての secret を輸送路だけで渡す形が、機構を増やさずに権威を作る最小の手段
  である。
- `scheduler` は `_protocol_preimage` に含まれないので、policy bytes の sha256 は変わるが
  `protocol_sha256` は変わらない。

**却下した選択肢:**

- **再現可能ビルド** — path 非依存化を 2 巡実装しても差分が 149 → 56 → 45,454 bytes と収束しなかった
  実測がある (2026-08-31 の B-10 正式走)。
- **login 側の supervisor が repetition ごとに別 request を投げる形** — cell ごとに queue 待ちが
  乗り、短縮幅を保証できない。ssh が使えることは実測で確かめたので、この案を採る理由が消えた。
- **計算ノードから qsub する形** — job body に `qsub` の文字列を書けない既存契約に反する。
- **policy へ `verify_fanout` object を新設する** — 既存の `scheduler.nodes` だけで切り替えられる。
  受理面を増やさない。
- **worker の host と boot id を認証の gate にする** — ノードが違うことは正しさの真偽値を変えない。
  gate 化すると正しい結果を性能上の理由で拒否する。
- **worker と contract loader を head 供給の二段 bootstrap で起動する** — 下の限界に書くとおり、
  閉じる対象が single-tenancy 前提の外にある脅威であり、新機構の追加になる。

**限界 (主張せず明記する):**

- worker と contract loader は自分自身を使って自分の checkout を検査する。head の照合後・worker の
  import 前の窓に同じ uid の別 process が共有 checkout を書き換えれば、この照合は迂回できる。
  複製済み実行ファイルの hash 後 TOCTOU と同族の限界であり、単独テナントの前提の外にある。
- 実機の 5 ノード実走はまだ行っていない。73 分から 16 分から 18 分へという見込みは、
  検査 1 回あたり約 425 秒という 1 attempt の実測からの静的な見積りである。
- 生死確認の実走は legacy 構成 (4 スレッド・200 tuple・1 秒) であり、48 スレッド・100 万レコードの
  full-scale trace と検査を別ノードで完走させた実測ではない。
- 「ノードを跨いで建て直すと bytes が変わる」という既存の言い切りは、一次資料では「別 job で
  建て直すと job 固有の path が混入して bytes が変わる」であり、2 台の計算ノードで建て直して
  sha256 を突き合わせた記録はない。本決定はその含意に依拠せず、配る形を採ることで問題自体を
  回避している。

**研究状態への影響:** A-6 policy bytes の sha256 は変わるが `protocol_sha256` は不変。過去の
certification・受領証・README は書き換えない。変更後の新しい attempt だけが本決定の対象である。
判定・実験規模・trace と perf の分離は変えていない。
