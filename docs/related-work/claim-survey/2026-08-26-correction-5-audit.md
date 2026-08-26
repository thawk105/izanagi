# 2026-08-26 — 訂正 5 件目 (Polyjuice / CCaaLF の特徴づけ) の整合監査 (凍結)

- **作成日:** 2026-08-26
- **入力 commit:** `e29084e0` (本 wave の base)
- **入力 path:** `docs/paper-story/README.md` の「版の履歴」 /
  `docs/paper-story/2026-08-26.md` の「1. 何のプロジェクトか (一言)」 /
  `docs/paper-story/2026-07-10.md` の「3. 新規性の主張」 /
  `docs/related-work/README.md` の「7.1 並行性制御側の系譜」 /
  `docs/related-work/literature-map/izanagi_literature_map.md` の「柱1」 /
  `docs/related-work/literature-map/izanagi_literature_map.csv` /
  `docs/related-work/literature-map/gap-research-2026-07-10.md`
- **文献 cutoff:** 2026-07-10。Polyjuice / CCaaLF→NeurCC の改題・改名・採択・実装状態は
  `docs/related-work/literature-map/gap-research-2026-07-10.md` の同日の取得記録が最後であり、
  本監査では再取得していない。
- **規則の正本:** `docs/related-work/README.md` の
  「7.7 主張軸別の調査状態と、不在主張の成立条件」

> **凍結物である。** 書いた後は上書きしない。
> **`docs/paper-story/` は本監査でも一切変更していない** (同 README の凍結規定)。

---

## 0. 監査の対象

`docs/paper-story/README.md` の「版の履歴」は、2026-08-26 版が前版を訂正した箇所を 7 つ挙げる。
その 5 件目は次である。

> §1 — Polyjuice と CCaaLF を「policy table を出すだけ」と一括していたが、
> `related-work/README.md` は CCaaLF (v4 で NeurCC へ改名) を
> 「CC を学習可能関数としてモデル化」と記す。

**問い:** この訂正は、現在の `docs/related-work/literature-map/` と整合しているか。

**本監査での正本の順序 (先行研究の特徴づけという主題に限る):**
`docs/roadmap.md` の「8. 本システムの新規性 (ポジショニング)」が
「精密な先行研究との差分と優先権主張は `docs/related-work/` で管理する」と委譲しているので、
この主題については `docs/related-work/README.md` が正本である。
`docs/related-work/literature-map/` は自称「監査前データ」でその下位。
`docs/paper-story/*.md` は導出物かつ凍結物である。

**これは文書全体の優先順位ではない。** `docs/paper-story/README.md` が挙げる正典は
`docs/roadmap.md` §8 ・ `docs/decisions.md` ・ `docs/worklog.md` ・
`docs/phase3.md` と `docs/phase3-main-experiment.md` であり、
`docs/related-work/` はその一覧に入っていない。
別の主題で矛盾が起きたときに `docs/related-work/` を最上位に選んではならない。

## 1. 総合判定 — 二段に分かれる

- **訂正 5 それ自体は整合している。** `docs/paper-story/2026-08-26.md` §1 の記述は、
  正本 `docs/related-work/README.md` 7.1 の Polyjuice / CCaaLF→NeurCC エントリと同じ語で書かれている。
  訂正は正本に正しく合わせられた。
- **四者 (§1・正本 7.1・litmap の Markdown・CSV) を横断すると部分整合にとどまる。**
  litmap 側が、正本の作った語の区別を持っていない。

## 2. エントリ単位の判定

