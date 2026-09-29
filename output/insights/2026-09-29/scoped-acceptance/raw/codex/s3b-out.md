## 所見

1. **受領証の digest は実行の証明にならない。** 現行 land は受領証の形、Git blob、申告された `child_rc` と `log_sha256` を照合するが、ログや子プロセスの実行事実を独立には検証しない（`tools/dev_wave_land.py:970–1184`）。新 schema に直接実行３本の rc とログ digest を足すだけでは、書換可能な受領証を同じ値で偽造できる。**放置時:** 全受入を経ない tip が main に入る受理経路が残る。**推奨:** 受領証ファイルを信頼する境界を明示し、その境界を要求するなら launcher の生成・原子的公開経路に限定して検証する。任意のファイル提出も攻撃対象なら、digest 追加では足りない。

2. **「tested main の固定 blob で再導出」だけでは選択器を固定できない。** plan は分類器・選択器の blob を固定するが、その Python が import する module、読み込む設定、収集時の `conftest.py` と test の内容まで固定する設計は示していない。現行 launcher も runner 自体は blob から実行する一方、実行場所は wave の repo である（`tools/acceptance_launcher.py:59–70, 610–665`）。**放置時:** tip 側の依存物が選択集合を縮め、検出力を落とせる。**推奨:** 再導出は依存物を含む固定 tree の隔離環境で行うか、参照可能な依存物を列挙して blob と実行 bytes を照合する。未列挙の import・設定参照は全受入に倒す。

3. **`output/insights/**` の一括許可は成立しない。** 実際に campaign が読む例として、`paper_story_a1_source.py:16–45` は amendment の README と設定 JSON が指す preregistration を照合し、`paper_story_a1_paired.py:216–223, 1768–1774` は preregistration 本文を照合する。`s1_known_axes_freeze.py:67–69, 903–918` は insight と `docs/phase3-main-experiment.md` を proof source として読む。`tools/check_docs.py:228–242` にも insight path の既知債務がある。**放置時:** 凍結・proof chain の入力が縮小受入で main に入る。**推奨:** 許可は実測済みの個別 prefix に限定し、設定 JSON が指す path と動的 reader の到達範囲を全受入側へ含める。親の「軽い literal 照合」だけでは、この間接参照を覆えない。

4. **docs の除外も個別名と間接参照を要する。** `docs/phase3-8c-preregistration.md`（`orchestrator/campaign/s8c_preregistration.py:44`）、`docs/b10-backoff-static-tail-preregistration.md`（`b10_backoff_static_tail_formal.py:43`）、`docs/phase3-b4-reflux-ablation-preregistration.md`（`p3_b4_analysis_prereg_consumer.py:1040`）、`docs/t1998-balanced-stock-inline-preregistration.md`（`t1998_stock_inline_pair.py:76`）、`docs/phase3-8b-descriptor-design.md`（`s8b_holdout_freeze.py:44`）、`docs/ai-provenance.md`（`tools/check_ai_provenance.py:46`）が実在する。**放置時:** 命名規則から漏れる門の入力が縮小受入になる。**推奨:** これらを初期除外表に実名で入れ、reader が設定から path を得る場合は参照先も閉じて列挙する。

5. **land の分岐箇所は plan の記述より多い。** 登録前の `_verify_acceptance_static`、lock 内の `_verify_acceptance_receipt` ２箇所、forward-main 比較２箇所に加え、`main()` の release authority は `_receipt_object` を別途読む（`tools/dev_wave_land.py:5637, 5702, 5793, 5800, 6140, 6382, 6439`）。**放置時:** scoped が着地だけ通って release に失敗する、または途中の再検証だけ旧 schema を拒否する。**推奨:** schema dispatch を単一の検証入口に集約し、登録・lock 再検査・fold 後再検査・release の正負例をそれぞれ設ける。

6. **forward-main の再受入条件は D987 より広い。** D987 の逐語は「取り込んだ main 側が実行器を変えている場合だけ」再受入とする。一方 plan は test、`conftest.py`、pytest 設定、直接 gate まで変更時の再受入を求める。現行コードは runner blob だけを比較する（`tools/dev_wave_land.py:887–910`）。**放置時:** plan を無断で採れば既裁定と食い違い、runner だけを維持すれば scoped の選択保証が変わり得る。**推奨:** scoped receipt 固有の追加条件として裁定を明記する。比較は「取り込んだ main のどの blob が、選択・収集・実行の保証を変えるか」に限定し、全変更で再受入にはしない。

7. **本 wave を全受入にする条件は運用宣言だけでは足りない。** plan は「本 wave 自身は全受入」とするが、新分類器の閉じた path 許可が `tools/` の追加・変更を必ず拒否することを land 自身で確認する必要がある。D95 判定器は `patches/` を実装面から外すため、単独の判定器ではこの保証を作れない（`tools/check_ai_provenance.py:1593–1609`）。**放置時:** 分類器自身を含む tip に scoped receipt を付けられる実装ミスが、受理集合を直接広げる。**推奨:** `tools/`、`orchestrator/`、`hooks/`、設定・patch・test の変更を含む tip の land 拒否を、分類器とは独立した負例で固定する。

8. **親の速度見通しは一回の観測からは導けない。** 親 notes の「148 node」は指定 nodeid 数で、結果は 135 passed＋41 skipped＝176 件に展開している（`s3-parent-notes.md:5–11`）。138.92 秒は pytest、173 秒は短い queue を含む wall である。同 notes の headroom 不足も同時利用者がいる時点の一観測である。**放置時:** 短縮幅と login 完結率を過大・過小に一般化し、効果判定を誤る。**推奨:** 同じ tip の全受入との同時刻対照で、収集数、実行時間、queue 待ち、直接 gate、land までを別々に記録する。

## 代案

初版は、許可する個別の文書領域を少数に絞り、`docs/spool/{worklog,decisions,failures}/` は既存の fold gate と直接検査が通る場合だけ許可する。diff は raw tree entry の追加・通常 blob の内容変更だけを受け、削除、rename の両側、mode・type 変更、symlink、gitlink、非 UTF-8、非正規 path、巨大 file は全受入へ倒す。`.gitattributes` と `.gitmodules` の変更も同じ diff 全体で拒否する。

選択器と分類器は tested main の**依存物込み**の固定実行面で再導出する。scoped 受領証は v5 と別 schema とし、waiter の post-claim merge（`tools/dev_wave_wait.py:3830–3930`）後の確定 tip に対して分類・選択・実行し、land の全入口で同じ receipt digest と再導出結果を照合する。

## scope 外候補

- 設定ファイルや動的 glob を含む全 reader の依存関係解析。初版で証明できない到達 prefix は全受入に置く。
- 任意に書換可能な受領証ファイルに対する実行証明の設計。これは既存 v5 にも関わるため、scoped 固有の field 追加だけで解決した扱いにしない。
- v5 の再設計、hold 追加・解除、テスト削除、画像・PDF の許可拡大。

## 総括

plan の方向は成立し得るが、現状のままでは **reader の間接参照、固定 blob の依存物、受領証の実行証明、land の全入口**が未閉鎖である。これらを閉じてから受理集合を広げるべきである。今回は指定どおり静的検査のみで、テストと実走は行っていない。