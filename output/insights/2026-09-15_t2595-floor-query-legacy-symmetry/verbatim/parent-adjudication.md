# [T-2595] 段 4 裁定とプラン v2

親 = /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2595-floor-query-legacy-symmetry
入力 = 段 1 brief、段 2 plan、段 3 敵対 2 本 (sol = 正しさ境界、luna = 実効性)

## 所見の裁定

| # | 所見 | 出所 | 判定 | 処置 |
|---|---|---|---|---|
| 1 | 親 brief 事実 4 が誤り。認可 cache は Runner インスタンス単位 (`s8b_floor_campaign.py:6103`) であり process 単位ではない | luna | **real** | brief を訂正。実装は変えない |
| 2 | 混在履歴 (legacy 完了 + recovery 候補) は query より前に拒否される。`s8b_floor_campaign.py:6593-6594` が round の全 retry start に `_replay_cut6_start` を掛け、`s8b_holdout_admission.py:4342` の `_assert_retry_start_authorized_locked` が両根拠で拒否する。`_retry_round` (6595) へ到達しない | sol + luna | **real** | 親が現物で検算し確認。brief の到達性説明を訂正 |
| 3 | 親 brief の成果物影響「測定 1 本空費 → artifact-invalid」は成立しない。consume は測定 callback より前 (`s8b_floor_campaign.py:5998` 対 `6008`) | sol + luna | **real** | brief を訂正。下記「訂正後の成果物影響」を正本とする |
| 4 | production に registry recovery 行の writer が無い。`record_attempt_recovery` の呼出し元は `s8b_attempt_registry.py:3537` の内部委譲とテストのみ | luna | **real** | 親が `git grep` で検算し確認。事実として記録 |
| 5 | 親 brief 事実 6 は条件付き。registry 読取が slot identity 判定に先行するため、framing 不正は空候補でなく例外になる | sol + luna | **real** | I3 の文言を限定する |
| 6 | H1 — legacy 完了行の `round` 不整合を consume は受理するのに query は落とす、逆向きの既存非対称 (`s8b_holdout_admission.py:5742-5746` 対 `5836`) | sol | **real・scope 外** | 実装しない。裁定パッケージへ |
| 7 | registry の `start_event_sha256` が list/dict のとき `s8b_holdout_admission.py:5485` が `TypeError` を送出し admission 例外へ変換されない既存挙動 | sol | **real・scope 外** | 実装しない。裁定パッケージへ |
| 8 | 提案ブロックが consume より狭い母集合を数える | sol | **refuted** | 両者とも同じ helper・同じ母集合 |
| 9 | 追加 helper 呼出しが、consume なら受理する履歴に新しい赤を作る | sol | **refuted** | consume は `5759-5761` で同じ helper を無条件に呼ぶ。反例なし |
| 10 | 追加条件が F590 型の時点依存述語を新設する | sol | **refuted** | legacy trigger は planned slot で ordinal 常に 0。最新性・未使用を含まない |
| 11 | 例外でなく `None` を返すべき | sol | **refuted** | `None` は呼び手 (`6170`) が「retry 不要」と読む。異常検出の意味を失う |
| 12 | 変異 4 件の帰属が別 gate に先取りされる | sol | **refuted** | 静的に 4 件とも帰属成立 |
| 13 | plan のテスト 3 (campaign resume 全走) は本題に対して過大で、新しい拒否の production 到達性を証明できない | luna | **real** | **不採用**。下記参照 |

## 訂正後の成果物影響 (DW-G05 の再記述)

**現時点の成果物 (certified 選択・レポート・台帳) の値・受理集合・参照は変わらない。** 理由は
所見 2 と 4 — production に recovery 行の writer が無く、仮に外部から混在履歴を置いても
通常 resume は cut-6 replay で先に abort する。

閉じるのは、`__all__` に載る公開 query API `floor_retry_trigger_for_round` と消費側
`_assert_retry_start_authorized_locked` が**同じ履歴に異なる判定を返す**という API 境界の
不整合である。これは scheduler collector が接続された時点で live になる潜在欠陥であり
(`s8b_holdout_admission.py:5619` の「This path cannot fire in production today because no
scheduler collector exists」がその前提を明記している)、依頼文自身の位置付け
「既存の穴」「certified 受理集合は広がらない」「query の認可返却と retry 起動準備だけが
非対称に残る」と一致する。

## 実装するか

**する。** 承認済みユーザー裁定であり、段 3 の新事実は依頼の前提を覆さない — 覆したのは
親 brief が上乗せした過大な影響主張だけである。裁定文・worklog に未記録の新事実は
所見 6・7・4 であり、いずれも本題の実装方向を変えない。

