---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-17
wave: dev-wave-t1279-layer3-head-outside-repo
seq: 2
---

## {{D:layer3-head-fallback-order}}. 層 3 材料レポートの生成元版は campaign の git HEAD を先に見て、repo 外でだけ lock の pin へ退避する

**決定:** `meta.generated_from_head` を呼び手が渡さないときの解決順を次で固定する。

1. 明示引数があれば無変更で使う。
2. campaign directory の git HEAD が取れればそれを使う。
3. 取れず、かつ campaign が生成器 source repo の**外側**にあり、campaign lock が authority を
   持つ v2 なら、その `contract_loader_commit` を使う。
4. それ以外は fail-closed で送出する。

certifying 入口 (受領証に束縛されたレポート生成) では 3 を使わない。呼び手が値を渡さない場合は
生成前に campaign の git HEAD を要求し、wave 前と同じ受理集合を保つ。

**理由:**
- この field が答えるべきは「この report を生成したコードの版」であり、campaign 置き場の版ではない。
  両者はたまたま一致していただけである。
- lock の pin は lock 作成時点の版であって再生成時点の版ではない。lock を先に見ると、repo 内の
  v2 campaign で値が現在版から作成時版へ変わる。これは指示されていない挙動変更である。
- 版の権威を厳密に定めることに費用を払わないことは既に確定している。ここで求められているのは
  「repo 外でも倒れないこと」だけであり、粗い版が分かれば同じコードを再現できる。
- certifying は指示の対象外である。指示された緩和が自動的に波及するのを許すと、正しさの門を
  意図せず緩めることになる (規律 2)。

**却下した選択肢:**
- lock の pin を git HEAD より先に見る — repo 内 v2 campaign で official の値が変わる。
- 生成器自身の位置 (`__file__`) から repo HEAD を取る — packaging 次第で無関係な repository の
  HEAD を静かに拾う。値の意味が曖昧になる方向であり、粗い provenance という要求より悪化する。
- 呼び手側で値を渡させる — 同じ穴を持つ他の入口 (受領証束縛の生成、CLI、直接の render) が
  取り残される。
- 明示引数に版形式の検査を足す — 既存 API は非版形式の文字列を受理しており、これを縮めるのは
  求められていない厳密化にあたる。
