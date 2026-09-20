## 所見

行番号は実装後のもの。`checker`＝`tools/check_ai_provenance.py`、`land`＝`tools/dev_wave_land.py`、`dispatcher`＝`tools/pegasus/dispatch_compute.py`。

1. **real / should — 終端ログのキー名が契約と異なる。** `checker:2945`、`orchestrator/tests/test_check_ai_provenance.py:6988`、`s4-ruling.md:38`。契約は `deadline_margin_s`、実装とテストは `deadline_at_margin_s`。author 報告にも選択理由はあるが、指定された正本との不一致は残る。
   **放置時の影響：契約のキー名で読む集計処理は32秒の余裕を取得できない。**

2. **refuted / — 締切算術・投入前拒否・未設定時互換の穴は認めない。** `checker:2892,2905,2913,2927,2951`、`land:3555,3565,3576`。§2の項1〜4・7は一致し、項5の差は所見1、項6は所見4の限定どおり。

   ```text
   K=1470、now=1000、C=90
   D=1470−32=1438
   queue_budget=470−32−90−60=288
   Q=min(Q_existing,288)
   ```

   `<16` は dispatcher 未呼出し、`==16` は呼出し。不正文字列は `float`、NaN・±Infは有限性検査で `ValueError` となり、既存 `_invoke_dispatch` が16へ写像する。有限の過去期限は残余不足となる。未設定時は既存kwargsだけを渡し、D612 parser・注入seam・local scope・dispatcher本体は差分対象外。
   **影響：既定経路を維持し、期限明示時だけ裁定された受理集合の縮小が生じる。**

3. **refuted / — 時計の起点差・文字列往復による追加の精度損失はない。** `land:3565`、`checker:55,2896,2913`、checkerテスト`:6833,6855,6874`。`repr(float)`→`float` は元の浮動小数点値を復元する。480加算自体の丸めと、文字列化による損失は別である。

   landで取得した時刻をL、checker到達までの遅延をsとすれば、`remaining=(L+480)−(L+s)=480−s`。起動・import・admission等の消費は自動控除される。同一hostの共有monotonicという前提は `checker:55` と裁定§1 A3に明記されている。fake clockも絶対値1000／1470を使い、cap_oomで40進めてもDを固定してQだけ40減らすため、意味は整合する。ただし、プロセス間の時計共有を実測するテストではない。
   **影響：起動遅延によって内側期限が後ろへずれる退行はない。**

4. **refuted / — dispatcherとの期限接続は成立する。ただし完了保証ではない。** `dispatcher:3652,3664,3916,4156,4206,4245`。

   | 接続先 | 実際の制約 |
   |---|---|
   | 初期監視期限 | `min(submitted_at+W+G,D)` |
   | RUN初観測後 | `min(run_observed_at+W+G,D)` |
   | collection | `min(now+A,D)` |
   | cleanup | `min(C,max(0,D−now))` |
   | scheduler command | `min(requested_timeout,D−now)` |

   dispatch前の観測時刻をt、queue起点までをp、queue超過の観測遅延をδとすると、`Q≤D−t−C−60` より、検出時の残余は **`D−(t+p+Q+δ)≥C+60−p−δ`**。従って `p+δ≤60` ならcleanup開始時にCを確保できる。取消成功には別途fresh QUE/HLD等の条件が必要。

   渡す値はfloatで、受理されたQは16以上。既存の負値拒否に抵触しない。RUN／collectionがDまで使えばcleanupは0となり、`:3103`で取消を拒否し、`:3947`以降でholdを扱う。裁定はこの限界を明記している。新規テストはkwargs導出までであり、RUN／collection期限到達からholdまでの結合実証ではない。
   **影響：queue取消の条件付き余裕は確保するが、RUN残留・保存遅延は残る。**

5. **refuted / — landの480秒pinとrc分類は弱まっていない。** landテスト`:4820,5847,5860,9917,9972,10020,12138`、`land:3635,3646`。ASTの実引数名・定数値480・累積算術を検査し、`480+180+fold予算+30<1280`を維持する。envは動的な期限値だけ範囲検査し、残りはexact一致。継承値上書きも別テストで固定する。

   `TimeoutExpired`は従来の`after 480 seconds`、retryable分類、stderr非転送を維持する。checkerから返ったrc=1は変更なく、landではrelease-safeな違反に分類される。期限取消によって**rc=1に到達しなくなる場合**と、同じrc=1の分類変更は区別されている。
   **影響：同じ返却rcに対する分類・lease処理は不変。**

