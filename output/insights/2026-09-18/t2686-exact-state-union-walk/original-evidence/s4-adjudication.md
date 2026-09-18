# 段 4 裁定 — [T-2686] (2026-09-18 16:35 JST)

親が plan (s2)・addendum・consult A (git 意味論)・consult B (予算・契約・test) の所見を裁定し、plan v2 と変異事前登録を確定する。

## 所見の裁定 (real / refuted、採用 / 不採用、scope 内 / 外)

| # | 所見 | 裁定 | 扱い |
|---|---|---|---|
| A-1 | rename 検出で移動元 path の候補が落ちる (実在 commit 8e0aadc1 で実測) | **real** | 採用・must-fix: union command に `--no-renames` (親も実測: 両名が出る)。合成 repo test + 変異 |
| A-2 | 非 UTF-8 の file 名で strict UTF-8 parser が旧版より早く赤になる | real | 採用: name は bytes のまま扱い decode しない。登録 path (`_parse_raw_diff` で UTF-8 保証済) を `encode("utf-8")` して bytes で prefix 一致 |
| A-3 | repo-local `log.follow=true` で旧 single-path 走査が `--follow` になり結果が変わる (親実測: 2 → 16 件) | **real** | 採用: `git config --get --type=bool log.follow` が true なら union を作らず旧 per-path command へ fallback (A3 と同じ経路) |
| A-4 | prefix 規則は `tools/`・`.` 等の未正規化 pathspec には合わない | real (入力域の明記) | 採用: 供給 object の入力域は `_parse_raw_diff` 由来の正規化 tree path (末尾 `/` なし、`.` なし) に限ると docstring・D に明記。fail-closed 検査は足さない (入力は自コードが作る) |
| A-5 | 走査順の pathspec 非依存は一般証明でない | 判定不能 → 採用 (受入条件の形) | 実 repo 47 path の一致 + 合成 DAG test (timestamp 逆転・同時刻・親順入替・octopus・削除だけの merge) を証拠とし、「同一」の主張は「実測範囲と test 範囲で同一」に限定して D に書く |
| A-6 | A1 の時間保証は導けない | real | 採用: A1 は「逆転経路を狭める改善」であり非退行の証明ではないと明記。受入条件から時間保証を外す (A5 と整合) |
| A-7 | 既存 probe は新設計 (framing/parser) の証拠にならない | real | 採用: probe は候補列 (集合・順序・上限) の一致証拠にだけ使う。framing/parser の証拠は合成 repo test |
| B-1 | P1 (scope 移動) は依頼意図に沿う (条件付き) | real | 採用: file 名の誤記訂正と「本標本での優先順位」を分けて記録。「closure 改善は収益なし」→「本標本で 2.3 秒 / 372 秒、優先順位が低い」に改める |
| B-2 | P2 「別 file なので衝突しない」は根拠にならない | real | 採用: 着手は待たない。land 前に main を取り込み、T-2691 が land 済なら `test_check_branch_landed.py` と `test_check_branch_rescue.py` の両方を焦点走 + 受入で通す (統合検査を land 条件にする) |
| B-3 | A1 で timeout 悪化を塞げるは誤り。反例 {p 要走査, q tip 一致で hot} | real | 採用: 登録集合を「tip 不一致で実際に走査が要る path」に絞る (下記 v2-3)。非退行の主張は撤回 (A-6) |
| B-4 | 再走査は同じ Git・同じ deadline | real | 採用: 2 本目も `Git.run` (min(45, remaining))、remaining ≤ 0 なら `Git.run` が `assessment-timeout` を投げる (既存契約)。再起算・retry なし |
| B-5 | fallback の失敗 memo の範囲 | real | 採用: union 失敗は union 全体で memo (同じ例外を再送出)。per-path fallback は path ごとに独立 (旧版と同じ)。tip 不一致判定に使う ls-tree の失敗は従来どおりその call site で送出 |
| B-6 | argv 閾値の根拠 | real | 採用: 定数 `HISTORY_CANDIDATE_ARGV_BYTES_LIMIT = 65536` (path bytes の総和 + 1/path)。根拠: Linux の MAX_ARG_STRLEN 128 KiB (1 引数) と ARG_MAX ≥ 128 KiB (POSIX 最小は 4 KiB だが Linux は stack/4 ≥ 128 KiB) に対し固定 argv (~400 B) + env (~300 B) を足しても 1/2 未満。超過は旧経路 fallback なので閾値の値は正しさに影響しない |
| B-7 | 受入実験は CLI 上限 300 秒・`--main` は branch 名 | real | 採用: 比較は外部 driver から両版の `assess(repo, oid, timeout_seconds=900)` を呼ぶ形に変更 (production CLI/定数は不変)。旧版 = 比較元 main の file を job dir へ抽出 (source sha256 記録)、新版 = worktree。同じ `--repo` (worktree path)、同じ target OID、各走の前後で `git rev-parse main` を記録し動いた組は無効。旧/新/旧/新で raw JSON・rc・wall・process 数を保存し、timing 系 field を除いた canonical JSON を byte 比較 |
| B-8 | D2054 は batch_safe の裁定でない | real | 採用: 参照を C:785 (`batch_safe`、T-2639 実装) に改める |
| B-9 | 5 倍等の一般化は不可 | real | 採用: 報告は「同時刻交互 A/B の観測値 (条件付き)」と「同一入力での process 数削減」だけ。「4〜25 秒」は単発計測の範囲、全走では 28.6 秒もあったと併記 |
| B-10 | timing 重複計上・`report_sha256` 変化 | real (nit) | 採用: D に明記。field 名は `timing.history_candidate_walks` / `timing.history_candidate_walk_seconds` に統一。fallback 時の walks は実際に走査した path 数 |
| B-11 | 変異 (b) は非整列 OID の assert、(c) は境界正例、(g) は他検査との重複確認 | real | 採用: 事前登録に反映 (下記) |
| B-12 | plan の stdin 設計・「常に 1 本」記述の削除 | real | 採用: v2 では `--stdin` を使わない。walks は 0 / 1 / 2 / fallback path 数 |
| P-1 | RS framing の衝突 | real | 採用済 (addendum A2: `%x00%H`、空 field = header) |
| P-2 | 全入力での timeout verdict 同一は主張できない | real | 採用: A5 の限定 (正常完走時の同一 + timeout 時 indeterminate class) を D に書く。片側だけ timeout する入力があることも明記 |

