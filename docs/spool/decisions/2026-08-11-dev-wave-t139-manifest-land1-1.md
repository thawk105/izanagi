---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-11
wave: dev-wave-t139-manifest-land1
seq: 1
---

## {{D:t139-record-items-and-second-erratum-approval}}. T-139 の再発行 record-items・受領証 schema・第 2 erratum の承認を機械可読 payload として固定し、D262 の `record_items` 承認を role 付きで前向きに失効させる

**決定:** 次の payload を canonical 台帳へ固定する。この payload を fold した commit を `F_r` と呼び、
後続 wave が発行する approval manifest は `F_r` を `approval_fold_commit` として literal で持つ。
**resolver は manifest を信用する前に、`F_r` の `docs/decisions.md` から本 payload を読み、
manifest の三つ組集合・erratum 順序・合成 digest・保証境界が本 payload と exact 一致することを
要求しなければならない** (manifest だけを trust root にすると、`approval_fold_commit` を保った偽 manifest が
自分の宣言値で自己整合してしまう)。

```text
decision_kind = t139-preregistration-approval-supersession/v1

forward_supersedes:
  D262.approved_blobs.record_items   (旧 blob は post-F_r manifest の record_items role では非承認)
  D263.reason                        (「同じ core に対する第 2 の erratum が既に承認済みである」の事実文)

preserved:
  D262 の target_core / addendum_a / derivation_map / erratum(t139-core-s15-exactkey-v1) の承認
  D263 の決定本文 (erratum_id 別 validator、未知 ID の fail-closed)
  D264 の gate 完成までの 4 名前非 export

target_core:
  path   = output/insights/2026-08-07_t139-mainrun-design/preregistration.md
  commit = 88d68f9127b31df5aafc3d59607896626a1652e8
  sha256 = ac939af4de87dff0cd3964e37cef975d57919a709d57f4e9523c8b6a9fcd60e9

approved_blobs:
  addendum_a
    path   = output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md
    commit = 622bd786191d40bda388596fa2adbf119ee84c9a
    sha256 = f7db96ce8ecb12359fedf56baea24939c629d4d16a1ec167c183425ea198cfec
  derivation_map
    path   = output/insights/2026-08-08_t139-r4-env-probe/derivation-map.md
    commit = 7ec088163dee920f0b8e1e9783faa6e36b22b730
    sha256 = bf5b6783b5a1a0b6c495618fe5292a968e44712d857cf84bdc436dcf027f6025
  erratum_t139_core_s15_exactkey_v1
    path   = output/insights/2026-08-08_t139-addendum-a/erratum-core-s15.md
    commit = 1d235e0e455020cf54e66cf83304961910c369d8
    sha256 = a1abc60ef8e3f4346f61fbdd8282c295f353ca272062af02a856e3c5de9dd6d3
  record_items
    path   = output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md
    commit = d0e7645192d56f429fc8d8a04f9c1776d50978d9
    sha256 = 61ba2f8b009ab6a17d657a5e3af3ce8a3afb251e3da664fc0117cd46a048a480
  receipt_schema
    path   = output/insights/2026-08-11_t139-manifest-land1/receipt-schema-v1.json
    commit = d0e7645192d56f429fc8d8a04f9c1776d50978d9
    sha256 = d541ccd5919c7c3545c04a806ca7f9cf04e6391cdf1791d7b9273317199b047e
  erratum_t139_core_s7_stresscheck_v1
    path   = output/insights/2026-08-11_t139-manifest-land1/erratum-core-s7-stresscheck-v2.md
    commit = d0e7645192d56f429fc8d8a04f9c1776d50978d9
    sha256 = deedd71b97640213035c76dac1b22ea15bb21d447991000b0e433de873684df2

erratum_application_order = [t139-core-s15-exactkey-v1, t139-core-s7-stresscheck-v1]
composed_sha256           = e0b0caeaca9300acffbb5cd6b81db7b6fb7fa8f9eeab81219affb4e2f94a8e0c

not_approved_as_record_items_root:
  path   = output/insights/2026-08-08_t139-addendum-a/record-items.md
  sha256 = 1957026c83db3486a39508a9aae07fd03ff5ac84d4edfc0d24b7051758f78fd3
  note   = D262 時点の承認記録は改変しない。ただし F_r 以後の T-139 approval manifest において
           本 blob は record_items role の承認対象ではなく、resolver はこれを拒否しなければならない。

operational_boundary = """
この保証は、指定された一つの canonical local main、その Git common directory、
tools/dev_wave_land.py を通り同一 land lock 下で取り込まれた予約履歴、およびその全履歴を
毎回再検査する trusted resolver / report の範囲に限る。独立 clone、別 common directory、
権威台帳外の投入、履歴を共有しない writer、同一権限の非協調 writer、canonical main の外で
作られた競合予約は保証しない。
"""
```

