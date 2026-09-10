## 総括

**計画は条件付き採用を推奨します。実装方針の重大な欠陥は確認できませんでしたが、変異の検出帰属に1件修正が必要です。** 編集・pytest・再構成の実走は行っていません。

旧実物のSHAは `354f4b…11f516` と一致し、`e5dfa84c6` のgenerator blobも記録SHAと一致しました。ただし、このcommitを全sourceの歴史的closureとする根拠にはなりません。

### C1 / P2 — 旧source識別子の改竄拒否と、source検査の有効性を区別する

- **file:line:** [plan.md:98](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2527-historical-source/artifacts/t2527/plan.md:98)、[s1_known_axes_freeze.py:873](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2527-historical-source/orchestrator/campaign/s1_known_axes_freeze.py:873)
- **real疑い根拠:** 旧source SHAを変更すると歴史識別に失敗し、fallbackでは先に旧generator SHA不一致で拒否されます。したがって、この負例が落ちるだけでは、source比較の削除やSHA正規化範囲の拡大を検出した証拠になりません。計画106行の注意は正しいものの、98行の「無条件に除外する弱体化を検出」は帰属が広すぎます。
- **成果物影響:** 実装の受理集合ではなく、変異matrixが未検証の防御を検証済みと報告する恐れがあります。
- **最小対処:** この負例は「旧文書改変の拒否」に帰属させる。入力hash比較は未変更の旧文書＋resolver入力改変、比較範囲は未変更の旧文書＋再構成側のpath/key差分で検証する。歴史識別の弱体化は、その識別分岐を変える変異として別に帰属させる。

### 静的検算と受理境界

**現在の`build_document`について、source SHA以外の出力値差は静的読取では確認できませんでした。** 記録SHAと一致する旧generatorとの差分では、[本体:734](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2527-historical-source/orchestrator/campaign/s1_known_axes_freeze.py:734)の構成・散文は変更されていません。呼出し先の変更は主にcomparator/name/述語の拒否検査追加です。現行trigger・sort・backoffのflags定義も旧文書と整合します。ただし、動的なcampaign探索を含む全文一致は未実走であり、「差はSHAだけ」と確定報告する段階ではありません。

旧文書経路では、**実物bytes不変・凍結入力一致・liveコードSHAだけが異なる文書**を歴史閲覧の正例とし、現行利用ではさらに再構成一致を要求します。出所識別子・内容・束縛入力の改変は拒否し、現行意味の不一致は現行利用を拒否します。

新規・未知文書経路では、現行`build_document()`の出力を従来検証で受理する正例を維持します。generator/source不一致、非ancestor、再構成不一致は拒否し、この経路の成功を「未知文書の歴史的真正性を認証した」と説明してはいけません。

固定rootを**例外経路の識別条件**に使い、不一致を従来経路へ送る案は妥当です。[T-080:2458](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2527-historical-source/orchestrator/campaign/t080_freeze_migration.py:2458)のheld検査を実行へ戻すこととは異なります。既存markerとheld/released契約は維持してください。

consumerの取り残しは確認できませんでした。measurementの[呼出し:164](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2527-historical-source/orchestrator/campaign/s1_measurement_freeze.py:164)、校正の[呼出し:235](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2527-historical-source/orchestrator/campaign/s1_verify_extime_calibration.py:235)、oracleの[非adapter経路:509](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2527-historical-source/orchestrator/campaign/s8b_oracle_driver.py:509)は現行意味検証を維持すべきです。旧measurement自身は[generator/implementation検査:400](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2527-historical-source/orchestrator/campaign/s1_measurement_freeze.py:400)が残るため、今回の成果を測定記録全体の閲覧復旧へ広げて報告できません。

### 推奨裁定と変異の帰属評価

**既知旧文書限定の識別・入力束縛・現行意味照合という計画を採用し、C1を修正してauthorへ進める**ことを推奨します。

- **F27:** 固定root認証後、旧コードsource SHAだけを比較用コピーで合わせるなら恒真化ではありません。未認証文書への適用やpath/keyまでの上書きは禁止です。
- **F28:** C1が該当。oracleの負例も他のrefusalだけで落ちていないことを親実測で確認する必要があります。
- **F29:** 実物閲覧、実`build_document()`正例、再構成側を操作する模擬負例を別々に記録してください。模擬負例の成功は実物再構成一致の証拠にはなりません。
- **consumer取り残し:** 静的にはなし。既定を現行利用に保ち、歴史閲覧への誤接続を変異で検証する計画は適切です。
