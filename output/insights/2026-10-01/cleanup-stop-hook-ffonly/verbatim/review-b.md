### B-1

**重大度: must-fix — 「最古項＝作成点」の一般化で既存の block が消える**

根拠: [brief-stage1.md:16](/home/SFC/tanab/.claude/jobs/d2fe5f67/wave/brief-stage1.md:16)、[dev_wave_cleanup_stop_hook.py:75](/work/1/SFC/tanab/izanagi/.codex/worktrees/csh-author/tools/dev_wave_cleanup_stop_hook.py:75)。

作成項が失効・削除され、reflog が新しい順に次の2項になった場合を考える。

```text
B merge main: Fast-forward
A commit: wave
```

wave の commit A を land した後、main が B へ進み、wave が追随した状態で成立する。旧判定は最古 OID A ≠ HEAD B、かつ B が main の祖先なので block。新判定は唯一の commit 項を `[:-1]` で除外し、通過する。25 branch の観測や「land tool は wave を動かさない」ことから、作成項の保持までは保証できない。

成果物影響: **land 済みの木に対する既存の撤去喚起が消え、brief の制約24行目に反する。**

推奨: ff 免除を、最古項が作成記録と確認できる場合に限定する。それ以外は既存の OID・祖先判定へ戻す。親裁定の「最古項を無条件に除く」部分も修正する。

### B-2

**重大度: must-fix — 空 subject を自分で解析不能に変えている**

根拠: [dev_wave_cleanup_stop_hook.py:47](/work/1/SFC/tanab/izanagi/.codex/worktrees/csh-author/tools/dev_wave_cleanup_stop_hook.py:47)、[同:72](/work/1/SFC/tanab/izanagi/.codex/worktrees/csh-author/tools/dev_wave_cleanup_stop_hook.py:72)、[test_hooks.py:5503](/work/1/SFC/tanab/izanagi/.codex/worktrees/csh-author/orchestrator/tests/test_hooks.py:5503)。

最古項の subject が空なら、正常な出力末尾の `OID + 空白 + 改行` が `stdout.strip()` によって OID だけになる。追加した区切り検査がこれを不正扱いして通す。例えば、空 subject の `update-ref --create-reflog` で作った branch に commit して land した場合、旧判定では block するが、新判定では通過する。

追加テストは**最新項**だけを空にしており、出力末尾のこの退行を検出しない。

成果物影響: **有効な履歴でも、形式変更と新しい検査の組合せで既存の block が消える。**

推奨: reflog の区切り空白を保持し、末尾改行だけを除去する。空 subject テストは削除せず、最古項の場合も扱える形へ組み替える。

### B-3

**重大度: nit — テストは統合でき、M1〜M5に対する最小構成ではない**

根拠: [test_hooks.py:5461](/work/1/SFC/tanab/izanagi/.codex/worktrees/csh-author/orchestrator/tests/test_hooks.py:5461)、[同:5472](/work/1/SFC/tanab/izanagi/.codex/worktrees/csh-author/orchestrator/tests/test_hooks.py:5472)、[同:5516](/work/1/SFC/tanab/izanagi/.codex/worktrees/csh-author/orchestrator/tests/test_hooks.py:5516)。

静的な変異対応は次の構成で足りる。

| 変異 | 必要なケース |
|---|---|
| M1 | 既存の landed linked worktree |
| M2・M5 | 新設の ff main のみ |
| M3 | 新設の side から ff |
| M4 | 新設の land 後にさらに ff main |

5461行目のケースは、5472行目のテストで「追加の ff 前」に同じ検査を置けば統合できる。5516行目の subprocess ケースも M2・M5では重複するが、実入口の確認には意味があるため、既存の subprocess テストへ初期状態の検査として統合するのがよい。各新設テストでの REASON 文言検査も、既存5325行目のテストと重複する。

成果物影響: **独立した検出範囲を増やさず、repo 作成・Git 起動・保守箇所が増えている。**

推奨: シナリオの検査は残して fixture と文言検査を統合する。空 subject テストは新しい解析処理の境界なので、単純な余剰とは扱わない。

### B-4

**重大度: nit — 最古 OID の分岐は既存の検証分岐へ戻せる**

根拠: [dev_wave_cleanup_stop_hook.py:72](/work/1/SFC/tanab/izanagi/.codex/worktrees/csh-author/tools/dev_wave_cleanup_stop_hook.py:72)、[同:78](/work/1/SFC/tanab/izanagi/.codex/worktrees/csh-author/tools/dev_wave_cleanup_stop_hook.py:78)。

`reflog[-1][0] == head` を72行目の条件へ `or` で統合すれば、独立した分岐を削れる。どちらも同じ通過結果を返すため、現在の「不正行、ff 免除、作成点と同じ HEAD」の和集合は変わらず、land 済みの block も弱めない。

成果物影響: **挙動を変えずに分岐と差分行数を減らせる。**

推奨: 統合は任意。最新項だけを見る方法や commit 系だけを探す方法は、M4・M3の保証を失うため採らない。

## 総括

**NO-GO。** 実装の一般化や互換層の追加は見当たらないが、B-1・B-2には従来の block を消す具体的な経路がある。

land tool の別 repo での replay と main 側の ff はソースと整合していた。25 branch の集計は brief の報告値として扱った。以上は静的検査のみで、テスト・変異・再現は実行していない。