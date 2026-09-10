## 所見

1. **対象:** 設計案 §2・§5・§6 の file:line  
   **主張:** 複数のアンカーが実在はするが意味を誤っている。`p3_autonomous_workload_trial.py:133` は `MAX_GENERATIONS = 10` で、承認上限は `:134`、CLI 既定値は `:1720`。`layer3_report.py:390` は lock の読込みで、`search_config` の検査・消費は `:416-418`, `:434-435`, `:459`。`p3_autonomous_workload_trial.py:503` は関数定義で、budget 挿入は `:510-518`。さらに [test_autonomous_trial_completeness.py:808](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/tests/test_autonomous_trial_completeness.py:808) は「定数 monkeypatch で多世代を通すテスト」ではなく、上限超過を拒否する負例である。  
   **根拠:** [p3_autonomous_workload_trial.py:133](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/p3_autonomous_workload_trial.py:133)、[layer3_report.py:390](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/layer3_report.py:390)、[s2-draft.md:176](/work/1/SFC/tanab/dev-wave-jobs/t434-cap-lift-receipt/s2-draft.md:176)。  
   **提案修正:** アンカーを実際の消費行へ直す。`:808` の負例は receipt 不在時の拒否として維持し、valid receipt fixture は真の多世代到達テスト (`test_p3...:644`, `:830`、completeness の `:843`) に付ける。  
   **確度:** high

2. **対象:** brief provisional (Q1)(Q2)  
   **主張:** 「機械 gate ではない」「受理集合を広げない」は、将来実装について同時には成立しない。現状 cap=1 との比較では valid receipt による多世代受理は集合を広げる。一方、裸の定数引上げとの比較では receipt 必須化が集合を狭める。設計案自身もこの二方向を認めている。  
   **根拠:** [brief.md:23](/work/1/SFC/tanab/dev-wave-jobs/t434-cap-lift-receipt/brief.md:23)、[s2-draft.md:174](/work/1/SFC/tanab/dev-wave-jobs/t434-cap-lift-receipt/s2-draft.md:174)、[s2-draft.md:178](/work/1/SFC/tanab/dev-wave-jobs/t434-cap-lift-receipt/s2-draft.md:178)、D96。  
   **提案修正:** Q1 を「本 wave は人間承認 record の設計だけ。後続の独立 wave が機械 admission へ結線する」と時相分離する。Q2 は「現状比では valid-receipt 集合を広げ、裸の cap-lift 比では狭める」と基準集合を明記する。  
   **確度:** high

3. **対象:** 設計案 §「事前登録文書」・択一 7  
   **主張:** 8c 事前登録面の対象文書を取り違えている。正本は `docs/phase3-8c-preregistration.md` であり、`docs/phase3-main-experiment.md` は S-1 の旧主実験・critic ablation 文書である。後者の再生成・repin は無関係な S-1 proof chain を変更する。  
   **根拠:** [phase3-8c-preregistration.md:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/docs/phase3-8c-preregistration.md:1)、同 `:69-72`、D116 決定 (1)、D121 `:5856-5861`、D150 `:7459`、[known_axes_freeze.json:623](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/output/s1-freeze/known_axes_freeze.json:623)。  
   **提案修正:** 事前登録面を `docs/phase3-8c-preregistration.md` に差し替える。`docs/phase3-main-experiment.md` と S-1 freeze は明示的 no-touch とし、「S-1 freeze 再生成・repin」を実装 handoff から削除する。  
   **確度:** high

4. **対象:** 設計案 `:115`, `:148`, `:223`／T-435 境界  
   **主張:** cap-lift 実装 wave に再事前登録を同梱し、T-435 の所有物を先取りしている。T-435 は「次の 8c 実走直前に generation 予算条項をまとめて改訂」を独立に所有する。  
   **根拠:** [worklog.md:1557](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/docs/worklog.md:1557)、同 `:1562-1564`、[s2-draft.md:115](/work/1/SFC/tanab/dev-wave-jobs/t434-cap-lift-receipt/s2-draft.md:115)。  
   **提案修正:** T-434 は T-435 への要求事項だけを渡す。順序を「T-435 の再事前登録 commit → その子孫で cap-lift candidate G → 人間 receipt commit A」と依存関係として裁定へ返し、T-434 実装 wave が文書改訂を所有しない。  
   **確度:** high

