# 受入lease (D239) の排他区間短縮 — 設計は成立せず、D270が既に同型の失敗様式を実測記録していた (2026-08-21)

- wave: `dev-wave-t1461-lease-window` (branch `worktree-dev-wave-t1461-lease-window`)
- base main: `4a2543f0` (worktree作成時点の local main)
- 依頼: 受入lease (D239) の排他区間を縮める設計の分析・検討。**実装なし (設計検討のみ、production
  コード変更ゼロ)**。
- 結論: **現時点の設計案 (claim前にmerge・受入テストを済ませ、claim後は前提再確認+ff+foldだけに
  する) は実装しない。** 段2 codex plan・段3 敵対相談2レンズ (正しさ境界レンズ/整合性・実効性・
  scopeレンズ) が独立に計15件のreal所見を検出し、うち1件は2026-08-10のD270が**既に同型の失敗
  様式を実測記録済み**であることが判明した。設計提案として記録し、より狭い実測を伴う次の一手を
  推奨する。

## 背景 (依頼の実測根拠の検証結果)

依頼は「受入投入〜land完了7時間のうち実テスト実行は8分44秒、残り98%超が並行wave間のlease順番待ち」
という数値を `output/insights/2026-08-20_t870-congestion-nproc/README.md` の実測として引用していた。
**この具体的な数値 (7時間・8分44秒・98%) は同README中に文字列として存在しないことを確認した**
(grep実測、`7時間`/`8分44秒`/`98%`のいずれもヒットなし)。同READMEが実際に記録しているのは、
本wave自身の段9受入投入時に (1) 1回目試行で全史provenance再監査が480秒枠でTimeoutExpired、
(2) 2回目試行はmerge・監査を通過したがdispatch自体が900秒既定のqueue-wait-timeoutで失敗、
(3) `ps`で15以上の別waveが同じ受入lease・compute dispatch queueを同時に奪い合っていたこと、である。

別の実測 (`output/insights/2026-08-20_t870-acceptance-lease-timing/README.md`、2026-08-20、
13並行peer session下、3件の実landed waveの事後解析) は次を記録している。

| wave | lease claim試行開始→PBS submit (lease contention) | queue待ち | pytest実行 | land所要 |
|---|---|---|---|---|
| T-1442 | 74分 | 38秒 | 223秒 | 74秒 |
| T-1445 | 49分 | 806秒 | 283秒 | (未回収) |
| T-1441 | 33分 | 101秒 | 207秒 | (未回収) |

**qualitative な結論 (「lease順番待ちが実テスト実行時間を大きく上回る」) は複数の独立実測で頑健に
支持される** (T-1442は74分待ち対223秒実行 ≈ 待ちが実行の20倍)。しかし **「7時間」「8分44秒」
「98%超」という具体的な数値そのものは、今回発見できたどの一次資料からも再現できなかった**。
より深刻な混雑 (15+並行、900秒queue-wait-timeout失敗を経て複数回retry) では実際に数時間規模へ
達しうることは`t870-congestion-nproc`が示す2回の失敗試行から否定できないが、その具体的な
時間内訳は一次資料に無い。**この数値の出典を再確認できるまで、今後この headline 数値を根拠として
使わないこと。** 問題の存在自体 (lease待ちが支配項) は否定しない。

## 現状の機構 (段2 codex planによるfile:line確認済み)

- **D239** (`docs/decisions.md:11172`): 排他lease (`tools/wave_land_window.py`) の原設計。目的は
  無駄な受入投資の防止 (thundering-herd対策) であって正しさ機構ではない。fencing tokenなし・
  release権限はwave slug digestのみを既知の限界として受容。
- **D270** (`docs/decisions.md:12433`、2026-08-10、**本waveの核心と直接衝突する既存決定**):
  「受入leaseを`acquired`にした待ち手は、その直後に自分でlocal mainを取り直し、merge・再検査して
  から受入全走を投入する」と明記し、**「main取り込みを親の事前作業にする」設計を明示的に検討し
  却下した過去がある**。却下理由を原文のまま引用する: 「取り込みを親の事前作業にすると、待機時間が
  取り込みの鮮度を超える区画で原理と機構が両立しない。並行waveが飽和した区画では`acquired`の
  時点で必ず追い越されており、取るたびにleaseを捨てることになる (**24分待って15commit遅れ、
  別waveで4回空振り**)」。本wave提案の「claim前にmerge・受入テストを済ませる」は、D270が
  「親の事前作業」と呼び却下した設計の直接の一般化である。
