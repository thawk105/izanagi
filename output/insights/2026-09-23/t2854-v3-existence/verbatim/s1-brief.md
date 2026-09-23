# [T-2854] 残り (1) — 設計 §3.3 の存在履歴を verifier に実装し、印 Integrity.v3_existence_unverified を撤去する — 段 1 brief (親)

wave: dev-wave-t2854-v3-existence / branch worktree-t2854-v3-existence / 起点 local main cadaf3805 (開始 gate fresh rc=0、2026-09-23 08:35 JST)
worktree: /work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-v3-existence
job dir: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-v3-existence

## 研究前進
D2212 項 2 (TPC-C 段 1 必須) の認定経路。現行 verifier は実 TPC-C v3 trace (単位 1・2 の B0、36,156 取引、辺 268,209、
orphan 0・version dup 0・X/P gate 充足) を「印だけ」で indeterminate にする (親が login で実測、workers 1/2 とも)。本 wave で印を存在履歴の
検査に置き換え、実 trace が certified に届くことを確かめる。これが無いと単位 5 (pipeline allowlist・witness・§6.1 の正例負例) の前提 (D2224 項 4、
単位 4 記録 §6 の R11) が満たせない。完了判定: (a) 合成 fixture で §3.3 の違反が object / compact (packed・tuple、workers 1/2) の全経路で
indeterminate、(b) 同じ fixture の違反を外した対照が certified、(c) 実 trace が certified (親の repo 外 probe)、(d) 事前登録の変異が全部 kill。

## scope (本題だけ)
- 変更面: orchestrator/verifier/{dsg,core,model}.py (必要なら parse.py)、orchestrator/tests/test_verifier.py。
- scope 外: 単位 5 (pipeline・allowlist・witness 試験・CLI 配線)、単位 3 (mocc emitter、並走 wave dbc416)、単位 11 (pin 前進)、
  段 2 (S/Q 行・範囲読み・§4.3 の初期キー一覧 file = 単位 7)、report.py の編集、CCBench の編集、新しい gate・検査・台帳・一般化。
- T-2847 (1) の並走 wave が新規 test file を足す。その file は触らない (本 wave は既存 test_verifier.py だけを編集)。

## 確定済みユーザー裁定・前提
- D2224 項 4: 存在履歴を検査するまで v3 を認定しない。印の撤去は §3.3 を実装する単位の完了条件。本依頼がその単位。
- 設計 §3.3 (逐語): 初期ロード済みの key は genesis (1,0) から存在する。初期に無く最初の committed write が INSERT の key は、INSERT より前が
  「挿入前 (unborn)」で genesis の値を持つとは解釈しない。DELETE は不存在の版を作り、R がそれを存在する値として読むのは不整合 (indeterminate)。
  W の op=I と独立 tag の I 行は別物。abort した挿入の版を読んだ R は既存の orphan read。
- 実 trace の値域 (親が実測、O13): W op は I (表 4..8、各 key の最初の write) と U (表 0,1,2,10) だけ、D は 0 件 (段 1 に Delivery なし)。
  R は表 0,1,2,9,10。提案規則 (P1〜P3) の違反は 0 件。

## 不変条件
1. v2 (C 7 token) の受理・拒否・verdict・integrity の各値と notes・result_to_dict の bytes・witness 順は不変。既存 v2 試験の期待値を変えない。
2. report.py は編集しない (silo_ladder_rung1 の verifier_module が bytes を束縛)。verifier に新 module を足さない (campaign_lock 等の source closure)。
3. 新しい test file・fixture dir を足さない。
4. object 経路と compact 経路 (packed・tuple、workers 1/2、並列→逐次 fallback、legacy 落ち) は同じ verdict・integrity を返す。
5. 規律 2・3: 判定できない存在は認定しない側へ倒す。違反は「どの txid がどの表のどの key のどの版をどう読んだ / 書いたか」まで構造化して返す。
6. 印を撤去する際、単位 4 の試験 test_v3_existence_unverified_and_v2_control の 2 例 (insert 後の genesis 読み、delete 版の読み) は
   非認定のまま、その理由が存在履歴の検査に帰属することを示す形へ書き換える (期待の緩和でなく帰属の置換)。v2 の同形は certified のまま。

## 親の provisional 裁定 (攻撃対象)
- (P1) 段 1 の初期キー集合は §3.3 の規則で W 行から決める: (表, key) が genesis で存在する ⇔ その key の最初の committed write
  (版順) が I でない。一度も書かれない key の genesis 読みは存在とみなす。§4.3 の初期キー一覧 file は段 2 (単位 7) で、ここでは使わない。
- (P2) 読みの違反: (a) 最初の write が I の key の genesis 読み、(b) op=D の版の読み。
- (P3) 書きの連鎖の違反: 版順で直前が存在する key への I、直前が不存在の key への U / D。§3.3 の直接の列挙ではないので scope 内か攻撃対象。
- (P4) Integrity に既定値 0 の件数欄を 1 つ足し clean() が 0 を要求、印の field と設定箇所は撤去。notes に見本。result_to_dict (report.py) は
  変えず、result_to_dict_v3 にだけ件数を出す。
- (P5) 検査は v3 のときだけ行う (v2 は op を検査しない現状を維持)。

## 成果物
production 差分 + 試験 (正例・負例・経路一致・印の撤去の帰属)、変異 matrix、親の実 trace probe の記録、insight README、fragment。

## 並列分割
author 1 本 (変更面が 3〜4 file で密結合)。
