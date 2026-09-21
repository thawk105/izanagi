## 所見

指定資料を静的に検査した。実走・ファイル変更はしていない。以下の資料名は射影された `verbatim/` 内のもの、コードの行番号は親 worktree を指す。

1. **主張：案 A を「迂回ではない」とする根拠が不足している。**
   **根拠：** `D103.md` 決定 (5)、`D2195.md:3,8,11`、`brief.md` (P2)・(P3)、`proposal-draft-v1.md:11`。D103 は見えない経路を規律で塞ぐ契約である。D2195 は「login 実行が許される file」等への限定付きであり、包括的な許可ではない。
   **親の記述との差：** 自走 harness と `-c pytest.main` には既存契約・用途の違いはあるが、双方とも admission を通らない in-process pytest になりうる。harness の存在・先例・少量という実績だけでは、許可と迂回を分けられない。さらに probe 対象の `test_b5_contrast_launch.py` は parametrize を含み、D2195 の適用外条件に当たる。
   **重大度：高。**
   **修正案：** 「hook 非拒否」と「規律上実行可能」を分離する。案 A は in-process pytest・scope 不使用を明記した条件付き案とし、許可の根拠が確定しなければ案 B を推奨する。手動列挙型への限定も、資源境界の問題までは解消しない。

2. **主張：「1 file・数秒・数十 MB」を新設・変更 file の実行許可へ一般化できない。**
   **根拠：** `parent-control-all.md` は選定した既存３ harness の観測。`T2814-s5-author-run-results.md:8` は１ file でも 580 passed・302.33 秒。`runbook-s7-policy.md:8`、`tools/run_tests.py:2504,2539,2545` は予算判定と上限付き scope に接続する。
   **親の記述との差：** 案 A は「変更した既存 file」も含むため、小さな編集が巨大 file 全走を誘発する。`MAXRSS` は全子孫の同時 charged memory の保証ではなく、「天井 14 GiB に対し無視できる」は言い過ぎ。
   **重大度：高。**
   **修正案：** 「file 数や過去の所要から軽量と推定しない。親が対象と既存の login 許可根拠を明示できない file、build・大きな fixture・資源量不明の subprocess を含む file は実行せず親の焦点走へ返す」を追加する。これは安全側の除外文であり、scope 不使用を正当化する新規許可ではない。

3. **主張：コマンド 7 は拒否観測に閉じず、実行・投入へ進みうる。**
   **根拠：** `tools/run_tests.py:1648` は admission を評価し、例外時も即 rc=16 ではなく dispatch 側へ進む。`:1734` は queue 観測不能を可用扱いにする。`:2545` は local scope、`:2580,2634` は dispatch。`D103.md` 末尾も rc=16 を login 一律禁止の意味にはしていない。
   **親の記述との差：** `probe-prompt-draft-v1.md:30` の「sandbox では rc=16」は過去事例からの予測であり、コードの保証ではない。`timeout 180` も「投入されない」「投入 job が消える」の証明ではない。
   **重大度：高。**
   **修正案：** コマンド 7 は削除する。T-2792／T-2803 の rc=16・`child_started=false` を過去の引用として示し、今回の sandbox での成否は未測定とする。`--force-dispatch` への置換も目的外。

4. **主張：「新設 test file は自走できることが契約上保証される」は誤り。**
   **根拠：** `orchestrator/tests/test_plain_runner_coverage.py:25,35` は `__main__` 以後に文字列 signal があるかを調べる。実行成功・全 test の到達・pytest との node 同値性は検証しない。`D2195.md:11` もこの限界を明記している。
   **親の記述との差：** `proposal-draft-v1.md:11` は構造検査を実行可能性の保証へ拡大している。
   **重大度：高。**
   **修正案：** 「harness の構造を要求する meta-test があるが、sandbox での実行成功・網羅性・login 許可は保証しない」へ置換する。成功件数だけでなく実行範囲を報告する。

