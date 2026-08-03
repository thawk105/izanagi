# 段 4 裁定 補遺 (改訂 2) — 全 parent が trusted な merge の扱い

## 新事実 (本 wave の land を実測して判明)
本 wave 自身の land が `landed-fold-owned-path` で停止した。原因は merge `4c17674` の
**両 parent が tested main の祖先**であること (`ea6ca43` と `e805d69`)。
worktree を main から切った直後、wave の commit を 1 つも作らずに main を取り込んだためである。
現行規則の「trusted が 2 個以上なら fail-closed で全 parent 走査」に該当し、
main 自身の fold 署名を拾って拒否された。

**「main に追いついてから作業を始める」は完全に正規の wave 形である。**
これを禁止するのは F82 の同じ形の 4 度目 — 防壁の禁止集合が、守ろうとした正規経路を含んでいる。

## 改訂前の案を採らない理由 (実装子の指摘、real)
初版の補遺は「trusted parent の極大元を一意に選ぶ」を**無条件に**適用するとしていた。
これは fix round 3 で新設した既存テスト
`test_octopus_with_multiple_trusted_parents_rejects_signature_visible_only_from_untrusted_parent`
と矛盾する。同テストの parents は `(first_trusted, cutoff, untrusted)` で
`first_trusted` は `cutoff` の祖先、merge tree は cutoff の tree そのものなので、
極大元 `cutoff` との差分が空になり受理されてしまう。
既存テストの期待値変更は禁止であり、実装子は契約どおり停止した。

## 採る規則 (改訂 2)
極大 trusted parent の選択を、**全 parent が trusted のときだけ**に限定する。

```
if parent 数 < 2:
    commit 全体の差分を判定にかける (現行どおり)
else if cutoff が None:
    全 parent との差分 (現行どおり)
else:
    T = tested main cutoff の祖先である parent の集合
    if |T| == parent 数:                      # 全 parent が trusted = main 追いつき merge
        M = T のうち、T の他のどの要素の祖先でもない要素
        if |M| == 1: その 1 つとの差分だけ
        else:        全 parent との差分 (fail-closed)
    else if |T| == 1:
        その 1 つとの差分だけ (現行どおり)
    else:
        全 parent との差分 (fail-closed、現行どおり)
```

## 健全性
- 全 parent が trusted な merge は、main の履歴だけから作られている。
  唯一 wave が持ち込めるのは **merge 解決そのもの**であり、それは最も新しい trusted parent
  との差分に必ず現れる。fragment を消す・`FOLDED.md` を書き換える細工は拒否される。
- untrusted parent が 1 つでもある merge の扱いは**一切変えない**。したがって
  fix round 3 で新設した octopus 負例を含む既存テストは全て現行のまま通る。
- 「全 parent が trusted なら commit を丸ごと飛ばす」案は採らない。merge 解決の細工を
  見逃す fail-open になる。

## 追加するテスト
- **正例**: wave の commit を 1 つも作らずに main (fold commit を含む) を取り込んだ merge が
  受理される。両 parent が main の祖先で、片方がもう片方の祖先である形。
- **負例**: 同じ形 (全 parent が trusted) の merge で、wave が merge 解決により
  main に存在する fragment を削除する → 拒否される。
- **負例**: 全 parent が trusted だが極大元が 2 つ (互いに祖先関係にない) の merge に
  署名がある → 全 parent 走査へ落ちて拒否される。

## 追加する変異 (事前登録)
- **M09**: 極大元の選択を「`T` の先頭を採る」へ変異 → 2 番目の負例が緑になる
  (古い trusted parent を選ぶと削除署名が見えなくなる形にする)。
- **M10**: 極大元が一意でないときの fail-closed を「先頭を採用」へ変異 → 3 番目の負例が緑になる。
- **M11**: 「全 parent が trusted」の判定を「1 つ以上が trusted」へ緩める変異 →
  fix round 3 の octopus 負例が緑になる。
