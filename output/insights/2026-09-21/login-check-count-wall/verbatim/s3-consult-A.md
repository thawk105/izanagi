## 所見

参照略号：`J` = `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-login-check-wall`、`V` = `J/verbatim`、`R` = 指定 worktree。以下は静的検査結果であり、親 script の出力を再実測済みとは扱わない。

1. **real / must-fix — P1 の全史監査回数は、固定加算では定義できない。**
   `V/DW-O17.md:3–7` は通常 commit 後だけでなく ff・非 ff merge 後も full 監査を要求する。一方、受入の merge 後監査は `R/tools/dev_wave_wait.py:3838` の `behind > 0` 分岐内であり、claim 前監査にも到達前の失敗経路がある。`2 × attempt数` ではなく「claim 前監査への到達数＋merge 後監査への到達数」とする。親が行った前進 merge も義務対象だが、tool が同じ義務を履行した分を重ねて数えない。
   **放置時の影響：必須回数に過大・過小計上が混在し、「習慣による余分」の差分が成立しない。**

2. **real / must-fix — check_docs の義務を「docs commit ごと1回」に置き換えている。**
   `V/CLAUDE-sagyo.md:18` はクラス2/3の「完了変更」が対象で、docs-only に限らない。`V/spool-README-unyo.md:6–12` は fragment の commit 前検査、`V/DW-S07.md:11–12` は docs commit **後**の repo scan invariant・影響テスト再走を要求する。前後の異なる義務を1回に丸められない。post-claim merge 後も検査対象・checker が変わったかを確認する必要があり、全史監査だけで他検査の義務を履行したことにはならない。具体的に t2797 は merge 後 check_docs・focus 再走を記述する（`V/hyp-check_evidence2.txt:389–391`）。
   **放置時の影響：正当な再走が「習慣」に落ち、完了変更に必要な検査を削減候補へ入れる。**

3. **real / must-fix — fold・三軸語・land も、イベントと到達条件で数える必要がある。**
   `V/spool-README-unyo.md:19` は land 前に dry-run を rc=0 まで通す義務であり、fragment 検査と常に別の1回を要求してはいない。同じ検査対象で両義務を満たすなら共有可能だが、対象変更・赤後の再走は必要。三軸語は `V/DW-S07.md:8` の凍結前義務で、「wave 1回」を超えたら任意とはならない。land 全史監査も no-op・recovery では0回（`V/DW-O25.md:3–4`）、失敗・再試行を含めた実回数は landed 1件から決まらない。
   **放置時の影響：fold 必須数を過大計上し、凍結後変更への再検査と land 再試行を過小計上する。**

4. **real / must-fix — 「契約／tool内蔵／習慣」は排他的な3分類ではない。**
   land 監査は契約かつ機械強制である。義務の根拠と実行主体を別軸にする必要がある。また `--message-file` は full 監査と別実行であり、通常列・受入 merge・fold commit に存在する（`V/DW-O17.md:3`、`R/tools/dev_wave_wait.py:3862`、`R/tools/dev_wave_land.py:5081`）。依頼の5種表では full 回数に混ぜず、付帯検査欄へ出す。再試行・是正・影響確認も「必須数超過＝習慣」とは分類できない。
   **放置時の影響：branch-residue の preflight 10本が wall・呼出回数から消えるか、full 監査へ誤加算される。**

5. **real / must-fix — replay の warm 条件は実装と同一ではない。**
   `J/receipts_by_wave.py:153–162` は partition・bindings・祖先だけを見る。実装は権限・形式、schema、rc=0、selection の集合と digest、coverage、records 等も検証し、同 tip 再利用も許す（[check_ai_provenance.py:2451](/work/1/SFC/tanab/izanagi/.claude/worktrees/diag-login-check-wall/tools/check_ai_provenance.py:2451)、同 `2516–2574`）。さらに delta に raw correction 候補があれば再利用を捨て full へ戻る（同 `2634–2646`）。候補選択順も「最新mtime」ではなく距離・名前順（同 `2623–2629`）。
   **放置時の影響：warm/cold 表と原因表が、実際に full へ戻った走を warm とする可能性がある。**

