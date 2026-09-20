---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-t2803-provenance-receipt
seq: 1
title: [T-2803] 全史 provenance 監査の受領証 attributes fingerprint を index の directory 集合非依存にした — 実在する候補だけの digest + 候補 directory に「監査で属性が効く merge path の祖先」を履歴から加える (D2045 の改訂)、判定不変を正例・負例 6 本と変異 4/4 KILLED で固定、attributes 束縛単独の隣接失効 旧 25/60 → 新 0/60、実機正例 cold 58 秒 / CPU 108 秒 → warm 22 秒 / 9.5 秒 (コード + テスト、branch worktree-dev-wave-t2803-provenance-receipt)
---

## 本文

- ユーザー依頼 (2026-09-20、dev-wave 引数の逐語は insight `verbatim/T-2803-origin.md`) の範囲で 1 wave。起点は entry 1722 の [T-2803]、一次資料
  `output/insights/2026-09-20/t2609-t2656-provenance-cost/`。本 wave の一次資料は `output/insights/2026-09-20/t2803-receipt-attributes-fingerprint/README.md`
  (時系列・論証・反例・テスト表・変異 matrix・実測・限界・裁定パッケージ候補・再現資料)。設計判断は {{D:receipt-attributes-history-candidates}}。
  専用 handoff は job dir (`/home/SFC/tanab/.claude/jobs/75bfe8b0/handoff/`)、wave の生ログ・clone・script は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2803-provenance-receipt/`。
- 起点 local main `f94b61fc865af29ff3c7e1c8ef8b99fd8a1216ad` (開始 gate rc 0、20:53 JST、main が動いていたので ff-only を 2 回)。段 1 実測: 共有 store の受領証 424 件 /
  11 partition、直近 8 件は同一 checker なのに attributes digest が 8 種すべて異なる (cold 連鎖)、候補 dir 2,835 / index 29,684、実在 `.gitattributes` は root 1 件。
  DW-O13 (受理形を増やす既存述語の改訂) 成立で入力 field・値域・正負例の到達性を brief に書いた。
- 段構成: 軽量版 + 敵対検証 (段 2 は親 plan、段 3 consult 1、段 5 author 1、段 6 review 2 + fix 3 巡 + 焦点再レビュー 1)。Codex 全段 `gpt-6-astra` / medium、計 8 本 60 call。
- **設計の推移:** 初版 (段 4 plan v2) = absent 候補を digest から外し、受領証に候補集合 (zlib + base64) を保存して「受領証の候補 ⊆ 現在の候補」を検査。段 3 相談 A の
  must-fix (候補 dir 脱落 + untracked `.gitattributes` 出現の反例) を閉じる形だったが、段 6 レビュー A が実 Git で「候補外 dir の untracked `.gitattributes` が root の
  `-diff` を上書きして監査に効き、後で dir が候補入りしつつ file が消える」反例を構成し、初版は受領証なし oracle (rc 1) と食い違う (rc 0) と判明 → NO-GO。
  私は段 4 でこの残差を「D2045 の既存限界の内側」と分類していたが、判定基準は oracle との一致であり誤分類だった。
  最終形 (段 6 裁定 plan v3) = 候補 directory を「root ∪ index の祖先 ∪ S(head) の merge 全件の『merge と第 1 親の name-only diff』の path の祖先」にする。
  `--cc` の候補 (全親 diff の交わり) ⊆ 第 1 親 diff なので上位集合、履歴とともに単調増加。これで両反例が digest で cold になり、包含検査・候補保存・schema 2 は不要になって撤去。
- fix は 3 巡 (DW-O16 の上限): fix1 = plan v3、fix2 = 候補列挙を `git log --no-walk --stdin` 化 (既存 pin `diff-tree --stdin` = D2169 path batch の識別子と衝突) +
  T-neg-6 の untracked 前提の修正 (`_commit` helper が `git add -A`)、fix3 = argv 順序 (既存 pin `log --no-walk=unsorted` = D2033 message batch の識別子と衝突)。
  焦点再レビュー GO (must-fix 0、nit = 費用記述)。実装 commit `4c532aa0b`、fix commit `00d781372`、merge commit (local main 7c0a1c63a) `47fbfd58c`。
- 焦点走 (計算ノード): 6 file 2718 passed / 5 skipped / 0 failed (focus-6)、単独走 555 passed (base 549 + 新 6、focus-8)。commit 後 full 監査 (login) rc 0 × 3
  (実装 commit 12,061 件 112.5 秒、fix commit の E-2 cold 58.4 秒、merge 後 12,157 件 47.4 秒、いずれも cold・新規違反なし)。
- 変異 matrix (独立 clone D1009、main = `00d781372`、計算ノード dispatch、`test_check_ai_provenance.py` 単独走、exact な置換文字列、各 `old` 出現 1):
  probe で観測 node を集め final で完全一致 — **baseline PASSED、M-1〜M-4 = 4/4 KILLED (期待 node 完全一致: M-1 12 node、M-2 = T-pos-1 のみ、M-3 = T-neg-3 のみ、
  M-4 = T-neg-1 + T-neg-6)、等価 EQ-1 SURVIVED (期待どおり)、MISMATCH 0**。
- 実測 (login pegasus02、1 回ずつ、時間短縮率とは読まない): (E-1) 同一 60 遷移 (local main first-parent、独立 clone、同一 checkout で旧 blob `7c02fb2d…` と新 file
  `2b72e1d5…` を評価) の attributes 束縛単独の隣接失効数 **旧 25/60 → 新 0/60** (新 dir 導入遷移 25、dir 削除 0、`.gitattributes` 変更 0)。
  (E-2) 独立 clone・新 checker: cold 全史 rc 0 / 12,062 件 / wall 58.4 秒 / CPU 108 秒 → 新 directory 導入 commit で warm rc 0 / 12,063 件 / **wall 21.9 秒 / CPU 9.5 秒**
  (受領証 2 件目発行) → root `.gitattributes` 変更で cold 62.6 秒 / 96 秒。候補列挙の費用 (4,369 merge): `rev-list --merges` 0.65 秒 + `git log --no-walk` 1.7〜3.5 秒、
  1 走 2 回 (lookup と publish)。他 binding・partition・混雑時・計算ノード・実 land の連鎖は未測定。
- 限界・言わないこと: `attr.tree` / bare / `GIT_ATTR_*` / errno は従来どおり束縛外。既存テスト 2 本が absent 候補差への感度を失う (期待値不変、記録のみ)。
  「50 % → 0 %」は attributes 束縛の隣接失効数の比。改訂直後の land は checker sha が変わるので cold。
- 事故 (自分起因): 単独走の dispatch 走行中に fix commit を作り実 repo HEAD を読むテスト 23 件を非帰属赤にした (F558 の同型再発、failures fragment)。
  E-2 で clone に author identity が無く commit が失敗したまま 1 走投げた (同 tip の warm 走として記録、identity は `git -c` で commit だけに与えた)。
- 裁定パッケージ候補 (起票せず insight §11): 候補列挙の 1 走内 memo 化、`attr.tree` 等の束縛、errno 正規化。
- 工数: codex 8 本 (consult 1、author 1、review 2、fix 3、focus 1、60 call)、計算ノード job = 焦点走 7 + 変異 probe 6 + final 6、login 走 = full 監査 3 + E-1 2 + E-2 4。

## 次の一手差分

### 完了

- [T-2803] 受領証の attributes fingerprint を「実在する候補だけの digest + 監査で属性が効く merge path の祖先 dir を履歴から候補に加える」形へ改め、判定不変を正例・負例
  6 本と変異 4/4 KILLED で固定し、attributes 束縛単独の隣接失効 旧 25/60 → 新 0/60 と実機正例 (cold 58 秒 → warm 22 秒) を記録した。
  remaining: none
  base: 45bc7ee4c9b0a4b32e025155526f09efff1fd42b3d8bf626ca7874f50aa2858c
