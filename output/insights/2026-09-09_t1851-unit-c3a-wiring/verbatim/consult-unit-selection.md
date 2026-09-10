## 総括

次は **C3** を選ぶ。C3 は旧 6 段の C に残った「production 配線＋実環境値域」であり、`C → D2` の依存順を引き継ぐ。  
既存基盤が揃っているため、見積りは 5 file / 350–550 行、焦点 test 12–18 node 程度で、上限寄りだが 1 wave に収まる。  
ただし C3 完了には、配線後の production 経路による計算ノード上の実 campaign が必要である。既存 fake や単体 `measure_point()` probe では代替できない。  
本 consult では静的読解と `rg` のみを行い、pytest・campaign は実行していない。

## 依存順の実測

強制順序は **C3 → D2** である。

- 6 単位分割の正本は順序を `B1 → A → B2 → D1 → C → D2` と明記する。[s4-adjudication-r2.md:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/output/insights/2026-09-01_t1946-t2107-registry-wiring-design/s4-adjudication-r2.md:29)、[s4-adjudication-r2.md:34](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/output/insights/2026-09-01_t1946-t2107-registry-wiring-design/s4-adjudication-r2.md:34)
- 契約は役割を「C1b が実体化、C2 が供給、D2 が再検証」と定めている。[contract-v3.1.md:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/output/insights/2026-09-08_t1851-unit-c1b-sealed-terminal-evidence/contract-v3.1.md:17)
- 現 C2 は producer 側の 1〜3 だけを実装し、production 配線と実値域を達成していない。[README.md:11](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/output/insights/2026-09-08_t1851-unit-c2-derivation/README.md:11)、[README.md:87](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/output/insights/2026-09-08_t1851-unit-c2-derivation/README.md:87)
- 裁定 2 (a) は、その残余を C3 に移す案である。[ruling-package.md:87](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/output/insights/2026-09-08_t1851-unit-c2-derivation/ruling-package.md:87)

したがって C3 は独立した新機能というより、旧 C の供給責務の残りである。D2 の fixture 作成だけを先行できる余地はあっても、D2 単位を完成扱いにはできない。

## 選んだ単位の scope 境界

静的な 5-file 上限は次の構成を推奨する。

- `orchestrator/campaign/s8b_floor_campaign.py`: 約 180–260 行  
  `_run_session()` の直接 probe／`measure_fn`／`_finish_session()` 経路を launcher に接続し、closed genesis、reservation、terminal builder、prefix capture、resume/finalize を束縛する。現状は campaign が直接計測している。[s8b_floor_campaign.py:6215](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_floor_campaign.py:6215)、[s8b_floor_campaign.py:6262](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_floor_campaign.py:6262)
- `orchestrator/campaign/s8b_floor_contract.py`: 約 2–15 行  
  production result を既設 v5 契約へ切り替える。現状は v5 shape が存在する一方、producer alias は v4 のままである。[s8b_floor_contract.py:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_floor_contract.py:29)、[s8b_floor_contract.py:96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_floor_contract.py:96)
- `orchestrator/tests/test_s8b_floor_campaign.py`: 約 150–230 行
- `orchestrator/tests/test_s8b_floor_contract.py`: 約 10–25 行
- `orchestrator/tests/acceptance_duration_ledger.json`: 約 8–25 行、add-only

合計は概ね **350–550 行**。launcher 自体には production `capture_measure_point` と公開入口が既にあるため、原則として変更しない。[s8b_floor_attempt_launcher.py:210](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_floor_attempt_launcher.py:210)、[s8b_floor_attempt_launcher.py:1189](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_floor_attempt_launcher.py:1189)  
live v5 inspector も既設である。[s8b_floor_stats.py:1155](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_floor_stats.py:1155)

焦点 test は 12–18 node を目安とする。

- production caller の実到達性
- planned/retry 全 slot の closed genesis
- marker・claim・schedule・attempt identity の等値束縛
- 7-key rep evidence の terminal 化
- competing／capture failure／partial／integrity の precedence
- terminal の一回記録
- v5 result の prefix proof
- 別世代・改竄 proof の拒否
- cut-6 resume と finalize-pending の再入
- caller が registry や sealed result を注入できないこと

既存 5-file 枠を越えて registry core、holdout admission、D2 consumer の改変が必要になった場合は C3 を完成扱いにせず停止する。その場合のみ、ユーザー裁定を得て `C3a=配線・v5 producer`、`C3b=実 campaign・値域記録` に分け、両方を D2 より先に置く。

