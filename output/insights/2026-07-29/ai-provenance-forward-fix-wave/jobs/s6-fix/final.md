## 総括

変更対象は [check_ai_provenance.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/tools/check_ai_provenance.py) と [test_check_ai_provenance.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/orchestrator/tests/test_check_ai_provenance.py) の2ファイルだけです。

- correction を raw物理1行、隔離 `--no-divider` canonical parse、隔離 default-divider final block の三層で検証し、`---` で `AI-Agent` と分断された反例を拒否しました。
- key を単一定数へ集約し、payload は `spec.target` と固定 evidence fields から生成します。`CorrectionAudit.exact` は findings の集約となり、raw exactness の重複判定を除去しました。
- `forward-corrected=1` は全 findings が空の rc=0 時だけ出力します。
- `_commit_exists` は `git cat-file --batch-check` の machine-readable recordを使用し、missing objectだけを `False`、Git backend異常を rc=2 に分類します。
- merge preflightと履歴監査を、全 parent と異なる path の積集合へ統一しました。sideから持ち込まれただけの実装pathは除外し、全parentと異なるresolutionは検出します。非first-parent側の既存correction、malformed/read-errorの `MERGE_HEAD` も固定しました。
- production targetの通常findingが exact missing 1件だけであること、複数tip、target ancestry外、raw whitespace、divider分断などを回帰固定しました。

実走結果:

- `python3 -m pytest -q orchestrator/tests/test_check_ai_provenance.py` — **116 passed in 5.30s**
- `python3 -m py_compile ...` — rc=0
- `git diff --check` — rc=0
- production checker — **533件中1違反、rc=1**。findingは固定target `6b64d21…` の `AI-Agent trailer がない` だけです。correction commit前なので、これは期待値でありgreenとは扱っていません。

scope内の未達はありません。所有外のdocs、output、handoff、他test/helper、commit、pushには触れていません。既存の未追跡 wave outputも不変更です。Stage 6焦点再レビュー・mutation matrix・親受入、Stage 7のO17/docs更新とcorrection commit作成は親の所有として残しています。