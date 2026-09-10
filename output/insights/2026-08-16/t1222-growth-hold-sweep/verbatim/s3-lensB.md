静的検査のみ。pytest・Web検索は実行していない。

```text
[BLOCKER / REAL] 段2の230件で母集合が閉じたという主張

主張：
段2の「230 function node」が、指定範囲の比例 node を網羅している。

根拠 file:line：
s2-plan.md:3-7,50-70,401-404 は `check_docs.py` 文字列検索と、S8c の3 nodeだけを列挙している。
実際には orchestrator/tests/test_s8c_preregistration_invariant.py:252-274 が実 ROOT を確認した後、`check_docs.main()` を同一プロセスで呼ぶ。`.py` 文字列を含まないため、段2の subprocess 検索では拾えない。

これが真なら何が壊れるか：
230件・74件登録・3 pin・inventory が過少になる。docs bytes に比例する約5秒級の実 repo 読み取りが既定走行に残る。

提案：
この node を候補集合へ追加し、D451を別判定する。既存の positive `check_docs` node と同じ executable だから自動的にRとはせず、negative-control検出力の代替経路を確認する。

[BLOCKER / REAL] in-process provenance 呼び出しの取りこぼし

主張：
subprocess検索と AST 閉包で production の重い呼び出しを拾えている。

根拠 file:line：
orchestrator/tests/test_check_ai_provenance.py:18,2646-2652 は実 REPO を既定利用する `provenance.main()` を直接呼ぶ。
tools/check_ai_provenance.py:30,1122-1145,1316-1323,1365-1392,1552-1560 は policy `git log`、全祖先 `rev-list`、ancestry構築を実行する。
この node は s2-plan.md:133-459 の230 node一覧にない。

これが真なら何が壊れるか：
対象範囲は1 commitでも、履歴 commit 数と policy履歴に比例する費用が受入に残る。段2の230件と「未検出0」の根拠が崩れる。

提案：
少なくとも候補数を232件へ修正する。tools/dev_wave_land.py:1845-1878,2701-2702 と tools/dev_waves/cli.py:188-195 に独立 provenance 経路があるため、D451は有力だが、既知違反の固定期待値を失う collateral note を必須にする。

[REFUTED / ただし監査記録の欠陥] floor の direct call は新規 hold ではない

主張：
別名 root と indirect production call の発見例として、floor node を230件へ追加すべきである。

根拠 file:line：
orchestrator/tests/test_s8b_floor_campaign.py:1233-1239 は実 ROOT を clone し、:6678-6680,7040-7048 は clone root を campaignへ渡す。:7058,7065 は production の `enumerate_repository_files(clone_root)` を直接呼ぶ。
しかし orchestrator/tests/conftest.py:246-247 と test_real_repo_serialization.py:99-100 が同 nodeを既に `REAL_REPO_SERIAL_NODES` の独立 goldenへ登録している。
また s2-plan.md:486 の self-loader 行は現ソースの実位置7191-7194とずれている。

これが真なら何が壊れるか：
serial ledger と growth hold の二重登録、不要な guard、件数の二重計上を招く。逆に stale line は guard可否の判断を誤らせる。

提案：
新規holdにはせず、棚卸しに `already_default_serial` として明記する。行番号ではなく node IDとASTアンカーで self-loader根拠を記録する。

[REAL] 親の copytree refuted は誤り

主張：
親 brief.md:70-72 の「copytree系は成長比例でない」という裁定。

根拠 file:line：
親 brief.md:56-59 は現在7〜13 file、数msだから比例でないとするが、D335は docs/decisions.md:14959-14974 で構造比例を基準にする。
orchestrator/tests/test_codex_agents.py:37-46 は実 `.claude/agents`、`.codex/role-adapters`、`orchestrator/codex_roles` を copytree する。
test_dev_waves_checker.py:60-71 と test_dev_waves_integration.py:160-185 は実 `tools/task_runs` を copytree する。

これが真なら何が壊れるか：
role/tool/task-run file が増えるたびにコピー量が増えるD335違反を、現在の短い実測だけで見逃す。親P1の refuted 根拠は成立しない。

提案：
実測秒数ではなく、source subtreeが実 repository の可変集合かで判定する。synthetic tmp fixtureは除外し、実 subtree copyは比例候補として扱う。

[REFUTED / 部分的にREAL] 「headで切った」は確認できないが、wc -lは完全性を証明しない

主張：
段2のゼロ件根拠が `head` 切りである。

根拠 file:line：
s2-plan.md:29-70 は `head` を使っていないと明記し、各検索結果を `wc -l` で数えている。この攻撃自体は成立しない。
一方、s2-plan.md:50-54 の `.py`文字列・root名検索は、上記 :274 と provenance.main を落としている。

これが真なら何が壊れるか：
「検索式ごとの全件数」を「候補の全件数」と誤認し、該当なしの主張を過大にする。

提案：
「式Xのヒット数」と「候補集合の件数」を分けて記録する。ゼロは「宣言した primitive と AST規則の範囲で未検出」と書き、globalなゼロとは書かない。
ratifiedの固定 `_REAL_V1`（test_s8b_ratified_verify.py:48-54）と、最初のsilo node（test_silo_ladder_rung1_evidence.py:1202-1213）は固定量という反証があり、この部分の親裁定は維持できる。

[REAL] module/session fixtureの部分保留は純損失

主張：
親 brief.md:73-77 の、S8cの名指し1 nodeだけを保留候補にする考え。

根拠 file:line：
test_s8c_preregistration_invariant.py:76-100 の `_candidate_commit` は実 indexへ `read-tree`、`add -A`、`write-tree`、`commit-tree` を行う。
:118-121 の session fixtureが、:125,190,206 の3 consumerへ共有する。
D451の正本 docs/decisions.md:18873-18881 も、1 consumerが残ればfixture費が残ると明記する。

これが真なら何が壊れるか：
最後のscan nodeだけを保留してもfixture構築費は残り、holdout/candidate検出力だけを削る。3 node全保留なら防壁がゼロになる。

提案：
3 nodeとも既定走行に残す。費用を下げるなら、fixture入力をbounded化する設計変更を先に行い、部分holdはしない。
なお :257 の新規negative-control nodeには `@CANDIDATE_XDIST_GROUP` がなく、個別5秒が受入wall短縮を保証するわけではない。critical-path測定なしにwall削減を断定しない。

[REAL] P3の経路同値はpositive gateに限る

主張：
s2-plan.md:467 の「check_docsを呼ぶ3 nodeは独立経路で同じ検出をする」という拡張。

根拠 file:line：
既存positive nodeは test_check_docs.py:7282-7289,7462-7471,9433-9441。
landは tools/dev_wave_land.py:2211-2237,2335-2342、wave checkerは tools/dev_waves/checker.py:351-361,643-688 で実 `check_docs.py` を実行する。このP3判定は妥当。
しかし新規S8c nodeは test_s8c_preregistration_invariant.py:257-279 で不在path・腐敗行番号を注入するnegative controlであり、land/checkerのclean positive実行とは検出対象が異なる。

これが真なら何が壊れるか：
「同じmainを呼ぶ」だけを根拠にnegative-control nodeを保留すると、mutation検出力を失う可能性がある。

提案：
既存3 nodeのR判定とS8c negative nodeのD451判定を分離する。後者は独立negative routeが確認できるまでN扱いにする。

[REAL] 台帳は3 pinだけでは閉じない

主張：
親 brief.md:40-42 の3 pin更新を中心に追加すればよい。

根拠 file:line：
正本は growth_test_holds.py:99-512。
3 pinは test_growth_test_holds_contract.py:39-41,228-231。
独立 collateral mirrorは同:60-150,363-379、guard filenameとAST検査は同:475-525,589-607。
test_hold_inventory.py:26-200,304-324,504-512,650-656 は独立期待集合を再構成する。
collection metadataは conftest.py:390-435。
serialへ移す場合だけ conftest.py:170-180 と test_real_repo_serialization.py:38-70,724-737 のgoldenも波及する。
release transportは dispatch_compute.py:58-71 と test_hold_inventory.py:577-596。
row追加だけなら run_tests.py:799-808 と test_growth_test_holds_contract.py:382-410 のsuite identityは変更してはいけない。

これが真なら何が壊れるか：
registryだけの変更はpin・mirror・guardで止まる。逆に `test_growth_test_holds_contract.py:228-231` はpinをregistryから再計算するだけなので、3 pinだけを共変更すれば通り、D335/D451の妥当性は検査しない。全mirrorとpinを共変更すれば、意味論的な誤登録も通り得る。

提案：
registry、3 pin、collateral、expected group、guardを同一変更として監査する。serial golden、dispatch allowlist、suite identityは必要な場合以外触らない。比例性とD451の根拠は契約テストではなく段3裁定記録に残す。

[REAL] completeness表現は registered-layers-only に限定する

主張：
s2-plan.md:529-537 の「7,941-node母集合」「230 candidate」を、そのままworklog/insightのhold inventory説明に使える。

根拠 file:line：
tools/hold_inventory.py:1-4,35-38 は `registered-layers-only` と未知層の自動発見非保証を明記する。
test_hold_inventory.py:731-749 は全層・complete inventory・完全性保証の主張を拒否する。
現worktreeにはT-1222 insight directory自体がなく、既存記録の違反は確認できない。ただし無修飾の「母集合が閉じた」「全件網羅」は危険。

これが真なら何が壊れるか：
2登録層のsnapshotをrepository全層のcomplete inventoryとして利用者が誤認する。D347の制限に反する。

提案：
次の定型文を使う。
「対象は `orchestrator/tests` のtop-level test nodeと、本文に列挙した探索primitive・既存2台帳に限定した候補分析である。数値はこの対象内の候補数を示す。hold inventoryの `completeness` は `registered-layers-only` であり、未知のhold層は自動発見しない。」

[REAL] I3は妥当だが、禁止範囲を狭く書くべき

主張：
親 brief.md:34-35 の、母集合閉包検査を一切新設しないというI3。

根拠 file:line：
D335 docs/decisions.md:14959-14979 はrepository成長比例テストの新設を禁止する。
一方、s2-plan.md:32-42 の直接copytree検索は34 call site、copytree/copy2等は99 hit、top-level testは8018（同:76-82）。候補は現在230件、上記2件を加えて232件、約2.9%であり「ほぼ全テスト」ではない。
固定pathの単一文書readは自動的に比例とは限らない。test_check_ai_provenance.py:761-764 は `docs/ai-provenance.md` を読むが、tools/check_docs.py:193-197 の6300-byte hard limitでboundedである。

これが真なら何が壊れるか：
全repositoryを走査するclosure detectorをacceptanceへ追加すれば、detector自身がD335対象になる。逆にI3を広く解釈しすぎると、固定費の台帳整合検査まで禁止してしまう。

提案：
判定式を次で固定する。
`P(t) = real-root ∧ unbounded-input(F_t) ∧ W_t = Ω(|F_t| または bytes(F_t)) ∧ default-selected`
ここでF_tは実repositoryの可変集合。固定tmp fixtureや固定byte ceilingは除外する。
I3は「acceptance内のunbounded repository-wide closure scan」を禁止し、固定台帳・hash整合検査と、wave差分だけを見る外部preflightは許可する。未知の将来nodeを同じ固定費で検出する方法はない。
```

## 総括

- BLOCKER: 230件は閉じておらず、少なくともS8cの `check_docs.main()` と provenance の2 nodeが漏れている。
- REAL: 親のcopytree非比例裁定はD335の構造基準に反する。
- REAL: S8c共有fixtureの部分保留は費用を残して検出力だけ削る。
- REAL: P3は既存positive checkには有効だが、negative-controlへ自動拡張できない。
- REAL: `_HOLD_ROWS` 追加はpin、mirror、guard、inventoryへ波及する。
- REAL: inventory文言は `registered-layers-only` に限定する必要がある。
- REFUTED: 段2が`head`で切ったという攻撃。計数自体は`wc -l`で行っている。
- REFUTED: floor direct callは新規holdではなく、既存serial goldenに登録済み。
- I3はacceptance内の全体走査を禁じる点で妥当、差分限定preflightまで禁じるのは過剰。
- pytest・Web検索・緑の主張はしていない。