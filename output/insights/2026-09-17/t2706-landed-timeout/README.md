# [T-2706] 着地判定器の per-command 上限を実測で 5 秒から 45 秒へ決めた

authority: none / default_effect: no-state-change (プロセス監査・逐語凍結。可変状態の正本は worklog 末尾と現行 phase doc)

- wave branch: `worktree-dev-wave-t2706-landed-timeout`
- 基準 commit: `abc7085ae6e…` (local main、wave 開始時) → `b4631a92ee57227e9d1d13227896f723895bce35` (第 20 回 rulings の着地を ff-only で取り込み。計測・実装・変異はこの main で行い、記録中に main は `67e221a30` へ進んだ — 取り込みは land の post-claim merge)
- 実装 commit: `73ca7e4e1` (Codex `role=author`、2 file、製品側は定数 1 行 + コメント 2 行、test +114 行)
- 起票: worklog archive entry 1552 の T-2706 項 (T-2640 で「本 repo では 30/30 が `assessment-timeout`」と実測)
- 裁定: D2104 項 24 (2026-09-17 第 20 回 /rulings 全件)。「受理述語は不変と確認したうえで、per-command 上限の値は Git 操作別の完了時間と全体予算内の完走率を実測して有界に決める」
- 設計判断: 本 wave の decisions fragment (slug `landed-checker-command-timeout-from-measurement`、D 番号は land の fold が付ける)
- job dir (prompt・log・probe / 集計 script・計測原本・受入 / land の launcher): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2706-landed-timeout/` (使い捨て script は repo へ入れていない。集計規則は本文に書く)

## 何をしたか

`tools/check_branch_landed.py` の `COMMAND_TIMEOUT_SECONDS` (各 git 子プロセスの `subprocess.run(timeout=min(上限, 残り全体予算))`)
を 5.0 から **45.0** に変えた。製品コードの変更はこの 1 行と根拠コメント 2 行だけで、受理述語・`min(上限, 残り)` 構造・
CLI・JSON schema・探索方式は触っていない。test を 6 node 足した (下記)。

## 受理述語は不変 (現物で確認、段 2 plan・段 3 レンズ A・段 6 レビュー A が独立に検算)

- `Git.run` の `subprocess.TimeoutExpired` は `AssessmentError("assessment-timeout", outcome="truncated")` に変換される
  (`tools/check_branch_landed.py` の `Git.run`)。`AssessmentError` の捕捉は **10 箇所** (brief の 8 は誤り): 入力解決
  (`branch-not-found` 以外は再送出)、verbatim 観測、spool 整合性、spool exact 探索、history scan、ledger corpus、
  ledger probe、patch-id、task index、最上位。
- 決定的層 (spool の 2 箇所、history scan の不完全時、最上位) はいずれも `_decision("indeterminate", …)` にしか落ちない。
  `landed` は exact tree state (tip または履歴) か fold receipt の一致から、`not-landed` は pure-add + 同 path 候補ゼロ +
  any-path 探索 (`log --find-object`) の不一致 + 完全な history scan + 終端 ref 一致からだけ出る (D922 項 2・4)。
- **精密化 (段 3 A1/A2):** 観測層 (`cherry`、ledger、verbatim) の timeout は捕捉されて続行するので「timeout が 1 度でも
  出れば最終 indeterminate」ではない。不変なのは「決定的証拠 → verdict の受理条件」であり、**時間内に確定できる入力集合は
  変わる** (それが目的)。観測層の待ちが延びて終端 ref 確認が予算切れになる逆向きも理論上あり、採用値での実走で件数を数えた (下記)。
- 上限の役割は「1 本の git が固まったとき全体予算を待たずに indeterminate で返す」だけで、verdict の質には寄与しない。
  上限 = 全体予算 (60) にすると `min` で無意味になるので、有界 = `0 < 上限 ≤ DEFAULT_TIMEOUT_SECONDS` と定めた。

## 実測 1: 上限を持ち上げた 30 件の Git 操作別完了時間 (`evidence/timing-lifted-2.jsonl`、sha256 `d53424b9…`)

母集合 = `docs/unreachable-object-ledger.md` の到達不能 commit 30 件 (proof unit 1〜42、中央値 13)。判定器を module として
読み込み `Git.run` を包んで (操作名・所要・timeout の有無) を逐次記録、上限だけを 300 秒へ持ち上げ (`min` 構造はそのまま)
全体予算 300 秒で `assess()` を順に回した。regime: pegasus02 login node、git 2.34.1、main `b4631a92e` (11,246 commit、
packed 176,575 object、19 pack、579 MB)、load average 24 → 92 (他 wave の codex 子 4 本と test 走行 11 本が同居)。
適用先 (rescue gate / cleanup の判定) も同じ login node なので regime は一致する。30 run、git 子 2,935 本、打切り 0、
壁時計 10.2〜250.6 秒 (中央値 52.6、合計 2,194 秒)。

| 操作 | n | 中央値 | p95 (nearest-rank) | 最大 | 層 |
|---|---:|---:|---:|---:|---|
| `log --full-history --max-count=1 --find-object=<oid> <main>` | 8 | 16.35 | 26.87 | **26.87** | 決定的 (`not-landed` に必須の全履歴走査) |
| `log --full-history --format=%H --max-count=1025 <main> -- <path>` | 349 | 3.84 | 9.11 | 21.29 | 決定的 (exact state 探索) |
| `cherry -v <main> <oid>` | 30 | 4.17 | 12.91 | 13.66 | 観測 |
| `rev-list --topo-order` | 36 | 0.51 | 1.16 | 1.19 | 決定的 |
| `ls-tree` | 1,089 | 0.05 | 0.25 | 1.16 | 決定的 |
| 他 8 種 (`diff` / `cat-file --batch` / `show` / `cat-file --batch-check` / `diff-tree` / `rev-parse` / `cat-file` / `for-each-ref`) | 1,423 | ≤ 0.84 | ≤ 1.11 | ≤ 1.12 | 混在 |

verdict (持ち上げ走): landed 2、not-landed 4、indeterminate 24 (うち `refs-moved` 1 = 97 秒の判定中に main が動いた、
`one-or-more-states-unproven` 23)。observations / ref_snapshot phase は 30 件とも matched。

**上限ごとの超過 command 本数 (2,935 本):** 5 → 136 (`log -- <path>` 117、`cherry` 11、`--find-object` 8)、10 → 25、
15 → 11、20 → 3、**30 以上 → 0**。旧 5 秒は `log -- <path>` の p95 (9.1 秒) にも `--find-object` の最小値 (13.2 秒) にも
届かず、`not-landed` は構造的に出せなかった。

**無中断推計** (記録した command 列を順に流し、各 command の実効 timeout = `min(上限, 予算 − 経過)`、`cherry` は超過しても
上限ぶん待って続行、他は超過で中断、最後に wall − Σelapsed を足して予算内なら完走。実測完走率ではない):

| 上限 \ 予算 | 8 (rescue 内部既定) | 60 (判定器既定) | 120 | 300 (CLI 上限) |
|---|---|---|---|---|
| 5 | 0 : 0 | 3 : 0 | 3 : 0 | 3 : 0 |
| 10 | 0 : 0 | 10 : 1 | 19 : 2 | 20 : 2 |
| 20 | 0 : 0 | 15 : 3 | 25 : 4 | 27 : 4 |
| **30 / 45 / 60** | 0 : 0 | **16 : 4** | 27 : 6 | 30 : 6 |

(完走 : 確定 / 30。確定 = 持ち上げ走の verdict が landed / not-landed)。予算 60 で上限を上げても完走しない 14 件は
いずれも全体予算の枯渇 (最初に予算切れになった操作: `log -- <path>` 12、`--find-object` 1、終端 `rev-parse` 1) で、
上限でなく「予算 × 必要操作の合計」の律速。予算 8 では上限を何にしても 0 件。

## 実測 2: 反復点検 (`evidence/repeat-heavy.json`、段 3 レンズ B の B2)

30 件走の直後、load 27〜40 で重い 3 操作を判定器と同じ引数・env で反復した。`log -- <path>` 69 本 (`cd066a04` の 23 path
× 3) = min 1.95 / 中央値 7.87 / **最大 35.94** 秒 (同じ path が 9.6 → 35.9 秒と 3.7 倍の幅、共有 /work の I/O 競合)、
`--find-object` 3 本 = 11.34 / 17.50 / 20.76、`cherry` 3 本 = 2.43 / 2.85 / 6.87。

## 値の決め方 (段 4 で事前登録、30 件完了後に機械的に適用)

1. 全 command の最大 = 26.87 秒 (`--find-object`)。× 1.5 = 40.3 → 格子 {10, 15, 20, 30, 45, 60} の最小の上 = **45**。
2. 反復点検の最大 35.94 ≤ 45 → 据え置き (超えていれば次の格子)。45 は反復最大の 1.25 倍、30 件走最大の 1.67 倍。
3. 45 ≤ `DEFAULT_TIMEOUT_SECONDS` (60)。60 は `min` で上限が無意味になるので採らない。
4. 段 5 の暫定値 30 (10 件時点の最大 19.5 × 1.5) は、反復点検で 2 本 (35.9 / 30.5 秒) が超過した。
5. 倍率 1.5 は親の判断値 (導出値ではない)。同じ操作が load で 2 倍動く観測から置いた。

焦点再レビュー (段 6) が (a) 最大値と操作、(b) `log -- <path>` の n / 中央値 / p95 / 最大、(c) `cherry` 最大、(d) 上限別
超過本数、(e) 推計表、(f) verdict 内訳、(g) 反復点検、(h) 規則の出力を原データから独立に再計算し、すべて一致した。

## 実測 3: 採用値の判定器 CLI で 30 件を既定予算 60 秒で実走 (現行 producer、対照は同時刻の旧 5.0)

`evidence/live-control-5s.jsonl` (HEAD 版 5.0) と `evidence/live-new-45s.jsonl` (実装後 45.0)、いずれも CLI 既定
`--timeout-seconds 60`、同じ 30 OID、対照 → 新の順で連続実走 (07:42〜08:13 JST、load 9〜35)。集計は `evidence/live-summary.txt`。

| 版 | 完走 (timeout なし) | 確定 (landed / not-landed) | `assessment-timeout` | timeout した phase | `refs-moved` | 壁時計 中央値 / 合計 |
|---|---|---|---|---|---|---|
| 旧 5.0 | **10 / 30** | 0 | 20 | proof 20 | 0 | 18.3 秒 / 550 秒 |
| 新 45.0 | **16 / 30** | **3** (landed 1、not-landed 2) | 14 | proof 13、**終端 ref 確認 1** | 2 | 57.5 秒 / 1,307 秒 |

- 新 45.0 の完走 16 は無中断推計の 16 と一致した。確定は推計 4 に対し 3 で、差の 1 件は実走中に main が動いた
  `refs-moved` (2 件) による。旧 5.0 は `--find-object` (最小 13.2 秒) が必ず落ちるので確定 0。
- **観測層の待ちが延びて終端 ref 確認が予算切れになる逆向き (段 3 A1) は 1 件で実測された** (`ref_snapshot` truncated 1、
  `observations` truncated 0)。旧 5.0 では 0 件。
- 対照が entry 1552 の 30/30 timeout より軽い (20/30) のは負荷差 (T-2640 時は未記録、本走は load 11〜25)。完走率は
  負荷に依存するので、本 wave の主張は「観測条件で 10/30 → 16/30、確定 0 → 3」に限る。

## test (6 node、`orchestrator/tests/test_check_branch_landed.py`)

- `test_command_timeout_default_is_bounded_and_bound`: `0 < COMMAND_TIMEOUT_SECONDS <= DEFAULT_TIMEOUT_SECONDS` と
  `Git.run` の既定引数が定数と同値 (既定引数は def 時に束縛されるので module 属性の monkeypatch では変わらない)。
- `test_git_run_real_command_timeout_is_truncated`: PATH 先頭の偽 git (`exec sleep 2`) で `run([...], command_timeout=0.05)`
  が実 `subprocess.TimeoutExpired` (timeout ≈ 0.05) から `assessment-timeout` / `truncated` になる。
- `test_assess_real_log_timeout_is_indeterminate_not_a_verdict[{True,False}-{proof-path-log,any-path-find-object}]`:
  偽 git が `-c VALUE` 群を読み飛ばして `log` の形 (`--` あり / `--find-object=` あり) を判別し、対象だけ `exec sleep 2`、
  他は本物 git へ全引数で委譲。`Git.run` の観測 wrapper (実物へ委譲) が対象到達時にだけ `command_timeout=0.05` を渡す。
  遅延あり → `indeterminate` / `assessment-timeout`、proof phase `truncated`、`negative_paths == []`、
  `branch_delete_authorized is False`。遅延なし (同じ偽 git 経路) → 証拠どおり `landed` (履歴 exact state) /
  `not-landed` (closed-world 負証拠)。**上限でなく証拠が verdict を決める対。**
- 実走: 焦点走 (計算ノード) 判定器 file 102 passed、新規 6 node PASSED (4.1 秒)、fix 後は判定器 + rescue の 2 file 182 passed (5.4 秒)。

## 変異 matrix (container worktree `.codex/worktrees/t2706-mutcontainer` = 実装 commit `73ca7e4e1`、dispatch、D612 上書き 1800/600)

spec は `mutation-spec-probe.json` / `mutation-spec-final.json`、台帳は `mutation-ledger-probe.json` / `mutation-ledger-final.json`。

runner は `python3 tools/run_tests.py orchestrator/tests/test_check_branch_landed.py -q -rf --force-dispatch`。

- probe 走 (spec sha256 `d871d876…`、全件 SURVIVED 登録で観測 node を集める): baseline PASSED (28.8 秒)、M0 SURVIVED、M1〜M5・M7 は
  全部 MISMATCH (= 赤 node を観測)。観測 node をそのまま本走 spec の `expected_nodes` へ写した。
- 本走 (spec sha256 `1b8362e5…`): **baseline PASSED (27.9 秒)、負例 6 件 (M1〜M5・M7) すべて KILLED で期待 node と観測 node が
  完全一致 (matching 7/7)、等価変異 M0 (コメント 1 語) は SURVIVED、MISMATCH 0、TIMEOUT 0、anchor はすべて 1 箇所、所要 249 秒。**

| ID | 変異 (single-site、`tools/check_branch_landed.py`) | KILLED node 数 | 主担当 / 検出 node |
|---|---|---|---|
| M0 | 根拠コメントの `max` → `maximum` (等価) | — (SURVIVED) | — |
| M1 | `Git.run` の `TimeoutExpired` を握り潰し空 stdout の成功を返す | 3 | 実 timeout 単体 + assess の delayed=True 2 node |
| M2 | `outcome="truncated"` → `"error"` | 3 | 同上 (outcome / proof phase の検査) |
| M3 | `Git.run` の既定引数を定数から旧値リテラル `5.0` へ切り離す | 1 | `test_command_timeout_default_is_bounded_and_bound` |
| M4 | 定数を `61.0` (全体予算超) | 1 | 同上 (有界 pin) |
| M5 | 最上位 except の `indeterminate` → `landed` | 26 | assess の delayed=True 2 node + 既存の indeterminate 系 24 node |
| M7 | 不完全な history scan でも負例 unit を `indeterminate` へ戻さない | 1 | 既存 `test_history_scan_limit_is_indeterminate_and_measured` |

専属 killer は M3/M4 (有界 pin) と M7 (既存 test) の 3 件。M1/M2/M5 は複数 node が検出する (段 3 B9 の指摘どおり専属とは書かない)。

- M6 (`_regular_decision` の `any_path.incomplete` → not-landed) は段 4 で登録したが、author・レビュー A・B が独立に
  「`--find-object` の timeout は非 spool の `_proof_unit` で捕捉されず最上位へ伝播するため `any_path.incomplete` が真になる
  経路が無い」と判定し、両層変異は一箇所置換の条件を外れるので除外した (`verbatim/value-decision.md`)。

## consumer と残る制約 (scope 外、記録のみ)

- `tools/check_branch_rescue.py` は判定器を `--timeout-seconds 8.0` (既定、上限 60) で subprocess 起動する。`min(45, 残り)`
  で 8 に切られるため、rescue 経路では「残り 5 秒超の操作」にだけ効き、30 件のどれも 8 秒では完走しない (推計 0/30)。
  内部予算と外側 timeout の配分は裁定パッケージ候補として worklog の次の一手に置く。
- 判定器既定 60 秒では 30 件のうち 16 件しか完走せず、unit 数の多い commit は `log -- <path>` の合計で予算を超える。
  `DEFAULT_TIMEOUT_SECONDS` の見直しは本 wave では変えない (名指しの変更に限定、D2104)。
- 共有 repo では長い判定が ref 移動に負ける (`refs-moved`、30 件中 1 件)。
- `Git.run` は `OSError` (git 不在等) を捕捉せず JSON を返さず落ちる (段 3 A5)。偽 verdict の経路ではない。
- 焦点再レビューの F1: 新 test の `__cause__.timeout ≈ 0.05` は wrapper の `remaining() > 1.0` と `Git.run` 内の再取得の間に
  約 1 秒の停止があるときだけ偽赤になる。fix せず記録。

## verbatim / evidence

`verbatim/` は各段の brief・plan・相談・裁定・author・レビュー・fix・焦点再レビュー・値の確定文書。`git diff --check` に
触れる行末空白を除いてあり、原本の sha256 は `verbatim/originals.sha256`。`evidence/` は計測原本 (JSONL、集計、反復点検、
実走)。使い捨ての計測・集計 script は job dir にあり repo へ入れていない (集計規則は上に逐語で書いた)。
