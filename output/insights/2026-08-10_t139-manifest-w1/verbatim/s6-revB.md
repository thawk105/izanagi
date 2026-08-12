## 判定: NO-GO

指定資料はすべて読了しました。実装自体は U-E2 の範囲に留まり、gate API 非実装・pilot 投入不可という記録は差分と一致しています。ただし、変異検出力を緑と記録できる状態ではありません。

### M1〜M6

| 変異 | 判定 |
|---|---|
| M1 | 単一 node。s7 validator 固有の operation 数検査で、他の既存検査とは分離されています。 |
| M2 | **過剰決定。** `old_sha256` 検査は s7 専用でなく、承認済み s15 も同じ `_validate_operation_binding()` を通ります。[erratum.py:367](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w1/orchestrator/preregistration/erratum.py:367) 無効化すると `test_s7_erratum_rejects_old_sha256_mismatch` だけでなく、既存の `test_erratum_rejects_old_sha256_mismatch` も落ちます。 |
| M3 | 対象語句の exact-count 検査だけを変異させるなら単一 nodeです。ただし mutation 実走未確認です。 |
| M4 | **事前登録の形が不十分。** 実際の適用可否は依然として `_ERRATUM_VALIDATORS` の membership で決まり、`compose_core()` は draft も登録済みなら合成します。[erratum.py:420](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w1/orchestrator/preregistration/erratum.py:420) [erratum.py:465](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w1/orchestrator/preregistration/erratum.py:465) `APPROVED_ERRATA` に draft を直接足す変異なら、approved/draft の直和検査が先に拒否します。[erratum.py:428](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w1/orchestrator/preregistration/erratum.py:428) |
| M5 | 単一 node。各 validator と合成 digest が成立した後に locator 重複だけで拒否されます。 |
| M6 | 既知 validator を既定値にする明確な fail-open 変異なら単一 nodeですが、変異の具体的置換が未固定です。未知値をそのまま返すだけなら `KeyError` になり、意図した受理集合拡大になりません。 |

### blocker

- **M2 は単一理由性を満たさない。** s7 専用の検査として変異できるよう、旧 s15 と共有している SHA 検査を分離してください。  
  成果物影響: 変異台帳が「s7 の防壁を証明した」と誤記し、s15/s7双方の受理集合を同時に変える欠陥を見逃します。

- **mutation harness の実走結果がない。** 実装報告自身が pytest collection と mutation の未実走を明記しています。[s5-impl.md:35](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-w1/s5/s5-impl.md:35) [s5-impl.md:58](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-w1/s5/s5-impl.md:58) DW-M08 は赤くなった node の実記録と新旧 HEAD の比較を要求しています。[mutation.md:49](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w1/docs/dev-wave/mutation.md:49)  
  成果物影響: certified 選択・レポート・台帳へ進める前提となる検出力の証明がなく、変異を kill 済みとは記録できません。

### must-fix

- **M4 は「wave 前の形と同型」という主張を修正するか、実効 boundary を作る必要があります。** 現状の M4 は `approved_erratum_ids()` の返却値を壊す変異であって、wave 前の `_ERRATUM_VALIDATORS` membership による適用可否を再現していません。[erratum.py:440](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w1/orchestrator/preregistration/erratum.py:440)  
  成果物影響: 「登録済み≠承認済み」が将来の admission 経路で実効になることを証明できず、draft が誤って投入対象になる距離を残します。

- **DW-M08 の旧実装走査に純増でない node がある。** `test_s7_erratum_target_line_digest_is_frozen` は core の固定 hash だけを検査するため、旧実装でも通ります。[test_t139_preregistration_binding.py:742](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w1/orchestrator/tests/test_t139_preregistration_binding.py:742) 一方、旧実装では新しい import 名が存在せず、テストファイル全体が node 単位でなく collection error になります。[test_t139_preregistration_binding.py:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w1/orchestrator/tests/test_t139_preregistration_binding.py:24)  
  成果物影響: 旧実装との差分検出が「validator の新規検出」ではなく import failure に潰れ、純増検出力を示せません。

- **記録の M1〜M6 単一理由主張がコードと不一致です。** 裁定は単一理由性を「確認済み」と記録しています。[s4-adjudication.md:102](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-w1/s4-adjudication.md:102) しかし M2 は共有 helper による過剰決定です。  
  成果物影響: 変異台帳の証拠強度を過大表示し、将来の gate 実装判断を誤らせます。

### nit

- draft artifact はテスト内で直接 working tree から読み、`DRAFT_ERRATUM_REF` はゼロの commit/hash です。[test_t139_preregistration_binding.py:52](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w1/orchestrator/tests/test_t139_preregistration_binding.py:52) [test_t139_preregistration_binding.py:762](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w1/orchestrator/tests/test_t139_preregistration_binding.py:762) 合成 digest の固定で大部分は拘束されていますが、draft 単体の検査は揮発値に依存します。  
  成果物影響: draft の内容と検査対象の同一性を参照で再現できず、承認集合の監査証跡が弱くなります。

公開 API については問題ありません。`APPROVED_ERRATA`、`DRAFT_ERRATA`、`approved_erratum_ids` は `__init__.py` から export されておらず、4つの admission API も非 export のままです。[__init__.py:15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w1/orchestrator/preregistration/__init__.py:15) [__init__.py:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w1/orchestrator/preregistration/__init__.py:17) 既存の第1 erratum digest 回帰も固定されています。[test_t139_preregistration_binding.py:748](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w1/orchestrator/tests/test_t139_preregistration_binding.py:748)

## 総括

pilot gate 未実装・pilot 投入不可という記録は正直です。ただし、M2の過剰決定、M4の変異意味論不一致、旧実装との node 単位比較欠落、mutation 未実走があるため、DW-M01/DW-M08 に適合した「防壁が効く」証明にはなっていません。**NO-GO**。