6. **real / must-fix — 現在 store から実行時の cold は確定できない。**
   `J/receipts_by_wave.py:4–6` の限定は不十分。同 tip 上書きで消えるのは件数だけでなく、先行受領証が存在した時刻と内容でもある。終了時mtimeが先でも、対象走の lookup 時には未発行だった可能性がある。剪定も祖先優先・mtime順であり、単なる直近64件ではない（`R/tools/check_ai_provenance.py:2429–2444`）。現存35件というだけでは保存履歴全体の無剪定を証明しない。
   特に t2243 は親 log 終端22:49:39の後、同 tip の受入受領証22:54:10が replay cold とされる（`V/hyp-check_evidence2.txt:8–14`、`V/hyp-wave_timeline.txt:3–5`）。先行同 tip の喪失を疑う具体例である。
   **放置時の影響：「login cold 11」「現行 partition の偽cold 0」が確定値として過剰に見える。**

7. **real / must-fix — cold 原因は直近祖先との差分だけでは帰属できない。**
   `J/receipts_by_wave.py:165–184` は partition 不問の直近祖先1件との差を原因とするため、別環境の land 受領証を比較相手に選ぶだけで config/env 差が付く。これは再利用できなかった全候補の説明ではない。`V/D2192.md:15,37` と `R/tools/check_ai_provenance.py:2409–2419` には policy、epoch、cab_hits、registry_manifest 等の束縛もある。attributes 指紋差も `.gitattributes` の内容変更そのものとは限らない。
   **放置時の影響：「attributes 5＋checker 5」という排他的原因集計と、3分類で尽きるというP3が過断定になる。**

8. **判定不能 — t2797 の旧 checker 使用は支持されるが、cold 原因の確定までは支持されない。**
   `V/hyp-partition_table.txt:10` と `V/hyp-wave_timeline.txt:287–291` は `7c02fb2d…` から merge 後 `e69764c1…` への変更を示す。旧版との対応も `V/hyp-check_evidence2.txt:129` にある。ただし環境の checker 値は実行ファイル bytes のSHA-256であり、tip tree の同一性を単独で証明しない（`R/tools/check_ai_provenance.py:2396`）。旧partition内の先行受領証欠落・attributes差を除外できず、「旧版だから cold」の単独因果は未確定。
   **表への影響：旧checker使用を観測条件、coldとその原因を再構成仮説として分ける必要がある。**

9. **real / must-fix — env 指紋は主体・実行ノードの識別子ではない。**
   `LC_ALL=C` と `GIT_CONFIG_GLOBAL` の存在は land の必要な特徴には合うが、値 `/dev/null` や他 override を照合しておらず十分条件ではない（`J/receipts_by_wave.py:112–116`、`R/tools/dev_wave_land.py:564–579`）。受入も親環境を完全継承せず、一部Git変数を除く（`R/tools/dev_wave_wait.py:650–659`）。`LC_CTYPE=C.UTF-8` から別shell／計算ノードdispatchを特定できない。
   **放置時の影響：「login 46／land 12」が実行主体・実行場所の確定内訳として誤読される。**

10. **real / must-fix — commit所属と監査呼出主体の所属が混同されている。**
    `J/receipts_by_wave.py:75–83,143–151` の集合帰属では、既存main tipを監査する受入ref走を落とし、他waveのtipを使った走を元waveへ帰属させうる。amendで到達不能になったtipは `--all` のグラフからも落ちる。時刻窓が1候補でも、対象外waveを除外できない。
    t2817 のref attemptは `2afb39768` を入力tipとする（`V/hyp-wave_timeline.txt:251`）。4 attempt・4 mergeなら現行経路は8監査だが、帰属受領証は7件。欠けた1件は集計単位の問題を実際に示す。
    **放置時の影響：wave別回数を過小計上し、共有受領証によるwave間の移し替えを見逃す。**

11. **real / must-fix — attempt・検査log抽出に既知の欠落がある。**
    `J/wave_timeline.py:56–63,98–99` はchain表記に依存し、summaryでは t2814 が attempts=0／started=2、t2797 が0／3となる（`V/hyp-wave_timeline.txt:403–413,455–464`）。また検査抽出は直下の名前検索で、script内の文字列は実走証拠ではない（`J/check_evidence2.py:37–61`）。t2814 のdry-runは通常3本に加えて land前1本が見えており、wave総数なら少なくとも4本の痕跡がある（`V/hyp-check_evidence2.txt:220–231`）。
    **放置時の影響：attempt 0やfind-fold-owned 0を実行ゼロと誤記し、必須数・実行数とも欠落する。**

