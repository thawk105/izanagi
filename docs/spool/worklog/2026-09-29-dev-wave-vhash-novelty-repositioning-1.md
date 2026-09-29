---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-29
wave: dev-wave-vhash-novelty-repositioning
seq: 1
title: [T-2873] VHash 論文の新規性を置き直した — 近い 8 方式と本案を同じ記法で書き分け、主張との対応を先に固定した検索を OpenAlex・arXiv・DBLP で全件判定した。U2 (前向きに非最新版を選ぶ) は既知へ移り、新規性の主張は U0 (実行中の前進を保護下限へ反映する機構) と U1 (cold 契機) に置き直した。範囲つきの主張文の候補 3 案と取り寄せ一覧を一次資料に置いた (insight のみ、branch dev-wave-vhash-novelty-repositioning)
---

## 本文

- 依頼: 並行 VHash wave の md_9 (`/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_9.txt`)。一次資料は `output/insights/2026-09-29/vhash-novelty-repositioning/README.md`。
- マネージャー役のセッションからの伝達 (09:4x): ユーザーは「新規性が強い」と見ている。U0・U1・U2 の組合せを本命の強い形で書き、弱めた代替案は従に。ただし範囲つき・事前登録・形式的書き分けの規則は変えない。→ 主張文候補の並べ方 (一次資料 §7 の案 A を本命) にだけ使い、判定規則は変えなかった。
- 結論の要点: CockroachDB (SIGMOD 2020 の read refresh) と SI-STM (TRANSACT 2006) は登録検索の外 (親の知識による補助探索) から見つかり、本案 (2) の「前向きに進んで非最新版を選ぶ」を既知にした。これらを md_1 は拾っていなかった。
- 段 6 review は NO-GO 6 件 (Hekaton を前進と誤分類、U1 の不在文に OCC-TI の未裁定、主張文に cutoff なし、SI-STM が保持短縮の目的を既に述べる、保持の打ち切りの言い過ぎ、再走規則の時点) で全件 real。焦点再レビュー 1 巡目は closed 3・partial 3・新規 3 (主張文の cutoff の書き方ほか)、2 巡目は closed 6・新規 3 (§0・§5.2 の不在文の cutoff、§6 の件数、OCC-TI と U1)、3 巡目 (上限) は closed 2・partial 1・新規 2 (fragment の題の短縮、SI-STM の保持規則の一般化、未読 2 本の影響の断定)。いずれも real で、3 巡目の残りは DW-O16 に従い再レビューを重ねず親が修正して grep で閉じた。
- 登録の不備 2 点 (一次資料 §4.1・§5.2 と `search-registration.md` に記録、登録は書き換えていない): U2 の検出条件が md_1 の文から「hot」を落としていた (どちらの読みでも結論は同じ)、登録前の構文確認の件数の数え違い。
- OpenAlex の匿名利用は負荷時に 429 を返し、1 走目で 3 式が未完走になった。N01〜N07 と arXiv の取得後、N08〜N10 がまだ結果未取得の時点で再走規則を登録へ追記し (式・対応・判定規則は不変、再走規則そのものは事前登録ではない)、再走して完走した。arXiv の陽性対照 (Shirakami) は登録語の取りこぼしで出なかった (診断 request 2 本で原因を確認)。
- DBLP の検索 API は依然 bot 判定のため、全件書き出し (1.1 GB) を取り込み、題名を手元で照合した (照合器は Codex author、repo 外)。
- 判定: 全 hit 368 件 (索引固有 ID、OpenAlex 319・arXiv 25・DBLP 24) を親が直接判定した (検出 1・要裁定 20・近傍 112・除外 235)。要旨の無いレコードは Semantic Scholar・Crossref・出版社頁で補った。要裁定 20 件はすべて N10 (U2 だけを支える式) に出た。18 件は U2 だけに触れ、U2 は既知なので結論を変えない。OCC-TI 1997 の 2 件 (OpenAlex・DBLP) は U1 にも触れるので、U1 の不在文から名指しで除いた。
- 本文を取得して読んだもの 6 本 (CockroachDB 2020、SI-STM・LSA 2006、Boksenbaum VLDB 1984、Mühe CIDR 2013、Hekaton SIGMOD 2013)。取得できなかった 5 本は取り寄せ一覧 (一次資料 §6) にまとめ、人間の手番として {{T:vhash-lit-library-order}} に分けた。Bayer 1982 の第 3 著者は "Heller" でなく Johannes Heigert (DBLP 書き出しで確認)。
- エージェント工数: Codex author 1 (取得器・照合器・台帳生成器、repo 外)、Claude 読み取り子 5 (sonnet: 記法での読み取り 3、取得試行 1、LSA の取得と読み取り 1)、段 6 review 1 + 焦点再レビュー 3 巡 (Codex read-only、gpt-6-sol / medium)。計算ノード: なし (login node で API 取得と照合のみ)。

## 次の一手差分

### 完了

- [T-2873] VHash 論文の文献調査と新規性の位置づけの残件を、一次資料 `output/insights/2026-09-29/vhash-novelty-repositioning/README.md` で閉じた。U2 は既知 (SI-STM・CockroachDB)。U0 は保持短縮という目的と GC 規則が既知で、実行中の前進を保護下限へ反映する機構が登録検索の範囲 (索引別 RW2) で見当たらなかった。U1 は同じ範囲で見当たらなかった (OCC-TI 1997 を除く)。範囲 = OpenAlex (題名 + 要旨、2026-09-29 09:51〜10:20 JST 取得)・arXiv (all、同 09:49〜09:50 JST)・DBLP (題名、Last-Modified 2026-09-28 20:23:37 GMT の全件書き出し) の事前登録した式 N01〜N08 と、読んだ原典。新規性の主張文の候補 3 案 (§7) と、次の版への申し送り (§8) を置いた。本文未取得 5 本の取り寄せは人間の手番として別 item に分けた。
  remaining: none
  base: 061d54167b06c05d3a58a25a339e53b4a4879dd1ad74efc1fa65d5cfe473032b

### 新規

- {{T:vhash-lit-library-order}} **P3・人間の手番 (取り寄せ)**: VHash 論文の関連研究で本文を取得できなかった 5 本を図書館経由で取り寄せる。書誌・DOI・どの主張の確定に要るかは `output/insights/2026-09-29/vhash-novelty-repositioning/README.md` §6 の表。U0・U1 の確定を強めるのは 1 (vWeaver、SIGMOD 2021)・2 (Diva、SIGMOD 2022) と 5 (OCC-TI、IPL 1997。U1 にも関わりうる未裁定で、現在は U1 の不在文から名指しで除いている)。届いたら AI が同 README §3.1 の 7 項目で読み、U0・U1 の判定を追記の新しい一次資料で更新する。
