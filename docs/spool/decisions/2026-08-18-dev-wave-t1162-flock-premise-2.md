---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-18
wave: dev-wave-t1162-flock-premise
seq: 2
---

## {{D:bundle-flock-premise-not-transferable}}. D130 条件 2 は同種の排他の運用前提では閉じない — 択一を裁定へ返す

**決定 (1): 条件 2 に残っているのは cross-node flock の可否ではなく、1 host pair からの一般化である。**
cluster probe が 2 回、別々の host pair で `/work`・`/home` とも 6/6 `BLOCKED`・`localflock` 不在を
観測し、2 回目は `qstat` の Execution Host 照合まで通して `dangerous: false` を確定させている。
正本は `output/insights/2026-08-16_t402-flock-execution-host/RESULT.md`。同文書が自ら
「1 host pair の 1 回の観測は十分条件ではない」と限定しており、条件 2 は未充足のまま残る。
測定を続ける道は資源上も機械的にも塞がっている — sanctioned probe driver の
`FLOCK_LEG_ONLY_SUBMISSION_LIMIT = 1` が既に 1/1 消費済みで、再走には gate 定数の引き上げという
受理集合の変更が要る。

**決定 (2): 「排他を lock から作業木の一意性へ移せば設計だけで閉じる」という案を却下した。**
D216 が既に「lock は `--out` へ束縛する。harness の `flock` は repo 絶対 path 由来なので、
scratch を変えると分裂し、同じ台帳を後勝ちで上書きできる」と定め、producer 一意性の authority を
`<out>.lock` (flock) に置いている。実装上も、wrapper の `--resume` 枝は既存 container を
`lstat` と admin 再束縛で受け入れるだけで **atomic claim を行わない**ため、その枝の排他は
外側の flock だけである。fresh invocation の `mkdir(exist_ok=False)` は atomic create 系だが、
その cross-node 成立自体が未測定であり、flock について exact host pair から一般化しないと
自己限定しておきながら `mkdir` を無測定で一般化するのは非対称である。

**決定 (3): 「束ね経路では wrapper 必須」と docs に書いて閉じることも却下した。**
同じ案を D216 が既に却下しており、理由は「機械的 admission が無い状態の『必須』は prose-only で
あり、旧 direct 経路も台帳 consumer も拘束しない」である。運用正本の本走 recipe は現に
wrapper 非経由の直接起動を掲載しており、設計正本も wrapper を必須としていない。

**決定 (4): 同種の排他 (campaign 実行所有権) の運用前提の適用可否は「未確定」とし、
1 点だけをユーザーへ問い返す。** 逐語では排他単位 (campaign 対 解決済み checkout path) と
投入主体 (ユーザーの番号付き投入 対 wave 内での親の自動起動) が違う。しかし述語を
「一つの logical run に node を跨ぐ active owner は一つだけ」と置けば、束ねは harness 全体を
1 job に収めるため、retry と `--resume` を重ねない運用なら同型に読める。この可否は運用意思に
属し AI が決めない。問いは「束ねた変異 job について、同一 spec / 同一 `--out` に対する retry と
`--resume` をノード跨ぎで同時に走らせない運用を約束できるか」である。

**決定 (5): 二重注入の影響記述を広げる。** 壊れるのは変異台帳の値と復元後 bytes だけではない。
一方の復元中に他方が test を走らせれば偽 SURVIVED、一方の変異上で他方が走れば偽 KILLED になる。
偽 KILLED は無効な正しさ gate を land させ、将来の certified 選択の受理集合を誤って広げる。
偽 SURVIVED は正しい変更を拒否する。proof chain の参照先も別 invocation 由来に分裂しうる。

**理由:**
- `DW-S04` は「scope 外の real 所見は実装せず、設計択一・所見・推奨案を裁定パッケージで
  ユーザーへ返す」と定める。承認済み裁定は 2 分岐 (前提が適用できるなら設計変更なしで閉じる /
  できない場合に限り supersede を検討して判断材料を返す) しか許しておらず、
  親が段 1 で描いた「前提は適用できないが別機構で閉じる」は分岐の外だった。
- 段 3 の敵対 2 レンズが独立に否定側で返し、refuted はゼロだった。両レンズが独立に重なった
  指摘は 3 点 — 分岐外の第三の道、prose-only の必須化、既存失敗事例の誤一般化である。
- D130 は 4 条件の連言であり、条件 2 だけを閉じても transport は進まない。
  手続きの択一を返した決定も未裁定のままである。

**却下した選択肢:**
- **条件 2 を「閉じた」と記録する** — 決定 (2)(3) のとおり、荷重を担う経路が flock に残る。
- **wrapper 必須化を本 wave で実装する** — 承認済み裁定が「実装を先に走らせない」と定め、
  かつ活性化は独立 wave の裁定に委ねると D216 が既に決めている。
- **fan-out の path 一意性機構を束ねの充足材料に算入する** — 経路が違ううえ、
  fan-out 本走はこの機体で実行不能と確定しており、稼働実績として引用できない。
