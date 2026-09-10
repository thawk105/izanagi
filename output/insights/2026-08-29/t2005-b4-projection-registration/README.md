# [T-2005] B-4 projection closure hash の事前登録 — 機構は閉じ、値は未登録

2026-08-29。branch `worktree-dev-wave-t2005-b4-projection-registration`。
base main `d03855e92`、取り込み後 main `164e2c355`〜`17bfcda68`。

## 何を依頼され、何を返したか

依頼は「B-4 正式実走の前に、base / sort / trigger の 3 driver それぞれの新しい projection
closure hash を、事前登録と admission record へ登録する」だった。あわせて
「凍結物の再発行が要る場合は、その手順と権限が既存の事前登録・批准の枠内で閉じるかを先に実測し、
閉じないなら不足を記録して停止する (新しい権限主体を作らない)」という条件が付いていた。

**返したのは、登録の器と規範である。値そのものは登録していない。** 理由は 1 つに絞れた。

## 実測した停止理由

事前登録 §0 は「未記入の欄には placeholder 語だけを置く」と定め、部分記入の例外を
「実行責任者・開始時刻」欄 1 行に限り「他の 9 欄へこの例外を広げない」と明記する。
対象セルは model snapshot・prompt hash・projection hash の 3 種を 1 セルに持つので、
projection だけを書くことはできない。

3 種のうち 2 種は repository の bytes から機械導出できる。

- projection: `p3_b4_closed_critic.projection_sha256(kind)`。
- prompt: 未改変の `.claude/agents/critic.md` の本文と mediated projection contract から作る
  effective prompt の sha256。base main `d03855e92` 時点の実測値は
  `1b5006f6cde3c05d8b9b935ff590632074ed87ac876a264d7953e07e0435f0cf`。

**`expected_claude_model_snapshot` だけが導出できない。** 実 CLI 応答の `modelUsage` が返す
exact slug は走らせる時期で変わる — 本 repo の成果物には `claude-opus-5[1m]`
(2026-08-21 の probe raw stdout) と `claude-opus-4-8` (s6-rounds の 125 件) の両方が実在する。
role frontmatter の `opus` は snapshot slug ではない。D998 が定めるとおり本欄は
「事前宣言 + 実行時照合」であって予測ではないので、値の指名は実験条件の決定である。
docs 全体を検索しても、この欄の宣言源・承認者を定める規範は存在しなかった
(`expected_claude_model_snapshot` への言及は D998 の 1 箇所だけ)。

**したがって値を書けば新しい権限主体を作ることになる。** ユーザーが指示した停止条件に該当する。

## 凍結物の再発行は要らなかった (実測)

- 事前登録文書は §0 が自ら「発効前 draft」と宣言し、`tools/check_docs.py` も living 扱いにする。
- `p3_b4_analysis_prereg_consumer.py` が exact pin する §5.1.1 の raw / semantic sha256 は、
  §5 の表と §5.1 の当該項目だけを編集しても不変であることを、編集前後の実測で確認した
  (raw `0ceab4cd064eb8ff6c5dba22364fff04a6d708de8acb9d9cde52115f0891df30`)。
- bytes を pin する commit 済み admission record は repo に 1 件も存在しない。

**この結論は「最初の record を発行する前の一時点」に限る。** 発行後は文書編集のたびに
record の再発行が要る。

## 段 3・段 6 が見つけた、自分たちの誤り 2 件

**(1) 親の段 4 裁定が受理集合を広げていた。** 親は「文書 3 値が live と一致し record 値が
選択 driver の live と一致すれば、record 値と文書の当該 tag の一致は導かれる」と裁定し、
`verify_b4_admission_record` へ driver 種別を渡さない設計を採った。**これは pair 経路しか
見ていなかった。** 起動器の bootstrap 経路 (`p3_b4_launcher.issue_context` →
`launch_bootstrap_impl`) は同 verifier しか通らず、pair 生成点の照合を 1 つも通らないまま
実 driver を起動する。変更前は `assert_section5_...` が record と文書の projection を
照合しており bootstrap も守られていた。段 6 の敵対レビューが指摘し、親が実測で裏取りして
裁定を訂正した。

**(2) fix 子が文書に合わせて実装を緩めた。** レビュー B の「文書の `<slug>` と `<64 hex>` が
実装より広い」という所見に対し、fix 子は実装を広げる向き (model の `claude-opus-` 接頭辞要求を
落とし、hash に大文字を許す) で解決した。正しい向きは文書を実装へ合わせることである。
焦点再レビューが指摘し、狭める向きへ戻した。

どちらも独立レビューでしか捕まらない型である。

## 閉じた機構

