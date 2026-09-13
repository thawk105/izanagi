---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-14
wave: dev-wave-t1851-c3c-protocol-binding
seq: 2
---

## {{D:floor-allowlist-binds-resolved-protocol-exact-path}}. official 床値の許可表は resolver が選んだ protocol の実 path へ exact 1 件だけ束縛する

**決定:** 起動証明書の freeze allowlist は、legacy 固定 anchor `output/s8b-freeze/floor_protocol.json` へ
その file 自身の bytes hash を束縛し、**実行時に resolver が選んだ protocol の実 path** へ実行 protocol の
canonical hash を束縛する。両者が同じ path なら 1 entry に畳む。

allowlist の key として新たに受理してよいのは、**呼び手が渡した `protocol_relpath` と exact 一致する
1 件だけ**である。命名規則・正規表現・prefix 一致で受理してはならない。`protocol_relpath` は公開入口が
保持した authority record からのみ取り、下位関数が resolver を呼んで導出してはならない。新 keyword は
すべて既定 `None` とし、`None` のときの受理集合・分類・digest は変更前と 1 bit も違わない。

**理由:**

- D1111 の解決で protocol は世代別 namespace へ分かれたが、起動証明書の allowlist がその改版に
  追随していなかった。resolver が世代別 protocol を選ぶ限り、legacy file の bytes hash が
  resolved protocol の canonical hash と一致することは構造的にありえない。official 床値走行が
  一度も成功していない事実はこれで説明がつく。
- 同じ強度の検査を正しい対象へ向けるだけなので、受理集合は resolver の権威が既に固定した 1 path
  ぶんしか広がらない。族ごと受理する案は、選ばれていない世代別 protocol まで allowlist key として
  通してしまう。
- legacy anchor の bytes は、直前の `historical_protocol` 比較 (pre_oracle_head の Git blob との一致)
  が独立に押さえている。allowlist の legacy entry はその検査済み bytes を後続の 2 回の走査へ
  束縛する役割であり、**独立検証ではない**。

**却下した選択肢:**

- legacy 固定 file を現行 pin で再封印して両者を一致させる — 凍結 bytes を変えることになる。
- resolver を legacy 固定 path へ戻す — D1111 の解決を巻き戻す。
- 世代別 protocol の命名規則で allowlist key を受理する — 選ばれていない世代まで通る。

## {{D:private-core-official-seam-falls-back-to-legacy-anchor}}. 到達しない fail-closed を置くより、private seam は変更前の挙動を保つ

**決定:** campaign の private core は official 分岐で、authority record があればその実 path を使い、
**無ければ legacy anchor へ fallback する**。record 不在を理由に official を拒否する fail-closed は
置かない。公開入口に「record が非 None であること」の assert も新設しない。

**理由:**

- private core の非 test 呼び手は公開入口 1 箇所だけで、その入口は authority を解決できないときに
  例外を投げる。`None` が届く経路は monkeypatch だけである。したがって fail-closed は production で
  決して発火しない。**発火しない assert を足すことは、謳うだけで効かない保証を作ることである。**
- fail-closed を置いた初稿は、共有 fixture が official core を直接呼ぶ既存テスト 28 件を落とした。
  通すには fixture が authority record を捏造することになり、捏造した record を根拠に
  「実 path へ束縛した」と主張する形になる。これは正しさ検査の弱体化である。
- fallback が効くのは production が到達しない seam だけで、そこでの挙動は変更前と同一である。
  official の production 経路が実 path へ exact に束縛される性質は変わらない。

**却下した選択肢:**

- 共有 fixture 側へ authority record を配線する — 捏造した権威で gate を恒真にする。
- 公開入口へ非 None の assert を足す — 恒真である。
- 既存 28 件の期待値を変える — 正しさ検査の弱体化にあたる。