裁定パッケージへ返す項目: なし (すべて scope 内で採用し、研究前進・実測欠陥に関わる未裁定の択一は残らない)。scope 外 real 所見 (closure/introduced_states の一括化の余地、rescue 8 秒予算) は insight に記録するだけ。

## plan v2 (author への確定仕様)

対象 file: `tools/check_branch_landed.py`、`orchestrator/tests/test_check_branch_landed.py` のみ。

1. **供給 object** `_HistoryCandidates` (module 内 class、frozen でない dataclass か通常 class):
   - 構築: `git`, `main_oid`, `candidate_limit`, `pairs: list[tuple[str, TreeEntry]]` = 登録対象 (path, required)。登録対象 = 全 state のうち (a) non-spool の `required`、(b) spool で `not required.missing and object_type == "blob" and mode in {"100644","100755"}` の `required`。distinct 化は path 単位で行うが pair は全部保持する。
   - `candidates(path) -> list[str]`: 初回呼び出しで 1 回だけ供給を作る。2 回目以降は memo。未登録 path は `ValueError` (呼び手の bug、AssessmentError にしない)。
   - 供給の作り方 (初回):
     1. **tip 絞り込み**: 各 distinct path の main tip entry を `_tree_entry(git, main_oid, path, len(oid))` で得る (`_find_exact_state` / `_proof_unit` の同じ call を memo `tip_entries: dict[str, TreeEntry]` に載せ替える — 同じ command、同じ parse、失敗は同じ例外をその call site で送出)。走査対象 `P = {path | ∃ pair (path, required): not _entry_matches(required, tip_entries[path])}`。P が空なら走査 0 本。
     2. **fallback 判定** (どちらかで per-path mode): `git config --get --type=bool log.follow` (allowed rc 0/1) が `true`、または `sum(len(p.encode()) + 1 for p in P) > HISTORY_CANDIDATE_ARGV_BYTES_LIMIT`。per-path mode では path ごとに旧 command `log --full-history --format=%H --max-count={limit+1} <main> -- <path>` を**要求時に**実行し path ごとに memo (失敗も path ごと)。
     3. **union mode**: `git.run(["-c", "log.showRoot=true", "log", "--full-history", "--diff-merges=separate", "--no-renames", "--ignore-submodules=none", "--name-only", "-z", "--format=%x00%H", f"--max-count={K}", main_oid, "--", *sorted(P)])`、K = (limit+1) × |P|。出力を strict parse (下記) → distinct commit 数 n と派生列。`n == K` かつ `∃ p: len(list) < limit+1` なら `--max-count` 無しで 1 回だけ再走査し結果を置換 (連結しない)。`n > K` は parse error。
     4. 派生: entry 出現順 (同じ H は初出位置) を保ち、path p の列 = [c | ∃ entry of c: ∃ name: name == p_bytes or name.startswith(p_bytes + b"/")] を先頭 limit+1 件で切る。
   - 記録: `walks` (実行した log 本数)、`seconds` (log の合計秒)、`mode` ("union" / "per-path" / "none")。assess が `payload["timing"]["history_candidate_walks"]` / `["history_candidate_walk_seconds"]` に書く。
   - 失敗 memo: union mode の `AssessmentError` は保存し、以後の `candidates()` で同じ instance を再送出。
