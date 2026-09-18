## 検査範囲

指定資料はすべて読取可能。静的読解のみで、書込み・pytest・build・ベンチ実走は行っていない。以下、`V` は `t2774_probe-v4.py`、`R` は `t2774-README.md`、`O` は `operational-facts.md`、`plan` は `s2-plan.md` を指す。

## must-fix

**MF1 — defines の拒否は key・型までで、値の形式を被覆しない。**

- **どこ:** plan §2、42–62行・124–133行。`V:415–433`。`Options.cmake:60–87`。
- **何が誤りか:** `validate_defines` は空文字、空白、`"1;TRACE=0"`、`"-DCCBENCH_BACK_OFF=1"` を値として受理する。最後の例から生成されるのは `-DCCBENCH_BACK_OFF=-DCCBENCH_BACK_OFF=1` であり、意図した指定ではない。CMake 側には `foreach(item IN LISTS ARGN)` と空値を落とす処理があり、文字列なら単一の define 値として保存される、という被覆はない。実際の build 結果は未実測。
- **成果物への影響:** 不正値でも validation を通り、build 失敗による欠測、または意図と違う設定の binding が生じ得る。plan の JSON にある `"1"` 自体は正しいが、「fail-closed」という説明は値の形式まで成立しない。
- **修正案:** 七つの key に対応する値の許容形式を明記し、少なくとも空文字・空白・`;`・完全な `-D…` 文字列を拒否する。本 wave の実効差が BACK_OFF 一個だけである照合も残す。selftest は正常な arm に不正 `defines` だけを入れ、`validate_arms` 経由で拒否されることを確認する。未知 key・接頭辞違い・非文字列を検査する既存案は維持する。

**MF2 — 打切り時の「未開始」と、queue 未起動 block の主解析規則が未確定。**

- **どこ:** brief P1・環境、plan §4–5、229–249行。`V:274–281,317,533–556,667–668`。`dispatch_compute.py:4215–4238`。
- **何が誤りか:** 「未完走は計画数と実現数を分ける」だけでは次のケースを区別できない。
  - `run_one` の途中で終了すると、その走の `run.json` があっても `result.json.runs` には未追加となる。
  - 強制終了では `finally` の `not_started` 更新自体が実行されない。
  - queue 未起動では runner の `result.json` が存在しない。dispatcher も、未開始を肯定できる条件を対象 job の `QUE` 確認に限定している。
- **成果物への影響:** 実行中だった走を未開始に数える、欠落 block を計画数から消す、完走 block だけを事後選択する、といった差で N・欠測表・主解析対象が変わる。逐次保存は完了済み prefix の保護であり、全計画標本の会計ではない。
- **修正案:** 段4で、四 block の固定一覧、集計締切、利用可能な保存済み走を採用する規則、途中 block の扱いを固定する。block ごとに「保存済み」「開始証拠あり・未収載／未完了」「未開始確認済み」「状態不明」を区別し、原本を書き換えず親の会計表へ載せる。揃わない block は補充せず、揃った分で解析し、不足を明示する。

  所要の中心見積は妥当な外挿だが上限ではない。`90×300秒=7.5時間` は verifier だけの値で、run・準備を含めればさらに長い。walltime 02:30:00 を維持するなら、打切りを上記規則で扱うことを事前登録する。

**MF3 — runner SHA は insight の記載予定に留まり、実走 binding に入る変更がない。**

- **どこ:** plan §2、137行、§7、376行。`V:274–280,478–488`。`R:59–63`。
- **何が誤りか:** plan は「SHA とともに insight に束縛する」とするが、v5 の実装差分には runner の path・sha256 を binding に保存する処理がない。実行 argv の path だけでは、その時点の内容を識別できない。前 wave も、実走は v2/v3、再分類は v4 と版が分かれている。
- **成果物への影響:** smoke 後の修正や同じ path の差替えがあると、各 block の実走版と集計版を一意に復元できない。
- **修正案:** author の変更範囲に、実行開始時の runner path・sha256 の block binding 保存を加える。実走には保存した版を使い、各走を block ID・ordinal でその binding に対応付ける。insight には smoke／B1〜B4／集計それぞれの SHA を記す。全走への同じ SHA の重複埋込みは必須ではない。

