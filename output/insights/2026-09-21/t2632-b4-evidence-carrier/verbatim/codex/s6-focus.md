静的検査とログ読解による判定です。テスト・probe・変異は実走していません。対象3ファイルは最終 commit `92f501c28` の内容と一致しました。

以下、`C`＝`orchestrator/campaign/p3_s4_loop.py`、`T`＝`orchestrator/tests/test_p3_s4_loop.py`。ログ参照は [f2](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/focus-f2.log:1)、[f5](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/focus-f5.log:1) です。

## 1. 所見ごとの対応表

| real 所見 | 判定 | 最終形の根拠 | 焦点走ログ |
|---|---|---|---|
| A2：canonical hash不能による過剰拒否 | **closed** | [C:3714](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/campaign/p3_s4_loop.py:3714)で `B4ProtocolError` を捕捉しnull。T:7577のNaN回帰は実mainを通り、評価呼出し・rc=0・hash=nullを検査 | f2:134、f5:26。B-5／B-4各modeのNaN実走まで示すログではない |
| A3：`.corrupt.*`停止条件の説明過大 | **closed** | [C:1558](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/campaign/p3_s4_loop.py:1558)で「原本不在の場合だけ」と限定。動作変更なし | f5:26。説明修正の直接根拠はコード |
| A4：bootstrap再実行拒否の説明過大 | **closed** | C:1619でWAL履歴のあるbootstrapに限定。C:2580のWAL不在時returnと整合 | f5:26。説明修正の直接根拠はコード |
| A7/B6：新設11件のfixture不備 | **closed** | [T:7240](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/tests/test_p3_s4_loop.py:7240)、7296のimport、7405の`exist_ok=True`、7506のadmitted history。duplicateは7256のanomalies、7260のtagsまで修正 | f2:119・137ではduplicateだけ失敗。f5:16–26は655件すべてpass |
| A7/B4：launcher positiveのattempt証拠不足 | **closed** | [test_p3_b4_closed_critic.py:2749](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/tests/test_p3_b4_closed_critic.py:2749)で同一IDのstart／commit／receipt operationを生成。2823以降の既存assertは維持 | f2:1に対象ファイル、119・164に唯一の失敗が別テストと記録。その後このファイルは不変 |

passの個別node一覧はログにありません。上表は対象指定・全体集計・失敗全件の記録を合わせた判断です。

## 2. fix の副作用

**受理集合・射影・本番attempt検査の意図しない変更は認めません。**

- fix-a1のproduction変更はhash例外処理とdocstring限定。fix-a2〜a4はduplicate fixture／assertの変更だけです。
- 既存launcherテストの差分は評価stub内のWAL出力・payload・receipt束縛だけです。期待rc・既存assertは不変。ただしverify実行まで含む本物のcertificationを、このstubが証明するわけではありません。
- productionのattempt検査は[C:1662](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/campaign/p3_s4_loop.py:1662)のcommit由来ID選択、1675のID必須、1679のstart一意性、1684のvariant＋attempt絞込みを維持しています。
- whiteboard／planner射影は不変。T:7309の読取り禁止検査とT:7503のreport不在・異なるhash間の出力bytes比較も維持されています。`proposal_document`はC:3152のagent envelopeへ展開されません。

A2とbootstrapのregistry束縛は矛盾しません。bootstrapはloader内の[C:2863](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/campaign/p3_s4_loop.py:2863)→C:617でcanonical hashを先に要求します。この例外はC:3718のcatchへ到達しません。null化はloader通過後のcarrier用計算に限定され、B-5の既存拒否sidecar／rc=3分岐も不変です。

［consumer 取り残し］の旧所見は閉鎖。［恒真ゲート］についても、異なるattempt・異なるreport・実際のWALレコードを比較しており、対象検査を常に成功させる修正はありません。

## 3. 親の訂正の検算

§4.1・§4.2の訂正はコードと整合します。

1. anomalies未指定なら`None`となり、[artifact_admission.py:846](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/campaign/artifact_admission.py:846)で
   `persisted COMMIT verify anomalies must be exact int zero`。
2. anomalies修正後も、[commit_receipt_support.py:193](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/tests/commit_receipt_support.py:193)の既定値は`tags=("legacy",)`。WALの2件とreceiptの1件が一致せず、artifact_admission.py:887で
   `persisted COMMIT receipt evidence does not match WAL verifies`。
3. 最終fixtureと[probe:20](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/probe_duplicate_fixed.py:20)では、先行attemptがstart＋abortの2件、採用attemptがstart＋verify×2＋commitの4件。receiptも同順の`legacy`／`s2`です。C:2058でduplicateを返し、C:1663・1684から採用IDと4 refsになる計算です。