## プラン v2

段 2 plan の実装ブロックを**そのまま採用する** (P1 採用)。`s8b_holdout_admission.py` の
`if legacy:` ブロック (現行 5881-5885) を次へ置換する。

```python
        if legacy:
            trigger = str(legacy[0]["attempt_id"])
            evidence = _floor_registry_recovery_evidence_locked(
                state, records=records, trigger=trigger,
            )
            if evidence.candidates:
                raise HoldoutAdmissionError(
                    "retry trigger has both completion and recovery evidence"
                )
            return FloorRetryAuthorization(
                trigger_attempt_id=trigger,
                source="legacy-failed-session",
            )
```

例外文言は既存の逆方向検査 (5866-5869) と同一のものを再利用する。

### テスト

- **採用 1**: `test_used_legacy_trigger_query_rejects_registry_recovery_candidates`
  (parameterize = `valid-one` / `corrupt-one` / `valid-plus-corrupt`)。plan の設計どおり。
- **採用 2**: `test_used_legacy_trigger_without_registry_authorizes_second_retry`。
  DW-M01 が要求する「受理集合を縮小する wave の、承認外の過剰拒否を撃つ正例」を兼ねる。
- **不採用 3**: campaign resume 全走の正例。理由 — (a) 所見 13 のとおり新しい拒否の
  production 到達性を証明できない、(b) 局所的な保存性は採用 2 が撃つ、
  (c) legacy 経路の retry / resume は既存の production テスト
  `test_partial_reps_invalidates_session_and_burns_retry_then_nulls_pair` (9780)、
  `test_retry_sequence_is_metamorphic_to_other_cells_values` (9833)、
  `test_resume_does_not_reissue_retry_slot_after_retry_start_crash` (10928) が
  `orchestrator/tests/test_s8b_floor_campaign.py` で既に撃っており、この file は焦点走に入る。
  (d) ユーザー裁定「本題の修正だけ」。

### 変異事前登録 (DW-M01、実装前登録)

| 変異 ID | 位置 | 置換 | KILL する test |
|---|---|---|---|
| `MUT-T2595-LEGACY-RECOVERY-OMIT` | 新設 `if evidence.candidates:` | `if False:` | 採用 1 の全 parameter |
| `MUT-T2595-LEGACY-RECOVERY-MULTIPLE-ONLY` | 同上 | `if len(evidence.candidates) > 1:` | 採用 1 の `valid-one`・`corrupt-one` |
| `MUT-T2595-LEGACY-RECOVERY-SINGLE-ONLY` | 同上 | `if len(evidence.candidates) == 1:` | 採用 1 の `valid-plus-corrupt` |
| `MUT-T2595-LEGACY-RECOVERY-EMPTY-REJECT` | 同上 | `if evidence.candidates is not None:` | 採用 2 (過剰拒否の正例) |

単一理由性は実装後に確認する。前後・内側に同じ入力を拒否する層が無いことは段 3 で静的に
確認済み (所見 12)。

### 不変条件 (訂正版)

- I1: consume `_assert_retry_start_authorized_locked` と最終 inspection の受理集合を変えない。
- I2: 使用済み trigger を legacy 候補から一律除外しない (同じ trigger の複数 retry を保つ)。
- I3: registry 不在なら空候補で返るため新たな赤を作らない。**読取に成功した上で** slot identity
  が不明な場合も空候補で返る。framing 不正など読取自体の失敗は既存挙動 (consume も同じ helper を
  無条件に呼ぶため非対称を作らない)。
- I4: 新規 test file・新 gate・新台帳・framework・互換層・一般化を作らない。
- I5: F593 の「候補は絞る前の母集合で数える」を維持する。
- I6: 変更は `floor_retry_trigger_for_round` 内に閉じ、共有 helper の意味を変えない。

### 焦点走

段 2 plan の 12 file を周辺回帰集合として採用する。ただし「12 file すべてが本変更を踏む」とは
主張しない (所見: luna)。本変更を直接踏むのは `test_s8b_holdout_admission.py` と
`test_s8b_floor_campaign.py` の 2 file である。

## 裁定パッケージ候補 (ユーザーへ返す・本 wave では実装しない)

1. 所見 6 — legacy 完了行の `round` 不整合を consume が受理する逆向きの非対称。
2. 所見 7 — registry の hash 型不正が `TypeError` のまま admission 例外へ変換されない。
3. 所見 4 — registry recovery writer が production 未接続である事実。recovery 機構一式を
   いつ live にするか (scheduler collector の接続) は本 wave の外の優先順位判断である。
