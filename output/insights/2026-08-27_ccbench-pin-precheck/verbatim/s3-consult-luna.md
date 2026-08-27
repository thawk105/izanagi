## 所見一覧

1. **対象:** [docs/failures.md:876](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-pin-precheck-20260827/docs/failures.md:876)、[s1_known_axes_freeze.py:642](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-pin-precheck-20260827/orchestrator/campaign/s1_known_axes_freeze.py:642)、[findings.md:3](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-ccbench-pin-precheck-20260827/findings.md:3)  
   **内容:** 親の merge probe と仮 gitlink commit は、実際の Git commit/tree を作っているので F29 違反ではない。`K.ROOT` 差し替えも、`_stock_common()` が実ファイルから行番号・本文・SHA を読む範囲に限れば妥当。ただし findings は基準を `b7f66232` と記す一方、resolver probe の親 commit は `0d3d80e1` だった。関連 production file に両 commit 間の差は無く結論は変わらないが、測定条件の記載は不正確。  
   **深刻度:** minor  
   **根拠:** [実体確認] F29 は「測定対象が命題と違っていた」ことを禁止し、特に「自己 hash・自己参照を持つ対象では monkeypatch による模擬を根拠にしない」とする。今回の merge と gitlink は実オブジェクトで、`_stock_common()` も `ROOT / OPTIONS_REL` 等を直接読む。一方、trial commit `567871ae` の親は `0d3d80e1`。  
   **推測・評価:** 完全に疑義を消す測り方は、`b7f66232` 固定の使い捨て clone に実 gitlink commit を作り、target commit を submodule として展開し、その clone 自身の module から `build_document()` を呼ぶ方法。これなら `K.ROOT` 差し替えも不要。

2. **対象:** [brief.md:10](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-ccbench-pin-precheck-20260827/brief.md:10)、D16  
   **内容:** 「pin が master の祖先でない」ことは「上げる／上げない／条件付きで上げる」の三択を無効にしない。無効なのは「master tip へ直接付け替える」という一実装だけ。親は選択肢と実装方式を混同し、full merge を事実上の唯一案にしている。  
   **深刻度:** major  
   **根拠:** [実体確認] D16 は trace-hook の行き先を `izanagi-trace` branch と明記し、master 直行を要求していない。full merge の実差分は16 commit・21 file・`+211/-158`、うち SS2PL の実機能に必要なのは主に `b629dc1`、`df47e3a`、必要なら `ff291e4` の3 commit。  
   **推測・評価:** 正しい択一は「今は据え置く／必要 commit だけ取り込む／一般 upstream 同期として full merge する」。full merge は選択肢の一つであって既定解ではない。

3. **対象:** [findings.md:205](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-ccbench-pin-precheck-20260827/findings.md:205)、[mocc_trace_v1_policy.json:16](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-pin-precheck-20260827/tools/pegasus/mocc_trace_v1_policy.json:16)、[test_mocc_trace_pair.py:16](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-pin-precheck-20260827/orchestrator/tests/test_mocc_trace_pair.py:16)  
   **内容:** 親の「bump で更新が要る live な束縛 7 件」は3件過大。MOCC policy と2 test の `511c9538 → 058d0c4e` は現行 gitlink ではなく、既に測った source pair の歴史的 identity であり、pin bump 時に更新してはいけない。実際の live literal は4件＋golden 1行＋追加 floor record。  
   **深刻度:** major  
   **根拠:** [実体確認] policy は `base_oid` と `new_oid` の対を固定し、test fixture は binary SHA・workload・old/new OID を一体で固定している。pilot receipt も [mocc_trace_pilot.sh:1371](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-pin-precheck-20260827/tools/pegasus/mocc_trace_pilot.sh:1371) で両 OID を記録し、`outer_gitlink_advanced: false` とする。  
   **推測・評価:** この3 literal を新 pin に追随させると、pin 移行ではなく過去実験の意味の書換えになる。

