## 指摘

静的レビューのみ。実装・pytest・計測は行っていない。以下、`brief` / `plan` / `facts` は指定された job dir の資料、コード名は `orchestrator/verifier/` 配下を指す。数値外挿は実測結果ではない。

1. **【観点1・must-fix】最小案を比較する前に、(i)〜(v)を積み上げる計画になっている。**  
   根拠: `plan:60,70,80,102,112,126,165`、`facts:9–16`。各案の「64 B/write削減」「峰値40%削減」等は改善の条件であって、完走に必要な条件ではない。6 sから単純外挿すると次の規模になる。

   | workload | 10 s相当の主 process maxrss | wall | 示唆 |
   |---|---:|---:|---|
   | write-heavy | 約31 GiB | 約411 s | 通常の増加だけなら容量・時間とも余裕。異常停止の解消を先に試す |
   | balanced | 約46 GiB | 約595 s | worker側の増幅を抑えるだけで足りる可能性 |
   | read-heavy | 約143 GiB | 約1441 s | 親側の構造削減が必要になる可能性が高い |

   **修正案:** 「局所解放＋worker削減」を最初の候補とし、目標を満たした時点で止める。構造変更は、それを省いた構成では対象traceの容量・時間を満たせない場合だけ追加する。

2. **【観点1・must-fix】既定worker削減を候補から排除する根拠がない。ただし既存pinの例外裁定が必要。**  
   根拠: `plan:54`、`parse.py:493–511`、`decisions-excerpt.md:56–82`、`test_verifier.py:2234–2241`。D1553の8並列は16並列に対し、峰値約20%減、wall約10%増だった。大規模への保証ではないが、今回の記憶量問題に最も小さい比較案である。worker削減はparse同時生存量・CoWには効きうるが、親の全候補・全隣接の量はなくならない。  
   **修正案:** 既存の明示`workers=8`、不足時4で対象10 sを比較する。成功した場合だけ既定変更を採り、`==16`の設定pinを更新する例外を段4で決める。明示48上限と判定pinは維持する。

3. **【観点1・should】(ii)と(i)の必要性を独立に切り分けるべき。**  
   根拠: `plan:76–80`、`dsg.py:146–164,325`。`gc.freeze()`単独はrefcount由来のCoWを止めない。一方、「配列だけ読む」は現行のproducer/versions lookupを書き換える構造変更であり、freezeを足すだけの局所修正ではない。(i)はwrite-heavy 10 sで約78M writeと外挿される大きなindexを縮め、結果としてCoWも軽減しうるため、**(i)だけで完走する可能性もある**。ただしparse・転送・pool待機が原因なら解決しない。  
   **修正案:** 停止phaseに応じ、低worker構成、freeze単独、(i)単独を順に比較し、(ii)のflat化は残存CoWが容量超過を説明する場合だけ採る。

4. **【観点2・must-fix】read-heavy 10 sの保全済み入力がない。完了条件をそのまま実行できない。**  
   根拠: `brief:8,45`、`plan:224–230`。指定保全先の [read-heavy 10 s result.json:252](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-verify-phase-adopted-backoff/run/calib/fixed-5-read-heavy/extime-10/result.json:252) は`not_run`、理由は`verifier wall > 600 s`、`preservation.files=[]`。当該directoryにはこのJSONのみがある。  
   また [paper-story:3185](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-verifier-capacity/docs/paper-story/2026-09-20.md:3185) のB-8本文は対象・種・長さの不足を述べるが、全3 workloadの10 s完走をこの容量waveの必須条件とは定めていない。  
   **修正案:** 本waveの完了を「balanced / write-heavyの保全済み10 s未完走2件の解消＋read-heavy 6 sの回帰確認」に変更する。read-heavy 10 sは入力取得から別途裁定へ返す。これはB-8取得とは数えない。

5. **【観点2・should】(iii)の範囲分割、(iv)、(v)は現時点では必要性が立証されていない。**  
   根拠: `plan:83–126`、`dsg.py:370–382,429–479`。CSRはread-heavy約1B edgeを対象にするなら有力だが、未完走2件の解消だけなら必須とはいえない。さらに一sourceずつsetを解放する設計では、sourceを重み付き「範囲」に束ねる層自体は省メモリ化に不可欠ではない。(iv)はSCC峰値が実際の制約になった場合だけ必要。(v)の「緑1件で発火しSCCが20%短縮」は“あれば嬉しい”条件であり、停止がSCC以前なら欠陥を直さない。  
   **修正案:** 初期実装から(iii)〜(v)を外し、残る容量超過のphaseに対応するものだけ追加する。CSRが必要になっても、まずsource単位処理に留める。

