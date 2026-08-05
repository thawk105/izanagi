---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-06
wave: dev-wave-t532-name-mask-binding
seq: 2
---

## {{D:trigger-name-mask-forward-authority}}. trigger record の期待名は emitter の正引きで決め、逆文法パーサを作らない

**決定:** 凍結文書の trigger record について `name` と `gate_predicate` の一致を検査するとき、
期待値は次の**正引き**で得る。

1. 述語 → mask (`trigger_gate_binding.mask_for_canonical_predicate`、32 正準述語の逆 index)
2. mask → 要因部分集合 (`GATEABLE_REASONS` の bit 順)
3. 要因部分集合 → 正準名 (`s8a_trigger_sweep.subset_name`)

`g_rl` のような名を文法として逆パースする実装は作らない。名の権威は emitter 側にあり、
検査側が文法を二重実装すると drift する。

`ident_all` は全要因 mask の明示 alias として index へ登録する。全要因 mask には
`subset_name` が返す通常名と `ident_all` の 2 つの正当な名があり、configuration 固有の名称制限は
加えない。それは name↔mask 一致を越える schema 拡張になる。

**emitter 名の単射性は仮定せず検査する。** mask 0〜31 の全点で index を構築し、同じ名が 2 つの mask へ
現れたら fail-closed で止める。alias が既存名と衝突する場合も止める。

**index の構築は初回検査呼出しまで遅延し、成功時だけキャッシュする。** module 読み込み時に構築すると、
失敗が consumer の構造化拒否境界より前に出て raw import traceback と pytest collection error になる。
遅延すれば各 consumer の既存例外境界の中で拒否として現れる。

**非 str の `name` は membership より先に exact 型検査で拒否する。** membership は `__eq__` を使うため、
`__hash__` / `__eq__` を偽装した object が正準名と等価に見える。述語側は既に exact `str` を要求しており、
名側だけ緩いのは非対称である。**この拒否経路の診断では対象 object の `repr` を呼ばない** —
f-string の `!r` は例外構築より先に `__repr__` を実行するため、`__repr__` が例外を送出する入力で
一様な拒否例外を送出できなくなる。

**理由:**
- 期待名の権威を emitter に一本化すると、名の文法が変わっても検査側の追随が要らない。
- 単射性を仮定して正引きすると、略称が衝突した将来の emitter で同じ名が 2 つの mask を指し、
  「name が指す mask」が一意でなくなる。仮定は検査で置き換える。
- 遅延構築は fail-closed 性を落とさずに診断の構造を保つ。import は副作用の場所として不適切である。

**却下した選択肢:**
- 名の逆文法パーサ — 略称表の二重実装になり、emitter との drift を検出できない。
- 期待名表のハードコード — 現行 3 名だけを固定する実装が全テストを通ってしまい、
  他の mask を過剰拒否する欠陥を検出できない。
- 検査 helper を `trigger_gate_binding` へ置く — 同 module は WAL・pipeline・loop から import され、
  emitter は pipeline を import するため循環する。
- module 読み込み時の index 構築 — 上記のとおり consumer の拒否境界を壊す。
