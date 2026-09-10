必須入力はすべて読めた。結論は、現プランのままでは **land 不可**。最大の問題は、read-only 用とされた C1〜C3 が実際には新規 oracle 実走の admission にも使われており、歴史契約の受理が producer 側へ漏れることにある。

## 所見 B-1 — C1〜C3 は read-only 専用ではなく、live oracle admission でもある（blocker）

**根拠 (path:line)**

独立に列挙した契約述語層は次のとおり。

| 層 | 親との対応 | 実際の性質 |
|---|---|---|
| floor protocol semantic 検証 | C1 | read-only と live admission の共用 |
| journal receipt / calibration | C2 | read-only と live admission の共用 |
| recorded run_cmd 再導出 | C3 | read-only と live admission の共用 |
| oracle report の manifest receipt | C4 | read-only |
| committed silo-ladder evidence | 親の見落とし | scope 裁定が必要、B-2 |

`LaunchValidatedFreeze` は明示的に oracle driver の実走型である（[s8b_ratified_freeze.py:764](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_ratified_freeze.py:764)）。実際に driver は active freeze を読み、public `launch_validate` を呼ぶ（[s8b_oracle_driver.py:1047](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_oracle_driver.py:1047)）。C1〜C3 はその内部にある（[s8b_ratified_freeze.py:2870](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_ratified_freeze.py:2870)、[s8b_ratified_freeze.py:1795](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_ratified_freeze.py:1795)、[s8b_ratified_freeze.py:2272](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_ratified_freeze.py:2272)）。

変更後の `LaunchValidatedFreeze` に resolved contract/generation を保持する計画はない。一方、実走直前の `_prepare_v2_execution` は oracle manifest の `run_contract` を current lookup に照合するだけで、validated floor の recorded contract と同世代かを照合しない（[s8b_oracle_driver.py:737](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_oracle_driver.py:737)、[s8b_oracle_driver.py:753](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_oracle_driver.py:753)）。oracle manifest 側も freeze と run contract を個別に検証するだけである（[s8b_oracle_manifest.py:693](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_oracle_manifest.py:693)、[s8b_oracle_manifest.py:868](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_oracle_manifest.py:868)）。

なお、親が除外した [s8b_ratified_freeze.py:960](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/s8b_ratified_freeze.py:960) は返却 contract を捨てる env_tag 実在検査だけであり、この除外判断は正しい。

**成立条件**

current=g2、active/floor artifact=g1、oracle manifest の run contract=g2、env_tag は同一とする。計画どおり `launch_validate` を historical 化すると g1 floor は通り、その後 g2 manifest も current admission を通る。両契約を結ぶ検査がないため、g1 floor/binary と g2 execution receipt の混成を拒否できない。

**成果物 (certified 選択・レポート・台帳) への影響 1 行**

g1 の floor 証拠と g2 の実走 receipt を混成した oracle 結果が certified レポート／台帳候補になり得る。

**推奨**

read-only 再検証入口と live `launch_validate` を分離し、oracle driver が使う入口は current 契約一致を維持すること。別案として resolved `GenerationEntry` を `LaunchValidatedFreeze` に保持し、live path では oracle manifest の世代との完全一致を必須にする。current=g2・floor=g1・manifest=g2 が marker/WAL/budget 書込み前に拒否される public `run_block` 回帰試験が必要。

## 所見 B-2 — 親の C1〜C4 は repo 全体の read-only 層を被覆していない

**根拠 (path:line)**

committed `silo_ladder_rung1` artifact は g1 の `contract_sha256` を保持している（[silo_ladder_rung1.json:11](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json:11)、[同:567](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json:567)）。

その `verify-result` は `validate_current_bindings` を呼び、artifact の calibration path/hash/contract hash を current `env_contract.lookup("pegasus")` と比較する（[silo_ladder_rung1.py:3511](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/silo_ladder_rung1.py:3511)、[同:3534](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/silo_ladder_rung1.py:3534)、[同:4832](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/silo_ladder_rung1.py:4832)）。既存 test も runtime source binding は歴史値のまま保持しつつ、calibration だけ current lookup に合わせている（[test_silo_ladder_rung1_evidence.py:1239](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/tests/test_silo_ladder_rung1_evidence.py:1239)、[同:1252](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/tests/test_silo_ladder_rung1_evidence.py:1252)）。

新規 floor producer、oracle driver の run contract、pipeline/loop/trigger gating は current admission なので scope 外でよい。しかし silo verifier は「歴史 proof の再検証」か「現行実装への再束縛」かが未裁定で、C1〜C4だけでは scope が閉じていない。

**成立条件**

silo artifact が g1 を記録したまま current が g2になると、内容が不変でも current contract 不一致だけで `verify-result` が落ちる。

**成果物 (certified 選択・レポート・台帳) への影響 1 行**

g1 の committed silo evidence が current 更新だけで再検証不能となり、certified evidence 選択から脱落する。

**推奨**

T574へ無断追加せず、裁定パッケージとして「silo verify-result は historical proof verifier か current-compatibility verifier か」を決めること。前者なら recorded hash resolver を配線し、後者なら D196 の「全 certified 成果物を再検証可能」という表現から明示的に除外する。