2. **parser** `_parse_history_candidate_stream(raw: bytes, expected_oid_length: int) -> list[tuple[str, list[bytes]]]` (commit 順、各 commit の name 集合。同一 commit の複数 entry は 1 要素に集約):
   - 文法: stream := (`\0` H `\0` `\n` name (`\0` name)* `\0`)*。NUL で split し、空 field の直後を header と読む。header 直後の field は `\n` で始まること (ちょうど 1 byte 剥がす)。name は非空 bytes。末尾は `\0` で終わる (split の最終要素が空)。空 stream は正常 (候補 0)。
   - 逸脱 (H が 40/64 lowercase hex でない・長さが expected と違う、header 直後が `\n` で始まらない、name が空、末尾 `\0` 欠落、先頭が `\0` でない) → `AssessmentError("history-candidate-parse-error", ..., outcome="error")`。name を decode しない。
3. **`_find_exact_state(git, main_oid, required, candidate_limit, supplier)`**: tip 照合を `supplier.tip_entry(required.path)` (memo) に置き換え、`git.run([log ...])` を `supplier.candidates(required.path)` に置き換える。それ以外 (batch_safe、`_batch_check_path_candidates`、`_tree_entry` 再確認、`> limit` の truncated、SearchResult の reason 文字列) は不変。`elapsed_seconds` は関数入口からの経過のまま。
4. **`_proof_unit`**: signature に `supplier` を足し、2 箇所の `_find_exact_state` 呼び出しと `tip_entry = _tree_entry(git, main_oid, ...)` を supplier 経由にする。分岐条件・例外捕捉は不変。
5. **`assess`**: `states` 確定後・unit loop 前に supplier を構築 (走査はしない)。loop 後に timing 2 field を書く (except 経路でも書けるよう supplier を try の外で None 初期化)。
6. **test** (`orchestrator/tests/test_check_branch_landed.py` に追加、既存 test の期待値は変えない。注入面の更新は plan の T:395–412 / 455–475 / 488–512 / 1037–1117 のとおり、意味上の期待を保つ):
   - 正例群 `test_history_candidates_match_legacy_command[<case>]`: 合成 repo で supplier の派生列と、同 repo・同 env で走らせた旧 command の出力 (list) を**順序付きで直接比較**。case: ordinary / one_parent_merge (対照に merge OID が含まれることも assert) / both_parent_merge / octopus / delete_only_merge / timestamp_inversion (親より古い committer date の子) / equal_timestamps / parent_order_swapped / root (repo-local `log.showRoot=false` を設定) / delete_readd / file_to_directory (`f` と `f/child` を両方登録) / gitlink (repo-local `diff.ignoreSubmodules=all` を設定した variant も) / rename_exact と rename_modified (移動元・移動先を両方登録、旧 command との一致) / limit_plus_one (長さがちょうど limit+1、順序一致、対照列が lexical sort でないことを assert) / positive_at_limit_plus_one (limit+1 番目に正証拠 → matched) / lf_in_name と rs_in_name と leading_lf_name と hex40_name と non_utf8_sibling (別 file 名が非 UTF-8 でも登録 path の列は一致)。
   - 有界走査群 `test_history_candidates_bounded_walk[<case>]`: `n < K` / `n == K` 全飽和 (walks == 1) / `n == K` 未飽和 (walks == 2、置換で連結なし) / merge の親別 entry を 1 commit と数える。
   - fallback 群: `log.follow=true` (repo-local) で per-path mode になり旧 command と一致 (rename fixture で follow の差が出る構成)、argv 上限 (monkeypatch で定数を 0 と、境界直前/直後) で per-path mode、per-path mode の失敗が path 単位であること。
   - parser 群 `test_history_candidate_parser_rejects[<case>]`: 不正 hex / 長さ違い / header 直後に `\n` 無し / 空 name / 末尾 NUL 欠落 / 先頭が NUL でない → code と outcome。`test_history_candidate_parser_preserves_names`: 先頭 LF・RS・CR・TAB・40hex・非 UTF-8 の name を bytes のまま保持。
   - timeout 群: union 走査で偽 git が `TimeoutExpired` → 非 spool unit では `assessment-timeout` / `truncated` / `indeterminate`、spool unit では unit evidence に同 code。2 本目 (再走査) 開始前に残り 0 → `assessment-timeout`。
   - 契約群: `test_history_candidates_walk_count`: 複数 path・同 path 複数 unit・spool fallback 併存で walks == 1、全 tip 一致で walks == 0、tip 一致の hot path が走査対象に入らない (pathspec に含まれない) こと。
   - payload 群 `test_assess_payload_matches_legacy_supplier`: test 専用の旧供給 (path ごとに旧 command) へ差し替えた assess と新 assess の payload が `elapsed_seconds` と `timing` を除いて等しい (合成 repo、正常完走)。
