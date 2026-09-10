# T-2527 旧known-axesの歴史的出所と現行意味照合

authority: none
default_effect: no-state-change

D1936項22・絶対規律7に従った限定改訂の検証記録。可変状態の正本はworklogとphase doc。

## 変更と境界

- 既存T-080固定rootと一致する旧known-axesを識別し、CLI verifyでは歴史閲覧する。
- Pythonのverify/verify_documentは既定で現行意味照合を行う。6種コードsourceのSHAだけを比較用コピーで補正し、入力・path/key/lines/件数・構成・述語・comparator・参考値・pairing等の比較を維持する。
- 歴史閲覧は当該コードsourceの存在や現行意味への適合を条件にしない。非コード凍結入力の存在・hash検査は維持する。
- 未知・新規文書は従来の厳格検証を通る。既存holdの解除・拡張はしない。
- 旧artifact SHA256は `354f4b875a3c8106169252afc71cee1fd08df83b0f3024c72bda0a791e11f516` のまま。旧判定を変更せず、再認証したとも主張しない。旧measurement全体の閲覧復旧ではない。
- repo内のgateとテストを同じ主体が変更できるため、挙動検査を意図的弱体化への完全な防壁とは主張しない。

## 実測と裁定

- 起動時、登録済みClaude/Codex worktreeの実差分を照合。T-2262/T-2341/T-1851 D2関連の候補file重複0。
  最終5実装fileでの再照合では、T-2515とconftest/serializationの登録2fileが重複した。本体コード・dirty差分の重複は0。未landの他wave差分は採用していない。
- 変更前CLIはgenerator SHA不一致で拒否。現行再構成と旧文書の差はcode source6ファイルのSHA24箇所だけだった。
- 独立相談2本で変異帰属とoracle adapter経路のmaskを補正。独立レビュー2本で歴史コードの不要live readを検出し、別Codex authorが局所修正。焦点再レビューは追加must-fixなし。
- 初回consumer検査の1赤は、旧source差拒否を期待する既存oracle testだった。D1936項22と矛盾するその期待だけを変更し、実generator改竄・held/released・pin・floor/budget・sentinelのexact検査を維持した。別の不一致をfixtureへ加えて緑にしていない。
- 親の公開APIで旧実物の閲覧、code-only非存在resolverの閲覧を確認した。後者は入力置換であり、実コード削除の実験ではない。

## 関連検査

いずれも統合worktreeの未commit実装に対する親実走。author sandboxのテストはqstat preflight失敗で未起動であり、緑に数えない。

| 対象 | 計算ノードrequest | 結果 | runner所要 |
|---|---|---|---|
| 初回known-axes単独 | 991726.nqsv | 49 passed / 9 skipped | 51.86s |
| 初回consumer・meta・hold 9file | 991730.nqsv | 393 passed / 18 skipped / 1 failed (旧期待、修正済み) | 168.56s |
| R1修正後known-axes・serialization・plain coverage | 991734.nqsv | 109 passed / 10 skipped | 56.19s |
| oracle単独修正後 | 991740.nqsv | 128 passed / 6 skipped | 152.01s |

初回known-axesのbounded local走は予約capに達して終了し、runnerが計算ノードへ自動dispatchした。上表はそのdispatch後の結果。
既存skip/holdを解除・追加していない。

## 固定commitの変異と全走

実装anchorは `50a38ca37500ed555404cee3257a56e3f2881e57`。

| 変異 | 検出対象 | 結果 |
|---|---|---|
| M1 | 歴史閲覧へのgenerator同一性拒否の復活 | KILLED |
| M2 | 旧文書識別の無効化 | KILLED |
| M3 | 非コード凍結入力SHA拒否の無効化 | KILLED |
| M4 | 現行意味照合の無効化 | KILLED |
| M5 | SHA限定補正をsource record全体へ拡張 | KILLED |
| M6 measurement / calibration | 現行consumerを歴史閲覧へ誤配線 | 各KILLED |
| M7 | 歴史コードの不要live readの復活 | KILLED |

基準走行はPASSED、8件すべて失敗node完全集合が事前登録と一致。
別枠のM6 oracleとM8 holdout generatorは、特定拒否理由の消失を捉える診断感度であり、最終allowed反転のkillには数えない。
診断初回は両方を検出したが、共有木status/submodule-statusの前後照合が変化を検出してwrapper rc=125となった。
比較元payloadは保存されておらず、変更元は断定しない。初回結果を保持し、同一spec/anchorでfresh再走した。
再走は基準走行PASSED、2件の期待node一致、wrapper rc=0・shared_snapshot_matches=true・teardown完了。

段6全走は `1fd7b79708e44f7e454f08f4113770aa621bfdff` に対して **23098 passed / 68 skipped**、
`child-green`。tested mainは `4cfda49e0f38b2a87c9e08c107ebeb50d077e769`。
anchorからこのtipまで本件の5実装fileは同一。leaseは未取得のためrelease対象なし。
この記録commit後の最終受入は別に行う。

anchorのfull provenanceは9631件・新規違反0・既知違反56。履歴全体が無違反とは主張しない。
Codex workerは9走（plan1、consult2、author1、review2、fix2、focus1）、全走accepted。

## 証拠の所在

- `verbatim/`: 親brief・裁定とworker最終出力。末尾空白/最終LFだけの可逆正規化を
  `normalization.json` に記録した。原文SHA/bytesと復元手順を持ち、可視文字は変えていない。
- `worker-receipts/`: 各workerのCLI記録。served modelのattestationとは区別する。
- `mutations.json`・`mutation-primary*.json`: 8件の事前登録と実走台帳。
- `diagnostic-mutations.json`・`mutation-diagnostic*.json`: 診断初回・再走を両方保持。
- `raw/primary/`・`raw/diagnostic-first/`・`raw/diagnostic-retry/`: 各requestのstdout/stderrとreceipt。
  台帳の旧scratch pathの末尾 `<request-dir>/<file>` は、対応するraw配下の同じ末尾へ対応する。
- 保存ログの末尾空白は `raw-normalization.json` の可逆手順で正規化した。
  receipt・台帳の原文hashと照合するときは同手順で復元する。元のjob側ログは変更していない。
- `focus-*.log`、`acceptance-stage6*.log`・`acceptance-stage6.json`: 親の関連検査と全走。
- `final-scope-overlap.log`: scope確定後の実ファイル照合。
