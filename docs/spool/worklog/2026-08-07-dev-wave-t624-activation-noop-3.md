---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-07
wave: dev-wave-t624-activation-noop
seq: 3
title: [T-624] activation record の no-op 拒否規則を明文化し、述語の実装は見送った — 番号 delta の述語では裁定の狙った失敗を塞げず、提案された表は検出力ゼロだった (docs のみ、実装差分なし、branch worktree-dev-wave-t624-activation-noop)
---

## 本文

- **ユーザー裁定 (a) は本 wave で完了した。** 遷移規則を「全 env の delta ∈ {0,1} かつ
  少なくとも 1 env の delta == 1」へ明文化し、全 env 据置の no-op activation record を
  受理集合から外した ({{D:activation-transition-rejects-no-op}})。
  決定本文には裁定の逐語規則と射程だけを書き、未裁定の要素 (env 集合変化の扱い、述語の署名、
  型規約) を含めていない。
- **段 2 は GO、段 3 の 2 レンズはともに NO-GO で、根拠が独立していた。** レンズ A は
  裁定境界と規律 (`DW-G04` の発火材料が無い、identity 副作用を成果物影響に数えると `DW-G05` が
  恒真になる)、レンズ B は述語の意味と検出力を攻撃した。親が裏取りして**不採用に裁定した**。
- **決め手は 2 つある。** (1) 世代番号の delta だけを見る述語は、裁定の元の懸念
  「serial が増えているのに新規 run の contract hash が旧較正へ戻る」を塞がない。
  番号が指す contract の再束縛は規則の外にあり、D176 自身が逆引き index を authority と
  扱ってはならないと明記している。(2) 段 2 が提案した 20 行の表は**検出力がゼロ**だった —
  各 delta を見ずに「delta の総和が 1 以上かつ env 数以下」で判定する誤実装が 20 行すべての
  期待値と一致し、その誤実装は `(+2, −1)` の record を受理する。親が probe で実測した。
  land していれば、検出力の無い gate が「no-op を拒否する保証」として台帳に残っていた。
- **親の provisional 裁定 (P1)(P2) は誤り、(P3) は未裁定へ戻した。** 段 3 が親の一般化を覆すのは
  **5 wave 連続**である。今回覆されたのは「D176 が data 層の先行配置を許すのだから同型だ」という
  類推で、実測すると `is_valid_successor` は module 初期化の call chain に結線済み (2 世代目登録の
  瞬間に発火する) で、consumer が 1 つも無い新述語とは別物だった。
- **前提実測 1 件が偽だった (F30 の 4 度目の再発)。** 段 1 で「`env_contract.py` の bytes を
  literal で pin する台帳・test は 0 件」と記録したが、実際には silo evidence (path+sha 隣接 field) と
  t419 probe manifest (role 名 key) の 2 種が pin している。原因は検索出力を `head` で
  10 件に切ったことと、role 名 key を path 検索で探したこと。正しくは**歴史 pin 2 件・live pin 0 件**で、
  現行 bytes は既に pin 値と不一致のため実害は無かった。段 3 の 2 レンズが独立に検出した。
- **検査 (実装差分が無いため受入全走と変異 matrix は対象外)。** `check_docs.py` 違反なし、
  `spool_fold.py --dry-run` rc=0、docs 関連 3 file (`test_check_docs` / `test_s8b_repo_scan_invariant` /
  `test_spool_fold`) **398 passed**。docs commit 後の再走で repo scan invariant と check_docs の
  2 file **305 passed**、`check_ai_provenance.py` rc=0 (known-violations=6、増減なし)。
- **段 8 の改善候補は 2 件、dev-wave 本文の変更は 0 件。** (1) 検索出力を件数で切らない —
  `DW-O09` は「path の hit 0 件を pin なしと結論しない」を既に定めており、本文不足ではなく
  適用漏れなので failures の再発記録で閉じた。(2) 先例を根拠に scope を正当化するとき、
  その先例が production の call chain に結線済みかを実測する義務 — `DW-S01` の
  「brief 前に承認済み裁定の前提を実測する」が実質的に覆っており、同型欠陥の独立 2 例も無いため
  `DW-G03` に従い一般化しない。dev-wave 4 文書の aggregate は 25,134 / 25,200 bytes
  (余地 66 bytes、2026-08-07 実測)。予算引き上げは提案せず、新しい T / F も作らない。
- 一次資料 = `output/insights/2026-08-07_t624-activation-noop/` (段 1 brief、段 2 プラン逐語、
  段 3 の 2 レンズ逐語、段 4 裁定と親の裏取り実測 P〜S)。

## 次の一手差分

### 完了

- [T-624] 遷移規則の明文化を {{D:activation-transition-rejects-no-op}} として記録した。
  no-op 拒否の条件は決定本文が正本。述語の実装形は下記 2 件へ分離した。
  remaining: none
  base: 9277a3dfdd3afe6baadd42a9e4837969c863387f6739ce15f1050918ce51a5f0

### 新規

- {{T:activation-transition-predicate-form}} **P2・新規・ユーザー裁定待ち**:
  no-op 拒否規則を**コードでどう体現するか**。択一 = (a) env→generation の数値 mapping を
  受ける純述語 / (b) generation と contract hash (`GenerationEntry`) を同一入力で束縛し
  `is_valid_successor` と合成する / (c) 実 activation record schema が決まるまで置かない
  (親の推奨、次点 (b))。(a) は番号射影のため contract の rollback を素通しする。
  併せて `DW-G04` を T-624 系に限り上書きするか (合成 fixture を発火証拠と認めるか) も裁定が要る。
  親の推奨は上書きしないこと。逐語と根拠は
  `output/insights/2026-08-07_t624-activation-noop/s4-adjudication.md` の択一 α / γ
- {{T:activation-env-membership-migration}} **P3・新規・ユーザー裁定待ち**:
  activation の世代遷移で **env 集合が変わる場合**の扱い。択一 = (a) 集合変化は activation
  transition では永久に拒否し別機構へ回す (親の推奨、ただし別機構の裁定が要る) /
  (b) 追加は許し削除は拒否 / (c) 未定義のまま置く。決めないと、新 env を足した最初の
  activation record が一律拒否され、例外経路の後付けか受理集合の再変更になる。
  逐語は同 `s4-adjudication.md` の択一 β