5. **対象:** brief (Q3)、設計案 §P6 の受理写像  
   **主張:** T-433 と独立という前提は成立していない。T-433 は「実装済み」の意味的充足契約と `NOT_CLAIMED` の global/per-run 射程を所有する。現案は revision 全体に単一 P6 status を置くため、per-run gate 裁定なら構成 identity を表現できない。また既存 P6 結果は reason code 付きなのに、schema は単なる enum へ縮約している。  
   **根拠:** [worklog.md:1552](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/docs/worklog.md:1552)、D150 `:7418-7445`、[P6 contract:127](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/output/insights/2026-08-03_t244-p6-contract/README.md:127)、[s2-draft.md:55](/work/1/SFC/tanab/dev-wave-jobs/t434-cap-lift-receipt/s2-draft.md:55)。  
   **提案修正:** P6 部分を provisional/opaque と明記し、T-433/V1 裁定後に schema version を確定する。少なくとも「同じ union のまま使える」という `:72` の断言を削除する。  
   **確度:** high

6. **対象:** 設計案の D96 手続・実装 wave handoff  
   **主張:** 「新 D」を置くだけでは不足する。D114 決定 (1) は解除手続きを「定数 1 個と境界テストの同時変更だけ」と明記しており、receipt/witness/consumer を新たな必要条件にするなら、この文を明示的に supersede する必要がある。  
   **根拠:** D114 `:5331-5334`、D96、[s2-draft.md:178](/work/1/SFC/tanab/dev-wave-jobs/t434-cap-lift-receipt/s2-draft.md:178)。  
   **提案修正:** 後続新 D の必須内容に、D114 決定 (1) の逐語アンカーと置換後の遷移契約を追加する。CLI literal default 1、環境変数・隠し flag・provider 例外禁止は維持する。  
   **確度:** high

7. **対象:** brief の「3 入口 gate」一般化、設計案 §producer  
   **主張:** 3 入口という実測数は正しいが、実際の cross-generation／反復経路の閉集合ではない。D114 は `drive/providers/preview` 注入、直接 `drive_iteration()`、並行 race を保証外と明記している。receipt を `generations > 1` だけに結線してもこの一般化は閉じない。  
   **根拠:** D114 `:5390-5398`、[p3_autonomous_workload_trial.py:1538](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/p3_autonomous_workload_trial.py:1538)、[runbook:108](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/docs/phase3-s8c-autonomous-trial-runbook.md:108)。  
   **提案修正:** 保証を「`generations` 引数の 3 入口」に限定し、D114 carve-out を逐語維持する。注入 seam の閉鎖は P5/T-433 側の独立 wave に残し、T-434 で第 7 面として増やさない。  
   **確度:** high

8. **対象:** 「実装 wave に送る事項」全体  
   **主張:** DW-G04 を満たす既存 artifact path／計測 ID がない。提案中の `output/cap-lift/...` は将来作る path であり、既存発火 artifact ではない。したがって「そのまま実装 wave に着手可能」という形にはできない。  
   **根拠:** [DW-G04](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/docs/dev-wave/core.md:57)、D150 `:7446-7456`、[brief.md:18](/work/1/SFC/tanab/dev-wave-jobs/t434-cap-lift-receipt/brief.md:18)、[s2-draft.md:105](/work/1/SFC/tanab/dev-wave-jobs/t434-cap-lift-receipt/s2-draft.md:105)。  
   **提案修正:** handoff を「実装待ち」ではなく「blocked design memo」とする。再開条件に、実在する cap-lift 申請 artifact path または計測 ID、T-433/T-435 の land、必要前提の充足を列挙する。  
   **確度:** high

9. **対象:** journal / report / Layer 3 の detached projection  
   **主張:** 同一 payload の exact schema が未定義である。`run-start.cap_lift_receipt` は「body + receipt_sha256」、report は同名 top-level projection、campaign identity は SHA のみ、Layer 3 は再び detached receipt と記述され、どこまでが同一 bytes か不明である。D75 型の同名二義化を残す。  
   **根拠:** [s2-draft.md:153](/work/1/SFC/tanab/dev-wave-jobs/t434-cap-lift-receipt/s2-draft.md:153)、同 `:160`, `:167`、[layer3_schema.json:5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/layer3_schema.json:5)。  
   **提案修正:** 例えば `{receipt_raw_sha256, receipt}` の exact envelope を一度だけ定義し、journal/report/Layer3 が同じ canonical bytes を持つか、SHA のみを持つかを面ごとに固定する。raw receipt、projection、witness hash の名称も分離する。  
   **確度:** high

