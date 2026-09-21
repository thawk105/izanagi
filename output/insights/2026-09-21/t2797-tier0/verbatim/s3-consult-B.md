**must-fix は3件です。最小案は、投入前の perf build＋固定 smoke、結果記録、既存 A/B 分岐への接続です。追加開始印・trace build の前倒し・score での再検査は、事前登録から必須とは導けません。**

以下、`P`＝[段2 plan](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-tier0/codex/s2-plan.md)、`B`＝[親 brief](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-tier0/brief.md)、`C/`＝`orchestrator/campaign/`、`T/`＝`orchestrator/tests/`、`V/`＝指定された逐語資料ディレクトリです。静的検査のみで、編集・commit・テスト実行はしていません。

1. **must-fix — plan §3：正常通過時の sidecar → 台帳の接続が記述上抜けている。**

   根拠：`P:211` は「submission が無い場合」に Tier0 を読む一方、`P:225` 以降は通過後の event にも証拠を添付するとしています。現行 `C/b5_generator_contrast.py:333`、`:399` の正常経路には Tier0 の読込み・返却がありません。

   **影響：** header が実装済みを宣言しても、正常な評価・certified endpoint の元 event に Tier0 通過証拠が届かず、report の契約照合が正常台帳を拒否するか、欠落を黙認することになります。

   推奨：対象 slot では submission の有無にかかわらず terminal Tier0 結果を読む、と明記してください。B の判定は submission、Tier0 の判定はその物理 attempt の結果として分離します。特に `C/b5_generator_contrast.py:634` は `submitted_once` を最終結果へ畳み込むため、**以前の attempt が投入済み・今回が Tier0 拒否**という正常な retry 履歴を、同一 attempt 内の矛盾と混同してはいけません。

2. **must-fix — plan §3／P5：`tier0-interrupted` に系列停止への接続がない。**

   根拠：`P:200` は開始印だけなら新 outcome `tier0-interrupted`、処置は未完走としています。しかし `C/b5_generator_contrast.py:781` の停止集合にこの値はありません。

   **影響：** 子だけが中断して driver が生き残ると、分類不能なのに次の A へ進み、`:787` の endpoint 選択・`:794` の fallback・score に到達し得ます。

   推奨：新 outcome を削り、既存の `unclassified-missing` に `reason="tier0-interrupted"` を添えてください。これで既存停止分岐を使えます。子中断後も driver が存続するケースで、次候補・score・fallbackへ進まないことを検査します。

3. **must-fix — plan §3／P4：通常のコンパイル失敗を分類する実装境界が未確定。**

   根拠：`P:198` はコンパイラ終了失敗を候補拒否にしますが、`:204` は「境界を識別するか、識別できなければ error」としています。実体は `C/buildcache.py:3816` の通常の `RuntimeError`。同じ build API には cache integrity・`nm` 検査不能などもあります（`:2717`、`:3777`）。

   **影響：** 候補の通常のコンパイル失敗まで分類不能にすると、A を使って次候補へ進む系列が欠測終了に変わります。逆に全 `RuntimeError` を拒否へ寄せると、基盤障害を生成器の失敗として計上します。

   推奨：plan v2 で、候補起因と認定する既存境界・取得できる証拠を一つに決めてください。`_run` を通った事実だけでは候補起因の証明にはなりません。通常の候補コンパイル失敗を `error` に逃がす選択肢は完了条件から外します。型付き失敗を返すため buildcache の変更が必要なら、現在の所有外なので**所有変更の裁定パッケージ候補**として返し、編集不要と断定しないでください。

削除レンズでの各要素の判定は次のとおりです。

