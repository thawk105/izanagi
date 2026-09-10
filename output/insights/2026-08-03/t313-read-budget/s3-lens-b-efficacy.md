判定は **NO-GO**。plan v1 のまま段 4 で採用してはならない。静的検査と Git 履歴だけを行い、実装・テスト実行・ファイル変更はしていない。worktree は clean。

## 容量の再計算

現行 gate は family 残余 2 bytes が先に効く。新 gate の file ごとの実効余地は次のとおり。

| 場所 | 現在 | 旧 gate の追加可能量 | plan の追加可能量 | 実質解放 |
|---|---:|---:|---:|---:|
| `core.md` | 8,537 | 2 | 139、L1 全体で共有 | 最大 +137 |
| `workers.md` | 4,623 | 2 | 139、L1 全体で共有 | 最大 +137 |
| `mutation.md` | 3,682 | 2 | 139、L1 全体で共有 | 最大 +137 |
| `operations.md` | 8,356 | 2 | L1 139 + L2 8,863 = 9,002 | **+9,000** |

上3冊の 139 bytes は同時に使える値ではなく、L1 全体で一つの共有枠である。新 gate の理論上限は `20,200 + 14 × 1,000 = 34,200 bytes`。旧 25,200 に対して **9,000 bytes、35.7% の受理拡大**となる。

## 所見

### B-01 — BLOCKER / real: これは「置換」ではなく、二方向で予算を引き上げている

親 brief は [brief.md:11](/work/1/SFC/tanab/izanagi-jobs/9aba3998/t313/brief.md:11) で「**予算値の引上げは不採用**」と固定している。一方 plan は [plan.md:168](/work/1/SFC/tanab/izanagi-jobs/9aba3998/t313/plan.md:168) で L1 に 139 bytes の headroom を置き、[plan.md:174](/work/1/SFC/tanab/izanagi-jobs/9aba3998/t313/plan.md:174) で「これは予算値の引上げではありません」と断定する。

この断定は成立しない。

- 現在の L2=5,137 を固定した旧 gate で許される L1 最大値は `25,200 − 5,137 = 20,063`。
- plan の 20,200 は、その同条件より **137 bytes 広い**。
- family 全体では最大 34,200 となり、旧上限より **9,000 bytes 広い**。

「引上げでない」の判定基準は、厳格なら L1 ceiling=20,061、旧残余 2 bytes まで保存するなら最大20,063である。20,200 はどちらにも入らない。

逆に20,061〜20,063へ締めると、L1 義務の追加余地は0〜2 bytes、L2新節の余地も0節で、後続義務を入れる目的を達成しない。これはコードで解ける矛盾ではなく、追加余地を許すかの再裁定が必要である。

反証条件は「L1 +139、L2 +8,863、family +9,000 を置換由来の意図的緩和としてユーザーが明示承認すること」。現裁定にはない。

### B-02 — BLOCKER / real: 解放先が偏り、歴史的な必要箇所とも十分一致しない

plan 自身が [plan.md:170](/work/1/SFC/tanab/izanagi-jobs/9aba3998/t313/plan.md:170) で「L2節数 cap 14 / 現行14 / headroom 0節」と認め、[plan.md:172](/work/1/SFC/tanab/izanagi-jobs/9aba3998/t313/plan.md:172) で新節ごとの独立審査を要求している。これは「残2 bytes」を「残0節」に置き換えただけである。

`git log --numstat -- docs/dev-wave/` と作成 commit `2cd329d` からの再計測は次のとおり。

| file | `2cd329d` | `e0b9073` | 増分 | touch commit数 |
|---|---:|---:|---:|---:|
| core | 7,830 | 8,537 | +707 | 20 |
| workers | 4,362 | 4,623 | +261 | 10 |
| mutation | 3,331 | 3,682 | +351 | 6 |
| operations | 7,081 | 8,356 | **+1,275** | **30** |

operations が最大の成長先なのは real。ただし内訳は、[operations.md:125](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/docs/dev-wave/operations.md:125) の無条件 `DW-O23` 新設だけで +1,123 bytes、operations 純増の88%を占める。現行L2節は +518 だが、旧L2 `DW-O07` 483 bytes の削除を含めると条件節全体の純増は約35 bytesにすぎない。

さらに増加実績のある主要L2節ほど余地が小さい。

| 節 | 現在 | 作成時からの増分 | 新 cap まで |
|---|---:|---:|---:|
| `DW-O09` | 935 | +294 | **65** |
| `DW-O17` | 703 | +410 | 297 |
| `DW-O19` | 675 | +137 | 325 |
| `DW-O20` | 489 | +221 | 511 |
| 新しい条件節 | — | — | **0節** |

一方、縮小してきた節を含む場所へ6,473 bytes相当の余地が残る。理論上8,863 bytes解放しても、最も太った `DW-O09` には65 bytes、新しい発火条件には0節しか来ない。

反証条件は、後続義務を「どの既存L2節へ何bytes入れるか」まで列挙し、全件が当該headroom内に入ること。brief/planにはその需要対応表がない。

### B-03 — BLOCKER / real: T-314 は1 byteも unblock されない

