---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-16
wave: worktree-dev-wave-t1142-oracle-n-pilot
seq: 1
---

## {{D:oracle-n-indifference-zone}}. 8b oracle の n は indifference-zone で事前登録し、単一値でなく n(δ, α) を出す

**決定:** 8b oracle の `n` を決めるための誤選択率は、**真の best より相対 δ を超えて劣る
configuration を選ぶ確率**と定義する。δ 以内の差しかない configuration を選ぶのは誤りに数えず、
`tie` verdict も誤りに数えない (tie 率は別欄で報告する)。目標は
δ ∈ {0.5%, 1%, 2%, 5%} × α ∈ {0.05, 0.10} の**格子として事前登録**し、
pilot の出力は単一の `n` ではなく**表 `n(δ, α)`** と各点の片側 Wilson 上側信頼限界、
全 candidate の合否列、非単調 flag とする。`n` の選択は
「その candidate 以上の全 candidate が合格する最小の n」とし、単調性を仮定しない。

**理由:**

- 実装されている判定は holdout ごとの 6 configuration の median-of-medians +
  float 完全一致 argmax である。真の順位を入力に取らないので、素朴な「誤選択率」は定義できない。
- 連続ノイズ下では、全 configuration が同性能でも有限標本の完全一致 argmax はほぼ必ず
  唯一勝者を返す。「false unique-best を誤りと呼ぶか」で誤選択率が 0 と 1 の間を反転する。
- δ を宣言すると両方の逆理が同時に消える。拮抗は定義上「誤りでない」となり、
  誤りは実用上の損失としてだけ数えられる。
- 先行 wave は「同じ仮定の変奏で必要な n が 7 から 14 まで振れる」と記録した。振れの原因は
  **宣言されていない仮定**である。格子として宣言すれば、答えが振れるのは宣言済みの
  (δ, α) の違いによってだけになる。**同じ (δ, α) なら同じ n が出る。** これが
  「n を統計的に導出可能にする」ということの内容である。
- 単一の (δ, α) を選ぶ判断は集約規則の再凍結に従属するため、pilot では選ばない。

**却下した選択肢:**

- **全標本 argmax との一致率 (選択不安定率)** — 真値を仮定せず測れるが、
  これは pilot 内の安定性であって誤選択率ではない。単独では n の根拠にならない。
- **検出力** — 真の差の大きさを仮定しないと書けない。仮定を置けば
  「宣言されていない仮定で答えが振れる」元の問題に戻る。
- **単一 δ の即決** — 実用的同等幅を選ぶ根拠が現時点で無い。
  根拠なく 1 点を選ぶと、以後の n がその 1 点に暗黙に束縛される。

## {{D:oracle-n-pilot-lower-bound}}. pilot の n は下限として宣言し、条件付けを成果物へ刻む

**決定:** pilot が出す `n(δ, α)` は**下限**であると出力 schema に持たせ
(`status: "lower-bound"`)、`all-rows-eligible` / `three-allocations` /
`exact-pin-and-binaries` の 3 条件を `conditioning` として同じ成果物へ刻む。
allocation は 3 本へ均等分割し、allocation 差は**有無と向きだけ**を報告する。
分散成分の推定にも上側信頼限界にも使わない。

**理由:**

- 実 judge は各 row の verify / eligibility 状態も見るが、pilot は throughput しか集めない。
  したがって得られる誤選択率は「全 row が eligible」条件下の値であり、
  **certified error rate と呼んではならない。**
- 同一 allocation 内の連続 round は cold-boot・温度ドリフトを含まない**下限**である
  (既存の between-run floor driver が同じ注意を明記している)。
  下限の分散から導いた n は必要量を過小評価する。
- K=3 では allocation 変動の自由度が 2 しかない。ここから分散成分や上側信頼限界を作ると、
  精度の見かけだけが上がる。**測れないものを測ったことにしない。**
- noise 分布が ccbench pin に対して不変という仮定は未検証である。結果を pin と
  binary SHA に条件付ければ、後続がその前提を検査できる。

**却下した選択肢:**

- **allocation を 1 本にする** — 母集団が単一割当に閉じ、割当間差の有無すら分からない。
- **allocation を 5 本以上取る** — 分散成分の推定には要るが、pilot の費用範囲を超える。
  必要になった時点で独立 campaign として起こす。
- **下限であることを注記だけに留める** — 下流が schema しか読まない場合に失われる。
  機械可読な状態として持たせる。

## {{D:pilot-artifacts-stay-out-of-repo}}. holdout を測る driver は成果物を repo 外へ出し、書込み前に三軸 gate を通す

**決定:** holdout workload を実測する driver は、測定 artifact を repo 外の output root へ書き、
repo へ commit するのは三軸 conjunction を含まない要約だけとする。JSON / Markdown / spool の
唯一の writer に `holdout_conjunction_hits` を書込み前 gate として通し、汚染時は
destination も親 directory も作らない。driver source に workload 値を書かず freeze から読み、
test の汚染 payload は `HOLDOUTS` から実行時に組み立てる。

**理由:**

- `measure_point` は workload dict をそのまま CLI flag へ展開するため、`ScalePoint.run_cmd` は
  三軸 conjunction を必ず含む。既存の between-run floor driver は run_cmd を JSON と Markdown の
  両方へ書いており、**同じ形を holdout workload へ流用すると書いた瞬間に repo が汚染される。**
- 汚染すると floor / oracle の launch certificate の clean scan が**恒久的に**赤になり、
  本走が起動不能になる。`enumerate_repository_files` は untracked も列挙するので、
  一時ファイルでも成立する。
- 除外領域は凍結ディレクトリだけであり、そこは書込み禁止領域でもある。逃げ場は repo 外しかない。
- 未知性 gate は**literal hygiene** であって計測事実の台帳ではない。両者を混同しないよう、
  driver は計測の申告を別 field (`measurement_declaration`) として持つ。

**却下した選択肢:**

- **run_cmd を hash 化して保存** — 再現には freeze SHA・cell ID・binary SHA・環境契約で足り、
  hash を置く必要がない。置けば「復元できるのでは」という誤解だけが残る。
- **凍結ディレクトリへ出力** — そこは除外領域だが writer が拒否する保護領域でもある。
- **書き手の注意に委ねる** — 「気をつける」は gate ではない。機械検査にする。
