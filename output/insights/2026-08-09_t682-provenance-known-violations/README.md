# [T-682] provenance 既知違反 23 件の登録 + probe の .md 逐語移行

2026-08-09、branch `worktree-dev-wave-t682-provenance-known-violations`。
ユーザー裁定 2 件 ([T-682] / [T-139]、いずれも 2026-08-09) に従う実装 wave の一次資料。

## 何をしたか

`tools/check_ai_provenance.py` の `KNOWN_PROVENANCE_VIOLATIONS` へ 23 件を裁定参照つきで登録した。
内訳は [T-139] R4 probe wave の形式違反 22 件と、[T-682] の
`2c1929533a6f641b513f4f7990fe06e6cdb383b1` (missing-codex-author) 1 件である。
あわせて `output/insights/2026-08-09_t659-activation-deploy-window/verbatim/probe_split_window.py` を
同 directory の `.md` 逐語へ移した。

**許可値 (`ROLES` / `IDENT` / `AGENT_VALUE`) は広げていない。**裁定は案 (c) を明示的に
不採用としており、gate を過失へ合わせないためである (規律 2)。

## 裁定文を超えて締めた点 (ユーザー確認対象)

裁定文の scope は「形式違反用 kind の追加 + `_LEDGER_FINDING_KINDS` への追加 + note 必須」である。
本 wave はそれに加えて `KnownViolationSpec` へ `expected_finding_value` を足し、
抑止条件を `SHA + kind` から **`SHA + kind + 観測された不正 trailer 値の完全一致`** へ狭めた。

理由は段 3 レンズ A の所見 A-01 である。裁定文自身が
「(b) は将来の本物の形式違反も同じ経路で登録できる状態を作る」と懸念し、緩和として note 必須を
置いているが、実コードの抑止は finding 本文を見ないため、同じ SHA・同じ kind の別 finding が
登録枠を消費しうる。note は人間向けの説明であって機械的な同一性保証ではない。

**受理集合は広がらず狭まる方向のみ**であり、既存 7 entry は `expected_finding_value=""` で
従来どおりの挙動を保つ。

## 段 6 で私が入れた gate 自身の穴 (F177 として記録)

追加 kind の note 必須を「拒否リスト」で実装したところ、U+034F・U+FE0F (`Mn`) と
U+3164 (`Lo`) だけからなる note が通った。拒否リストを 2 度広げても閉じず、
焦点再レビューの指摘で「可視の説明文字を最低 1 つ要求する正条件」へ切り替えて閉じた。
`Lo` に属する filler があるため「Letter なら可視」も不十分で、default-ignorable 相当の
明示除外が要る。詳細は failures 台帳の該当エントリ。

## scope 外として返したもの

- **`tools/check_docs.py` の insights 走査が下位 directory を含まない** (`INSIGHTS_DIR.glob("*.md")`)。
  `verbatim/` 配下の .md は placeholder guard にも三軸語検査にも掛からない。
  既存の全 verbatim package に等しく当たる既存の死角で、本 wave が導入したものではない。
  新 gate 新設は本 wave の scope 外とし、「check_docs が新 .md を検査する」と主張しないことだけを
  義務にした。裁定へ返す。
- **F37 の land 関門** (`tools/dev_wave_land.py`) は並行 wave
  `worktree-dev-wave-t139-provenance-known-violation` の所有。本 wave は触っていない。
  順序は「本 wave の land → peer の関門 land」で相互合意した。

## ファイル

- `verbatim/s1-brief.md` — 親の段 1 brief (provisional 裁定 P1〜P6)
- `verbatim/s2b-plan.md` — 段 2 プラン (codex sol/max、read-only)
- `verbatim/s3-lensA.md` / `s3-lensB.md` — 段 3 敵対相談 (sol/max、luna/max)。ともに NO-GO
- `verbatim/s4-adjudication.md` — 親の段 4 裁定と変異事前登録 M1〜M6
- `verbatim/s5-impl.md` — 段 5 実装子 (sol/high、workspace-write) の報告
- `verbatim/s6-lensC.md` / `s6-lensD.md` — 段 6 敵対レビュー。ともに NO-GO
- `verbatim/s6-fix.md` — fix 1 巡目 (C-01/D-01/C-02)
- `verbatim/s6-refocus.md` — 焦点再レビュー。F-01 で NO-GO
- `verbatim/s6-fix2.md` — fix 2 巡目 (F-01)
- `mutation-spec.json` / `mutation-ledger.json` — 変異 M1〜M8 の事前登録と本走結果

## 実測

- **変異 matrix**: KILLED 8 / SURVIVED 0 / MISMATCH 0 / TIMEOUT 0、baseline PASSED、
  全変異で記録 node と期待 node が一致 (repo_head `ef06e7f2`)。
  M7 (必須 note の正条件) と M8 (過剰拒否を検出する正例) は、対象 gate が段 4 時点に
  存在しなかったため段 6 で追加登録した。
- **full-history provenance 監査**: 登録前 rc=1 / 1947 件中 23 新規違反 →
  登録後 rc=0 / 新規違反なし / known-violations=30 / stale 0。
- **対象テスト**: fix 1 巡目前 6 failed / 261 passed → 1 巡目後 281 passed →
  2 巡目後 286 passed (いずれも rc=0 で確定したのは後 2 者)。
- **受入全走**: rc=0、**7615 passed / 20 skipped** (1350.34s)。lease `d076270d68a3` を保持して
  1 走で実施した。

## 子の非実走について

段 5・段 6 の実装子はいずれも sandbox から pytest を起動できず (dispatch preflight が
`qstat -Q` を引けない)、**緑を主張せず `partial` と申告した**。これは契約どおりの正しい
fail-closed であり、実測はすべて親が行った。
