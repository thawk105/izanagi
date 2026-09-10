## B-1 — BLOCKER

- 主張: zero-test probe は「計測用」という名目で production shard 選択後に `items[:] = []` とし、brief が禁止した selection 縮小を明示的に行う。
- 根拠: brief は selection 縮小を一切検討しないとする [brief.md:25-30](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2097-fixed-cost-decomp/brief.md:25) 一方、plan は production plugin の割付後に全 item を除去し、rc=5 を期待する [stage2-plan.md:238-250](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2097-fixed-cost-decomp/artifacts/t2097-fixed-cost-decomp/stage2-plan.md:238)。production plugin は既に担当 shard への deselect と selected state の保存を済ませる [acceptance_shards.py:825-852](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-fixed-cost-decomp/tools/acceptance_shards.py:825)。
- 成果物影響: selected と finished が一致しない非受入経路の値が「現在の受入固定費」としてレポート・台帳へ参照され、後続の certified 短縮対象選択を誤らせる。
- 直し方: plan の Z-A/Z-B 四 arm と P2 の zero-test 再測定を外し、real arm の測点だけで A/B/D/C を出す。zero-test 例外を残す判断は明示的な規律例外なので、実装案ではなく「裁定パッケージ候補」とする。

## B-2 — BLOCKER

- 主張: shard-2 だけを計装しても、「全 shard 共通の約 56 秒」の内訳は得られず、得られるのは shard-2 の内訳だけである。
- 根拠: D1384 は全 shard 共通成分を対象とする [D1384:44034-44045](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-fixed-cost-decomp/docs/decisions.md:44034) が、全 real arm は shard-2 固定である [stage2-plan.md:283-298](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2097-fixed-cost-decomp/artifacts/t2097-fixed-cost-decomp/stage2-plan.md:283)。既存 14 走が示したのは shard-1/2 の残余総量が近いことだけで [README.md:48-50](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-fixed-cost-decomp/output/insights/2026-09-01_t2097-acceptance-floor-decomposition/README.md:48)、既存 artifact から A/B/D/C は分離不能である [stage2-plan.md:527](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2097-fixed-cost-decomp/artifacts/t2097-fixed-cost-decomp/stage2-plan.md:527)。
- 成果物影響: shard-2 固有の成分構成が「共通内訳」として採用され、レポートと次の certified 短縮候補が誤った対象を指す。
- 直し方: 少なくとも shard-1 と shard-2 を同じ測点で別々に出し、両方で再現した成分だけを「共通」とする。shard-0 の追加計装は D1384 が採らなかった約 21.9 秒へ入るため「裁定パッケージ候補」とし、本 plan へ実装案を入れない。

## B-3 — MAJOR

- 主張: brief の既存被覆は、同じ性質の 48-worker・0-test wall を warm/cold で既に測った D918/F595 を落としている。
- 根拠: D918 は cache 無し 49.32 秒、cache 有り 15.40 秒を実測し [D918:33152-33170](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-fixed-cost-decomp/docs/decisions.md:33152)、F595 は cache 状態を照合しない probe が本番を代表しなかった失敗として記録する [failures.md:16526-16540](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-fixed-cost-decomp/docs/failures.md:16526)。D711 の 12.86 秒との差は node 数だけでなく cache regime でも説明できるが、plan の保存項目には rewrite-cache 状態がない [stage2-plan.md:415](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2097-fixed-cost-decomp/artifacts/t2097-fixed-cost-decomp/stage2-plan.md:415)。
- 成果物影響: 最大 33.9 秒の cache 差を node 増加や collection 成分へ誤帰属し、zero calibration とレポート値の選択が変わる。
- 直し方: brief の既存被覆へ D918/F595 を追加し、純増を「19215 node・当該 checkout の production-warm cache 状態における測点付き再観測」に狭める。plan には既存 rewrite cache の件数・有効性・受入前後関係を記録させる。

## B-4 — MINOR

- 主張: 約 56〜61 秒級の残余そのものと候補機構の存在は既に複数の決定で記録されており、新規性は残余の発見ではなく現在の checkout での測点付き分解に限られる。
- 根拠: D1103 は K=3・48 worker・17455 collection で `160.92 − 101.70 = 59.22 秒`を実測済み [D1103:37240-37258](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-fixed-cost-decomp/docs/decisions.md:37240)。D747 は 61.3 秒の残余へ unit 送信、index 検索、完了 event、pending 再走査、collection が混ざりうると記録済み [D747:29140-29143](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-fixed-cost-decomp/docs/decisions.md:29140)。D917 の 288-session 値は `wall − real-repo pole` なので今回の `wall − max report duration` とは異なる [D917:33129-33134](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-fixed-cost-decomp/docs/decisions.md:33129)。
- 成果物影響: 数値自体は変わらないが、レポートが既知の残余と候補を新発見として重複登録し、既存決定への参照を失う。
- 直し方: brief の既存被覆へ D1103/D747/D917 を異同付きで追加し、純増を A/B/D/C の時系列分離と現行 19215-node 条件への更新だけに限定する。

## B-5 — MAJOR

- 主張: `wall − max worker occupancy` を「固定費」または因果的な「report 外費用」と呼ぶ射程は、plan 自身の四項分解と既存裁定を超える。
- 根拠: D1298 はこの差を worker idle、lock 待ち、scheduler、session suffix が混ざる上界とする [D1298:41751-41754](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-fixed-cost-decomp/docs/decisions.md:41751)。F755 も「全 worker が test を走らせていない時間」ではないと導出済み [failures.md:19695-19718](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-fixed-cost-decomp/docs/failures.md:19695)。plan の D 項は別 worker が report を出していた時間そのものであり [stage2-plan.md:24-43](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2097-fixed-cost-decomp/artifacts/t2097-fixed-cost-decomp/stage2-plan.md:24)、plan も因果的総和ではないと認めている。
- 成果物影響: 並行度や workload で変わる露出残余が差し引き可能な固定費として台帳化され、後続の certified 改善量が過大評価される。
- 直し方: brief、artifact path、表見出しを `pytest wall − 最大 report duration 残余`へ改め、A/B/D/C は「露出 wall の加法区間」とだけ主張する。P3 は event の存在だけで成立扱いにせず、主成分性が示せなければ未解決または棄却とする。

