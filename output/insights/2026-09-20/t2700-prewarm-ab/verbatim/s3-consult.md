## レンズ A

**現状のまま「6 対で検出力 0.75〜0.87」を事前登録することには反対する。** W_max を主指標にする目的は妥当だが、機序の観測量、検出力の対象、失敗走の扱いを修正する必要がある。

先に「必要走数を確定できない」とする条件を定義する。次のいずれかが残る場合、その結論を insight に明記すべきである。

- 同一測定条件に対する ΔW_max の効果量・分散を、過去データから移せる根拠がない。
- 採用する検定・15 秒閾値・失敗処理を合わせた判定規則について、目標検出力を評価していない。
- 妥当な効果量・分散・非対称性の感度範囲で必要対数が予算上限をまたぐ。
- treatment に依存する失敗・欠測が残り、成功走だけの推定と運用上の効果を区別できない。

現在はこれらに該当する。以下、行番号は指定された worktree または射影ファイル内の番号である。

**must-fix A1 — H、D と介入の範囲を修正する。**

根拠: `conftest.py:2334–2431,2495–2517,2589–2630`、`xdist/dsession.py:103–105,274–307`、`acceptance_shards.py:924–938,1013–1092`、brief:16–18,27。

L では controller が collection 通知を処理する hook 内で同期 barrier を待つ。`DSession.worker_collectionfinish` はその hook が戻ってから scheduler に collection を渡して配布するため、**正常な L の prewarm は test 配布より前に完了する**。ただし、最初の通知時点で他 worker はまだ collection 中かもしれず、「その間すべて idle」は強すぎる。

H は controller の collection 完了時刻ではない。xdist controller は自身の collection を短絡し、report の値は **worker が記録した collection-finish 時刻の最大値**である。E では conftest の `tryfirst` hook が memo を待ち、その後 acceptance plugin の `trylast` hook が時刻を記録する。したがって E の H は早期待ちを含む。H ≈ D は「collection と resolver が完全に重なった」証拠ではない。

D も scheduler の送信時刻そのものではなく、test report の最初の開始時刻である。機序の代理指標としては使えるが、D−H を resolver の純所要とは扱えない。L の barrier 開始から最遅 worker の collection 完了までの重なりは D−H から落ちる。

さらに opt-out は receipt だけでなく **oracle memo の早期起動と全 worker の待ちも切り替える**。E は consumer 不在 shard でも両 memo を準備し、L は consumer に応じて準備する。「変わるのは起動時点だけ」という説明は厳密には成立しない。

成果物への影響: ΔD_0 を ΔW_max の予測値と同一視し、27 秒の効果とその原因を過大に確定する。

是正案: 介入を「T-2616 の早期 memo 機構全体の有無」と定義する。H は「worker の待ちを含む collection-finish 最大時刻」、D は「最初の test 開始」とする。W_max、全 shard の W/H/D、receipt・oracle・barrier の所要を併記し、追加計装なしでは配布時刻・純 collection 時間・CPU 競合を分離できないと明記する。

**must-fix A2 — 6 対の検出力と必要対数の計算が、採用する判定規則に対応していない。**

根拠: brief:19–21,38、`power.py:2–3,19–25`、plan:38、T-2766 README §5。

0.75〜0.87 は正規分布を仮定した t 検定の評価であり、P4 の「片側 exact Wilcoxon **かつ中央値 ≥15 秒**」の検出力ではない。

σ_d≈√2×11.8 は、等分散かつ対内共分散ゼロの近似にすぎない。一般には
Var(L−E)=Var(L)+Var(E)−2Cov(L,E)。隣接していても allocation は異なり、相関は未測定である。加えて T-2766 の A/B は順序変更の異なる workload で、今回の E/L 分散と同じとは限らない。

T-2766 の提示された有効対差 101.706、112.871、144.324 秒から直接計算した標本 SD は **22.10 秒**。これも n=3 で移植可能な推定ではないが、「同じ先行走から17秒だけを採る」根拠の弱さを示す。最忙 worker の構成変化、L の右裾、node・時刻差を含めれば25秒超も排除できない。

plan の `t_crit×σ_d/√n` は t 検定の有意化境界に相当し、80%検出力の MDE ではない。必要数式も n に依存する臨界値、`t_0.8` の定義、P4 との不一致が未解決である。

