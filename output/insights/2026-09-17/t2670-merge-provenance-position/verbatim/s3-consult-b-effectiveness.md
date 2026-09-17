## 所見 (既存 test の pin)

**B01 / refuted / plan「既存 test の更新表」に漏れがある疑い**  
根拠: `orchestrator/tests/test_dev_wave_wait.py` を検索・集計した結果、`_history_provenance_argv` は23箇所（定義込み、直接参照する test は11本）、`("git", "merge", "--abort")` は8箇所、`_STAGES` は2行3出現、`merge_stages` は7箇所、`history_provenance_stages` は2箇所。`_provenance(fake)` の利用3箇所（6644、7091、8112）も含め、plan はすべて拾っている。queue が厳密順序なのは同ファイル:475–480で確認した。  
影響: 指定された pin の更新漏れによる受入赤は、静的検査では見つからない。  
推奨: 更新表を維持する。特に stage test は queue 側と expected 側の双方、abort 集合2箇所（6812、6912）を更新する。

**B02 / refuted / 他ファイルに同じ順序 pin がある疑い**  
根拠: repository の Python test 検索で、同じ history／stage 集合の pin は上記ファイルに限定される。`test_dev_wave_wait_compute.py:19–27` は waiter を別名でロードするが、merge 経路を検査しない。`:656` の wrapper `_run()` は同ファイルを pytest に渡す。`test_run_tests_shards.py:20` も waiter を直接 import する。  
影響: compute 等に位置移動の期待列更新は不要。ただし runner の対象と期待失敗 node の集合を混同すると matrix 判定を誤る。  
推奨: matrix の中心は `orchestrator/tests/test_dev_wave_wait.py`。同一 module の回帰確認として `orchestrator/tests/test_dev_wave_wait_compute.py`、`orchestrator/tests/test_run_tests_shards.py` を含める。wrapper／import 先はそれぞれ同 compute test、`tools/dev_wave_wait.py` であり、別の隠れた merge 順序 test は確認できなかった。

## 所見 (新規負例と変異被覆)

**B03 / refuted / plan の実 git 負例では M1 を区別できない疑い**  
根拠: `_real_waiter_repo` は `test_dev_wave_wait.py:1133–1137` で main の基点から wave を作る。plan:113–128どおり共通基点を更新した後、main だけを進めれば、その commit は commit 前の wave HEAD に到達不能。`--no-ff --no-commit`（`dev_wave_wait.py:3834`）はこの関係を保持する。偽 checker の引数分岐も history と message を区別できる。  
影響: M1 では history が緑になり、正常実装では merge commit 後の history が赤になる。位置移動の意味的差を観測できる。  
推奨: **実 git 版を本走の主証拠にする。** 開始時の非祖先関係、終了時の親2本、違反 SHA の到達性を明示 assert する。fake 版は補助でよい。

**B04 / real / plan「変異被覆表」の KILL 帰属が過大**  
根拠: `_FakeEffects.run` は `test_dev_wave_wait.py:477–480` で順序不一致を即拒否する。既存 history 赤2本は `:7315`、`:7352` で `behind=[1]` を指定し、監査赤を無視すると後続 postcheck が `:1330` の `assert self.behind` で落ち得る。`mutation.md:16–20` は診断だけの赤や過剰決定 fixture を単独変異の証拠にしない。  
影響: M1/M2/M3 が赤でも、command 投入を防いだ関門の検出力ではなく、queue 不一致・fixture 枯渇・stage 表示差を KILL と数えるおそれがある。  
推奨: 実 git 版で M1/M2/M3 の各変異時に **runner 計数が増える**ことまで親が確認する。fake を意味的証拠にも使うなら、監査を通過した先も正常に完走できる入力を用意する。順序 pin の失敗は補助証拠として分ける。

**B05 / real / plan の「lease 解放」と実行可能性の証拠が一部任意**  
根拠: plan:131 は lease 存在 trace を任意としているが、fixture は `test_dev_wave_wait.py:1088–1090` で空の lease directory を作る。終了時の lease 不在だけでは「取得後に解放」を直接観測しない。また plan:114 の計数 runner は、変異時に実際に到達できることをまだ実証していない。  
影響: 別の拒否理由で command が0回のままでも、未投入 assert 自体は通る。lease 解放の主張も間接証拠に留まる。  
推奨: history checker の trace に観測 HEAD・判定 rc・lease 存在を記録し、commit 後監査時の lease 存在と終了時不在を対で assert する。runner は既存 `_write_exact_runner`（:1040）を使い、外部計数と正常な scheduler marker を出す形にする。

