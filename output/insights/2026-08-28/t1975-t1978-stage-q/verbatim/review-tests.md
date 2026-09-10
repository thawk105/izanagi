レビュー結果は受理不可です。production実装には裁定逸脱を見つけませんでしたが、台帳と変異proofに2件のmust-fixがあります。pytest実走は0件で、緑判定はしていません。

## Must-fix

1. 所要時間台帳がnodeid変更を反映していません。

[author.patch](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1975-t1978-stage-q/author.patch:1)は台帳を変更しておらず、[acceptance_duration_ledger.json](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/orchestrator/tests/acceptance_duration_ledger.json:6)には削除済みの旧nodeidが7件残っています。一方、改名、新設、parametrize展開を含む新nodeid 13件は全て未登録です。

対象はlauncher 2件、landの改名5件、runner shape 3 case、D987新設3件です。`_plain_cases` consumerについては[追加済み](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/orchestrator/tests/test_dev_wave_land.py:1824)ですが、所要台帳側のconsumerは満たしません。

未修正時の影響: 新nodeid 13件が所要台帳の受理集合から外れ、旧nodeid 7件が余剰になるため、台帳coverage/meta-testをproof参照にできません。

2. mutation preregが統合後の一意anchor確認を完了しておらず、期待する失敗node集合にも静的な不一致があります。

[mutation-prereg.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1975-t1978-stage-q/mutation-prereg.md:3)は統合後に逐語確認するとしていますが、具体的anchorと確認結果が記録されていません。

| 変異 | 静的レビュー結果 |
|---|---|
| 1 | equality復元は正例だけでなく、tip digest負例、M3 drift負例、real waiter E2Eも先行拒否で赤になります。 |
| 2 | land正例に加え、real waiter E2Eとchecker lookup到達testも赤になります。 |
| 3 | final変更負例は2本あるため「専用負例testだけ」は不正確です。 |
| 4 | mask設計は妥当ですが、`forward_main_merges[-1]`はhelper外にも存在します。[helper内](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/dev_wave_land.py:862)へscopeしたanchorが必要です。 |
| 5 | net restore正例の方向は妥当ですが、any比較を導入する具体的置換anchorがありません。 |
| 6 | 最初の呼出しを消すとordering testだけでなく、2回呼出しをpinするclean-chain 2 caseも赤になります。2つの類似callsiteを区別するanchorも必要です。 |
| 7 | E2Eとlauncher正例に加え、M3 drift負例のrunner source assertも赤になります。 |
| 8 | main/tip digestの2本に加え、real waiter E2E、checker lookup到達test、既存tested-main gate testも影響します。 |
| 9 | tip欠落guardとtip非blob guardは[別の述語](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/tools/dev_wave_land.py:1093)です。単一変異として扱うなら一意な全block anchorを示すか、存在guardとtype guardへ分割する必要があります。 |

未修正時の影響: 変異による赤集合を誤ってD987またはQの単独killと数えるため、B-057 mutation proofを成果物の受理根拠として参照できません。

## Nit

- [2段reject fixture](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/orchestrator/tests/test_dev_wave_land.py:7050)は第1mainがrunner不変になる構築ですが、tested-mainとのblob等値assertも置くと単一理由性がより明確です。現状でも別ファイルだけをcommitしているため、機能上の欠陥ではありません。

## Refuted

- real waiter E2Eは恒真seamではありません。[tip runnerが97で失敗する内容](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1975-t1978-stage-q/orchestrator/tests/test_dev_wave_land.py:2272)なので、tip bytesが実行されればreceipt生成前に失敗します。実waiter、実launcher subprocess、実landを通り、main digestとtip digestの不一致もassertしています。ただしrunner自体は合成実装なので、証明範囲は「real waiter/launcher/land配線」であり、repository本物の`run_tests.py`全体ではありません。
- 2段forward-mainは両方向を備えています。第1不変・第2変更の拒否と、第1変更・第2復元の受理が分離されています。
- D987のproduction比較は最後のincorporated main対tested mainで、Git lookup失敗だけretryable、欠落、非blob、不一致はnon-retryableです。provenance前と再preflight後の2回呼出しも裁定どおりです。
- main/tip片側欠落・非blobはshape matrixと既存main欠落testで両側を覆い、`release_safe=True`、`retryable_same_request=False`を固定しています。main-tree caseの仮digestはblob guardで短絡され、guardを落とした場合はretryableへ変わるため分類assertがmaskを検出します。
- 既存期待値の不当な緩和は見つかりませんでした。反転された期待値は削除対象の2等値述語に限定され、tested-main実行、再読、binding report、waiter/checker束縛、receipt main digestは維持されています。
- schema、既定shard数、Git mode、waiter/checker/dispatcher productionへのscope拡張もありません。

## 総括

production差分は段階QとD987の裁定に整合しています。受理を止めるのは、所要台帳の旧7件・新13件の不整合と、mutation preregのanchorおよび失敗node集合未確定の2点です。scheduler認証エラーによりpytest実走は0件であり、本レビューは静的確認のみです。