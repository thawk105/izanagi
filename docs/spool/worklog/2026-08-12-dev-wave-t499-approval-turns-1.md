---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-12
wave: dev-wave-t499-approval-turns
seq: 1
title: 委任された凍結・承認手番 (A)(B) は承認対象が未生成で実施できないと実測した — 親の実施不能根拠 2 件は誤りで撤回 (docs のみ、branch worktree-dev-wave-t499-approval-turns)
---

## 本文

- 第 5 束 (authority: user、2026-08-12) が AI へ委任した [T-499] の凍結・承認手番 (A)(B) の
  実施を試み、**どちらも承認対象の artifact が未生成で実行できない**ことを実測した。
  手番の確定リストは (A) を「未承認のあいだ機構全体が fail-closed で止まっており、これを
  解除する」と書いていたが、実態は「通すべき対象がまだ無い」であり、止まっているのは正しい状態。
- **実施不能の決め手** — (A) reviewed bytes と、その内容である研究設計値 (`n` / master seed /
  block size / campaign ID 等) が未確定のまま `APPROVED_SPEC_SHA256 = None`。
  (B) budget pin / production official floor result / canonical generation record の**三者不在**。
  v2 candidate producer 自体は実在するが、その入力が揃っていない。
- **親が段 1 で挙げた実施不能の根拠 2 件は、段 3 の検証で誤りと判明したため撤回した。**
  - 「AI は承認 commit を作れない」 — `_assert_user_commit` が検査するのは非 merge・逐語
    `AI-Agent: none`・祖先性であって、内容を誰が選んだかではない。ユーザーが exact bytes を
    確定した後の機械的な Git 代行なら `AI-Agent: none` は正当に成立する。
    使えないのは exact bytes が無く、AI が承認判断をすれば実質的関与になるからにすぎない。
  - 「(B) は D328 と衝突する」 — D328 は正しさゲートと admission を明示的に対象外としており、
    承認連鎖の構造検証はそこに入る。さらに freeze-chain-hold-sweep wave の敵対相談が
    [T-499] A/B を保留の**明示的 keep 集合**へ入れるよう要求していた。
    **(A)(B) の fail-closed は緩めずに保つべき正しさ境界**であり、保留の対象ではない。
- 実施不能の判定自体は 4 系統 (段 2 プラン子・段 3 レンズ A/B・親の一次資料検算) が独立に一致した。
  レンズ A は全 126 ref・dangling commit・全 worktree・dev-wave job 保存域まで探索し、
  reviewed spec / v2 世代 / budget approval の**いずれも存在しない**ことを確認している。
- **セッション異常 1 件 (親の prompt 不備)**: 段 2 プラン子が `check_codex_output` rc=1 で
  不受理になった。NFC 由来の事故を避けるつもりで prompt に「ASCII のみ」と書いたところ、
  子が字義どおり守って見出しまで `## Soukatsu` とローマ字化し、必須の `^## 総括` に当たらなかった。
  子の作業自体は健全 (573 秒、8,805 bytes、codex_exit_code=0) だったため、再投入せず
  **親が全所見を一次資料で検算して採用**した (子出力は根拠に使っていない)。
  正しい指示は「NFC 正規形で書く」であって ASCII 強制ではない。
- **副産物として確定した設計事実** — 機構は「世代は AI が作ってよい / 承認は人間だけ」を
  C1-6 として対で機械強制している (世代導入 commit G は非 none の `AI-Agent` trailer 必須、
  `AI-Agent: none` なら「AI 生成物の provenance 虚偽」として拒否)。また D302 により
  **hash 記入だけを「承認完了」とは書けない** (hash は識別子にすぎず承認は内容の再導出を伴う)。