12. **real / must-fix — docs-only分類をcheck_docs対象変更数に流用できない。**
    `J/wave_timeline.py:45–47` は `.md` を含むため `.claude/commands/*.md` は拾うが、`docs/`・`output/insights/` 以下のコードもdocs-onlyにし、mixed commitを落とし、mergeを未分類にする。`tools/check_docs.py` 自身の変更も検査への影響を持つ。実際 t2814 は拡張子上docsの変更に whole-file pin追随が必要だった（`V/hyp-check_evidence2.txt:243–247`）。check_docs走査対象の完全な一致は、今回の射影に同checkerがないため判定不能。
    **放置時の影響：docs-only件数から導いたcheck_docs必須回数と、実装面0行の判断を誤る。**

13. **refuted — 同tip上書きとrange非発行というP4の実装上の主張は正しい。**
    path は partition内の `<head>.json`、発行は `os.replace`（`R/tools/check_ai_provenance.py:2421–2422,2498`）。`authoritative = args.rev_range is None`、rangeではreceipt_stateを作らない（同 `3777–3790,3867–3868`）。ただし上書きは**同partition内**に限る。rangeはfull監査の「見えない回数」へ足さず別モードにする。
    **表への影響：P4の別列方針は維持できるが、受領証・log・handoffは同じ実行を示しうるため単純加算しない。**

14. **real / must-fix — branch-residueの「親log 5＝受領証5」は、実行数の一致ではない。**
    親の5本目は04:15:07、同tipの受入受領証は04:19:31（`V/hyp-check_evidence2.txt:323`、`V/hyp-wave_timeline.txt:269–271`）。両者を対応付ければ、親5走＋受入1走で少なくとも6走の痕跡があり、現存login受領証は5件である。t2817の7件も「受入走と整合する」以上に、親監査の有無や全wave共通の上書き率を示さない。
    **放置時の影響：P4を掲げながら、実行数をunique receipt数で代用し、親側の削減余地を誤推定する。**

15. **real / must-fix — mtime差を検査wallや親手番へ直接変換できない。**
    `.err` は空なら作成・truncate時刻の候補だが、非空なら最終書込時刻である。t2814の `.err` は10bytesでJSONと同mtime（`V/hyp-check_evidence2.txt:224–229`）。preflight→full終端の間にはcommit・起動・待ちも入る。started→受領証も前段処理を含み、受領証発行は終了処理全体の終端ではない。したがって13–19秒、36–47秒、12秒、41–112秒は区間定義ごとに分ける。`*.time` の存在が示されるt2803は、まずその計測値を読むべきである（同 `75,84,97`）。
    **放置時の影響：前提22／58秒と代理区間が混ざり、検査wall・負荷差・短縮率を誤表示する。**

16. **real / must-fix — P2の15–20分／waveと「残差28%の一部」は未証明。**
    branch-residueの95・83秒は完了log間隔2点であり、親手番のみではない。t2814の4・12秒も異なる処理間隔で、call境界や因果比較を証明しない。算術も `80–95秒 × 10–15回` は **13分20秒–23分45秒**。entry1776の標本は今回と異なり、残差は「合計−実行区間union」で親実働ではない（`R/output/insights/2026-09-21/dev-wave-wall-decomp/README.md:13,16–17,45–50`）。今回との共通waveは t2344・t2803・t2804 の3本だけ。
    **放置時の影響：仮説を平均削減効果として掲載し、並走中の時間まで残差から二重に回収する。**

17. **real / should — 保存資料のsnapshot整合と観測カテゴリが不足する。**
    `J/s1-brief.md:16` は495件、`V/hyp-receipts_summary.txt:2` は496件。帰属58件＋未帰属430件＝488件で、残る8件が要約に説明されない。scriptは曖昧帰属を文字列で持ち、未帰属集計から除くため、曖昧8件の可能性がある（`J/receipts_by_wave.py:151,208,218`）。またland同定は出力fileの最終mtimeで、追記・複製による順序変動を含む（`J/list_landed.py:55,65–71`）。
    **放置時の影響：母集団・除外件数・対象12本の再現性が揃わず、probe間の数字が照合できない。**

18. **判定不能 — 「仮説」表示だけで親script本文をrepoへ収容できるとは確認できない。**
    `J/s1-brief.md:29` は「repo実装面0行」と「親scriptをverbatimに残す」の意味が曖昧。射影資料の先例はscript本体をrepoへ入れずhashで束縛する（`R/output/insights/2026-09-21/dev-wave-wall-decomp/README.md:5`）。D95本文・凍結境界の詳細は今回の射影にないため最終判断は不能。「仮説」のラベルや著者変更は、観測不能な値を確定値に変えない。
    **表・成果物への影響：script本文まで収容すると、実装面0行・変異免除の前提を再点検する必要が生じる。**

## 親 brief への指摘

