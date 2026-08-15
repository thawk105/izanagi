# t1132 — codex model routing (sol→luna) 再検討

依頼 (2026-08-16): 「gpt 5.6 sol を使っているところを luna max にしても品質がほとんど変わらないなら
そうしてほしい」。ほぼ同一の依頼が 2026-08-08 に D241/D242/D243 として裁定済みだが、今回は対象が
「sol 使用箇所全体」であり、D241 が扱わなかった段2 (plan)・段5 (author) を含む新しい scope を持つ。

## 経路

1. **技術調査 (fork)**: dev-wave の codex model は `docs/dev-wave/operations.md` DW-O01 の権威行
   (`operations.md:14`) を `tools/dev_waves/launch_authority.py` が正規表現で解釈して決める。
   コード側に以下の構造的不変条件がある。
   - I1 (`launch_authority.py:396-397`, runtime raise): 他段 (plan/author/review/fix/focus) の
     model は段3レンズ1 (`sol` capture) の model と一致必須。
   - I2 (`test_dev_wave_launch_authority.py:98-101`, test assert): 段3の2レンズは異なる model 必須。
   - I3: 他段 (plan/author/review/fix/focus) は現行コードで単一の `other_model` に束ねられ、
     段2/5 だけを段6 と切り離す独立設定は出来ない。
   両方とも `s1-brief.md` 作成前に自分で file:line を直接読んで確認済み。
2. **段2 プラン (`s2-plan.md`, codex sol, reasoning=max, read-only)**: I3 を解いて model authority を
   consult / 段2・5 / 段6 の3系統へ分割する実装案 (`launch_authority.py` の v1 (legacy, historical
   receipt 再構築専用) / v2 (live) 分割) を file:line 粒度で提示。「flip trick」(権威行の sol/luna
   位置を入れ替えるだけの docs-only 近道) は不採用と結論——145 箇所の実在 `--lane sol/luna` 呼び出し
   (`dev-wave-jobs/**/*.sh`) の意味が逆転する footgun があり、かつ現行 `check_docs.py` の exact pin
   に拒否されるため、そもそも「docs 1 行だけ」の近道にならない。
3. **段3 敵対相談 2 レンズ (`s3-lensA-correctness.md` = codex sol、`s3-lensB-scope.md` = codex luna、
   ともに reasoning=max, read-only)**: 独立に **NO-GO** で一致。

## 段3 が倒した論点

- **核心**: 「段2/5 の出力は下流 (段3敵対相談・段6敵対レビュー+変異matrix+受入全走) で独立再検査
  されるから、証拠なしで model を変えても安全」という brief の (P1) 論法は、**D207
  (`docs/decisions.md:9889`) が既に明示的に却下した論法と同型**である。D207 は段2プラン起草の
  effort 引き下げ提案を「起草物は後段が必ず攻撃するので安全に見えるが、弱い起草が must-fix と
  fix 巡回を増やし、消費と正しさが同時に悪化する経路を排除できない。この比較こそ paired 評価の
  対象」として却下している (`decisions.md:9907-9909`)。「検出力を下げる変更は規律2の対象」という
  D207 の一般原則は model 軸にも effort 軸にも等しく及ぶ。両レンズが独立にこの反論へ到達した。
- sol→luna の品質同等性を示す証拠は段2・段3・段5のいずれにも無い (ゼロ)。認証済み A/B
  (D266, `decisions.md:12259`) は段6 focused review の high 対 max だけであり、model 比較でも
  他工程の観測でもない。2026-08-08 の luna shadow pilot (91%/token−31.6%) は n=1・非盲検・循環評価
  として policy 根拠から明示除外されている (D241 自身がそう記録している)。
- **手続き上、段4 (親裁定) には D241 の該当部分を supersede する権限が無い**
  (レンズB)。D241は「段2/5/6はsolのまま」と明示的に固定した決定であり、これを再開する提案は
  「D241の論理を適用するだけ」ではなく「D241の段2/5部分の再開・supersede」に当たる。
  DW-S04 (`docs/dev-wave/core.md:72-76`) が定める段4裁定の権限は real/refuted と scope の裁定、
  および scope外real所見の裁定パッケージ化までであり、supersede そのものはユーザー裁定にしか無い。
- 段2プランが追加提案した段6 (review/focus) reasoning effort の `high→max` 変更は、model分割に
  必要な変更ではなく、D243 (`decisions.md:11309`)・D266 (`decisions.md:12259`) が明示的に据え置いた
  値への無根拠な上書きに当たる。両レンズが独立に不採用と判定。
- brief 自身の「T-184/T-189 がともに未着手」という記述は不正確 (両レンズが指摘、refuted 部分)。
  T-184 は reasoning 軸を採用済みで resource/retry 軸だけ残っている
  (`docs/phase3.md:1069-1086`)。未着手なのは T-189 (model-routing の妥当な比較実験の設計、
  `docs/phase3.md:1191-1195`) だけである。正確な記述は「段2/5の品質同等性を示す証拠が無い」。

## 段4 裁定 (親)

- 段2プランの中核提案 (I3 を解く model authority 分割、段2/5 だけ luna) は**技術的には実装可能**
  だが、その採用根拠だった (P1) は refuted。**証拠なしで実施してよいという結論は support されない。**
- 段6 effort の `high→max` は不採用。flip trick は不採用。
- **今 wave では実装しない** (`DW-S04` の「実装しない」裁定、4→7→8→9)。段2/5 の model 変更は
  scope外の real 所見として、設計択一・所見をユーザーへ裁定パッケージとして返す。
- 段3/段6 の model・段6 の effort はいずれの案でも変更しない (現行の D241/D243/D266 のまま)。

## ユーザーへの裁定パッケージ

**問い**: 段2 (plan)・段5 (author) の codex model を証拠なしで sol→luna (reasoning は現状維持)
へ変更してよいか。それとも T-189 (model-routing の妥当な比較実験の設計) を先に行うか。

**択**:
- (a) **T-189 を正式起票し、妥当な比較実験 (held-out 複数 task、paired・blind、事前登録済み
  非劣性 margin) を先に設計・実行する。** 証拠が出てから改めて判断する。親の推奨。
- (b) 証拠なしで段2/5 限定・既存 effort 維持 (model-only swap、変数を1つだけ動かす最保守形) の
  実装 wave を明示的に指示する。D241 の段2/5 部分を supersede するユーザー裁定として扱う。
  実装には `launch_authority.py` の v1/v2 分割 (legacy receipt 互換を含む)、`check_docs.py` pin
  更新、`DW-M01` 拡充 (レンズAが指摘した7カテゴリの変異登録) が要り、中規模の実装 wave になる。
- (c) 現状維持。今回の依頼は見送る。

**注記**: 「luna max」は 2026-08-08 の原文 (`output/insights/2026-08-08_t182-luna-stage3-hybrid.md:18`)
では段3 (元々 reasoning=max) への適用として使われた語であり、段5 (現状 high、pin なし) へ
自動適用できる根拠ではない。(b) を選ぶ場合も、model と effort は別々に判断できる
(レンズBの指摘: 変数を1つだけ動かす方が保守的)。

## エージェント工数

codex 子 3 本 (plan 1・consult 2)、すべて `check_codex_output.py` 受理。3 本とも read-only sandbox
で pytest 非実走を正しく申告。I1/I2 の実在と段5 effort の unbound 性は親が
`launch_authority.py:385-404`・`test_dev_wave_launch_authority.py:90-109` を直接読んで実測確認した。
編集は一切していない (worktree clean)。
