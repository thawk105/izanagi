# [T-2595] 段 1 brief — 床値 retry query の legacy / recovery 候補計数の非対称を閉じる

wave: t2595-floor-query-legacy-symmetry
worktree (投入先 repo root): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2595-floor-query-legacy-symmetry
基準: main = 0600887d9、wave branch = worktree-dev-wave-t2595-floor-query-legacy-symmetry (同 tip、clean)

## 研究前進 (土台)

B-4 床値 campaign の resume 経路で、`floor_retry_trigger_for_round` は消費側が拒否する履歴に
retry 認可を返しうる。走ると測定を 1 本空費してから `artifact-invalid` で終わる。閉じるのは
query 側の候補計数 1 箇所であり、床値 official 走行の前に潰す。完了判定は「同じ履歴に対して
query と consume が同じ判定を返すことを、正例と負例の対で示せたこと」。

## scope と成果物影響 (DW-G05)

放置すると、床値 campaign の journal に消費側が拒否する retry 試行行が 1 本増え、その cell の
retry 枠が 1 消費され、最終 inspection が `artifact-invalid` を返す — すなわち試行台帳の値と
終端診断が変わる。certified 受理集合は広がらない (consume と最終 evidence 検査が同じ履歴を拒否する)。

## 確定済みユーザー裁定

- 実在する不整合の解消に限定する。一般的な retry framework を作らない。
- 規律 2 を緩めない (anomaly を検出した履歴の拒否を弱めない)。
- 実装面は Codex `role=author` の実装子が書く (D95)。親は実装面を直接編集しない。
- 仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。

## 変更面 (実アンカー)

- `orchestrator/campaign/s8b_holdout_admission.py`
  - `floor_retry_trigger_for_round` (def が 5792 行) の内部:
    - legacy 収集ループ (5822-5841): starts を走査し `completions` から canonical failed planned を拾う。`used_recovery_triggers` を見ない
    - `used_recovery_triggers` の構築 (5842-5848)
    - recovery 収集ループ (5849-5857): `if trigger in used_recovery_triggers: continue` で除外する
    - 多重性検査と返却 (5860-5890)
  - 参照のみ: `_assert_retry_start_authorized_locked` (5749 行)、`_trigger_session_candidates` (5723 行)、`_floor_registry_recovery_evidence_locked` (5450 行)
- `orchestrator/tests/test_s8b_holdout_admission.py` — 既存 file へ正例・負例を追加する

## 実測済みの事実 (親が現物で確認)

1. 使用済み trigger が「canonical failed planned の完了行」と「registry recovery 候補」を併せ持つとき、
   query は recovery 候補を数えず `len(recoveries) + len(legacy) == 1` を通し、legacy 認可を返す。
2. 同じ履歴に対し consume 側 `_assert_retry_start_authorized_locked` は
   `len(trigger_sessions) + len(recovery.candidates) != 1` で拒否する。query と consume が非対称。
3. query 側には逆向きの検査だけが既にある — recovery を選んだ trigger に完了行があれば
   `"retry trigger has both completion and recovery evidence"` を上げる。legacy を選んだ側に同じ検査が無い。
4. production consumer は `orchestrator/campaign/s8b_floor_campaign.py` の
   `_Runner._retry_authorization` (6174 行)。(round, cell) で memo 化するため、同一 process では
   retry start 追記前に 1 回だけ呼ばれる。resume (新 process) では journal に retry start がある
   状態で再問い合わせされる。すなわち本件が発火するのは resume 経路である。
5. legacy 経路は「同じ trigger で retry 枠を使い切るまで複数回 retry する」のが設計
   (`_retry_round` 6406 行の while ループ)。**使用済み trigger を legacy から一律除外する修正は
   正当な resume を壊す。**
6. `_floor_registry_recovery_evidence_locked` は registry 不在または slot identity 不明なら
   candidates 空で返る。純粋な legacy 走に新たな赤を作らない。
7. pin 閉包: `s8b_holdout_admission.py` / `floor_retry_trigger_for_round` を path・記号で検索した
   live な bytes pin は無い。hit は `output/insights/**` の過去 mutation spec (履歴) と
   `orchestrator/tests/acceptance_duration_ledger.json` (所要の scheduling hint、未知 test は既定値で
   許容) と `orchestrator/tests/test_check_docs.py` の R33 role contract 逐語 (本件の変更面と無関係)。

## 不変条件

- I1: consume 側 `_assert_retry_start_authorized_locked` の受理集合を変えない。query 側だけを consume に揃える。
- I2: 事実 5 の legacy 複数 retry 設計を壊さない。使用済み trigger を legacy 候補から一律除外しない。
- I3: registry 不在・slot identity 不明の純 legacy 走で新たな赤を作らない。
- I4: 新規 test file を作らない (既存 test file へ追加)。新しい gate・台帳・framework・互換層を作らない。
- I5: F593 の「候補は絞る前の母集合で数える」規約を維持する。絞り込みで曖昧さを隠さない。
- I6: 変更は `floor_retry_trigger_for_round` の内部に閉じる。共有 helper の意味を変えない。

## (P1) 親の provisional 裁定 — 攻撃対象

非対称の閉じ方は「legacy 候補を認可として返す前に、その trigger の recovery 候補を
**使用済み除外なしで**数え、非空なら consume と同じく `HoldoutAdmissionError` を上げる」とする。
黙って `None` を返す案は採らない — consume が拒否する履歴を「retry 不要」と誤って報告し、
campaign が試行不足のまま finalize しうるため。この裁定自体を段 3 の攻撃対象とする。

## 成果物の形

`s8b_holdout_admission.py` の 1 関数の差分 + 既存 test file への正例 1 本以上・負例 1 本以上 +
変異 matrix + 受入全走 + worklog / insight / decisions の spool fragment。

## 並列分割方針

段 2 plan 1 本。段 3 敵対 2 本 (レンズ A = 正しさ境界と query/consume の対称性、
レンズ B = 実効性と production resume 経路の到達性)。段 5 実装 1 本 (単一 file 群のため分割しない)。
段 6 敵対レビュー 2 本。
