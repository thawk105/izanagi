# 段 4 裁定 — [T-618] 既知違反台帳への `3f2c43d7` 追加

## 所見の裁定表

| # | 出典 | 所見 | 判定 | 採否 | scope |
|---|---|---|---|---|---|
| L1-1 | lens1 | 自動 dev-wave 層 (`dev_waves/checker.py` → `task_run_check.py`) は stdout を捨て rc=0 だけで pass。`PR-A02` の「緑と読むな」が機械化されていない | **real** | 実装しない | **scope 外** — 既起票 [T-621] |
| L1-2 | lens1 | 既定範囲の `--ancestry-path` に pre-policy branch merge の blind spot | **real** | 実装しない | **scope 外** — 既起票 [T-619]。brief が範囲式変更を明示的に scope 外にしている |
| L2-1 | lens2 | 非空 `note` の stdout 契約が rc=0 側でしか pin されない。rc=1 側だけ旧 formatter のまま残しても計画済みテストが検出しない | **real** | **採用** | scope 内 |
| L2-2 | lens2 | 「LF・CR・Unicode line separator を一括拒否」と書きながら LF 1 例しか pin しない | **real** | **採用** | scope 内 |
| L2-3 | lens2 | 変異候補「新 entry 削除 / SHA drift」が単独帰属しない (4 経路が同時に不成立) | **real** | **採用** | scope 内 (変異事前登録の是正) |
| L2-4 | lens2 | 変異候補「stale raise 削除」も単独帰属しない (5 node が同じ層を要求) | **real** | **採用** | scope 内 (同上) |
| L2-5 | lens2 | caller 列挙が `tools/dev_waves/` の固定 check 層を落としている | **real** | 射程限定のみ | L1-1 と同一 = [T-621] |
| L2-6 | lens2 | 新記録が何を supersede するかが受入項目になっていない | **real** | **採用** | scope 内 (段 7 の記録契約) |
| L2-r6 | lens2 refuted 6 | D221 は台帳 schema を 3 要素と明記しており、`note` 追加だけ land すると本文と実装が食い違う | **real** | **採用** | scope 内 (段 7 で decisions fragment) |
| L2-sp1 | lens2 speculative | `note` guard の predicate を逐語指定しないと、型検査除去時に `AttributeError` が `main()` の `except (OSError, RuntimeError, UnicodeError)` を素通りする | **real に格上げ** | **採用** | scope 内 (親が `check_ai_provenance.py:2050` を実読して確認) |
| L2-nit | lens2 nit | 段 5 を 2 単位に分割できる | refuted しない が **不採用** | — | 下記 |
| L1-sp1 | lens1 | `note` に `sha=` 様の文字列や ANSI を入れると表示を惑わせうる | nit | 不採用 | 研究プロトタイプ方針。受理集合でなく表示の問題で、注記の実文字列は親が固定する |

**段 5 の 1 単位維持の理由 (L2-nit への回答):** 受理集合は分割しても変わらず、差は wall-clock と作者分離だけ
という lens2 自身の評価に同意する。そのうえで 1 単位に留める積極的理由は、**`note=` の stdout 逐語を
production と test の 2 単位が独立に決めると必ず食い違い、統合時に「どちらが正か」の裁定が要る**こと。
変更規模 (production 約 25 行 / test 約 90 行) は 1 単位で収まる。

## plan v2 (段 2 プランからの差分)

段 2 プランを基礎に、次を上書きする。それ以外はプランのままとする。

