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

- 起動時、登録済みClaude/Codex worktreeの実差分を照合。T-2262/T-2341/T-1851 D2関連の対象file重複0。
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
既存skip/holdを解除・追加していない。変異と最終受入は固定commitに対して別途実行し、結果を追記する。
