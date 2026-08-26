---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-26
wave: dev-wave-real-repo-chain
seq: 2
---

## {{D:real-repo-resource-rw-lock}}. 受入の real-repo 排他は資源別 reader/writer lock で行う

**決定:** 受入全走で `REAL_REPO_SERIAL_NODES` の 73 node を単一 xdist loadgroup へ閉じ込める
全対全排他をやめ、次の形へ置き換える。

- 73 node を access map (資源 x read/write) へ分類する。resource 71 / local-only 2、
  reader 67 / ccbench writer 4。
- 排他は `pytest_runtest_protocol` の wrapper で setup / call / teardown の全区間を囲う。
  **function fixture では module fixture の setup を守れない**ため、fixture 単独では成立しない。
- 資源は親 working tree と共有 ccbench の 2 本。取得順は常に前者から後者で固定し deadlock を作らない。
  reader は共有ロック、writer は排他ロック。
- lock file の path は repo root の realpath から決定的に導出する。session 固有の値を混ぜない。
  **保証の射程は同一 host・同一 filesystem までであり、cross-host 排他は主張しない。**
- blocking な flock を使わず、有限 deadline の非 block 再試行にする。deadline は受入の 5 分上限から
  観測された最長 resource cohort を引いて決める。超過は資源・mode・保持者情報を添えて fail-closed で
  落とす。skip や続行にしない。
- resource node の access stamp が欠落・不一致なら、テスト本体に入る前に拒否する。
- `real-repo` marker と group 名は残し、collection の post-yield で最終 nodeid から
  `@real-repo` suffix だけを除いて xdist の work unit 化を解除する。
- process memo を使う node は suffix を保ち、単一 work unit・単一 process の 1 回払いを維持する。
- suffix 除去の**後**に所要降順の並べ替えを行う。順序が逆だと全 node を 1 unit として cost を計算する。
- 所要台帳の lookup は suffix 付きの歴史的 key も互換参照する。
- 共有 checkout guard は「registry にいる」ではなく ccbench=write を要求する。

**access map は「共有資源に触る node」の allowlist であり、map 外は資源に触らないと仮定する。**
これは置き換え前の `REAL_REPO_SERIAL_NODES` と同じ仮定であり、本決定は仮定を強めも弱めもしない。
「map 外の既定は writer」は主張しない — 実装すれば全 node が直列化して受入が壊れる。

**理由:**

- 鎖は所要台帳で 239.1 秒、前 wave の同一系列実測で 210.5 秒あり、shard-0 の pytest wall
  266.89 秒のほぼ全部を占めていた。鎖の 84% は 1 file の 21 node で、最長単体は 94.0 秒である。
- **一方でこの排他が守っている writer は 4 件・合計 0.19 秒しかない** (うち 3 件は slow 印で
  受入では実走しない)。残り 69 node はすべて reader であり、reader 同士は排他を必要としない。
  239 秒の直列化はほぼ全部が不要な待ちだった。
- 生死実験で、同じ 21 node を計算ノードで直列 145.79 秒 / 21 並列 54.83 秒と測った。
  **結果集合は 21 passed, 2 skipped で完全に一致し、2.66 倍速い。**
  並列側は login node での反復 3 走を含め 4 走すべてで直列と同一の結果だった。
- D532 が認める 3 手のうち (a) 鎖の短縮と (b) 排他閉包の細分化に当たる。worker 数と配布順は
  同決定が実測で否定済みであり、本決定でも触れない。
- **鎖が縮むまで shard 数・worker 数・計算ノードへの分散は makespan を動かせない。**
  work / (48K) は約 77.8 秒であり、鎖 210.5 秒がその上にある間はどの並列化も鎖に隠れる。
  本決定の値打ちは「鎖を仕事量の下へ落として、初めて並列化が効く領域へ入れる」ことにある。

**却下した選択肢:**

- **loadgroup を reader / writer の 2 group に割る** — xdist の group は互いに並行実行されるため、
  group 内の直列化しか表現できず reader と writer の相互排他にならない。
  両者へ同じ group を付ければ現状へ戻る。
- **function fixture だけで flock を取る** — function fixture は module fixture より後に setup される。
  実 repo を読む module fixture の構築が lock の外に出る。
- **worker 間で構築済み snapshot を共有する cache を作る** — 利得に寄与しないことを実測で確認した。
  並列実測 54.83 秒は cache 無し (各 worker が自分で fixture を構築) で得た値であり、
  内訳も「単独 fixture setup 11.80 秒 + 最長 call 43.22 秒 = 55.02 秒」と一致する。
  **構築費は並列に払われて累積しない。** 一方 cache は共有可変 tree という新しい競合面を作り、
  reader が `git status` 経由で index refresh lock を踏む経路と、
  排他ロック下で検証待ちが直列化する経路を生む。規律 5 に従い作らない。
- **散らし先を 2 lane に制限する** — loadgroup で表現すると別 shard component になりうる。
  同 shard 内に留める機構は `tools/acceptance_shards.py` を触らずに作れない。
- **custom scheduler** — D390 / D393 が実効 scheduler を exact 型へ束縛し受入 receipt が照合する。
- **テストの削除・skip・selection の縮小** — D747 と規律 2 に反する。検討対象にしない。

## {{D:mutation-source-repo-independent-clone}}. 変異 harness の `--source-repo` には独立 clone を渡す

**決定:** `tools/mutation_worktree.py` の `--source-repo` には、稼働中の wave worktree ではなく
**その wave の commit を `main` に固定した独立 clone** を渡す。

**理由:**

- 同 wrapper は source と main の共有木について、走行の前後で `status` と `submodule-status` の
  stdout bytes が不変であることを検査する。
- **local main は他 wave の land で頻繁に進む。** 本 wave の変異走行中、実測で main が
  25 commit 進み (`df7f0905` → `1310af2f`)、事後検査が
  `共有木の観測 bytes が変化した` で赤になった。**本 wave の変更とは無関係な赤である。**
- 再試行しても main の churn は続くので再発する。独立 clone を渡せば観測対象は誰も触らない木になり、
  この赤を構造的に断てる。`git clone --local --no-checkout` は実測 6.6 秒で、
  wave branch の fetch と submodule の再帰初期化を含めても安い。

**却下した選択肢:**

- **稼働中の worktree をそのまま渡して再試行する** — main の churn は止められないので、
  混雑した時間帯ほど落ちる。所要の長い変異ほど当たりやすい。
- **事後検査を緩める** — この検査は「変異が共有木を汚していない」ことの保証であり、
  緩めれば変異が主 tree を壊しても気づけない。
