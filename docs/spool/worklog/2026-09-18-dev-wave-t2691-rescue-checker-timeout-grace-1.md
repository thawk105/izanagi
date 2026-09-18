---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-18
wave: dev-wave-t2691-rescue-checker-timeout-grace
seq: 1
title: [T-2691] rescue の landed checker 待機に終了余裕定数 1 つを足し、子の期限 JSON (assessment-timeout) を親が回収できるようにした — 実 repo の期限事例で 0/2 → 4/4 (コード + テスト + docs、branch worktree-dev-wave-t2691-rescue-checker-timeout-grace、変異 matrix = baseline PASSED・4/4 KILLED 期待 node 完全一致 (うち m4 は時間契約 pin)・等価 m5 SURVIVED・MISMATCH 0)
---

## 本文

- ユーザー依頼 [T-2691] (P2、entry 1542 起票): `check_branch_rescue.py` の rescue で子 process の deadline と外側 subprocess timeout が同値のため、子の理由 JSON より先に親が kill しうる欠陥を、定数 1 つの最小差で直し、正例・負例を変異登録する。Codex author (D95)。[T-2686] は同梱しない。
- 対象 file の訂正 (裁定を覆さない新事実): 依頼文の「`audit_dangling_commits.py` の rescue」は起票の要約ずれで、実体は `tools/check_branch_rescue.py::_landed_assessment` ↔ 子 `tools/check_branch_landed.py`。`_audit()` の子は deadline 引数を持たず理由 JSON も出さない。
- **実装・変異検査の成果を回収した。** 一次資料は `output/insights/2026-09-18/t2691-rescue-checker-timeout-grace/README.md` (実測・変異台帳・子成果物の逐語)。設計判断は {{D:rescue-checker-exit-grace}}。
- 素材: 子は自分の期限を interpreter 起動後から数え、親は Popen 後の `communicate()` から同値で数えるため、子が期限で書く `indeterminate/assessment-timeout` の JSON は観測2走で親の kill に間に合わなかった (login node 12 走の wall − T = 0.087〜0.134 s、実 repo の親経由は 0/2)。親側に終了余裕 2.0 s (観測 max の約 15 倍) を足すだけで、期限事例 4/4 を回収した。両者は異なるcheckoutの観測で同条件の対照ではない。JSON 検証述語・rc↔verdict・子予算・overall 残時間の cap は不変で、変わるのは時間内に回収できる契約準拠の報告の範囲 (D498 同型)。共有 FS 高負荷は未測定 (超えれば従来どおり `checker-timeout`)。
- 段 2 plan (codex read-only、`gpt-6-astra`、medium) が brief の P1〜P6 を検算 (子 CLI の許容は 0 超〜300 s、自己検査 test は負例へ統合)。段 3 レンズ sol (正しさ境界) real 5 / 疑い 2、レンズ luna (過剰・削除) real 6 / 疑い 2。段 4 で 19 件を裁定 — 採用 13 (brief の「Popen 前 / 必ず / 100%」を観測 2 走に限定、時間を含む受理集合の拡大を明記、正例に未証明 unit 1 件、m4 は cap を残す形、正例 T=0.5 で test 公称 4.3 s、docs 2 行)、不採用 2 (定数 comment の観測内訳削除、等価変異の削除)、scope 外 real 1 (overall 値は厳密な wall 上限でない — 既存限界、実害の観測なし、insight 記録のみ)。
- 段 5 author (Codex、13 calls、accepted) は裁定プラン v2 と完全一致の patch を書き「実装済み・未実走」(sandbox で pytest 不可)。親が実走: 実 checker の期限事例 4/4 回収 (T=1 ×2、T=4 ×2)、焦点走 127 passed / 68 s、新規 3 本 4.36 s、check_docs 違反なし。段 6 レビュー 2 本は production / test の must-fix 0 (nit 5 件中 3 件採用: 実測記録の「列挙前に期限」訂正、docs の「2 秒」重複除去、受入 wall 増分は未立証と記録)。fix 子・焦点再レビューは起動していない。
- 実走: 変異 matrix (container、dispatch、baselineと変異の計6走。4分47秒はqueue等を含む外側wallで、pytest所要ではない: baseline PASSED、m1〜m4 KILLED 期待 node 完全一致、等価 m5 SURVIVED、MISMATCH 0。集計は受理・打切りの kill 3 本 + 時間契約 pin m4 1 本)。旧waveの受入全走は未実施で、旧結果から完了とは判定しない。回収waveの最終受入は記録後に実施し、child-greenの受領証をlandの必須入力とする。
- 段 8: 候補 1 件 (依頼文の対象 file 名が実体と違う) は next-tasks 側の再抽出の問題で dev-wave 手順の欠落ではなく、正本を変えない (insight に記録)。
- 回収監査: 着手時main `b2037abfa` から専用branch `codex-dev-wave-t2691-recovery` を作成し、旧親 `8647973a2` と同一実装のauthor終端 `0d98d9701` を通常mergeで保全。旧review2本・matrixを回収し、独立read-onlyレビュー1本で実装must-fix 0、記録訂正3件を確認した。観測2走の一般化、未実施受入の実走扱い、dispatch外側wallの誤読を訂正。旧親の待機processは終了確認済み、mutation dispatch生ログをrepo外へ退避した。
- 回収後の焦点走: 統合commit `61be923f4` のrescue・ledger・check_docs consumerは706 passed / 3 skipped、pytest所要12.90秒（計算job6362）。check_codex_agents・check_docs・spool dry-run rc0。全史provenanceは新規違反なし（既知違反の記録は保持）。phaseにT-2691の未了checkboxは存在せず、本fragmentでT-2691を終端する。回収記録と受入の一次資料は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2691-recovery/`。
- 工数: codex 子 6 本 (plan 1、consult 2、author 1、review 2、全段 `gpt-6-astra`)。親の実測: probe 6 種、焦点走 2 回、変異 6 走。wave 開始 14:52 JST。
- 回収時の受入中断: 初回は未起動shardのqueue待ち900秒超過で中断し、兄弟jobの自然終了・clean/HEAD確認後にholdを解除した。互換holdの解除確認漏れによる投入前拒否1回も記録に残した。queue待ちだけを既存設定で3600秒にして再投入し、2分割は10373 passed/8 skippedと10805 passed/8 skipped。最後の分割ではT1259の未変更module fixtureのgit status/ls-filesが30秒timeout（22 setup errors）、S1の読取ではccbench lock期限によるxdist internal errorが発生し、成功受領証は発行されなかった。
- 上記赤はスタックと実差分で裁定した。該当probe/test/conftestは着手時mainから差分ゼロでrescue呼出しが無く、assert本体にも未到達。規定の単独再走1回（T1259 file全体とS1 crashitem）は同じ実装tip `7aa7bcd0e` で52 passed/15.41秒、再現しなかった。除外・期待値変更・hold登録をせず、受入の再走1回へ進む。最終判定はその受領証による。初回からのログと裁定は専用handoffへ保持する。
- その受入は統合tip `0a12e0f89` で25136 passed/69 skipped、child-greenに達したが、landのfold検査が親のauthor直合流commit `4f10b9e6d` を拒否してmainをrollbackした。原因は古いauthor親とのtree比較に `docs/spool/FOLDED.md` の差が現れた統合順であり、実装の赤ではない。authorと旧親を同じmain `d62518621` へそれぞれ先に揃えてから合流する履歴へ組み直し、gate・台帳検査・実装内容は変更しない。旧greenの事実は保持し、組み直したtipへの受領証を改めて取得する。拒否された回収branchはforensic保全のため残す。

## 次の一手差分

### 完了

- [T-2691] 親側の終了余裕定数 `CHECKER_EXIT_GRACE_SECONDS = 2.0` と外側 timeout 1 行で、子の期限 JSON を回収できるようにした (実 repo 0/2 → 4/4、正例 1・負例 2 を変異登録、m1〜m4 KILLED)。
  remaining: none
  base: cb56598d78ee75724ce977b0d66976d02624202f12e7b917b181e8efbc9e45ad