## 実測の要否

**要る。計算ノード上の実 campaign が必要。**

契約 9 節は、現在の gate 入力が fake 値域だけであり、実環境値域を未主張だと明記する。[contract-v3.1.md:455](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/output/insights/2026-09-08_t1851-unit-c1b-sealed-terminal-evidence/contract-v3.1.md:455)、[contract-v3.1.md:457](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/output/insights/2026-09-08_t1851-unit-c1b-sealed-terminal-evidence/contract-v3.1.md:457)  
C2 の走査でも、production caller、campaign から registry への参照、実 campaign 成果物はいずれも 0 件だった。[README.md:92](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/output/insights/2026-09-08_t1851-unit-c2-derivation/README.md:92)、[README.md:95](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/output/insights/2026-09-08_t1851-unit-c2-derivation/README.md:95)

最低限必要なのは、配線後の default production 経路、すなわち injected `measure_fn`／`probe_fn`／fake registry を使わない fresh pilot campaign である。trace-disabled の実 binary を計算ノードで走らせ、次を記録する。

- commit、env tag、protocol／freeze／manifest digest
- 実際の probe、7-key rep evidence、throughput・失敗 counter の観測範囲
- terminal evidence と registry row
- result v5 の prefix proof
- live verifier による同一 prefix の再検証結果

全異常枝を自然発生させる必要はなく、枝の閉包は unit test が担う。ここで必要なのは、fake でない campaign→launcher→registry→result の実到達と、そこで観測された値域である。

## 裁定未記録の扱い

**C3 を provisional な次作業として進めてよいが、7 単位化を親の確定裁定として記録・land してはならない。**

- D1341 が禁じるのは配線または proof 検査の片側 land であり、同一 branch 上の未 land checkpoint 作成ではない。[decisions.md:42841](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/docs/decisions.md:42841)、[decisions.md:42850](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/docs/decisions.md:42850)
- D1703 は、前提が動く間は個別裁定せず、所有 wave が着地時に整理・再提示するとしている。また、裁定待ちでも進行中作業は塞がらないと確認している。[decisions.md:51860](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/docs/decisions.md:51860)、[decisions.md:51868](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/docs/decisions.md:51868)、[decisions.md:51871](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/docs/decisions.md:51871)
- D1675 は、親裁定を後からユーザーが明示的に追認した先例である。[decisions.md:51137](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/docs/decisions.md:51137)
- D1660 に従い旧世代 token を近道にせず、current-generation marker で新規実走する。[decisions.md:50849](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/docs/decisions.md:50849)
- D1661 は主経路 C を先に通すとし、journal TOCTOU の追加防壁を現 scope に混ぜない。[decisions.md:50866](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/docs/decisions.md:50866)、[decisions.md:50872](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/docs/decisions.md:50872)

したがって親は「ユーザーから委任された次単位の選択」として C3 を開始し、成果は unlanded checkpoint に留める。全単位が揃った時点で裁定 2 を再提示し、ユーザー追認と decisions fragment を得てから land する。

## 最強の反論と応答

最強の反論は、「D2 は既存 6 分割で明示済みの最後の単位だが、C3 は decisions 未記録の新設単位であり、さらに実 campaign と main 取り込み競合まで伴う。まず D2 の consumers/fixtures を終える方が承認済み計画に忠実」というもの。

それでも推奨は変えない。D2 の責務は C が供給した値を再検証することであり、供給前の fixture は fake 値域しか固定できない。これは契約 9 節が明示した未充足状態を consumer 側で固定し、C3 後の再作業か、より悪ければ恒真な検証を作る。main 競合は C3 着手前に解く統合作業であって、`C → D2` の意味依存を逆転させない。

## 却下した案

- **D2 を先行:** supplier 不在のまま consumer/fixture を完成扱いにするため却下。
- **C2 をさらに延長:** 7-key producer の受入と production 配線の受入が混ざり、裁定 2 自身が 1 wave 不適とした。[ruling-package.md:90](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/output/insights/2026-09-08_t1851-unit-c2-derivation/ruling-package.md:90)
- **実値域を schema 準備または fake で代替:** 契約の正しさゲートを弱めるため却下。
- **直ちに C3a/C3b へ再分割:** 現時点では必要な launcher・v5 schema・live inspector が既設で、5-file 上限内と見込める。上限超過を静的に確認した場合だけユーザー裁定へ戻す。