## 所見ごとの対応表

| ID | 判定 | 根拠 file:line |
|---|---|---|
| C-01 | closed | clock-only reason は exact 1 件となり、全 sample・literal tolerance・method/governor・禁止成果物が固定された（[cli.py:439](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:439)、[test_calibrator_certify.py:931](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_calibrator_certify.py:931)）。ただし profile hash の第三者再計算性は PC-01 に残る。 |
| C-02 | partial | 指定 2 反例は shape→policy→band の順と先頭違反短絡に戻った（[execution_guard.py:183](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/execution_guard.py:183)、[execution_guard.py:257](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/execution_guard.py:257)、[test_execution_guard.py:650](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_execution_guard.py:650)）。ただし evaluator が shape/get を `try` 外で再評価するため、stateful `Mapping` では旧版になかった例外経路が残る（[execution_guard.py:213](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/execution_guard.py:213)）。 |
| C-03 | regressed | partial write の掃除は追加されたが、`O_EXCL` が既存 temp を検出して失敗した場合まで無条件に `unlink` する（[cli.py:288](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:288)、[cli.py:791](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:791)）。自分が作っていない既存 file/symlink を消す回帰である。 |
| C-04 | partial | M1/M2 は sensitivity pin として成立するが、F-8 が M3 を後段で mask し、M4 の conjunction anchor は F-1 後に消滅、M5/M8/M10 も登録どおりの単一置換ではない（[s4-adjudication.md:197](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-u2-recalibration/s4-adjudication.md:197)、[cli.py:793](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:793)、[cli.py:820](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:820)）。 |
| C-05 | closed | `not_evaluated` は test-local literal になり、reason/status/tolerance/禁止成果物も literal 固定された（[test_calibrator_certify.py:34](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_calibrator_certify.py:34)、[test_calibrator_certify.py:616](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_calibrator_certify.py:616)）。fix 追加テストに実装定数を期待値へ戻す再発は見つからない。 |
| RC-01 | closed | owned consumer が渡す通常の plain dict/JSON 値では旧 public 制御フローに復元された。receipt、CLI、silo 2 経路に加え F-8 caller も確認した（[execution_guard.py:159](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/execution_guard.py:159)、[cli.py:509](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:509)、[silo_ladder_rung1.py:1974](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/silo_ladder_rung1.py:1974)）。generic `Mapping` は C-02 の残件。 |
| PC-01 | partial | 保存した `effective_clock_input` から canonical rejection は再計算できる（[cli.py:442](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:442)）。しかし SHA は保存 subset ではなく全 in-memory profile の canonical JSON hash であり、その全 preimage は保存されない（[cli.py:396](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:396)、[cli.py:446](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:446)）。第三者は同じ hash を再計算できない。 |
| PC-02 | out-of-scope | scope 内の「同一 process・内部 profile 非参照」は production 化済みで、rename 後 target を読む（[cli.py:475](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:475)、[cli.py:804](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:804)、[cli.py:820](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:820)）。別 process verifier の完全形は明示的 scope 外（[s4-adjudication.md:227](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-u2-recalibration/s4-adjudication.md:227)）。 |
| REG-01 | partial | C-02/REG-01 の巨大 tolerance と「先頭帯外＋後続巨大 int」は制御フロー上ともに旧・現 `False`（[execution_guard.py:191](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/execution_guard.py:191)、[execution_guard.py:284](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/execution_guard.py:284)）。ただし二度目の Mapping shape 評価による一般 API 回帰は残る。 |
| NE-01 | closed | final assembly/schema と published-bytes 検査を追加し、dynamic 名も具体化した（[cli.py:64](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:64)）。列挙は early 分岐後の実順序（[cli.py:737](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:737)）と一致する。 |
| OPS-01 | out-of-scope | raw/sanitized attempt path と rejection-only collector test は裁定パッケージ送りのまま（[s4-adjudication.md:232](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-u2-recalibration/s4-adjudication.md:232)）。collector 自体は任意の非空 manifest を扱える（[collect_receipt.py:76](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/collect_receipt.py:76)）。 |
| OPS-02 | out-of-scope | live worktree drift は明示的 package 項目で、fix の 4 file はこの面に触れていない（[s4-adjudication.md:235](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-u2-recalibration/s4-adjudication.md:235)）。 |
| OPS-03 | out-of-scope | reservation 式・2340 秒問題は明示的 scope 外（[s4-adjudication.md:229](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-u2-recalibration/s4-adjudication.md:229)）。 |
| TEST-01 | closed | 許可 3 parameter node＋metamorphic 1 nodeだけが更新され、旧保証は現 test へ移植された（[test_calibrator_certify.py:898](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_calibrator_certify.py:898)、[test_calibrator_certify.py:1040](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_calibrator_certify.py:1040)）。親報告の 663 passed / 2 skipped / 0 failed は所与として扱うが、私は実走していない。 |
| REC-01 | regressed | 追記 2 は旧誤記を訂正したが（[s4-adjudication.md:170](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-u2-recalibration/s4-adjudication.md:170)）、新 sidecar が成功 attempt の inventory（[s4-adjudication.md:94](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-u2-recalibration/s4-adjudication.md:94)）に未反映。追記 3 の mutation 記述も F-8 後の mask と合わない。 |

