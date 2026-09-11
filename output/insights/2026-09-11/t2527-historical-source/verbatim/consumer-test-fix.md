## 総括

対象[test](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2527-author/orchestrator/tests/test_s8b_oracle_driver.py:4375)だけを未stageで修正しました。既存stage済み4ファイルは変更していません。

- **期待変更の根拠**：D1936項22と親裁定に従い、旧source差による拒否期待を変更。live module用の`ROOT`差替えと不要な旧generator移植を除去しました。入力コピーは従来どおり`root`／`source_resolver`で参照します。
- **受理・拒否**：held時はknown-axes意味照合成功を正例とし、拒否集合はfloor/budgetのみ。released時は実pin不一致とholdout generator改竄拒否を加えたexact集合です。SHAは実入力から取得し、固定値化していません。
- **保持した検査**：generator実bytes改竄、held/released双方の`allowed=False`、floor/budget拒否、sentinel到達・拒否、sentinel verifyの1回と実verifyの2回の引数一致。
- **検証**：`git diff --check`成功。runnerで対象nodeidと`test_t080_stub_free_e2e_exact_consumers_and_nodeids_b5`を指定しましたが、`qstat -Q`失敗でrc=16・子未起動。**実装済み・未実走**であり、親全走の代替にはなりません。
- **波及**：共有fixture、consumer metaの6関数／11 node、既定選択meta、hold／台帳は変更なし。test/meta累計変更量は追加・削除合算368行で450行以内です。

**M8のanchor**はproductionの[generator検査](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2527-author/orchestrator/campaign/s8b_holdout_freeze.py:1026)と、対応する[released拒否集合assertion](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2527-author/orchestrator/tests/test_s8b_oracle_driver.py:4452)です。検査無効化で`generator_refusal`が消える変異を検出する箇所ですが、変異実走は未実施です。
