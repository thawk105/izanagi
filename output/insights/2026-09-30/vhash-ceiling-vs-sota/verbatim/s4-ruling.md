# 段 4 裁定 — dev-wave-vhash-ceiling-vs-sota (md_42、T-2962)

裁定者: 親 (Claude)。2026-09-30 22:3x JST。起点を local main 908741c6f へ ff-only で進めた後 (md_37 hot v2 の着地を含む)。
入力: `s1-brief.md`、`codex/s2-plan.md` (check rc=0)、`codex/s3-a.md` (正しさ・整合、NO-GO)、`codex/s3-b.md` (過剰・削除、条件付き GO)、`codex/s3-parent-addenda.md`。
裁定 inbox の再走査: 開始後の決定は D2330・D2331。D2330 は T-2962 (d) の「ユーザー確認待ち」が D2322 項 2 で決着済みと明記 (本 wave は修正入り R と stock S を並べる)。D2331 は hot v2 (B-post) の設計。どちらも本 wave を止めない。

## 0. 新しい事実 (段 3 の後に親が実測)

- **md_37 (hot v2 = B-post) が main に着地した** (2991b1c2b、e0c081727)。依頼の「着地していれば使う」に従い、hot v2 の K=1・K=8 を腕に入れる。hot v2 = `patches/cicada-vhash-hot-block-variant.patch` + `patches/cicada-vhash-hot-block-post.patch` (新 macro なし、`CICADA_VHASH_K` は compile 時)。
- git apply (1 patch ずつ、fuzz なし) で当たる: pin→ro-gcflag variant→hot variant→post、pin→trace→ro-gcflag variant→hot variant→post、pin→trace→V→区間 GC、pin→trace→V→前進 C。
- 当たらない: pin→`instr-cicada-version-lifetime.patch`→V→hot variant (transaction.cc の文脈衝突)。→ VLIFE 計器は S と R の木でしか使えない。
- md_39 (E の修理) は main に無い → 待機型 2 点は欠測 (旧 E で代用しない)。

## 1. 所見の裁定

