## 過剰と削れるもの

- [plan:11,25,33](/work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/codex/s2-plan-out.md:11): 現行 helper が受け付ける式に無限反復はない。`MAXREPEAT` 用の注入 test と変異は削れる。放置すると実在しない分岐の検査が増え、受入時間は縮まらない。
- [plan:24,28](/work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/codex/s2-plan-out.md:24): 端・重なり・単軸の真偽と独立 reference の report bytes 比較は必要だが、六つの変異をすべて追加することは依頼の条件ではない。放置すると検査費用が増える。
- [brief:16](/work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/s1-brief.md:16): 局所化を必須と決める前に、共通 literal の判定共有だけを測る余地がある。それだけなら regex 約46秒は残る一方、差分は小さい。局所化だけなら共通判定約16秒が残る。放置すると小さい実装で十分な可能性を調べず、land 判定に必要な差分を広げる。
- [plan:44](/work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/codex/s2-plan-out.md:44): test が差し替える小さな検索 helper は D513 の発火確認に用途がある。production の無効化 knob は不要。放置すると差し替え点を持たない実装では、局所化の効果を回数で分離できない。

## 効果の見込み

- [profile-summary:9,27](/work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/profile-summary.md:9): child 約86秒のうち regex 行約46.2秒、共通 `in` 行約16.1秒が対象。約62秒は**両行の時間が全部消えた場合の上限**で、`find` と窓ごとの search の費用を差し引く必要がある。放置すると「50〜60秒短縮」を実測値として land 判定に持ち込む。
- [oracle driver:1041](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2273-issue-subprocess/orchestrator/tests/test_s8b_oracle_driver.py:1041): 発行 child は五要素 key ごとの builder で走る。L node の `test_t080_failed_launch_preserves_receipt_refusal` は `active_v2_base=True` の builder を要求し、同じ key は lock 内で一度構築されるが、別 key の builder は別 lock で並行しうる。放置すると複数 child の短縮を W_0 に足し算して過大評価する。
- [oracle driver:1866](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2273-issue-subprocess/orchestrator/tests/test_s8b_oracle_driver.py:1866): L node がその builder を待つ間だけ W_0 に効く。単独走の child 短縮がそのまま W_0 の短縮になる保証はない。放置すると 10% 達成や5分達成の見込みを強く言い過ぎる。
- [holdout freeze:592](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2273-issue-subprocess/orchestrator/campaign/s8b_holdout_freeze.py:592): 変更は `search_repository` を使う実 repo 走査にも効きうる。ただし単独 profile は計算ノードの `/tmp` fixture で、実 repo や shard-1/2 の利得は示さない。放置すると他 shard の改善を測定済みと誤記する。

## 計測設計

- [brief:34](/work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/s1-brief.md:34): 隣接3対と事前固定は前 wave と整合する。B の W_0 が約296〜337秒なら 10% は約30〜34秒で、child の推定上限約62秒の半分前後が W_0 に届く必要がある。閾値は厳しいが達成可能性を排除しない。放置すると閾値の意味を見誤る。
- [D2271:6](/work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/verbatim/D2271.md:6): W_1 と pre は各対の値・対差を補助量として報告し、land 条件には後から足さない。5分判定は B の `W_max` 中央値で別に行う。放置すると shard-1 の伸びや pre の変動が成果物から消える。
- [前 wave README:157](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2273-issue-subprocess/output/insights/2026-09-27/t2273-shard0-precopy-impl/README.md:157): 受入6走は約5,273 node秒。焦点2走693秒、変異668秒、温め111秒を足すと約1.87 node時間で、brief の2.2〜2.6時間は余裕を含む見積りとして妥当。放置すると「実績単価」と「余裕込み見積り」が混同される。

## 先に確かめること

- [profile-summary:3](/work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/profile-summary.md:3): 実装後、同じ L node の単独走 profile を一回取り直し、regex と共通判定の sample、child 時間を比較する。前回単価は212 node秒、約0.06 node時間。放置すると child に効かない案へ約5,273 node秒の受入系列を投入しうる。
- [brief:30](/work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/s1-brief.md:30): 自己汚染確認では変更した二 file のゼロ hit と、既知の陽性 file を含む別走の陽性対照を分ける。放置すると陽性対照の不成立を実装不良と誤判定する。

## 判定

**修正後 GO。** [plan:39](/work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/codex/s2-plan-out.md:39): child の改善余地は大きいが、50〜60秒と W_0 の10%達成は未実測。無限幅の注入検査と過剰な変異を削り、単独 profile で child 短縮を確認してから事前登録した受入系列へ進む。放置すると費用と land 見込みの両方を過大に扱う。

## 総括

共通判定の共有は小さい差分の候補。局所化を加えるなら、端・重なり・単軸と report bytes の等価性を守る。単独走は child の効果を測り、land と5分達成は実受入で判定する。