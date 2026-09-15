# [T-2595] 床値 retry query の legacy / recovery 候補計数の非対称

wave: `dev-wave-t2595-floor-query-legacy-symmetry`
実装 commit: `3fc3b83fe`

## 何を閉じたか

`orchestrator/campaign/s8b_holdout_admission.py` の公開 query `floor_retry_trigger_for_round` は、
round の各 session-start から完了行を集めて legacy 候補を作るループと、registry recovery 候補を
集めるループの 2 本を持つ。後者だけが「既に retry へ使われた trigger」を除外していた。

その結果、使用済み trigger が canonical な失敗 planned 完了行と recovery 候補を併せ持つとき、
query は recovery 候補を数えずに多重性検査を通し、legacy 認可を返した。消費側
`_assert_retry_start_authorized_locked` は同じ履歴を「完了数 + recovery 候補数 != 1」で拒否する。
公開 query と消費ゲートが同じ journal に別の判定を返していた。

修正は legacy 返却の直前に、選んだ trigger の recovery 候補を**使用済み除外なしで**数え、
非空なら消費側と同じ文言で `HoldoutAdmissionError` を上げる 8 行である。

## 成果物への影響 — 現時点ではゼロ

段 3 の敵対 2 本が独立に、親 brief の影響主張を現物で否定した。親はすべて検算した。

1. **混在履歴は query へ届かない。** `s8b_floor_campaign.py` の `_Runner.run()` は
   `_retry_round` を呼ぶ手前で round の全 retry start に `_replay_cut6_start` を掛ける。
   その先の `floor_attempt_requires_cut6_replay` → `_assert_attempt_authorized_by_journal` →
   `_assert_retry_start_authorized_locked` が同じ混在履歴を先に拒否する。
2. **「測定を 1 本空費」も成立しない。** consume は測定 callback より前に走る。
3. **production に registry recovery 行の writer が無い。** `record_attempt_recovery` の
   非テスト参照は core 定義と `s8b_attempt_registry.py` の内部委譲だけである。

したがって certified 選択・レポート・台帳の値・受理集合・参照は変わらない。閉じたのは API 境界の
判定不一致であり、scheduler collector が接続された時点で live になる。
`s8b_holdout_admission.py` の replay 境界のコメントが「no scheduler collector exists」と
その前提を明記している。

## 採らなかった案

- **使用済み trigger を legacy 候補からも一律除外する。** legacy 経路は同じ trigger で retry 枠を
  使い切るまで複数回 retry するのが設計 (`_retry_round` の while ループ)。正当な resume を壊す。
- **黙って `None` を返す。** 呼び手 `_retry_authorization` は `None` を「この cell は retry 不要」と
  読む。消費側が拒否する履歴を検出しておきながら、試行不足のまま先へ進める。
- **recovery 側の使用済み除外を外す。** recovery の一回限定設計を変える。

## 変異 matrix

baseline PASSED。4/4 KILLED、MISMATCH 0、SURVIVED 0、期待 node は 4 件とも完全一致。
spec は `mutation-spec.json` (sha256 `35e533e089bfe25b4025c132b1d55e68f83a56e69850bbfbc2c0ab7c439fa281`)、
結果は `mutation-report.json`。runner は
`python3 tools/run_tests.py orchestrator/tests/test_s8b_holdout_admission.py -q -rf --force-dispatch -p no:cacheprovider`。

| 変異 ID | 置換 | KILL した node |
|---|---|---|
| `MUT-T2595-LEGACY-RECOVERY-OMIT` | `if False:` | 負例 3 parameter すべて |
| `MUT-T2595-LEGACY-RECOVERY-MULTIPLE-ONLY` | `if len(...) > 1:` | `valid-one` / `corrupt-one` |
| `MUT-T2595-LEGACY-RECOVERY-SINGLE-ONLY` | `if len(...) == 1:` | `valid-plus-corrupt` |
| `MUT-T2595-LEGACY-RECOVERY-EMPTY-REJECT` | `if ... is not None:` | 既存正例 + 新規正例 |

最後の 1 件は `DW-M01` が要求する「受理集合を縮小する wave の、承認外の過剰拒否を撃つ正例」である。
空 tuple も拒否する変異を入れると、registry 不在の正当な legacy resume が落ちることを示す。

## 裁定パッケージ候補 (本 wave では実装しない)

1. **完了行の round 不整合。** 消費側の canonical 判定は完了行の `round` を検査しないが、
   query は検査する。逆向きの既存非対称であり、本題とは別。
2. **registry の hash 型不正が `TypeError` のまま漏出する。** 候補判定の集合 membership に
   list / dict が来ると admission 例外へ変換されない。消費側と共有する既存挙動。
3. **registry recovery writer が production 未接続。** recovery 機構一式をいつ live にするか
   (scheduler collector の接続) は本 wave の外の優先順位判断である。

## verbatim

`verbatim/` に段 1 brief、段 4 裁定、段 2 plan、段 3 敵対 2 本、段 5 実装、段 6 レビュー 2 本の
全文を置く。