## 所見 B-3 — P2/C3 は production 上観測不能な「versioned dispatch」である

**根拠 (path:line)**

正当な successor が変更できるのは calibration path と SHA の組だけである（[env_contract.py:202](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/env_contract.py:202)）。clock や attestation mode の変更は明示的に拒否される（[test_env_contract.py:383](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/tests/test_env_contract.py:383)、[同:483](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/tests/test_env_contract.py:483)）。

それにもかかわらず、プランの C3 正例は clock/numactl の異なる不正 successor 相当の contract を private predicate へ直接渡す（[s2/out.md:139](/work/1/SFC/tanab/dev-wave-jobs/t574-historical-resolver/s2/out.md:139)、[同:145](/work/1/SFC/tanab/dev-wave-jobs/t574-historical-resolver/s2/out.md:145)）。これは引数 plumbing は検査するが、正当な世代解決を検査しない。

また helper は `GenerationEntry` を解決した後 contract だけを返す計画であり（[s2/out.md:55](/work/1/SFC/tanab/dev-wave-jobs/t574-historical-resolver/s2/out.md:55)）、generation に対応する predicate 実装版は保持しない。D176 が将来仕事とした「versioned predicate dispatch」（[decisions.md:8691](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/docs/decisions.md:8691)）に対し、これは calibration データ選択以上のものではない。D196 が拒否した観測不能機構とも同型である（[decisions.md:9510](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/docs/decisions.md:9510)）。

**成立条件**

すべての production-reachable g1→g2 が現行 successor 規則に従う限り、C3 の clock/numactl と attestation mode は g1/g2で同値となり、current lookup を残した mutant と resolved-contract 実装を観測的に区別できない。

**成果物 (certified 選択・レポート・台帳) への影響 1 行**

台帳上は「世代別 run_cmd predicate 検証済み」と見えても、実際には current-bound 実装を排除できない。

**推奨**

保証を「recorded hash の解決＋歴史 calibration 選択」へ狭め、C3 の引数 test は将来配線の非認証テストと明記すること。真に versioned predicate dispatch と呼ぶなら、正当な世代で観測差を作れる遷移規則と generation-aware dispatcher を別裁定する。テストのためだけに fuse/successor を緩めてはならない。

## 所見 B-4 — P5 の正例は構成可能だが、production 経路の証明が不足する

**根拠 (path:line)**

C1 の正例は、production fuse の拒否も確認したうえで test index/current view を差し替え、public `launch_validate` と本物の production resolver を通す（[s2/out.md:114](/work/1/SFC/tanab/dev-wave-jobs/t574-historical-resolver/s2/out.md:114)）。したがって、この seam 自体は production bootstrap fuse を外す test 専用抜け道ではない。

一方 C4 の正例は private `_receipt_expectations` を直接呼ぶだけである（[s2/out.md:127](/work/1/SFC/tanab/dev-wave-jobs/t574-historical-resolver/s2/out.md:127)）。production caller は別に存在するため（[s2/out.md:197](/work/1/SFC/tanab/dev-wave-jobs/t574-historical-resolver/s2/out.md:197)）、caller が current resolver を渡す mutant をこの正例は殺せない。

producer negative も `s8b_floor_campaign.validate_protocol` leaf だけであり（[s2/out.md:123](/work/1/SFC/tanab/dev-wave-jobs/t574-historical-resolver/s2/out.md:123)）、新規 run が副作用前に拒否されることまでは実測しない。P3 の unknown/cross-env/dishonest-resolver の fail-closed matrix 自体は妥当だが、public report 経路でも必要である。

**成立条件**

private leaf は正しくても、production caller の resolver wiring または admission 順序が誤っている場合、計画した試験は緑のままになる。

**成果物 (certified 選択・レポート・台帳) への影響 1 行**

テスト緑でも production の oracle report が current lookup のまま、または producer が副作用後に拒否する可能性が残る。

**推奨**

C4 は `build_observations` 以上の public report 経路で current=g2・manifest=g1 を通すこと。producer は `run_campaign`/CLI 相当を副作用 sentinel 付きで呼び、g1拒否が出力・budget・journal生成前であることを検査する。B-1の live oracle negative も同じ matrix に加える。

## 所見 B-5 — P4 は linux-baremetal の resume availability を実際に失わせる

**根拠 (path:line)**

linux-baremetal は `allow_resume=True`、Pegasus だけが `False` である（[env_contract.py:237](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/env_contract.py:237)、[同:256](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/orchestrator/campaign/env_contract.py:256)）。

resume 経路は先に protocol を current 契約へ照合し、その後で `allow_resume` を見る（`orchestrator/campaign/s8b_floor_campaign.py:2750-2789`）。さらに run command 投影も current lookup を再実行する（同 `:1865-1880`）。したがって入口だけ historical 化しても安全な resume にはならない。

**成立条件**

linux-baremetal の g1 campaign が中断され、その後 current がg2へ進むと、契約上 `allow_resume=True` でも g1 protocol の hash 不一致で再開不能になる。

