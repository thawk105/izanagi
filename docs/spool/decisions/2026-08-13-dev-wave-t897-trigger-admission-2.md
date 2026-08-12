---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-13
wave: dev-wave-t897-trigger-admission
seq: 2
---

## {{D:trigger-axis-gate-validates-bytes}}. trigger 軸の semantic admission は block の bytes だけを検証する

**決定:** build gateway の trigger 軸検査は、marker block (BEGIN 行頭〜END 行末) の bytes が
凍結 template と逐語一致するか、hole 1 行だけが emitter の 32 出力のいずれかと exact 一致するかを
判定する。**block が生きた C++ かは検証しない。** 自前の C++ コメント字句解析は持たない。
file 全体の BOM / NUL / UTF-8 decode 検査も持たない。

**理由:**
- 実装当初に置いた自前字句解析は、敵対レビューの静的追跡で**両方向に誤る**ことが実証された。
  raw string の payload と行継続を認識しないため、(a) raw string 内の偽 block を実 block として
  受理し、(b) 正当な source の `/*` を未終端コメントと誤認して受理集合内の source を拒否する。
- **過剰拒否は正当な build を止めるため、fail-open と同等以上に有害である。**
- 正確な C++ 字句解析 (翻訳フェーズ 1〜3・raw string・行継続・trigraph) は 1 検査の付随物として
  持つには大きすぎる。誤った字句解析を残すのは、謳うだけで発火しない保証と、誤爆する保証の両方を
  同時に抱えることである。
- block **外**の C++ 意味論は、同 wave の段 4 で既に scope 外と裁定していた。コメントによる
  block の無効化も raw string 内の囮も block 外の C++ 意味論であり、同じ区分に属する。

**却下した選択肢:**
- 自前字句解析の改良 — raw string と行継続だけ足しても翻訳フェーズ全体としては不正確なままで、
  「どこまで正しいか」を主張できない。
- file 全体の BOM / NUL 拒否の維持 — 凍結 block と完全一致する source を block 外の 1 byte で
  拒否する。裁定した受理集合より狭く、過剰拒否である。

## {{D:frozen-skeleton-identity-is-in-the-language}}. 骨格の単位元を受理言語に含める

**決定:** trigger 軸の受理言語は、生成器が出す 32 述語に加えて、凍結 template が持つ hole の
初期値 (`izanagi_gate_pass = true;`) を含む。ただし初期値を受理するのは **block 全体が凍結
template と逐語一致する場合に限る**。

**理由:**
- 生成器の 32 述語は要因 8 種のうち 5 種と番兵しか覆わない。残り 2 種に対して全ビット立ての
  述語は「抑制しない」を返し、初期値は「抑制する」を返すので、**意味が一致する代替は存在しない**。
- 「その 2 種が実際には発火しない」ことこそ characterization driver が測る対象なので、
  全ビット立てで代用すると測りたい前提を答えに使う循環になる。
- したがって初期値は 33 番目の候補ではなく**骨格の単位元**であり、受理言語に含めることは
  候補空間の拡大ではない。
- 検査導入前は gate 自体が存在せず全 source が受理されていたため、新受理集合はその真部分集合である。

**却下した選択肢:**
- 初期値を一律拒否する — 骨格の特性計測 driver 2 本を恒久的に再走不能にする。正しさの利得はゼロで
  研究能力だけを失う。
- 生成器の登録簿へ characterization 専用 member を足して型で分離する — 登録簿は受入方針の
  preimage に含まれ、方針ハッシュは全 admission receipt の field である。**member を 1 つ足すだけで
  過去・現在の全 receipt の SHA が変わる**ため、凍結 pin 閉包の全面移行なしには実装できない。
