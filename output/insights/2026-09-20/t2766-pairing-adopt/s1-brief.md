# 段 1 brief — [T-2766] 受入 shard 内 pairing を既定 on にして main へ入れる採用 wave (dev-wave-t2766-pairing-adopt)

作成 2026-09-20 13:4x JST。着手時 local main `947fd160a` (= wave 木の HEAD、clean、submodule 511c9538)。job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2766-pairing-adopt/`。

## 研究前進 (1 行)

土台: 受入 1 走の最遅 shard の wall を 100 秒級 (前 wave 実測 101.7 / 112.9 / 144.3 秒、対率中央値 24.2 %) 縮め、全 dev-wave の受入待ち (合成ループを前に進める律速の 1 つ、T-2273 の 300 秒目標の途中) を短くする。完了判定 = 既定 on の実装が main に入り (land)、待ち手経由の実受入 3 対で効果が再確認されて記録されること。効果が消えていれば land せず記録だけ。

## scope と確定済みユーザー裁定 (D2172 項 1、択 (a)、2026-09-20)

- opt-in 実装 (branch `impl-t2766-pairing-optin`、`0eabe67ba`、code 4 file +373 −3) を**既定 on** にして main へ入れる。受理集合 (selected / hold / group / unit 境界、テストの合否) は不変、変わるのは順序だけ。
- 待ち手 (`tools/dev_wave_wait.py acceptance`) 経由の実受入で A = 採用前 main / B = 採用後 (= A + 採用 commit) の隣接対 3 組 (A,B / B,A / A,B) を測り、効果が消えていれば land しない。tip・条件差 (leader 数・load・他 wave の受入) を走ごとに記録し、「毎受入 100 秒」と一般化しない。
- A 側 witness (機序調査) は相乗り可だが採用を遅らせない。gate・台帳・一般化の追加は scope 外。
- scope 外 = e2e の分割、別系列への移動、新 slot / FIFO、300 秒目標の他の律速 (T-2786)、pairing の閾値・幅の変更。

## 着手前実測 (brief 前に前提を実測した結果)

- 4 file (`orchestrator/tests/conftest.py`、`tools/pegasus/dispatch_compute.py`、`orchestrator/tests/test_acceptance_schedule_order.py`、`orchestrator/tests/test_pegasus_dispatch_compute.py`) は main で `a99425b66` 以降無変更。impl branch の docs 3 本 (s1/s2/s4) は main と同一 → `0eabe67ba` の cherry-pick は code 4 file だけの差分になる (X1)。
- conftest / dispatch_compute の bytes を pin する凍結・oracle gate・proof chain は無い (`hold_inventory.py` は path 名の参照、`admission_registry.json` は class 分類のみ) → 条件 08/09/10 不成立。gate の新設は無い (env gate を撤去する) → 条件 13 不成立。file 削除なし → 11 不成立。
- 前 wave の A 走 `report.json` は `worker_occupancy` (worker 別 duration / items) と `session_timeline` はあるが item → worker の対応は無い。A 側 witness は A の code を変える (A ≠ 採用前 main になる) ので、本 wave では取らない ((P2))。
- 待ち手は claim 後に `HEAD..main` が非 0 なら `git merge --no-ff --no-commit main` を自動 commit する (merge message は self-report、両親で変わる実装面 path があるときだけ Codex author file が要る)。A/B の tip は走ごとに変わりうる → 走ごとに tested_main / tip を記録し、対内で main が動いたかを表に出す。
- 現況 13:4x: 受入 leader 1、門番 loop 1、load1 ≈ 10、pigz 0。

## 割れうる前提 (親の provisional 裁定・攻撃対象)

- (P1) property (`izanagi_acceptance_pairing_v1_{scope,rank,partner,worker}`、全 item) は**残す**。理由: 本番の毎受入に発火と実配布の witness が残り、既定 on の正例 test と変異 M5 の帰属がそのまま使える。費用は junit が shard あたり数百 KB 増えるだけ (前 wave §7)。env 定数 / token / `_acceptance_pairing_opted_in` / allowlist 行は撤去 (opt-out も足さない、D2172「付随する gate を足さない」)。
- (P2) A 側 witness は取らない (上記)。B 側 witness (property) は毎走の junit から検証する。
- (P3) 効果再確認の判定規則は前 wave の事前登録と同じ量 (最遅 shard の JUnit wall W_max、対差 ΔW、対率 r、3 種の中央値) を使い、**land 条件 = 有効 3 対すべて ΔW > 0 かつ med r ≥ 10 %** (前 wave の (i))。それ以外 ((ii) 閾値未満 / (iii) 符号混在・退行 / 反復不足) は land せず、記録と裁定パッケージだけを残す。閾値 10 % は D357 の 1 走比較の注記と同じ保守基準。
- (P4) A の測定木は wave 木とは別の worktree (branch `worktree-dev-wave-t2766-pairing-adopt-a`、main から) を待ち手で走らせる。A 木は land しない (受入 receipt は記録のみ)。B の最終走の receipt を land に使う。
- (P5) 軽量版: 段 2・3 は省く (設計択一は P1〜P4 で親が仮裁定、受理集合は不変、正しさ防壁に触れない)。段 5 = Codex author 1 本、段 6 = read-only レビュー 1 本 (test の弱体化・受理集合・変異帰属) + 必要時 fix 子 + 変異 matrix + 受入。

## 不変条件

- 受理集合 (selected / hold / group / unit 境界・marker・既存 property・identity) は不変。順序と追加 property だけが変わる。
- 未設定 env で pairing が発火する (既定 on)。unit < 96 は無変更・property 無し。cardinality 不成立は `UsageError` (fail-closed のまま)。
- テストの弱体化で通さない: G6 / G8 / G10 / G12 の既存不変条件は保ち、pairing で観測順序が変わる箇所は同 fixture から独立に導いた paired 順を期待値に固定する (本番 helper から期待値を算出しない)。
- 測定中は自分の他 job を走らせない。判定規則は結果を見る前に固定 (本 brief §事前登録)。

## 変更面 (実アンカー、X1 = main + cherry-pick `0eabe67ba` の行番号)

| file | 位置 (X1) | 変更 |
|---|---|---|
| `orchestrator/tests/conftest.py` | `:1022-1026` 定数 4 つ | `_ACCEPTANCE_PAIRING_ENV` / `_ACCEPTANCE_PAIRING_TOKEN` と「T-2766 measurement opt-in, off by default」comment を削除。`_ACCEPTANCE_PAIRING_PROPERTY_PREFIX` / `_ACCEPTANCE_PAIRING_HEAD_UNITS` は残す |
| 同 | `:1788-1797` `_acceptance_pairing_opted_in` | 関数ごと削除 |
| 同 | `:1883-1884` reorder 内の `if _acceptance_pairing_opted_in():` | 無条件に `_pair_initial_distribution_units` を呼ぶ |
| 同 | `:2348-2354` hook の分岐 | 常に `workerid=getattr(config, "workerinput", {}).get("workerid", "")` を渡す 1 呼び出しに畳む |
| `tools/pegasus/dispatch_compute.py` | `:131-132` allowlist | key と comment を削除 (main と同一に戻す) |
| `orchestrator/tests/test_pegasus_dispatch_compute.py` | exact pin の 1 key と request 伝播 test 1 本 | main と同一に戻す |
| `orchestrator/tests/test_acceptance_schedule_order.py` | G12 (`:1764-2039` 付近、9 本) | autouse の env fixture・`_PAIRING_ENV`/`_PAIRING_TOKEN` 参照・off 負例・invalid token 負例を撤去。正例は既定 (env 無し) で発火することを固定。「既定 on の負例」= 旧 env を設定しても挙動が変わらない (env を読まない) 1 本に置換。cardinality 負例・短 queue・worker 数非依存・junit 到達・hold/selected/real-repo 保全 (enabled param を既定 1 本に)・配布反例は保つ |
| 同 | G6 `:720-` の `traced_reorder(collection, durations)` | hook が常に `workerid=` を渡すので署名を合わせる |
| 同 | G8 `:1169-1201` (101 unit、`index(unknown) == 96`) | pairing で 49〜96 位が変わるため、cost 順の不変条件 (unknown = 96 位 cost に同値、無 known は no-op) を pairing 前の順で検証する形へ書き直す (例: unit を 95 以下にして 96 窓の tie は台帳側で作る、または pre-pairing 順を seam で観測)。不変条件の意味を落とさない |
| 同 | G10 `:1347-` | 40 unit (< 96) なので順序は不変。署名・`workerinput` の有無で落ちる箇所だけ直す |

分割方針: 実装子 1 本 (workspace-write、unit worktree `.codex/worktrees/t2766-adopt-unit-impl`、X1 起点)。同時に集計器 `t2766_adopt_analyze.py` を unit worktree の `probe-t2766-adopt/` に書かせ、親が job dir へ退避 (repo へ入れない)。

## 成果物

- main への commit (親が統合、Codex author trailer): 既定 on の実装 + test。
- 一次資料 `output/insights/2026-09-20/t2766-pairing-adopt/README.md` (走表・対表・中央値・witness・tip / 条件差・判定・変異 matrix)、spool fragment (worklog / decisions)。
- job dir: `runs/<NN>-<A|B>/` (run.json、受入 log / receipt、session の 3 shard junit.xml / report.json の写し)、`analysis/`。

## 事前登録 (結果を見る前に固定、前 wave `s4-ruling.md` §事前登録を継承)

- 有効走: 待ち手 rc=0 (child-green)、3 shard の report.json 実在。B はさらに witness (property 被覆 100 %、rank 48〜95 = partner 集合、head の (cardinality, cost) 多重集合と partner の cost 多重集合が selected + 台帳からの再計算と一致) 通過。
- 有効対: 隣接 2 走 (A,B または B,A) が両方有効。順序 A,B / B,A / A,B。無効対は同順序で追加、測定走上限 10。3 対未満 → 「判定不能 (反復不足)」で land しない。
- 指標: shard j の W_j (JUnit testsuite time)、O_j (report.json worker_occupancy 最大 duration)、F_j = W_j − O_j、W_max = max_j W_j。ΔW_k = W_max(A_k) − W_max(B_k)、r_k = ΔW_k / W_max(A_k)。集計は med ΔW、med r、条件別中央値差の 3 つを併記。
- 判定: (i) 全対 ΔW_k > 0 かつ med r_k ≥ 10 % → land。(ii) 全対 ΔW_k > 0 かつ med r_k < 10 % → land しない (閾値未満)。(iii) それ以外 → land しない (効果未確立、副分類: 符号混在 / 退行)。3/3 は有意差判定ではない。
- 条件差の記録: 走ごとに tested_main、tip、投入時刻、完了時刻、投入時の他 wave leader 数、load1、対内で main が動いたか。効果は「この tip・この夜の regime」の観測として書く。
- 赤: 全件本文を残す。B 固有で再現する赤は実装問題として fix。F945 型でも本文で判定。
- 変異 (段 4 で確定): M1 partner sort key 昇順 → 降順、M2 head 幅 48 → 47、M3' pairing 呼び出しを削除 (常に off)、M4 cardinality 検算削除、M5 property 付与削除。各 1 理由・単独適用・baseline 緑先行。