5. **主張：コマンド 6 の目的は迂回ではないが、拒否と報告の証拠設計が不足している。**
   **根拠：** `hooks/README.md:23,37,75,81`。exit 2 は対象 tool 呼び出しの阻止についての説明であり、session 全体の終了を意味するとは読めない。一方、拒否された呼び出しの JSON event は生成されず、拒否証拠は stderr に出る。launcher の静的検査も live 発火を保証しない。
   **親の記述との差：** 子の最終報告だけでは、実際の hook 拒否を十分に回収できない。hook 不発火時には、拒否観測のつもりの pytest が実走する。拒否時の hook rc と未起動 pytest の rc も別物である。
   **重大度：中。**
   **修正案：** この precheck ではコマンド 6 も削除し、静的 rc=2 と既存の拒否記録を引用するのが最小。live 対照を残すなら親側の launcher stderr を保存し、非拒否時の実走を許容する根拠を先に確定する。

6. **主張：fixture の代表性は部分的にあるが、sandbox 制約全般は測れない。**
   **根拠：** `test_t1259_scan_bound.py:17` は tmp 内で実際に Git init/add/commit、`test_b5_contrast_launch.py:13,36` は Git と tmp fixture、`test_floor_pair_job_contract.py:33,433` は subprocess・一時ファイルを使う。対象３ file に socket 接続を直接試す箇所は見つからない。
   **親の記述との差：** tmp・Git を外しているという攻撃は成立しない。ただし Git rc=128 の全原因、T-2810 の socket 制約、admission の `/run/user` 利用まで代表するとは言えない。環境辞書の組立検査も、外部環境依存の実証とは異なる。
   **重大度：中。**
   **修正案：** 「既存３ harness における tmp・Git・subprocess を含む実行例」と限定する。socket 等は未測定とし、rc=128／`PermissionError` だけで「sandbox 起因」と断定せず、診断根拠がなければ原因未確定と報告する。

7. **主張：編集ゼロの定義と確認手段が噛み合っていない。**
   **根拠：** `probe-prompt-draft-v1.md:18,24,31` は repo への１ byte の変更も禁止するが、実行形は bytecode・pytest cache の生成を抑止していない。Git status は ignored file を示さず、`git status | wc -l` の終了値は通常 `wc` のものになる。`test_t1259_scan_bound.py:27,29` は fixture 内で Git add/commit も実行する。
   **親の記述との差：** 「tracked 実装差分ゼロ」と「repo 内の全 bytes 不変」は別で、status の行数だけでは後者を証明できない。Git 操作の全面禁止を子孫にも適用すると、指定 test と衝突する。
   **重大度：中。**
   **修正案：** 禁止対象を作業 repo のソース・index・HEAD の編集に明確化し、fixture の一時 repo 操作を区別する。全 bytes 不変を要求するなら cache 出力を repo 外へ向けた別条件の probe として設計し直す。観測後に cleanup して差分を隠さない。

8. **主張：「往復１巡の削減」は期待効果としても断定が強い。**
   **根拠：** `memory-selfrun-section.md:34` の T-1851 は１ wave の記録で、追記された対処は direct call と変異確認。`T2792-README-s4.md:3` の赤は dirty tree と lineno pin。`T2796-README-s5.md` も self-run の有無による比較ではない。
   **親の記述との差：** `proposal-draft-v1.md:12,16` は、異なる走種の待ち時間と平均 wave 時間から削減効果を示唆する。7/154＝4.5%、26/154＝16.9% なので丸め算術は妥当だが、期待削減率の推定にはならない。
   **重大度：高。**
   **修正案：** 「変更 test 自身で再現する fixture／assert 誤りを先に発見できれば、修正往復を減らせる可能性がある。頻度・削減時間は未測定。7〜26 分は別走種の待ち込み所要の参考値であり、本案の効果量ではない」へ置換する。

9. **主張：今回新しく測る量と過去の証拠、author と fix の反復を分ける必要がある。**
   **根拠：** `memory-selfrun-section.md:12` は fix 子５本の過去記録、`T2814-s5-author-run-results.md:3,8` は in-process pytest の実走報告。`brief.md:51` は同木の fix を「独立２例目」と呼ぶ。`docs/dev-wave/workers.md:17` は author/fix 共通の sandbox 契約。
   **親の記述との差：** 「子は一切実走できない」は既存記録に反する。今回の追加価値は現在の対象・launcher・sandbox での指定 harness の rc／所要／変更状態であり、能力の初発見ではない。同木・同 file の fix は役割別の再現確認であって独立した族の証拠ではない。
   **重大度：中。**
   **修正案：** author １本を最小 probe とし、fix は役割による差を疑う具体的理由がある場合だけ追加する。一般化しない結論に DW-G03 の独立２例を持ち込まない。依頼が現在の実測を求めているため、過去記録だけで probe 全体を不要とはしない。