## B-6 — MAJOR

- 主張: plan は新しい走行が既存の約 56 秒と同じ regime であることを束縛できず、D1299 の必須 metadata である growth-hold 状態も欠く。
- 根拠: D1299 は wall 主張に tested tip、K、worker 数、collection digest、growth-hold 状態の五つを要求する [D1299:41757-41771](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-fixed-cost-decomp/docs/decisions.md:41757)。plan の保存項目は HEAD、affinity、version、argv、digest までで hold がなく [stage2-plan.md:415](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2097-fixed-cost-decomp/artifacts/t2097-fixed-cost-decomp/stage2-plan.md:415)、P4 は page cache と温度が揃わないと認める一方 [stage2-plan.md:451-455](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2097-fixed-cost-decomp/artifacts/t2097-fixed-cost-decomp/stage2-plan.md:451)、受理条件は uninstrumented real residual が既存 56 秒級を再現したかを扱わない。
- 成果物影響: 別の hold/cache regime で得た分解が D1369 の 56 秒へ結び付けられ、レポートの参照先と採用値が変わる。
- 直し方: D1299 の五項を artifact field として明記し、checkout が worktree であることと cache 状態も併記する。control residual が既存分布と異なる場合は値を破棄するのでなく、「56 秒の分解ではない当該走の観測」と射程を狭める。

## B-7 — MAJOR

- 主張: A/B/B/A は各 arm 二走でも一つの PBS job・一つの node に閉じており、plan はその母集合を成果物の主張境界として固定していない。
- 根拠: 全八 arm は一つの gen_S job で逐次実行される [stage2-plan.md:283-296](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2097-fixed-cost-decomp/artifacts/t2097-fixed-cost-decomp/stage2-plan.md:283)。既存 14 走は七 tested tip にまたがり、56 秒級の中央値は複数走の記述的証拠にすぎない [stage3-consult-b.md:75-94](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-fixed-cost-decomp/output/insights/2026-09-01_t2097-acceptance-floor-decomposition/verbatim/stage3-consult-b.md:75)。D1320 も一 session からの一般化を禁じる [D1320:42367-42373](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-fixed-cost-decomp/docs/decisions.md:42367)。
- 成果物影響: 同一 node 内の二つの相関した観測が、checkout・node・時刻を越えた「床の内訳」としてレポートや台帳へ昇格する。
- 直し方: README と measurements に `1 PBS job / 1 hostname / real B n=2 / zero B n=2 / 当該 checkout 限定`を固定し、各走を別掲して一般値を出さない。複数 job・node へ一般化する追加実測は「裁定パッケージ候補」とする。

## B-8 — MAJOR

- 主張: top-level A+B+D+C は閉じても、B と C の補助内訳には親成分との橋渡し項がなく、D1320 の意味で加法分解になっていない。
- 根拠: `B=(L-F)-R` に対して `B_protocol=(Q-P)-R` なので差の `(F-P)+(Q-L)` が未命名である [stage2-plan.md:161-183](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2097-fixed-cost-decomp/artifacts/t2097-fixed-cost-decomp/stage2-plan.md:161)。同様に `C_worker_finish+C_controller=E-Q_all` であり、親の `C=E-L_all` との差 `Q_all-L_all` が残る [stage2-plan.md:200-215](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2097-fixed-cost-decomp/artifacts/t2097-fixed-cost-decomp/stage2-plan.md:200)。top-level closure 検査はこの子成分不一致を検出しない [stage2-plan.md:217-225](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2097-fixed-cost-decomp/artifacts/t2097-fixed-cost-decomp/stage2-plan.md:217)。
- 成果物影響: レポートの B/C 内訳行が親成分へ合計せず、それでも top-level closure が緑となって「分解済み」と台帳化される。
- 直し方: 差分の橋渡し区間にも測点付きの名前を与えて子成分を親へ閉じるか、`B_protocol` と C 補助値を非加法的な診断値と明記して内訳表から外す。

## B-9 — MINOR

- 主張: controller の interpreter/plugin 起動前後を数値化する部分は対象の pytest wall に入らず、D1384 の約 56 秒の内訳から外れる追加計測である。
- 根拠: plan は `controller_pre_session` と `controller_post_session` が A と 56 秒の外だと明記しながら測定する [stage2-plan.md:152-159](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2097-fixed-cost-decomp/artifacts/t2097-fixed-cost-decomp/stage2-plan.md:152)。D1369 の射程は pytest wall の層だけである [D1369:43624-43633](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2097-fixed-cost-decomp/docs/decisions.md:43624)。
- 成果物影響: session 外の秒数が breakdown 表や台帳へ並ぶと、56 秒の成分または短縮余地として誤って加算される。
- 直し方: brief の純増説明から interpreter/plugin を外し、E0 は時刻境界と provenance にだけ使う。pre/post 値を残す場合も「56 秒の外」と別表に隔離し、成果物の内訳合計へ入れない。

## 総括

BLOCKER 2 件。  
D1384 の三つの却下肢は直接踏んでいないが、zero selector、shard-2 単独、対象外 pre/post 計測があるため、計画全体は D1384 の枠内に収まっていない。  
本レビューは静的読取のみで、実走も repo 状態変更も行っていない。