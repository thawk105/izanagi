---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-17
wave: dev-wave-t1279-layer3-head-outside-repo
seq: 1
title: 層 3 材料レポートの生成元版 fallback が repo 外 campaign で必ず倒れる件を直し、8c 探索の最後の閂を外した (コード + テスト、branch worktree-dev-wave-t1279-layer3-head-outside-repo、変異 matrix = baseline PASSED・8/8 KILLED・正例 1 SURVIVED・MISMATCH 0)
---

## 本文

**8c 探索を止めていた直列 2 本のうち残り 1 本を閉じた。** 層 3 材料レポートの
`meta.generated_from_head` は、呼び手が値を渡さないとき campaign directory に対して
`git rev-parse HEAD` を実行していた。8c の build cell はこの経路を必ず通り、探索用 output root を
repo 外へ置いた構成では rc=128 で必ず倒れる。もう 1 本 (schema の `perf_observation` 穴) は既に
land 済みなので、本件で探索経路の閂は無くなった。

**親の暫定裁定が段 2 で反証された。** 親は「lock が束縛する pin を git HEAD より先に見る」形を
provisional に置いたが、repo 内 v2 campaign では lock pin (lock 作成時 HEAD) と現行値
(現在 HEAD) が食い違うため、official 側の値が変わる。確定形は「明示引数 → campaign の git HEAD
→ 生成器 source repo の外側かつ v2 lock の authority があればその pin → fail-closed」とした
({{D:layer3-head-fallback-order}})。

**レビューが受理集合の漏れを 1 件出した。** 新 fallback は `build_accepted_report`
(certifying 入口) にも自動的に効き、repo 外 campaign が certifying レポートを作れるようになる。
ユーザー裁定は非 certifying の生成が repo 外で失敗しないことだけを要求しており、certifying の
緩和は指示されていない。規律 2 に従い、certifying 入口は wave 前と同じ受理集合へ固定した
(値も例外型も wave 前と同一)。

**レビューが親 brief の一般化を反証した。** brief は「探索 campaign は機械的に必ず repo 外に
置かれる」と書いたが、これは過大である。探索用 output root の環境変数が未設定なら repo 内
`output/` へ落ちる。repo 外強制が働くのは環境変数を設定した経路だけで、そこでは
git 祖先を持つ path が機械的に拒否される。修正の方向は変わらないが、記述としては誤りだった。

**新規テストが自分の fixture に騙されていた。** 段 5 が足した repo 外 v2 テストは、期待 pin を
`_campaign` fixture の v2 lock から取っており、その値は現在の source HEAD と同じだった。
このため「lock pin の代わりに source repo の HEAD を返す」退行が全 assertion を通り抜ける。
pin を source HEAD と異なる固定値へ変え、campaign が source repo の外かつ git HEAD を取得
できないことを前提 assert で固定した。この修正が効いたことは変異 M07 が KILLED になることで
裏が取れている。

**前提 assert が環境の残骸に引っかかった。** 1 巡目 fix が代理条件で前提を書いたため、
実行機に残っていた空の `/tmp/.git` で 3 node が赤になり、焦点走 1 回を捨てた
({{F:proxy-precondition-false-red}})。前提を「実際に git HEAD を取得できないこと」へ
書き換えて解消した。

**scope 外の real 所見 2 件をユーザーへ返す。** (1) CLI から repo 外 campaign を render できない
(`output_root` を渡す手段が無く、campaign 配置検査が先に拒否する)。これは本件とは別の層の制限で、
直すには CLI に新 option を足す設計判断が要る。(2) 8c の E2E テストが標準 producer ではなく
test helper で v2 lock を直接書いているため、標準 producer が v1 lock を作る退行を単独では
検出しない。どちらも本 wave が作った穴ではない。

**agent 工数**: codex 子 7 本 (plan 1・author 1・review 2・fix 2・focus 1)。
親の実測は焦点走 4 回、全史 provenance 監査 1 回、変異 probe 1 回、変異本走 1 回。

## 次の一手差分

### 完了

- [T-1279] 層 3 材料レポートの生成元版 fallback を repo 外 campaign でも成立する形へ直し、
  certifying 入口の受理集合は wave 前へ固定した。8c 探索を止めていた直列 2 本は両方とも閉じた。
  remaining: none
  base: ada9684084c2f03887c49c473694998bda510735c7af7582b5c55829dd5349e0

### 新規

- {{T:layer3-cli-external-campaign}} **P2・新規**: 層 3 レポートの CLI が repo 外 campaign を
  render できない。`output_root` を渡す手段が無く、campaign 配置検査が helper 到達前に拒否する。
  直すには CLI へ新しい option を足す受理集合の設計判断が要る。実害は手動検証経路だけで、
  8c 自動経路は Python API を直接呼ぶため影響を受けない。
- {{T:s8c-e2e-uses-test-lock-builder}} **P2・新規**: 8c の E2E テストが標準 producer を通らず
  test helper で v2 campaign lock を直接書いている。標準 producer が authority 無しの lock を
  作る退行を、この E2E は単独では検出しない。既存のテスト構成の問題であり、検出力を
  上げるなら producer 経由の fixture へ寄せる必要がある。
