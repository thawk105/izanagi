## 所見

以下、資料名は `/home/SFC/tanab/.claude/jobs/0a534e2c/tmp/` 内を指します。原本 XML の読取り検算を実施しました。pytest・計測は実行していません。

1. **real | must-fix — P1 は機序の支持から因果の確定へ飛躍している。** `conftest.py:670,2161` と `252e24b4f` の first-parent 差分は、t1259 の30関数を接尾除去の例外にしたことを支持する。しかし testcase 所要から fixture の開始・終了時刻やピーク同時数は復元できず、「42〜46本同時」「主因を分離した」は未証明。根拠：`adjudication.md:12`、`f945-supersede-draft.md:7`。**成果物への影響：F945 は「grouping 後の改善を観測、重複走査の寄与を示唆」までに限定する必要がある。**

2. **real | must-fix — 前後の母集団が混在している。** survey の個票を集計すると、前 regime は **18走・成功代理値713件・error87件・成功30秒超145件・max58.874秒**、後 regime は23走・代理値23件・error0。brief の14走・567件・59件、および依頼の102件とは別集計である。後 regime の最大24.494秒の session は survey 上 **overlap=0** で、「前 regime wave 並走時」という説明とも一致しない。根拠：`survey-1.md:9–18,38–40,239`、`brief.md:8–14`。**成果物への影響：対象 session 一覧と抽出時点を固定しなければ、分布・負荷条件・採用根拠を再現できない。**

3. **real | must-fix — error 件数を独立した右打ち切り走査数にしている。** 集計器は `<error>` をすべて「30秒右打ち切り Git 観測」とするが、fixture の例外 cache による再掲を区別しない。原本検算では87 error中13件が2秒未満。例えば session `702141…` は14 error中4件が0〜0.001秒で、30秒の新規走査ではない。根拠：`junit_scan_survey.py:68,77–78,94`、`survey-1.md:469–475`。**成果物への影響：「59件／87件の打ち切り標本」ではなく「setup error件数」と記録し、独立した走査試行数は別途不明とする必要がある。**

4. **real | must-fix — testcase 合計時間、Git 呼出し単位の上限、lock deadline が混同されている。** 成功 testcase が30秒を超えても、各 Git 呼出しが30秒未満なら矛盾しない。120秒は4呼出しそれぞれに適用され、合計120秒にはならない。245秒はlock取得待ちの期限であり、取得後の snapshot を打ち切る期限ではない。根拠：`author-u1.patch:193–225`、`brief.md:46–47`、`conftest.py:1036,1495,1528`。**成果物への影響：「120 < 245だから安全」「1走査が採用値を超えれば再発」を削除し、単一 Git 呼出しと全体所要を分ける必要がある。**

5. **real | must-fix — P3 は事前の判断規則にはなるが、120秒の実測導出にはならない。** `max ≤ 60` は、60・90・120・180秒のうち120だけを支持しない。max の対象も、junit合計・samplerのGit別・sampler合計のどれか曖昧。根拠：`adjudication.md:16–17`、`rulings-verbatim.md:5–16`。**成果物への影響：120秒を確定するには、測定単位・負荷条件・余裕の選択理由・検出遅延の費用を実測と並べて記録する必要がある。**

6. **real | should — 「2秒以上＝fixture実行回数」を再発判定へ昇格させてはいけない。** 後 regime 23走の原本では、最初のcase以外の最大は1.039秒で、今回の代理には支持がある。一方、test本体には実driver拒否確認やshell subprocessがあり、将来2秒を超える可能性を排除しない。速いfixtureは逆に数え落とす。根拠：`test_t1259_qsub_env_delivery_probe.py:267,895`、`f945-supersede-draft.md:15–16`。**成果物への影響：「1超ならmemo退行、1ならFS負荷」という二分判定は誤診を生むため、接尾・worker・traceback確認の補助指標へ戻す。**

7. **real | should — sampler は別ホストの能動測定であり、無擾乱の負荷計ではない。** `/proc` のload・process数はloginホスト限定で、`run_tests.py` の文字列一致数は計算ノードのxdist worker数ではない。試走のGit合計6.768／10.834秒は、予定20秒周期なら約34／54%を追加走査に使う規模。走査が周期を超えると休止せず次sampleへ進む。根拠：`scan_sampler.py:12–21,55–68,90–94`、`sampler-smoke.jsonl:1–2`。**成果物への影響：sampler値を計算ノード側の裾分布や混雑度へ外挿せず、測定による競合・cache warmingの影響を未評価と明記する。**

8. **real | should — 走査対象の維持と、実repoの清浄性を検査する能力は別である。** fixture は `tracked_status`・`untracked_paths` に加えて **`detached` も上書き**する。実値としてconsumerへ残るのは `head` と `source_sha256`。根拠：`test_t1259_qsub_env_delivery_probe.py:77–80`、`adjudication.md:101–103`。**成果物への影響：「argvと取得処理を維持」は成立するが、「実repoのdirty／untrackedをfixtureが検出する」は成立しない、とinsightに明記する。**

9. **refuted | should — helper＋新test fileが過剰だという指摘は採らない。** 13行のhelperは実repoを読む既存moduleから定数・呼出しを切り出し、新testをそのautouse fixtureやinventory更新へ巻き込まない役割がある。根拠：`author-u1.patch:1–150`、`adjudication.md:18–19`。**成果物への影響：ここを統合しても検証は簡単にならず、既存consumerへの変更範囲が広がる。**

## 親の実測値への反証・限界

**P1：非group化による重複走査が主因か**