10. **対象:** Layer 3 v4 handoff  
    **主張:** 「v2/v3 を読み続ける」は現行実装へ直接落とせない。現コードは current=v3 と legacy=v2 の一分岐しかなく、単純に current を v4 へ上げると v3 artifact が schema v4 で検査されて拒否される。  
    **根拠:** [layer3_report.py:39](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/layer3_report.py:39)、同 `:190-200`、[s2-draft.md:168](/work/1/SFC/tanab/dev-wave-jobs/t434-cap-lift-receipt/s2-draft.md:168)。  
    **提案修正:** v2・v3 の明示的 legacy schema 分岐、v4 generator、三版の正負 reader test を handoff に列挙する。  
    **確度:** high

11. **対象:** receipt の固定 path と Layer 3 renderer  
    **主張:** renderer が receipt をどの trust root から読むか未定義である。8c build では `output_root=output/exploration` が渡されるため、それを基準に `cap-lift` を導出すると提案した global `output/cap-lift` ではなく `output/exploration/cap-lift` を指す。  
    **根拠:** [p3_autonomous_workload_trial.py:1040](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/p3_autonomous_workload_trial.py:1040)、[layer3_report.py:322](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/layer3_report.py:322)、[s2-draft.md:107](/work/1/SFC/tanab/dev-wave-jobs/t434-cap-lift-receipt/s2-draft.md:107)。  
    **提案修正:** campaign `output_root` と cap-lift trust root を別引数・別定数として定義し、production では repository root に固定する。caller 注入可能な任意 root を authority にしない。  
    **確度:** med

12. **対象:** witness manifest §4  
    **主張:** 「少なくとも」の箇条書きは strict schema ではなく、独立 wave がそのまま実装できない。P1/P2/P3/P5/P7 は検査対象の閉集合が未定義で、D150 も cap-lift の実 field は 0 件とする。存在しない評価器・artifact path を source closure に置く案は DW-O13 を満たさない。  
    **根拠:** [s2-draft.md:74](/work/1/SFC/tanab/dev-wave-jobs/t434-cap-lift-receipt/s2-draft.md:74)、D121 `:5842-5850`、D150 `:7446-7448`、DW-O13。  
    **提案修正:** T-434 では witness hash の receipt field だけ確定し、manifest v1 は実 artifact path が揃うまで未確定とする。実装可能と称するなら exact key/type/path/evaluator identity を全 P について列挙する。  
    **確度:** high

13. **対象:** `revocations/` と失効 gate  
    **主張:** revocation tombstone は裁定された 6 面にない追加 policy であり、保存済み report の受理を後から狭める新しい機械判断を導入する。schema、承認 authority、D96 手続、境界テストの変更単位が未定義で、盛らない規律に反する可能性が高い。  
    **根拠:** [s2-draft.md:109](/work/1/SFC/tanab/dev-wave-jobs/t434-cap-lift-receipt/s2-draft.md:109)、同 `:126-131`、[worklog.md:1557](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/docs/worklog.md:1557)。  
    **提案修正:** v1 から削除するか、必要性・authority・D96 適用を別の裁定パッケージ／独立 wave に送る。  
    **確度:** med

## 攻撃したが見つからず

- 現行コードにおける承認上限の **3 入口** (`CLI` / `run_trial` / `_run_workload`) と **2 consumer gate** (`run-envelope` / `campaign-chain`) の個数自体は実在する。
- 設計案には裁定が指定した 6 面の見出しがすべてある。欠落は見出し数ではなく、事前登録面の対象文書と実装粒度にある。
- P4 を無条件義務として扱い、P6 の `NOT_IMPLEMENTED` / `NOT_CLAIMED` と 4 値結果を別語彙に保つ点は D150 と整合する。
- D150 決定 (2-b) の遷移契約、D96 の「新 D + 境界テスト同時更新」、現 wave で cap・凍結 bytes・proof chain を変えない境界は明記されている。
- 本レビューは静的検査のみで、pytest・build・ファイル編集は行っていない。

## 総括

現案は 6 面を形式上列挙しているが、8c 事前登録と S-1 凍結文書を取り違え、T-433/T-435 の所有物を先取りしている。  
また、将来の受理集合を「狭めるだけ」とする brief 前提は成立せず、D114 の解除契約を明示 supersede する新 D が必要である。  
DW-G04 の実在 artifact がないため、現時点では実装 wave へ直送せず、blocked design memo として返すべきである。  
最優先修正は、事前登録面の差替え、P6 schema の provisional 化、D114/D96 遷移契約、detached projection の exact 化である。