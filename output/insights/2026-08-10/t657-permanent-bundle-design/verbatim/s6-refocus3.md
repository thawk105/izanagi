| # | 2 巡目の残件 | 判定 | 要点 |
|---:|---|---|---|
| 1 | precedence の文書間矛盾 | `regressed`（型 2） | resolver の一意解決規則は揃ったが、追記が下位 active pointer を上位成分とし、上位本文の approved-inactive 参照と衝突する。 |
| 2 | legacy cutoff の非総体性 | `regressed`（型 2） | 複数導入は拒否、Git 外成果物は段 0 へ送られたが、複数導入の一律拒否が「X 前の成果物を遡及拒否しない」と衝突する。 |
| 3 | 非交代成分の親束継承 | `closed` | 交代成分の導入・承認確認と、非交代成分の親束との byte 一致が明記された。 |
| 4 | Q3 の暗黙裁定 | `regressed`（型 3） | 直接の anti-lockstep 文言は消えたが、環境単独交代と祖先成分への rollback が別規則で先に拒否されている。 |
| 5 | 下位 conformance gate | `closed` | U-A1、conformance literal、下位実装と exact 正本との差の 3 件が段 0 gate に入った。 |

## must-fix

### 1. 下位 pointer と approved-inactive 束の混同（型 2）

追記は、上位 resolver が成立する HEAD では下位の `active-bundle pointer` が上位束の成分になると規定しています。[freeze 文書の追記](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/freeze-permanent-design.md:18>)

一方、本体は上位束が `approved-inactive` の下位束を参照でき、下位 `X_f` を上位発効より前に強制しないとしています。[本体 §5.1](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:181>)

下位 F1 が承認済みだが pointer は F0 のまま、という HEAD では、本体は上位束から F1 を解決できますが、追記は F0 を指す pointer を成分とします。resolver の成立条件自体は揃いましたが、解決する凍結成分が揃っていません。

**成果物影響:** certified 選択・レポート・台帳に記録される freeze authority 参照が、同じ HEAD で F0 または F1 に分岐する。

### 2. cutoff と遡及不拒否の衝突（型 2）

§9.1 は X より前に作られた bundle-ID なし成果物を遡及拒否せず、歴史として読むと要求します。[遡及不拒否](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:324>)

しかし新 cutoff は導入 commit が複数なら無条件に拒否します。[cutoff](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:334>) 現行履歴検査も、同一 bytes の削除・再追加で複数導入が生じ得ることを明示しています。[実装](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_ratified_freeze.py:469>)

```text
C1 < C2 < C3 < X
C1: R を追加
C2: R を削除
C3: 同じ bytes の R を再追加
```

この R は全導入が X 前なので前段落では legacy 受理対象ですが、導入 commit が 2 本なので cutoff では拒否されます。現 HEAD に該当成果物が実在するかは未確認ですが、上記履歴は本文と現行検査が許す構成です。

**成果物影響:** 同じ bundle-less receipt／report を legacy として採用するか拒否するかが実装解釈で分かれ、certified 選択の材料集合と台帳の受理集合が変わる。

### 3. Q3 が依然として未裁定になっていない（型 3）

§5 と Q3 は lockstep／片側後継を未裁定としています。[§5](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:146>)・[Q3](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:450>)

しかし、次が先に固定されています。

- §2 は「較正の世代交代は凍結の世代交代なしには完了しない」と断定しています。[§2](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:65>)
- §11.1 は「環境活性化だけ進み floor が旧世代」を保存必須の拒否としています。[§11.1](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:413>)
- 新規の「交代した成分は導入 commit と承認が同じ列に実在」という規則は、祖先世代の既承認成分へ戻す rollback を拒否します。[成分整合規則](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:153>)

したがって、直接の lockstep 禁止を削除しても、環境単独後継と既存 identity への rollback は Q3 前に排除されています。

**成果物影響:** environment-only successor と祖先束への rollback の受理可否が裁定前に拒否へ固定され、上位 pointer chain、certified 選択、レポート・台帳の authority 参照集合が変わる。

## closed の確認

- 非交代成分については、親束との byte 一致が明示され、旧構成 `F1 →（G_f/A_f なし）→ F2` は規範上拒否されます。[本体 §5](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:153>)
- 段 0 gate は 3 件へ拡張されています。[本体 §10.1](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:389>) 下位正本の未了 2 件、および現行実装の approval/pointer 同一 commit 要求も静的に確認できました。[下位正本](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/freeze-permanent-design-s2.md:3>)・[現行実装](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_ratified_freeze.py:1189>)
- topology 図は直列となり、旧来の枝図と exact-parent 規則の矛盾は解消しています。
- Git 上に導入 commit を持たない成果物を「未定義・段 0 が定める」とした点は、提示された前提に従い欠陥として数えていません。

## 総括

- 型 1: **0 件**
- 型 2: **2 件**
- 型 3: **1 件**

**NO-GO。** precedence 追記による凍結成分参照の分岐、cutoff の自己矛盾、Q3 の暗黙裁定が残っています。静的検査のみで、ファイル変更・pytest 実行は行っていません。