成果物への影響: 「必要6対」「不足時の追加必要数」「MDE」が、実際の判定能力と異なる値になる。

是正案: P4 を維持するなら、その全判定規則を使い、δ=15/20/27秒、σ_d=17/22/25/30秒、非対称・外れ値を含む感度分析で n=6/8/10等を評価する。6対は現時点では**予算固定の探索測定**としてのみ支持する。8対は改善案だが十分性は未証明であり、16走上限なら取り直し余地がない。3対の D_0 測定への変更は機序探索にはなるが、W_max 短縮という起票目的の代替にはならない。無補正の途中検定・有意になるまで追加は採らない。

**must-fix A3 — P4 の exact、同順位、ゼロ、推論対象を固定する。**

根拠: brief:38、plan:38、`power.py:28–30`、D357。

指定された反例は次のとおり。

| 対差 | 片側 exact の結果 | P4 の判定 |
|---|---:|---|
| +40秒×5、−45秒×1 | 絶対値の平均順位は3,3,3,3,3,6。符号を全列挙すると **17/64=0.265625** | 未確立 |
| 異なる正差5個と、絶対値最大の負差1個 | 同順位なしなら **14/64=0.21875** | 未確立 |
| 全6対が+5〜+10秒 | **1/64=0.015625** | 方向のみ支持、15秒未満 |
| ゼロ差を含む | ゼロ除外後の m で列挙 | m≤4なら全正でも p≥0.0625 |

最初の例を「5勝だから支持」に変更すべきではない。大きな逆方向の差を含み、小標本では不確実という結果を受け入れるべきである。ただし同順位を勝手に1〜5位に分ける実装では p が変わる。

符号順位検定の exact 性には、帰無下の符号対称性・独立性などの前提が要る。非対称な対差でも「中央値ゼロの検定として常に exact」にはならない。順序を決め打ちで交互化しているため、無作為割付に基づく exact な因果検定とも説明できない。

片側は「改善だけを支持判定する」と事前固定すれば選べるが、機序は退行不可能を保証しない。15秒は27秒の厳密な半分でもなく、σ_d は価値基準ではない。「機序予測の半分・約1σ」だけでは実用閾値の根拠が弱い。

成果物への影響: 同じ対表で p・支持判定が変わり、対称性を満たさないデータに過強な有意差主張を付ける。

是正案: 平均順位、ゼロ除外、m=0、標本 SD=0、欠測時の出力を固定し、上表を selftest に入れる。15秒は独立した運用上の閾値として理由を述べるか、便宜的な探索閾値と明記する。「p≤0.05かつ標本中央値≥15秒」は母効果≥15秒の証明ではない。t は記述的併記に留める判断を支持する。D357 の10%は単走差の扱いであり、反復対差の15秒閾値を導出・禁止する規則ではないが、各単走差を10%未満の改善実績として数えてはならない。

**must-fix A4 — E 固有の失敗を捨てる P6 は、今回の主張に対して選択バイアスを作る。**

根拠: brief:23,37,40、plan:35–36,45、T-2766 README §5 01-A、D2062、`real_repo_receipt_memo.py:645–698`。

今回の treatment 自体が早期待ち timeout を発生させ得る。E の遅い・失敗する走を除いて6緑対まで補充すると、推定対象は「両腕が成功した選別後の走」に変わる。T-2766 では両腕とも早期機構が有効だったため、その除外規則を今回へ無条件に移せない。

120秒は session 開始からではなく、worker が待ちに入ってからの共有 deadline である。また「E の特定 timeout 分岐が L にない」と「L は失敗しない」は別である。

成果物への影響: 失敗率を脚注に残しても、W_max の支持判定だけが E に有利に偏る。

是正案: 成功走の速度と全投入の成功・失敗を別の推定対象として事前登録する。最小案は、treatment 関連失敗を捨てず、発生時には無条件の「受入短縮を支持」を出さず「成功走に条件付きの速度差」とすること。失敗を符号上の敗北にする感度分析も可能だが、∞を通常の Wilcoxon・t・SD に混ぜてはならない。両腕失敗、原因不明、成果物欠損、再試行の上限到達を規定する。再試行分は別 attempt として全件残す。

**should A5 — 親の前提実測は、標本選択と一般化の限界を表にする。**

