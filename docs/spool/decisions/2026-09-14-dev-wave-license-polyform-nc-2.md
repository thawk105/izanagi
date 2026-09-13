---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-14
wave: dev-wave-license-polyform-nc
seq: 2
---

## {{D:license-polyform-noncommercial}}. izanagi 本体のライセンスを PolyForm Noncommercial 1.0.0 にする

**決定:** izanagi 自身が書いた成果物 (コード・ドキュメント・ツール・計測結果) は PolyForm
Noncommercial License 1.0.0 で提供する。本文は配布元の公式 plain text を逐語で `LICENSE.md` に置き、
先頭へ `Required Notice:` の 1 行だけを足す。submodule として取り込む第三者の著作物は適用範囲の
外に置き、その旨を README に書く。

**理由:**
- ユーザー裁定である。非商用の研究・検証・改変を認め、商用利用には個別の許諾を求めるという方針に
  そのまま対応する既製ライセンスが PolyForm Noncommercial 1.0.0 である。
- 大学・公的研究機関・非営利団体による利用が資金の出所を問わず許可対象に入ると本文が明示している。
  査読・追試・artifact evaluation を止めない。
- 本文を逐語で置くのは、ライセンスでは条項の同一性そのものが価値だからである。字句を足した時点で
  既製ライセンスではなくなり、受け取る側が条件を読み直さなければならなくなる。
- 第三者の著作物へ自分のライセンスを主張しないことは、外部から取り込んだものをデータとして扱う
  規律の帰結でもある。取り込んだ素材の条件は配布元が決める。

**却下した選択肢:**
- 非商用条項を自作する — 既製ライセンスの互換性と可読性を失い、解釈の負担を受け取る側へ押し付ける。
- Apache-2.0 / MIT — 商用利用を無条件で許すので方針に合わない。
- CC BY-NC — ソフトウェア向けに設計されておらず、特許の扱いも定めていない。
- 全 source file への SPDX ヘッダ一括付与 — 実装面の全 file を触るので本 wave の scope 外とし、
  必要なら別 wave で扱う。ライセンスの効力はファイル単位のヘッダに依存しない。