**成果物 (certified 選択・レポート・台帳) への影響 1 行**

generation 更新を跨いだ linux campaign が未完のまま stranded となり、予定していた certified ledger を生成できない。

**推奨**

worklog 注記だけで済ませず裁定すること。選択肢は、(A) current-only resume を正式仕様として availability loss を受容し回帰試験で固定、または (B) recorded contract を resume 全実行辺まで伝播する別 scope。後者は admission leaf 一箇所の変更では不十分。

## 所見 B-6 — DW-O09 の「旧 source hash pin は0件」は、その書き方では偽

**根拠 (path:line)**

tracked silo artifact は `orchestrator/campaign/env_contract.py` の旧 SHA `88d557…` を保持する（[silo_ladder_rung1.json:67](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json:67)）。現行ファイルの実測 SHA は `8d5298…` で一致しない。

さらに t419 artifact は path を key にせず、role 名 `env_contract_sha256` で同じ旧 SHA を保持する（[manifest.json:105](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/output/env/pegasus/t419-probe-causality/0_889400.nqsv/manifest.json:105)、[同:265](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver/output/env/pegasus/t419-probe-causality/0_889400.nqsv/manifest.json:265)）。したがって path-key grep だけでは pin を見落とす。

ただし、今回編集予定の `s8b_ratified_freeze.py`、`s8b_oracle_report.py`、`s8b_floor_contract.py` の旧 hash pin は独立検索でも見つからず、プランは `env_contract.py` を変更しない。この狭い意味では既存 proof chain を新たに壊す証拠はない。

**成立条件**

親の「0件」を repo-wide、または brief が明示した `env_contract.py` まで含む主張として読む場合に反例が成立する。

**成果物 (certified 選択・レポート・台帳) への影響 1 行**

今回の差分だけなら直ちに無効化しないが、現 DW-O09 証跡では既存成果物への影響なしを認証できない。

**推奨**

主張を「今回編集する3 module の pin は0件、変更しない env_contract の歴史 pin は存在する」に訂正すること。再検査は path 文字列だけでなく `*_sha256` role map、runtime binding 配列、generator version map を schema-aware に走査し、`env_contract.py` 無変更を差分で固定する。

## 所見 B-7 — 親 probe の実測範囲より brief の一般化が広い

**根拠 (path:line)**

probe が import するのは env contract、floor campaign/contract、oracle report だけで、ratified freeze 自体を読んでいない（[probe_g2_consumers.py:15](/work/1/SFC/tanab/dev-wave-jobs/t574-historical-resolver/probe_g2_consumers.py:15)）。

測っている C1 相当は producer と共有する `fc.validate_protocol` leaf（[同:37](/work/1/SFC/tanab/dev-wave-jobs/t574-historical-resolver/probe_g2_consumers.py:37)）、C4 は private `_receipt_expectations`（[同:58](/work/1/SFC/tanab/dev-wave-jobs/t574-historical-resolver/probe_g2_consumers.py:58)）である。C2、C3、public `launch_validate`、selector、`build_observations` は実測していない。brief 自身も C1〜C3 のE2E未実走を認めながら（[s1-brief.md:42](/work/1/SFC/tanab/dev-wave-jobs/t574-historical-resolver/s1-brief.md:42)）、floor/freeze/selector/reportすべてが落ちると一般化している（[同:84](/work/1/SFC/tanab/dev-wave-jobs/t574-historical-resolver/s1-brief.md:84)）。

**成立条件**

この probe を C1〜C4および selector/live admission 全体の実測証拠として扱う場合に、未測定部分が保証へ混入する。

**成果物 (certified 選択・レポート・台帳) への影響 1 行**

probe の赤／緑だけでは certified freeze・selector・oracle report の production 配線を証明できない。

**推奨**

結果を「leaf 実測」「public component integration」「静的推論」に分けて記録すること。active pointer 不在なので E2E 緑は主張せず、実装後は public `launch_validate`、`build_observations`、live oracle refusal の component integration で補う。

## 総括

最も重い3件は次のとおり。

1. **B-1:** historical 化した C1〜C3 が live oracle admission に漏れ、g1 floor/g2 run の混成を許す。
2. **B-3:** C3の「versioned predicate dispatch」は正当な successor 上では current-bound mutant と観測的に区別できない。
3. **B-2:** committed silo evidence という第5の再検証層が scope 判定から漏れている。

P1〜P5の判定は、P1は入口分離まで不採用、P2は保証範囲の縮小または再裁定、P3は public-path 試験付きで採用、P4は availability 方針の裁定待ち、P5は C1について成立するが C4・producer・live oracle が不足、となる。D197については activation identifier を生成・直列化しないため、現プランの非適用判断でよい。

したがって、**現プランは land してはならない**。最低でも B-1 の admission 分離、production-path positive/negative control、P2の保証文言修正、silo/resume の裁定パッケージ化、DW-O09の訂正が必要である。なお本レビューは静的読取りのみで、pytestその他の実行試験は行っていない。