単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier

必読事項の射影: (下記をすべて読む。読めなければ即停止し、読めなかった path を報告する)

- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/verbatim/stage1-brief.md — 親 brief (P1〜P7、攻撃対象)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/codex/s2-plan-r2.md — 段 2 のプラン (攻撃対象)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/verbatim/request.md — 依頼の逐語。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/verbatim/d2194-item3.md — 本 wave の裁定の逐語。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/verbatim/d2120-item5.md — D2120 項 5 の逐語。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/verbatim/insight-t2632-s7.md — 一次資料 §7。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/verbatim/insight-t2632-s2.2-2.3.md — 一次資料 §2.2 / §2.3。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/verbatim/prereg-s5.1.1-reference.md — 凍結事前登録 §5.1.1 共通参照点 (逐語)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/campaign/p3_s4_loop.py — 読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/campaign/p3_s4_loop_trigger_gating.py — 先例。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/campaign/p3_b4_prerun_caller.py — 読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/campaign/artifact_admission.py — trigger provenance の admission 検査 (先例、本 wave は base へ広げない)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/tests/test_p3_s4_loop.py — 読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/tests/test_p3_b4_prerun_caller.py — 読めなければ即停止

## レンズ B: 過剰・削除・scope と研究前進

プランを守らせず検査する。**親 brief 自身も検査対象**である。依頼と D2194 項 3 が求める 4 項に対し、足りないもの・余計なもの・
削れるもの・局所修正で足りるものを探す。攻撃面に `docs/failures.md` の型タグ [手順漏れ] [誤前提] [権限逸脱] [consumer 取り残し]
[防壁の射程誤認] を含める。次を必ず検査し、各項目を real (欠陥あり) / refuted (欠陥なし) で判定して根拠 (file:line・裁定の逐語) を示す。

1. **4 項の被覆:** プランは (1) side channel、(2) 参照点の定義の確定、(3) 順序、(4) caller の codec 経由化のすべてを、依頼と裁定の
   literal どおりに実装・記録するか。とくに (2) を「記録 + docstring で確定、resolver を作らない」(brief P1) とする読みは、
   裁定の「新 object・新 producer は作らない」と、一次資料 §4.3 の「定義後に carrier (辺 A と同じ side channel に `reference` 欄を
   持たせるのが自然) が要る」のどちらに沿うか。reference 欄を side channel に持たせないと (2) の定義が次 wave で実装不能になるか、
   それとも D2194 項 3 (1) の 6 field 列挙が reference 欄を排除しているか。
2. **過剰:** プランに scope 外 (gate・台帳・一般化・admission 検査・sort / trigger への展開・新 schema version 管理・resolver・
   互換層) が混ざっていないか。先例 trigger driver の header (INFORMATION_SOURCES / GATE_RECORD / firewall 文言) を base に写す必要は
   あるか (base の記録義務にない情報源記録を持ち込んでいないか)。test が必要以上に多い / 重複していないか。
3. **依頼文と裁定の食い違い (brief P7):** 依頼は先例を `_write_source_preimage_artifact` と名指し、裁定は `reports/<driver>_provenance.json`
   を名指す。親の読み (file の意味は `_append_provenance_entry` 系、書き込みの堅さは `_write_source_preimage_artifact` 系、source
   preimage artifact は足さない) は妥当か。別の読み (base にも source preimage artifact を書く) を採るべき根拠はあるか。
4. **研究前進の実効性:** 本 wave の成果で、新規 base campaign から赤 precursor が出たとき、D2100 の 12 field のうちどれが「出所あり」に
   変わり、どれが不足のまま残るか。caller (p3_b4_prerun_caller) は side channel を読まないので、本 wave 後も `_MISSING_SOURCES` の
   報告は 12 件のまま変わらないはずだが、それは依頼の scope と整合するか (caller に side channel を読ませるのは scope 外か)。
   「完了判定」(brief 冒頭) が本 wave だけで達成可能な形になっているか。
5. **局所修正の可否:** caller の修正は `trial` の取り出しだけで足りるか (`lock` の他 field を読む箇所は無いか)。codec の例外を
   既存 `CampaignInputUnreadable` へ写す最小形になっているか。test fixture の v2 化は既存 test の意図 (unreadable の各分岐) を
   保つか、削った分岐はないか。
6. **削除・非接触:** 既存 test・既存 fixture・既存 docstring で、プランが削る / 書き換えるものは必要最小か。凍結事前登録・whiteboard
   型・sort / trigger driver に触れていないか。

## 制約

- sandbox は read-only で書込可能な tmp が無い。**静的検査だけでよい。** テスト実走は親が行う。実走していないことを「確認した」と書かない。
- 新しい gate・検査・台帳を提案する場合は、依頼の scope 外であることを明記し、裁定パッケージ候補として分けて返す。
- 予算が尽きそうなら、途中までの結論を下記の出力形式どおりに書いて終える。

## 出力形式

項目 1〜6 を見出しで分け、各項目に判定 (real / refuted) と根拠を書く。real には must-fix / should-fix / nit の別と、放置時に成果物
(B-4 の適格行・参照点・台帳・certified 判定) がどう変わるかを 1 行で添える。最後に `## 総括` を置く。
