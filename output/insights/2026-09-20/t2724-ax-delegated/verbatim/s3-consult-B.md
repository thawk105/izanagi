## 検査結果

以下、repo 内は指定 worktree 相対、`J/` は指定 job directory 相対。静的読解と Git の読取りのみ実施し、pytest・loader・full scan・書込みは実施していない。

**B-1 — real：帰結テストの列挙に2本漏れている。** `orchestrator/tests/test_s8b_binding_driftguards.py:249` の `test_run_block_broken_binding_manifest_refuses_and_writes_nothing` と同 `:300` の `test_gate_check_broken_binding_manifest_stacks_manifest_verify_refusal` も実 ROOT と ratified memo を使い、manifest refusal を要求する（`:270,286,313,327`）。合成 freeze は floor/budget を充填した v2（`test_s8b_oracle_driver.py:2799`）なので、A/X 後は両方とも full launch validation に進む。そこで失敗すれば manifest 検査へ到達せず、成功しても run-block は合成 freeze と active bytes の不一致で先に戻る。したがって既知の影響集合は driver 4本にこの2本を加える必要がある。`test_real_repo_serialization.py:2830` 自体がこの2本を memo consumer として列挙しており、plan の同ファイル内検索だけでは閉じない。manifest 検出力は独立した適切な tmp repo 経路で維持すべきで、拒否理由を置換するだけでは不足する。

**B-2 — real：現 g1 は、A/X が正しくても full launch validation の lineage 条件を満たせない。** `s8b_ratified_freeze.py:3493` は floor result と measurement closure の導入集合を `{generation_commit}` に限定する。一方、`output/s8b-freeze/holdout_freeze.v2.g1.json:1` の result は `…/20260916T111925Z-2c8cf9be/result.json`、G は `32ba8cae4`、その親は X1'=`cc82edc8c`。Git 読取りで result が X1' と G に同じ blob `43a2febf…` として存在し、G の追加は世代文書1件だけと確認した。導入の定義は「全 parent で absent」（同 module `:495`）なので、G は result の導入 commit になり得ない。前段が通れば必ず `binding-chain-mismatch`、cause=`generation-introduction` で落ちる。plan `J/codex/s2-plan.md:286` は要件を列挙しただけで、この現物との矛盾を検算していない。既存 G／床値／lineage 契約の変更は今回の trailer 改訂へ混ぜず、裁定パッケージへ返す必要がある。

**B-3 — 条件付き：実 repo の予測は「launch 成功」ではなく、遅くとも段階(6)で拒否である。** `_launch_validate:3134` の(1)は loader 取得後に HEAD が動かなければ通る。`activation_head` は pointer 導入 commit 固定ではなく解決時 HEAD（同 `:1409`）なので、帰結 commit 後は loader を取り直す。(2) generation=1 は現文書で成立。(3) protocol/result/cert/journal/manifest は G・現 HEAD の tree entry と worktree bytes の一致を確認し、measurement closure は空。(4) current contract は activation record `env_contract_activations/00000001.json:1` の `e576e9…` と protocol が一致するが、manifest、admission、床選択の全 semantic 条件を本段で通過確認したとは言えない。(5) binding 全辺も未実行。(6)は B-2 により不成立、cert 自体は X1' 導入で G の厳密祖先という条件と整合する。(7) exact exemption は active chain 再解決・bytes 照合（`:2986,3502`）、(8) occurrence/union/full scan は `:3515` 以降であり、現履歴では到達しない。従って `binding-chain-mismatch/generation-introduction` は**前段通過時の予測理由**であり、最初に観測する理由の保証ではない。P6 の対照にはこの優先順と未確認事項を記録する。

**B-4 — real：brief の v1 gate-check 予測は誤りで、run-block と分ける必要がある。** `J/brief.md:32` の v1=`freeze-not-active-generation` は `s8b_oracle_driver.py:627` に反する。v1 standalone gate-check は active loader に進まず、runbook の既知4拒否が対照になる。対して `run_block:1324,1340` は指定 path にかかわらず active loader→launch validation を先に行うため、現 g1 では v1 指定も g1 指定も launch failure が先行する。これを解消して初めて v1／合成 freeze は `freeze-not-active-generation`（`:1366`）、g1 は後段 gate へ進む。plan `:345` の訂正は採用すべきである。

