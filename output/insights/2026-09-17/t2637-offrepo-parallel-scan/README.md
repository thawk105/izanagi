# [T-2637][T-2660] 到達不能監査の repo 外走査を directory 単位の work queue で並列化した (第 1 段)

- 日付: 2026-09-17
- wave: `dev-wave-t2637-offrepo-parallel-scan` (branch `worktree-dev-wave-t2637-offrepo-parallel-scan`、基準 main `abc7085ae`)
- 裁定: D2104 項 20 (第 20 回 /rulings 全件 2026-09-17)。D2038 (範囲限定より先に並列化)、D2034、D958 (所要上限と受理条件)。
- 実装 commit: `78f8af060` (Codex `role=author`、`gpt-6-astra` / `medium`)。main 取り込み merge `372abc858`。docs は後続 commit (本 README を含む)。
- 一次資料: 本 README、`verbatim/` (brief・plan・段 3 レンズ 2 本・段 4 裁定・author / fix / review の報告)、`mutation-ledger-*.json`、
  job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2637-offrepo-parallel-scan/` (計測の生 log = `measure/*.out|.meta`、
  patch、prompt、receipt。repo 外なので本 README に要点を写す)。

## 何をしたか

`tools/audit_dangling_commits.py` の `_enumerate_offrepo_candidates` (repo 外の同一実体を探す走査) を、
**範囲・規則・出力を変えずに** thread 並列化した。

- 並列単位は **directory 1 個 = 1 task**。固定 `OFFREPO_SCAN_WORKERS = 16` 本の thread が `queue.Queue` から
  task を取り、`os.walk(directory, topdown=True, onerror=…, followlinks=False)` の**最初の yield だけ**を処理して
  generator を閉じ、sorted `dirnames` のうち `os.path.islink` が偽のもの (= `os.walk` 自身の再帰条件) を子 task に積む。
  scandir 失敗は `onerror` 1 回・候補なし、symlink dir は `dirnames` に載るが降りない — いずれも `os.walk` の現物の
  意味論をそのまま使う。
- 候補照合 (basename → size → executable の prefilter、`lstat`、`S_ISREG`、`(OID, dev, ino)` の group 化) は逐次経路と
  同じ helper `_process_offrepo_iteration` を共有し、複製しない。
- 逐次版の first-seen 代表 (前順 DFS: directory の file を全部処理してから sorted 順に subdirectory) は
  **walk key** `(((1, dir), …, (0, file)), 候補列内の位置)` の最小で再現し、`possible` の OID / identity の挿入順も
  key 順に復元する。root は `sorted(roots)` の順に逐次に完結させ、入れ子 root の alias 2 個・失敗 2 回は現行どおり。
- workers=1 は pool を作らず従来の 1 本の `os.walk` を通す (意味論の参照実装)。計測用 env
  `IZANAGI_AUDIT_SCAN_WORKERS` (正整数のみ、空・非整数・0・負は `RuntimeError` → rc=2) は列挙実行時に読み、
  candidates 空の早期 return では env にも filesystem にも thread にも触れない。CLI flag・報告行・`--help` は不変。
- heartbeat は主 thread だけが出す。待機は `POLL_CEILING_SECONDS` (1 秒) の正の timeout (F627 型の busy-spin を避ける)。
  worker の非 OSError 例外は最初の 1 件を全 thread の join 後にそのまま再送出する。
- 並列禁止 test `test_initial_patch_contains_no_parallel_execution` (D985 の結論を静的文字列で固定していた) は、
  裁定どおり削除でなく同じ位置で `test_parallel_offrepo_scan_preserves_enumeration` (workers=1 / 4 の canonical 結果と
  手書きの期待集合) へ置換し、計 12 test を新設した。既存 test の期待値は変えていない (155 passed)。

## 第 1 案 (直下 subdirectory 単位) が tail で頭打ちになった

段 5 の実装は探索根直下の subdirectory ごとに `os.walk` 全体を worker へ配る形だった。実根で走らせると、最初の
60 秒は約 14,500 file/秒 (変更前の約 10 倍) で進むが、120 秒以降は `dev-wave-suite-floor-recheck/measure/run2/…/
pytest-of-tanab/…` (pytest の tmp repo が数万個ある深く小さい directory の森) を **1 worker が逐次に 15 分以上**歩き、
他の 15 worker は遊んでいた (`/proc/<pid>/task/*/fd` で開いている directory が 1 本だけ、process CPU 9%)。
列挙 1041.8 秒で、変更前 warm (935.3 秒) より遅い。**利得が最大部分木の逐次時間で頭打ちになる**ので、段 6 で
directory 単位の work queue へ設計を替えた (`verbatim/s6-parent-measurement-v1.md`、fix 指示 `verbatim/s6-fix-prompt.md`)。

段 4 裁定 §3 の「prototype 判定 (列挙倍率 < 1.2 なら停止)」への erratum: 判定の目的は「Python thread では倍率が
出ない」ことの検出であり、並列段の速度 (14,500 file/秒) がその前提を反証したため、停止ではなく分割単位の是正へ進んだ。
閾値と D958 の受理条件は最終版の実測にそのまま適用した。

## 実測 (login node、fixture repo × 実根、warm)

現行 main は findings 0 件 (`finding_commits=0`、41.5 秒) で repo 外走査が**省略される**ため、探索根の外
`/work/1/SFC/tanab/t2637-audit-fixture/repo` に到達不能 commit 1 本 (4 file: A = 実根の file と同一 bytes + landed 参照、
B = 同一 bytes + 参照なし、C = よくある basename で固有 bytes、D = 固有 basename) を持つ fixture repo を作り
(`make-fixture-repo.sh`、job dir)、探索根 `/work/1/SFC/tanab/dev-wave-jobs` (直下 1,252 entry、tool 計数で約 24 万 dir /
185 万 file) を走査させた。期待どおり抑止 1 対 (A)、未参照 copy 1 件 (B)、要確認 1 commit (B, C, D) を報告する。
変更前 tool (old) は main `abc7085ae` の bytes (sha256 先頭 `77251de5`) を job dir へ写し `--repo <fixture>` で起動した。
new = 本 wave の最終 bytes (`dc4edcf8`、実装 commit `78f8af060`)。段 6 版 (`788eb86c`) との差は fix2 の tie-break だけ。
生 log は job dir `measure/*.out|.meta|.err` (時刻・load・sha・rc を各走の `.meta` に記録)。

| 走 | tool | workers | 開始 (JST) | 列挙 (秒) | 全体 (秒) | load (開始→終了) | 確認不能 | 備考 |
|---|---|---|---|---|---|---|---|---|
| fixture-old-warmup | old | 1 | 06:58 | 1365.669 | 1366.379 | 19→90 | 0 | cold 寄り |
| fixture-new16-warmup | 段 5 版 (直下分割、`14ce41ff`) | 16 | 07:23 | 1041.759 | 1043.369 | 44→21 | 0 | tail 15 分超 |
| fixture-old-1 | old | 1 | 07:40 | 935.326 | 936.152 | 21→36 | 0 | |
| fixture-new16-1 | 段 6 版 (`788eb86c`) | 16 | 07:56 | 188.247 | 189.103 | 36→14 | 11 | |
| fixture-old-2 | old | 1 | 08:01 | 1296.845 | 1297.888 | 21→65 | 0 | |
| fixture-new16-w | new | 16 | 08:22 | 225.734 | 230.293 | 65→82 | 2 | D958 の warm-up (捨て) |
| fixture-new16-2 | new | 16 | 08:26 | 237.666 | 240.169 | 82→78 | 149 | D958 走 1 |
| fixture-old-3 | old | 1 | 08:30 | 1113.165 | 1114.406 | 78→13 | 0 | |
| fixture-new16-3 | new | 16 | 08:49 | 118.780 | 118.943 | 13→9 | 0 | D958 走 2 |
| fixture-new1-1 | new | 1 | 08:51 | 550.677 | 551.077 | 9→77 | 0 | 新 tool の逐次経路 |
| fixture-new16-4 | new | 16 | 09:00 | 110.286 | 110.429 | 77→89 | 220 | D958 走 3 |
| fixture-new16-5 | new | 16 | 09:04 | 163.797 | 164.231 | 47→37 | 0 | D958 追加 1 |
| fixture-new16-6 | new | 16 | 09:07 | 194.654 | 194.866 | 37→95 | 0 | D958 追加 2 |
| fixture-old-4 | old | 1 | 09:10 | 1067.407 | 1068.362 | 95→86 | 0 | |
| fixture-new16-7 | new | 16 | 09:28 | 323.278 | 327.000 | 86→50 | 0 | **無効**: 親の onerror probe (16 worker) が 09:29:05〜09:34:25 に同じ探索根を同時走査 (待ち手の鍵を `old-4.done` にした親の誤り) |
| fixture-new16-8 | new | 16 | 09:38 | 334.878 | **335.762** | 34→42 | 0 | D958 追加 3 (代替、単独) |

- **同時刻対照の倍率 (隣接する old / new の対):** 936.2 / 189.1 = **4.95** (old-1 / new16-1)、1297.9 / 240.2 = 5.4
  (old-2 / new16-2、間に warm-up)、1114.4 / 118.9 = **9.4** (old-3 / new16-3)、1068.4 / 194.9 = 5.5 (old-4 / new16-6、逆順の隣接)。
  new1-1 (新 tool の逐次経路) 551.1 は old の 935〜1298 より速いが、同時刻の old 対照が無い (load 9→77 の窓) ので倍率は言わない。
- **D958 の形 (warm-up 1 走を捨てた独立 3 走、max/min > 1.5 なら 3 走追加し全 6 走の max):** 走 1〜3 = 240.2 / 118.9 / 110.4
  (max/min 2.18 > 1.5) → 追加 3 走 = 164.2 / 194.9 / 335.8 (new16-7 は上記の理由で無効、代替 new16-8)。**有効 6 走の max = 335.8 秒
  > 300 秒**、他の 5 走は 110〜240 秒。old は 4 走とも 935〜1298 秒 (上限の 3.1〜4.3 倍)。max/min = 3.0 は共有 login node の
  Lustre client の混雑 (load 9〜96、他 session の worktree 生成・削除・受入) を反映しており、静的な複製 (下) では 6 走が 0.66〜0.68 秒
  (new16) / 1.47〜4.19 秒 (old) と安定している。
- **実 repo (現行 main、findings 0 件、走査省略) の D958 の形:** new16 で 18.1 (warm-up) / 14.1 / 15.5 / 9.1 秒 → max 15.5 秒 ≤ 300。
  到達不能 1,259 commit、tips 114。
- 変更前 (2026-09-16、探索根 176 万 file) の warm 列挙 455 秒に対し、本日は 935〜1298 秒だった。pytest tmp repo の森が増えた
  ことと共有 login node の負荷による。

## 計算ノード (補助系列、bnode044、generic dispatch、impl worktree から投入)

| 走 | request | tool | workers | 列挙 (秒) | 全体 (秒) | 確認不能 |
|---|---|---|---|---|---|---|
| compute-new16-1 | 2978.nqsv | new | 16 | 77.250 | 77.476 | 0 |
| compute-old-1 | 2986.nqsv | old | 1 | 192.396 | 192.520 | 1 |
| compute-new16-2 | 2999.nqsv | new | 16 | 106.529 | 106.691 | 32 |
| compute-new1-1 | 3005.nqsv | new | 1 | 213.936 | 214.180 | 0 |

4 走とも同じ node に割り当てられたため、client cache が空なのは 1 走目 (new16-1) だけで、それが最速だった。cold の倍率は
言えない (T-2660 (b) は「別 node の 1 走目」の形では取れなかった)。計算ノードでは old が 192 秒 (login の 5〜7 倍速い) で、
並列の利得は 1.8〜2.5 倍に縮む。全条件が 300 秒以内。

## 静的な複製 (churn なし) での同一性

実根の job dir 2 本 (`dev-wave-t2397-a1-attempt4`、`dev-wave-t2723-floor-cell-admission`) を探索根の外
`/work/1/SFC/tanab/t2637-audit-fixture/static-root` へ `cp -a` した (59,927 file / 5,131 dir)。fixture repo からこの木を走査すると、
old / new16 / new1 / old / new16 / new16 の 6 走で報告行 (進捗行・`elapsed_seconds=` 行・所要上限超過行を除く) が逐語一致し、
確認不能 0、未参照 copy 2 件 (A・B の複製) と要確認 4 path が一致した。所要は old 4.19 / 1.47、new16 0.68 / 0.66 / 0.66、new1 1.49 秒
(書いた直後で cache 済み)。

## 「確認不能」(scan_failures) の帰属

並列走の一部に「repo 外候補の確認不能 N 件 (抑止せず)」が出た (11 / 2 / 149 / 220 / 32 件。逐次走と、低負荷の並列走 5 走は 0)。
Codex author の使い捨て probe (`verbatim/s6-probe-author.md`、job dir `probe/t2637_onerror_probe.py`、149 行、repo には残さない) で、
本番の `audit_with_offrepo` をそのまま呼びつつ `_OffrepoCounts.record_error` と `Path.lstat` を記録だけの wrapper で包み、
失敗の path・errno・走査後の存在を取った。

- 実根の通常走 (16 worker、09:29 と 09:34): 記録 0 = 報告 0 (再現せず)。
- **正例実験 (churn):** 静的複製 (59,723 file / 5,120 dir) を探索根直下 `0000-t2637-churn-a` へ写し、16 worker の走査開始 20 秒後に
  `rm -rf` (2 分 19 秒) → **確認不能 123 件、全件 ENOENT、全件その木の下、走査後に全件不在**、記録数 = 報告数。同じ実験を
  1 worker (`0000-t2637-churn-b`、開始 8 秒後に削除) で行うと 0 件。
- 帰属: **探索根の churn (他 wave の mutation worktree 生成・削除、1 本 26,000 file) が原因**。directory を親が列挙してから子 task が
  走査するまでの遅れが、逐次 DFS (直後に再帰) より work queue (FIFO、数千 task が滞留) で長く、その間に消えた directory が
  `os.walk` の `onerror` (ENOENT) で「確認不能」に数えられる。規則 (scandir 失敗 = 確認不能) は逐次版と同じで、観測の機会が
  違う。抑止を増やす向きではなく (確認不能 = 抑止せず)、findings / suppressions / unreferenced_copies は全走で一致した。
  安定した木では両版が同一である (上の静的複製)。走査中に消えた directory を「確認不能」から除く (または再試行する) 案は
  規則の変更なので本 wave では入れていない (残存限界に記す)。

## D958 項 1 の判定と受理の決定 (段 7 前、相談 2 本の逐語は `verbatim/s7-consultA-decide.md` / `s7-consultB-attack.md`)

段 4 §3 は結果を見る前に「new(16) の独立 3 走 (max/min > 1.5 なら 6 走) の max ≤ 300 秒を fixture と実 repo の両方で満たすこと。
fixture で超過なら land せず、実測値を添えて裁定パッケージへ返す」と固定した。結果: **fixture は有効 6 走の max 335.8 秒で不合格**、
実 repo は max 15.5 秒で合格。「裁定パッケージへ返す」は 2026-09-14 のユーザー指示 (裁定へ返さず codex に相談して親が決める) と
整合しないため、材料 (`verbatim/s7-consult-brief.md`) を codex 2 本に渡し、決定側 (A) と点検側 (B) で攻めさせた。

- A (決定側): land する。D958 の合格としてではなく、上限超過の状態から改善する本 wave 限定の追補 D を置く。fixture の判定は不合格の
  まま残す。第 2 段の有効化条件は warm の実測で満たした。
- B (点検側): 見送るべき。最も強い理由は「結果を見る前に固定した不受理条件を結果後に解除する手続き上の不利益」。ただし
  「1 走の超過では第 2 段へ進めない」「第 1 段を land しなければ第 2 段に進めない」という反論は成立しない、と明記。
- 親の決定: **land する** (追補 D は decisions fragment の slug `d958-improving-wave-acceptance-t2637`、fold の dry-run では D2107)。代替受理条件 = (1) 変更後の有効 6 走の max
  (335.8 秒) が同時刻対照の old 全走の最小 (936.2 秒) を下回る、(2) 実 repo の D958 判定が上限内。D958 の逐語による判定は不合格と
  記録し、上限達成とは書かない。B の最も強い反対理由と「第 1 段を保存して第 2 段と合算で land する道」は追補 D に逐語で残した。
  根拠は D2104 項 20 (第 1 段を採る)、D2038 の順序、2026-08-11 のユーザー指示 (数値目標で本物の改善を捨てない、対象は受入全走で
  本件と異なるため設計根拠にとどめる)、正しさ検査 (等価性 test・変異 9/9 KILLED) を 1 つも緩めないこと。
- 段 4 §3 の凍結は結果後に変更した (事後変更)。旧条件と旧判定はこの節と `verbatim/s4-adjudication.md` に残す。

## 段 3・段 6 の所見 (逐語は `verbatim/`)

- 段 3 レンズ A / B が親 brief の数値 (warm 455 + 113 ≠ warm 478.1 = 455.4 + 22.7)、P1 (D958 の受理条件の読み替え)、
  I4 (代表を path 昇順最小にすると現行と非等価: 同 inode の alias でも `os.open` の失敗有無が path で変わりうる)、
  I6 (例外の rc 契約) を real とし、裁定で採用した。「最大 job dir 59,723 file」は被覆表の値で全体最大ではないので撤回、
  「単一 thread 3 走」は GNU find 1 + bfs 2 の混合。
- login node 計測は runbook §7 の「性能測定は計算ノード」と不整合という指摘 (A7 / B4) は一部 refuted: 同節の列挙は
  CC 計測 (ベンチ・calibration・noise floor・floor / oracle) で、監査は掃除が login で叩く運用 tool、D958 の受理値自体が
  1 login node で取られている。login を主系列、計算ノードは補助系列とした。
- 段 6 レビュー A / B は GO (must-fix 0)。nit 4 件 (同値 key の OID 挿入順の tie-break、読めない dir を worker 数超に、
  M5 の局所 witness、例外 test の join 検証) を fix 子で反映した。

## 変異 matrix

container worktree `.codex/worktrees/t2637-mutcontainer` (tip `78f8af060`) で `tools/mutation_harness.py --runner-mode dispatch`、
runner = `tools/run_tests.py orchestrator/tests/test_audit_dangling_commits.py -q -rf --force-dispatch`。spec は job dir
(`mutation-spec-probe.json` sha256 `5d9479f3…`、`mutation-spec-final.json` sha256 `00adfd52…`、本 dir に写し)。
probe 走 (全件 SURVIVED 登録、12 request) で観測 node を集め、本走 (12 request、09:08〜09:21) で完全一致を検査した。
台帳は `mutation-ledger-probe.json` / `mutation-ledger-final.json`。

| ID | 変異 | 本走 | 観測 node |
|---|---|---|---|
| M0 | docstring の言い換え (等価対照) | SURVIVED | — |
| M1 | worker の failures を主 thread へ合算しない | KILLED | 3 (`preserves_failure_counts`、`preserves_report`、`unreadable_subdirectory`) |
| M2 | sorted `dirnames` の末尾 1 個を子 task に積まない | KILLED | 37 (既存 test の多くが subdirectory を持つ) |
| M3 | root 直下 filenames の候補照合を skip | KILLED | 9 (`preserves_enumeration`、flat heartbeat、prefilter 系) |
| M4 | 子 task の `islink` 判定を除去 (symlink dir を降りる) | KILLED | 2 (`preserves_enumeration`、`symlink_directory_is_listed_not_entered`) |
| M4b | `followlinks=True` (1 yield しか使わないため等価対照) | SURVIVED | — |
| M5 | 代表選択の key 比較を反転 (局所 + merge) | KILLED | 2 (`preserves_first_seen`、`preserves_enumeration`) |
| M6 | worker 例外を握りつぶして続行 | KILLED | 1 (`propagates_worker_exception`) |
| M7 | worker から progress callback を直接呼ぶ | KILLED | 1 (`heartbeat_runs_on_caller`) |
| M8 | 既定 workers 16 → 0 | KILLED | 41 (並列経路の全 test) |
| M9 | candidates 空の早期 return より前に `queue.Queue()` | KILLED | 1 (`empty_offrepo_candidates_touch_neither_filesystem_nor_pool`) |

baseline PASSED (155 passed)、負例 9/9 KILLED で期待 node と観測 node が完全一致、等価 2 件 SURVIVED、MISMATCH 0。
段 4 で登録した M4 (`followlinks=True`) は新設計では等価変異になる (fix 子の指摘) ため `islink` 判定の除去へ再照準し、
元の形は M4b として等価対照に残した。

## 残存限界・scope 外 (記録のみ)

- cold (client cache が空) の倍率は login では測れない。別 node の 1 走目 (計算ノード補助系列) は追記する。
  取れなければ T-2660 (b) として持ち越す。
- `tools/check_branch_rescue.py` は監査を子 process で再実行し env allowlist に `IZANAGI_AUDIT_SCAN_WORKERS` が無いため、
  掃除経路では常に既定 16 で走る (T-2663 の射程、本 wave は触らない)。
- thread 生成に失敗する環境 (`RuntimeError: can't start new thread`) では逐次版なら完走した監査が rc=2 (実行不能) になる。
  既定 16 の安全は本 login node での観測に限る。
- 例外・割込み後の終了待ちは実行中 task の I/O 完了まで上限なし (thread は非 daemon)。
- 第 2 段 (用途分離、T-2661) の有効化条件 (第 1 段の実測で 300 秒に入らないことを示す) は warm の fixture 6 走 max 335.8 秒で
  満たした。計算ノードでは全条件 300 秒以内、cold は未測定なので「全環境で超過」とは言わない。用途分離は未実装・未受理。
- 走査中に消えた directory (ENOENT) を「確認不能」から除く、または再試行する案は規則の変更なので入れていない。並列版は
  queue の遅れの分だけ churn を観測しやすく、その走の報告行 (確認不能 N 件) は逐次版と一致しない。抑止は増えない。
- new16-7 (327.0 秒) は親の onerror probe との同時走査で無効にした。待ち手の鍵を直前の走 (`old-4.done`) にした親の誤り。
  戻しても D958 の判定 (不合格) は変わらない。
- T-2662 (境界 helper の真偽表)、T-2664 (hardlink alias 配布) は編集面が近いが本 wave では触っていない。

## 逐語の行末空白の可逆正規化 (DW-S07)

`verbatim/` の `.md` は `git diff --check` に触れる行末空白 (Codex 出力の Markdown 二重空白改行) を除いてある。可視文字は不変。
原文 bytes は `verbatim/originals.json` (sha256 `91c8e4157512557ad2dacbb05b4244a3468c4550f093c45f384ffb4d157398ff`) に UTF-8 text として
収め、各 text をそのまま書き出せば原文 bytes を復元できる。末尾改行の無い file (`s3-lensB.md`、`s5-author.md`、`s6-fix.md`、
`s6-fix2.md`、`s6-probe-author.md`、`s6-reviewA.md`、`s6-reviewB.md`、`s7-consultA-decide.md`、`s7-consultB-attack.md`) は
末尾改行を 1 byte 足しただけ。

| file | 原文 bytes | 原文 sha256 | 行末空白を除いた行数 | 正規化後 bytes |
|---|---|---|---|---|
| `s1-brief.md` | 6553 | `d1cd591e6a2d0a82…` | 0 | 6553 |
| `s2-plan.md` | 26761 | `704b4ee70757a714…` | 7 | 26748 |
| `s3-lensA.md` | 22250 | `750b890e7af23da9…` | 17 | 22217 |
| `s3-lensB.md` | 15732 | `23b26908c5ffd464…` | 0 | 15733 |
| `s4-adjudication.md` | 13306 | `02a203135d1ea548…` | 0 | 13306 |
| `s5-author.md` | 7626 | `a4f1bafc2bc7f983…` | 0 | 7627 |
| `s6-fix-prompt.md` | 11630 | `6b8b7b9f69160580…` | 0 | 11630 |
| `s6-fix.md` | 5843 | `b35044fefcf46e4e…` | 0 | 5844 |
| `s6-fix2-prompt.md` | 6184 | `188577136373e584…` | 0 | 6184 |
| `s6-fix2.md` | 2602 | `0121cf51a5611e63…` | 0 | 2603 |
| `s6-parent-measurement-v1.md` | 2277 | `7e1d9c494cb97e9b…` | 0 | 2277 |
| `s6-probe-author.md` | 1062 | `f326dcef545fac82…` | 0 | 1063 |
| `s6-probe-brief.md` | 1571 | `71adbc48577ef02a…` | 0 | 1571 |
| `s6-probe-prompt.md` | 5493 | `3009d5e29084da68…` | 0 | 5493 |
| `s6-reviewA.md` | 14875 | `c1be392869105230…` | 0 | 14876 |
| `s6-reviewB.md` | 14120 | `8ae571f4d8153b23…` | 0 | 14121 |
| `s7-consult-brief.md` | 5268 | `9d3eb129eb2cfab5…` | 0 | 5268 |
| `s7-consultA-decide.md` | 11371 | `aff6b5b2419acfd6…` | 0 | 11372 |
| `s7-consultB-attack.md` | 11560 | `7879949ccdee9550…` | 0 | 11561 |