- **支持する証拠：** `252e24b4f` は実際にgroupingを変える差分であり、後 regime では全23走が長時間case一つ・setup errorゼロ。module fixtureを同一workerへ寄せる機序と整合する。
- **反証・代替説明：** 「1 shardでerror一件」はfixture cacheと矛盾しない。失敗workerにそのmoduleのcaseが一つしか割り当てられなければ一件になる。原本 `15a504…/shard-0/junit.xml` は51case中、一件だけ38.076秒の `ls-files` timeout。一方、複数errorにはcache再掲も実在する。前 regime のoverlap=0にもmax57.688秒・14 errorがあり、overlap=3はmax33.192秒・errorゼロ。単純な「他session数が多いほど遅い」は成立しない。
- **書くべき限界：** overlapは走行窓がどこかで交差したsession数で、fixture実行時の同時数でも共有FS負荷でもない。抽出対象外session・他利用者負荷を含まず、時刻・ホスト・worktree差も未調整。今回の結果は重複走査削減の寄与を支持するが、主因の分離や42〜46本の同時実行を証明しない。

**P2：呼出しごとの上限と分布の解釈**

- **支持する証拠：** 既存productionと同じtimeout構造を保つ局所変更として整合する。成功30秒超102件という旧集計も、今回145件という集計も、複数呼出しの合計なら正常に説明できる。
- **反証・代替説明：** junit timeにはsetup/call/teardownが含まれ、厳密な「4 Git＋sha256だけ」ではない。error除外後のp99は「成功し、かつ2秒以上だったcase」の条件付き分位点であり、未完了走査を含むp99ではない。後 regime n=23のp99は上位二点の補間で、安定した裾の推定とはいえない。
- **書くべき限界：** 120秒ならGit待機予算の和は480秒相当になり得る。さらにhash・プロセス起動等の時間があり、厳密な全体上限ではない。lock待ち245秒や受入5分枠への収まりを保証しない。原本errorには `ls-files` だけでなく `status` timeoutもあった。

**P3：120秒を採用する最小の根拠**

- **支持する証拠：** 事前に規則を置き、超過時に自動増額しない方針は妥当。ただし「2倍の余裕」は設計判断であり、実測から一意に求まる値ではない。
- **反証・代替候補：**

| 呼出し上限 | 真のhangを検出する待ち時間の目安 | 4呼出しの待機予算の和 | 評価 |
|---|---:|---:|---|
| 60秒 | 60秒 | 240秒 | 最小候補。ただしmaxが60秒近傍なら余裕がない |
| 90秒 | 90秒 | 360秒 | 60秒に対し1.5倍の余裕 |
| 120秒 | 120秒 | 480秒 | 2倍の余裕。60秒より検出が最大約60秒遅れる |
| 180秒 | 180秒 | 720秒 | 今回の分布から追加費用を正当化する証拠がない |

- **書くべき最小記録：** 対象commit・session・host・時刻・原本リンク、grouping状態、測定単位、成功数／error数、max、負荷条件の観測範囲、sampler併走の有無を固定する。その上で「この条件で完了を確認し、未観測変動への余裕として120秒を選ぶ理由」と検出遅延を記す。混雑条件を捉えていなければ候補のままにする。呼出し別の計算ノード計測がない以上、そこまで測ったとは書けない。

## 削除・縮約の提案

- **削除：** 「主因を分離した」「同時走査の自傷は構造的に無い」「2秒以上の件数で原因を二分できる」。groupingは一つのshard内の重複を抑えるが、別sessionやsamplerとの競合まで排除しない。
- **縮約：** n=23のp99を採用根拠の中心から外し、件数・中央値・最大値・error件数を前面に出す。詳細分位表は補助資料に留める。
- **維持：** helper、新test file、受動集計器と能動samplerの分離。二つのscriptを統合する実益は小さい。ただしscript・入力一覧・実行条件は、将来再検算できる形で記録する。
- **不足：** fixture固有の所要と実行識別情報がなく、testcase代理に依存している。局所的な計測記録が望ましい。追加しない場合は「実行回数・呼出し別所要は未計測」とする。
- **不足：** 定数変更時の再測定条件と、固定値120をassertするtestの更新手順をinsightに短く残す。M1の定数assertによるkillだけでは実際のtimeout伝播を証明しないため、予定するfixtureの `TimeoutExpired` 実走結果も別に記録する。

## F945 追補の書き直し案

- F945 **supersede: 2026-09-20** — D2148項12に基づく受入fixture限定のtimeout再検討として、252e24b4fのmemo登録後に今回のsurvey対象23走で長時間testcase代理値が各走1件、最大24.494秒、setup error 0となったことを確認したが、grouping前後の時刻・ホスト・共有FS負荷との交絡は未分離であり、主因・ピーク同時走査数・将来の裾分布は確定していない；junit timeはsetup/call/teardownを含む代理値で、error件数にはfixture例外cacheの再掲が含まれるため独立した打ち切り走査数とは扱わない；T-2790の候補120秒はGit呼出しごとのfixture局所上限で、採用は対象を固定した受入実測と余裕・検出遅延の根拠をinsightへ記録して判断し、login samplerは別ホストの能動測定として扱い計算ノードの呼出し別所要を代替しない；production既定30秒・走査argv・拒否論理は維持するが、fixtureはdetached・tracked_status・untracked_pathsを模擬値へ上書きしており、再発時はGit argvとTimeoutExpired、接尾・worker配置を確認し、2秒以上のcase件数だけで原因を断定しない。

## 総括

**NO-GO：現草案の因果断定と120秒の確定採用。**
局所実装の構成を過剰として差し戻す根拠はない。
母集団・errorの単位・時間境界を修正し、負荷下実測と採用理由を記録することが条件。
受入全走・正式変異・sampler本走は未実施であり、本レビューはその完了を認定しない。
