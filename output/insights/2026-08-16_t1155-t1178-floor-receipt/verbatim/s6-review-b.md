静的レビューのみ実施した。pytest・build・Web 検索・書込みは行っていない。

到達範囲は、producer/resume/finalize/render、pure/live verifier、ratified closure、holdout freeze、oracle report、oracle driver、materialization/`PreparedCell` を照合した。ratified→report の伝播と campaign の通常・resume・`M-finalize-pending` は live admission に到達している。一方、holdout freeze に重大な取り残しがある。

[severity: must-fix]  
[取り残し] `s8b_holdout_freeze` は sibling journal の completed `session` 行を捨て、`result.sessions` を completed lifecycle として採用する。result 内の throughput/session/floor を一貫して改竄しても、対応する `session-start` があれば live inspector と pure verifierを通せる。  
[根拠 file:line] [s8b_holdout_freeze.py:1432](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_holdout_freeze.py:1432) で journal を読むが、[同:1440](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_holdout_freeze.py:1440) は `session-start` だけを残し、[同:1445](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_holdout_freeze.py:1445) で result 自己申告 session を足す。pure verifier 自身も [s8b_floor_stats.py:602](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_floor_stats.py:602) で raw session 真正性を保証しないと明記する。  
[提案] scope 内で、strict 検証した journal `event=session` 射影と `result.sessions` の exact equality を要求する。ratified の [s8b_ratified_freeze.py:3145](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_ratified_freeze.py:3145) と同じ辺を張り、result だけの throughput 改竄変異を追加する。  
[成果物影響] 塞がないと journal に存在しない session 値から [s8b_holdout_freeze.py:1473](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_holdout_freeze.py:1473) の `pairs`・`scale_ref`・`scalar_alt` を作り、後続 certified freeze の床値を変更できる。

[severity: must-fix]  
[取り残し] holdout freeze の sibling `manifest.json` は bytes hashだけが検査され、manifest v3 の strict parse、exact key、schema、cells/binaries/schedule整合を一切検査しない。  
[根拠 file:line] [s8b_holdout_freeze.py:1417](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_holdout_freeze.py:1417) は raw bytesを取得し、[同:1424](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_holdout_freeze.py:1424) は SHA一致だけを見る。対して ratified は [s8b_ratified_freeze.py:3004](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_ratified_freeze.py:3004) で strict loadし、[同:3039](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_ratified_freeze.py:3039) で manifest semantics を検査する。  
[提案] scope 内で shared manifest validator を `s8b_floor_contract.py` 側へ置き、holdout/ratified/resume が同じ v3 exact契約を使う。`{}` や v2 manifest と整合する ledger/result 一式を拒否するテストを追加する。  
[成果物影響] 塞がないと schema v3 でない manifest bytesを closureの正当な manifestとして受理し、無検査のmanifest hashを持つ refreeze candidate が成立する。

[severity: must-fix]  
[取り残し] fix2 の `session-start` 認可は `attempt_id` と `seq`/`retry_ordinal` の正準対応を検査しない。同一cellの別seqまたは別retry slotの `attempt_id`を start に載せ、markerを1件作るだけで、その別ticketのledger行を正当化できる。resume validatorにも同じ穴がある。  
[根拠 file:line] producerの正準式は [s8b_floor_campaign.py:4092](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_floor_campaign.py:4092) と [同:4393](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_floor_campaign.py:4393)。inspector は [s8b_holdout_admission.py:1804](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_holdout_admission.py:1804) で集合所属しか見ず、[同:1837](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_holdout_admission.py:1837) でも `attempt_id == cell::seq{seq}` を検査しない。resume側も [s8b_floor_campaign.py:5871](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_floor_campaign.py:5871) 以降でこの対応を欠く。  
[提案] scope 内で planned/retry双方の正準 `attempt_id` を再導出して exact一致させる。consume時、inspector時、resume時の3層へ共通validatorを接続し、別seq・別retry ordinal移植を独立nodeidにする。  
[成果物影響] 塞がないと実際に認可されたslotとは異なる attempt row が受理集合へ入り、`attempt_row_count` と `ledger_projection_sha256` が偽の消費を含む。