根拠: `head_stats.py:9–26,32–46,68–74`、`dist_start.py:29–31`、`dist_start-output.txt:1–48`、brief:16–18。

- L は hook が存在する shard から選ばれる。したがって、この抽出だけでは「L の shard-1/2 は必ず不発火」を検証できない。
- E は直近40 shardの選択後に timeline 欠損等を落としている。提示出力は shard-0=13、shard-1=13、shard-2=14で、**合計13 shardではない**。
- `head_stats.py` は表示時には shard_count=3で絞るが、保存 rows と、それを読む `dist_start.py` の集計では同じ絞込みがない。
- rcを保存しても緑条件では絞っていない。177と13という数だけでは、有効標本の同等性を保証しない。
- 「E で resolver が55秒なのは CPU 競合」「tail 10.0対7.1は tip差」は候補説明であり、提示資料では原因を同定していない。
- 476/236/200は別々の中央値。今後も shard-0 が最遅という保証ではない。E の他 shard の追加仕事は共有資源競合や失敗を介しても W_max に効く。
- L の shard-1/2 の D が提示されていないため「E が約4秒不利」は直接比較ではない。

成果物への影響: δとσの根拠表が、異なる母集団・欠測・未実測の原因説明を混ぜたものになる。

是正案: 条件別に抽出数、除外理由、session数、shard数、日付、SHA、緑条件、schedulerを列記する。歴史データは仮説形成に限定し、上記の原因説明は条件付きに直す。

**nit A6 — brief の tail 定義だけ単位が一致しない。**

根拠: brief:44、plan:33、`dist_start.py:37`。

成果物への影響: plan の式で実装すれば数値は変わらない。brief を実装仕様にすると epoch の引き忘れになる。

是正案: brief も `W−(last_finished−timestamp)` に統一する。

## レンズ B

**P1 の属性経由という設計と、正常な L の同期 prewarm 経路は静的には成立する。** 問題は、その結線を検査する test と、成果物を有効と判定する仕様の不足である。

**must-fix B1 — helper 直呼びだけでは configure 結線を証明できず、M1 の期待 kill も誤っている。**

根拠: plan:12,23–27,51、`test_real_repo_serialization.py:550–557,6423–6469,6608–6644`、`conftest.py:2925–2946`。

`_load_suite_conftest` はファイルを別 module として実行するだけで、pytest plugin として登録して `pytest_configure` を呼ばない。synthetic config に属性が付かず既存 test が E 経路を維持する、という P1 の説明は正しい。

反面、新 test が `_configure_early_memo_opt_out` を直接呼ぶだけなら、**本物の `pytest_configure` からの呼出しを削除しても全 test が緑になり得る**。

M1 の恒真化は新しい E 負例では落とせるが、既存 `test_early_memo_narrowing_destinations_match_real_parser` は helper を呼ばないため、記載された kill は成立しない。また L 正例で `ids=()` と barrier の hook 名だけを見る案は、実際の memo 公開を証明しない。

成果物への影響: L のつもりで E を測る実装、または L で cache が作られない実装を単体検査が通し、測定走を浪費する。変異表にも誤った帰属を記録する。

是正案: 実 `pytest_configure`→属性→`pytest_configure_node` の結線を検査する。無関係な依存の隔離は可能だが、対象 helper・選択判定・結線は stub しない。L 正例は receipt/oracle の実 consumer ID を与え、同期 hook 復帰時の cache 実在と reader の成功まで確認する。M1の期待 nodeを訂正し、「configure 呼出し削除」を追加または既存変異と交換する。

変異帰属は次のように限定すべきである。

| 変異 | 帰属させる検査 |
|---|---|
| M1 恒真 | 新 E 負例。既存 parser test は対象外 |
| M2 属性を置かない | helper/実 configure 後の属性検査 |
| M3 属性 check 削除 | 属性がある config の選択・起動検査 |
| M4 allowlist key 削除 | exact pin と実 request 生成の検査 |
| M5 不正値を受理 | 不正値の例外検査 |

独立 clone のディスク上の conftest を変異すれば別 module にも見える。一方、外側で import 済みの module だけを monkeypatch しても、再ロードされた module には反映されない。mutation対象パスと読み込んだ `__file__` を一致させる必要がある。

**must-fix B2 — L の伝播は設計上通るが、E の unset と、存在しない先行 test を修正する。**

