---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-08
wave: worktree-dev-wave-t182-luna-stage3
seq: 2
---

## {{D:stage3-hybrid-model-user-ruling}}. 段 3 敵対相談を sol/luna 混成にする — 根拠はユーザー裁定であって被覆率実測ではない

**決定:** dev-wave 段 3 (敵対相談) のレンズを 2 本とし、1 本目を `gpt-5.6-sol`、
2 本目を `gpt-5.6-luna` とする。段 2 / 段 5 / 段 6 は `gpt-5.6-sol` のままとする。
`reasoning` と `sandbox` は各 worker 節の規定を変えない。

**この採用の根拠はユーザー裁定だけである。** [T-182] の shadow pilot が出した
被覆率 91% と token −31.6% は、同 ID 自身が循環・非盲検・事前登録なし・n=1 を理由に
「policy 根拠にしてはならない」と記録しており、本決定もそれを根拠にしていない。
[T-184] (証拠に基づく既定 policy 採用) と [T-189] (妥当な比較実験の設計) は
supersede も carve-out もせず、所有範囲を変えずに据え置く。

**ユーザー裁定の経緯:** 初回の指示は「luna が 91% の能力を発揮し、トークン効率を 30%
よくしているならば luna max に置き換えてほしい」という条件付きの全置換だった。
段 3 の敵対レビュー 2 本が NO-GO を返し、親が一次資料の読み違いを訂正したうえで
三案 (全 luna / 混成 / [T-189] の A/B 待ち) を再提示した結果、混成が選ばれた。

**理由:**
- 全 luna 化は段 3 の検出力を落とす。D207 は「検出力を下げる変更は規律 2 の対象」と明記しており、
  policy 根拠に使えない観察値と token 節約を理由に検出力を落とす経路をこの repository は禁じている。
  混成は sol レンズを 1 本残すため、この論点が発火しない構成である。
- 91% は「11 件中 1 件の見落とし」であって見落とし確率ではない。基準集合が sol 自身で循環しており、
  レンズを跨いだ独立性も測っていない。全レンズを同一 model にすると系統的盲点が共通化する。
- 混成なら段 3 の token 削減は概ね半分になるが、model 多様性が増える。異製品レンズの補完性は
  過去の wave でも実証されている。

**却下した選択肢:**
- **全 luna (初回指示どおり)** — 段 3 の敵対レビュー 2 本が NO-GO。sol にしか出せない所見を
  落とす構成であり、検出力低下を token 節約で買う形になる。ユーザーが再裁定で不採用とした。
- **[T-189] の A/B まで現状維持** — 前進しない。混成は検出力を下げないため、
  A/B の完了を待つ理由が弱い。ユーザーが再裁定で不採用とした。
- **model 権威を dispatcher (`.claude/commands/dev-wave.md`) に置く** — 起動直前の必読集合に
  入らず、byte 予算も他 wave が使い切っていた。`DW-O01` へ移した。

**この決定が保証しないこと:** 文書契約が縛るのは記述だけである。`-m` の実引数を権威行と
機械照合する層は無く、served model の attest も F56 のとおり不能である。記録できるのは
`requested_model` までで `served_model` は unknown である。

## {{D:dev-wave-model-single-authority-absence-pin}}. dev-wave の model 権威を DW-O01 の 1 行に集約し、他 surface では slug の「不在」を検査する

**決定:** dev-wave が起動する codex の model 指定は `docs/dev-wave/operations.md` の
`DW-O01` にある 1 行だけを権威とする。`DW-S02`、`DW-S03`、`.claude/commands/dev-wave.md`、
その他の worker 節は model 名を持たない。`DW-O01` の起動雛形は `-m <model>` の placeholder とする。

機械 pin は**期待値との一致ではなく slug の不在**を検査する。権威行だけが例外で、
その行自体は可視テキスト上 exact 1 件で固定し、`-m <model>` の存在も別 finding で要求する。

**理由:**
- 期待値照合方式は decoy で迂回できる。正しい slug を 1 つ残したまま同じ節へ別の slug を足せば
  「期待値と一致する値が存在する」ため通ってしまう。不在方式なら decoy を置く場所自体が違反になる。
- `DW-O01` は条件 dispatch 01 が codex 起動直前に必ず読む節であり、権威が起動直前の
  必読集合に入る。worker 節や dispatcher の別節に置くとこの性質が得られない。
- 節単位でなく file 全体 (見出しを含む) を検査対象にしないと、検査対象外の節や
  見出しに第二の権威を置ける。

**却下した選択肢:**
- **各 worker 節が自分の model を書く** — 権威が分散し、`DW-S05-A` / `DW-S06-A` のように
  model を書いていない節との整合が prose の解釈に委ねられる。
- **dispatcher の「凍結境界」へ段別 model 表を置く** — 起動直前の必読集合に入らず、
  byte 予算も残り 43 bytes しかなかった。
- **`DW-O01` の雛形に具体 slug を直書きしたまま worker 節で上書きする** — どちらが権威かが
  一意に決まらず、`DW-STOP` の「指定が一意でない」に該当する。

**限界:** この pin は文書契約だけを守り、実際の起動引数も served model の identity も
attest しない。runtime binding は本決定の射程外であり、裁定パッケージへ返す。