| 重大度・対象 | 根拠 | 削除時／放置時の影響と推奨 |
|---|---|---|
| **should — 新 sidecar、P4** | `V/prereg-3.md:22`、`P:173`、`C/p3_s4_loop.py:1945` | **結果記録は残すが、新しい拒否体系は不要。** 拒否は既存 `proposal-rejected.json` に Tier0 の理由・結果を載せる案が使えます。ただし、そのままの classifier は内容を読まず `rejected-preprocess` にする（`C/b5_generator_contrast.py:309`）ため、小変更は必要。通過結果用に `tier0.json` 一つを残す案も妥当です。両方式を重ねる必要はありません。 |
| **should — 開始印 P5** | `C/b5_generator_contrast.py:587`、`C/p3_s4_loop.py:2833`、`C/b5_generator_contrast_report.py:357`、`:391` | **削除候補。** 既存 attempt-start で A・物理 attempt、submission で B を回収できます。開始印を削っても §3.3 の A/B は満たせます。失うのは中断位置の細分化であり、時間切れ原因の証明でもありません。 |
| **should — 新 event kind** | `C/b5_generator_contrast.py:58`、`:231`、`P:222` | **追加しない判断に賛成。** 既存 `proposal-rejected`／`evaluation-result`／`score-session` の追加 field で足ります。新 kind を削っても §3.1／§3.3 の不足はありません。 |
| **should — header 契約記録** | `V/prereg-3.md:23`、`V/prereg-11-12.md:46`、`C/b5_generator_contrast.py:551` | **残す。** 削ると、依頼された未実装表示の置換と実値の参照が欠けます。ただし exact 契約は一か所に定義し header へ保存すればよく、独立した契約台帳・発効 gate は不要です。 |
| **should — report 変更** | `C/b5_generator_contrast_report.py:308`、`:379`、`:391` | **結果回収は残すが、計数器は再利用。** A・物理 attempt は既存処理で足ります。投入前結果を `reconciled` に追加する設計なら `submitted is True` 条件が必要、という plan は正しい。ただしこれはその拡張に伴う条件であり、P5 の新開始印が必要な根拠ではありません。 |
| **should — 新 test file** | `P:261`、`T/test_b5_generator_contrast.py:126`、`:324`、`T/test_b5_generator_contrast_report.py:624` | **ファイル新設は任意、検証内容は必要。** 既存 fixture・予算・retry・report 検査を拡張できます。別ファイルを削っても契約違反にはなりません。既存 writer の汎用耐久性を再証明するテストより、Tier0 が submission より前に記録される接続を検査してください。 |
| **should — score slot の Tier0、P4** | `V/prereg-3.md:3`、`:17`、`C/b5_generator_contrast.py:797`、`:805` | **削除候補。** §3.1 は探索予算の定義で、既に選ばれた endpoint の5回再計測に Tier0 を繰り返す明文はありません。残すと smoke の一過性失敗だけで score が欠測になる受理条件を追加します。最小案は search のみ。残すなら「同じ関数を通るから」ではなく、追加の score 契約として今回明示的に採否を決めるべきです。 |
| **should — trace build の前倒し、P2** | `V/prereg-3.md:17`、`:43`、`C/pipeline.py:2016` | **削除候補。** perf binary のコンパイル＋smoke で Tier0 は成立し、trace build は従来どおり pipeline が実行できます。§3.3 は投入後の correctness build 失敗も明記しています。両 build を前倒しすると trace 固有の失敗が B 消費から A のみへ移ります。これは cache 最適化だけでなく予算契約の選択です。 |

4. **should — plan §1／§7：U2 の直列化は妥当だが、U1 の先行 land は不要。**

   根拠：依頼逐語 `V/T-2797-request.md:8` は共有 file を相手の land 後に変更するよう指定しています。`B:36`、`P:241` は先行 consumer と中間状態の互換処理を計画しています。

   **影響：** U1 単独では Tier0 の受理集合は変わらず、子の定数の有無による暫定分岐と二段階の検証だけが増えます。

   推奨：U1 の実装・レビューを先行し、**land は U2 と統合して一度**でよいです。U2 は build 入力作成と smoke を helper に寄せ、既存 condition gate 後に最小の build 呼出し・結果記録・早期 return を置きます。ただし `T/test_ccbench_spawn_sites.py:738`、`:1048` の既存検査があるので、build を無条件 helper に移して検査を弱める短縮は採りません。

   所有は宣言上、U1 と T-2830 の列挙 path は素集合、U2 と T-2632 は共有です。**現在の他 wave の実変更面は射影資料だけでは確認できません。** land 後の親による再照合が必要です。

