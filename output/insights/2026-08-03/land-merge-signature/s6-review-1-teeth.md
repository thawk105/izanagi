静的レビューの判定は **NO-GO** です。テストは実行しておらず、緑は主張しません。

## blocker 所見

### 1. real — cutoff 未指定経路の受理集合は、timeout を含めると現行同一ではない

裁定は「**渡されない呼び出し経路は現行挙動 (全 parent 走査) を保つ**」および「**受理集合を変えない**」です（[ruling.md:30](/work/1/SFC/tanab/izanagi-jobs/9aba3998/land-fix/ruling.md:30)、[ruling.md:46](/work/1/SFC/tanab/izanagi-jobs/9aba3998/land-fix/ruling.md:46)）。

差分集合は同じですが、旧実装の commit 当たり 1 subprocess に対し、現況は次の数になります。

- non-merge/root: `_commit_parents` + `_commit_diff` = 2
- cutoff なし、parent 数 `p` の merge: `1 + p`
- cutoff あり・trusted 一意: `p + 2`
- cutoff あり・trusted 0/複数: `1 + 2p`

根拠は [git_state.py:670](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:670) の parent 取得、全 parent ancestry、tree-diff ループです。全体で共有する 30 秒 deadline は [git_state.py:36](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:36) と [git_state.py:824](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:824) にあります。

schema v2 は landed commit を最大 1000 件許します（[schema_v2.json:104](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/schema_v2.json:104)）。no-fold の場合:

- 1000 linear commits: 旧 1002 → 新 2002 subprocess
- 1000 個の 2-parent merge: cutoff なし 3002、trusted 一意 4002、曖昧 5002
- fold ありは各値に +1
- parent 数に上限がないため、コード上の厳密な最悪値は有限でない

checker は残り総 deadline と 30 秒の小さい方（[checker.py:127](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/checker.py:127)、[checker.py:543](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/checker.py:543)）、daemon recovery は 5 秒（[daemon.py:1526](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/daemon.py:1526)）です。したがって、Git がすべて成功するという抽象条件下では同じでも、実際の受理集合は過剰縮小します。実装報告自身も subprocess 増加を認めています（[impl.md:48](/work/1/SFC/tanab/izanagi-jobs/9aba3998/land-fix/impl.md:48)）。

成果物影響: 正規 schema-v2 wave が `fold-commit` failure／recovery rejection／land timeout となり、canonical 3 台帳・FOLDED 参照・後続 certified 選択とレポートが生成されない、または旧 HEAD のまま残ります。

### 2. real — ancestry と「全 parent 走査」を新設テストが逐語では固定していない

次の壊し方が関連新設テストを通過します。

- ancestry 判定を `parent == cutoff` に縮退させる。
  - 正例では trusted parent と cutoff が同一 SHA（[test_dev_waves_git_state.py:422](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:422)）。
  - octopus fixture では proper ancestor と cutoff 自身の 2 trusted parent があるものの、cutoff→result にも削除署名があるため、誤って cutoff だけを選んでも同じ拒否になります（[test_dev_waves_git_state.py:539](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:539)）。
- trusted 0 個で全 parent ではなく先頭 parent だけを見る。
  - `test_merge_without_trusted_parent_rejects_resolution_signature` は `_seed_pending` 後に両 branch を作るため、削除署名が両 parent から見えます（[test_dev_waves_git_state.py:511](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:511)）。先頭だけでも緑のままです。
- `len(parents) >= 3` を無条件で全 parent 走査にする。
  - unique-trusted octopus の正例がなく、[test_dev_waves_git_state.py:539](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:539) はその壊し方でも緑です。

つまり受理集合の純増を直接固定するのは 2-parent の `test_landed_interval_allows_main_fold_merge_from_trusted_cutoff` だけです。他の merge 負例は旧実装でも拒否され、fallback の「全 parent」という量化までは証明していません。

成果物影響: proper-ancestor／unique-trusted octopus が過剰拒否されて台帳を land できないか、逆に zero/multi-trusted merge の一部 parent にだけ存在する隠れ fold 署名を受理し、FOLDED と canonical 台帳の参照が食い違います。

### 3. real — 事前登録した恒真変異の kill 理由が成立しない

質問の焦点については、懸念自体は **refuted** です。`_is_ancestor` を恒真化しても正例は緑のままになりません。

2-parent merge では両 parent が trusted となり、`len(trusted) == 1` が偽なので全 parent へ戻ります（[git_state.py:685](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:685)）。wave parent との差分に fragment `D`／FOLDED `M` が再出現し、[test_dev_waves_git_state.py:422](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:422) の正例が赤になります。

一方、裁定の変異 #1 は「恒真化 → fragment を落とす負例が緑」と逐語で事前登録しています（[ruling.md:53](/work/1/SFC/tanab/izanagi-jobs/9aba3998/land-fix/ruling.md:53)）。その因果は誤りで、実際には fail-open でなく過剰拒否です。変異 #8 の正例拒否と検出理由が重複し、祖先判定の fail-open 感度を証明しません。

成果物影響: 実装の現在の受理集合は変わりませんが、このまま記録すると変異 matrix・材料レポート・台帳の failed-node／kill 理由参照が事実と異なります。

## 仕様適合