| 所見 | 判定 | 採否・処置 |
|---|---|---|
| A-1 / B-1 勝つ腕の選択が未定義 | real | 採用。M の腕を {R+hot v2 K=1、R+hot v2 K=8、R+C-min K=1} に固定。有望点・代表の腕の選択と継続判定は M の腕だけで行い、**同じ M の腕**が代表点 ≥1.5 と隣接点 ≥1.3 を満たすときだけ「継続の材料」。S・R−LR・区間 GC は対照の別表 |
| B-2 C-min は長い読み手を前進させない | real (hot v2 着地で一部解消) | 採用。C-min は「通常更新 tx の前進」の限定的な腕と書く。E の修理が欠測なので、推奨は「今ある試作 (hot v2・C-min) から見た継続判断」に範囲を限る |
| A-5 / B-3 R−LR は上限でない | real | 採用。R−LR を「読み手除去の対照」(同じ binary、通常 worker 47 本のまま batch_th_num=0) として予備だけに置く。上限・不達の証明に使わない。1.2〜1.5 帯の「大きく伸ばせる残存費用」の判断材料の一つにする |
| A-2 / B-9 完了条件が 0 超に弱い | real | 採用。対ごとに batch_commits(腕)/batch_commits(R) を保存し、点 × 腕の中央値が **0.8 未満**なら、その点のその腕の勝ちは数えない (事前に固定)。P1〜P3 で batch_commits=0 の走行は失格 |
| A-3 trace 検査が恒真になりうる | real | 採用。trace build に各機構の計数 macro を同時に入れ (verify 用 build で perf ではない)、腕ごとの非空 witness を要求: 全腕 = batch worker の C 行 ≥1、R = ro-gcflag の flag 立て ≥1、hot = hot の hit ≥1、C-min = 前進成功 ≥1、区間 GC mode 1 = 剪定 ≥1。0 なら extime を 1→3 秒で 1 回だけ延ばし、なお 0 なら「未検証 (機構未行使)」とし、その腕の値は継続判定に使わない。壊し正例は 1 本: `broken-cicada-interval-gc-overprune.patch` を R+区間 GC の木に重ね batchR で走らせ、判定器が巡回を出すこと (出なければ正例不成立と書く。事前登録外に付け替えない) |
| A-4 C 行数と batch 完了数の同一視 | real | 採用。全 commit 数 = 全 C 行数、batch 完了数 = batch worker の thread ID の C 行数、の 2 つを別々に照合 |
| A-6 perf 分離を macro 名に依存 | real | 採用。perf build の compile command の -D 集合が腕ごとの期待集合と**完全一致**することを検査 (名前での拒否は補助)。新 macro の 0 で前処理が pin と一致することを smoke で確認。完了数の出力は計測窓 (runner の join と結果集計) の後であることを patch と test で確認 |
| A-7 対の成立と単独性 | real | 採用。raw に job ID・node・job 内の順序・run ID・開始時の同居 process 一覧 (`ps` の利用者と cmdline) を残し、同じ点・round・GC の対は同じ job・同じ node に限る。30 秒比較の run ID は予備と重複禁止 |
| A-8 / B-6 build 共有の provenance と 5 分枠 | real | 採用 (P5 は採る)。binary ごとの manifest (pin、patch 名と sha256 と順序、macro 集合、compile command の sha256、compiler の --version の sha256、binary の sha256) を build job が書き、計測 job は node local へ写した後に binary の sha256 と manifest を照合してから走らせる。build job は木ごとに分け、smoke の build 実時間で 1 job ≤ 約 5 分になるよう shard を決める |
| A-9 gate の owner と header | should → 採用 | condition gate の meaning (owner TU の前処理) で 0/1 を確かめる既存の経路を使う。header 側の分岐は owner TU (ycsb_cicada.cc) が include する範囲に置く |
| A-10 総和 pin の根拠 | should → 採用 | 実装子が完成 patch の実 site と総和の式から数え直す。定数だけを先に書き換えない |
| A-11 patch 適用の一般化 | real | 採用。smoke で全木 (perf・diag・trace) を実 build し、workload 行の出力を確かめてから投入 |
| A-12 隣接点を削ると判定不能 | real | 採用。隣接点を削った場合の継続基準は「判定不能」と固定。予算を超えそうなら削る前に land 調整役へ相談する (依頼元経由のユーザー委任) |
| A-13 推奨の範囲 | real | 採用。推奨は「R (md_11 の観測最良設定 + 修正) に対する研究継続の判断」と明記し、区間 GC の SOTA (lock なし実装) との未比較を独立の残課題として残す |
| B-4 区間 GC を 30 秒比較へ運ばない | real | 採用。区間 GC mode 1・3 は予備・診断・正しさ検査だけ (依頼の腕の列挙は満たす)。30 秒比較の腕は S・R・代表の M 腕・次点の M 腕の 4 本 |
| B-5 削り順 | 採用 (順序を修正) | 予算超過時は (1) S の非選択 GC 間隔の予備、(2) 区間 GC mode 3 の P1、(3) R−LR、(4) C-min の P3 の順に削る。隣接点・R・正しさ検査・M の代表腕は削らない (削る前に相談) |
| B-7 実装の縮小 | 部分採用 | subcommand は smoke / build / run / verify / aggregate の 5 個 (prelim・diag・compare は run の mode)。build・parse・verify は `vhash_ro_gc_publish.py` の構造を流用。作図器は小さく (比の点図 1 枚と完了比の表)、test は小さい fixture。条件 gate の閉包・perf/trace 分離・正しさ検査は削らない |
| B-8 撤退条件の版数の診断 | real (部分) | 採用。S・R は VLIFE 計器 (公開回数・境界年齢・論理生存版数) を診断 build で取る。M 腕は各機構の計数 (hot の hit・fallback、前進の試行・成功)、区間 GC は自前の計数 (公開・剪定・鎖)。M 腕の版数は計器が当たらず欠測と明記。撤退条件の「縮むのが境界年齢・版数だけ」は「throughput の比 <1.2 かつ機構は発火した」で判定し、機構が発火しなければ「未判定 (働かない負荷)」 |

## 2. plan v2 (s2-plan.md からの差分だけ)