| エントリ | 判定 | 所見 |
|---|---|---|
| Polyjuice `2105.10329` | **不整合** | §1 と正本 7.1 は「事前定義したアクション空間の中での最適配合探索」に留まる、で一致する。一方 litmap の Markdown と CSV は「機械学習でワークロード特化型の並行制御アルゴリズムを**自動合成**し、既存手法を上回る性能を実現」と書く。**Izanagi が自らの新規性の核に置く「合成」という語を、そのまま Polyjuice に与えている。** 配合探索とアクション空間の拡張の境界が消える |
| CCaaLF→NeurCC `2503.10036` | **部分整合** | §1 と正本 7.1 は「CC を学習可能関数としてモデル化し、関数近似へ一般化」で一致する。litmap の「機械学習で CC 関数を学習し、多様なワークロードに最適化された並行制御を**自動設計**する」は直接の矛盾ではないが、Polyjuice との差を保存しない粗い要約である |
| ATCC `2603.13906` | **整合** | 訂正 5 の直接の対象ではない。正本・litmap・CSV とも「未知・エージェント的ワークロードへの適応」で一致する |
| Declarative Concurrent Data Structures `2404.13359` | **判定不能** | litmap の Markdown と CSV には柱1 として存在するが、正本の逆引き索引にも 7.1 本文にも現れない。採録を却下したのか未処理なのかを示す記録が見つからない。凍結物側は変更せず、未解決事項として残す |

**litmap の Markdown と CSV は同じ要約を複製している。両者の一致は独立した裏取りではない。**

## 3. なぜこの語の差が危ないのか

`docs/paper-story/2026-08-26.md` §3 の軸 1 は、Izanagi と先行との質的な差を
**「アクション空間自体を LLM が拡張する」**点に置いている。この差は、
先行が「事前に開かれた空間の中を探索する」側にとどまることを前提にして初めて成り立つ。

litmap は Polyjuice を「自動合成」と書く。もし positioning の執筆者が
`docs/related-work/literature-map/` を直接引けば、**先行も合成していることになり、軸 1 の新規性の核が消える。**
`docs/related-work/literature-map/README.md` は自らを「監査前データ」と宣言し、
「取り込み・引用の前に必ず監査すること」と定めているが、
**この 1 語がどう危ないかは書かれていなかった。** 本 wave で同 README に警告を足した。

**なお、これは litmap の誤りではない。** litmap は横断掃引の一次生成物であり、
1 行の日本語要約に正本の語の区別を負わせる設計ではない。
危ないのは **litmap を正本の語彙として引くこと**である。

## 4. 名前で引けない採録 — 再発防止

**CCaaLF は `docs/related-work/literature-map/` に採録されている。** ただし v4 で改題された後の題名
`Modeling Concurrency Control as a Learnable Function` で載っており、
`CCaaLF` や `NeurCC` の語では Markdown も CSV も引けない。

`docs/related-work/literature-map/gap-research-2026-07-10.md` が改題と改名の経緯を記録している —
arXiv `2503.10036` は v1 (2025-03-13) の題名 `CCaaLF: Concurrency Control as a Learnable Function`
から v4 (2026-03-10) で改題され、システム名も NeurCC へ改名、
PACMMOD Vol.4 Issue 3 (SIGMOD 2026) に掲載。

**この取りこぼしは名前で引いたことが原因である。** 対策は `docs/related-work/README.md` 7.7.6 に規則として入れた —
主キーを arXiv ID または DOI とし、旧題・新題・略称・改名前後のシステム名を同じ alias レコードに
束ね、題名一致だけの重複除去を禁じる。

## 5. 前版に残っている記述

`docs/paper-story/2026-07-10.md` の §3 軸 3 は
「**policy table しか出せない先行**に対し」と書いている。これが訂正 5 の対象そのものである。
同じ版の §3 軸 1 には「先行なし」「系譜の 3 本目」という撤回済みの主張も残っている
(`docs/related-work/claim-survey/2026-08-26-inventory.md` の 4 節)。

**凍結物なので書き換えない。** 矛盾したら新しい版と正本が勝つ。

## 6. この監査の限界

- **repo 内の語彙整合だけを判定した。** 各論文が原文で「synthesis」「design」をどう定義したかは
  再監査していない。Web 取得を行っていないためである。
- **外部の現況を再確認していない。** 改名・採択・実装リポジトリの状態は
  `docs/related-work/literature-map/gap-research-2026-07-10.md` の 2026-07-10 時点の記録のままである。
  現在まで約 1 か月半が経っており、**鮮度を確認したとは言えない。**
- `2404.13359` の採録判断は判定不能のまま残る。
