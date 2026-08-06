---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-06
wave: dev-wave-t300-login-headroom
seq: 1
title: [T-300] ログインノードの空きメモリとキュー可用性で実行場所を決めるようにした — 汎用 launcher は敵対レビューで取り下げ、上限付き実行を entry point の内側に閉じた (コード + docs、受入 6987 passed 時点の赤 2 件を閉じて再走、変異 16/16 KILLED、branch worktree-dev-wave-t300-login-headroom)
---

## 本文

**ユーザー裁定 (2026-08-06)。** 「性能測定以外のコンパイル・コマンド・ツール実行は、余裕があれば
ログインノードで行う。`memwatch.sh` で合計メモリ使用量が分かる。16GB で OOM kill されるので
14GB までは使ってよい。特定コマンドのメモリ使用量を推定して OOM しそうなら計算ノードへ投げる。」
これは runbook §7.0 が「未実装であり裁定待ち」と記録していた headroom admission gate ([T-300]) の
値裁定であり、詳細は {{D:login-headroom-admission}}。

**追加のユーザー助言 2 件を wave 中に取り込んだ。** (a)「`qstat` で `gen_S` がインアクティブなら
投げても受理されない。そういう時もログインノードで仕事すべき。性能測定できないなら
『今はできない状況』と理解できるべき」→ キュー可用性を判定の 2 次元目にした。
(b)「並行セッションの数も確認すべき。5 セッションが同時に 4GB 使ったら OOM」→ 親は当初
「予備枠 = セッション数 × 1GiB」を提案したが、ユーザーが「10 セッションで開発するので予備だけで
16GB になる」と棄却。**この是正が正しい** — 各セッションの使用量は既に `memory.current` に
含まれており二重計上だった。予備枠は固定 2 GiB のまま。

**段 3 の敵対レンズ 2 本が段 2 プランを設計ごと否定した。** プランは任意 argv を受け取る
`tools/pegasus/local_run.py` を提案したが、両レンズが独立に blocker を積み上げ、親は
**汎用 launcher を取り下げて上限付き実行を entry point の内側へ閉じる**方針へ差し替えた
({{D:no-arbitrary-argv-bounded-launcher}})。レンズ A の初回は上流の安全分類器に拒否されて
rc=1 で出力ゼロになり、防御レビュー寄りに書き直して成立させた。

**段 5 の実装子 2 本が「裁定と既存テストが矛盾する」として契約どおり fail-closed で停止した。**
親が一次資料を読み、**どちらも既存 assert を 1 文字も変えずに解ける**ことを確認して裁定を
差し替えた。(a) site 判定の穴は `classify_site` ではなく `_has_nqsv` 側にあり、PATH 非依存 marker
(`/opt/nec/nqsv`) を証拠に足せば既存テストは無傷。(b) gate 順序は「LOCAL のときだけ preflight より
前へ出し、DISPATCH は従来順序を保つ」で既存の変異 anchor テストが緑のまま通る。

**親の実機実測が設計の生死を決めた。** `--user` scope の `MemoryMax` は実際に強制され
(cap 64 MiB で 256 MiB 確保 → その scope だけ SIGKILL、slice は無傷)、親から `oom_kill` を観測でき、
scope 生成は 5〜6 ms。一方 `MemoryOOMGroup` は systemd 249 では transient property として受理されず
(`Unknown assignment`)、child が自分で `memory.oom.group` を書く形へ差し替えた。
scope は最後のプロセス終了で消えるため、終了後に `memory.events` を読む設計も走行中 sampling へ
差し替えた。いずれも実装後に親が実機で捕まえた欠陥である。

**段 6 のレビュー 2 本 (両者 NO-GO) から採用 8 件・返す 5 件・反証 1 件を裁定した。** 最も重いのは
「bounded local の pytest から legacy build cache 経由で計測 producer へ到達し、ログインノードの
throughput が COMMIT され得る」で、**本 wave が新たに開いた面**かつ絶対規律 1 に触れるため
計測 producer 側の site 検査で塞いだ。反証したのは「祖先 cgroup の `memory.max=max` を無制限として
扱うのは fail-closed と逆」で、これは cgroup v2 の正しい意味論であり、自 slice の有限性は別途
要求されている。

