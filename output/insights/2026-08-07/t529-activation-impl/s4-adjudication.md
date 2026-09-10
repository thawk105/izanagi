# 段 4 裁定 — [T-529] 本 wave では実装しない

基準 commit: 364c6067。段 3 の 2 レンズは独立に **NO-GO** で一致した。
親の provisional 裁定 P1・P2 は**覆った**。以下は親が裏取りした結果に基づく裁定である。

## 親が独立に裏取りした 3 点 (すべて real、file:line は親の実測)

1. **循環 import。** `env_attestation.py:25` が module 冒頭で `env_contract` を import する。
   プランは逆向きに `env_contract` の module 初期化中へ
   `env_attestation.load_verified_calibration()` を呼ぶ設計なので、`env_attestation` を
   先に import する既存 consumer (oracle report / T-126 / silo / 複数 test) では
   部分初期化中の module へ到達する。**単位 A の authority loader は現プランどおりには起動しない。**
2. **floor の公式経路は Python gate より前に書く。** `tools/pegasus/floor_campaign.sh:882-894` は
   `floor-driver.stdout` / `.stderr` / `floor-driver.launch-attempted` を書いた**後**に
   `s8b_floor_campaign.py --mode official` を起動する。process-local gate は公式経路では
   最初の書込みより前に立てない。
3. **T-126 は git-archive した source stage から driver を起動する。**
   `tools/pegasus/t126_qualification.sh:736-738` は `$SOURCE_STAGE/...t126_driver.py` を
   `--git-repo-root "$ARTIFACT_REPO_ROOT"` 付きで起動する。source stage に `.git` は無く、
   authority root は CLI 解析後にしか判らない。**import 時 HEAD loader は成立しない。**

## 親の実測のうち覆ったもの

- **実測 5 は誤りだった。** R1 と T-529 裁定 (1) は別の問いである。
  裁定 (1) は *activation record* の trust root を何にするかであり、
  R1 は *記録 hash だけで、当時 active だった証明なしに世代を選んでよいか*である。
  両レンズが独立に file:line 付きで指摘した。**R1 は未裁定のままである。**
- **実測 6 は主張しすぎだった。** module 属性 patch で 2 世代 registry を注入できることは示したが、
  それは import 時の初期化経路 (`_build_registry → validate_generations → REGISTRY`) を駆動しない。
  よって「複数世代を import 時に拒否する実装」でも同じ正例が通る。
  **正例は依然として永久 fuse と観測的に区別できない。** 親自身の probe が import に成功したのは、
  import 時点の registry が 1 世代だったからであり、この点を親は取り違えていた。
- **(P1) は半分だけ成立する。** D196 の理由は 2 本ある。(a) 配線順序は T-574 で充足した。
  (b) 「発火する正例を書けないので `DW-G04` により設計メモに留める」は**充足していない**。
  親は (a) の充足を D196 全体の充足へ一般化していた。
- **(P2) は成立しない。** `DW-G04` に「既知事実なら免除」という条項は無く、
  裁定逐語にも同 gate を上書きする指示は無い。

## 裁定

**本 wave では実装しない。** `DW-S04` に従い段 5・6 を飛ばして `4→7→8→9` とする。
実装差分が無いため**変異 matrix と受入全走は対象外**である。

理由は D196 の判断を覆す材料が無く、むしろ増えたことにある。上記 3 点は裁定時点で未見の新事実であり、
とくに (2)(3) は**裁定された設計 (「6 入口が最初の書込み前に検査する process-local gate」) が
floor と T-126 では実現できない**ことを意味する。ここを黙って部分実装すると、
入口被覆率の過大報告 (裁定 6 が禁じたもの) と、永久 fuse と区別できない「名ばかりの保証」
(D176 が型分離を却下した理由と同型) の両方を台帳へ残す。

`DW-S04` に従い、親が不採用にはせず、新事実付きでユーザー再裁定へ戻す。

## ユーザーへ返す択一 (real 所見のうち scope 外のもの)

| # | 択一 | 親の推奨 | 決めないと何が起きるか |
|---|---|---|---|
| A | **R1 (記録 hash を、当時 active だった証明なしに世代選択の権威としてよいか)。** (a) 現状受容し「非偽造」を主張しない / (b) historical authority を「activation chain 上で ever-active な hash」に限定する / (c) 外部 trust root | (b)。(a) は registry にあるだけで一度も active でない g2 を記録した artifact まで再検証が受理する | 未活性 g2 を記録した artifact が historical evidence として certified 選択の proof 参照へ入りうる |
| B | **`DW-G04` を T-529 に限り上書きするか。** (a) 上書きせず、正規 g2 を取得できるまで設計メモに留める / (b) 合成 g2 (temp commit) の正例を発火証拠と認めて実装を進める | (a)。(b) は合成試験だけが発火証拠として台帳に残る | 実装しても永久 fuse と観測的に区別できない実装が land する |
| C | **shell wrapper 側の pre-write をどう扱うか。** (a) 裁定 (5) の certified writer 閉包へ送る / (b) floor と T-126 の 2 本の shell を本 wave の scope へ入れる | (a)。(b) は Python 外の 2 言語へ gate を複製することになる | floor / T-126 を「最初の書込み前に保護した入口」と数えると被覆率の過大報告になる |
| D | **activation record 間の世代遷移規則。** 現プランは skip (g1→g3) と downgrade (g2→g1) と no-op record を無制約に受理する | 「各 env は据置または +1」を置く | serial が増えているのに新規 run の contract hash が旧較正へ戻る受理が通る |
| E | **authority loader の起動点。** import 時 HEAD 読取りは循環 import と T-126 の source stage で成立しない。(a) CLI 解析後の遅延 load / (b) 述語を共有 leaf へ抽出 | (b) を土台に (a) を併用 | 単位 A がそもそも起動しない |

## 本 wave で確定した副産物 (再裁定の材料。実装はしない)

- 依存 [T-574] は D196 の理由 (a) を充足させた。親が実 artifact で確認した実測 3 —
  合法な g2 を current にしても historical 経路は committed `output/s8b-freeze/floor_protocol.json` を
  受理し、記録 hash `e576e9cd` へ解決する。current 経路の拒否は D202 が意図した live admission の
  current 束縛であり proof chain の破壊ではない。**この 1 点だけは、依存 wave の
  「blocker は外れていない」という総括より狭く、かつ確かである。**
- 段 3 レンズが挙げた scope 内 real 所見のうち、実装したら直ちに効くもの:
  例外境界の翻訳 (lensB #8)、新 module の env-neutral AST 閉包 (lensB #9)、
  S8c C12 との非混同 (lensB #7)、identity 値が動く旨の明記 (lensA #5)。
  いずれも実装を再開する wave の brief へ引き継ぐ。
