# 段 7 照合 (Claude opus、read-only 子 1 本、general-purpose) の報告 — 逐語

Codex が利用上限で使えないため、本 insight と worklog fragment の事実照合は Claude の read-only 子 1 本で行った (docs のみで実装面ではない)。以下は子の最終報告の逐語 (harness の行頭インデントだけを除いた)。所見 13 件は親がすべて real と裁定し反映した (README §7)。

---

## 不一致

1. **must-fix (事実誤り): 段 5 の author prompt は「そのまま再利用できる」ものではない**
   - 対象の記述: README 結論 2「段 5 の author prompt (`verbatim/s5-author-prompt.md`) もそのまま再利用できる」。§6.3 の「基にする…(例: 再開である旨と書きかけ file の所在の 1 段落を足す)」と、fragment の次の一手「`verbatim/s5-author-prompt.md` の bytes を変えて投入する」も、段落を 1 つ足せば済むように読める。
   - 一次資料の値: `codex/s5-author-prompt.md` には、この wave に固有の値が直書きされている。
     - 作業 worktree と所有 path が `/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2826-probe` (branch `author-t2826-probe`) に固定されている (15〜16 行、8〜10 行)。
     - 既定の出力先が `OUT_ROOT=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2826-shard-plugin-modify-timing/job-out` になっている (34 行)。
     - 仕様 file の置き場がこの wave の job dir を指している (4〜6 行)。
     - `acceptance_shards.py` / `conftest.py` の行番号が `d99c556df` 時点の値になっている (8〜9 行)。
   - README §5 自身が「branch は段 9 の撤去で退避される」と書き、§6.1 は tip を改めて固定するとしている。したがって、この prompt は path と行番号を差し替えないと使えない。「そのまま」を削り、差し替えが必要な項目を書くべき。

2. **must-fix (引用の言い過ぎ): 入口の規定は「段 4 から再開」であって「段 5 から」ではない**
   - 対象の記述: README §6.2 は「入口の『裁定後に別 context が段 4 から再開する型』として…段 5 から始める」。fragment も「再開は fresh wave で段 5 から」。
   - 一次資料の値: `.claude/commands/dev-wave.md` 27〜28 行は「裁定後に別 context が段 4 から再開する型は、変更面の骨格が同一なら前 wave の段 2・3 成果物を流用でき、再検査は段 6 レビューへ寄せる」。流用できるのは段 2・3 の成果物で、再開は段 4 から。段 4 裁定そのものを流用して段 5 から始めることまでは書いていない。
   - s4-ruling §7 (逐語) も同じ読み方をしているため、README は裁定とは一致している。ただし、根拠として挙げた規定の射程を超えている。修正案:「段 4 で本裁定 §3 / §4 を変えずに採り直し、段 5 へ進む」。

3. **should: 「計測値を 1 つも出していない」と、本文中の実測値が食い違う**
   - 対象の記述: README 4 行目「**本 wave は計測値を 1 つも出していない。**」と §7「計測値は 1 つも無い」。
   - 一次資料の値: 同じ README の §2 に「付随の観測」として `27033 tests collected in 57.34s`、pyc 784 / 370 が載っている (`verbatim/pyc-warm-wave.log` 末尾、`pyc-warm-wave.times`)。
   - 数量の言い方が過剰。「本題 (modify 複合区間の関数別計時) の計測値は 1 つも出していない」と限定すればよい。

4. **should: job-id が prompt の hash で決まるのは `--job-id` を省いた場合だけ**
   - 対象の記述: README §6.3 と fragment の「job-id は prompt の hash で決まるので、prompt の bytes を変えて (F411)」。
   - 一次資料の値:
     - `tools/dev_wave_codex.py` 237〜246 行では、prompt の hash から job-id を作るのは `--job-id` を省いたときだけ。
     - 本 wave の起動 script はどちらも `--job-id` を明示している (`codex/launch-s5-author.sh` の `--job-id t2826-s5-author`、`launch-s3-consult-1.sh` の `--job-id t2826-s3-consult-1`)。
     - fresh wave では `--wave` も artifact root も変わるので、成果物の dir はもともと別になる。
   - 理由を条件付きにするか、削る。

5. **nit: as-of の時刻 14:08:04 を、時刻を含まない file で出典づけている**
   - 対象の記述: README §1「as-of = 開始 gate の時刻 2026-09-21 14:08:04 JST (`verbatim/startup-gate.log`)」。
   - 一次資料の値: `startup-gate.log` の中身は INFO と OK の 2 行だけで、時刻を含まない。14:08:04 は原本の mtime と `handoff.md` にある。insight 側の写しの mtime は 14:37。同じ時刻を本文に書いている `verbatim/s1-brief.md` の 1 行目を出典にすべき。