T-314 の一次資料は [worklog archive:924](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/docs/archive/worklog-phase3-0802-106-110.md:924) で「裁定待ち項の一貫した目印」、[同:928](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/docs/archive/worklog-phase3-0802-106-110.md:928) で「`.claude/commands/rulings.md` に余白6 bytesしかないため T-313 後」としている。

しかしplanは [plan.md:144](/work/1/SFC/tanab/izanagi-jobs/9aba3998/t313/plan.md:144) で「command/self/provenanceの既存capには触れません」と明記する。したがって T-313 が解放する `docs/dev-wave/**` の余地は、T-314 の `rulings.md` へ移らない。

現在は D129 により `rulings.md` が4,601/5,000、残399 bytesになっているが、それはT-313の効果ではない。親が前提にした依存関係は既に誤りか陳腐化している。

反証条件は、T-314が `rulings.md` を変更せず `docs/dev-wave/**` だけへ入る設計を示すこと。一次資料と逆である。

### B-04 — BLOCKER / real: L1 は「実際の常時読量」ではない

[core.md:8](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/docs/dev-wave/core.md:8) は L1 を「段 dispatch の無条件節」と定義する一方、[core.md:12](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/docs/dev-wave/core.md:12) は既定軽量版で段2・3・6を省けるとしている。省略した段の「無条件節」は、そのwaveでは読まれない。

それでもplanは [plan.md:62](/work/1/SFC/tanab/izanagi-jobs/9aba3998/t313/plan.md:62) で workers全8節、mutation全8節をL1へ入れる。ユーザー裁定の根拠だったdocs-only実読10,515 bytesに対し、提案proxyは20,061 bytesで **1.91倍**である。

逆方向にもずれる。現在の段6・全条件成立時のreference読量は15,746 bytesだが、新L2余地を使い切ると最大24,748 bytesへ **57%増えても gate は緑**である。読量過多という実害を守れていない。

より適切なrepo決定的proxyは、実行時の一値ではなく段別 envelope である。現行の代表値は段5最悪10,315、段6最悪15,746、段8はselfを含め7,497。段ごとの「無条件 + 到達可能条件の最大」を制約すれば、実行履歴に依存せず実害へ近づけられる。

反証条件は、守る対象を「各agentが読む量」ではなく「全段で参照され得るIDの和」と明示的に再定義すること。44%の実読を根拠にした裁定とは整合しない。

### B-05 — HIGH / real: L1分類はdispatch表との二重管理で、drift検査がない

plan は [plan.md:39](/work/1/SFC/tanab/izanagi-jobs/9aba3998/t313/plan.md:39) で無条件/条件付きmapをコード内に新設し、既存照合はその和だけにするとしている。

現行parserは [check_docs.py:2339](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/tools/check_docs.py:2339) から行内pairをstage集合へ足すだけで、「成立した条件」「commitするなら」という修飾を保存しない。実際の表には [dev-wave.md:66](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/.claude/commands/dev-wave.md:66) の「成立した条件の」、[同:74](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/.claude/commands/dev-wave.md:74) の「commitするなら」がある。

そのため、例えば段7の「成立した条件の」を削って無条件化してもpair集合は不変で、checkerは通るが実読量だけ増える。逆に段9へ「commitするなら」を足しても `DW-O23` はコード上L1のままになる。

テストfixtureも [test_check_docs.py:371](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/orchestrator/tests/test_check_docs.py:371) からflattened集合を再生成し、修飾語を持たない。planned literal testはコード側分類をpinするだけで、commandとの一致を証明しない。

反証条件は、parserが各stage rowの条件性を保持し、typed contractとの完全一致を検査すること。

### B-06 — HIGH / real: 受理集合表がparser変更を取り落としている

現行H2検査は [check_docs.py:2773](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/tools/check_docs.py:2773) のraw regexである。planは [plan.md:102](/work/1/SFC/tanab/izanagi-jobs/9aba3998/t313/plan.md:102) でfence/commentを無視する可視inventoryへ置換する。

これはbyte gate以外の受理集合も変える。

- 実H2 + fence内同名H2: 現行は重複で赤、新は緑。
- fence内H2だけ: 現行は必須節として数え得る、新は欠落で赤。
- fence内孤児H2: 現行は赤、新は緑。

しかし [plan.md:232](/work/1/SFC/tanab/izanagi-jobs/9aba3998/t313/plan.md:232) の受理集合表にはこれらがなく、「最後の二行が新たに狭まる受理集合」と断定している。briefの「受理集合変更を表に残す」という不変条件を満たさない。

反証条件は、parser意味変更を別変更へ分離するか、上記の双方向ケースを受理集合表へ追加すること。

### B-07 — mixed: 「operations capを残すと解放ゼロ」は逐語ではrefuted

親は [brief.md:19](/work/1/SFC/tanab/izanagi-jobs/9aba3998/t313/brief.md:19) で operations 残余44 bytesを示した直後、[brief.md:20](/work/1/SFC/tanab/izanagi-jobs/9aba3998/t313/brief.md:20) で「実質何も解放しない」と一般化する。

正確には次のとおり。

