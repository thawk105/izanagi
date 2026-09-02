# [T-2139] B-4 材料レポートと certified 選択の接続は、今は実装できない

2026-09-01 の dev-wave (branch `worktree-dev-wave-t2139-b4-certified-connection`)。
**実装面の差分はゼロである。** 本 wave が残すのは実測した事実、却下した設計、
再開条件の 4 点である。

依頼は「`p3_b4_analysis_path.py` の docstring が scope 外と宣言する 5 語のうち最後の 1 語
(`certified-selection connection`) を埋める」だった。段 2 で設計を起草し、段 3 の 2 レーンが
独立に blocker を出し、ユーザー指示により段 4 の裁定を Codex へ相談した。
**3 者が独立に同じ結論へ到達した — 現 checkout では接続を完成できない。**

## 一次資料

| file | 中身 |
|---|---|
| `verbatim/stage1-brief.md` | 親の段 1 brief |
| `verbatim/stage2-plan.md` | 段 2 の実装プラン (却下した設計。下記参照) |
| `verbatim/stage3-lens-a.md` | 段 3 レーン A (正しさ境界) |
| `verbatim/stage3-lens-b.md` | 段 3 レーン B (整合・実効性) |
| `verbatim/stage4-parent-ruling.md` | 親の段 4 裁定 |
| `verbatim/stage4-codex-decision.md` | ユーザー指示による Codex 相談と、その推奨 |

`verbatim/` 配下は placeholder guard・三軸語検査の対象外である
(2026-08-09 裁定、`docs/phase3.md` 見送り台帳 [T-686])。

## 測った事実

### 1. Layer3 の accepted-report 経路は構造的に閉じている

`certifying_input: True` を production で作る箇所は `layer3_report.py` の
`build_accepted_report` 内の 1 か所だけである。そこへ入るには同 file の
`verified.certifying is not True` を通す必要がある。
その `VerifiedAcceptanceReceipt` を作る唯一の parser は `s8c_acceptance_receipt.py` にあり、
**「Both generations structurally record unresolved approval authority.
No accepted bytes can turn either generation into a certifying receipt.」**
と明記したうえで `certifying` が `False` 以外なら必ず拒否する。

`build_accepted_report` を成功させている既存テストは、いずれも
`require_current_verified_receipt` を差し替えて初めて通る。
**実 receipt のまま receipt gate を越えるテストは 1 件も無い。**

### 2. ただし「certified 側がすべて閉じている」は誤りである

親は当初その一般化を書いたが、Codex 相談が反例を出し、親が実物で確認して訂正した。
D1236 が定める B-4 の支配点は WAL の COMMIT 合流点にあり、`wal.py` の
`STAGE_COMMIT` 分岐が exact な B-4 marker を見て `verify_b4_launch_context` を呼ぶ。
**この関門は実際に発火する。**
ただし材料レポートを作るより**前**にある sink なので、
「レポート → certified 選択」の接続先にはならない。

正確な言い方は次である。

> Layer3 の正方向は構造的に閉じている。別に実在する B-4 の WAL sink は材料レポートの
> consumer ではない。そして現 checkout には、レポート生成**後**の正規呼び出し元も、
> 実物の材料レポートも、耐久化した判定の置き場も無い。

### 3. 実物の材料レポートは 1 件も着地していない

`find output -name report.complete` は 0 件。
`p3_b4_material_report.py` を読む production consumer も 0 件。
`DW-G04` が要求する「発火条件を満たす既存 artifact path か計測 ID」を書けない。

### 4. 親の brief の一般化 2 件を訂正した

- 「到達可能な分析 verdict は 1 つだけ」→ 正しくは
  **材料レポートの正規コマンドに限れば 1 つ**。分析経路そのもの
  (`evaluate_b4_artifacts`) は妥当な floor を渡せば `established` へ到達する。
- 「下流 consumer が存在しない」→ 正しくは **B-4 材料レポートを読む consumer が存在しない**。
  `certifying_input` を作る仕組み自体は実装済みで、上記 1 の理由で到達できない。

## 却下した設計 (`verbatim/stage2-plan.md`)

段 2 は新規 module `p3_b4_certified_selection_connection.py` と test 1 本を提案した。
`report.complete` が束縛する `report.json` / `report.md` の実 bytes を再検証し、
正規に到達する 2 形を「許可しない」判定へ写す設計である。

**これは接続ではなく、孤立した validator である。** 却下理由:

- 呼び出し元が無く、実装しても certified 選択の受理集合・材料レポート・台帳は
  1 bit も変わらない (`DW-G05` を満たせない)。
- 許可判定を `Literal[False]` で固定すると、決して偽にならない恒真の保証になる
  (レーン A)。実装するなら「阻害理由の集合が空か」で計算し、
  理由集合が到達入力で実際に変わる形にしなければならない。
- `DW-G04` の発火 gate を書けない。tmp に pair を作る pytest node は
  **入力生成条件**であって接続の発火条件ではない (レーン B)。
- 3 file 束縛は内容整合しか示さず、対象・発行者・配置を束縛しない。
  協調して差し替えた bundle は通る (レーン A / B が独立に構成)。
- 登録予定の変異 3 件は Markdown 層に mask され、赤の理由を 1 つに絞れない (レーン A)。

**この設計は「上流が解けたらそのまま実装する案」ではない。**
§5 未発効・floor 不在・現行 exact field 群という**閉鎖状態そのもの**を検査する設計であり、
floor が発効すればその前提が反転して作り直しになる。
再利用できるのは具体案ではなく、下の設計条件だけである。

## 再利用できる設計条件

将来 接続を実装する wave は、次を満たすこと。

- fail-closed であること。
- caller が書いたレポートの field を、それ単独で権威にしないこと。
- 対象 (publication / campaign identity)、発行者、配置を束縛すること。
- sink の**必須入力**にすること (任意の補助検査にしない)。
- 判定を耐久化し、sink 側から参照できること。
- 実 artifact を実呼び出し元から sink まで通す end-to-end の変異を持つこと。

## 再開条件

T-2139 は次の**論理積**が成立するまで再開しない。

1. 実物の材料レポート (`report.complete`) の安定した所在、または計測 ID。
2. レポート生成後の正規の呼び出し元と、その持ち主。
3. 耐久化した判定の保存先と、sink からの参照。
4. 順方向 (許可枝) も含める場合のみ — floor の発効 ([T-2140]) と、
   発行可能な approval authority。

## 本 wave がしていないこと

- production / test code の追加。
- 事前登録 `docs/phase3-b4-reflux-ablation-preregistration.md` の編集。
- 材料レポートの wire の変更 (`certification_scope.not_guaranteed` は
  `certified_selection_connection` を含んだままである — レポート単独では保証しない、
  という記述は今も真である)。
- 稼働中の別 wave が所有する `p3_b4_{admission_record,closed_critic,launcher,wiring_probe}.py`
  とその test の編集。
- 正式 B-4 実走、qsub、性能測定、build。

## 子の内訳

Codex `gpt-5.6-sol` / `reasoning=xhigh` を plan 1、consult 2、consult (裁定相談) 1 の計 4 本。
全件 `tools/check_codex_output.py` rc=0。
いずれも `sandbox=read-only` で pytest を実走していない。**子の未実走を緑と記録していない。**
実測はすべて親が行った。
