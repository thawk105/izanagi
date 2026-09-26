単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy

必読事項の射影 (読めなければ即停止し、読めなかった path を書いて終われ):
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy/s4-ruling.md — **段 4 裁定 (plan v2 と事前登録)。これが仕様の正本。**
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy/s1-brief.md — 段 1 brief (背景。s4-ruling と食い違う所は s4-ruling が優先)。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy/codex/s3-consult-a-out.md、s3-consult-b-out.md — 段 3 相談 (裁定済み)。
- 第 4 回診断: /work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe/output/insights/2026-09-23/t2273-shard0-bottleneck-4/README.md と同 dir の verbatim/s4-ruling.md。
- 対象コード (編集禁止、読むだけ): /work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe/orchestrator/tests/test_s8b_oracle_driver.py (`_copy_git_visible_output` 847、`_T080SharedBases` 920、`_t080_join_shared_bases` 974〜992、builder `_build_t080_stub_free_e2e_repo` 1437、複製呼出し 1458、発行 child 1564〜1710、`subprocess.run` 1712〜1724、別 child 2527 は対象外)、/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe/orchestrator/tests/conftest.py (`_early_memo_selected` 2368、`_start_early_memo_job` 2388、`pytest_configure_node` 2583)。

## 作業

作業木は /work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe (branch `author-t2273pc-probe`)。**所有 path はこの 3 file だけ:** `tools/t2273_replica_runner.py`、`tools/t2273_replica_plugin.py`、`tools/t2273_replica_analyze.py`。それ以外 (production・test・conftest・docs・台帳) は 1 byte も変えるな。commit はするな (起動器が終端で記録する)。