- family capを外し、4個別capを残す: operationsは2→44で **42 bytes解放**。family全体は2→1,552で **1,550 bytes解放**。
- operations個別capだけ外し、family capを残す: family残余2が効くので **追加解放は0**。

したがって親の主張は「operationsに意味のある量が来ない」という評価なら方向的にrealだが、「ゼロ」という計算はrefuted。ユーザー例の単純案は本当に即時解放ゼロであり、容量を作るには他冊の縮小・機械化が要る。

### B-08 — complexity / real: 費用対効果は、9,000-byte緩和を承認しない限り合わない

現行gateは [check_docs.py:2534](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/tools/check_docs.py:2534) のcap-sumと [同:2701](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/tools/check_docs.py:2701) のaggregate比較が中心である。

planはtyped dispatch二面化、raw section slicer、H2 semantics変更、read loop再編、3 gate、8新テスト、8変異を導入する。対価が「L1 +137 useful bytes、L2新節0」であれば過大である。

比較すると、

- operations capだけ撤去・family維持: 実装は単純、即時余地は2 bytesのまま。
- family撤去・個別cap維持: 単純、operationsに44 bytes、familyに1,552 bytes。ただし常時読量を測らない。
- 段別envelope + 旧family外枠維持: 中程度の複雑さで実害と総量を両方守る。現在値にpinすれば引上げなし。
- plan案: 最も複雑で、重いwaveの読量を最大約9KB広げる。

即時余地・予算据置き・実害制約の三つは同時には得られない。planはその矛盾を「新軸だから引上げでない」と言い換えている。

### B-09 — refuted: 段5を単一実装単位にする判断自体は妥当

[brief.md:70](/work/1/SFC/tanab/izanagi-jobs/9aba3998/t313/brief.md:70) は2ファイルの相互依存を理由に単一workerとする。checker定数・parser・fixture・境界期待値が相互に依存し、code/testを別workerへ分けると同じ箇所を競合編集する。ここは欠陥ではない。

問題は分割ではなく設計面積である。planを縮めてから単一authorへ渡し、独立レビューを段6に残すのがよい。

### B-10 — MEDIUM / real: briefの受入環境がPegasus契約と矛盾する

[brief.md:75](/work/1/SFC/tanab/izanagi-jobs/9aba3998/t313/brief.md:75) はPegasus login上の `run_tests.py` としつつ、次行で「計算ノードは不要」とする。しかし [AGENTS.md:36](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/AGENTS.md:36) はloginでpytestを一切禁止し、[run_tests.py:10](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/tools/run_tests.py:10) もloginからgen_Sへ同期dispatchすると明記する。

正しくは「loginからwrapperを起動し、テスト本体は計算ノードへdispatch」。本レビューではテストを走らせておらず、緑は主張しない。

## 裁定パッケージ候補（scope外）

### P-A — L0とselfを「常時読量」に含めるか

planは [plan.md:66](/work/1/SFC/tanab/izanagi-jobs/9aba3998/t313/plan.md:66) で入口をL0、selfを対象外とする。しかしcommandは [dev-wave.md:14](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/.claude/commands/dev-wave.md:14) でselfの一部を開始時に読み、[同:73](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/.claude/commands/dev-wave.md:73) で段8に全節を読む。

- entry command: 8,907 bytes
- self: 5,997 bytes
- 対象外の常時層合計: **14,904 bytes**
- plan L1と合わせた成功waveの基礎集合: **34,965 bytes**
- selfの現行cap残余: **3 bytes**

従って新gateを「dev-wave全体の常時読量」と呼ぶのは誤り。scopeを広げないなら名称を「4 referenceのdispatch-L1量」と限定し、L0/selfとの合成値を別途報告するべきである。family拡張はユーザー裁定候補。

### P-B — provenanceとの方式統一

[D110:5125](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/docs/decisions.md:5125) はprovenanceについて「個別capとfamily上限を独立に置き、総量は上げない」と裁定し、現在8,981/9,000である。planはdev-waveで個別・familyの両方を削除するため、同じ「常時読量」に逆のschemaが並立する。

ただし [core.md:52](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/docs/dev-wave/core.md:52) のDW-G03違反だと直ちに断定するのも不正確である。planは局所変更であり族一般化そのものではない。またprovenanceは単一の常時入口、dev-waveは段別contextで構造が異なる。

裁定候補は次の二択。

- dev-wave固有方式として残し、provenanceとの差と「常時読量」の別定義を明記する。
- provenance/dev-waveを独立2例としてproducer/consumer同型性を立証し、共通family schemaを別waveで裁定する。

現waveでprovenanceを便乗変更するのはscope拡大である。

## 総括

- 最大所見は、planが旧25,200に対し最大34,200 bytesを受理し、L1も旧同条件より137 bytes広げる点。現裁定下では予算引上げである。
- 解放9,000 bytesはoperationsへ偏るが、新L2節は0、最大成長節O09は残65 bytes。T-314の`rulings.md`には1 byteも来ない。
- L1は実読量ではなく全段unionで、軽量waveを約1.9倍に過大評価する一方、重い段6を最大57%肥大させても検出しない。plan v2前に指標と許容緩和の再裁定が必要。