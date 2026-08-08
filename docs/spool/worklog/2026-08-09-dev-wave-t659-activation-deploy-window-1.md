---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-09
wave: dev-wave-t659-activation-deploy-window
seq: 1
title: activation 発行→配備の分裂窓 ([T-659]) の設計択一を裁定へ返した — 実装はしていない (docs のみ、実装差分なし、branch worktree-dev-wave-t659-activation-deploy-window)
---

## 本文

- **ユーザー指示に基づく設計 wave** (「最小形とし、本番コードは編集しない、実装は [T-657] の
  land 後の次弾」)。**実装差分ゼロ**で終端し、段 5・6 を飛ばして `4→7→8→9` を通った
  (`DW-S04` の「実装しない」裁定)。変異 matrix は同条項で免除。裁定パッケージと逐語は
  `output/insights/2026-08-09_t659-activation-deploy-window/`。
- **段 3 の敵対 2 レンズはいずれも NO-GO** (レンズ A = sol / must-fix 8 + nit 1、
  レンズ B = luna / must-fix 9 + nit 1)。
- **親は段 2 プランの推奨を採らなかった。** プランは「record と head 定数が同一 commit に
  入ったことを land 前に機械検査する gate」(概算 300〜500 行) を推奨したが、これが変えるのは
  **land 可能な Git 履歴の集合だけ**で、certified 選択・レポート・試行台帳のどの値も
  受理集合も変えない (`DW-G05`)。runtime は分裂の両方向を既に fail-closed で拒否している。
  研究最優先 (D205) に照らし、**推奨を「機構を作らず手順で担う」へ差し替えた**。
- **親自身の当初案も取り下げた。** 「発行 tool に head 定数まで書かせる」案は、レンズ A が
  確度 high で「発行が commit 前の有効化になり、承認された head という信頼の根が発行者の
  選択に置き換わる」と指摘した。**選択肢から落とすことを推奨に含めた。**
- **親の記述を 4 件訂正した。** (i) 窓は 2 つでなく 3 段の壁 (発行ツリー内 / 配備 /
  旧世代の掃け残り)。(ii) 「record と head はどちらも git tracked」は誤り —
  `git ls-files` で確認したところ追跡下にあるのは `00000001.json` の 1 件だけで、
  **発行直後の record は untracked**。`git commit -a` が record を落とし、素の `stash` が
  分裂を作る一方、中断からの復帰は untracked 削除で足りる。(iii) 「receipt の serial で
  混在を追える」は誤り — durable には `contract_sha256` しか載らず、据置 env は新旧の
  activation を区別できない (D245 が据置を許すため)。段 1 で書いた `evidence_contract_sha256`
  は段 8c の evidence 文書 hash で、環境世代の識別子ですらなかった。(iv) probe が実測したのは
  leaf の検証関数の範囲までで、production の読み込み経路 (cache・fork・root 解決・較正検証) は
  通していない。
- **親が範囲を訂正した段 3 所見 1 件。** レンズ B は「runbook への追記が `docs/dev-wave` の
  byte 予算を超える」としたが、`docs/pegasus-runbook.md` に `tools/check_docs.py` の byte 上限は
  存在しない (`PROVENANCE_REFERENCE_LIMITS` は provenance 2 文書のみ)。**予算超過の懸念は
  当たらず、節境界を切らずに §7.3 へ混ぜると受入 lease と activation 窓が同じ契約に見える、
  という指摘だけが real。**
- **並行 wave の発見で設問が 1 つ解けた。** 段 2 走行中に
  `dev-wave-t657-t660-g2-activation` が [T-657] の実活性化を手動の同一 commit 手順で実装中と
  判明したため、順序の論点は「serial 2 は手動で先行、本設計は serial ≥ 3 が対象」に確定し、
  brief へ追補 2 として入れた。現在の登録は linux-baremetal g1 と pegasus g1/g2 だけで、
  **今の材料では serial 3 を発行できない** (未登録世代と全 env 据置の no-op はどちらも拒否)。
- **`DW-O13` の読了期限を 1 回超過し、段 2 を巻き戻した。** 設計案が gate 新設を含みうると
  気づいたのが段 2 投入後だったため、入口規則どおり producer を停止して成果物を
  invalidate し、gate 入力の実在義務を組み込んだ prompt で再投した。
- **段 2 子を 1 本喪失した。** `.done` を書かず process group ごと消滅 (wrapper の echo すら
  未実行)。login ノードの user cgroup OOM kill が有力だが `dmesg` 権限がなく確定できない
  (当時 codex 10 本 + claude 11 本が並走)。3 本目で完走した。
- **背景 task の完了通知が捏造される事象を独立 10 例以上実測した。** process 生存中に
  「完了 rc=0」が届き、通知の Output 行は script の成功時 echo をなぞった文字列で、実 output
  ファイルは空か不存在だった。非 persistent task は偽完了で待ち手ごと閉じられる。
  `DW-O01` の「完了通知を判定にしない」に従い、**成果物の実在・`.done` の exit code・
  producer process の死の 3 点照合**だけで判定した。
- **段 8 の改善候補は 1 件、本文編集なしで記録のみとした。** 「`DW-O13` の発火条件は設計 wave
  でも成立する (実装ゼロでも裁定パッケージが gate 案を含む時点)」を入口へ足す案だが、
  (i) 実測は本 wave の 1 例だけで `DW-G03` の独立 2 例に届かず、(ii) [T-661] の裁定
  「本文編集せず台帳記録で担う」がそのまま当てはまる。既存規則の読み落としであり、
  規則自体の欠落ではない。`F24` の再発 (通知の虚偽) は別途 failures fragment で起票した。

## 次の一手差分

### 更新

- [T-659] **P2・ユーザー裁定待ち**: 発行から配備までの分裂窓。設計パッケージを
  `output/insights/2026-08-09_t659-activation-deploy-window/package.md` へ返した (R0〜R4)。
  推奨は R0 = 列挙できる閉集合に限る、R1 = 機構を作らず手順で担う (発行 tool に head を
  書かせる案は選択肢から落とす)、R2 = 活性化専用の作業窓を手順で置く、R3 = R1/R2 の採用分が
  land するまで次の活性化を始めない、R4 = runbook に専用節を作る。実装は [T-657] land 後。
  base: 7e6a1765a1db09bff01d69cefdd1c1a89fe93eb914550ecdee9e811da2dff08b
