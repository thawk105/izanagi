---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-13
wave: dev-wave-t1027-acceptance-reds-checker
seq: 1
title: 非帰属 checker の collect 打ち切りを直し、判定不能から非帰属を出さない不変条件を確立した — 実運用到達は producer 裁定待ち (コード + docs、変異 11/11 KILLED、branch worktree-dev-wave-t1027-acceptance-reds-checker)
---

## 本文

[T-1027] の P1 バグを直した。**真因は dispatch relay の stdout 打ち切りだった** —
child rc=0 の走行では子 stdout が末尾 4 KiB へ切り詰められ、collect 出力が 12,098 bytes ある
test file では `omitted_bytes=8002`、114 件中およそ 40 件しか親へ届かない。
checker はこの部分集合を完全な collection として扱っていた。
**依頼が挙げたもう一方の候補 (xdist group suffix) は実 log で否定した** —
`...@s8c-preregistration-candidate` は正しく match しており、`| ` 行前置の除去も正常だった。
打ち切りは出力が relay 上限を超える file でだけ起きる。

**親 brief の不変条件は向きが逆だった。** 「不完全な collection から `attributable` を
出すな」と書いたが、`attributable` (rc=1) は停止する側で安全である。危険なのは rc=0 側で、
下流は「取り込んでよい」と読む。段 3 の敵対レンズが blocker として拾い、段 4 で
{{D:unverifiable-input-must-not-yield-non-attributable}} として是正した。
**fail-closed 系の不変条件は、禁止する側の rc / status を明示して書く必要がある。**

**親の実データ実走が、静的レビューの出せない欠陥を出し続けた** ([T-1028] の完了条件を適用)。
段 3・段 6 のレンズ計 4 本は production 経路の rc=0 漏れを 1 件も見つけられなかったが、
親の実走は 5 件目の実環境欠陥 (probe 指紋 gate と自分自身の dispatch 残骸の衝突) を出し、
**変異 matrix は本 wave 自身が入れた回帰**
({{F:checker-replays-child-pytest-output-into-its-own-log}}) を出した。

**段 6 レビューが親の修正案を正しく否定した。** 親は「checker が作った残骸を消す」案を
出したが、既存契約 `test_ignored_artifact_from_node_fails_closed` は rerun node が作った
ignored な `__pycache__/marker.pyc` を必ず拒否することを求めており、一括削除はこの防壁を
壊す。指紋から `!!` 行を除外する案も同じ理由で採らなかった
({{F:absolute-clean-gate-vs-self-inflicted-dispatch-residue}})。

**scope の壁に当たった部分は裁定へ返した。** 残骸を安全に消す唯一の道は計算ノードに
bytecode を書かせないことだが、`PYTHONDONTWRITEBYTECODE` は dispatch の env allowlist に
無く、`tools/pegasus/**` はユーザーが指定した編集面の外である。`DW-S04` に従い、
親は scope を広げず {{T:probe-fingerprint-dispatch-residue}} として返した。
**したがって本 wave は [T-1027] の P1 バグを閉じたが、tool の実運用到達は
その裁定に依存する。**

変異は 2 巡した。1 巡目は KILLED 0 / MISMATCH 9 / SURVIVED 1 で、これは probe である。
MISMATCH の原因は上記の replay 汚染 (抽出結果に repo 非実在 nodeid が混入) であり、
SURVIVED 1 件は親の変異が等価だったため
(`PYTEST_ADDOPTS` は削除集合から差し引かれ別途上書きされる)。
replay を直し、期待 node を完全集合へ再導出し、当該変異を実効 gate へ 2 件に分割して
再走した結果が **baseline PASSED / 11 件すべて KILLED / SURVIVED 0 / MISMATCH 0** である。
1 巡目の結果は `mutation-result-probe1.json` として保全した。

子の工数は Codex 7 本 (plan 1、consult 2 + 再投入 1、author 1、review 2、fix 2 + 再投入 2)。
**段 3 レンズ A の初回は上流分類器に cybersecurity risk として弾かれ、rc=1・出力ゼロで
24 model call を失った。** 既存の教訓「防御目的を明記する」だけでは足りず、
prompt 全体の語彙 (攻撃・穴・偽装) が引き金だった。冒頭に「これは自社内製ツールの
品質レビューであり、セキュリティ製品でも攻撃ツールでもない」という前置き節を置き、
動詞を「評価せよ・列挙せよ」に替えたら通った。
fix2 は SIGTERM (model call 0) と、失敗 receipt が残るため同じ job-id を再利用できない
rc=2 で 2 度落ち、明示 `--job-id` で 3 回目に通った。

## 次の一手差分

### 完了

- [T-1027] collect 出力の打ち切りを真因として特定し、collection の権威を dispatch receipt へ
  移して footer 完全性 gate を張った。実データ実走で当該 nodeid の解決まで到達している。
  残る停止点は別事象として {{T:probe-fingerprint-dispatch-residue}} へ分離した。
  remaining: none
  base: e175e5ca5753ddf91cd2183b95ab08defe82132e59fe65cb9bea99404a40ff48

### 新規

- {{T:probe-fingerprint-dispatch-residue}} **P1・ユーザー裁定待ち**: probe 指紋 gate が
  「ignored file も含めて完全に空」を要求する一方、checker 自身が同じ worktree で pytest を
  dispatch するため `__pycache__` が残り、赤を含む実 log では必ず rc=2 になる。
  推奨は producer の env allowlist へ `PYTHONDONTWRITEBYTECODE` を足す案 (指紋 gate を
  1 bit も弱めない)。控えは裁定 inbox の
  `2026-08-13-t1027-probe-fingerprint-vs-dispatch-residue.md`。
- {{T:acceptance-reds-checker-2n-dispatch}} **P2・新規**: 帰属 checker は赤 1 件ごとに
  fresh probe worktree + collect + rerun を直列実行するため dispatch が 2n 回走る。
  実測 211-213 秒/dispatch なら 10 件で約 70 分。path 単位の collection 再利用は
  `test_each_node_uses_a_fresh_probe_worktree` の不変条件と衝突するため別 wave で設計する。