- 期待値行の文法を base / sort / trigger の固定順・固定 tag の 3 projection へ置換した。
  旧 1 値形・tag 欠落・重複・順序違い・末尾余剰を拒否する。
  **1 driver 分だけを登録できる形を残すと、どの driver で走るかを結果を見た後に選べる。**
- 文法を raw bytes にも課した。`_normalized_source_cell` の NFKC 正規化により、
  `ﬀ` (U+FB00) を含む 63 文字の生文字列が正規化後に 64 桁 hex になり、U+00A0 は普通の空白へ、
  全角の角括弧は ASCII へ変わることを実測した。raw と正規化後の両方に fullmatch を要求する。
- `verify_b4_admission_record` へ既定値なしの driver 種別を戻し、record の単一 projection が
  文書の当該 tag と exact に一致することを検査する。repository 内の caller 20 箇所
  (production 3、test 17) が全件 driver を明示し、既定値経路は無い。
- 文書 3 値すべてを live `projection_sha256(kind)` と照合する関門を、bootstrap 経路、
  pair 生成点、invoke、最終 certification の 4 か所に置いた。**従来 production は実走する
  driver の 1 値しか照合せず、非選択 driver の閉包が陳腐化したままでも実走できた。**
- D998 が要求する順序に合わせ、live 照合を executable 探索と artifact root 作成より前へ移した。

record の canonical JSON schema `p3-b4-prerun-admission/v1`、root key 集合、単一 projection
field、sidecar schema は変えていない。admission record の JSON artifact は 1 件も作っていない。

## 規範として足したもの (D1060 が env_tag 等で採ったのと同じ形)

§5.1 の当該欄へ解除条件を足した — セルの原子性、3 driver 全件を要求する理由、記入が継続的
不変条件であること (閉包 member の bytes が変われば 3 値は同時に無効になる)、
`<slug>` と `<hash>` の字句、そして model snapshot について先に固定すべき 4 点
(結果に依存しない宣言源・承認する人間の識別子・宣言の時点・観測 slug が食い違ったときの扱い)。
(d) を「宣言を書き換えて同じ実走を続ける」と定めてはならないことも書いた。

§10 へ不足を記録した。閉じたのは機構だけであり、本欄が埋まるまでに残るのは
(i) 4 点の先行固定、(ii) 3 値の原子的記入、(iii) その版の commit、(iv) driver ごとの
record 発行であること、発効にはさらに §5 の他 9 欄と §6 の前提条件が要ることを明記した。

## 変異 matrix

`mutation/` に spec と台帳。DW-M07 に従い、まず全件 SURVIVED 期待の probe で観測 node を集め、
その完全集合を期待値にして本走した。**baseline PASSED、8/8 KILLED、SURVIVED 0、MISMATCH 0、
TIMEOUT 0、期待 node 完全一致。**

|変異|落とした防御|KILLED node 数|
|---|---|---|
|M1|bootstrap の live 3 値照合|1|
|M2|pair 生成点の live 3 値照合|2|
|M3|共有 helper の右辺を live から文書自身へ (恒真化)|5|
|M4|verifier の record↔文書 projection 照合|3|
|M5|旧 1 値形を追加で受理する緩和|1|
|M6|`fullmatch` → `search`|1|
|M7|raw 側の文法検査|1|
|M8|invoke 時の 3 件再照合|1|

**M3 は共有 helper への変異であり、bootstrap・pair・invoke・最終 certification の 4 層を
同時に倒す。** D1275 に従い、独立に発火する関門 (M1・M2・M8 が別々の層を単独で守る) と
区別して数えること。M5 は「旧形へ置換」ではなく「旧形を追加受理する緩和」として登録した —
置換では現行の正例まで壊れ、KILLED が旧形受理でなく正例破壊で生じるためである。

## 実走した検査

- 焦点走 (`test_p3_b4_admission_record.py`、`test_p3_b4_closed_critic.py`、
  `test_p3_b4_launcher.py`): 122 passed / 0 failed。Pegasus 計算ノード、loadgroup。
- `tools/check_docs.py`: 違反なし。
- `tools/check_ai_provenance.py`: 導入時点から HEAD まで rc=0。
- §5.1.1 の raw / semantic pin: 全編集後も不変。
- §5 全体の関門: 他 9 欄の `未記入` により依然として拒否する (実測)。**開かないのが正しい。**

## 一次資料

- `verbatim/` — 段 1 brief、段 2 plan、段 3 の 2 レンズ、段 4 裁定、段 5 実装子報告、
  段 6 の敵対レビュー 2 本と焦点再レビュー。
- `mutation/` — probe と本走の spec・台帳。
