---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-27
wave: dev-wave-t1805-predicate-exec-proof
seq: 2
---

## {{D:predicate-execution-proof-placement}}. 宣言と実体の照合は規範的に行い、関門は build 実装の内側へ置く

**決定:** D966 が求める「宣言した述語が build と実走へ届いた証明」を次の 3 層で構成する。

1. **関門**は `buildcache.build_v2` の内側に置く。宣言由来の参照実体化 → 実体化 tree との
   exact 照合 → snapshot の非書込化 → snapshot からの証拠再導出 → 呼出側証拠との全体一致。
   宣言記述子が渡ったときに発火し、渡らなければ変更前と厳密に同じ挙動を保つ。
2. **証拠の要求**は binary admission receipt の発行と中央検証に置き、**無条件**とする。
   証拠を欠く binary は receipt を発行できず、receipt の無い binary は consumer 全経路で拒否される。
3. **campaign コードは値を通すだけ**とし、証拠について何も要求しない。

非到達化と別変数による実効分岐は、意味解析ではなく**実体化 tree 全体を宣言由来の期待 tree と
exact 一致させること**で閉じる。実体化は (pinned commit + template patch + 正準述語) の
決定的関数なので期待値が導ける。

**理由:**
- 既存の証拠は観測値を記録するだけで、宣言から導いた期待値と照合する経路が無かった。
  欠けていたのは解析能力ではなく照合先である。規範的照合にすれば、prologue への `return;` 挿入も
  変数の shadowing もコメント化も header 改変も、すべて tree の差として落ちる。
- 単体テストは実 build を注入で差し替える。実 I/O を要する関門を campaign コードへ置くと、
  それらのテストが必ず落ちる。関門をテストが差し替える境界の内側に置けば、
  実 build を飛ばすテストは関門も一緒に飛ばす。これは正しい対応関係である。
- 証拠の要求を campaign 側にも重ねると、receipt 境界の要求と冗長になるだけで守りは増えず、
  実 build を差し替えるテストを壊す。

**却下した選択肢:**
- 差分 build witness (2 値で build して binary bytes の差を見る) — 述語が実走した十分条件でも
  必要条件でもない。非到達 code でも binary は変わりうるし、正当な 2 述語が最適化で同値化すれば
  同じ binary になる。段 2 と段 3 レンズ A が独立に棄却した。
- 関門を共有実体化器や identity 合成器へ置く — 実測で 3 度失敗した。
- 証拠を共有 build 器の必須引数にする — S8b と無関係な campaign の可用性を奪う。

## {{D:evidence-requirement-only-at-receipt-boundary}}. 実 build だけが作る値への要求は receipt 境界にだけ置く

**決定:** compiler input manifest・snapshot digest・期待実体化 digest のような
**実 build だけが生成する値**への要求は、receipt の発行と検証の境界にだけ置く。
campaign コードと共有 build 器には置かない。共有 build 器へ足す引数は既定値ありとし、
未指定時は変更前と厳密に同じ挙動 (cache identity の preimage に key を足さないことを含む) にする。

**理由:**
- 「条件付きで検査する」と「検査を外せる」は違う。関門は receipt 境界で無条件に立っており、
  証拠を欠く binary は receipt を発行できない。共有 build 器を条件分岐させても主張は弱まらない。
- 必須引数にすると、S8b と無関係な既存 campaign が呼出し時点で落ちる。これは受理集合の縮小では
  なく可用性の喪失であり、certified 値が誤るのではなく生成できなくなる。
- 未指定時に cache identity の preimage へ key を足すと、既存 cache entry が全件 miss になる。

**却下した選択肢:**
- 共有部品でも無条件に要求する — 上記のとおり他 campaign を止める。
- campaign 側にも重ねて要求する — receipt 境界と冗長で、守りが増えないままテストを壊す。

## {{D:compiler-input-inside-outside-split}}. compiler input は snapshot 内外で扱いを分ける

**決定:** compiler が読んだ入力のうち、**snapshot 内のものは bytes 一致を要求**し、
**snapshot 外のもの (system header、libstdc++、外部依存の header) は hash を manifest へ
記録するが在籍は要求しない**。加えて EVOLVE-BLOCK source が snapshot 内に在り、その bytes が
build 前後で不変であることを要求する。

**理由:**
- 実測した depfile には system header と外部依存 header が必ず現れる。全入力を snapshot 内へ
  要求すると正当な全 cell が拒否され、成果物が 1 件も生成されない。
- 「宣言 source が依存一覧に載っている」だけの検査は、build が成功している時点で target 定義から
  必ず真であり恒真である。bytes 検査だけが実質を持つ。

**却下した選択肢:**
- 全入力を snapshot 内へ要求する — 正当な build を全件拒否する。
- 在籍だけを検査する — 恒真であり、防壁として数えられない。
