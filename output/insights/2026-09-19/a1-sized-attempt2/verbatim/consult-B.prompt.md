単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dw-a1-sized-attempt2

必読事項の射影:
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-a1-sized-attempt2/brief.md (親の段 1 brief。点検対象そのもの。読めなければ即停止)
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-a1-sized-attempt2/materials/t1505-scripts.sh (attempt-0001 を投入した 4 script の逐語: hydrate / submit / complete / materialize。読めなければ即停止)
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-a1-sized-attempt2/materials/t1505-adjudication.md (attempt-0001 wave の段 4 裁定。読めなければ即停止)
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-a1-sized-attempt2/materials/code-run-submit-head.py (submit の事前検査の抜粋。読めなければ即停止)
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-a1-sized-attempt2/materials/code-barrier-head.py (bench 前 barrier の signature 抜粋、timeout_s=600。読めなければ即停止)
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-a1-sized-attempt2/materials/code-parent-porcelain.py (clean tree 検査の抜粋。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dw-a1-sized-attempt2/output/insights/2026-09-18/t1505-a1-sized-attempt1/README.md (attempt-0001 の投入記録。§2・§3 を必ず読む。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dw-a1-sized-attempt2/docs/paper-story/results/2026-09-18-a1-balanced5-sized-attempt1-descriptive.md (attempt-0001 の results 稿。§1.4・§2.5・§4・§5 を読む。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dw-a1-sized-attempt2/output/insights/2026-09-13/paper-story-a1-balanced5-sized-preregistration/README.md (事前登録。§2.1・§6 を読む。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dw-a1-sized-attempt2/tools/pegasus/paper_story_a1_paired.sh (job body。preflight・依存 build・barrier 周りを `grep -n` で索引して読む。全文は読まない。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dw-a1-sized-attempt2/docs/failures.md (`grep -n "^## F1\b\|^## F36\b\|^## F29\b\|^## F1\.\|^## F36\.\|^## F29\."` で F1 / F29 / F36 の見出しだけ索引し、該当節だけ読む。読めなければ即停止)

上の射影以外は、必要になった箇所だけを `grep -n` で索引して読む。全文を読み込まない。
書込可能な tmp は無い。pytest の実走は求めない (静的検査でよい)。テスト実測は親が行う。
予算が尽きそうなら、その時点の結論を下の出力形式どおりに書いて終われ (無出力が最悪)。

## 目的

これは自分たちの計測手順の設計レビューである。paper-story A-1 balanced5 sized 本走 attempt-0002 を、ユーザー裁定
(2026-09-19、brief に逐語) に従い既存 submit 経路で 1 attempt だけ投入する。認可は 1 attempt で、どの層で落ちても
再投入しない。したがって**手順の欠落・順序誤り・環境要因で 1 回きりの attempt を無駄にする経路**を事前に潰すことが
この点検の目的である。brief 自身も点検対象である。親の実測値とその一般化を疑え。

## レンズ B — 実効性・手順の欠落・過剰

次を点検し、所見ごとに **real / refuted / 根拠不足** を付け、根拠の file:line を示せ。

1. **投入手順の完全性。** attempt-0001 の手順 (T-1505 §2.1: submit-tree = local main の detached worktree + submodule 再帰初期化
   + `git worktree lock` → hydrate 2 箇所 (既定 staging root と job dir の `--third-party-source-root`) → submit → 監視 →
   complete → materialize) を attempt-0002 で再現するとき、brief と script に欠けている前提・順序は無いか。
   特に: (a) hydrate cache `/work/1/SFC/tanab/izanagi-thirdparty-cache` の実在と pin 一致の確認、(b) submit-tree の
   `status --porcelain --untracked-files=all --ignore-submodules=all` が 0 行であること (hydrate の既定 staging root は gitignore 済みか)、
   (c) CCBench submodule の tracked-clean と canonical pin、(d) `--expected-head` と submit-tree HEAD の一致、
   (e) attempt root の親 dir (durable base) の実在と権限、(f) job body の preflight が HEAD / dirty で見るもの。
2. **1 回きりを無駄にする環境要因。** bench 前 barrier は 3 job の ready を 600 秒以内に要求する。gen_S の queue 待ちで
   1 job だけ遅れる場合、他 2 job が barrier timeout で落ちる。brief の「149 host 中 65 idle だから即時開始が見込める」という
   一般化は妥当か。投入直前に何を実測すべきか (qstat -Q の QUE 件数・自分の他 job・時間帯)。落ちたときに
   `scheduler-or-infrastructure-failure-before-bench` として事前登録 §6.4 の再走理由に該当しても、ユーザー裁定で再投入しない
   ことの記録の形。
3. **記録・稿の一次資料束縛。** 成果物 (results 稿・記録 insight) が F1 (日付・hash・件数は一次資料から)、F36 (hash 自己参照)、
   F29 (模擬で裁定しない) の型を踏まない構成になっているか。brief の成果物 (1)〜(4) に過不足は無いか。「2 attempt の並記」を
   表で行うとき、D1993 項 6 (プール禁止) を守りつつ読める形は何か (集計語・平均・勝敗の禁止語を列挙せよ)。
   materialize が拒否された場合、attempt-0002 の権威 bytes を repo 内に置く経路 (受領証・raw result.json の byte 複製 + sha256)
   と、置けない場合 (guard 拒否) の代替 (原文 path + sha256 の引用) のどちらを既定にすべきか。
4. **過剰・削除。** brief の scope に、研究前進 (反復間の再現性の観察) に不要な成果物・手順・検査が入っていないか。
   逆に、後で「やっておけばよかった」になる最小の追加 (例: attempt-0002 の job 開始時刻と queue 待ちの記録、
   attempt-0001 との条件照合表の項目) は何か。図を作らない (P3) の当否。

## 出力形式 (見出しは全部 `##`。最後の節は必ず `## 総括` で、`### 総括` と書いてはならない)

## 所見
番号付き。各所見に real / refuted / 根拠不足、根拠 (file:line)、放置時に成果物 (results 稿・記録・台帳) の値・受理集合・参照が
どう変わるかを 1 行。

## 投入直前チェックリスト
親が投入直前に実測すべき項目を、1 項目 1 コマンド (複合 shell にしない) で列挙する。

## 段 4 への提案
採用すべき変更 (brief の文言・手順・稿の書き方) を箇条書きで。scope 外の所見は「裁定パッケージ候補」と明記して分ける。

## 総括
3〜5 行。
