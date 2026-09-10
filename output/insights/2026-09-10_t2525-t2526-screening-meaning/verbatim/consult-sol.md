## 総括

**real候補は1件。** 宣言の転送と既存 gate で本題を満たせます。screening 独自の case 不一致拒否は削除するのが最小です。静的確認のみで、書込み・pytest・性能測定は実施していません。

- **real / must-fix候補 — 明示宣言への追加拒否**
  - **位置:** [plan.md:38](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2525-t2526/artifacts/dev-wave-t2525-t2526/plan.md:38)、同 `:95`。
  - **根拠:** `backoff_sweep.py:118` の要求 key 完全一致検証と `:425` の外側 gate が既に存在します。共通 gate は `condition_meaning_gate.py:3413` で対象 case 不在を未確立とし、`:4100` で受理します。今回の具体的な caller から、その挙動を追加拒否へ変える必要は示されていません。また途中で引数が `None` に落ちる変異は「明示時だけの検証」では捕捉できません。
  - **影響:** 本題の物理量照合とは別に、共通 gate が未確立として受理する入力を screening 独自に拒否します。
  - **最小修正案:** `:38` の局所拒否と `:95` の専用検査・変異を削除。既存 helper の宣言を転送し、literal・符号化点の意味 green と要求不一致の red、各転送箇所の回帰で配線を確認します。

- **refuted候補 — 期待値が観測依存になる**
  - **位置:** [plan.md:31](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2525-t2526/artifacts/dev-wave-t2525-t2526/plan.md:31)、`backoff_sweep.py:145`、`backoff_extended_sweep.py:550`。
  - **根拠・影響:** 要求格子の physical から期待 bits を生成し、実 C++ 観測と分離する計画です。extended 側の encode は要求から raw key を作る用途で、観測から期待値を逆算していません。
  - **最小修正案:** 不要。raw `3000` / physical `1000` の正例と raw `1000` / physical `1000` の負例を維持します。

- **refuted候補 — 乱択設定への静的宣言の強制**
  - **位置:** [brief.md:11](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2525-t2526/brief.md:11)、`plan.md:42`、`b10_backoff_shape_sweep.py:782`。
  - **根拠・影響:** 未宣言を維持し、raw の値域だけで static witness を生成しない計画です。乱択の受理集合を狭める追加 gate は不要です。
  - **最小修正案:** 不要。乱択の無宣言回帰は今回の自動宣言混入を検出する範囲に限定します。

- **refuted候補 — create-only の新規検査を必須にする**
  - **位置:** [plan.md:99](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2525-t2526/artifacts/dev-wave-t2525-t2526/plan.md:99)、`backoff_extended_sweep.py:1268`、`test_backoff_extended_sweep.py:785`。
  - **根拠・影響:** create-only は既存挙動で、共通 writer に既存被覆があります。今回変わる参照境界は v2 identity と discovery です。
  - **最小修正案:** create-only 専用の新設・変異を必須から外し、v1 を新走入力に選ばない検査と JSON/DAT の版・status 整合に集中します。

親 brief の D1859・D1936 項19引用は正本と一致しました。plan の AST 成功・既存 hash 不一致は本段では再実測しておらず、意味照合の成功や凍結再発行の根拠には数えていません。