- **D254/D432** (`docs/decisions.md:11672`, `17940`): landの内部lock (D128、`dev_wave_land.py`)
  は「取得後に束縛を再検証する」パターンを持つ (D432、2026-08-16改訂)。180秒のwait capは
  **safety保証ではなくavailability capであり、公平性(FIFO)を一切保証しない**と明記
  (実測lock保持時間: median 6秒・p99 18秒・max 145秒)。D432自身が**「待機化はprovenance監査の
  同時流入を増幅しうる。保持者が監査のためlockを解放している間に待ち手が順に取得して各自監査を
  始め、最初の1本がlandすると残りはfingerprint不一致で拒否される。上限は13×480計算秒で、
  発生率は未計測」という残余リスクをユーザー裁定へ送ったまま未解決**にしている。本wave提案は
  この既に未解決と分かっているリスクの対象を「480秒の監査」から「merge+受入テスト全体
  (実測200〜300秒超のpytest本体 + queue待ち最大806秒)」へ拡大するものであり、同型リスクを
  縮小ではなく拡大する可能性が高い。
- 受入receipt (schema `dev-wave-acceptance-receipt/v5`) は**27 field** (26ではない、brief記載の
  誤り)。`tested_main`/`tested_tip`のexact binding、`lease_holder`のdigest検査は
  `tools/dev_wave_land.py:716-786`。

## 段2/段3の所見 (real、要旨。file:line詳細は `verbatim/` 参照)

正しさ境界レンズ (sol) と整合性・実効性・scopeレンズ (luna) が独立に検出し、本wave (親) が
D270/D432の原文突合で追認した所見:

1. receipt publish後・D128再確認前のTOCTOU (main進行を検出できない窓が残る)。
2. D254の既存監査条件 (`active_plan is None`) をそのまま流用すると、新設の厳密checkが
   fold-recovery経路で抜ける。
3. `held-self`はinvocationを識別できない — 別invocationの誤ったreceipt publishを防ぐ
   fail-closed状態機械が現行コードに存在しない。
4. race検出後のlease解放が`expected_main_sha`不一致で失敗しうる (leaseが解放されずに残留する
   可能性)。
5. `MERGE_HEAD` cleanupがlease ownership状態に結合しており、claim前merge失敗時に残留する
   (3者が独立に到達した最重要所見の一つ)。
6. race検出時、既に作成したmerge commitを再利用するか破棄するかが未定義。
7. **D270が「claim→main再取得→merge→再検査→受入」の順序を明示的に決定済みであり、本wave提案は
   これを反転させる。D270の却下理由 (飽和下での事前作業の恒常的な陳腐化) が直接的な反証材料。**
8. **`lock-busy`は現行契約 (`retryable_same_request=True`によりD469の自動release条件から除外)
   でleaseをRETAINEDのまま残す。「race検出後はfresh contextへ戻りcross-wave資源を保持しない」
   という本wave不変条件の前提と正面から矛盾する。**
9. D253のFIFO fairnessが変質する (「受入を始めたい順」から「テストを終えてclaimに到達した順」へ)
   — 重い/遅いdiffのwaveが軽いwaveに恒常的に追い越されうる新しい不公平。
10. TTL・`--max-wait-seconds`のリテラル値は変わらないが、運用上の意味論 (何を覆う時間か) が
    暗黙に変わり、D253/D469が明記する「意味論不変」と抵触する。
11. D402 (`docs/decisions.md:16887`) が要求する「決定の入力文脈 (並行数・sibling worktree数・
    main/MERGE_HEAD/indexの観測時点) を変える変更は同値性の実測なしに採用しない」というgateを
    本設計は満たしていない。
12. 提案する厳密`locked_main == tested_main`検査は、現行のD254/D432 audited-closure許可
    (`current ∈ audited-set`かつ祖先関係なら許可) より**狭い**— 現在は正しく受理されている
    already-landed経路を誤って拒否しうる。