**理由:**

- **D262 は現行 record-items の digest を承認済み blob として固定しており、`F_e` より後に生まれた
  blob を `F_e` が承認することはできない。** ユーザー裁定 Q-A が求めた「record-items への承認済み修正」を
  実現するには、再発行版を承認する新しい decision を先に fold するしかない (2 段 land の第 1 段)。
- **旧 blob を「非承認」と一言で書くと、D262 の歴史的承認記録と矛盾する。** そこで
  `not_approved_as_record_items_root` として **role と時点を限定**した。旧 blob は D262 時点では
  承認済みであり、`F_r` 以後の manifest の `record_items` role では承認対象でない。
- **第 2 erratum は core の較正義務を 2 箇所 (221 行と 333 行) 置換する。**`較正` を含む行は
  凍結 core にちょうど 2 件あり、1 箇所だけの置換では「§7 = stress check、§14 = 較正」の
  二重状態が残る (絶対規律 3 が禁じる「保証していない性質を保証したと書く」)。
  合成 digest は親が凍結 core の blob から独立に算出し、適用順に不変であることも確認した。
- **承認済み追補 A の `a12` 見出し行に残る `較正` の語は据え置く。** 直後の本文が
  「本 field はその較正を与えない」と明記しており、受理集合を動かさない語の整合のために
  承認済み三つ組を組み替えると、digest を pin する payload と実装 pin が連鎖的に変わる。
  当該見出しは **legacy label であり較正の主張ではない**。
- **受領証 schema は JSON Schema draft-07 で発行する。** 実行環境の `jsonschema` は 3.2.0 で
  2020-12 の validator を持たず、repo の既存受領証 schema も draft-07 + `definitions` 形式である。
  dialect を実装に合わせないと、承認した schema をその時点の engine で検査できない。
- **本 payload は resolver が機械的に読める形で書く。** manifest だけを trust root にすると、
  `approval_fold_commit` を保った偽 manifest が自分の宣言値で自己整合する。台帳 → manifest の
  第 1 矢印を resolver の必須検査に含める。

**却下した選択肢:**

- 草案 (1 operation の第 2 erratum) をそのまま承認する — 置換後 core が二重状態のまま凍結される。
- 承認済み追補 A を再発行して `a12` 見出しも整合させる — 受理集合を動かさない語の整合のために
  承認済み三つ組と実装 pin を連鎖的に変える。壊すものが得るものより大きい。
- 受領証 schema を JSON Schema 2020-12 で発行する — 承認時点の検査実体が存在せず、
  engine の差 (`unevaluated*` の扱い) が受理集合を動かす経路が残る。
- D262 全体を失効させる — `target_core` / `addendum_a` / `derivation_map` / 第 1 erratum の承認は
  正しく、実装 pin も依存している。失効させるのは `record_items` role の 1 項でよい。
- 旧 record-items を無条件に非承認と書く — D262 の歴史的記録と矛盾する。
- manifest だけを trust root にする — 偽 manifest が自己整合する経路が残る。