根拠: plan:27,34,44、`run_tests.py:1290–1304,1320–1324,1402–1444,1509–1533`、`dispatch_compute.py:119–135,1661–1665,1820–1853,3693–3696`、`test_pegasus_dispatch_compute.py:6260–6269`。

L の exact token は、allowlist追加後には次の経路で保持される。

| 段 | 静的確認 |
|---|---|
| login runner→dispatcher | `_dispatch_environment` が環境をコピー |
| dispatcher→request | allowlistにある存在するkeyを採取 |
| request→compute runner | inheritした環境へrequestをoverlay |
| compute runner→shard pytest | `os.environ.copy()`。削除はshard指定等で、新keyは残る |
| controller→通常のlocal xdist worker | 継承環境を利用する構成。最終実測は未実施 |

login の独立 collect-only にも key は残る。exact tokenなら新 parser は例外を出さず、collect-only は既存選択条件で早期起動しない。不正な非空値なら login でも UsageError になる設計である。

問題は、plan:44の「Lだけ設定」では E 実行時の継承済みtokenを消した保証にならないこと。また `_job_run` の inherit+overlay は、requestでkeyが欠けていてもcompute側の同名keyを消さない。

さらに現 worktree の指定 test fileに `PAIRING` は存在しない。`IZANAGI_RUN_GROWTH_HELD_TESTS` も検索結果はexact pinの1箇所だけで、指定された専用伝播testはない。T-2766実装がmainにない運用と整合する。

成果物への影響: E が L として走る、または意図しない不正値で失敗する。存在しない test を前提に伝播被覆を完了扱いする。

是正案: launcherでEのkeyを明示unsetし、実効環境を記録する。compute側残留まで排除するなら、Eに空文字を明示overlayする方式を採り、「Eは不在」という検算仕様を「不在または明示空」に合わせる。新keyのrequest生成とcompute childへのoverlayを実際に検査する。既存の参考箇所は `test_pegasus_dispatch_compute.py:6747–6765` のbytecode環境伝播test等であり、PAIRING testの存在を前提にしない。

**must-fix B3 — 集計器の入力契約・有効走・witnessの根拠が未確定である。**

根拠: plan:31–38,44–45、D2164決定1、`conftest.py:920–938,978–995,2474–2492`、`acceptance_shards.py:894–920`。

具体的に以下が欠ける。

- 読み取り先は `dispatch/izdw-shard-N.e*`、launcherの複製元は `dispatch/shard-N/izdw-shard-N.e*`。平坦化するのか階層保存するのか未定義。
- globで複数jobのstderrが見つかった場合、どのreceipt/requestに対応するか未定義。
- `pytest_rc` は走表にあるが、有効条件には各reportの0確認が明記されていない。SHA256も保存するだけか再検算するか不明。
- session、shard index/count、選択集合・schedulerの一致、receipt終端状態、開始・終了時刻の非重複を検算項目にしていない。
- timeline欠損、空worker集合、naiveなJUnit timestampのtimezoneを扱う仕様がない。解析ホストのローカルtimezoneで解釈すると H/D/tail がずれる。
- receipt不発行・report無しの失敗走でも `run.json` と存在するlogを保存する処理が必要。必須ファイルのcopy失敗で記録自体を失ってはならない。
- slotに複数attemptがある場合の組合せと、16走で6対未達時の出力が未定義。

witnessは、緑走の正しいstderrにある `configure_node` 行なら早期barrierが仕事を行った根拠になる。ただし行はjoin後、例外再送出前にも出るため、**起動時刻そのものや成功だけを証言するものではない**。

Lで行が出ないコード上の理由は、receiptとoracleの両方が prerequisitesを満たさず timingが記録されないこと。shard番号による分岐はない。「shard-1/2にconsumer不在」は固定SHAの `selected` と両consumer registryで検算すべき条件であり、提示された履歴抽出だけから現tipでの成立を断言できない。

成果物への影響: 正しい走を無効化する、異なるjobのwitnessを採用する、または失敗走を走表から消して対表・判定を変える。

是正案: 保存layoutを一つに固定し、receiptに結び付いた相対path・hashのmanifestを集計器が検算する。現在の測定では必要field欠損を明示失敗とし、歴史データでは欠測数を残す。timezoneを固定・記録する。Lの期待witnessは事前のconsumer配置から確認する。試行単位、隣接性、逐次性、上限、未達終了をselftestに含める。