**B-5 — real：P3 の部分成功を「受理」と呼ぶと、未達を完了扱いできてしまう。** `J/brief.md:8,32` の3 prefix ゼロは批准経路の部分条件であり、`J/verbatim/runbook-s1.1-s2.md:26,42` の全 gate 成立とは同義でない。W-4 未承認を理由に `allowed:true` を予定しないことは妥当だが、launch validation は spec 承認検査より前なので、その失敗を一律 W-4 に送れない。判定は「A/X schema・hash・topology・trailer・新規 record の exact exemption 不備＝本 wave で修正」「既存 G／床値／contract／lineage の不整合＝別裁定、P3 未達を明記」「launch 成功後の独立 spec 承認拒否＝W-4」とする。B-2 を抱えたまま3 prefix ゼロという現完了条件は満たせない。plan `:343` の部分成功への言い換えだけでは解消しない。

**B-6 — real：memo の値保存性は維持されるが、payer の検出対象と所要時間の計画が不足する。** `real_repo_ratified_memo.py:79,112` が畳むのは loader の戻り値／例外だけで、`run_block:1340` の launch validation は対象外。A/X 後も cache 自体の設計は成立するが、payer は「no-active 翻訳」から「実 loader 成功後の拒否経路」へ変わる。plan `:298,300` の tmp repo 集約負例補完は必要であり、payer の説明も変更する必要がある。現在は B-2 により full scan の追加時間は0だが、前段検証コストは増える。将来4本が各 full scan に到達するなら scan 部分だけで直列追加は **4×T_scan 秒**、漏れた2本も到達するなら **6×T_scan 秒**である。`real_repo_ratified_memo.py:5` の4.4秒は過去の loader 計測であり T_scan に代用できない。資料に現 scan 実測値はなく、秒数や5分以内を確約できない。通常受入では対象 node の growth hold も考慮し、明示解除した焦点走と通常受入を分けて計時する。新たな launch memo は検出力・HEAD／root／作業木鮮度の検証を要する別変更であり、今回黙って追加しない。

**B-7 — 条件付き：B-10 pin 更新は妥当だが、「D2166 と同じ授権根拠」は限定して書くべきである。** `test_backoff_extended_sweep.py:2014` と `b10_backoff_grid.sh:585` は subdir を含む全通常 file を path＋NUL＋bytes で hash し、A/X を除外しない。更新対象3 literal と job 前後検査は plan どおりである。しかし `J/verbatim/D2166.md:30` は「別 context・独立レビュー・変異・負例」を実際の手続として記録しており、同 wave 更新がそれと同一とは言えない。本 wave では A/X 導入の事前授権から必然となる期待変更として、赤を見る前に更新対象を固定し、独立レビューで差分が A/X 2件だけと再計算照合することが条件となる。旧 literal への2変異、追加／1 byte 改変に加え **A または X の欠落**も負例に入れる。旧 cohort 記録・算法・完全一致・前後検査を保ち、新 phase の登録／実行許可とは区別する。

**B-8 — refuted：FROZEN_MANIFEST・clean scan・receipt prefix 除外が A/X だけで新規赤になるという懸念は成立しない。** `test_frozen_artifacts.py:171,234` は固定23 key を検査し、実 directory の未知 file を列挙拒否しない。official clean scan は `s8b_floor_campaign.py:318` の chain record pattern で適合 A/X を許容し、bytes hash を digest に含める（`:5481,5515`）。既存 official 成果物による赤は残る。T-080 の通常 scan が使う `s8b_holdout_freeze.py:45` は freeze namespace を除外するので、A/X 自体は新規 holdout hit を増やさない。ただしこの結論を今回追加する docs／insight 全体へ一般化してはならない。また active v2 の exact exemption／full scan 成功は別条件であり、prefix 除外から推定できない。