7. **docstring / D**: 供給 object の入力域 (正規化 tree path)、同一性の主張範囲 (正常完走時の候補列・payload。timeout 時は class のみ。片側だけ timeout する入力の存在)、A1 は改善であって非退行証明でないこと。

## 変異事前登録 (`DW-M01`。位置は author の実装後に 1 箇所へ確定し、単一理由を確認する)

| id | 変異 | 期待 | killer node |
|---|---|---|---|
| m01 | union command から `--no-renames` を外す | KILLED | match_legacy[rename_exact] |
| m02 | `--ignore-submodules=none` を外す | KILLED | match_legacy[gitlink_ignore_submodules_config] |
| m03 | prefix 規則を `name == p` だけにする | KILLED | match_legacy[file_to_directory] |
| m04 | 派生列を sort する | KILLED | match_legacy[limit_plus_one] (非整列 assert 付き) |
| m05 | `[:limit+1]` を `[:limit]` にする | KILLED | match_legacy[limit_plus_one] / positive_at_limit_plus_one |
| m06 | `--diff-merges=separate` を外す | KILLED | match_legacy[both_parent_merge] |
| m07 | `--full-history` を外す | KILLED | match_legacy[one_parent_merge] |
| m08 | `-c log.showRoot=true` を外す | KILLED | match_legacy[root] |
| m09 | 再走査条件を常に偽にする | KILLED | bounded_walk[n_eq_K_unsaturated] |
| m10 | n を distinct commit でなく entry 数で数える | KILLED | bounded_walk[merge_entries_count_once] |
| m11 | `log.follow` の fallback を外す | KILLED | fallback[log_follow_true] |
| m12 | argv 上限の fallback を外す | KILLED | fallback[argv_limit] |
| m13 | header 直後の LF を `lstrip(b"\n")` で剥がす | KILLED | parser_preserves_names[leading_lf] |
| m14 | tip 絞り込みを外す (全登録 path を走査) | KILLED | walk_count[tip_matched_hot_path_excluded] |
| m15 | 失敗 memo を外して再走査する | KILLED | timeout 群 (2 回目の要求で再走査しない) |
| m16 | コメントだけ変更 | SURVIVED (等価対照、集計から除外) | — |
| m17 | 供給を旧 per-path へ戻す (union を作らない) | 意味論 SURVIVED / 契約 KILLED | walk_count (process 契約) — 分類を混同しない |

## 受入条件 (事前登録、結果を見る前に固定)
1. 焦点走 (両 test file + 新規 node) 緑、変異 matrix baseline 緑・m01〜m15 KILLED・m16 SURVIVED・m17 は契約 node で KILLED。
2. 固定 OID `559bcbc29cfa27412f103b608e8ac708dcfae6b9`、同じ repo path、同じ main OID (前後で照合) で、旧/新/旧/新の `assess(timeout_seconds=900)`: timing 系 (`elapsed_seconds` 全出現、`timing.*`) を除いた canonical JSON が byte 一致、`timing.git_child_processes` が旧 > 新、wall は観測値として併記 (改善率の一般化はしない)。
3. 受入全走緑 (land の受領証)。T-2691 が land 済なら main 取り込み後に両 test file の焦点走を再走。
