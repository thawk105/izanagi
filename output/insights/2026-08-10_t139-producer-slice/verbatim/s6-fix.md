段 6 の指定所見を修正し、再照準後の変異 spec 13 件を作成しました。commit・docs・台帳類には触れていません。

### 所見対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| A2-1 | closed | `operations:` の subtree を限定し、直下の `  - ` だけを抽出。`decoy:` 攻撃を拒否 |
| A2-2 | closed | 空 `erratum_refs` を拒否。`expected_composed_sha256` を必須 keyword-only 化し、返却前に内部照合 |
| A2-3 | closed | backtick/tilde fence を追跡し、fence 内の見出しと節終端を無視 |
| A2-4 | closed | `erratum_id`→validator registry 化。既知 ID のみ実装し、未知 ID は fail-closed |
| A2-5 | closed | M1/M3/M9 を再照準し、M3a/M3bを分離。旧 M1 は登録対象から除外 |
| A2-6 | closed | 対象行 404/424 の digest をテストへ独立 literal 固定 |
| B-1 | closed | production に exact-13 定数を置き、`require_exact_fields` の既定値に設定 |
| B-2 | partial | 合成 digest の任意照合は閉鎖。approval manifest/resolver は確定 scope 外のため未実装 |
| B-3 | closed | erratum 固有検査と共通の順序・非重複・digest 検査を分離 |
| B-4 | closed | A2-3 と同じ fence-aware parser で閉鎖 |
| B-5 | closed | exact commit object と `100644`/`100755` regular blob entry を検査 |
| B-6 | closed | fields 節欠落と commit 不在を別 node に分割 |
| B-7 | closed | 非 admission-gate docstring marker をテストで固定 |

実 Git blobから独立再計算し、承認済みの結果が変わらないことも確認しました。

- field: exactly `a01`〜`a13`
- 対象行 digest: `6e87…681e` / `b5e2…b7d1`
- 合成 digest: `d1782b04ceb7cd56a3d10e2e6efb4eb7f90e6a89506a74bba727d34a5f79de82`

受理集合は、偽装 operations、空 erratum、fence 内の偽見出し、未知 erratum ID、tree ID、symlink blob を新たに拒否します。承認済み追補・erratum の受理は維持しています。

変異 spec は [2026-08-10_t139-producer-slice-mutation-spec.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer-slice/output/insights/2026-08-10_t139-producer-slice-mutation-spec.json) に作成しました。13 mutation・13 replacement anchor は全て修正後コード中に逐語で exact 1 件存在し、全 expected node 名も静的に確認済みです。M1′/M9′ は harness の安全 ID 制約に合わせて `M1-prime` / `M9-prime` と記録しています。

所有外への波及可能性は次のとおりです。

- `compose_core` の既存 caller は必須 digest 引数への追随が必要。ただし現 repo 内の caller は対象テストだけです。
- `ErratumDocument` の直接構築者は `erratum_id` が必要。現 repo 内に外部構築者はありません。
- `read_pinned_blob` の将来 consumer は tree ID・symlink・submoduleを参照できなくなります。
- 共有 fixture・consumer test への現時点の参照は検索上ありません。

## 総括

1. 変更ファイルと現在の総行数:

   - `orchestrator/preregistration/__init__.py`: 26行
   - `addendum_envelope.py`: 176行
   - `blobref.py`: 166行
   - `erratum.py`: 401行
   - `test_t139_preregistration_binding.py`: 431行
   - mutation spec: 217行

2. テスト実走:

   - 対象範囲: `orchestrator/tests/test_t139_preregistration_binding.py`
   - `tools/run_tests.py` 経由で通常走行2回・collect-only 1回を試行
   - 全てテスト開始前に `qstat -Q preflight rc=1`、runner rc=16
   - よって「実装済み・未実走」であり、緑は主張しません
   - AST parse、spec schema load、anchor exact-one、固定 blob digest の静的検査は成功

3. 登録できなかった変異:

   - 再照準後の変異は全件登録
   - 旧 M1 は検査3との過剰決定で単一理由帰属できないため、指示どおり意図的に除外

4. 残した既知の穴:

   - approval manifest、approval-fold ancestry、公開 resolver/admission gate は scope 外
   - 第2 erratum は専用 validator が追加されるまで未知 ID として拒否
   - mutation harness と対象 pytest は実行基盤障害により未実走です。