| 契約 | 判定 | 根拠 |
|---|---|---|
| plan v2-1: `commit-diff` から `-m` 削除 | 一致 | [git_state.py:90](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:90) |
| plan v2-2: 0/1、trusted 一意、0/複数の三分岐 | 実装は一致 | [git_state.py:677](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:677) |
| plan v2-3: cutoff は明示 keyword、未指定は全 parent | 論理的には一致、timeout 面で不一致 | [git_state.py:796](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:796) |
| 不変条件 1: 二署名・path 集合不変 | 一致 | classifier は未変更の [git_state.py:561](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:561) |
| 不変条件 2: `test_n31` を残す | 一致 | [test_dev_waves_git_state.py:408](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:408) |
| 不変条件 3: 既存拒否を緩めない | 差分上は一致 | commit は既存テストを変更せず純増 |
| 不変条件 4: cutoff なし受理集合不変 | **不一致** | subprocess/deadline による過剰拒否 |
| 不変条件 5: octopus は trusted 一意時だけ限定差分 | 実装は一致、テスト不十分 | [git_state.py:696](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:696) |
| 不変条件 6: Git rc・複数出力 fail-closed | 実装は概ね一致 | [git_state.py:177](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:177)、[git_state.py:634](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:634) |

## `-m` 削除と caller

`_commit_diff` の残る本番呼び出しは 2 箇所だけです。

- landed commit: parent 数 `< 2` の分岐内（[git_state.py:680](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:680)）。
- fold commit 形検査: 直前の `_commit_shape` が parent 数をちょうど 1 に限定します（[git_state.py:741](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:741)、[git_state.py:853](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:853)）。

したがって merge fold commit が `_commit_diff` に渡って空差分で素通りする経路はありません。merge は先に `header` で拒否され、既存テストもその形を保持しています（[test_dev_waves_git_state.py:604](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:604)）。

land の 4 分岐はすべて `tested_main` を渡しています。

- active fold recovery: [dev_wave_land.py:1783](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_wave_land.py:1783)
- no-fold: [dev_wave_land.py:1823](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_wave_land.py:1823)
- already-landed + fold: [dev_wave_land.py:1879](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_wave_land.py:1879)
- fresh ff + fold: [dev_wave_land.py:1939](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_wave_land.py:1939)

checker と daemon は cutoff を渡していません（[checker.py:543](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/checker.py:543)、[daemon.py:1526](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/daemon.py:1526)）。成功した Git 観測だけを比較すれば旧 `diff-tree -m C` と新しい parent ごとの `diff-tree P C` は同じ拒否集合ですが、deadline 面では blocker 1 の差があります。schema v1 の helper 迂回は変更されていません。

成果物影響: `-m` 削除そのものによる fold commit の誤受理はありません。land の cutoff 渡し漏れも現況にはありません。

## fail-closed 照合

| 入力・事象 | 現況 |
|---|---|
| Git rc≠0 | `_run` が `DevWavesError`。空差分には変換されない |
| `_is_ancestor` rc=0/1/その他 | true / false / 例外。新経路でも契約維持（[git_state.py:506](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:506)） |
| parent 空出力・複数行 | `_parse_commit_parents` が拒否 |
| parent 非 ASCII・不正 SHA | 拒否 |
| 存在しない commit SHA | `_commit_parents` の Git rc≠0で拒否。構文 parser 単体は存在性までは検査しない |
| root commit | parent `()` を正当に受け、`commit-diff --root` へ進む |
| diff path 非 UTF-8 | 拒否。正しい UTF-8 の非 ASCII path は通常 path として受理 |
| tree-diff 空出力 | `()` として受理し、署名なしへ進む |
| landed 区間の gitlink typechange `T` | parser は受理し、二署名 classifier は拒否しない |

空 tree-diff の受理経路は [git_state.py:569](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:569) → [git_state.py:617](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:617) → [git_state.py:832](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:832) です。trusted parent と同一 tree なら正当な空差分なので、それ自体は新規 defect ではありません。他 parent にだけある wave 自身の fragment を落とす穴は裁定が明示的に受容しています（[ruling.md:37](/work/1/SFC/tanab/izanagi-jobs/9aba3998/land-fix/ruling.md:37)）。

gitlink `T` は real ですが、裁定が既知の scope 外として明示しています（[ruling.md:70](/work/1/SFC/tanab/izanagi-jobs/9aba3998/land-fix/ruling.md:70)）。既存 `test_declared_fold_rejects_typechange_status` は最終 fold commit の閉形だけを検査し、landed merge 区間の `T` は覆いません（[test_dev_waves_git_state.py:382](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:382)）。

成果物影響: scope 外の `T` を放置すると、特に cutoff なし schema-v2 consumer が FOLDED の blob→gitlink 等を受理し、receipt と台帳参照が実体と食い違いうるため backlog の実害があります。

## 総括

- **NO-GO** — plan v2 の通常ロジックは実装されているが、受入証拠と cutoff なしの厳密な不変条件を満たさない。
- 最重 1: subprocess が 2〜5 倍以上へ増え、checker/daemon/land の共有 deadline により正規受理集合が縮む。
- 最重 2: equality-only ancestry、zero-trusted の単一 parent 選択、unique-trusted octopus 過剰拒否の変異が現行テストを生存する。
- 最重 3: trusted 判定恒真化は正例を赤にするため、事前登録した「負例が緑」という kill 理由と mutation ledger が成立しない。