6. **nit: §7 の参照先 §8 に、照合の記述が無い**
   - 対象の記述: README §7「本 insight 自体は段 7 で Claude の read-only 子 1 本の照合を受けた (§8)」。
   - 一次資料の値: §8 (dir の中身) には照合についての記述が無い。また、書いた時点では照合はまだ終わっていなかった。

7. **nit: fragment が、まだ行っていない段を「実行した」と書いている**
   - 対象の記述: fragment「段構成 (実行した順): … → 7 → 8 → 9」。
   - 一次資料の値: 書いた時点で段 8・9 は未実施で、段 7 は進行中。「予定を含む」と書き添える。

8. **nit: 残りの error 2 行は「起動器の定型警告」ではない**
   - 対象の記述: stop-evidence §3 (s4 §7 も同じ)「残り 2 行は起動器の定型警告」。
   - 一次資料の値: `attempt-0001.events.jsonl` の 2・3 行目は、`item.completed` の中の `item.type:"error"` で、トップレベルの error ではない。起動器 (`tools/codex_worker_launch.py:2065`) が付けた `--dangerously-bypass-hook-trust` に対して、Codex CLI が出した警告である。`"type":"error"` という文字列が 3 行に出るという件数そのものは正しい。

9. **nit: ユーザーへの通知は端末通知だけで、携帯へは届いていない**
   - 対象の記述: README 結論 1 と fragment の「ユーザーへ通知し」。
   - 一次資料の値: 親 session の会話記録 (`~/.claude/projects/-work-1-SFC-tanab-izanagi--claude-worktrees-dev-wave-t2826-shard-plugin-modify-timing/04a9e102-….jsonl` の 1088〜1090 行) では、通知の結果が "Terminal notification sent. Mobile push not sent (Remote Control inactive)"。送信は 14:35:57 JST で、前後の `date` 実測 14:34:32 / 14:36:47 の間に入っており、この時刻の記述は正しい。

10. **nit: 「凍結境界」の出典の付け方がずれている**
    - 対象の記述: fragment「凍結境界 (`docs/ai-provenance.md`) により」。
    - 一次資料の値: 「凍結境界」は `.claude/commands/dev-wave.md` 31〜35 行の節の名前である。`ai-provenance.md` 54〜55 行にあるのは「Codex が実行不能なら Claude は代行せず停止」という規則で、この用語は使っていない。

11. **nit: F411 の引き方が、取り消し追記を反映していない**
    - 対象の記述: README §7「F411 のとおり、表示どおりに復帰しない場合も」。
    - 一次資料の値: F411 の取り消し追記 (supersede、2026-08-20) は、「数分で自然回復した」のはアカウント切替による可能性が高いとしている。F411 が支えるのは「切替で早く使える場合がある」側だけである。

12. **nit: 「model 呼出し 9 回」は観測できた回数である**
    - 対象の記述: README 結論 1「model 呼出し 9 回」。
    - 一次資料の値: receipt は `model_calls_semantics: observed_token_count_events`、`possible_unobserved_overshoot: true`、`metering_status: missing`。9 回は観測値で、実際はこれを上回った可能性がある。

13. **nit: §1 と §6.1 で標本の時点の扱いが食い違って読める**
    - 対象の記述: README §1「この固定は再開 wave への引き継ぎ事項」。
    - 一次資料の値: §6.1 は「再開 wave の開始 gate で改めて固定する」。§1 は `d99c556df` / 14:08:04 を引き継ぐとも読める。

## 照合して一致したもの (約 140 項目)

- **receipt・events・log (約 25 項目): すべて一致。**
  - receipt の attempt 1: `codex_exit_code`=1、`failure_class`=f45_missing_output、`model_calls`=9、`output_bytes`=0、`wall_clock_s`=513.954562833、input 425575 / output 16254 tokens、`accepted`=false。receipt の sha256 と mtime 14:33:16。
  - events の sha256 と末尾 2 行の逐語 (曲がった引用符を含む)。`"type":"error"` を含む行は 3 行で、警告の本文も逐語で一致。
  - `s5-author.done`=1、`s5-author.log` と `s5-author.wait.log` の全文。
  - 待ち手の終了コード 70 (会話記録の "failed with exit code 70")。
  - 終端 commit `31894443efd6…` と、branch の参照 file の値。
  - launcher の引数 4 点 (job-id、stage と sandbox、repo-root、max-model-calls 400)。
  - 起動 14:24:40 (pid の mtime)、終了 14:33 (events 14:33:14 / receipt 14:33:16)。