1. **(L2-sp1) `note` guard の predicate を逐語で固定する。** `_known_violation_registry()` の
   `ruling` 検査 (221–225 行) の直後、`registry[spec.commit] = spec` (226 行) の直前に、次の順で置く。

   ```python
   if not isinstance(spec.note, str):
       raise RuntimeError(
           "known provenance violation registry has invalid note type: "
           f"{type(spec.note).__name__}"
       )
   if spec.note != "" and spec.note.splitlines() != [spec.note]:
       raise RuntimeError(
           "known provenance violation registry has line break in note: "
           f"{spec.commit}"
       )
   ```

   `spec.note != ""` の前置は必須である。これが無いと `"".splitlines() == []` が `[""]` と一致せず、
   既存 6 件の空 note が全部 rc=2 になる。`splitlines()` は LF / CR / CRLF / U+2028 / U+2029 /
   U+0085 等をすべて分割するため、改行族を一括で拒否する。

2. **(L2-1) rc=1 側の非空 note stdout を pin するテストを追加する。** プランの
   `test_ledgered_3f2c43d7580b_is_known_and_rc0` に加えて、**同一 range に「非空 note を持つ既知 1 件」と
   「未台帳の新規違反 1 件」を置き、rc=1 で既知行に ` note=…` が出ることを exact に pin する**
   合成テストを新設する。既存の
   `test_known_violation_stdout_is_public_on_rc0_and_rc1` (空 note の逐語) は変更せず残す。

3. **(L2-2) 改行 case を parametrize matrix にする。** 新設 `test_broken_registry_note_is_rc2` の
   改行 case を最低 4 つ (`"\n"` / `"\r"` / `"\r\n"` / `" "`) にし、`ids` を明示する。
   非 str case (`None`) は同関数に残す。全 case で `site=site_policy.OTHER` を明示する。

4. **(L2-3 / L2-4) 変異事前登録を下記のとおり差し替える。** プランの 6 候補のうち
   「entry 削除 / SHA drift」は integration 変異として期待 node を全列挙し、
   「stale raise 削除」は本 wave の差分でない既存層のため候補から外す。

5. **注記の実文字列を親が固定する** (子に文言を作らせない)。逐語:

   ```text
   trailer は本文に実在するが、AI-Agent 行と Co-Authored-By 行の間の空行で trailer block 不成立
   ```

   裁定文の注記と同義で、backtick と読点の入れ子を避けた 1 行。`;` も改行も含まない。

6. **ruling 文字列** = `"worklog(293) 2026-08-07 /rulings"` を entry 内リテラルで書く
   (プランの (P2) 判断を採用。`_KNOWN_VIOLATION_RULING` は変更しない)。

## gate の署名と正例 (`DW-S04`)

**禁止 (署名):**

```text
_known_violation_registry() は、いずれかの KnownViolationSpec について
  (a) spec.note が str でない、または
  (b) spec.note != "" かつ spec.note.splitlines() != [spec.note]
のとき RuntimeError を送出する。history 監査は main() の
except (OSError, RuntimeError, UnicodeError) で rc=2 に畳まれ、known-violation 行を 1 行も出さない。
```

**通る正例 1 つ:**

```text
KnownViolationSpec("3f2c43d7580b8c26724d90278589862057508965", "missing-ai-agent",
                   "worklog(293) 2026-08-07 /rulings",
                   note="trailer は本文に実在するが、AI-Agent 行と Co-Authored-By 行の間の空行で trailer block 不成立")
→ 受理され、stdout に
  check_ai_provenance: known-violation sha=3f2c43d7… finding=missing-ai-agent note=trailer は…不成立
  が出る。rc は新規違反だけで決まる。
```

## 変異事前登録 (`DW-M01`)