1. 出発点を取り出す: 作業木で `git show 7f38ac7fd:tools/t2273_replica_runner.py > tools/t2273_replica_runner.py` (plugin・analyze も同様)。これは第 4 回診断で実走済みの probe である。
2. s4-ruling.md §2 plan v2 と §3 事前登録を実装する。要点:
   - **runner:** 新 mode `ab` (`--order AP|PA`、`--smoke none|both`)。smoke は既存と同じ `-k shared_base_builds_real_builder_once_across_processes -n 2 --dist loadgroup` を A 形・P 形で 1 回ずつ。本走は既存 `replica()` と同じ argv・guard (clean・HEAD・others・stale_pytest・一時 dir 掃除・/tmp quota の記録) で条件 A (観測のみ) と P (env `T2273_PRECOPY=1`) を order の順に走らせる。既存 mode (`run`・`pair`) は残してよいが、`ab` は staging・X を使わない。1 条件が rc≠0 でも、もう一方は走らせて記録する (有効性は analyzer が判定)。
   - **plugin (両条件共通):** 既存 span・資源標本をすべて維持。追加: (i) builder の複製呼出しの直後に `root/output` の stat digest (相対 path・size・mode・mtime_ns を sort して sha256) と件数を別 span `copy.digest` で記録。(ii) 発行 child の**計測用 code 変換**: `subprocess.run` の argv が `[sys.executable, "-I", "-B", "-c", <child>, ...]` で child が builder の child (例: `migration.draft_receipt(` と `activate T080 receipt` を両方含む) のときだけ、child の各段 (import 群と runtime module 読込み、runtime source の HEAD 照合 loop、basis の rev-parse、draft_receipt、validate_draft、finalize_receipt、git add (+extra)、git commit、verify_receipt、gate_check) の壁時間・`time.process_time()`・`resource.getrusage(RUSAGE_CHILDREN)` を記録し、**stderr へ識別行 1 行** (例 `T2273_PUBLISH_PHASES <json>`) で出す。stdout の document JSON、`-I -B`、`_CurrentSourceLoader` の検査、`sys.path` の検査、既存 assert は一切変えない (元の文を順に実行する形を保つ)。wrapper は変換後の child を 1 回だけ実行し、戻り値をそのまま返し、stderr の識別行を解析して span に記録する。変換できない (目印が見つからない) ときは変換せず record-error を残す。(iii) timeline event: controller の `pytest_configure_node` 初回時刻、早期 memo job の開始・終了 (conftest の関数を観測 wrapper で包めるなら。包めなければ未計測と記録)、各 worker の collection 完了、各 builder の開始。
   - **plugin (P のみ、対照用の差し替えであり観測 wrapper ではないと docstring と span に明記):** controller (workerinput を持たない config) の `pytest_configure_node` 初回で非 daemon thread を起こす。identity = `sha256(json.dumps([str(ROOT), testrunuid]).encode())` (ROOT は test module の ROOT と同じ実 repo root、testrunuid は `node.workerinput["testrunuid"]`)。置き場 = `Path(tempfile.gettempdir()) / f"t2273-precopy-{identity}"` (worker の共有置き場とは別)。thread は test module の実関数 `_copy_git_visible_output(ROOT, <置き場>/output)` を 1 回呼び、成功で `ready.json` (戻り値の可視集合の sha256 と件数、開始/終了 epoch、thread の CPU 時間) を pending → rename、失敗で `failed.json`。controller の `pytest_unconfigure` で join してから置き場を削除し、所要を記録。worker 側は builder が `_copy_git_visible_output(source_root, destination)` を source_root = 実 repo root で呼ぶときだけ、「`ready.json` を待つ (待ち span、`failed.json` か上限超過なら例外 = P 無効、上限は有限で walltime より十分短く、値を記録) → `shutil.copytree(<置き場>/output, destination)` (既定の copy2) → 写しの可視集合を返す」に置き換える。fallback で直接複製してはならない。worker 側の identity 計算は `PYTEST_XDIST_TESTRUNUID` から同じ式で行い、controller と一致しない場合は例外。
   - **analyzer:** 新 `--ab-dir <out>` (1 job の A/P 対) と `--ab-series <dir1> <dir2> <dir3>` (3 job 集計)。s4-ruling §3 の有効性の全項目と判定量 (Δ_i、r_i、O_max・L・pre・post の対差、条件別中央値、順序別対差、写しの開始・完成と最初の builder 開始の差、builder の写し待ち、key 別の builder 構築時間、発行 phase 内訳 (key 別・条件別)、早期 memo の所要と超過件数) を JSON と markdown に機械出力し、§3.3 の基準の成否を「満たす / この基準では確認できない」で出す。既存 `--pair-dir`・`--run-dir` の出力は変えない。
3. 自己検査: 3 file の `python3 -m py_compile`。analyzer は第 4 回の出力形を模した小さな合成 fixture (repo 外の一時 dir) で `--ab-dir` と `--ab-series` を走らせ、有効性判定が崩れる入力 (digest 不一致、ready 無し、rc≠0) で「無効」になることを確かめる。plugin の child 変換は、builder の child 文字列を test module から読んで変換し、`compile()` が通り、元の文の順序が保たれることを静的に確かめる。**login では pytest の実走が hook で拒否されうるので、test suite は走らせなくてよい。実走できなかった検査は「実装済み・未実走」と書け。**

## 守ること

- production・test・conftest・台帳・docs は変えない。受理集合を変えない (規律 2)。既存 test の期待値は変えない。
- 観測 wrapper は実物へ同じ引数を 1 回渡す。P の差し替えと child の code 変換はそれぞれ「対照用の差し替え」「計測用 code 変換」と明記する (観測 wrapper と呼ばない)。
- 仮想リスク向けの gate・検査・一般化は足さない。s4-ruling にない機能を足さない。
- 所有外 caller・共有 fixture への波及を報告に静的列挙する。

## 出力形式

- `## 変更` (file ごとの要点と主要な関数名)
- `## 自己検査` (実走したもの / 実装済み・未実走のもの、コマンドと結果)
- `## 限界・未解決` (P の置き換えが効く builder 呼出し箇所、早期 memo の観測可否、child 変換の目印など)
- `## 総括` (3〜6 行)
