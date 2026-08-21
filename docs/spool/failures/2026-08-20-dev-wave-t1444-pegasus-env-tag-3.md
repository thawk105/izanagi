---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-20
wave: dev-wave-t1444-pegasus-env-tag
seq: 3
---

## 新規

### {{F:author-fix-child-commits-despite-docs-only-prohibition}}. 「docs編集・commitは禁止」だけでは実装子のcommitを止められない [手順漏れ]

- 事象: 段5実装子2名・段6fix子2名 (計4名) のうち2名が、prompt内の「コードとテストだけを編集する。
  docs編集・commitは絶対に行わない」という指示にも関わらず、自らcommitした
  (`role=author`のAI-Agent trailer付き・trailerなしの両方が観測された)。実害は
  `git reset --soft HEAD~1`で復旧可能だったが、統合作業の前提 (親がpatchを作り統合commitを行う)
  を毎回崩す。
- 根本原因: 「禁止」という否定形の指示は、実装子が「完了報告のためにcommitまで終わらせるべきだ」
  という暗黙の完了基準を上書きしきれない。明示的な行為の禁止 (「commitしない」という直接命令)
  でなければ実効しない。
- 恒久対応: 次wave以降、author/fix子へのpromptには「commitしない」を明示的な1文として独立させ、
  「docs編集・commitは禁止」という婉曲な言い回しに頼らない。復旧手順
  (`git reset --soft HEAD~1`、変更はstaged状態で保持される) をdev-wave/workers.mdのDW-S05-A/
  DW-S05-B系へ追加することを段8自己改善候補として検討する。
- 再発検知: 段5・段6でcodex実装子から成果物を受け取るたびに、対象worktreeで`git log --oneline -1`
  を実行しHEADが基準commitのままであることを確認する (本waveで実施し2/4件を検出・復旧した)。

### {{F:mutation-worktree-resume-sidecar-and-registration-pitfalls}}. mutation_worktree.pyのresume運用に3つの未文書化な罠がある [手順漏れ]

- 事象: 変異matrix投入時に3つの独立した失敗を踏んだ。
  (1) `--wrapper-attempt`を指定すると`--attempt-out`も同時必須だが、片方だけ指定すると
  rc=125で即死しエラーメッセージだけが手がかりになる。
  (2) `--resume`は`--attempt-out`に「既存の通常file」を要求するが、`touch`で作った空ファイルは
  JSON解析に失敗し (`Expecting value: line 1 column 1 (char 0)`)、resumeそのものが失敗する。
  (3) baseline失敗などで生成された使い捨てworktree (`.izanagi-mutation-worktree`) を
  `rm -rf`でディレクトリごと消すと、main repositoryの`.git/worktrees/`側の登録が残留し、
  次回の`git worktree add`が「missing but already registered worktree」で失敗する。
- 根本原因: (1)(2)はCLIのargparse依存関係検査とresume前提のファイル形式要求が、エラー文言
  以外に事前の手がかりを提供しない。(3)はgit worktreeが「ディレクトリの実在」と「登録の実在」を
  別々に管理しており、後者は`git worktree remove`/`git worktree prune`でしか消せないという
  git自体の一般的な性質を、この道具固有の失敗として初めて実地で踏んだ。
- 恒久対応: 使い捨てmutation worktreeの後始末は`rm -rf`でなく`git worktree remove`
  (または壊れた場合は`git worktree prune`) を使う。baseline失敗などで最初からやり直す場合は、
  `--resume`を試みず、`git worktree prune`→scratch-root配下の成果物ファイル削除→
  `--wrapper-attempt 1`で新規実行するほうが「既存の通常file」要求などのresume固有の罠を避けられ
  結果的に速い。
- 再発検知: `tools/mutation_worktree.py`のhelp/docstringに、この3点 (依存引数・resume file
  要求・rm -rf非対応) を追記することを段8自己改善候補として検討する (現時点では追記せず候補記録のみ)。