## 新規所見

| ID | 根拠 file:line | real / speculative | 成果物影響 | 区分 |
|---|---|---|---|---|
| NR-01 | [cli.py:439](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:439)、[test_calibrator_certify.py:639](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_calibrator_certify.py:639) | real | test は外部 fixture で全 profile を再構成するが、実 `rejection.json` だけでは profile hash の preimage がない。 | must-fix |
| NR-02 | [cli.py:288](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:288)、[cli.py:805](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:805) | real | temp 名が既存 file/symlink と衝突すると、create-only failure 後に他者の file を削除する。 | must-fix |
| NR-03 | [execution_guard.py:213](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/execution_guard.py:213)、[execution_guard.py:237](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/execution_guard.py:237) | real。現 owned caller への到達は speculative | 二度目の `set(expected)` や `expected.get()` が `try` 外なので、stateful/custom Mapping の `OverflowError` は structured diagnostics にならない。 | must-fix |
| NR-04 | [s4-adjudication.md:94](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-u2-recalibration/s4-adjudication.md:94)、[cli.py:821](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:821) | real | producer inventory が新しい成功 sidecar を列挙せず、記録と実 staging が再び不一致。 | must-fix |
| NR-05 | [s4-adjudication.md:199](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-u2-recalibration/s4-adjudication.md:199)、[cli.py:793](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:793) | real | 現登録のまま mutation matrix を回すと、mask された KILL を load-bearing 防壁と誤記録できる。 | must-fix |

NR-02 は `_write_exclusive` 自身が「作成後の書込み失敗だけを、自分が取得した ownership に基づいて掃除」し、caller は同関数が正常 return した後だけ temp を所有済みと扱う必要がある。

NR-01 の hash は、生 dict の hash ではなく次の bytes の SHA-256 である。

```text
json.dumps(profile, sort_keys=True, separators=(",", ":"),
           ensure_ascii=True).encode("utf-8")
```

したがって、全 `attestation_profile` と canonicalization identifier を保存するか、hash 対象を実際に保存した `effective_clock_input` に変えて field 名も是正しなければならない。

### 変異事前登録 M1〜M10