- **書きかけの 3 file (13 項目): すべて一致。** `partial-author/` の実物を数え直した。
  - 178 行 / 7683 bytes、530 行 / 20837 bytes、584 行 / 29446 bytes、合計 1,292 行。sha256 も 3 本とも一致。
  - 子 worktree 側の原本の sha256 とも一致。
  - 子が触った file は events 上もこの 3 本だけ。実行したコマンドは cat / sed / rg と生成用の python だけで、構文検査もテストも走らせていない。したがって「未検査」は正しい。
- **T-2817 / T-2617 から引いた値 (16 項目): すべて一致。**
  - T-2817: S2 45.66 / 45.55、S3 44.68 / 44.79、sys 80 → 2108 (S1-a → S2-a)、`intent_lock` 5.20 M → 60.9 M (11.7 倍)、26,407 件、`2afb39768`。sys +2027 秒は同 README 138 行。memo の終了時刻が計時点に含まれていないこと (35 行)。
  - T-2617 §3.2: user +1.74 秒、sys 1.37 → 3.09 秒、login で実行 (118 行)。§4 の判定。
- **pyc の温めと test file 数 (9 項目): すべて一致。**
  - 14:25:10〜14:26:34、rc 0、27033 件 / 57.34 秒、pyc 784 / 370。log 末尾の写しは原本の末尾 5 行と sha256 が一致。
  - `orchestrator/tests` 配下の `test_*.py` は 369 本。
- **行末空白の正規化の記録 (9 項目): すべて再計算で一致。**
  - 原文と写しの sha256・bytes (17251 / 17167)、42 行、行番号の列、どの行も半角空白ちょうど 2 個 (3 個以上もタブも 0)。
  - 原文から行末空白を除いたものの sha256 が、写しの sha256 と一致。
- **逐語の写し 9 本: すべて原本と sha256 が一致。** prompt の sha256 は receipt の `prompt_sha256` とも一致。
- **段 4 裁定が「結果を見る前に確定した」ことの裏付け: 一致。**
  - author 子が 14:24 台に読んだ時点の裁定本文 (events 7 行目の出力) と、現行の裁定から §7 を除いた部分の sha256 が一致した。§1〜§6 は後から変わっていない。brief も同様に変わっていない。
- **段 3 相談: 一致。** 所見 9 件 (高 4・中 5)、判定「修正後 GO」、「(c) 条件付きで scope 内」。相談子の rc 0、`check_codex_output` rc 0、model gpt-6-astra / medium / lane sol / read-only、2 レンズを 1 本で担当。README §3 の各所見の要約も裁定 §1 と一致。
- **時刻: 一致。** 依頼 14:03、開始 gate 14:08:04、T-2825 の 13:55 時点の状態 (7 走を終え、最終受入 → land の段)。
- **数量・断定の表現: 一致。**
  - 計算ノード job 0 本: `run-probe.sh` の pid / times / log も、probe/ dir も存在しない。
  - T-2825 と区間が重ならない: T-2825 の 14 時台の活動は最終受入だけ。
  - refuted 0、全件 real・採用、自動の再投入なし (attempt は 1 回だけ)、midflight gate の rc 1 → rc 0。
  - 子 worktree の起点 `d99c556df` と lock。
  - D582・F411・`ai-provenance.md` 54〜55 行の内容。
- **fragment の形式: 問題なし。** frontmatter の 6 key、題に引用符なし、`## 本文` と `## 次の一手差分` の 2 節、`### 更新` の item に `base:` 行、末尾の改行、行末空白 0。fold の dry-run が計画した content_sha256 は現行の file と一致。

## 照合できなかったもの

- N1 の「対象 3 file の差分 0 行 / 台帳 +434 行 (`b820bbaa7`)」。git が使えないため。
- N2 の「受入 worktree の test path は 11 component」。受入を実際に走らせる path が一次資料に無い。
- 「計算ノード job 0 本」は、wave dir に痕跡が無いことまでしか確かめていない。NQSV への照会はしていない。
- 「repo の実装面の差分ゼロ」は、会話冒頭の git status の写しと、insight に Python / shell file が無いことまでで確かめた。
- 「段 9 の撤去で evidence bundle へ退避される」は、これから行う作業の記述なので確かめようがない。

## 総括

must-fix は 2 件 (1: author prompt の「そのまま再利用」、2: 再開を「段 5 から」とする記述)。どちらも再開手順の文言を直すだけで済む。数値・hash・逐語・件数には誤りが見つからなかった。判定は **修正後 GO**。should の 2 件 (3: 「計測値を 1 つも」の限定、4: job-id の理由) も同じ機会に直すことを勧める。
