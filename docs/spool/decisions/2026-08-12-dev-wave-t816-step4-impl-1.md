---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-12
wave: dev-wave-t816-step4-impl
seq: 1
---

## {{D:frozen-evidence-historical-binding}}. 凍結証拠の binding が pin 前進で動いたら、bytes でなく期待側を歴史 golden へ分離する

**決定:** submodule gitlink や patch の base commit を前進させた結果、凍結成果物が sha256 で
束縛している対象 (driver source、policy、verifier module、patch ledger、patch 適用後 source 等) が
現行値と食い違うようになったとき、**凍結成果物の bytes は書き換えない**。検査側を次の形へ分離する。

1. 記録済みの historical hash を定数として固定し、凍結側の binding がそれと一致することを assert する。
2. **同時に、現行ファイルから再計算した値と一致しないことも assert する。**
3. 凍結成果物の内部で自己整合している assert (raw manifest・seal・provenance の相互参照) は
   現行のまま残す。

現用性の判定は「consumer が存在するか」ではなく「**consumer が何を要求しているか**」で行う。
新しい pin を要求する consumer と、記録済みの**旧 bytes** を要求する consumer は同居しうる。

**理由:**
- (2) がないと「drift を黙って許す」形になり、凍結証拠が現在の木と無関係になった事実が
  検査から消える。drift 自体を固定すれば、逆方向の事故 (凍結側を書き換えて現行と一致させる) も赤にできる。
- 凍結 bytes を書き換えると、既に certified された結果の proof chain を別物に差し替えることになる。
- 2026-08-12 のユーザー裁定は、bytes 級 provenance 機構 (恒久の同一性証明・pin 集合を受理する gate) の
  新設を否決している。本形式は機構を新設せず、期待値の置き場所を変えるだけである。

**却下した選択肢:**
- 検査を削除して通す — 正しさシグナルの後付けにあたる。
- 凍結 bytes を再 pin する — 旧 bytes を hash で束縛している下流 (移行 receipt、holdout freeze、
  oracle driver) を同時に壊す。閉包を追うと凍結 seal の書き換えまで波及する。
- pin 集合を受理する gate を作る — 恒久の同一性証明機構であり、ユーザー裁定が否決した。
