---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-11
wave: dev-wave-t783-toolchain-binding
seq: 2
---

## {{D:toolchain-binding-scope-narrowed}}. toolchain 束縛は authority ↔ 実測の二者で先に land し、attempt 脚と成果物 report は返す

**決定:** 床値 build の toolchain 束縛は、registered calibration の `acquisition_receipt` を
derived authority とし、build 直前の実測値と照合する**二者**の形で先に land する。
裁定済みだった三者照合の第 3 脚 (投入 shell が採った attempt 実測値を driver へ渡す) と、
成果物 (manifest / result) への binding report 追記は**実装せず、新事実つきで再裁定へ返す**。

**理由:**
- **attempt 脚**: production wrapper の official 注入拒否は**引数名を明示列挙した dict** である。
  新引数を足すと、列挙に加えない限り**注入拒否を素通りする** — すなわち official 経路で
  caller が用意した toolchain 値を「実測」として受理する穴が開く。これは規律 2 に触れる。
  逆に列挙へ加えると、将来の正規 official は必須値を渡した瞬間に必ず赤になる。
  どちらも受理集合の設計判断であり、裁定時点では見えていなかった。
  さらに attempt snapshot を job 識別子 (PBS job / nonce / execution receipt / file hash) へ
  束縛する設計が無く、そのまま入れると caller 注入値を「実測」と記録する恒真な緑になる。
- **成果物 report**: 再凍結の authoritative consumer は manifest / result の top-level key を
  exact 集合で検査し、余分な key を必ず拒否する。追記すると生成した床値成果物が
  再凍結を通らず、oracle が binary を certified source として受理できなくなる。
  schema 改版と consumer 改修を同じ land に含める必要があり、裁定した scope を超える。
- 二者の形だけでも、**環境・世代をまたぐ床値の混用は build 前に止まる**。
  `acquisition_receipt` を持たない legacy calibration は receipt 不在で fail-closed に拒否される。

**却下した選択肢:**
- 三者照合を諦めて恒久的に二者にする — 「shell が記録した値と build が観測した値が食い違っても
  検出しない」を残すため、束縛を入れる動機と噛み合わない。**先送りであって放棄ではない。**
- attempt 脚を注入拒否の列挙へ加えずに足す — 正しさゲートを緩める方向であり、規律 2 で不可。
- 成果物 report を先に足して consumer は後で直す — 生成した床値が再凍結を通らない窓が開く。

## {{D:site-resolution-and-binding-land-together}}. 認可の解禁と束縛検査は同一 land に含める

**決定:** 床値 build の compiler 解決を site 依存化する変更 (fail-closed 障壁を外す側) と、
registered calibration に対する toolchain 束縛検査 (新しい障壁を置く側) は、
**同一 land に含める**。片方だけを land してはならない。

**理由:**
- 解禁側だけを land すると、床値 build が「認可されていない compiler で通る」状態になる。
  現状の障壁は事故ではなく現に効いており、これを外すだけの変更は受理集合を一方的に広げる。
- 束縛側だけを land した場合は安全側 (build は従来どおり倒れる) だが、
  分割 land の可否を裁定しないまま単位を分けると、順序を誤ったときに窓が構造的に開く。
- 検査を新設する wave では「実装しない場合」だけでなく
  **「単位を分割して片方だけ land した場合」に受理集合がどちらへ動くか**を先に問う必要がある。

**却下した選択肢:**
- 解禁を先に land し束縛を後続 wave へ回す — 窓が開く期間が生まれる。
- 束縛を先に land し解禁を後続 wave へ回す — 安全側だが、束縛が一度も発火しないまま
  land され、検出力を実測できない。
