# [T-1116] / [T-1055] — 批准済み既知赤 registry は現 repo では成立しないことの実測

wave: `dev-wave-t1116-known-red-registry` / 2026-08-15 / branch
`worktree-dev-wave-t1116-known-red-registry`

## この材料が答えたこと

依頼は 2026-08-15 のユーザー裁定 (T-1116 = 択 (c) 批准済み既知赤 nodeid の registry を併設する、
T-1055 = 択 (b) registry + receipt へ nodeid を明記する) の実装である。裁定には
**「registry は『批准済み』であることを機械が確認できる形にし、任意の nodeid を後から足せる
fail-open な逃がし道にしないこと (規律 2)」**という拘束が付いていた。

**実装は行わなかった。** 段 2 プランと段 3 の敵対 2 レンズが**独立に NO-GO** を返し、
親が全主張を検算して成立を確認したため、`DW-S04` に従い裁定パッケージへ返した。

## 親が独立に検算した実測 (すべて commit `330f67d0` の worktree)

### 1. 人間だけが動かせる trust root が repo 内に 0 件

`tools/` `hooks/` `orchestrator/` を対象に `verify-commit` / `verify-tag` /
allowed-signers を検索して **0 件**。git 呼出しに現れる gpg 関連は
`--no-gpg-sign` / `commit.gpgsign=false` すなわち**署名を無効化する向き**だけである。

### 2. 書込みを禁止している機構は `hooks/` subtree だけ

- `hooks/guard_write.py` の拒否対象は `hooks/` subtree と成果物 tree であり、
  `tools/` 配下は含まれない。
- `tools/check_codex_hooks.py` の `_PINNED_GUARD_PATHS` (`tools/pegasus/admission_registry.json`
  を含む) は `_validate_pinned_guard_bytes` が working bytes と HEAD blob の drift を
  検査するものであって、**書込み禁止機構ではない。**
- したがって「先例の registry は codex 子から書けない」という親 brief の前提 (N3) は**誤り**だった。

### 3. `refs/remotes/origin/main` は trust root にならない

ローカル ref なので `git update-ref` で移動でき、実際の push と暗号学的に区別できない。
加えて実測時点で `origin/main = a2cb460d`、`main` は **92 commit 先行**しており、
1 回の push が全 entry の一括承認になる。

### 4. 非帰属判定の実行体は wave tip が握っている (本 wave の主産物)

- `tools/dev_wave_wait.py` は wave working tree の `tools/check_acceptance_reds.py` を起動し、
  receipt へ束縛する blob sha を `tested_tip` から採る。
- `tools/dev_wave_land.py` の受入検証も `tested_tip:tools/check_acceptance_reds.py` としか
  照合しない。**`tested_main` 側の checker blob と比較する検査は 1 件も無い。**
- land の protected path は `docs/handoff` と control container だけで、
  `tools/` 配下の内容を gate しない。

→ **registry の有無に関わらず、wave は自分の tip の checker を書き換えることで自分の赤を
非帰属に分類させ、land を通せる。これは本 wave が新設する穴ではなく、現行の穴である。**
registry を設計しても、この穴が開いている限り registry を経由せずに同じ救済ができる。

## 段 3 が出した突破手順 (親が検算して成立を確認)

- **2 wave 突破:** Wave A で registry へ将来壊す exact nodeid を登録し child-green で land →
  Wave B でその node を壊す。tested_main 束縛は同一 wave の後付けしか防がない。
- **同一 wave 突破:** registry JSON を一切変えず、tip の loader を「空 registry から特定 nodeid の
  active entry を合成する」実装へ変える。待ち手と land は blob identity しか照合しないので
  矛盾を検出できない (上記 4 の系)。

## 親自身の誤りとして訂正した点

- 不変条件 I2 が自己矛盾していた。「読めない registry を空として通してはならない」と
  「無い・空・読めないで今日と完全に同一」は両立しない。空 registry でも `rerun_rc == 1` は
  非帰属なので「全件 attributable」も誤り。正しい形は
  **「不存在または valid-empty は既存分類を保存する。存在するが読取不能・不正なら probe より前に rc=2」**。
- 「今日と 1 bit も変わらない」は受理集合・分類・rc について正しいが、
  receipt schema を上げれば receipt bytes は必ず変わる。両者を分けて書くべきだった。

## 事前登録変異

**登録していない。** 実装差分ゼロで受理集合が変わらないため `DW-S04` の免除に該当し、
かつ段 3 が「実装前の時点で単一理由性を確認できた候補は 0 件」と判定した。
`DW-M01` は確認できない変異を登録しないと定める。将来の実装 wave が使えるよう、
段 2 の変異候補 6 件と段 3 の単一理由性所見を `verbatim/` に保全した。

## 逐語

- `verbatim/s2-plan.md` — 段 2 プラン (NO-GO 結論 + 条件付き実装プラン + 変異候補 6 件)
- `verbatim/s3-lensA.md` — 段 3 レンズ A (規律 2 / fail-open 面、NO-GO)
- `verbatim/s3-lensB.md` — 段 3 レンズ B (schema / consumer 閉包 / bootstrap 面、NO-GO)

## 主張の射程

本材料が主張するのは「commit `330f67d0` の repo に、AI が動かせない批准の trust root が
存在しないこと」と「非帰属判定の実行体が wave tip 側にあること」の 2 点である。
「registry という設計が原理的に不可能」とは主張しない — 外部 trust root を与えれば成立する。