**B06 / real / brief P3・plan の変異登録は matrix 完成形ではない**  
根拠: plan:154–156 は失敗 test の候補列挙で、parameterized node を含む完全集合ではない。`mutation.md:55–60` は実測 node との完全一致を要求する。  
影響: 正しく KILL されても、未登録の順序 test まで赤になれば matrix の判定が成立しない。  
推奨: 対象 file／node を固定し、確定できない初回は probe と明記する。M0 はコメント変更の注入実在と fixture コピーを確認したうえで SURVIVED 対照にする。

追加変異は次を推奨する。

- **M4: `merge_pending=False` を監査成功後へ遅らせる。** `dev_wave_wait.py:3310` が commit 済みでも abort を試す。実 git 負例と既存 history 赤 test の abort 不在・cleanup 非優先化で検出する。終了後の lifecycle 値だけでは `:3352` が false にするため検出できない。
- **M5: history 失敗の stage 名だけ変更する。** 既存 history 赤2本と実 git 負例が検出するが、受理集合が同じなら `mutation.md:59` に従い **diagnostic sensitivity pin** とし、KILL に数えない。

**B07 / real / 数秒・全体5分以内という所要は未確認**  
根拠: 新規設計は小さい repository と偽 checker なので、本番の全史監査・queue 待ちは不要。一方、参照する CLI test の `subprocess.run`（`test_dev_wave_wait.py:8606`、`:8722`）には timeout がなく、plan に時間上限の具体化もない。  
影響: 通常は短時間と見込めるが、静的検査から数秒や matrix 全体5分以内は保証できない。  
推奨: 新規 CLI subprocess に短い timeout を付け、親が正常系と各変異の所要を測る。fixture 内の小さい計数 runner と、受入全体の直列化を混同しない。

## 所見 (brief の実測値の検証)

**B08 / real / brief:7–8「選択集合は同一」の断定が強い**  
根拠: `check_ai_provenance.py:1775–1787` は **policy commit 自身＋`policy..head`** を返す。`:3558` の HEAD 解決は呼び出しごとで、`:3573` の不変確認も各監査内だけ。preclaim と merge 側を同じ SHA に束縛する処理ではない。  
影響: 通常の自己処理では同一集合だが、両監査間の HEAD 変更まで排除した保証として一般化できない。  
推奨: 「両監査間に HEAD と checker の意味が変わらない通常経路では同一。未 commit の main-only commit は追加されない」と限定する。policy 自身の欠落も直す。新しい gate は不要。

**B09 / real / 「実測した現状」の根拠と行番号の精度**  
根拠: 呼び出し順は `dev_wave_wait.py:3831–3900` と一致するが、brief:6 の範囲 `3831–3872` は後段を含まない。cleanup 定義は3286、3330。brief が挙げる path-aware checker は `test_dev_wave_wait.py:991–992` で history を常に緑にするため、そのままでは新規負例に使えない。  
影響: 位置移動の必要性は変わらないが、既存 fixture の再利用だけで回帰検出できるという読み方は成立しない。  
推奨: 静的確認と実測ログを区別し、checker は「配置形式を参考にする新規 fixture」と明記する。提供資料から親の動的実測値までは検証できない。

**B10 / real / plan 冒頭・末尾の D2044 不一致報告が現在の資料と矛盾**  
根拠: 指定 `verbatim/D2044-item5.md:1–9` は、監査位置移動と中止・後始末の同時修正を明記している。「A-1 の本番測定」という内容ではない。  
影響: 受理集合は変わらないが、不要な資料差し替えを完了条件にして作業を止めるおそれがある。  
推奨: 現在の投影資料に基づき、plan の不一致報告を撤回する。

## 所見 (scope)

**B11 / refuted / plan が本題外の gate を追加している疑い**  
根拠: 提案は既存 `committed_sha` 取得（`dev_wave_wait.py:3873`）直後への移設で、既存比較（:3887）を利用する。cleanup の処理追加も不要で、`merge_pending` の解除位置を維持する。  
影響: 既存 HEAD 比較が監査呼び出しを挟む配置になり、追加の受理条件は導入しない。  
推奨: plan の配置を採用してよい。新規 fake 派生は既存 test と重複するため必須にせず、実 git 負例と必要な契約 assert を優先する。F365 の「監査赤なら abort」という記述修正は、brief の親 docs 成果物として残す。

## 総括

位置移動と既存 pin 更新の設計は妥当で、指定された更新漏れは見つかりませんでした。修正すべき中心は **変異の帰属**です。実 git 負例を主証拠にし、M1/M2/M3 が単なる stage 差ではなく command 投入につながること、監査時に存在した lease が解放されることを確認してください。

書き込み・pytest・変異実測は行っていません。所要と完全な失敗 node 集合は親の実測事項です。