## 判定

G3 は `partial` のままです。公開経路では要求された状態を構成できないため、指示どおり実装を変更せず停止しました。

## 公開経路で作れない理由

v2 の `attempt_ordinal != 0` に分類行と実物の claim/receipt を揃えるには、公開 `classify_attempt()` が要求する正規の `ReservedAttempt` handle が必要です。

しかし、その handle を発行できる公開経路は両方とも先に拒否します。

- `reserve_attempt_slot()` は `v2 reservation recovery ordinal is not capability-backed` で拒否する。
- `resume_attempt()` は今回対象の `v2 resume recovery ordinal is not capability-backed` で拒否する。
- `core.classify_attempt()` だけでは分類行と receipt payload しか作れず、adapter が要求する durable classification claim/receipt artifact は公開されない。そのため resume は別の artifact 検査で拒否され、受理にはならない。
- private handle 発行、private claim builder、直接 artifact 注入、依存先の差し替えを使えば合成可能ですが、公開経路ではなく、今回の制約にも反します。

したがって resume 側の回復序数 gate だけを削除しても、reserve 側の gate が残るため、公開経路から当該分類済み状態へ到達できません。

## assertion と受理集合

新しい assertion は追加していません。

既存 node の start-only 状態に分類行だけを core で追加しても、claim/receipt artifact 不在のため、回復序数 gate 削除後も resume は受理されません。よって「gate 削除時に `pytest.raises` が例外未発生で破れる」という要求を、公開経路の fixture では成立させられません。

既存の ordinal 0 正例対照は変更していません。

## 検査結果

- 実走した nodeid: なし
- 理由: 公開経路で前提状態を構成できないと判明した時点で停止
- `git diff --check`: 成功
- 3 巡目での編集: なし
- production・docs・既存テストへの変更: なし

## 変更量

- 3 巡目で追加した changed LOC: `0`
- worktree には2巡目までの既存差分 `120 changed LOC` がそのまま残っています。
- `git add`、commit、push、remote・branch 操作は実施していません。

## 総括

- G3: `partial`
- 新設・拡張した nodeid: なし。既存 `orchestrator/tests/test_s8b_attempt_registry.py::test_v2_resume_rejects_recovery_ordinal_and_accepts_zero` は未変更
- 受理集合が変わることの根拠: 公開経路では分類済み ordinal 1 状態を作れず、resume gate 単独削除による受理拡大を assertion できない
- 実走した nodeid と結果: なし
- 追加した changed LOC: `0`
- 読めなかった資料: なし
- 確かめられなかった事実: 要求状態を private fixture 注入で合成した場合の mutation 実走結果。制約により合成・実走していない