| ID | 変異 | 種別 | 期待 | 単一理由性の確認 |
|---|---|---|---|---|
| **M1** | `KNOWN_PROVENANCE_VIOLATIONS` から 7 件目 entry を削除 | integration | KILLED。期待 node **4 本**: `test_known_violation_ledger_is_exactly_seven_literal_entries` / `test_known_violation_ledger_matches_real_commit_findings` / `test_empty_registry_restores_all_seven_real_findings` / `test_ledgered_3f2c43d7580b_is_known_and_rc0` | 赤理由は「entry 不在」の 1 つ。node が 4 本になるのは検出層が 4 つあるためで、理由の分散ではない (L2-3 を受け、単独帰属の主張を撤回して全 node を登録) |
| **M2** | `_known_violation_line()` の note suffix を無条件に落とす | negative | KILLED。期待 node **2 本**: `test_ledgered_3f2c43d7580b_is_known_and_rc0` / 新設 rc=1 合成 stdout テスト | 台帳照合と rc は正常に通り、note を補う別層は無い。赤理由は「suffix 欠落」1 つ |
| **M3** | **rc=1 側の出力ループだけ** helper を迂回し旧式 (`sha=… finding=…`) で出す | negative | KILLED。期待 node **1 本**: 新設 rc=1 合成 stdout テストのみ | L2-1 が指摘した穴そのもの。rc=0 側は不変なので `…is_known_and_rc0` は緑のまま残る。この変異が SURVIVE したら L2-1 は未修理 |
| **M4** | `note` guard 2 本 (型 + 改行) を**まとめて**削除 | negative | KILLED。期待 node **1 本 (全 case)**: `test_broken_registry_note_is_rc2` の 5 case すべて | fail-closed (rc=2) → fail-open (rc=0 + 壊れた stdout)。受理集合が変わるので `DW-M03` の kill 条件を満たす |
| **M5** | 改行検査**だけ**を削除 (型検査は残す) | negative | KILLED。期待 node: `test_broken_registry_note_is_rc2` の改行 4 case のみ (`non-str` case は型検査に救われて緑) | 前段の型検査は改行入り str を拒否しない。赤理由は「改行が stdout 行へ到達」1 つ |
| **P1** | (正例 control) 変異なしの本走 | positive | 全 node 緑 + 既定 full 監査 rc=0 / known=7 / new=0 | `DW-M01` の「受理集合を変える wave では承認外の過剰拒否を検出する正例」。note guard の新設が正しい注記まで拒否していないことを示す |

**候補から外したもの (`DW-M01` の「確認できなければ登録しない」に従う):**

- **型検査だけを削除** — `note=None` で改行 predicate が `None.splitlines()` を呼び `AttributeError` になる。
  `main()` の `except` は `(OSError, RuntimeError, UnicodeError)` だけを捕捉する
  (`tools/check_ai_provenance.py:2050` を親が実読して確認) ため例外は素通りし、fail-closed のまま。
  受理集合は変わらず `DW-M03` の kill にならない (診断だけの赤)。M4 に吸収する。
- **SHA drift** — registry validator (full SHA / 重複) が先に rc=2 にするため、変異が台帳照合層へ届かない。
- **stale raise 削除** — 本 wave の差分ではない既存層で、同じ層を 5 本の既存 node が要求する
  (L2-4)。本 wave の検出力を測らないため外す。
- **`note` 既定値を非空へ変更** — 既存 6 entry と 13 箇所の `_known_spec()` 呼び出しへ同時に波及し、
  赤理由が分散する。

## 段 5 の分割

**Codex `role=author` 1 単位。** 編集面 = `tools/check_ai_provenance.py` と
`orchestrator/tests/test_check_ai_provenance.py`。worktree 分割なし。

## 段 7 で必ず記録する (L2-6 / L2-r6)

- **D221 の addendum** — 台帳 schema が 3 要素から `note` を含む 4 要素になったこと、`note` は既定空・
  optional・単一行必須で、rc / 照合条件には影響しないこと。decisions fragment で書く。
- **supersede 関係** — 過去記録 (worklog 289 の「7 件目は台帳に入れなかった」、T-614 insight の
  「既知 6 / 新規 1 / rc=1 が期待値」) は**書き換えず**、新しい T-618 記録で
  「worklog(293) の再裁定によって運用状態が supersede された」ことと最終 HEAD の実測値を書く。
- **[T-621] は未解決である**ことと、本 wave の land 証拠が自動 receipt でなく
  **post-commit の権威 full 監査の生 stdout** であることを明記する (L1-1 / L2-5 の射程限定)。