6. **refuted / — 終端予算行は例外時にも1本だが、stderr全体が1行になる契約ではない。** `checker:2937,2941,2956`、checkerテスト`:6968`。rcを16で初期化しているため、OSError／KeyboardInterruptでも終端行は`rc=16`。その後、既存例外診断がもう1行出る。拒否行はdispatcher未呼出しで1行。出力は予算・残余・rcであり、queue待ちやRUN実測値を捏造しない。

   **保存先については注意が必要。** 直叩きでは呼出元のstderrに出るが、保存にはリダイレクト等が必要。landは捕捉して捨てる。また、この行はdispatcherが戻った**後**に出るため、当該dispatcher receiptへ自動保存されない。receiptの`queue_wait_s`・`state_history`・schedulerログは別の観測である（`dispatcher:4338,4371,4407`）。
   **影響：「予算行もreceiptに残る」と扱うと、land実行後の調査で存在しない証拠を探すことになる。**

7. **refuted / — 焦点走に帰属判定すべき赤はない。** `focus-1.log`は **3893 passed、7 skipped、終了rc=0**。失敗assertionは記録されていない。`recording-unavailable:series-invalid`は診断記録の警告であり、テスト失敗として本差分へ帰属させる根拠はない。
   **影響：焦点走を失敗扱いする根拠も、受入全走済みと扱う根拠もない。**

8. **判定不能 / — 後段hが32秒以内という実測保証。** `s4-ruling.md:39`、author報告「未実装・未実走」。指定資料にはL1〜L3とhの測定結果がない。
   **影響：静的算術の成立から、receipt永続化・checker終了が480秒内に完了すると一般化できない。**

## 変異登録の判定

以下は静的予測。checker側の指定テストはdispatcherをMockに置換しており、実dispatcherの検証が先に入力を拒否することはない。複数nodeが同じ契約違反を検出することと、別理由で先に落ちることは区別した。

| ID | 判定 | 指定nodeでの検出理由 |
|---|---|---|
| M1 | 単一理由 | `derives`のD=1438との不一致、`reserved_intervals`の`D+32=K`違反。 |
| M2 | 単一理由 | Qが378となり、期待288／予約区間和に違反。 |
| M3 | 単一理由 | Qが348となり、期待288／予約区間和に違反。 |
| M4 | 単一理由 | `composes_d612`のQ=100／900／0でmin契約を破る。同値288のcase単独では検出しない。 |
| M5 | 単一理由 | `derives`では正常予算288を拒否して赤。`refuses`の15.9も検出する。負予算を実dispatcherへ渡すcaseなら別の負値gateもあるが、指定Mock経路にはない。 |
| M6 | 単一理由 | `refuses`の境界16.0正例を拒否して赤。 |
| M7 | 単一理由 | 未設定でも正常returnまで到達してkwargsを追加する変異なら、`unset_preserves`のexact比較で赤。None演算等で先に落ちる変異は登録意図と異なる。 |
| M8 | 単一理由 | `derives`／`all_entries`のkwargs exact比較で`deadline_at`欠落を検出。 |
| M9 | 単一理由 | 不正値をNoneへ変換すればMockへ進んでrc=0となり、`invalid_value`のrc=16・未呼出し契約を破る。文字列変換例外も含めた変異が必要。 |
| M10 | 単一理由 | landの捕捉envから期限キーが欠落し、期限取得／exact契約で赤。 |
| M11 | 単一理由 | `overwrites_inherited`で`"9999"`が残るため赤。 |
| M12 | 冗長 gate | **AST node単独では**`:4826`の`==480`だけで赤となり、1280算術は通る。ただし登録された2ファイル全走では、実timeoutの480pin・期限範囲・`after 480 seconds`も検出する。「matrix全体で単一gate」とは言えない。 |
| E0 | 単一理由（等価） | 到達する両引数はNaNでなく、順序交換しても最小値・拒否判定・kwargsは同じ。SURVIVED予測は妥当。 |

## 判定

**GO** — 締切・時計・分類にmust-fixの実装欠陥は確認しない。ログキーの整合とM12の単一理由性の説明は修正推奨。

## 総括

指定資料と実コードを静的に照合した。書込み・pytest・変異実走は行っていない。この判定は実装レビューの通過判定であり、L1〜L3・h実測の完了判定ではない。

GO