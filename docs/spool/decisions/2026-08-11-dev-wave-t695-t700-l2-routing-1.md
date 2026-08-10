---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-11
wave: dev-wave-t695-t700-l2-routing
seq: 1
---

## {{D:o25-admission-exemption}}. 明示裁定による L2 admission の個別適用除外は `DW-O25` 限りとし先例にしない

**決定:** `docs/dev-wave/operations.md` の `DW-O25` (ff-only land の全史 provenance 関門) は、
D271 が新規 L2 節へ課す 3 条件のうち**条件 2 (現に機械代替されていない) と条件 3 (意味検索で
反証されず同一発火点の既存正本もなし) を満たさないまま登録した**。根拠はユーザーの明示裁定
(2026-08-10 /rulings §60、`[T-695]` (i)「新規 L2 節を作り登録する」) である。

この適用除外は **`DW-O25` 限りの一回限り**であり、**将来の L2 admission の先例にしない**。
以後の新規 L2 節は D271 の 3 条件をすべて満たすか、同じくユーザーの明示裁定を要する。
「過去に例がある」を admission の根拠にしてはならない。

**満たさない事実の逐語:**

- 条件 2 — 同じ義務は `tools/dev_wave_land.py` に runtime gate として実装済みで、
  非 0 拒否と main 不変を検証するテストも存在する。
- 条件 3 — D254 が同じ発火点 (ff-only land) の同じ義務を既に逐語で規定している。
  `DW-O25` はその reference 同期であり、定義上「同一発火点の既存正本」が存在する。

**理由:**

- D271 が塞ぎたかったのは「byte 余白が空いたことを理由に見送り済み候補を復活させる」非対称である。
  本件はその型ではなく、**ユーザーが reference 同期を明示的に要求した**ものである。
- 機械代替済みを理由に本文を置かない運用は、同じユーザーが §54 で既に否定している
  (「実装が強制するから本文不要」は採らない)。条件 2 を機械的に適用すると、
  §54 の裁定と正面から衝突する。
- 適用除外を記録せずに登録すると、次の wave が「D271 は満たさなくても通る」と読む。
  除外の射程を節 1 つに束縛して明文化することが、規範を空洞化させない唯一の方法である。

**却下した選択肢:**

- **D271 の条件 2・3 を一般に緩める** — 削除側の鏡像という設計意図が消え、
  byte 余白による復活を塞げなくなる。
- **`DW-O25` を登録しない** — ユーザーの明示裁定に反する。親が承認済み裁定を不採用にしない。
- **除外を worklog にだけ書く** — 将来の admission 判断者は decisions を索引して読む。
  規範 (D271) の隣に置かなければ届かない。

## {{D:normative-section-exact-pin}}. dev-wave の規範節は可視 H2 節全体を exact で pin し、不可視構造を節内に許さない

**決定:** dev-wave の起動導線と routing を担う規範節は、**可視 H2 節全体の exact 一致**で
`tools/check_docs.py` が pin する。対象は `.claude/commands/dev-wave.md` の `## 入力と開始`、
`.agents/skills/dev-wave/SKILL.md` の `## 開始する`、`docs/skill-self-improvement.md` の
`## routing`、`docs/dev-wave/operations.md` の `DW-O25` の 4 節である。

- 比較は **dispatch 可視化を通した slice だけ**で行い、raw slice と混ぜない。
- 同じ 4 節について **raw slice と可視 slice の一致**も要求する。
  節の内側に fence・HTML comment・raw HTML block を置けない。
- `DW-O25` の可視 H2 が `DW-O23` の可視 H2 より後にあることを検査する。
  対象 H2 の探索は**題の有無に依らず**行い、欠落・重複は fail-closed で finding にする。

**理由:**

- 規範節は「どの語で義務が書かれているか」が意味を持つ。語の言い換え・item の移動・
  例外文の差し込みは、いずれも義務を弱めるのに従来の検査 (H2 の有無、literal の出現件数) を通る。
- 節全体 exact にすると、pin 済み節の**内側**へ例外規定を差し込む経路が閉じる。
- 順序 pin の heading 探索を題込みの前方一致にすると、題を消すだけで検査が
  finding を出さずに通る。実装時にこの形が実際に入り、敵対レビューが検出した。
  **見つからない場合に黙って通す検査は恒真と同じである。**

**閉じない残余:** pin 済み節の**外側** (同じ file の他節) へ「ただし任意参照とする」型の
例外文を置く経路は残る。全 file を exact pin すると通常の docs 改訂が checker 改変を
必須にするため採らなかった。dispatch 契約がどの節を読むかを限定していることが緩和になる。

**却下した選択肢:**

- **literal の出現件数だけを pin する** — blockquote 化・別節移動・言い換えを通す。
- **raw slice を exact 比較する** — fence や HTML comment の正当な使用まで拒否し、
  可視化を通した検査と二重管理になる。
- **全 file を exact pin する** — 誤字修正のたびに checker 改変が要り、実運用が回らない。