## should

**S1 — arm 名だけの集計は、入力 binding の一致確認を代行しない。**

- **どこ:** `V:185–215,677–689`、plan §5・§8。
- **何が誤りか:** `summarize` は arm 名だけで合算し、pin・patch・defines・runner SHA を比較しない。入力 path の重複拒否も、別 path にコピーされた同じ block の重複までは被覆しない。
- **成果物への影響:** 同名 arm の設定違い、smoke、重複 block が混ざっても率と CP は計算される。
- **修正案:** runner の集計器は据え置き、親の集計手順に、固定 block 一覧、block ID の一意性、arm ごとの pin・patch 順序と SHA・実効 defines・witness・runner SHA の照合を明記する。その条件が満たされれば、今回の三 arm は名前が分かれており、defines を集計 key に追加する必要はない。binary SHA は保存するが、block 間の一致は要求しない（`R:68–69`）。

**S2 — 四 worktree と四物理 node は同義ではなく、submodule 初期化は対象 object の存在証明ではない。**

- **どこ:** plan §4、223–227行、`O:17`。`V:493–503`。`patchharness.py:346–368`。
- **何が誤りか:** checkout は各投入元の `base_dir` にある git object を使う。初期化済みという運用事実だけでは、全四箇所で e9e477ca を解決できることまでは確認できない。また四 job の投入だけでは異なる四 hostname を保証しない。
- **成果物への影響:** 一部 block が build 前に失敗する、または同じ node の別 block を「四 node の反復」と記載する可能性が残る。いずれも今回は未実測。
- **修正案:** 投入前に全四 base_dir で対象 commit の解決を確認する。launcher は各 worktree の dispatcher と対応する `--repo-root` を明示する。解析単位は B1〜B4 とし、実際の hostname を併記する。同一 hostname の再利用があっても、結果を見て置換しない。

**S3 — smoke と収集の成功条件に、退避先からの照合と具体的な集計入力を足す。**

- **どこ:** plan §4、239行、§7–8。`V:296–327,346–361,677–694`。
- **何が誤りか:** 「保存・集計まで到達」はあるが、保存先の JSON と raw の照合手順、最終 `summarize` の入力一覧が具体化されていない。三走の smoke で G2 が出なければ、G2 manifest 生成・保持の分岐は通らない。
- **成果物への影響:** summary の生成成功だけでは G2 raw の保全を確認できず、後続の cycle 表が保存資料と対応しない可能性が残る。
- **修正案:** smoke は三走の退避済み JSON と summary の読戻しまで確認する。G2 保持経路が未発火ならその旨を記す。本走後は B1〜B4 の実際の `result.json` を列挙して `summarize --inputs … --output …` を実行し、欠落 block は MF2 の別会計に載せる。G2 全件について manifest の file 数・byte 数・hash と、block／ordinal／arm／cycle txid／辺種／版を対応付ける。全 arm が witness off なので witness manifest を必須にしない（`V:323–327`）。

**S4 — warmup の妥当性は、argv と binary hash の確認だけでは証明できない。**

- **どこ:** plan §2、118–120行。`V:518–532`。`s3_mocc_lock_coverage.py:224–254`。`Options.cmake:10–11,60–68`。
- **何が誤りか:** plan 自身が認めるとおり、指定資料には Masstree target の定義がない。arm 別 argv と binary hash の確認は、共通 Masstree build に BACK_OFF が流入しないことの検査ではない。
- **成果物への影響:** 基底 warmup を共有してよいという根拠の被覆が不確実なまま残る。
- **修正案:** 基底 warmup 一回の方針は維持し、実装段で Masstree の build 定義または生成コマンドから CCBENCH define の非流入を確認する。smoke の binding 確認で代替できたとは記載しない。