probeはID一致とrefs数を**表示**しますが、終了コードの条件はduplicateだけです（probe:57–59）。したがってprobeのrc=0だけでは全主張を証明しません。最終T:7275・7281・7289・7291のassertとf5の成功が補強しています。

なお、§4の「後続abortならduplicateにならない」という説明は採用できません。C:2058はadmitted commitをabort分岐より先に扱います。

**新所見 F2：real／nit［誤前提］** — [make_mutation_spec.py:52](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/make_mutation_spec.py:52)のコメントに、撤回済みの説明が残っています。
放置時の成果物影響：変異の実装は正しくても、S4再照準の根拠を誤って再利用する恐れがあります。

## 4. 焦点走の量化

ログの進捗記号も再集計しました。

| 走行 | 対象 | 進捗記号からの集計 | summaryとの一致 |
|---|---:|---:|---|
| f2 | 33個の相異なるファイル | `F`＝1、`.`＝4701、`s`＝15 | f2:134と一致 |
| f5 | T単独 | `.`＝655、失敗・skip＝0 | f5:26と一致 |

f2のskipは120–133行の件数を合算して15件です。

| 理由 | 件数 |
|---|---:|
| 既存growth hold | 7 |
| template patch未適用 | 3 |
| 実機root／build環境未設定 | 3 |
| Python 3.11要件 | 2 |

統合差分にはこれらのskip条件を変える変更がなく、「全件既存理由」という分類は支持できます。skip対象の検査成功を意味するものではありません。

fix-a2〜a4に加え、`eee7e4ba3..92f501c28`の差分もTだけ（28追加・12削除）でした。production・他32ファイル・共有fixtureに変更はなく、**他32ファイルのf2結果を回帰証拠として持ち越す判断は妥当**です。合成すると4702 passed／15 skipped相当ですが、最終commitで33ファイルを一括実走した結果ではありません。両ログの「受入全走ではない」という限定も維持します。

## 5. 変異設計

S4の「最初のstartへ置換」は最終fixtureで**非等価**です。T:7275が先行ID≠採用IDを要求し、T:7281が採用IDと採用4レコードを期待するため、先行ID・2 refsを返す変異を検出できます。

ただし、§5の割り振り全体はそのまま承認できません。

**新所見 F1：real／must-fix［変異帰属］［テスト代表性］［誤前提］** — **E1でdriftが出ないnodeでも、S13／S8が入口停止を解除するとdriftへ到達します。**
放置時の成果物影響：live binding拒否を意図した機能検査のKILLとして登録し、評価前停止の検出力を過大評価します。

根拠となる経路は次のとおりです。

- [T:7393](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/tests/test_p3_s4_loop.py:7393)の破損テストは、通常／E1ではC:2971で停止します。
- S13はその呼出しを削除します。S8も初回の破損読取りを`return {}`へ変え、後続へ進ませます。
- 少なくとも非B-4ケースでは、評価stubより前に[C:3028](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/campaign/p3_s4_loop.py:3028)→`ident.ensure_campaign_identity`→[ident.py:392](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/campaign/ident.py:392)のlive binding照合へ到達します。
- fixtureのbindingはHEAD由来ですが、注入後のproduction bytesはHEADと不一致です。そこでdriftが発生し、T:7418の期待例外文言／後続の未呼出しassertによる本来の検出とは別の失敗になります。

したがって、drift一覧との非交差とE1 SURVIVEDだけでは十分ではありません。**S13はcommit群へ移す必要があります。S8も同じ破損driveテストを選ぶならcommit群へ移すか、直接loaderを検査するT:7526だけで独立に検出してください。**

その他の静的な検出設計は以下のとおりです。

| 変異 | 狙う検出理由 |
|---|---|
| S3・S4 | duplicate fixtureのattempt混入／選択違い |
| S5・S6 | record全体hashの違い／同stageのverify欠落 |
| S7 | 他iterationの消失 |
| S8 | 直接loaderテストなら初回拒否の消失 |
| S9 | regular file fsyncの失敗注入が届かなくなる |
| S1・S2 | 公開欠落／checkpointとの順序逆転 |
| S10・S11 | raw bytesとcanonical値の違い／capture欠落 |
| S12・S14・S15 | B-5記録欠落／入力へのreport混入／NaN過剰拒否 |
| C1〜C5 | trial取得・codec・v1受理・例外変換・欠落キー処理 |
| E1 | 等価対照。SURVIVED期待 |

これらは設計の評価であり、KILLの実測認定ではありません。失敗node集合の一致に加え、失敗箇所・理由が狙った検査に帰属することが必要です。

## 総括

**NO-GO。**

段6の採用real所見5件はすべて **closed**。productionの追加修正は認めませんが、**S13とS8の変異実行方法に帰属上のmust-fixが残ります**。その割り振りを修正し、親の走行で意図した失敗理由を確認してから変異検証を閉じてください。
