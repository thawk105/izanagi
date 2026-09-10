静的監査では、現行ルート自体は Claude/Codex 共通化されていますが、安全契約と独立テストに blocking finding が残っています。指示どおりテスト実行・編集・ネットワークアクセスは行っていません。

## Findings

1. High / must-fix — ignored/excluded worktree container が検証を完全に迂回する

   - 箇所: [tools/dev_wave_land.py:683](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/dev_wave_land.py:683)
   - `_verify_main_clean()` は status record が空なら 686–687 行で return し、`_registered_worktree_prefixes()` を呼びません。したがって `.git/info/exclude` や ignore 規則で container が status に出ない場合、malformed/unregistered child があっても双方向 Git-admin binding を検証せず land できます。
   - 現行テストは ignore のない合成 repo だけで、[test_dev_wave_land.py:263](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/orchestrator/tests/test_dev_wave_land.py:263) の alias は常に status に現れるため、この分岐を検出しません。
   - 最小修正: worktree container の列挙・binding 検証を status の空判定より前に常時実行する。container を exclude した正例と、同条件の unregistered child 負例を追加する。
   - DW-G05 影響: land の受理集合が「Git admin に束縛された foreign worktree」より広くなり、無効な foreign control-plane artifact を残した状態の local main と受入記録を生成できます。

2. High / must-fix — 統合済みなのに六 finding の恒久的な逃げ道が残っている

   - 箇所: [test_check_docs.py:3147](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/orchestrator/tests/test_check_docs.py:3147)
   - `DW-O23`、段5/6/9、条件23、`DW-S09` route は現在すべて統合済みです。それでも、この六点をまとめて削除すると `test_real_repo_clean` が成功します。
   - これは単なる transitional code ではなく、共通 land topology 全体の coordinated regression を緑にする active allowance です。
   - 最小修正: fallback 全体を削除し、`returncode == 0` と「違反なし」だけを要求する。
   - DW-G05 影響: docs acceptance set が、Stage 9 operation と唯一経路を欠いた repo を受理し、Claude/Codex の land 参照と開発台帳の再現性を失わせます。

3. High / must-fix — 「唯一経路」checker と fixture が同じ穴を共有している

   - 箇所: [check_docs.py:1728](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/check_docs.py:1728)、[check_docs.py:1748](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/check_docs.py:1748)、[test_check_docs.py:1833](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/orchestrator/tests/test_check_docs.py:1833)
   - `core.md` では helper path の S09 外出現を検査しますが、`operations.md` は O23 内の exact 1 件しか検査しません。O01 等へ同じ helper path を追加しても緑です。
   - また、Skill/command では同じ helper path だけを禁じるため、別 helper や直接 `git merge --ff-only` を第二通常経路として追記しても、既存必須 literal を残せば checker とテストはともに緑です。
   - これは明示的な self-consistent checker/test bug です。現在の本文は一本化されていますが、その保証は機械化できていません。
   - 最小修正:
     - `operations.md` 全体でも helper path が O23 内の一件だけであることを検査する。
     - Skill の「段9は dispatcher の共通 land 契約だけ」も exact に pin する。
     - command/Skill に代替 helperまたは直接 main mutation を足す独立負例を追加する。
   - DW-G05 影響: docs acceptance set が fresh Stage 9 外の main mutation 経路を受理し、未監査または stale な commit を local main と後続成果物へ混入させ得ます。

4. Medium / must-fix — post-merge HEAD 不明を `not-landed` と断定している

   - 箇所: [tools/dev_wave_land.py:834](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/dev_wave_land.py:834)
   - merge 後の HEAD 観測自体が失敗した場合、実際には land 済みかもしれませんが、838–840 行は `not-landed` と返します。「HEAD 実測で結果を分ける」という裁定を満たしていません。
   - 最小修正: 観測不能は非 retryable な `landed-postcondition-failed` 相当の保守的結果へ分類し、merge 後だけ `rev-parse` を失敗させるテストを追加する。
   - DW-G05 影響: JSON/受入台帳の status 値が実状態と食い違い、既に動いた main に対する再試行や誤った復旧判断を誘発します。

5. Medium / must-fix — audited sequence の「順序変更」テストが実在しない

   - 箇所: [test_dev_wave_land.py:371](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/orchestrator/tests/test_dev_wave_land.py:371)
   - docstring は「省略・順序変更」を拒否すると主張しますが、実際に試すのは `(tip,)` への省略と wave tip 移動だけです。二 commit を逆順に渡すケースはありません。
   - 最小修正: `tuple(reversed(audited))`、余分な commit、同長の別 commit をそれぞれ拒否する独立ケースを追加する。
   - DW-G05 影響: 現実装は exact 比較できていますが、将来 set 比較等へ弱体化しても受入が緑になり、監査列の順序・参照 provenance を失います。

6. Low / backlog — O23 が無関係な段5/6の全 operation 集合へ混入している

   - 箇所: [check_docs.py:308](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/check_docs.py:308)、[dev-wave.md:65](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/.claude/commands/dev-wave.md:65)
   - O23 の発火は「local main を取り込む直前」だけですが、段5/6の `_ALL_OPERATIONS` に含めたため、無関係な consumer とテスト外延まで広げています。実行時は「成立した条件」限定なので、直ちに早期 land する欠陥ではありません。
   - 最小修正: Stage 5/6 用 operation 集合から O23 を外し、段9・条件23だけに pin する。
   - DW-G05 影響: 現時点で成果物値・受理集合への影響は説明できないため、DW-G05 に従い must-fix ではなく backlog です。

## 契約・最小性の評価

現行の実運用本文は一つの経路です。

- Claude: [dev-wave.md:54](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/.claude/commands/dev-wave.md:54) → `DW-S09` / `DW-O23`
- Codex: [SKILL.md:44](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/.agents/skills/dev-wave/SKILL.md:44) → 同じ dispatcher
- 共通 leaf: [core.md:98](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/docs/dev-wave/core.md:98)、[operations.md:119](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/docs/dev-wave/operations.md:119)

現行 living surface に第二の通常 local-main mutation path は見つかりませんでした。wave-side resync の ff-only は別用途です。

約1058行の helper については、静的に未使用の関数・定数や大きな重複 subsystem は見つかりませんでした。identity/inode 検証、handoff/worktree schema、Git audit closure、lock/FD、postcondition がそれぞれ裁定済み攻撃面に対応しており、行数だけを理由にした削減は支持しません。上記1・4は局所的な契約欠陥であり、helper 全体の縮退理由ではありません。

文書は、valid foreign artifact の非接触例外、unknown untracked の拒否、stale/busy 後の fresh context、rebase/force/remote/push 禁止を [operations.md:121](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/docs/dev-wave/operations.md:121) で正しく述べています。`.gitignore` は変更されておらず、既存 startup/supervisor cleanliness consumer の横断的な弱体化もありません。

## 総括

現行 routing と文書本文は概ね正しいものの、ignored control-plane artifact の検証抜け、統合後も残る六 finding allowance、唯一経路 checker の自己整合穴が安全契約の受理集合を実際に広げています。これらを閉じるまで Stage 7 へ進める状態ではありません。

NO-GO