P1は「義務の発火条件と、その義務を履行した実行」の対応表へ変更する。契約必須数は単純なcommit数から出さず、通常commit、親merge、受入merge、凍結、fragment変更、land到達を区別する。義務との対応が不明な追加走は「習慣」でなく「理由未同定」とする。

P2は「束ねによる短縮の候補」へ弱め、15–20分／waveという代表値を外す。entry1776の7.2分は別標本の重なりを含む値で、今回の5検査総和の分解元にはできない。

P3は「現存storeから再構成した候補条件と差分」に変更する。**実cold／再利用可能候補あり／再構成不能**を区別し、原因は重複可能にする。

P4の別列方針は妥当。ただし列は「実行証拠の下界」「現存受領証数」「handoff記述」「未観測」を分ける。観測0は実行0ではない。失敗・非発行・上書き・剪定も明記する。

並走cold診断への分担は妥当。本waveにはlandの実行証拠数、成功・失敗・未観測、tip/checker/env、warm/coldの確度だけを残し、環境変更の実装や連鎖の因果分析は持ち込まない。

## 段 5 probe 仕様に入れるべき変更

3機能は必要だが、3本の独立scriptである必要はない。**受領証照合とイベント表の2本**にし、gapをイベント表から導出すれば重複抽出を減らせる。

- **入力固定・収支**：採取時刻、入力hash、full SHA、mtime_nsを保持。対象・対象外・曖昧・読取失敗を別集計し、総数と一致させる。旧checkerの走には当該版のreplay条件を対応させる。
- **受領証照合**：形式・rc・selection・coverage・records・correction fallbackまで確認。同tip履歴、lookup時点の存在、mode等を復元できなければ確定warm/coldを出さない。直近祖先との差は「比較差分」と表示する。
- **実行イベント表**：full／range／message preflightを分離。主体・ノード・環境特徴を別列にし、logと受領証をtip・時間・attemptで対応付ける。ref走、amend前tip、失敗attempt、land前dry-runを含め、対応不明を残す。
- **wall**：`time`等の直接計測、開始終了が裏付けられた区間、mtime代理区間、前提値、未観測を別列にする。check_docs・三軸語のwallが取れなければ空欄理由を示し、新規計測で補完しない。
- **効果計算**：前提モデルは `22×warm数＋58×cold数` と明記。cold不明数を勝手に割り振らない。束ねは削減可能なcall間隔を個別に挙げ、検査実行時間や並走区間を差し引けない部分は条件付き試算に留める。

親script本体はJへ残し、repoにはhash・由来・仮説出力を収容する形を推奨する。新しい永続台帳・gate・検査機構は不要。

## 裁定パッケージへ返すべき択一

| 択一 | 推奨・境界 |
|---|---|
| 記録前後の検査を個別call／同一shellで順次実行 | **同一shellでの順次実行を候補にする。** `V/DW-O17.md:6–7` に既存の許容がある。先頭`set -e`、検査rcをpipeへ渡さず、赤で停止し、commit前後の順序を保持する。3検査を1callにすればcall境界は2個減るが、検査は0回減。 |
| 親commit直後のfull監査／受入claim前監査へ集約 | **現行維持を推奨。** 集約はDW-O17の通常列を変える裁定であり、単なる重複削除ではない。最終tip、途中の停止条件、受入に到達しない場合、merge後の義務をどう保つかが未解決。規律2・正しさ防壁に触れる。 |
| fragment検査とland前dry-runを別走／同一結果で両義務を充足 | 対象fragment・canonical base等の検査入力が変わらない場合に限る候補。対象変更後まで省略する案は不可。削減数はイベント照合後に提示する。 |
| land envをloginへ寄せる／分離を維持 | **分離維持を推奨。** Git config・attributes入力を変えるため、cache効率だけの変更ではない。環境束縛を削る案も正しさ防壁に触れる。本waveでは実装せず、並走診断へ渡す。 |

D690の5分は「自分に起因しない赤への着地対応」の上限であり、land監査の480秒とは別契約である（`V/D690.md:4–9`、`V/D254.md:8`）。いずれの択一も両者を変更しない。

## 総括

**診断のscopeは妥当だが、P1の固定回数、P2の平均効果、P3のcold確定値は現状のまま採用できない。** P4の実装根拠は確認できた。

優先修正は、義務と実行の対応付け、受領証replayの不確実性、主体別帰属、wallの出所分離の4点。指定必読資料は読了。ファイル変更・probe実走・テストは行っておらず、実走確認済みの緑は報告しない。