13. `IZANAGI_WAVE_LEASE_DIR`未設定時にrenew/releaseが静かにno-opする既知の運用穴
    (`output/insights/2026-08-20_t870-acceptance-lease-timing/README.md`に実例記録あり) に
    本設計は対処していない。leaseが残留すれば混雑を悪化させる。
14. brief記載の複数不正確 (26→27 field、renew()「import限定」→現に`dev_wave_land.py`が使用、
    「親が明示release」→D469後は条件付き自動release、release権限「digestのみ」→
    `expected_main_sha`も使用)。
15. 効果の実効性が未証明 — 混雑がleaseからD128 flockへ単純に付け替わるだけの可能性を、
    D432自身の実測値 (14 wave同時到達で素朴計算でも14×18秒=252秒がcapの180秒を超えうる) が
    示唆する。

refuted (却下、記録しておくべき正の結果):
- schema自体 (27 field) の変更は不要 (verifierはlive lease/main状態を見ない、caller値の
  exact一致のみ検査するため)。
- D619 (TTL/queue-timeout/walltime既定値) の数値変更は本設計に必須ではない。
- 明示的なreward-hack (部分再検証・古いreceipt再利用の導入) は所見として見つからなかった —
  brief/planとも「race時は全量やり直す」を一貫して要求している。
- D239/D253/D299/D402/D432/D469/D595/D619は全て実在しplanの引用と一致 (親がD270/D432を
  直接原文照合、他は2レンズが独立に照合)。

## 結論・裁定

段4裁定: **実装しない (`4→7→8→9`)。** 理由:

1. D270が2026-08-10時点で**既に同型の設計 (main取り込みをclaim前の事前作業にする) を検討し、
   飽和下での恒常的な陳腐化を実測付きで却下している**。今回の提案はこの却下の射程を再訪する
   だけの新しい証拠 (飽和時のwasted-retest頻度の実測) を持たない。
2. D432が「監査lock解放の待機化はprovenance監査の同時流入を増幅しうる」という**既に未解決と
   分かっている残余リスク**を、本提案は「監査」から「merge+受入テスト全体」へ拡大する形で
   踏襲しており、悪化の懸念がある。
3. 2レンズが独立に検出したcorrectnessギャップ (TOCTOU、held-self、MERGE_HEAD cleanup結合、
   lock-busy時のlease残留) は、規律2 (正しさゲートを緩めない) に照らし「まず直してから」
   ではなく「解ける保証がまだ無い」段階の欠陷である。
4. 依頼の動機付けとなった数値 (7時間/8分44秒/98%超) が一次資料から再現できず、
   問題自体は実在するが規模の再測定が要る。

## 次の一手 (今wave scope外、次wave候補)

- **推奨・狭い実測を先に行う**: 「claim前にテストを済ませていたら、実際にどれくらいの頻度で
  main advanceによって無駄になっていたか」を、既存のland/acceptance receiptとworklog着地時刻
  から事後解析で定量化する (新規production変更ゼロ、`t870-acceptance-lease-timing`と同じ手法)。
  D270が示した「24分待って15commit遅れ」のような陳腐化率が今日の並行度 (15+) でどの程度かを
  実測しない限り、lock方式の変更が純便益かどうか判定できない。
- 上記実測が「陳腐化率は十分低く、shrinkする価値がある」と示した場合に初めて、次の設計waveで
  本wave所見15件 (特に8: lock-busy時のlease残留、5: MERGE_HEAD cleanup結合、3: held-self識別)
  を解消する具体的な実装案を起草する。D270の supersede はコード変更を伴わない設計判断であっても
  ユーザー裁定を要する (D270自身がユーザー裁定を経た決定であるため)。
- T-1462 (本wave着手中にユーザーから届いた別依頼、非帰属赤の既知登録・運用徹底) とは軸が異なる。
  混同しない。

## 一次資料

- `verbatim/s1-brief.md` — 段1 brief。
- `verbatim/s2-plan.md` — 段2 codex plan (`--stage plan`, read-only, reasoning=max)。
- `verbatim/s3-lensA-sol.md` — 段3 レンズsol (`--stage consult --lane sol`)。正しさ境界。
- `verbatim/s3-lensB-luna.md` — 段3 レンズluna (`--stage consult --lane luna`)。整合性・実効性・scope。
- `docs/decisions.md:12433` (D270)、`:17940` (D432) — 親が原文を直接照合。
