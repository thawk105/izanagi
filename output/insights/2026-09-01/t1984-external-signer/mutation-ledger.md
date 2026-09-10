# 変異台帳 — [T-1984] 外部署名主体

anchor commit: `831b30a51` (wave branch `worktree-dev-wave-t1984-external-signer`)
走行: 親 probe (repo 外)。各変異を注入 → 焦点走 → `git checkout --` で復元。
焦点走は `python3 tools/run_tests.py orchestrator/tests/test_external_acceptance_signing.py
orchestrator/tests/test_plain_runner_coverage.py -q -rf` (親環境、`effective_scheduler=loadgroup`)。

baseline は全走で緑 (rc=0、赤 node 0 件)。復元後の作業ツリーは毎回 clean。
node 抽出は `FAILED`/`ERROR` 行と `IZANAGI_FAILURE` の nodeid 欄の 2 経路で行い、
rc 非 0 で抽出 0 件なら fail-closed で停止する契約にした (F688/F689)。

## 最終結果 (anchor `831b30a51`)

| # | 変異 | 期待 | 実測 | 赤 node 数 |
|---|---|---|---|---|
| M1 | 署名不一致の例外を握り潰して成功扱いにする | KILLED | **KILLED** | 3 |
| M2 | 固定公開鍵 loader が環境変数指定の鍵を採用する | KILLED | **KILLED** | 1 |
| M3 | 署名対象から 1 root field を落とす | KILLED | **KILLED** | 4 |
| M4 | canonical 化の key 順序を挿入順へ倒す | KILLED | **KILLED** | 1 |
| M5 | 検査した tip の束縛比較を省く | KILLED | **KILLED** | 1 |
| M6 | 高水準 API が固定 loader と署名検証を迂回する | KILLED | **KILLED** | 4 |
| M7 | wave 名の束縛比較を省く | KILLED | **KILLED** | 1 |

7/7 KILLED、MISMATCH 0 件。

## erratum 1 — M7 は 1 回目の走行で SURVIVED だった

**初回結果を消さない。** anchor `46a07cceb` 時点の走行で、M7 は **rc=0・赤 node 0 件 =
SURVIVED** だった。wave 名の束縛比較を `False` へ倒しても、どのテストも赤にならなかった。

等価変異ではない。**別の wave 向けに署名された受領証が、他の条件さえ揃えば別 wave の
期待 context で受理される**ことを意味し、受理集合の拡大にあたる。
既存の再送負例は別の排他権世代・別の検査 tip を使っており、**wave 名の比較そのものを
通っていなかった。**

fix (commit `831b30a51`) が、期待 wave 名だけが異なり main・tip・排他権の世代・鍵・署名が
すべて一致する負例を追加して閉じた。再走で M7 は単一 node で KILLED になった。

**この穴は静的レビュー 2 本を通り抜けている。** 段 3 の敵対相談 2 レンズも、段 6 の
敵対レビュー 2 レンズも検出しなかった。**変異走行だけが検出した。**

## erratum 2 — M2 は段 6 レビュー時点で SURVIVES と判定されていた

段 6 の敵対レビュー A が、固定鍵 loader と高水準検証 API を**一度も通らない** control 群を
検出した。低水準 API へ呼び手が作った鍵を直接渡す形だったため、loader が環境由来の鍵を
採用しても、高水準 API が署名検証を迂回しても緑のままだった。

1 回目の fix が、固定 path の loader と高水準 API を実際に通る正例と、
鍵違い・環境差し替え・鍵欠落・不正形式の 4 負例を追加して閉じた。
**この初回判定も消さない。**

## 冗長 gate として証拠から外したもの (DW-M03)

**「署名 field を落とす」負例は M1 の証拠に数えない。** 署名検証へ届く前に
exact-schema の検査が先に赤にするため、単一理由性が成り立たない。
Ed25519 層の実効負例は鍵違いと field 改竄の 2 件である。

## 登録から外した変異

段 4 で登録した M6・M7 は、書込み防護機構への変異だった。**その機構は AI が編集できない**
(防護機構が自分の subtree への書き込みを自ら拒否する) ため、本 wave では実装せず、
対象実装も負例も存在しなくなった。そのまま KILLED と記録すれば実在しない防護を
充足済みと誤記することになるため、段 6 レビューの再照準に従い署名境界の変異へ差し替えた。
差し替え後の定義は段 4 裁定の erratum 8.2 を正本とする。

## 走行環境

`hang_risk` 変異は 1 件も登録していない。全変異は焦点走 1 回で判定が付き、
`hang_timeout` に依存しない。
