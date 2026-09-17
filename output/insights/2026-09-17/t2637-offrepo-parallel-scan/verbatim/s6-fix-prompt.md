単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.codex/worktrees/t2637-impl

## 必読事項の射影

次の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**する。これは射影 file 限定の停止規則であり、自分が推測して探した path が不在でも停止理由にしない。

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2637-offrepo-parallel-scan/s4-adjudication.md` — 親の段 4 裁定 (§2 実装仕様、§3 受理条件、§4 変異 matrix)。本 fix は §2 の「並列単位」だけを下の指示で置き換える。他は不変
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2637-offrepo-parallel-scan/s5-implementation.diff` — 段 5 の差分 (この worktree に未 commit で適用済み。これを土台に直す)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2637-offrepo-parallel-scan/artifacts/dev-wave-t2637-offrepo-parallel-scan/s5-author.md` — 段 5 author の報告
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2637-offrepo-parallel-scan/s6-parent-measurement-v1.md` — **親の実測 (本 fix の根拠)**: 直下 subdirectory 単位の分割では 1 本の巨大部分木が tail になり並列が効かない
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2637-impl/tools/audit_dangling_commits.py` — 編集対象 (適用済み現物)。`_OffrepoCounts` 〜 `_enumerate_offrepo_candidates` (868〜1110 付近)
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2637-impl/orchestrator/tests/test_audit_dangling_commits.py` — 編集対象 (適用済み現物)。新設 test (1189〜1530 付近)
- `/usr/lib/python3.10/os.py` — `walk` (340〜430 付近)。1 directory 分の意味論 (scandir 失敗 → `onerror` 1 回・その directory は yield しない、`is_dir()` で分類、再帰前の `islink` 判定) の正本

repo root は `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2637-impl` とする。**大きい file を全文 `cat` しないこと。** `grep -n` で位置を出し `sed -n` で 200 行以内ずつ読む。

## 何が起きたか (親の実測、詳細は s6-parent-measurement-v1.md)

実根 (直下 1,252 entry、約 185 万 file) で段 5 版を workers=16 で走らせたところ、最初の 60 秒は約 14,500 file/秒 (逐次版の約 10 倍) で進んだが、120 秒以降は 1 本の worker だけが動く tail に入り、約 500〜1,000 file/秒で 15 分以上続いた。開いている fd から、tail は `dev-wave-suite-floor-recheck/measure/run2/.../pytest-of-tanab/...` (pytest の tmp repo が数万個ある深く小さい directory の森) を 1 thread で walk していることが分かった。**直下 subdirectory 単位の分割は部分木の偏りに無力**で、16 thread の利得が 1 本の部分木の逐次時間で頭打ちになる。

## この段の仕事

並列単位を「探索根直下の subdirectory ごとに `os.walk` 全体」から **「directory 1 個ごとの task を work queue で動的に配る」** 形へ置き換える。範囲・規則・出力は引き続き一切変えない。workers=1 の経路 (pool なし、root 全体を 1 本の `os.walk`) は**そのまま残し、意味論の参照実装**とする。

設計 (必ず守る):

1. **1 directory の処理は `os.walk` の最初の iteration だけを使う。** task = `(directory: Path, key_prefix)`。worker は `walk = os.walk(directory, topdown=True, onerror=counts.record_error, followlinks=False)` を作り `iteration = next(walk, None)` を取り、`finally: walk.close()`。`None` (scandir 失敗、`onerror` は既に計数済み) なら何もしない。それ以外は既存の共有 helper で `dirnames.sort()` / `filenames.sort()` / `filenames` の候補照合 (`lstat`、`S_ISREG`、size・mode prefilter、group 化) を行い、**sorted `dirnames` の各 name について `os.path.islink(os.path.join(directory, name))` が偽のものだけ**を新しい task として queue へ入れる (これは `os.walk` 自身の再帰条件 `if followlinks or not islink(new_path)` と同一で、symlink dir は `dirnames` に載るが降りない)。再帰は自分でしない (走査した directory は 1 task が 1 回だけ処理する)。
2. **決定性 (first-seen の再現)。** 逐次版 (`os.walk` topdown、sorted) の訪問順は「directory の file をすべて処理してから sorted 順に subdirectory へ降りる」前順 DFS である。各 file に **walk key** = `key_prefix + ((0, filename),)`、各 subdirectory task に `key_prefix + ((1, name),)` を付ける (`(kind, name)` の tuple 列。同じ directory では file `(0, x)` が subdirectory `(1, a)` より先、file 同士・dir 同士は name 順)。group `(OID, dev, ino)` の代表 `external` (path + initial_stat) と `metadata` は **key 最小のもの**を採り、owners / aliases は union する。worker 内でも merge 時にも key 比較で代表を決め、完了順に依存させない。`possible[oid]` の identity の挿入順も代表 key の昇順に並べ直し、逐次版の挿入順と一致させる (oid の挿入順も同様に最小 key 順)。root は `sorted(roots)` の順に**逐次**に処理し (root ごとに queue を空にしてから次の root)、既存 group の代表は先の root のものを保持する (入れ子 root の alias 2 個・失敗 2 回は現行どおり)。
3. **root の扱い。** root の `lstat` と permission 検査は主 thread に残す (子へ再適用しない)。root 自身の最初の iteration は主 thread で処理し (key_prefix = `()`)、その subdirectory を最初の task 群として queue へ入れる。root の最初の iteration が `onerror` で終われば候補 0・failures 加算・`scan_performed=True` (現行どおり)。
4. **pool は固定 N thread + `queue.Queue` (または `SimpleQueue`) + 未完了 task 数の counter。** `concurrent.futures` の future を directory ごとに作らない (25 万 future の `wait` は二次化する、F628)。完了判定は「queue が空かつ処理中 task 0」。主 thread は `Event.wait(timeout=POLL_CEILING_SECONDS)` (または `Condition.wait`) で待ち、毎回 worker の公開計数 (lock 付き slot、既存 `_OffrepoCountSlot` を worker ごとに 1 個) を合算して `heartbeat.pulse(f"directories=... files=...")` する。`HEARTBEAT_INTERVAL_SECONDS` が 0 でも待ち時間を 0 にしない (F627)。heartbeat は主 thread からだけ。
5. **例外。** worker 内の `OSError` は現行位置 (walk の `onerror`、候補 `lstat`) で計数。それ以外の例外は worker が記録して停止 flag を立て、他 worker は次の task 取得時に停止し、主 thread は全 thread の join 後に**最初の例外をそのまま再送出**する (握りつぶさない、`RuntimeError` へ包まない)。thread は daemon にしない。停止 flag が立ったら残 task は捨ててよい (結果は破棄されるので出力に影響しない)。
6. **計数。** worker ごとの `_OffrepoCounts` (directories / files / failures) を持ち、最後に主 thread へ合算 (二重加算なし)。`failures` は `AuditReport.scan_failures` に出るので漏れなく。
7. **変えないもの:** `_offrepo_scan_workers` (env / 既定 16 / 検証)、candidates 空の早期 return (filesystem・pool・env に触れない)、workers=1 の逐次経路、`_process_offrepo_iteration` 相当の候補照合規則 (共有 helper のまま。key を渡す引数を足すのはよい)、報告行・`--help`、`_compare_offrepo_candidates` 以降、境界 helper (T-2662)、alias 配布 (T-2664)、`tools/check_branch_rescue.py`、docs。