**変異 matrix は 4 回走らせた。** 1〜2 回目 (local mode) は runner (`run_tests.py`) が変異対象の
admission コードを自分で使う自己参照のため成立せず、その過程で {{F:clean-tree-precondition-kills-normal-work}}
を実測で掘り当てた。3 回目 (dispatch mode) は {{F:new-behavior-broke-existing-tool-contract}} で
baseline から停止。`--force-dispatch` を足して 4 回目で 16 件中 15 件 KILLED、
M18 のみ期待 node の過小登録による MISMATCH (期待 5 件すべてが赤 + 同族 2 件も赤) だったため
実測へ揃えた v2 spec で再照準し KILLED。初回 ledger は erratum として保存した。

**セッション運用の失敗。** 修正子 3 本を投入した後に完了待ちを張り忘れ、**2 時間空転**した。
以後は投入と待ち受けを必ず対にする。また変異走行中に docs を編集し、harness を止める前に自分で
復元した (規律違反)。

**依頼の未達部分。** 「コンパイル」はまだログインノードへ移っていない。`g++-12` / `cmake` / `make` は
ログインノードに実在するので技術的には可能だが、計測 build cache への流入を断つ namespace 分離が
前提であり独立した作業になる。[T-300] の本丸である「AI の子プロセス自身に予約を取らせる」も
未接続で、予約 API だけ用意した。

## 次の一手差分

### 更新

- [T-300] **P2・更新**: ログイン側の headroom admission gate は本 wave で実装・受入・変異まで
  完了した ({{D:login-headroom-admission}})。**残るのは本丸の「予約を取らないプロセス」への接続**で、
  spawn 地点は `tools/codex_worker_launch.py` と `tools/dev_waves/worker.py`。予約 API
  (`login_headroom` の lease / scope 束縛) は用意済みなので、次 wave は接続とテストだけになる。
  実測では Claude 系 22 本が 1 本あたり 240〜390 MB で並走しており、runbook §7.0 が記録した
  OOM 主経路そのものである。
  base: 65ebeb5f7c9bfeccb1b7bf33e3bc22832a93b0ace31d19bac62312b1eddf0e2c

### 新規

- {{T:login-build-namespace}} **P2・新規**: ログインノードでの build 解禁。`g++-12` / `cmake` /
  `make` はログインノードに実在するので技術的には可能だが、**計測用 build cache への流入を
  構造的に断つ namespace 分離が前提**である。legacy `build-variants` cache は site / contract
  identity を持たないため、cache hit が計測 producer の site gate を迂回する経路が残る
  (本 wave は producer 側検査で塞いだが、build 自体は解禁していない)。ユーザー依頼のうち
  「コンパイル」の部分がここで未達である。
- {{T:reclaim-credit-ruling}} **P3・新規**: 判定量から reclaim 可能な file cache を差し引くか。
  本 wave は raw `memory.current` を使う裁定にしたが、実測では file 分が 4.35 GiB あり、
  差し引けば実効許容量がほぼ倍になる。差し引きには `unevictable` / `memory.min|low` 保護 /
  dirty / writeback の扱いと、圧力下での実回収量の実測が要る。
- {{T:four-outcome-ledger}} **P3・新規**: local 完了 / cap 到達 / 余裕不足 / dispatcher 失敗の
  4 値を task_run と PBS receipt へ別値で永続化する。現在は判定ロジックだけが 4 値を持ち、
  台帳と process rc では潰れているため、事後にどの経路で緑になったか復元できない。
- {{T:scope-escape-containment}} **P3・新規**: bounded scope から user systemd / D-Bus 経由で
  sibling unit を作れば cap の外へ逃げられる。任意 argv launcher を作らない設計にしたため
  現実的射程は小さいが構造的には残る。閉じるには実行 sandbox が要る。