6. **【観点3・should】構造変更の前に、以下の削除・局所修正を比較できる。**  
   根拠と概算効果は次表。解放bytesとRSS低下はallocatorのため一致しない。

   | file:line | 局所修正案 | 概算効果・限界 |
   |---|---|---|
   | `dsg.py:275–285` | 検証呼出し内でkey文字列を共有する | 16文字keyなら約`65×(W−K)` Bからcache費を引いた量。write-heavy 10 s外挿で約4〜5 GiB。decode自体は残りうる。`(key,commit)` tupleの単純削除は不可 |
   | `dsg.py:286–288` | edge構築前に`per_key`を解放 | list参照約8〜9 B/write＋鍵ごとの容器。write-heavy 10 sで約0.6 GiB以上。末尾の`key_versions`参照にも注意 |
   | `dsg.py:296–310` | task生成後にweightsを解放 | read側だけで約8N B。balanced 10 sで約0.11 GiB。`_weighted_ranges:76`のprefixを固定幅化する案は約28N B削減候補 |
   | `parse.py:701–726` | `seen`を削り、重複判定を`txid in winners`へ | set表を丸ごと削除。概算数十B/txn。last-winsと重複検出順は保てる |
   | `parse.py:553–585` | scan後に`local_txns`を解放 | `occurrences`がTxnを保持するのでdict表だけ減る。Txn本体は減らない |
   | `dsg.py:379–382` | dictの挿入順を保ち、setを一つずつtupleへ置換 | 全set＋全tupleの重なりを避ける。約8E Bの追加参照列が上限目安。全set構築時の峰値は下がらない |
   | `dsg.py:439` | `list(self.adj.keys())`を直接反復へ | 約8S B削減。SCC中にadjを変更していない |
   | `parse.py:795–809`、`dsg.py:333–359` | pool停止後、未採用結果への全参照を切ってからfallback | 未採用列・候補payloadの重複生存を除去。`received`だけでなくfuture・loop変数も対象 |

   **修正案:** 上表を最小候補としてprofileに対応付ける。なお、隣接setは現行でも関数復帰時に解放されており、恒久的な漏れではない。`_ParsedFileColumns`は`dsg.py:507–545`のwitness再構成に必要なので、edge構築直後の全削除は不可。Tarjanの`index/low`にも安全な単純削除はない。

7. **【観点4・must-fix】Private_Dirtyの残差だけではCoW原因を同定できない。**  
   根拠: `brief:37,43`、`plan:49–54`、`parse.py:547–606,695–754`、`dsg.py:120–176,345,442–478`。出力配列を差し引いても、worker内のsource辞書・小配列・pickle buffer・allocator残留がある。parse workerのTxn峰値、親のwinner merge、鍵ごとの`sorted(set())`、反復Tarjanの明示DFS stackも代替仮説として残る。`shutdown(wait=True)`待機とfallback実行時間も別である。  
   **修正案:** 既存probeへ、parse scan/列化/送信/merge、producer/sort、edge生成/送受信/replay/tuple化、SCCの境界時刻を追加し、同時刻のPID別Pss・Private_Dirty・CPU、候補容量、pool停止/fallback開始を対応付ける。原因判断はworker数・freeze等の対照比較で補強する。現在の射影には、この排除を済ませた観測結果はない。

8. **【観点2・4・should】見積りprobeが広い一方、実測欠陥のwrite-heavyを必須入力から外している。**  
   根拠: `plan:155–165`。全案についてbalanced/read-heavy 6 sを旧→候補→旧で測る構成は、不要案の試作まで要求する。一方、write-heavy 10 s timeoutへの効果を別形状のtraceだけで判断できない。  
   **修正案:** 初回profileが指したphaseと未完走2入力を中心に、採用候補だけprobeする。見積りは残し、全案一律の試作・閾値・反復を削る。

9. **【観点2・should】追加testと互換viewは採用差分に限定できる。**  
   根拠: `plan:68,90,184–220`、`test_verifier.py:2576,2679,2704,2734,2821`。既存testは順序・重複・疎txid・fallbackを既に検査する。不採用のCSR、配列Tarjan、前判定、freezeのための追加testは不要。逆に構造変更を採る場合、既存のproducer lookupやadj比較を支える狭いviewは「無条件に削れる互換層」ではない。  
   **修正案:** 全report比較と既存testを基礎に、採用変更で新しく生じる境界だけ追加する。viewも既存消費者が要求する操作だけに限定する。

