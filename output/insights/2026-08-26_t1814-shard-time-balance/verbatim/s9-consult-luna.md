## 頻度と費用の見積り

1走あたりに非帰属赤となる確率を \(p\) とする。走単位の最尤推定は単純に

\[
\hat p = 2/2 = 1
\]

である。ただし独立同分布を仮定した Clopper–Pearson 95%区間は約 \([0.158, 1]\)。観測が2点しかなく、同時期・同構成の共有環境なので、この区間さえ厳密には適用できない。

15 nodeを同率・独立と仮定し、30回のnode機会で2赤と数えると、node確率は \(\hat q=1/15\)、走単位では

\[
\hat p = 1-(1-\hat q)^{15}
       = 1-(14/15)^{15}
       \approx 0.645
\]

となる。ただし現物では15 nodeは均質でない。[test_dev_wave_cleanup.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1814-shard-time-balance/orchestrator/tests/test_dev_wave_cleanup.py:191)上、合成payloadを使わず実 `/proc` に到達する成功経路は landed 2、forward 2、reentry a/b 2の概ね6 nodeで、残りにはstubやoccupancy非実行状態が含まれる。この6 nodeだけを同率と仮定しても \(1-(5/6)^6\approx0.665\) であり、運用上は \(p=0.65～1.0\) を感度範囲にするのが妥当である。別nodeへ赤が移った事実は「観測済み2 nodeだけをholdすればよい」という見積りには不利である。

受入1走を \(C=(2\text{ request},\,T+Q)\)、\(T=275～307\) 秒、\(Q=\) queue待ちとする。DW-O18どおり再走を最大1回に限れば、

\[
E[\text{無駄になった初走/追加再走}] = pC
\]

\[
E[\text{受入走数/wave}] = 1+p,\qquad
P[\text{再走後も停止}] = p^2
\]

（最後の式は走間独立を仮定）。\(N\) wave全体の追加負担は、期待値で \(2Np\) request、\(NpT\) のpytest wall合計と \(NpQ\) のqueue待ちである。

20 waveを下限としても、\(p=0.645\) なら約25.8追加request・59.1～66.0分のwall合計、\(p=1\) なら40 request・91.7～102.3分に各queue待ちが加わる。並行受入自身がprocess churnを増やすなら、wave間は正相関し、この線形見積りより悪化しうる。

本waveを保持する直接費用はworktree/branch 1本、main更新の再取込み・再検証、未land結論の重複調査である。mainが数十分ごとに進む環境では無視できないが、同じ赤を20本以上が踏む反復費用の方が大きい。しかも本waveを止めても、他waveの赤は止まらない。

## 3 択の運用比較

| 案 | 今日landできるか | 次の再発を止めるか | 保守債務 | 戻す手順 |
|---|---|---|---|---|
| (a) file除外、94 node | 新しい直接裁定と編集後の受入greenがあれば最短。ただし現行DW-O18の通常経路ではない | このfile由来の受入赤は隠す。productionのrc22も他callerも直らない | 最大。安全な79 nodeも含む94 nodeを失い、旧entryの「消滅pid」という原因記述もF489の訂正後は古い | 下記の強化解除条件を満たすcombined commitで94 nodeを一括復帰 |
| (b) class hold、15 node | 現契約のままでは不可。registryはexact nodeごとの赤実測を要求し、13 nodeに証拠がない。2 nodeだけのholdでは次nodeへ移る公算がある | 15全てをholdできればこのclassの症状は止まるが、production原因は残る | 中～高。15行の証拠・task・解除状態を個別維持し、実scanしないnodeまで含む | 原因単位の修理証拠を作り、15行を同時に解除。nodeごとの解除にすると取り残しやすい |
| (c) production実装修理 | 原因payloadが欠けているため今日を約束できない。安全側のscannerを推測で変えるべきでない | 原因を正しく直せれば唯一production再発も止める | 選択債務はないが、安全クリティカルな `/proc` race処理の実装・回帰検査費用がある | 復帰操作なし。原因別regressionと高負荷受入を恒久保持 |
| 第4案：テスト隔離 | 小さいauthor変更と受入greenまで進めば今日の可能性が最も高い。未実走なので保証はしない | cleanup状態遷移テストの受入flakeを止める。productionのrc22は別途残る | 低。occupancyを依存注入し、hermeticな実checker統合テストを明示維持する | 除外がないため復帰不要。production修理は別P1として継続 |

(a)/(b)を選ぶ場合、前回の「taskがlandし、明示file走が全緑」は再利用してはいけない。8月24日除外、25日修理・復帰、26日再赤という往復が、その条件の不足を実証した。新しい解除条件は例えば次のようにする。

> F489の今回のissue source/errorを特定し、旧実装で赤・修理後にgreenとなる決定的process-churn回帰を追加する。修理と除外/hold解除を同じ候補commitに置き、そのexact commitを除外なしのcanonical K=2/48受入で3走連続green、かつ2つ以上の計算ノード割当で確認してから一体でlandする。

3走の解除検査は6 request、pytest wall合計13.8～15.4分＋queueである。20 waveへ継続課税するより一回限りの解除費用として安い。

## 推奨

第 4 案（cleanup状態遷移テストから実 `/proc` 依存を隔離する）

- 94 nodeをすべて受入に残せるため、受理集合を変更しない。
- 観測された2 nodeはoccupancy自体ではなくforward/reentry状態を検査しており、環境依存を注入する設計が自然である。
- 合成 `/proc` の成功、live occupantの拒否、payload不整合のfail-closeは専用nodeで維持し、配線を弱めない。
- 一つの小さい修理で全waveの反復費用を止め、本waveをlandした後に(c)を独立P1として進められる。

## この推奨の穴

- production cleanupのprocess-churn起因rc22は直らず、実運用ではworktree滞留が再発しうる。
- blanket stubにするとscannerとの統合断線を見逃す。合成 `/proc` を通す成功E2Eとlive occupant拒否を明示的に残す必要がある。
- 2赤のraw `issues` が保存されておらず、実際には別の共有状態が原因なら隔離後も赤が残る可能性がある。
- テスト隔離を「都合の悪い環境条件の隠蔽」として実装すると絶対規律2に触れる。各nodeの検査責務を先に分類する必要がある。

## 未確認事項

- 2赤それぞれのpayload内の `error`、`source`、PID状態、3 scanに入らず `attempts=1` だった理由。
- 2走が同一計算ノードだったか、同時受入数とprocess生成率がどの程度だったか。
- 15 nodeという論理classと、現物で実 `/proc` を通る約6 nodeとの差をcollector実行時にも確認できるか。
- queue待ちの実測値と、今後のwave総数。
- read-only制約に従いpytestは実行していない。greenは確認していない。

## 総括

観測上の点推定は \(p=1\) だが、2点だけなので真の確率は広く不明である。  
それでも現実的な感度値 \(p=0.65～1\) で、20 waveへ25.8～40追加requestの税になる。  
(a)は94 nodeを失い、(b)は13 nodeの証拠がなく、前回の解除条件も再利用できない。  
受理集合を保つ第4案で全waveを先に解放し、production修理(c)を別途継続するのが運用上最も安い。  
本結論は指定資料と現物の静的検査によるもので、テストgreenは主張しない。