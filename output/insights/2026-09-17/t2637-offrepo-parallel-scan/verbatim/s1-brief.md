# 段 1 brief — [T-2637][T-2660] 到達不能監査の repo 外走査の並列化 (第 1 段)

作成: 2026-09-17 06:50 JST、基準 main `abc7085ae`、branch `worktree-dev-wave-t2637-offrepo-parallel-scan`。

## 研究前進 (土台)

`/cleanup-branches` §1 必須の到達不能監査 `tools/audit_dangling_commits.py` が、repo 外走査
(`_enumerate_offrepo_candidates`、探索根 1,761,075 file) の warm 455 秒 + 走査以外 113 秒で
所要上限 300 秒 (D958、tool 内定数) を超え、掃除が `checker-timeout` で止まっている (entry 1521)。
最小差分は走査段の thread pool 化であり、範囲・規則・出力を変えない定数削減 (D2034 → D2038)。
完了判定: (a) 等価性 test 緑 + 並列経路の発火証拠、(b) 実根で workers=1 と workers=N の
findings / suppressions / unreferenced_copies / rc が逐語一致、(c) D958 の形 (warm-up 1 走を捨てた
独立 3 走、max/min > 1.5 なら 3 走追加) の warm 実測と倍率の報告。

## scope

- 実装面 (Codex `role=author`、D95): `tools/audit_dangling_commits.py` の `_enumerate_offrepo_candidates`
  (並列度は module 定数 1 個 + 計測用 env var、CLI flag は足さない)、
  `orchestrator/tests/test_audit_dangling_commits.py` の
  `test_initial_patch_contains_no_parallel_execution` を「並列化しても範囲・規則・出力が不変」の検査へ置換
  (削除でなく置換、裁定項 20)。既存 test の pin (`repo 外走査 heartbeat directories=1 files=1`、
  `os.walk must not run without candidate basenames`) は維持。
- docs (親): insight README、spool fragment (worklog / decisions)、変異 matrix 台帳。
- scope 外: 第 2 段 (用途分離、T-2661)、T-2662 (境界 helper)、T-2663 (`check_branch_rescue.py` の二重走査)、
  T-2664 (hardlink alias 配布)、gate・台帳・一般化の追加、`check_branch_rescue.py` と cleanup command の変更、
  cold 計測の制度化。

## 確定済みユーザー裁定

- 第 20 回 /rulings 項 20 (commit `ad12ba35b`、branch `worktree-rulings-all-20260917`、**main 未着地・D 番号未採番**、
  記録時に main で確認): 第 1 段を採る。D985 の並列化却下の射程は D2038 で「Python 実装に固定した場合」へ限定済み。
  並列禁止 test は削除でなく置換。第 2 段は第 1 段の実測で 300 秒に入らないことを示してから。
- D2038 / D2034 (定数削減を範囲限定より先に)、D958 (所要上限と受理条件の形)、D95 (Codex author)、変異事前登録。

## 不変条件

- I1. worker 数に依らず findings / suppressions / unreferenced_copies / rc / 報告行 (elapsed・進捗行以外) が同一。
- I2. 列挙規則 (basename → size → executable の prefilter、`lstat`、`S_ISREG`、`followlinks=False`、`onerror` 計数、
  root 検証) は既存 code を共有し複製しない。worker は per-directory の同じ関数を呼ぶ。
- I3. `failures` 計数と `scan_performed` の意味は不変。heartbeat は主 thread からだけ出す。
- I4. 決定性: `possible` の owners / aliases 集合は走査順に依らない。hardlink 群の代表 external は決定的に選ぶ
  (path 昇順最小) か、少なくとも報告に影響しないことを test で固定。
- I5. candidates 空の早期 return では filesystem に触れず pool も作らない。
- I6. worker の OSError 以外の例外は握りつぶさず伝播 (既存と同じく rc=2 経路)。
- I7. 抑止 (finding を消す側) を増やす向きの変更を 1 bit も含めない (規律 2)。

## 割れうる前提 (親の provisional 裁定・攻撃対象)

- (P1) D958 項 1 の受理条件 (独立 3 走の max ≤ 上限) は、現行 main が既に上限超過 (warm 約 570 秒) の状態で
  所要を単調に下げる本変更にどう適用されるか。親 provisional: 測定は D958 の形で行い報告する。上限超過は
  D2038 が予期した結果なので単独の land 拒否理由にしない。ただし変更前 (workers=1) より悪化していれば停止。
- (P2) 並列単位 = 探索根直下の subdirectory ごとに既存の `os.walk` を worker で走らせる (root 直下の file は
  主 thread)。根拠: `os.walk` の意味論 (onerror は dir 1 回、`followlinks=False` の symlink dir の扱い) を複製しない。
  最大 job dir 59,723 file の skew は許容。
- (P3) 並列度既定 16 (bfs 実測と同じ固定値、`os.cpu_count()` に依存しない)。workers=1 は pool を作らず既存経路。
- (P4) 置換 test は「workers=1 と workers≥2 の canonical 化出力 + `audit_with_offrepo` report の同一」と
  「並列経路が実際に複数 thread で走った証拠」を対にする。静的 assert (`"ThreadPoolExecutor" not in source`) は
  置かない。
- (P5) 実根の cold 相当 (別 node の 1 走目) は `generic` dispatch で 1 走ずつ試みる。混雑で取れなければ
  T-2660 (b) として持ち越す (裁定不要)。

## 模擬 / 実の差

- unit test は `tmp_path` の小 tree (模擬)。実根の逐語一致・所要は login node の warm (実、共有 node で外乱あり)。
  cold は client cache を落とせないので測れない。単独性は `ps` で他の監査走行 0 を確認してから走らせ、
  workers=1 / N を交互に並べて cache 押し出しの交絡を見る (entry 1521 と同手順)。
- 計測は `/usr/bin/python3` (3.10.12) の解決済み実体で `python3 tools/audit_dangling_commits.py --offrepo-root
  /work/1/SFC/tanab/dev-wave-jobs` を直に叩く (env var は未設定)。

## 成果物の形と分割

- 実装 commit 1 本 (author)、fix commit (必要時)、docs commit (親)。insight
  `output/insights/2026-09-17/t2637-offrepo-parallel-scan/` (README + verbatim + 変異台帳)。
- 段 2 plan 1 本、段 3 consult 2 本 (レンズ A: `os.walk` 等価性・決定性・失敗計数・受理集合、
  レンズ B: thread 安全・heartbeat・F627 型 busy-spin・F628 型 quadratic merge・GIL と倍率)。
- 段 5 author 1 本 (tool + test の同一所有)。段 6 review 2 本 + fix。変異 matrix は段 4 で事前登録。

## 既存被覆 (純増だけ書く)

- D985 (並列却下、射程は D2038 で限定)、D2034、D2038、D2039、D2040、D958、F526 (argv 長)、F627 (heartbeat と
  poll の同一定数)、F628 (同型の第 2 実例)。本 wave の純増は「Python thread pool の実測倍率」と
  「等価性 test への置換」。