- **裁定へ返した項 2 件** (控え = repo 外 inbox `2026-08-12-t499-approval-turns-blocked.md`)。
  Q1 = (A) の進め方。親推奨 = 事前登録が固まるまで待ち、producer と schema 再発行の設計を先行。
  Q2 = (B) の進め方。親推奨 = 前提 2 つ ([T-088] official guard 解禁・budget 数値の承認) を
  先行タスクとして起票し、揃った後に AI が機械準備を担う (承認判断はユーザー)。
- 逐語と工数は `output/insights/2026-08-12_t499-approval-turns/`。実装面 diff はゼロのため
  変異 matrix は `DW-S04` の免除 (「実装しない」裁定済みかつ実装差分ゼロ) に該当する。
- **受入の扱いと証拠**: 判定手順 = `git show --stat HEAD` の変更 path が
  `docs/spool/worklog/` と `output/insights/` の 8 file だけで実装面ゼロであることを確認した。
  これらを読む実 repo テストとして `orchestrator/tests/test_spool_fold.py` と
  `orchestrator/tests/test_check_docs.py` が実在するため**免除せず実走**し、
  568 passed / rc=0 を得た。あわせて `tools/spool_fold.py --dry-run` が `status=planned`、
  `tools/check_docs.py` rc=0、`tools/check_ai_provenance.py` が 2,978 件・新規違反なし。
- **段 8 (自己改善) の裁定 2 件** — どちらも本文編集は行わない。
  - 候補 1 (親 prompt の「ASCII のみ」指示が子の見出しをローマ字化し validator を不受理にする):
    恒久対応は既に機械化されており (`tools/check_codex_output.py` が実際に止めた)、
    残るのは親の prompt 作法だけなので新規 F を作らず本エントリの記録に留める (F43 の段 8 裁定と同型)。
  - 候補 2 (`dev_wave_codex.py` が `--artifact-root/<wave>/<job-id>` を作らないため親が
    `--dry-run` から job-id を読んで mkdir する必要がある): t316-r2-oracle wave と本 wave で
    **独立 2 例目**を実測したが、`DW-O01` への 1 行追記は L1.5 unique footprint が
    9,686 > 9,566 bytes で予算超過となり**見送った** (実測。予算値を上げる変更は自己改善に含めない)。

## 次の一手差分

### 更新

- [T-499] **P1・ユーザー裁定待ち**: 委任された凍結・承認手番 (A)(B) は承認対象が未生成で
  実施できないと実測した。Q1 (A の進め方) / Q2 (B の進め方) を裁定へ返している。
  親が挙げた実施不能根拠のうち「AI は承認 commit を作れない」「D328 と衝突する」の 2 件は
  誤りとして撤回済み。残余 (退役後も無変化の約 400 件) の進め方は別途裁定待ち。
  base: 494a3d55b37a370c2f18942fac98a7603aa727a481fc8eb72fd983d6c84f43da
- [T-782] **P1・ユーザー裁定待ち**: 承認 SHA 記入の手番は、reviewed spec の bytes と
  その内容である研究設計値が未確定のため実行できない。canonical path も production の
  生成経路も無く、設置は D302 の schema 据え置き前提に触れる。Q1 の裁定待ち。
  base: f6f3c3c84bbe81fb9885d865c7bf59d42ef592a2c16bfe5b3496cd6ac7291a6e
- [T-750] **P2・ユーザー裁定待ち**: 実凍結手番の 3 手 (candidate spec の内容確認 →
  canonical path への設置 → 定数への hash 記入) は、第 1 手の対象である candidate spec が
  存在しないため着手できない。Q1 の裁定待ち。
  base: 46c4d725e620262fc742524cf4c53d348e764a0ed4ee24a8fc7dc8daaaac6c5a
- [T-607] **P1・ユーザー裁定待ち**: freeze v2 の approval / active pointer 設置は、
  budget pin / production official floor result / canonical generation record の三者不在で
  実行できない。律速は承認手番ではなく前提側。Q2 の裁定待ち。
  base: cb78a01182b5ab5981a97fc714e5f6258cfa301a8167fe68480a96ac1cb0acee