| ID | fix 後の単一理由性 | 再照準 |
|---|---|---|
| M1 | 成立。early 削除は benchmark 未開始・rejection-only sensitivity を壊す（[cli.py:565](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:565)）。 | 現状どおり sensitivity pin。 |
| M2 | 成立。late 削除時は publish-policy gate が拒否し、reason だけ変わる（[cli.py:763](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:763)）。 | 現状どおり sensitivity pin。 |
| M3 | 不成立。policy gate を消しても F-8 が policy mismatch を拒否する（[cli.py:793](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:793)、[cli.py:820](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:820)）。 | accepted-set mutation から、reason・target 非生成時点の sensitivity pin へ再分類。 |
| M4 | 不成立。product に「3 分解の conjunction」anchor はもうない。 | [execution_guard.py:191](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/execution_guard.py:191) の policy mismatch early return を band math へ流す一置換へ。 |
| M5 | 不成立。`lower <= sample <= upper` の条件反転は `all→any` ではなく帯内/帯外の意味反転になる。 | [execution_guard.py:315](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/execution_guard.py:315) の math body を明示的 `any(...)` にする単一 AST/body replacement へ。 |
| M6 | 成立。loop 入力を `[1:-1]` にする一置換は先頭・末尾 property を落とす（[execution_guard.py:257](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/execution_guard.py:257)）。 | 現 anchor でよい。 |
| M7 | 成立。canonical call を diagnostic count に差し替える contradiction test がある（[cli.py:417](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:417)、[test_calibrator_certify.py:675](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_calibrator_certify.py:675)）。 | 現状どおり。 |
| M8 | 記載どおりでは不成立。helper は `target` しか受けず、in-memory profile 置換には signature と call の複数変更が要る。 | [cli.py:820](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:820) の引数 `target → staging_artifact` 一置換へ。tamper test が単独で kill する。 |
| M9 | 成立。early condition を反転すると正常 profile publish が赤になる（[test_calibrator_certify.py:828](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_calibrator_certify.py:828)）。 | 現状どおり。 |
| M10 | 不成立。shape、policy、band eagerness は別 anchor であり単一 mutation ではない。 | policy は M4へ移し、M10 は [execution_guard.py:320](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/execution_guard.py:320) の `collect_all_violations=False → True` に限定。shape pin が必要なら別 ID と extra-key overflow vector を追加。 |

### 反証できなかった点

- F-7 の旧保証脱落は反証できなかった。3 profile 区別・`[True,False,True]`（[test_calibrator_certify.py:909](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_calibrator_certify.py:909)）、48 sample/tolerance/reason/非 publish（[test_calibrator_certify.py:934](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_calibrator_certify.py:934)）、metamorphic の producer→loader→issuer→consumer→self と loader 負例（[test_calibrator_certify.py:1053](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_calibrator_certify.py:1053)、[test_calibrator_certify.py:1183](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_calibrator_certify.py:1183)）はすべて残る。
- F-8 が rename 後 target 以外の profile/dict を読む反例は得られなかった。sidecar は schema、判定、target raw SHA、policy identity のみで、時刻・path・nonce はない（[cli.py:485](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:485)）。
- F-8 mismatch は非 0 となり、target は削除されない（[cli.py:827](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:827)、[test_calibrator_certify.py:877](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_calibrator_certify.py:877)）。
- 新 sidecar で collector が壊れる反例は得られなかった。collector は全 file を opaque manifest 化し、sidecar も final receipt に hash 束縛される（[collect_receipt.py:171](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/collect_receipt.py:171)）。
- fix 追加テストに「production constant 自身を expected へ差し込む」自己参照 oracle の再発は見つからなかった。

scope 外へ逃がしてよいのは PC-02 の別 process 完全形と OPS-01/02/03 である。PC-01 の hash self-containment、C-03 の temp ownership、C-04 の mutation 再登録、REC-01 の新 sidecar inventory は今回の fix が直接作った scope 内問題であり、外へ送れない。

## GO / NO-GO

**NO-GO**

親報告の 663 passed / 2 skipped / 0 failed は否定しないが、NR-01/02 はその node 群が踏まない静的反例であり、M3/M4/M5/M8/M10 は mutation 段へ進める登録状態ではない。私は `pegasus02` の read-only reviewer として pytest を実走しておらず、緑は主張しない。

## 総括

- C-01、C-05、NE-01、TEST-01 と F-7 の許可 4 node 更新は閉じた。
- 指定 2 overflow 反例は旧・現とも `False` へ戻った。
- PC-01 は verdict 再計算まで閉じたが、profile hash の第三者再計算性が残る。
- C-03 は他者所有 temp を消す回帰を新たに入れた。
- C-04 と REC-01 は F-8 後の mutation mask・新 sidecar inventoryに追随していない。
- PC-02 完全形と OPS-01/02/03 は正当に out-of-scope。
- scope 内 must-fix が残るため **NO-GO**。