**S5 — 一時ファイルの「実行・確認」の範囲と撤去条件を明確にする。**

- **どこ:** plan §8、391–407行。brief「不変条件」。D95:10–19。
- **何が誤りか:** 「親が一時ファイルを実行・確認し、…退避」の順序では、repo 内の一時版を本走に使うかが曖昧。「repo から消す」だけでは index に残っていないことまでは被覆しない。
- **成果物への影響:** 実走版と退避版の対応、repo 非収載という成果物条件が曖昧になる。
- **修正案:** 一時版での確認は selftest 等に限定し、byte 同一・SHA 一致で job dir に退避してから compute smoke／本走を行う。commit 前に working tree と staged diff の両方で一時ファイル不在を確認する。実装修正を author に戻す分担と、段6の二レンズ案は D95 と整合する。

**S6 — 親の実測値は、版・母集団・時点を伴わせて引用する。**

- **どこ:** brief P1、`O:3,10,16,20–36`、`R:60–63,117,142`、plan §4。
- **何が誤りか:** O は v4 の節に Q2 所要を載せるが、R によれば Q2 実走は v3。約22秒は五 arm・build 込み block 平均で、今回の三 arm の上限ではない。六分の queue 待ち一例と QUE 99 の snapshot から、四 job の起動時刻は予測できない。
- **成果物への影響:** 所要や達成標本の保証、検出力83%の適用範囲を広く見せる。
- **修正案:** 「v3 Q2 の観測からの外挿」と明記し、準備時間と走行時間を可能なら分ける。plan が修正した「直接対応 arm の p=.05 では約72%、p=.058・完全抑制なら約83%」を親 brief にも反映する。検出力は独立試行を仮定した計算値で、実測された性能ではない。

## nit

**N1 — 同じ source の二 arm は別 checkout・別 build であり、費用の説明だけ補えばよい。**

- **どこ:** `V:378–379,474,498–504,526–527`、`patchharness.py:362–368`、plan §4。
- **何が誤りか:** 共通 pin＋patch の `e9-instr-nowit` と bo1 が source を共有するように読める説明は不正確。
- **成果物への影響:** 率・binding には問題を認めないが、準備費用を過小評価し得る。異なる arm 名、一意 scratch、一意 checkout により、示された設計で build directory の名前衝突は認めない。
- **修正案:** 三 checkout・三 arm build＋warmup 一回として費用を記す。今回、source 共有の最適化は不要。

**N2 — arms の逐語と置換順には、指定資料内で誤りを認めない。**

- **どこ:** plan §2–3、`V:420–433`、`arms-q2.json:4–6`、診断 patch:4–35、`R:54–58`。
- **何が誤りか:** 訂正すべき逐語誤りは認めない。指定 patch path は読取可能、pin は前 wave と一致し、X/P → 診断の順序、全 arm の witness false、診断 arm のみ observational_only true、`CCBENCH_BACK_OFF: "1"` は整合する。ただし patch 適用成功は未実測。
- **成果物への影響:** 七 define を元位置へ展開する実装なら、後続の `CMAKE_EXPORT_COMPILE_COMMANDS` 等の順序は維持される。arm 自身の argv から `configure_defines` を取る修正も正しい。
- **修正案:** この逐語を維持し、実装レビューでは「BACK_OFF 一項以外の argv が同一」を確認する。`"1"` から `-DCCBENCH_BACK_OFF=1`、さらに `BACK_OFF=1` への対応は Options の記述と整合するが、target-private な最終コンパイル引数は生成物で確認する。

## 総括

**must-fix は3件。** define 値の拒否範囲、打切り・未起動の標本会計、実走 runner SHA の binding 保存を具体化する必要がある。

**GO — 上記を反映する plan v2 への改訂に進める。現行 plan のまま実装・本走へ進む判断は NO-GO。**