5. **should — plan §4／§5：変異と検査対象の対応が一部成立していない。**

   根拠：`P:309` は「smoke に trace binary を渡す変異」を `test_smoke_exact_argv_and_parser` へ割り当てていますが、`:265` の検査入口は binary を受け取った後の smoke helper です。

   **影響：** helper 単体の argv が正しくても、呼出し側が `tr.binary` を渡す回帰は生き残り、計画した検収の射程を過大に報告します。

   推奨：この変異は子の実挿入点を通る検査へ割り当て、異なる trace/perf binary のどちらが gateway に届いたかを確認してください。P2・P5 を削るなら、それらの存在を固定する変異も削ります。新しい汎用変異基盤は不要です。

6. **should — P6：並列本数は今回決めてよいが、780秒をサービス時間の保証にしない。**

   根拠：`V/d2200-item1.md:33` 以降は親運用を AI 手番としています。`V/insight-6.md:47` は1系列・10巡の実測。`V/prereg-7-1.md:9` の6順序は workload ごとの12組全体です。

   **影響：** `p=4` を配置からの必然、または `4×780` を一般的な待ち時間と扱うと、親の不足による無応答欠測の見積りを誤ります。

   推奨：plan の brief 誤引用訂正を採用し、**p=4 は運用上の選択、1親1系列は context 分離の契約**と記録します。今回決めるのはこの対応と、親を確保してから対象 LLM 系列を開始する手順まで。108系列の exact schedule・モデル記録・prompt hash は別段に残します。追加 scheduler・親 spawn gate は不要です。

7. **should — P7：共通 W の式は今回、倍率と予算の発効は別段、という分離を維持する。**

   根拠：`V/prereg-3.md:44`、`V/prereg-11-12.md:29`、`V/insight-6.md:42`、`P:350`、`:367`。

   **影響：** `21259k` を全 workload の完走保証にしたり、各 job の予約上限と総 Elapse 管理上限を同一視すると、未完走・費用の解釈が変わります。

   推奨：3探索 arm 共通 `ceil(21259k)`、系列開始 stock・score をその内側とする設計には賛成です。block-stock の別基準も明示すれば妥当。`k` の確定、総 wall の倍率との関係、exact schedule・要求 walltime・発効 commit は別段へ返します。Tier0追加前・write-heavyのみ・共有 lock 下の実測という限定は残してください。`1800` を timeout と誤認しない plan の訂正も妥当です。

8. **nit — plan §4：既存 test のアンカーが誤っている。**

   根拠：`P:292` は未実装 header の assertion を `T/test_b5_generator_contrast.py:328` としていますが、実際は `:309`。`:328` は予算終了理由の assertion です。

   **影響：** 更新対象・変異対象の参照が別の契約を指します。

   推奨：行番号に加え test 関数名と対象式を記録し、U2 land 後に再照合してください。

全層の所有は、子の挿入点・sidecar＝U2、driver 分類・台帳・report・header＝U1 で覆えます。ただし所見1〜3の接続は未完成です。scheduler による中断原因の確定、§12 の hash・発効束、launcher の要求 walltime は、この実装で閉じたことにせず別段へ返してください。

## 総括

- **must-fix：3件。** 通過証拠の正常経路への接続、`tier0-interrupted` の停止漏れ、候補コンパイル失敗の分類境界。
- **P1：賛成。** 子の既存候補経路に置き、driver の build authority は増やさない。
- **P2：最小案として反対。** perf build のみを推奨。trace 前倒しは A/B 契約を変える任意の選択。
- **P3：賛成。** 既存 gateway・parser を再利用。timeout 実値の確定は必要。
- **P4：一部賛成。** Aのみ・retryなし・結果記録は必要。全 build 障害の候補帰属と score への自動適用には反対。
- **P5：追加開始印に反対。** 既存 attempt-start／slot-start／submission で計数できる。中断の詳細化と A/B 回収を分ける。
- **P6：条件付き賛成。** p=4 は運用選択として採用可能。配置からの導出と実測上限の一般化は棄却。
- **P7：条件付き賛成。** 共通 W の設計まで今回決め、倍率・総 wall 上限・発効は別段に残す。