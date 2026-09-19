**NO-GO：固定commit `c5bfe9e82`の候補exportを含む恒久採用。実測候補としての継続はGOです。** 基準`7975385b5`との差分を静的レビューしました。親の「nodes=5を保持し、同node排他を失う候補は撤回する」裁定を支持します。

- **must：候補exportによる既存consumerとの排他喪失を出荷しない。**
  [job body:349](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2489-author/tools/pegasus/paper_story_a2_certification.sh:349)はlockを`/scr/$USER/paper-story-a2-certification/bench.lock`へ強制変更します。一方、既存の[B10 shape:2679](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2489-author/orchestrator/campaign/b10_backoff_shape_sweep.py:2679)は環境指定がなければ`~/.izanagi/bench.lock`を取得します。同nodeで両ファイルが別inodeなら両方の`flock`が成功する具体的反例があり、測定排他を失います。競合process検査も取得の原子性を代替しません。親が予定するexport撤回と候補専用test/harness拡張の除去で閉じられ、別launcher改修は不要です。

- **should：probe完了と候補採用を明確に分ける。**
  [probe:239](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2489-author/t2489_lock_probe.py:239)ではmixed pathの`acquired`も正常な観測として完了します。これは実験設計として適切ですが、終了0は候補の安全性を意味しません。また`rank*-done`は相手の完了待ちより先に作成されるため、片側のdoneだけで成功扱いせず、両rankの終了結果・failure・観測値を確認する必要があります。

その他の確認結果：

- 保持通知→挑戦→解放の順序、holder生存・終了値、解放後取得、同node inode照合があります。子の異常終了やtimeoutから**両rank正常終了**へ抜ける経路は見当たりません。
- job-body由来の代入評価とstubbed inheritance harnessの証拠範囲は、報告どおりです。全job-body実起動、独立予約の同居条件、性能改善を証明していません。
- nodes=5のliteral hash・protocol pin・qsub argv・host/nodefile fixtureの変更は整合しています。単一node契約も専用fixtureで残り、既存負例の期待緩和・skip・削除は見当たりません。
- 差分は`role=author`付きの1commitです。汎用frameworkや他launcherへの拡張はありません。候補不採用時は一時probeもjob dirへ保全し、恒久差分をpolicyと5nodes閉包に絞る親方針が適切です。

## 総括

候補撤回方針を支持します。新しいgateやframeworkは不要です。親の実測・変異・受入は完了確認しておらず、緑とは判定しません。本レビューでは書込み・pytest・性能実行を行っていません。