test (同じ file 内で直す。**既存 test の期待値は変えない** — 旧 1183〜1186 の置換は段 5 で済み):

- 段 5 の新設 10 test は名前と意図を保ち、新設計に合わせて中身を直す。特に `test_parallel_offrepo_scan_uses_multiple_threads` は production の task 処理関数を wrap (保存した本物を呼ぶ、pool は置換しない) して `threading.get_ident()` 集合 ≥ 2 を Barrier で確認、`test_parallel_offrepo_scan_preserves_first_seen` は task の処理順を意図的に逆転・遅延させても代表 path と `possible[oid]` の挿入順が逐次版と一致することを内部代表の直接 assert で固定、`test_parallel_offrepo_scan_propagates_worker_exception` は worker の固有例外が呼び手へ同じ型で再送出され、かつ全 thread が終了していること (`threading.active_count()` が呼出前と同じ、または join 済み) を確認。
- 追加で 2 test: (a) `test_parallel_offrepo_scan_handles_deep_and_wide_trees` — worker 数 (4) より深い入れ子 (深さ 8 以上) と、1 個の巨大 subdirectory (数百 dir) + 多数の小 subdirectory の混在で、workers=1 と 4 の canonical 結果・計数が一致し、全 directory が 1 回だけ処理される (task 処理関数を wrap して directory の多重集合を記録し、重複 0・欠落 0)。(b) `test_parallel_offrepo_scan_symlink_directory_is_listed_not_entered` — root 直下と部分木内部の symlink dir が `dirnames` として計数され (directories 計数は逐次版と同じ)、その先の固有候補は列挙されない。
- parametrize id は ASCII のみ。fixture に現行 hash を差し込むなどテストを甘くしない。揮発 payload を期待値へ焼き込まない。

**禁止:** `git add` / `git commit` / docs 編集 / `docs/handoff/` への file 作成 / `.claude/**` `hooks/**` 他の `tools/**` `conftest.py` の編集。実根 `/work/1/SFC/tanab/dev-wave-jobs` を走査しない。

## test の実走

`PYTHONPATH=. python3 orchestrator/tests/test_audit_dangling_commits.py` (末尾 `_run` = `pytest.main`) を走らせ、緑には実走件数を併記する。走らなければ「実装済み・未実走」と書き `closed` と書かない。実走できない場合は test module を import して新設 test を直接呼び (`tmp_path` は `tempfile.mkdtemp()`、`monkeypatch` は `pytest.MonkeyPatch()` で代用)、fixture 成立と、検査を一時除去したときの赤化まで確かめて報告する。

## 完了報告に必ず含める

- 変更 file と関数の一覧 (file:line、新設 / 改名した helper の名前と役割)。
- 実走した件数と結果。未実走があればそう書く。
- 既存 test の期待値を変えていないことの申告 (段 5 新設 test の中身変更は列挙)。
- 逐次版との等価性の論証 (1 directory 1 task、`onerror` 1 回、symlink dir、first-seen の key、入れ子 root) を 5 行以内で。
- 変異 matrix (裁定 §4 M0〜M9) の各変異について、新設計での対象 file:line (old の逐語 1〜3 行) と予想 killer。M2 は「sorted dirnames の末尾 1 個を queue に入れない」、M5 は「代表選択の key 比較を逆にする (最大 key を代表)」、M6 は「worker 例外を握りつぶして続行」、M7 は「worker から progress callback を呼ぶ」へ読み替える。

## 出力形式

**出力は file に書かず、最終メッセージの本文に全文を書け。** 見出しはすべて `##` (H2) で書き、最後の節は必ず `## 総括` とする。`### 総括` と書いてはならない。予算が尽きそうなら、その時点の結論を出力形式どおりに書いて終われ (無出力が最悪)。

節の順:

## 変更一覧
## 実走結果
## 期待値と等価性
## 変異 matrix の対象行と予想 killer
## 総括