**B-9 — refuted：hooks・B-10 job fixture・dispatch 契約の変更は不要である。** `test_hooks.py:229` は fixture root に対する Write/Edit の path 拒否を検査し、実 A/X の存在に依存しない。`test_b10_backoff_grid_job.py:423` は digest と期待値をともに `fixture-freeze` に置換するため実 tree pin 更新の帰結ではない。`check_docs.py:4033` の task→child script 対応、`:6417` 以降の段 dispatch 契約にも A/X record との直接依存はない。指定 docs の文章修正は必要だが、hook・CLI・dispatch 契約まで変える根拠はない。最終 docs checker は実際の差分に対して実行する。

**B-10 — real：commit 間の順序は明確だが、land 時に A/X の SHA を保つ手順が plan に欠ける。** plan `J/codex/s2-plan.md:5,151,197` は実装→A→X→帰結、X^=A、A の確定 bytes から X を作る依存を守る。一方、ff-only land までの間に main が進んだ場合の処理がない。`git worktree list --porcelain` には B-10 results／pin-update／chain-land／verifier-capacity などの checkout が存在したが、存在だけで競合中とは断定できない。A 作成直前と land 前に関連 path の差分と main ancestry を確認し、A/X 後の rebase／cherry-pick／squash を避ける手順を追加すべきである。main 更新が必要なら A/X を改作せず保持する統合形を選び、統合後 HEAD で loader・P3・pin を再検証する。ff-only 自体は既存 commit SHA を変えない。

**B-11 — 条件付き：record 作成方式は十分具体的だが、現時点では script の実装保証ではない。** plan `:167,171,190` は UTC 実時刻、canonical JSON、create-only を要求しており、逐語手順 `J/verbatim/insight-README-s5.md:19,25,29,50,57` は `datetime.now(timezone.utc)` と `open("xb")` を明示する。時刻源は実行ホストの時計で、裁定識別子 `13:2x` ではない。author script は未作成なので、review では approval／pointer 両方の `"xb"`、A commit blob と hash 計算対象 bytes の一致、各 commit の追加1件だけを現物で確認する。

**B-12 — real：brief の P2 件数は古い。一方、祖先・digest・未登録 node の扱いは反証されない。** `J/brief.md:18` と runbook の「2 passed」に対し、`test_frozen_artifacts.py:187,201,212,227,234,251` は5関数を実行する。held marker は検証省略部分を示すので、5 passed を全23件の実 bytes 検証済みと呼んではならない。G と X1' の HEAD ancestry は両方 rc=0、世代 SHA は指定値と一致した。`conftest.py:1624,1739` は ledger を fail-soft に読み未登録 duration を `None` とし、`tools/acceptance_shards.py:397` は未登録 node に1秒の配分重みを置く。この意味で brief の記述は支持できるが、未知の実行時間が安いことや5分以内の証拠にはならない。

## 総括

real finding は以下。

- **B-1:** driver 4本以外に binding driftguard 2本が漏れている。
- **B-2:** 現 result の導入履歴と launch lineage の `{G}` 条件が矛盾する。
- **B-4:** brief の v1 gate-check refusal 予測が誤っている。
- **B-5:** P3 の部分成功と全 gate 受理を区別し、既存不整合を W-4 扱いしない。
- **B-6:** memo 対象外の検証コストと payer の検出力維持が未計画。
- **B-10:** A/X の SHA を維持する land／並行変更対応が不足。
- **B-12:** P2 の期待件数「2 passed」が現物と不一致。

裁定パッケージ候補は、**G／床値入力の導入順と launch lineage 契約の整合**、必要なら **P3 未達時の wave 完了条件**、実測後に必要性が判明した **launch validation の重複削減**。W-4 spec 承認は引き続き別手番とする。

**plan／brief は現状のまま採用非推奨。** trailer 改訂と A/X 作成の骨格は支持するが、B-2 を解決せずに「P3 の3 prefix ゼロまで完了できる」とは計画できない。拒否の実測をそのまま新しい期待値へ固定して完了扱いせず、上記の漏れと境界を修正してから進めるべきである。