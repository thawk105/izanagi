結論は F1=`partial`、F2=`closed`、F3=`closed` です。fix 起因の新規回帰や裁定逸脱は確認できませんが、F1 に must-fix が残ります。

### F1: `partial` / must-fix

追加された literal は production 実装から引いた値ではなく、数値自体も凍結値と一致します。

- H1 は rratio=80、skew=0.9、rmw=0、records=1,000,000、threads=48。[holdout_freeze.json:40](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/output/s8b-freeze/holdout_freeze.json:40)
- H2 は rratio=20、その他は同値です。[holdout_freeze.json:307](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/output/s8b-freeze/holdout_freeze.json:307)
- off=50 も凍結 positive control と一致します。[holdout_freeze.json:591](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/output/s8b-freeze/holdout_freeze.json:591)
- test 側はこれらを独立 literal として全六セルへ照合しています。[test_s8c_acceptance_receipt_v2.py:76](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:76) [test_s8c_acceptance_receipt_v2.py:123](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:123)

ただし照合対象は数値 5 field だけです。canonical descriptor に含まれる `schema_version`、`source`、`contention.label`、`objective`、`correctness`、および `policy_hint` 不在は固定していません。[test_s8c_acceptance_receipt_v2.py:89](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:89) 実際の凍結 descriptor はこれらも含む exact object です。[payload_rr80_on.json:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/output/s8b-freeze/selector-runs/payload_rr80_on.json:1) 特に schema は `source="human_declared"`、`contention.label="low"`、任意の `policy_hint` も有効値として許します。[s8b_descriptor_schema.json:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8b_descriptor_schema.json:3) [s8b_descriptor_schema.json:18](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8b_descriptor_schema.json:18)

したがって resolver が、数値を保ったまま例えば `source` を `human_declared` へ誤変更すると、fixture の assertion は通り、actual と verifier expected は引き続き同じ resolver を共有します。[test_s8c_acceptance_receipt_v2.py:128](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:128) [s8c_acceptance_receipt.py:813](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_acceptance_receipt.py:813)

成果物影響: 放置すると、固定 canonical descriptor と異なる `source`、`label`、`policy_hint` を含む content digest が標準 verifier の受理集合へ入り、将来の certified 選択が誤った descriptor provenance を参照しうる。

### F2: `closed`

lazy import、loader、resolver、および digest 属性取得までが `try` 内に入り、既存の `AcceptanceReceiptError` は同一 object のまま伝播し、それ以外の `Exception` は gate 固有の `AcceptanceReceiptError` に変換されます。[s8c_acceptance_receipt.py:703](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_acceptance_receipt.py:703) [s8c_acceptance_receipt.py:813](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_acceptance_receipt.py:813)

例外 branch に fallback 値や受理 return はありません。したがって予期しない例外を握り潰して受理集合を広げる経路はなく、以前成功した resolver 経路も変更されません。以前 raw exception で停止した入力は、現在も fail-closed で停止します。OSError 変換と既存 sentinel の同一性も test 化されています。[test_s8c_acceptance_receipt_v2.py:401](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:401)

### F3: `closed`

fix 前は test module が authority 3 module を top-level import していました。[s5-integrated-snapshot.patch:231](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1726-freeze-rederive/s5-integrated-snapshot.patch:231) 現在の top-level production import は receipt だけで、authority import は fixture/test 内へ移動しています。[test_s8c_acceptance_receipt_v2.py:14](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:14) [test_s8c_acceptance_receipt_v2.py:104](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:104)

cold-import test は同一 interpreter 判定ではありません。`sys.executable -c` を `subprocess.run` する clean process で receipt を import し、4 module の `sys.modules` 不在を調べます。[test_s8c_acceptance_receipt_v2.py:297](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:297) [test_s8c_acceptance_receipt_v2.py:310](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:310) AST test も対象 import の祖先に関数定義があることを要求しています。[test_s8c_acceptance_receipt_v2.py:322](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:322)

### 回帰・裁定照合

fix 前スナップショットから既存 test の期待値、拒否理由、skip、test 削除は変更されていません。fix 後の test 差分は literal assertion、cold-import/AST test、例外契約 test、および authority import の関数ローカル化です。[s5-integrated-snapshot.patch:218](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1726-freeze-rederive/s5-integrated-snapshot.patch:218) [test_s8c_acceptance_receipt_v2.py:76](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:76)

`git status --short` の変更面は、裁定が許した production/test の 2 file だけです。[s4-adjudication.md:81](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1726-freeze-rederive/s4-adjudication.md:81) authority leaf 新設、ancestor 検査、例外診断粒度の細分化は追加されていません。scope 外項目は裁定上も明記されています。[s4-adjudication.md:137](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1726-freeze-rederive/s4-adjudication.md:137)

pytest は本再レビューでは未実走です。静的検査のみです。

## 総括

| 所見 | 判定 | 根拠と残件 |
|---|---|---|
| F1 | `partial` | 数値 authority literal は独立かつ凍結値と一致するが、canonical descriptor 全体を固定しておらず shared-oracle が残る。must-fix |
| F2 | `closed` | `AcceptanceReceiptError` は保持し、その他の例外は必ず fail-closed 変換。受理 fallback なし |
| F3 | `closed` | 実 subprocess の clean interpreter test、AST test、test-side local import 化を確認 |
| 新規所見 | なし | fix 起因の受理集合拡大、過剰拒否、既存期待値緩和、裁定外編集は確認できない |