4. **対象:** [findings.md:234](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-ccbench-pin-precheck-20260827/findings.md:234)、[mocc-g2 brief:69](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-mocc-g2-repro-20260826/output/insights/2026-08-26_mocc-g2-repro/brief.md:69)  
   **内容:** `dev-wave-t1506-mocc-trace0` は「稼働中」ではない。tip `2caec363` は main の祖先で、残存 worktree と未追跡実測物があるだけ。親が見落とした実際の未着地作業は `dev-wave-mocc-g2-repro-20260826` で、MOCC pilot・pair checker・両 test を編集中。  
   **深刻度:** major  
   **根拠:** [実体確認] `git merge-base --is-ancestor 2caec363 main` は rc=0。対して mocc-g2 tip `abf2bde0` は main の祖先でなく、同 branch は上記4 file を変更している。`docs/handoff/` は README だけで、現行 worklog 末尾は B-4 作業であり T-1506 稼働の記録はない。  
   **推測・評価:** pin bump 自体で `058d0c4e` を rebase する必要はない。ただし同じ test/pilot を誤って編集すると未着地 mocc-g2 と競合するため、mocc-g2 の land 後に行うのが安全。

5. **対象:** [pin.py:20](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-pin-precheck-20260827/orchestrator/campaign/pin.py:20)、D16  
   **内容:** human push は実務上の hard sequencing gate。新 CCBench commit の remote 到達確認前に superproject gitlink を land してはならない。ただし過去実績上、恒久的 blocker ではなく人間手番1回の待ちである。  
   **深刻度:** major  
   **根拠:** [実体確認] pin.py は「human push まで un-clonable」と明記。Git 履歴の CCBench commit→superproject pin commit の間隔は、およそ2分、28分、1時間45分、17時間26分だった。4回とも最終的に remote branch へ到達している。  
   **推測・評価:** これは push 時刻そのものではなく commit 間隔だが、同日～翌日規模の運用 gate と評価できる。条件は「human push → fresh clone/cat-file で到達確認 → gitlink と承認定数を atomic に更新」とすべき。

6. **対象:** [brief.md:56](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-ccbench-pin-precheck-20260827/brief.md:56)、[SS2PL report:7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-pin-precheck-20260827/output/insights/2026-08-25_ss2pl-lock-protocol-study/report.md:7)、[docs/phase3.md:266](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-pin-precheck-20260827/docs/phase3.md:266)  
   **内容:** 「据え置くと SS2PL materials campaign が着手できない」は実体に反する。現 pin `511c9538`＋out-of-tree patch で、SS2PL YCSB study は既に350点の本走と210点の独立再現を完走している。  
   **深刻度:** major  
   **根拠:** [実体確認] report は「CCBench commit `511c9538` + 本 study の out-of-tree patch」と明記し、350点・別ノード210点を記録する。一方で「official proof chain の外」「certified 選択・floor/oracle の根拠には使えない」とも明記する。phase3 は別 protocol trace-hook を「現状 non-blocking」、cross-protocol を「8b＋層3後」としている。  
   **推測・評価:** 正しい費用は「descriptive study は既に可能、official/certified SS2PL は別途探索・verifier 配線が必要」。後者は現在の phase 経路ではない。

7. **対象:** [freeze_verification_hold.py:14](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-pin-precheck-20260827/orchestrator/campaign/freeze_verification_hold.py:14)  
   **内容:** (P3) の「pin 照合9件の追加コストはゼロ」は、保留継続中の即時実行費に限れば正しいが、ライフサイクル費用としては誤り。  
   **深刻度:** minor  
   **根拠:** [実体確認] `HELD=True` で21 check が `status: held` になり、解除は `explicit-user-command-only`。成功扱いではなく検査延期である。  
   **推測・評価:** pin をさらに進めると解除時の再凍結・差分説明が1世代増える。「即時費用ゼロ、延期負債は増加」が正しい。

8. **対象:** D444、D471、D491、[s8b_floor_campaign.py:1237](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-pin-precheck-20260827/orchestrator/campaign/s8b_floor_campaign.py:1237)  
   **内容:** (P2) の「床値 protocol の再発行に再計測不要」は、floor protocol の移送契約に限れば支持できる。ただし新 CCBench source の機能・性能検証まで不要という意味には広げられない。  
   **深刻度:** minor  
   **根拠:** [実体確認] D444 は更新可能 field を `contract_sha256` と `ccbench_pin` の2つに限定し、残る16 field を byte-exact 継承すると決定。resolver は新 pin の record が無ければ `E=0` で停止する。  
   **推測・評価:** pin、`CCBENCH_FULL_SHA`、追加 protocol record は同一移行単位にする必要がある。

## 親が挙げていない選択肢

### 1. 現 pin＋既存 out-of-tree SS2PL patch を維持する