10. **主張：案 A〜D は現状のまま「全件承認」で扱える形ではない。**
    **根拠：** `proposal-draft-v1.md:3,14,18,22`。A と B は排他、C は不採用、D は scope 外の将来案。`origin.md:8` は gate・台帳・一般化を除外する。
    **親の記述との差：** 本 wave の実行可否、将来の prompt 採否、admission 改修が同じ列に並んでいる。「実行できた」だけでは、DW-S04 にいう効果・実測欠陥を示したことにはならない。
    **重大度：中。**
    **修正案：** 「今回の選択は A または B、C は不採用、D は今回承認対象外」と明記する。現時点の推奨は B、A は許可境界の裁定が成立した場合の候補とする。D の代替 path 等の設計は展開しない。

11. **主張：rc・所要・拒否を機械的に取り出せる報告形式にはなっていない。**
    **根拠：** `probe-prompt-draft-v1.md:20,33,43` は自由記述と末尾15行。拒否時は command 自体が始まらず、`time` の失敗と test の失敗も異なる。「１回のみ」と time 失敗後の fallback の関係も曖昧。
    **親の記述との差：** 数値 rc をすべての行で要求すると、未起動に架空の rc を付ける余地がある。手動 harness の関数名と pytest nodeid、未取得の skipped 数も同一視できない。
    **重大度：中。**
    **修正案：** 各番号に `attempted`、`started`、`process_rc`、`hook_verdict`、`wall_s`、`maxrss_kb`、`executed_count`、`evidence` を固定し、未取得は `null` とする。末尾15行は添付摘要にとどめ、親が元の tool／launcher 出力を保存する。

## (P1)〜(P5) の判定

- **(P1)：conditional。** 過去の能力実証と現在の静的非拒否はある。現在の exact な子経路・対象での成功、live hook 発火、規律上の許可は未確定。
- **(P2)：refuted。** 新設・変更 file 一般への適用は、D2195・meta-test・３例の資源実績から導けない。受入代替禁止の文自体は適切。
- **(P3)：conditional。** `-c pytest.main` を採らない判断は妥当。ただし F121 はこの綴り自体を裁定した資料ではなく「同族」は推論。A だけを自動的に非迂回とはできない。
- **(P4)：conditional。** 自己完結する誤りを前倒し検出する可能性はある。「１巡削減」の達成・頻度・時間は未実証。また consumer／meta-test 等も、対象 file に含まれる場合まで絶対に検出不能とは言えない。
- **(P5)：conditional。** 境界が未定義で、本 wave で定義しない方針は妥当。その未定義部分を少量の実績で埋めて案 A の許可へ進むことはできない。

## probe prompt 草案の修正版 (差分だけ)

- **全体に追加：** 「静的非拒否は実行許可を意味しない。以下の live self-run は対象ごとの既存許可根拠が親から明示された場合だけ実施する」。未確定なら静的結果と既存証拠で裁定パッケージを返す。
- **コマンド 1 を置換：** 環境記録に `git rev-parse HEAD`、`git rev-parse --show-toplevel`、`git status --porcelain=v1 --untracked-files=all` を加え、各終了値を保持する。`wc -l` だけで clean と判断しない。
- **コマンド 1 に追加：** `/usr/bin/time` と `date` の利用可否を test 起動前に確認し、計時方式を確定する。拒否された後の別 wrapper による再試行は禁止。計時不能なら未取得とする。
- **コマンド 2〜4 に追加：** test 実行は各１回。`PYTHONPATH=.` は残す。t1259 と floor は自身で root を `sys.path` に追加するが、b5 は追加せず `tools` を import するため、必要性は file ごとに異なる。
- **コマンド 2〜4 に追加：** 「既存 file の限定観測。新設 file 一般、socket、admission の `/run/user` 利用は未検証」。親の先行走・cache 状態を記録し、cold-start 所要や性能改善を主張しない。別 worktree なので pyc が同一だったとも断定しない。
- **コマンド 5 に追加：** 「出力なし・rc=0 だけで０件を確定しない。harness 不在の静的確認と併せて test 未実行と判断する」。目的は既知の偽緑の対照であり、成功例に数えない。
- **コマンド 6 を削除：** 静的拒否結果と既存 live 記録を引用する。hook 不発火時の意図しない pytest 実走をこの probe に持ち込まない。
- **コマンド 7 を削除：** rc=16 固定ではなく local／dispatch に進むため。`timeout` とその fallback も不要になる。
- **コマンド 8 を置換：** コマンド 1 と同じ HEAD・status を終了値付きで再取得し、tracked／index／untracked の変化を報告する。「ignored bytes 不変までは証明しない」を付記する。
- **報告形式に追加：** 所見11の固定欄を用い、hook 拒否時の `process_rc` は `null`。親の静的 hook rc、過去資料の引用、今回の実走値を別欄にする。

