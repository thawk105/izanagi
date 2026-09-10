# 段 6 追加裁定 (fix 第 2 巡) — [T-2145]

fix 第 1 巡は F1〜F6・F8〜F10 を直したと報告したが、**pytest を 1 度も実走できていない**
(`rc=16` が 2 回)。親がキューの空きを捉えて実走したところ、次が判明した。

## 親が実走した検査

| 走 | 結果 |
|---|---|
| `test_sort_swo_oracle.py` (fix 前) | **104 passed / rc=0 / 55.13s** |
| 変更 production の検査側 6 file (fix 後) | **8 failed / 597 passed / 2 skipped / rc=1 / 52.07s** |

## G1 — tokenizer が閉じた語彙外で例外を投げ、決定順序を潰している (最重要・新規)

親が現物で確認した。`_sort_ir_tokens("int harmless = 1;")` は
`ValueError("token outside the closed grammar")` を投げ、`validate_sort_implementation` は
`sort-ir.tokenize-resource.v1` を返す。テストの期待は `sort-ir.envelope.v1` である。

閉じた語彙に無い token を 1 つでも含む入力は、構造上の問題が何であれ
すべて `tokenize-resource` になる。結果として `envelope` / `parameter-signature` /
`expression-shape` / `field-direction` は、**全 token が既に閉じた語彙に属する入力**に対してしか
発火しない。段 2 プランが定め段 4 が承認した決定順序が実効を持っていない。

**受理集合は広がらない** (どの経路でも拒否される) ので規律 2 の違反ではない。
破れているのは**規律 3** — 「なぜ壊れたかを構造化して返し、それを次の合成の入力にする」。
合成子は毎回「tokenize に失敗した」と告げられ、実際の欠陥へ誘導されない。

これは F1 (body 異常が `parameter-signature` へ誤分類) の一般形であり、F1 を包含する。

**修正:** tokenizer は C++ token として字句分割するところまでを責務とし、
語彙外 token は例外にせず token として返す。段階判定は期待 token 列との突き合わせで行い、
不一致が生じた段の rule id を返す。`tokenize-resource` は真の字句失敗
(未終端リテラル、byte/token 上限、行連結、UCN、raw string、代替トークン) に限る。
**受理する集合は 1 つも増やさないこと。**

## G2 — 正準形の再 materialize が byte exact でない (新規)

実装子自身が書いた `test_sort_quarantine_canonicalizes_outer_whitespace_bytes` が落ちている。
`extract_materialized_hole(padded_edited, "silo-writeset-sort")` が
`comparator + "\n"` と一致しない。段 4 裁定 R1 の中核 (build 対象・compile 対象・照合対象を
正準形で一致させる) がまだ成立していない。**テストが正しく実装が誤り。**

## G3 — role review ledger の pin 追随 (親の段 1 pin 閉包の漏れ)

`.claude/agents/*.md` は `orchestrator/codex_roles/review_ledger.py` の
`SOURCE_FILE_SHA256` で pin されている。本 wave は 2 枚を変更したため
`RoleSpecError: reviewed SOURCE_FILE_SHA256 drift; ledger明示更新が必要` で
`test_codex_agents.py` が collection error になり、
`test_real_repo_serialization.py` の 2 node が巻き添えで落ちている (8 件中 3 件)。

親が実測した drift:

| role | 記録値 | 実測値 |
|---|---|---|
| `auditor` | `e33c65d4...` | `a0912ebb...` |
| `coder-v4-autonomous-sort` | `fbabef04...` | `0d98a362...` |

**これは親の段 1 の pin 閉包検索の漏れである。** brief の実アンカー表に
`.claude/agents/coder-v4-autonomous-sort.md` を挙げながら、agent file を key にする pin を
探していなかった。

先例の手順 (D-level、`docs/decisions.md` の「役割契約」節) は
**「pin (manifest / adapter / review_ledger) は起草者と別の実装単位が、親の独立レビュー証跡を経て
更新した」**である。したがって:

- `coder-v4-autonomous-sort.md` の起草者 = 段 5 実装子、`auditor.md` の起草者 = fix 第 1 巡の子。
  **fix 第 2 巡の子はどちらの起草者でもないので、この要件を満たす。**
- 親は独立レビュー証跡を insight へ書く (段 7)。
- pin 閉包は `SOURCE_FILE_SHA256` に加え、`DESCRIPTION_SHA256` / `ROLE_MANIFEST_SHA256` /
  `SCHEMA_SHA256` / `ROLE_IO_CONTRACTS` / `codex_roles/manifest.json` /
  `test_reflux_originless_compatibility.py` の originless baseline を**実際の drift の有無で判定**して
  追随させる。役割の増減は無いので `EXPECTED_ROLE_COUNT` は 13 のまま。

## G4 — 既存 fixture の追随 (受理集合を狭めた当然の帰結)

`test_p3_s4_loop.py` / `test_p3_s4_loop_sort.py` の一部 fixture は、
comparator 言語と無関係の性質 (effect scanner の順序、marker の opt-in、auditor driver) を
検査しているのに、sort marker 経路で**受理される** comparator を必要としている。
受理集合を狭めたので、これらの fixture は正準 comparator へ差し替える必要がある。

**これは弱化ではない。** ただし次を厳守する。

- assertion を消す・緩める・反転する・skip する・xfail 化することは**禁止**。
- 差し替えてよいのは「受理される comparator が必要」という fixture の**入力**だけ。
- 拒否理由を期待する assertion は、**実装をバグに合わせて期待値を変えるのではなく**、
  G1 の修正後に本来の段の rule id になることを確かめて、正しい期待値にする。

## 変異事前登録の追加

G1 の修正に対して 1 件足す。

| # | 変異 | 機構固有の落ち先 |
|---|---|---|
| M11 | tokenizer が語彙外 token で例外を投げる版へ戻す | `test_backoff_grammar_dispatch_is_exact_marker_only` (期待 `sort-ir.envelope.v1`) |

## fix の分割

引き続き **1 子の一枚岩**。G1 は `sort_swo_oracle.py` の admission、G2 は同 module と
`p3_s4_loop.py` の正準化配線、G4 はその両方の consumer test、G3 は role pin である。
G1 を直すと G4 の期待 rule id が決まるため、分割すると期待値が単位を跨いで決まらない。