- **内容:** canonical pin は `511c9538` のまま、既存の `patches/ss2pl-lock-protocol-study.patch` と専用 runner を使う。
- **費用:** pin literal、golden、floor record、push は変更不要。既存 patch は2,733行あり、今後の保守面は大きいが投入済みの費用。
- **失うもの:** canonical `tpcc_ss2pl` の SIGSEGV は残る。study は certified ではなく、正式材料にするには verifier・探索配線と再測定が必要。
- **親の推奨案との比較:** 当面の descriptive SS2PL には最安。一般 upstream 同期は達成しない。

### 2. 必要 commit だけ cherry-pick する

- **内容:** YCSB入口 `b629dc1` と lock失敗報告 `df47e3a` を取り込む。DLR0 timeout が必要な場合だけ `ff291e4` を追加する。
- **費用:** CCBench 側2～3 commit＋human push。superproject 側は4 live literalと追加 floor record。2 commit案なら `Options.cmake` が動かず、親案の golden 1行更新も不要。
- **失うもの:** CI dependency 更新等の残り master commit、masterとの完全同期、将来 merge の単純さ。
- **親の推奨案との比較:** SS2PL が目的なら差分・裁定面とも小さい。一般同期が目的なら将来の取り込み負債が残る。

### 3. SS2PL 専用 source branch / source selector を設ける

- **内容:** global gitlink と別に `izanagi-ss2pl` commit を campaign source identity として指定する。
- **費用:** branch push、source selector、campaign-id/provenance、clean checkout 契約の追加。certified 化するなら trace/verifier 配線も必要。
- **失うもの:** 「現行 CCBench pin は1つ」という運用単純性。既存 driver の自動追随も使えない。
- **親の推奨案との比較:** 隔離は強いが、現状は既存 patch clone が同じ目的をより安く達成している。

### 4. mocc-g2 着地後まで据え置き、その時点で full merge を再裁定する

- **内容:** active mocc-g2 の source-pair 証拠を着地させてから、一般 upstream 同期が本当に必要なら親案を実施する。歴史的 `511→058` pair は更新しない。
- **費用:** 短期の延期。実施時は human push、4 live literal、golden 1行、追加 floor record。
- **失うもの:** master のSS2PL修正を canonical pinで直ちには使えない。
- **親の推奨案との比較:** full merge の便益は保持しつつ、誤ったMOCC書換えと進行中branch競合を避けられる。

### 5. trace branch を master 上へ rebase する

- **内容:** 8本の izanagi 側 commit を master 上へ載せ直す。
- **費用:** history rewrite、human force-push、全OID更新、MOCC後続commitの再構成。
- **失うもの:** 既存OIDの安定性と過去のsource binding。
- **親の推奨案との比較:** 線形履歴以外の便益が乏しく、mergeより明確に高コストなので不採用が妥当。

## 親の結論のうち支持できないもの

1. **「三択が成り立たない」**  
   master直行が不成立なだけ。択一は「据え置き／選択的backport／full merge」に再定義できる。

2. **(P1) full merge を既定推奨とすること**  
   一般 upstream 同期が目的なら妥当だが、SS2PL利用だけなら2～3 commitのbackportか既存patchの方が安い。

3. **(P3) held 9件の追加コストがゼロ**  
   正しくは「即時赤は増えないが、解除時負債は増える」。

4. **F10 の live literal 7件**  
   MOCC 3件は歴史的pairなので不変。live は4件である。

5. **F11 の「T-1506が稼働中で、058 branchもbaseごと動かす必要がある」**  
   T-1506は着地済み。真の未着地作業はmocc-g2であり、歴史的pairは動かさず、同作業のlandを待てばよい。

6. **成果物影響(a)「据え置くとSS2PL materials campaignを開始できない」**  
   descriptive study は現 pin＋patchで既に完走済み。開始できないのは未配線の certified SS2PL 経路であり、現行Phaseのblocking taskではない。

## 総括

推奨は **「現時点では上げない」**。SS2PL study は現 pin＋patchで完了し、Phase 3 の現行経路も SS2PL を要求していない。  
mocc-g2 を先に着地させ、歴史的 `511c9538→058d0c4e` pair は不変に保つ。  
certified SS2PL consumer が具体化した時点で、まず `b629dc1＋df47e3a` の選択的 backport を再裁定する。  
一般 upstream 同期まで必要になった場合だけ、human push と remote 到達確認を条件に full merge を選ぶ。  
本レビューは静的検査と read-only Git 問い合わせのみで、pytest は実行していない。