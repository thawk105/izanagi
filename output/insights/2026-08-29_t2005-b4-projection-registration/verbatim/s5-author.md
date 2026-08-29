## 現行の受理・拒否挙動

変更前は tag なし projection 1 値の行だけを受理し、3 driver 完全行を拒否していました。production は record の単一値と選択 driver の live 値だけを照合し、非選択 driver の stale 値は検出できませんでした。

## 実装した変更

- [p3_b4_admission_record.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2005-projection-author/orchestrator/campaign/p3_b4_admission_record.py:78): driver 集合を固定定数化し、固定順の base、sort、trigger を要求する grammar に置換。
- [p3_b4_admission_record.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2005-projection-author/orchestrator/campaign/p3_b4_admission_record.py:128): 文書の 3 値を immutable な `MappingProxyType` として verified record に追加。
- [p3_b4_admission_record.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2005-projection-author/orchestrator/campaign/p3_b4_admission_record.py:485): narrow parser を追加。旧形、欠落、重複、順序違い、末尾余剰を同じ署名で拒否。
- [p3_b4_closed_critic.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2005-projection-author/orchestrator/campaign/p3_b4_closed_critic.py:1160): pair 生成時に文書 3 値を live closure と全件照合。既存の record 単一値と選択 driver の照合は維持。
- [test_p3_b4_admission_record.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2005-projection-author/orchestrator/tests/test_p3_b4_admission_record.py:261): grammar の正例と指定された各負例、mapping の不変性を追加。
- [test_p3_b4_closed_critic.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2005-projection-author/orchestrator/tests/test_p3_b4_closed_critic.py:1202): 非選択 stale、3 値 stale、live 3 値の正例を追加。

v1 schema、record の root/key 集合、単一 projection field、`_DeclaredAdmissionRecord`、canonical parser は変更していません。

## 実走した検査

- `git diff --check`: 成功。
- 対象 4 file の AST parse: 成功。
- 型解決 smoke: mapping は `mappingproxy[Literal['base', 'sort', 'trigger'], str]`。
- 結合文字検査: 対象 4 file に該当なし。
- 次の nodeid は runner へ渡しましたが、`qstat -Q` が `Unknown user-id` で失敗し、`child_started=false`、rc=16 でした。テスト本体は未実走です。

  - `test_closed_critic_expectation_row_accepts_fixed_driver_tags_and_rejects_alternate_shapes`
  - `test_pair_creation_rejects_stale_nonselected_document_projection_before_provider`
  - `test_pair_creation_rejects_three_stale_document_projections_before_provider`
  - `test_admission_projection_expectation_selects_the_pair_driver_closure`
  - `test_p3_b4_admission_record.py` 全体

## 波及可能性

- production caller の `p3_b4_launcher.py` は拡張された verified record を受け取りますが、既存 field のみ使用します。
- sidecar schema と serializer は従来の単一 projection fieldのままです。
- 共有 fixture は `test_p3_b4_launcher.py`、base・sort・trigger の loop test から間接利用されます。
- 新規 nodeid に対する acceptance duration ledger の 90% coverage meta-testは未実走です。
- 2 module の bytes が変わるため、外部で登録する最終 closure 3 値は最終 tree から再計算が必要です。analysis prereg consumer と raw pin は未変更です。

## 残した赤・未了

既知のテスト失敗は無し。ただし pytest と制約 meta-test は dispatch infrastructure 障害により未実走です。実装済み・未実走であり、完了判定はしていません。

## 総括

指定された 4 file だけを変更しました。  
非選択 driver の stale 値を production 経路で拒否します。  
schema、docs、consumer、provider、JSON artifact、Git index・commit は変更していません。