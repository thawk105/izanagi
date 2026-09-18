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
- **閉じた。** 一次資料は `output/insights/2026-09-18/t2691-rescue-checker-timeout-grace/README.md` (実測・変異台帳・子成果物の逐語)。設計判断は {{D:rescue-checker-exit-grace}}。
- 素材: 子は自分の期限を interpreter 起動後から数え、親は Popen 後の `communicate()` から同値で数えるため、子が期限で書く `indeterminate/assessment-timeout` の JSON は親の kill に間に合わない (login node 12 走の wall − T = 0.087〜0.134 s、実 repo の親経由は 0/2)。親側に終了余裕 2.0 s (観測 max の約 15 倍) を足すだけで、期限事例 4/4 を回収した。JSON 検証述語・rc↔verdict・子予算・overall 残時間の cap は不変で、変わるのは時間内に回収できる契約準拠の報告の範囲 (D498 同型)。共有 FS 高負荷は未測定 (超えれば従来どおり `checker-timeout`)。
- 段 2 plan (codex read-only、`gpt-6-astra`、medium) が brief の P1〜P6 を検算 (子 CLI の許容は 0 超〜300 s、自己検査 test は負例へ統合)。段 3 レンズ sol (正しさ境界) real 5 / 疑い 2、レンズ luna (過剰・削除) real 6 / 疑い 2。段 4 で 19 件を裁定 — 採用 13 (brief の「Popen 前 / 必ず / 100%」を観測 2 走に限定、時間を含む受理集合の拡大を明記、正例に未証明 unit 1 件、m4 は cap を残す形、正例 T=0.5 で test 公称 4.3 s、docs 2 行)、不採用 2 (定数 comment の観測内訳削除、等価変異の削除)、scope 外 real 1 (overall 値は厳密な wall 上限でない — 既存限界、実害の観測なし、insight 記録のみ)。
- 段 5 author (Codex、13 calls、accepted) は裁定プラン v2 と完全一致の patch を書き「実装済み・未実走」(sandbox で pytest 不可)。親が実走: 実 checker の期限事例 4/4 回収 (T=1 ×2、T=4 ×2)、焦点走 127 passed / 68 s、新規 3 本 4.36 s、check_docs 違反なし。段 6 レビュー 2 本は production / test の must-fix 0 (nit 5 件中 3 件採用: 実測記録の「列挙前に期限」訂正、docs の「2 秒」重複除去、受入 wall 増分は未立証と記録)。fix 子・焦点再レビューは起動していない。
- 実走: 変異 matrix (container、dispatch、6 走 4 分 47 秒: baseline PASSED、m1〜m4 KILLED 期待 node 完全一致、等価 m5 SURVIVED、MISMATCH 0。集計は受理・打切りの kill 3 本 + 時間契約 pin m4 1 本)、受入全走 (本 commit を含む tip、結果は land の受領証)。
- 段 8: 候補 1 件 (依頼文の対象 file 名が実体と違う) は next-tasks 側の再抽出の問題で dev-wave 手順の欠落ではなく、正本を変えない (insight に記録)。
- 工数: codex 子 6 本 (plan 1、consult 2、author 1、review 2、全段 `gpt-6-astra`)。親の実測: probe 6 種、焦点走 2 回、変異 6 走。wave 開始 14:52 JST。

## 次の一手差分

### 完了

- [T-2691] 親側の終了余裕定数 `CHECKER_EXIT_GRACE_SECONDS = 2.0` と外側 timeout 1 行で、子の期限 JSON を回収できるようにした (実 repo 0/2 → 4/4、正例 1・負例 2 を変異登録、m1〜m4 KILLED)。
  remaining: none
  base: cb56598d78ee75724ce977b0d66976d02624202f12e7b917b181e8efbc9e45ad
