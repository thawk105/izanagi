# 段4裁定・plan v2

## real/refuted と採否
- planの限定案を採用。既知旧documentの識別、歴史閲覧、現行意味照合を分ける。
- sol C1 / luna C1はreal・scope内・採用。旧source識別子改竄は旧文書識別の負例であり、source入力検査のkillとは数えない。
- luna C2はreal・scope内・採用。oracleはadapter非発火でknown-axes verifyに到達させる。別refusalの存在では検出済みとしない。
- 親P1「consumerの既存局所照合だけで十分」はrefuted。現行の全文再構成比較をSHA限定補正付きで維持する。
- 旧measurement記録全体の閲覧復旧という一般化は採らない。対象はknown-axesの検証と既存consumerの現行意味照合。
- T-080のheld gateを解除・迂回して復活させない。既存固定root値の再利用は、限定経路を適用できる文書の識別条件だけ。新root/台帳は作らない。
- 追加のユーザー裁定は不要。D1936項22の範囲であり、新しい権限・仮想リスク向け機構は追加しない。
- 親実測(preflight-observation.md)で、現行再構成との差がsource SHA24箇所だけと確認済み。

## 実装単位と上限
- authorは別worktree /work/1/SFC/tanab/izanagi/.codex/worktrees/t2527-author、branch impl-t2527-historical-source。
- 本体所有はorchestrator/campaign/s1_known_axes_freeze.pyだけ。build_documentの生成内容は変えない。
- test所有はtest_s1_known_axes_freeze.pyを基本とし、必要ならtest_s1_measurement_freeze.py、test_s1_verify_extime_calibration.py、test_s8b_oracle_driver.py。
- meta所有は必要な実アクセス登録だけ: orchestrator/tests/conftest.py、test_real_repo_serialization.py、test_plain_runner_coverage.py(実在する登録が必要な場合だけ)。
- 新規test file/汎用helper/台帳/hold登録は作らない。既存golden/期待値/hold対象nodeの本文を変更しない。
- 規模目安: production追加200行以内、テスト/必要meta追加450行以内。超えそうなら実装前に理由を報告し、範囲を勝手に広げない。
- docs/commit/git stage/他waveファイルは親所有。新artifact bytesを発行せず旧判定を不変にする。

## APIと検証
- plan通りhistorical=Falseの明示keywordをverify_document/verifyに追加し、Python既存consumer既定は現行意味照合。CLI verifyは歴史閲覧を選ぶ。
- 歴史閲覧で旧文書の全内容と識別子が既存rootに一致することを確認し、凍結入力のsource resolver/存在/SHA検査は維持する。
- 6つの_module_source由来pathのコードSHAだけを歴史的出所として扱う。path/key/lines/順序/件数を一律除去しない。
- 現行利用は_validate_schema、assert_s1b_pairing、実build_documentとの内容比較を維持。SHA補正は確認済み旧文書の比較用コピーだけ。
- historical経路で現行意味権威やdangling HEADを閲覧条件にしない。新規・未知文書は既存厳格経路を維持。
- 既存holdのmarker/held-released契約は維持し、成功をcertifiedや保留解除と説明しない。
- 受理: 旧実物はコード差だけで閲覧拒否しない。新規実build_documentは自己整合なら従来通り通る。
- 拒否: 旧内容/識別子/入力改竄、現行利用の意味不一致、新規文書のsource/generator/ancestor/全文不一致を拒否する。
- 実正例は旧実物の公開verifyと新規の実生成。意味不一致の模擬は実builderを通った値への単一変化であり、旧artifactを書き換えたふりをしない。

## 変異事前登録
各変異は独立、親がauthor成果の正確な置換anchorと期待node集合を検算してspecへ落とす。
1. M1: 歴史閲覧に旧generator/live SHA比較を戻す過剰拒否。旧実物のhistory正例だけを指定してKILLEDを期待。
2. M2: 旧文書識別を無条件成功にする。旧文書のwhat/識別子改竄が歴史閲覧で通る弱体化を、歴史完全性の負例でKILLED。
3. M3: 歴史文書の非コード入力SHA不一致拒否を無効化する。未改変旧文書＋resolverの入力コピー改竄でKILLED。generator拒否に帰属させない。
4. M4: 旧文書の現行意味比較を無効化する。歴史閲覧は通り現行利用は拒否されるflags単一差の負例でKILLED。
5. M5: 比較用コピーのSHA補正をsource record全体の上書きへ広げる。実再構成側source key単一差の拒否を失いKILLED。
6. M6: consumerをhistorical=Trueへ誤配線。measurement/calibration/oracleの対象呼出しで旧文書＋非互換な現行構成の負例を使う。oracleはadapter非発火を証明し、校正はread-heavy以外の差で後段maskを避ける。実効性が他層にmaskされる場合はその事実を記録し、単独killを主張しない。
- 新規文書の既存拒否テストをそのまま回す。既存期待値・golden・held nodeを変更して検査を緑にしない。