[severity: should-fix]  
[取り残し] fix3でdigestから落とした `measurement_head` は、形状とledger/claim間の一致しか検査されない。ledgerとclaimを同時に別の40hexへ変更すると、portable digestもlive acceptanceも変わらない。  
[根拠 file:line] 除外は [s8b_holdout_admission.py:1458](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_holdout_admission.py:1458)。検査時の期待値は [同:1725](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_holdout_admission.py:1725) でledger自身から取得し、claimへコピーしている。追加負例も [test_s8b_holdout_admission.py:858](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/tests/test_s8b_holdout_admission.py:858) のledger片側変更だけである。  
[提案] root移植性とHEAD authorityを両立させる外部期待値が定義できるならscopeへ入れる。できないなら「非権威的な同値確認用field」と再分類する裁定パッケージへ送り、同期変更positive controlを追加する。  
[成果物影響] 現状では台帳が主張する測定commitを変更してもresult receiptと受理集合が変わらず、台帳provenanceが実態より強く読める。

[severity: should-fix]  
[取り残し] 公開live verifierはschema文字列だけを確認し、result v4のtop-level exact-key集合を検査しない。ratified/holdoutとの受理集合が不一致である。  
[根拠 file:line] [s8b_floor_stats.py:633](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_floor_stats.py:633) はschemaだけを確認し、その後もartifact全体の余分key検査がない。ratifiedは [s8b_ratified_freeze.py:2194](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_ratified_freeze.py:2194)、holdoutは [s8b_holdout_freeze.py:1331](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_holdout_freeze.py:1331) でexact-keyを要求する。  
[提案] scope 内でmode条件付きのresult key契約を共有化し、live verifier単体へ `unexpected` key拒否テストを足す。  
[成果物影響] standalone公開入口だけは未検査fieldを持つresultを成功扱いし、同じv4成果物の受理集合がconsumerごとに変わる。

[severity: nit]  
[取り残し] 並行waveとの衝突面は、末尾追加だけでなく共有fixtureと既存E2Eの中央部まで広い。  
[根拠 file:line] `_fake_prepare` [test_s8b_floor_campaign.py:292](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/tests/test_s8b_floor_campaign.py:292)、`_run_campaign` [同:482](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/tests/test_s8b_floor_campaign.py:482)、two-phase E2E [同:5107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/tests/test_s8b_floor_campaign.py:5107)、新規群 [同:8401](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/tests/test_s8b_floor_campaign.py:8401)。  
[提案] land前に `dev-wave-t1142-oracle-n-pilot` の同ファイルを関数単位で照合し、fixture signatureと末尾test名の双方を手動統合する。  
[成果物影響] 直接の値変更はないが、競合解消でlive-admission fixtureやreceipt到達testを落とすと、上記受理集合回帰が未検出になる。

確認できた非所見として、8縮退分岐は [test_s8b_holdout_admission.py:701](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/tests/test_s8b_holdout_admission.py:701) から別nodeidで存在し、missing/zero-byteは [s8b_holdout_admission.py:1503](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_holdout_admission.py:1503) と [同:1518](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_holdout_admission.py:1518) で分離されている。SWO実行非証明と台帳再構成非耐性のdocstringも実在する。テスト削除行のassertは2件とも条件付きkey対応・新schema goldenへの置換で、skip/xfail化やassert消失は見つからなかった。

## 総括

scopeから漏れている最重要層は `s8b_holdout_freeze` である。live admission自体は呼ぶが、journal completed sessionとresult sessionの同一性を閉じておらず、refreezeする床値をresult自己申告から変更できる。

fix 3巡で緩んだ箇所はある。fix1のruntime/portable分離は静的には維持されているが、fix2はstartとattempt IDの正準束縛を欠き、fix3は`measurement_head`の意味的authorityをportable receiptから外したままである。