## 案 A の文の修正版 (差分だけ)

- **表題を置換：** 「親の推奨」から「login 許可境界が確認できた対象に限る条件付き候補」へ。
- **実行対象を置換：** 「新設・変更した file だけ」から「新設・変更した file のうち、親が対象と既存の login 許可根拠を明示したものだけ」へ。不明なら未実走で返す。
- **資源条件を追加：** 「１ file という単位は資源上限ではない。build・大きな fixture・資源量不明の subprocess を含む場合は実行せず、親の焦点走へ返す。」
- **許可の限界を追加：** 「pytest.main 委譲型は in-process pytest であり、admission の cgroup scope を通らない。hook 非拒否・harness 契約・過去の軽量実績だけを許可根拠にしない。」
- **赤の扱いを置換：** 「自分の差分への帰属を根拠付きで確認できた赤だけを修正する。既知の統合前の期待赤、原因未確定、実行環境の拒否は内訳を報告し、期待値変更・skip／xfail 化で緑にしない。」
- **報告条件を追加：** 実行した file・ケース名／nodeid・件数と未実行範囲を併記する。手動 harness の関数名を pytest nodeid と偽らない。
- **維持・補強：** 「self-run は計測でも受入でもなく、親の焦点走と受入全走を代替しない」は維持する。子の緑を理由に親の焦点集合・consumer 検査を縮めないと追記する。
- **根拠・効果を置換：** 「契約上保証」「天井に対し無視できる」「往復１巡削減」を削除し、所見4・8の限定文へ置換する。

## 見つからなかったこと

- **親の焦点走・受入を代替する明文上の穴：** 案 A の「代替しない」と `DW-S05-C` を照合したが、禁止は既に明記されていた。
- **F27 を無視する直接指示：** 「赤」「甘く」「F27」を確認したが、テストを甘くしない禁止はある。問題は原因分類の粗さ。
- **tmp・Git fixture が皆無という欠陥：** `tmp_path`、`TemporaryDirectory`、`git`、`subprocess` を検索し、実操作を確認した。
- **`.codex` と `.claude` の名前だけによる guard 判定差：** `guard_bash.py` の両文字列と root 解決を確認したが、該当分岐は見つからない。ただし `main()` は payload の `cwd` を判定へ渡さず、trust は絶対パス単位なので、payload の cwd 変更だけでは実 worker の同等性を証明できない。
- **hook exit 2 が session 全体を必ず終了する根拠：** README の `exit 2`・拒否・event の記述にはなかった。報告回収は別途必要。
- **規律7／DW-O19 に反するソース注入・復元の指示：** 草案にはない。cache、一時 fixture、run_tests の副作用は別問題として指摘した。insight には実行可能 script を写さず `.md` 逐語だけを残せばよい。
- **D289 の内容を独立に確認する資料：** 射影には含まれない。D103 が関連正本であることは確認できたが、「D289 は並行投入」の説明は親の記述として扱う。また依頼の禁止を無断で「綴りだけの禁止」へ狭められない。
- **新規 D／F が必須となる新種の欠陥：** 見つからない。F76／F121 の既存型との対応を記すのは適切だが、本 wave の台帳編集には広げない。過去の実走は当時の証拠として保存し、現在の条件差で無効化しない。

## 総括

重大度「高」は **５件**。現行草案の live probe は **NO-GO**。
最重要は、**hook が見ない実行経路を、規律上許された実行経路と同一視していること**。
コマンド 6・7を外し、対象の許可根拠と編集ゼロの定義を確定した縮小 probe なら再検討できる。
許可境界が閉じなければ、既存証拠と静的所見を示して案 B を推奨し、案 A は条件付き裁定候補として返す。