**should B4 — P1の境界は支持するが、非再入性とworker側の意味を明記する。**

根拠: plan:9–13、`conftest.py:2314–2331,2415–2418,2528–2560,2925–2946`。

新属性名は提示範囲の既存属性と衝突しない。workerにも属性が付くが、起動は既存worker guardで除外される。workerの待ちは属性ではなく `workerinput` のjob keyで決まる。新parserを既存try内に置く案は、UsageError時の両nonce復元と整合する。

直接envを読む代案はsynthetic testまでLに切り替えるので不適切。acceptance pluginのshard属性設定箇所へ置く代案は結合先と被覆面を増やす。`PYTEST_ADDOPTS` は新optionの登録・parsed-option面との整合を要し、今回の縮小にはならない。

ただし「Falseなら属性を置かない」は同じconfigをTrue→Falseで再設定しても旧属性を消さない。通常の一回configureでは問題ない。

成果物への影響: 同一configを再利用するtest/再入経路があればEのつもりでもLになる。

是正案: 一config一回という契約で検査し、再入を要しない限り属性リセットの一般化は足さない。E負例は新configを使い、環境の未設定と空を明示して外側L環境から隔離する。

**should B5 — L の正常経路は生きている。追加修復ではなく、その境界をtestで固定する。**

根拠: D518、D2062、`conftest.py:2559–2560,2589–2630`、`dsession.py:287–307`、`real_repo_receipt_memo.py:645–698`。

opt-outで早期jobがなくなるとworkerの早期待ちは即returnし、controllerはconsumer collection通知で同期prewarmする。hook復帰前には配布されないので、同じHEAD・run ID・nonceの正常走で「consumerがwriterより先にcacheを読む」という競合は見つからない。120秒deadlineもearly job明示時だけで、Lへ無条件に適用されない。

成果物への影響: Lを復活させる追加実装を足すと、起動方式以外の差を測定へ混ぜる。

是正案: 既存L経路を変更せず、B1の実cache正例で固定する。登録漏れconsumer、HEAD変更、cache消失等まで「Lでは起こらない」と一般化しない。

**nit B6 — 実装規模と非landing運用は概ね妥当。**

根拠: plan:9–18,39–40,52、D2164決定3。

成果物への影響: 定数3・helper2自体を減らしても走表・判定は変わらない。汎用化は不要で、足りないのはB1〜B3の結線と検算である。

是正案: 実装はimpl branchへ保存し、landingは測定記録のみという方針を維持する。再現用に測定SHA、実装commit、launcher・集計器の逐語とhash、事前登録版を残す。他waveの対照は任意の記述資料とし、その欠測を主解析の停止条件にしない。

## 総括

**must-fixは7件（A1〜A4、B1〜B3）。** 静的読解のみで、pytest実行・ファイル書込みは行っていない。

| provisional裁定 | 判定 |
|---|---|
| P1 属性経由のopt-out | **支持**。configure結線と実L cache経路の検査が必要 |
| P2 W_max主、D_0副、stderr witness | **条件付き**。H/Dの意味、両memoへの介入、consumer配置、log対応を修正 |
| P3 有効6対・最大16走・取り直し | **条件付き**。探索予算としては可。必要数の根拠と失敗処理は現状不可 |
| P4 exact Wilcoxon＋中央値15秒 | **条件付き**。同順位・ゼロ・対称性・閾値の意味と検出力を固定 |
| P5 軽量段構成＋review＋変異 | **条件付き**。M1期待killを訂正しconfigure呼出し欠落を被覆 |
| P6 E timeoutを除外して件数だけ記録 | **反証**。今回のtreatmentに依存する選択バイアスを残す |

**必要対数は現資料から確定できない。6対を「検出力0.75〜0.87の必要数」としては支持しない。** 6対固定の探索測定は可能。8対は感度分析後の候補であり、十分性はまだ言えない。D_0の3対への置換では起票目的を満たさない。

**envは、allowlist追加後のL exact tokenについて全段を通る設計である。** 現コードには新keyがなく、全段の実測証明は未実施。Eの不在はinherit+overlayだけでは保証されないため、launcherの明示解除または空overlayと、対応する検算を確定する必要がある。