10. **【観点5・should】P4は容量waveとして妥当。ただし600 s達成もB-8前進も別に表示すべき。**  
    根拠: `brief:38`、`facts:16`、`paper-story:3190`。read-heavy 6 sを808〜864 sから600 sへ入れるには、全体で約26〜31%短縮が必要。メモリ削減に伴って達成する可能性はあるが、phase別wallなしに見込めない。局所wallを1.5〜2倍まで許すplanは、600 s改善を保証しない。  
    **修正案:** 600 sは副次観測に留め、専用高速化を追加しない。3600 s内完走と校正適格性を別欄で報告する。

11. **【観点5・should】全5案をauthor一本へ入れる規模判断は支持できない。**  
    根拠: `brief:52`、`plan:169–195`。400 model calls / 5400 sで、packed版・共有入力・CSR・Tarjan・前判定・複数fallbackをすべて実装し検査できる根拠はない。3 s全workloadの旧版検証だけでもfactsの合計は約698 sあり、大規模計測を同じauthor枠へ含める余裕は小さい。  
    **修正案:** まず局所修正の一本へ縮める。実測後も必要ならindex/共有入力、さらに隣接構造を直列の別実装単位に分ける。`core.py`は現計画どおり原則無変更でよい。

12. **【観点6・should】容量改善の結果から先の研究・運用裁定を自動成立させない。**  
    根拠: `brief:14–15,22`、`plan:235,252`、`paper-story:3188–3196`。600 s規則、最終候補、seed、旧lock再開、witness pin変更は容量改善とは別の判断である。  
    **修正案:** 以下の裁定項目に測定結果を添えて返し、本waveの実装済み項目に含めない。

## brief の誤り

- **`brief:8,45`の「保全済み10 s × 3 workload」は誤り。** 指定先のread-heavy 10 sは未実行・未保全。現scopeはbench/buildも禁止しているため、入力を新規取得することも既定作業にはできない。
- **`brief:37`の400 B/write・150 B/edgeは構造単体の単価ではない。** 主process全体の経験比率であり、producer/隣接だけの削減可能量として使えない。commit tupleとtxidはtxn内で共有される。
- **同じく「主process CPU 520 s」という帰属は不正確。** `facts:18`はworker CPUも合算されるとしている。低CPUから親fallbackを直接推論できない。
- **`brief:39`の「txidはdense」は正常traceの前提に限る。** 疎txidをboundedな`indeterminate`にする既存契約がある。
- **`brief:15`の「永久に得られない」は過大。** 低worker実行を排除した実測がない。またB-8は長さだけでなく対象と種も未充足である。
- **`brief:8`の比較対象12 verdictは一覧不足。** factsの完走7行との対応を親が特定する必要があり、推測で補ってはいけない。

## 段 4 で親が決めるべき裁定項目

| 項目 | 択 | 推奨 |
|---|---|---|
| 本waveの完了範囲 | 未完走10 s × 2件／read-heavyを含む3件 | **2件＋read-heavy 6 s回帰**。3件なら未保全入力の取得を別途認可 |
| 最小実装 | 全5案を候補順に積む／局所修正から必要分だけ追加 | **局所修正から追加** |
| 既定worker | 16固定／大規模実測に基づき削減 | **8、必要時4を比較して裁定**。自動調整機構は作らない |
| exact pin | 全期待値を不変／設定pinだけ限定更新／witness変更も許す | **worker設定pinのみ必要時更新**。report・witness pinは維持 |
| 校正≤600 s | 維持／予算変更 | **本waveでは維持し、結果を裁定へ返す**。容量完走を適格化と扱わない |
| B-8の対象・seed | fixed-5再検証を取得扱い／最終候補とseed記録を別途決定 | **後者**。本waveは容量上の障害解消まで |
| campaign lock drift | 旧lockを書換え／旧成果物保存＋新closureで再走 | **後者**。再走対象・時期は人間へ返す |
| 比較対象12件 | 件数から推測／既存artifact一覧を固定 | **一覧を固定**し、同一性確認の対象を明確化 |

## 総括

最初に試すべきは、既定worker削減と不要な同時保持の解消である。  
(i)〜(v)のどれも、現資料だけでは未完走2件への必須変更と断定できない。  
read-heavy 10 sは未保全であり、3 workload必須という完了条件を修正する必要がある。  
容量完走・600 s適格性・B-8取得を分け、後二者は裁定へ返す。