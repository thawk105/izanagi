---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-13
wave: dev-wave-a1-sizing-certificate
seq: 2
---

## {{D:a1-sized-policy-freeze}}. A-1 balanced5 の本走 policy は非認証 lane のまま凍結し、証明書の登録値は consumer が照合する

**決定:** A-1 balanced5 の本走 policy を次の形で凍結する。

1. `authority.formal=false` / `promotion_prohibited=true` / `final_estimate_eligible=true` とする。
   後者は「本走の観測値が登録済み解析の対象になる」という意味であり、投入の認可でも正式な結果への
   昇格でもない。この限定を事前登録の本文に書く。
2. 本走 policy の bytes を module 定数で pin する。既存の v2 と pilot にある機構を sized へ
   対称適用するだけとし、新しい gate 機構は作らない。
3. sizing 証明書が申告する試行回数・候補範囲・root seed を、consumer が事前登録の値と型込みで
   exact 照合する (D1452 の consumer 側)。照合は既存の workload / n / df / k / sigma の検査の後に
   置き、既存の拒否理由の優先順位を変えない。**道具側は変更しない。**
4. sized の `k` と `planned_sigma_tps` は証明書が出す十進文字列を逐語で受け取る。数値へ丸めない。
   受理の条件は、Decimal として正で有限であることに加え、float へ変換しても有限かつ正であること。
5. 本走の schedule root seed は pilot のものを使い回さず、原像を先に固定した別系列とする。
   事前登録には「pilot 完走後・本走投入前に新規に凍結した」と書き、pilot より前から凍結済みで
   あったとは書かない。

**理由:**

- `formal=false` は設計上の選択ではない。非認証 lane の identity 検査 2 箇所がいずれも独立に
  `formal is False` と `promotion_prohibited is True` を要求しており、`true` を名乗る policy は
  campaign の identity 検査で拒否される。policy の bool を反転すれば正式 lane へ移れる実装ではない。
- policy hash を返さない分岐が sized にだけ残っていたため、人間可読の事前登録の hash を変えずに
  disk 上の seed・出力先・証明書参照を差し替えられた。凍結と呼べる状態になっていなかった。
- 証明書は試行回数と候補格子を記録しているが、突き合わせる側が無かった。候補上限を 1 だけ下げても
  実現候補列は変わらず、選ばれる反復数も変わらないため、登録範囲と異なる設定で決めた証明書が
  既存の検査をすべて通る。文面の断り書きはこの穴を説明するだけで塞がない。
- 証明書の sigma は 17 桁の十進文字列であり、JSON 数値へ落とすと最短表現になって exact 照合に
  落ちる。数値を要求したままでは、本番の証明書と一致する policy をそもそも書けない。
- 文字列を許すと Decimal 上の正値判定だけが残り、float へ変換すると 0 になる値が通る。
  区間の半幅が 0 になる policy を受理しうるため、変換後の条件を残す。
- 本走の seed を pilot と共有すると、同じ組番号の順序 bit が共有され、短い本走の系列が pilot の
  先頭部分と重なりうる。別系列にすることでこの共有は避けられるが、測定値の独立性や残留効果の不在を
  保証するものではない。この限定も本文に書く。

**却下した選択肢:**

- **`formal=true` を名乗って凍結する** — 非認証 lane の identity 検査で拒否される。
  実装に裏付けの無い正式性を宣言することにもなる。
- **道具側で試行回数と候補範囲を強制する** — 道具は凍結済みであり、本走のデータを読む前に
  固定した受理範囲を後から狭めることになる。照合は consumer 側で閉じる。
- **文面で「道具が強制する値ではない」と断るだけに留める** — 拘束が発火しない。
- **証明書の十進文字列を数値へ丸めて policy へ書く** — exact 照合が落ちる。
  照合を緩めて float 比較にすれば、17 桁目の差を見分けられなくなる。
- **pilot の root seed を本走へ流用する** — 順序 bit が共有される。
- **本走の実行面まで同じ単位で整える** — source 契約・hydrate 入力・staging・source binding の
  生成箇所・amended build の受理形が pilot 専用のまま残っており、1 箇所の限定解除では足りない。
  証明書と policy の凍結とは別の単位で扱う。
