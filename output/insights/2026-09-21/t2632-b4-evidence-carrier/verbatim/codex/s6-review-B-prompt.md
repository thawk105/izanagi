単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier

必読事項の射影: (下記をすべて読む。読めなければ即停止し、読めなかった path を報告する)

- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/verbatim/stage4-ruling.md — 段 4 裁定とプラン v2 (実装の正本)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/verbatim/request.md — 依頼の逐語。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/verbatim/d2194-item3.md — 裁定の逐語。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/codex/a.patch — 実装子 A の差分 (side channel)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/codex/b.patch — 実装子 B の差分 (caller)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/codex/s5-author-A.md — 実装子 A の最終報告。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/codex/s5-author-B.md — 実装子 B の最終報告。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/focus-f1.log — 親の焦点走 (計算ノード、33 file) の生 log。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/campaign/p3_s4_loop.py — 統合後 (commit `ec6459863`)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/campaign/p3_b4_prerun_caller.py — 統合後。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/tests/test_p3_s4_loop.py — 統合後。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/tests/test_p3_b4_prerun_caller.py — 統合後。読めなければ即停止

## レンズ B: 過剰・削除・scope (DW-S03 の過剰・削除レンズに固定)

実装を守らせず検査する。依頼と D2194 項 3 の 4 項・段 4 裁定のプラン v2 に対し、余計なもの・削れるもの・足りないもの・局所修正で足りるものを探す。
攻撃面に `docs/failures.md` の型タグ [手順漏れ] [権限逸脱] [consumer 取り残し] [防壁の射程誤認] を含める。各項目を real / refuted で判定し根拠 (file:line) を示す。

1. **過剰:** 裁定が求めない機能・検査・分岐が入っていないか (例: `.corrupt.*` が残る限りの再開拒否、schema / axis の header 検査、directory fsync、
   `initial_proposal_sha256` 引数の型検査、module docstring への追記)。それぞれ放置すると何が起きるか、削ると裁定のどの要件が欠けるかで判定する。
2. **scope 外の混入:** admission 検査・reference 欄・caller の side channel 読み・sort / trigger への展開・台帳・gate が混ざっていないか。
   base report が「certified の証明」「適格行」と読める説明になっていないか。
3. **test の過剰と重複:** 追加 test (side channel 19 関数、caller 2 関数 + parametrize 5 件) に、同じ性質を二重に検査するもの、機構を通らないもの、
   裁定 §3.3 が「作らない」とした test の再来が無いか。test の所要が全体 5 分の上限を圧迫しないか。
4. **削除・非接触:** 既存 test の assertion の削除・緩和、既存 fixture の書き換えが必要最小か。loader stub 3 箇所の追従は既存の意図を保つか。
   凍結事前登録・whiteboard 型・sort / trigger driver・`campaign_lock.py`・共有 fixture に触れていないか。
5. **説明の正確さ:** docstring・comment (P4 の限定、参照点の定義、caller の不足分類の限定) が実コード・裁定・凍結事前登録と食い違っていないか。
   「回復可能」「全件」「証明」など過大な語が無いか。
6. **焦点走の結果:** `focus-f1.log` の失敗・error・skip のうち、過剰な実装や過剰な test が原因のものがあるか。

## 制約

- sandbox は read-only。**静的検査と log の読解だけでよい。** テストの実走は親が行う。実走していないことを「確認した」と書かない。
- 新しい gate・検査・台帳を提案する場合は scope 外と明記して分ける。
- 予算が尽きそうなら、途中までの結論を下記の出力形式どおりに書いて終える。

## 出力形式

項目 1〜6 を見出しで分け、各項目に判定 (real / refuted)、must-fix / should-fix / nit の別、根拠、放置時に成果物 (B-4 の適格行・参照点・台帳・
certified 判定) がどう変わるかを 1 行で書く。最後に `## 総括` を置き、GO / NO-GO を明記する。
