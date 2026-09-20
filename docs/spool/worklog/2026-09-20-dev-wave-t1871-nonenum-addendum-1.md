---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-t1871-nonenum-addendum
seq: 1
title: [T-1871] 旧 headline 復活条件の「非列挙」に D1441 の操作的定義を置く追補 1 を、事前登録の bytes を変えない別 file として着地した (docs のみ、branch worktree-dev-wave-t1871-nonenum-addendum、実装面 0・変異 matrix 免除、段 3 相談 2 本 real 5 / refuted 3、段 6 レビュー NO-GO → fix → GO)
---

## 本文

- **依頼の前提を覆した段 1 実測:** `docs/phase3-main-experiment.md` の sha256 `e544de19…` は凍結成果物 5 本 (s1-freeze 2 本、s8b-freeze 3 本) に source として記録され、同 doc に 1 行足すだけで現 root を読む直接 verifier `s1_known_axes_freeze.verify()` が `source sha256 不一致` で赤になる (一時変異で実測、復元済み)。「同 doc へ日付付き追記」は D1789 (発効後の事前登録は bytes を変えず別 file で訂正、sha 貼り直しは却下案) にも当たる。
- **裁定 (親、段 3 相談 2 本で攻めた後に確定):** 追補は別 file `docs/phase3-main-experiment-addendum-1.md` に置き、同 doc は 0 byte 変更。先例 = b10 の `…-erratum-1.md`。sha 追随 (2026-07-16 の先例) は T-080 が JSON の raw bytes を code 定数で pin して以降は凍結 chain 全体の再凍結になるため採らず、`_HISTORICAL_CODE_PATHS` への docs 追加は verifier の弱体化なので採らない。別 file は「唯一の形」とは書かない。
- 相談で real 5 件 (8b 全経路への一般化は過大 = T-080 adapter 発火時は H_mig blob 照合の別経路、語義改訂の発効と D1012 の休眠解除の発火を分ける、phase3 pointer に将来規則 `addendum-N` や「唯一」を書かない (不在 path は check_docs 赤)、節の圧縮、命名)、refuted 3 件 (D1441 の記録だけで足りる / 休眠・(c')・B-5 との矛盾 / 逐語だけでは不足)。段 6 レビュー 1 本は must-fix 1 件 (「偵察結果を 1 件も見ていない」が一次資料 §2 M8 を超える → 既知結果の開示に置換) で NO-GO、fix 後の焦点再レビューで 4 件 closed・回帰なし・GO。
- 焦点走 (`test_s1_known_axes_freeze.py`、追補入りの木、bounded local 94 秒): 50 passed / 9 skipped (growth hold) / 0 failed。実 repo を読む `test_historical_current_use_matches_real_reconstruction` は passed 側。受入全走は本 fragment の後の tip へ投入し、結果は job dir の受入 receipt (insight の job dir 参照)。
- 追補が発効させるのは語義改訂だけ。旧 headline の復活・D1012 の休眠・D52 (c')・壁 2 (D1409) は動かない。論文ストーリー 2026-09-14 版の「定義の置き直しは未裁定」は D1441 以降の現状を表さないが、論文ストーリー次版は scope 外なので本 wave では触らない。
- 素材: 事前登録の bytes が凍結 chain に pin されている文書は、日付付き改訂を同 file へ足せない。別 file の追補 (D1789 の erratum 系列) が append-only 契約の履行形になる — 一次資料 = `output/insights/2026-09-20/t1871-nonenum-addendum/README.md` §0。
- 工数: codex 子 4 本 (consult 2・review 1・焦点再レビュー 1)。test 走行は焦点走 1 + 受入全走 1。

## 次の一手差分

### 完了

- [T-1871] D1441 の 4 点 (固定予算下の操作的定義、新状態骨格は追わない、レンズ本数は規則にしない、段階 A gate はやり直さない) を `docs/phase3-main-experiment-addendum-1.md` に日付付き追補として置き、`docs/README.md` と `docs/phase3.md` 分離節から導線を張った。事前登録本体の bytes は不変。
  remaining: none
  base: a4f3d6536509131c572fec46e474a00d53722098c5b864e95aaef64907a27e2d
