---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-09
wave: dev-wave-t682-provenance-known-violations
seq: 1
title: [T-682] provenance の既知違反 23 件を裁定参照つきで登録し、probe を .md 逐語へ移した — 抑止条件は SHA+kind から SHA+kind+観測値へ狭めた (コード + docs、受入 7615 passed / 20 skipped、変異 8/8 KILLED・SURVIVED 0、branch worktree-dev-wave-t682-provenance-known-violations)
---

## 本文

- **ユーザー裁定 2 件に従った実装。**[T-682] の 1 件 (`2c1929533a6f...`、missing-codex-author) と
  [T-139] R4 wave の 22 件 (形式違反) を `KNOWN_PROVENANCE_VIOLATIONS` へ登録した。処置は案 (b) で、
  `ROLES` / `IDENT` の許可値拡張 (案 (c)) は採らない — gate を過失へ合わせないため。
  一次控えは `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/` の
  `2026-08-09-t659-provenance-and-f37-rulings.md` と
  `2026-08-09-t139-r4-probe-provenance-format-violation.md`。
- **裁定文の逐語を超えて gate を締めた点が 1 つある。**段 3 レンズ A が、抑止条件が
  `SHA + kind` だけで finding 本文を見ないことを指摘した。裁定文自身が懸念していた
  「将来の本物の形式違反も同じ経路で登録できる」経路は note 必須では塞がらないため、
  `KnownViolationSpec` へ「その commit で観測した不正 trailer 値」を持たせ、
  `SHA + kind + 値`の完全一致でのみ抑止する形にした。受理集合は広がらず狭まる方向のみ。
  裁定文の scope (kind 追加 + note 必須) を超える追加なので、ユーザーの確認対象として明示する。
- **段 6 で私が入れた gate 自身に穴が見つかり、2 巡目の fix を要した。**制御文字の拒否リスト方式では
  U+034F・U+FE0F・U+3164 のような不可視文字だけの note が「1 件ずつ理由を書く」という裁定の
  必須条件を素通りする。拒否リストは維持したまま、可視の説明文字を 1 つ以上要求する正条件を
  重ねて閉じた。**拒否リストだけでは名目化を防げないという型**であり {{F:blacklist-only-note-gate}} に残す。
- **並行 wave との所有分割を実測合意で決めた。**起動直後に `worktree-dev-wave-t139-provenance-known-violation`
  が同じ 22 件を scope に持つことを handoff から検出し、peer へ照会した。peer は
  段 1 途中・codex 子 0 本・差分ゼロと実測回答し、`tools/check_ai_provenance.py` 系を本 wave へ譲り、
  自らは F37 land 関門 (`tools/dev_wave_land.py`) を取った。編集 file は素集合。
  **順序制約は「本 wave の land → peer の関門 land」**で相互合意した — 関門は既知違反以外の赤で
  land を拒否するため、23 件が未登録のまま有効化されると自分自身の land を止める。
- **scope 外として実装せず返す 2 件。**(i) `tools/check_docs.py` が `output/insights/**/*.md` を
  再帰走査しない死角 (`INSIGHTS_DIR.glob("*.md")`)。既存の全 verbatim package に等しく当たる
  既存問題で、新 gate 新設は本 wave の scope 外。**「check_docs が新 .md を検査する」と主張しない**ことだけを
  義務とした。(ii) land 関門は peer 所有。
- **`AI-Agent` の model 表記。**本セッションは `/model` 切替をしていないが、実行面が示す ID は
  `claude-opus-5[1m]` で `IDENT` に反する。[T-139] 裁定文が正しい例として名指しした
  `claude-opus-5-1m` を使った。`reasoning` は自分の effort を context から確認できないため、
  規約の「本来確認できるが記録時に確定できない場合」に当たる `unknown` とした (推測しない)。
- **段 8 の改善候補 1 件は [T-317] へ返した** — 詳細は同項の更新を見ること。

### 実測した環境事実 (本 wave の差分とは無関係)

- `python3 tools/check_ai_provenance.py` は login node で完結せず、headroom 次第で
  local bounded scope と Pegasus dispatch のどちらでも走る。本 wave の実測は dispatch 経路
  (request 896594.nqsv、Elapse 20S)。
- 変異 harness の期待 node 実在検査で 6 件が「不在」と赤になったが、**原因は spec 側の書き方**で
  実装にもテストにも欠陥はなかった。pytest は明示 `ids=` の backslash を ASCII escape するため、
  source の `"note-\\u00ad"` (backslash 1 個) は node id では 2 個になる。実測値へ合わせて解消した。
  途中で「dispatch relay の collection 切り詰めが原因」と判断したのは**誤り**で、`-k` で出力を
  小さくしても再現したため棄却した。切り詰め自体は実在する (`omitted_bytes=27598` / 31694、87%)。
- 受入 lease は 30 秒間隔の待ち手では 65 分・3 holder 交代のあいだ 1 度も解放窓を取れず、
  8 秒間隔へ詰めた。既存 memory の「30 秒間隔」は本日の並行度では不足という独立事例。
- 背景 task の完了通知が 1 度**偽**だった (通知後に `.done` 不在・producer 生存)。
  成果物 + `.done` + producer 死の 3 点照合で検出した。

## 次の一手差分

### carry

- [T-317]

### 完了

- [T-682] 既知違反 23 件を裁定参照つきで登録し、形式違反用 kind と note 必須を機械強制した。
  probe の .md 逐語移行も完了。抑止条件は SHA+kind+観測値の完全一致へ狭めた。
  remaining: none
  base: 4e667b1f4d8052194daa693ad9bcdfded03ecb73cbbf55c1ff153563d99c9e6f

### 更新

- [T-139] **P2・登録は完了、残るは R4 本走の後続**: provenance 形式違反 22 件の
  known-violation 登録は [T-682] の wave で完了した (kind `malformed-ai-agent` を追加し、
  22 件を裁定参照 + note + 観測値つきで登録)。本項に残るのはそれ以外の [T-139] 残件である。
  base: d562b4d2eda198abe1e59a638ee95039f16fc42517a90909995505caf6330558

### 新規

- {{T:insights-verbatim-not-checked}} **P3・新規**: `tools/check_docs.py` の insights 走査が
  `INSIGHTS_DIR.glob("*.md")` で下位 directory を含まないため、`verbatim/` 配下の .md は
  placeholder guard・三軸語検査のどれにも掛からない。既存の全 verbatim package に等しく当たる
  既存の死角で、本 wave が導入したものではない。再帰走査する専用 guard を足すか、
  「対象外である」を成果物側に明記するかの択一をユーザー裁定へ返す。