- **点:** P1 (rr5・ro 0%・通常 47 + batchR 1・skew 0.6)、P2 (同 skew 0.9)、P3 (同 skew 0.97)、P4 (rr50・ro 指定 95%・通常 12・skew 0.9・長い tx なし)。record 100 万・値 4 B・通常 tx 10 操作・batchR 1,000 read。
- **腕 (予備):** P1〜P3 = S、R、R−LR、R+hot K=1、R+hot K=8、R+区間 GC mode 1、mode 3 (+ P2・P3 は R+C-min K=1)。P4 = S、R、R+hot K=1、R+hot K=8。
- **木と build:** S と R は pin→V→新 workload (S は RO_GCFLAG なし。md_22 が inert を確認した V の既定 0 経路)。hot = pin→V→hot variant→post→新 workload (K=1・K=8 で 2 binary)。C = pin→V→FWD→新 workload。区間 GC = pin→V→IGC→新 workload (mode は実行時)。診断 = S・R は pin→VLIFE→V→新 workload (当たるかは smoke で確認、当たらなければ S・R の版数は欠測)、hot は + `cicada-vhash-hot-block-count-v2.patch` と COUNT、C は FWD_COUNT、区間 GC は INTERVAL_COUNT。trace = 各木の先頭に trace patch と、witness 用の計数 macro。
- **GC 間隔:** 予備で全腕を 10・100 µs の両方で走らせ、点ごとに R の中央値 (3 round) が高い方を選ぶ (同値は 10 µs)。以後その点の全腕をその間隔で読む。
- **有望点と代表の腕:** P1〜P3 の各点で、M の各腕の予備の比 (選んだ GC 間隔、同じ round・node の対) の中央値を出し、完了比の中央値 ≥0.8 かつ正しさの witness が非空の腕だけを候補とする。最大の (点, 腕) を代表とする (同値は P2→P3→P1、腕は hot K=1→hot K=8→C-min)。隣接点は P2→P3、P1→P2、P3→P2。全敗でも P2 と最大の M 腕を代表として残す。P4 は別条件として報告し、M の腕の予備の比の中央値が 1.3 以上なら、30 秒比較に P4 と隣接の P4′ (skew 0.97) を加える (予算内なら。超えるなら相談)。
- **相手側の追加調整:** 代表点の予備で M の腕の比の中央値が 1.5 以上なら、30 秒比較の前に R を GC 間隔 {1, 10, 100, 1000} µs で 3 round ずつ走らせ、最良の間隔を R と全腕の 30 秒比較に使う。
- **30 秒比較:** 代表点と隣接点で、S・R・代表 M 腕・次点 M 腕の 4 腕 × 新しい 6 round × 30 秒。
- **job:** smoke 1 → build (木ごと、1 本 ≤約 5 分) → 予備 (点 × round、同じ job に両 GC 間隔と全腕、round ごとに順序を回転・逆順) + 診断 (点ごと) + verify (腕ごと) を同時投入 → 30 秒比較 (round ごと)。1 node 1 job、node local $TMPDIR、共有 repo に書かない。driver は投入前に各 job の直列条件数と見積り秒、全体の node 秒を出す。2 node 時間を超える見込みなら削り順 (§1 B-5) か land 調整役への相談。
- **完了数の出力:** batch worker の既存の per-thread commit 数を、計測窓の後に 1 行 (`IZANAGI_CICADA_CEILING_WORKLOAD_V1 {...}`) で出す。hot path に計数を足さない。

## 3. 変異の事前登録 (実装前、DW-M01)

実装後に位置と単一理由性を確かめ、成り立たなければ実効 gate へ再照準する (登録は消さず erratum)。期待は KILLED。
- M1: perf build の -D 集合の完全一致検査を外す → perf に COUNT が混ざった build を受理してしまう
- M2: 比の対を「同じ round・node」でなく点の全走の中央値どうしで作る
- M3: GC 間隔の選択に M 腕の値を使う (R だけを見ない)
- M4: 有望点の選択に S・区間 GC・R−LR を含める
- M5: 完了比 0.8 の下限を外す
- M6: trace の機構 witness の非空要求を外す (発火 0 の腕を「検査済み」にする)
- M7: 全 commit 数 = 全 C 行数の照合を、batch 完了数との照合にすり替える
- M8: manifest の照合を binary の sha256 だけにする (patch 順・macro の食い違いを受理)
- M9: round ごとの腕順の回転を外す (全 round 同順)
- M10: 隣接点が欠けても継続判定を出す (「判定不能」にしない)
- M11: 30 秒比較が予備の run ID を再利用しても受理する
- M12: 判定器 rc 3 を certified と表示する
