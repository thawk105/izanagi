---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-11
wave: dev-wave-t793-pubcore-impl
seq: 1
---

## {{D:publication-trust-root}}. D291 payload の trust root は `F_p` の実 bytes に固定し、caller が payload を注入する公開経路を作らない

**決定:** 公表層の承認 resolver と report は、**必ず `F_p` (`b13b7ea840ad51199f40b3a534c9d1cdb422af2e`)
の `docs/decisions.md` を毎回読んで payload を導出する。** 次の 4 つを禁じる。

1. **caller が構築した payload object を権威として受理する公開 API。**
   `require_d291_projection_exact()` / `approval_report_to_dict()` は
   payload / report object ではなく repository root だけを受け取る。
   payload・resolution・report の型は公開名から外す。
2. **`F_p` を差し替えられる公開引数。** `fold_commit` を override できる公開経路を持たない。
   任意 bytes を受け取る parser は private に限定し、テストからのみ使う。
3. **単一 role だけを解決する公開 API。** payload 全体を `exact_closure`
   (top-level key ちょうど 14、`approved_blobs` の role ちょうど 2、三つ組一致、
   `document_relations` 節全体の一致、`value_projection` 9 行) で検証してから、
   role → 状態の写像を一括で返す。
4. **D291 節の終端を `## D292` という literal で決めること。**
   終端は「次の可視 `## ` 見出し **または EOF**」とする。

**理由:**

- **`F_p` に D292 は存在しない。** `git show b13b7ea8:docs/decisions.md` は D291 を最後の見出しとして
  13579 行で EOF になる。`## D292` を終端 literal にすると、**trust root そのものを読めない**。
  現在の checkout には D292 があるため、この誤りは現行 HEAD を読む限り露見しない。
- **caller 注入は trust root を無効化する。** 偽 payload を構築すれば `F_p` を一度も読まずに
  任意の値を承認済みにできる。D291 自身が「resolver は manifest を信用する前に `F_p` の
  `docs/decisions.md` から本 payload を読め」と要求しており、caller 注入はこれを迂回する。
- **単一 role API は `exact_closure` を迂回する。** D291 の閉包は「role 集合**ちょうど**」を要求する。
  単一 triple を渡して承認を返す口があると、`publication_core` を欠落させた manifest が
  `source_addendum_b` だけの照合で通る。
- **`document_relations` は節全体が照合対象**であり、散文の `note` 行も含む。
  役割名だけの一致にすると、三つ組と値を保ったまま `depends_on` / `satisfies` /
  `pins_source_study_one_way` を差し替えた manifest が通る。

**却下した選択肢:**

- **payload 引数を残しつつ型で守る** — dataclass は外部から構築できる。型検査は出自を証明しない。
- **`F_p` を設定 file や環境変数で与える** — 呼び手が trust root を選べる時点で trust root ではない。
- **`document_relations` を field 単位で照合する** — D291 が「括弧内に挙がっていない field も
  照合対象である」と明記しており、列挙は必ず取りこぼす。

## {{D:marker-gate-scope}}. 未確定 marker gate は fold の 3 経路すべてで「書かれる bytes」を検査し、保証範囲を `approved_blobs:` 形式に限定して記録する

**決定:**

1. **検査対象は fragment ではなく、実際に canonical へ書かれる `after_bytes` である。**
   `_discover()` / `apply_fold()` / CLI resume の 3 経路すべてで同じ検査を通す。
2. **拒否するのは exact 2 語** (`__UNRESOLVED_APPROVAL_FOLD_COMMIT__` と `__UNRESOLVED__`) が
   **承認 payload の pin する blob に含まれる場合だけ**とする。
   一般の「未確定」語や、草案として insights に置かれているだけの文書は拒否しない。
3. **`approved_blobs:` 節の構文破壊・重複は専用 code で拒否する** (握り潰さない)。
4. **形の正しい三つ組の解決失敗は拒否せず、診断だけ残す。**
5. **保証範囲を `approved_blobs:` 形式で三つ組を宣言する fragment に限定して記録する。**
   散文で承認を述べる fragment は検査対象が空集合になり素通りする。
   **「全承認に効く」とは書かない。**

**理由:**

- **`_discover()` だけでは覆えない。** `tools/spool_fold.py` の CLI は active state があるとき
  `_state_plan(_load_state(...))` を直接読み、`plan_fold()` も `_discover()` も通らない。
  `apply_fold()` も plan を直接受け取る。gate 導入前に作られた state を resume すると、
  marker 入りの `after_bytes` がそのまま適用される。
- **fragment を検査しても書かれる bytes は守れない。** hash が合う fragment が 1 つでもあれば
  それだけを見る実装では、marker の無い正規 fragment の receipt と、marker 入り blob を承認する
  `after_bytes` を組み合わせた plan が通る。
- **握り潰しは fail-open である。** 壊れた / 重複した triple を黙って捨てると、
  marker 入り blob を正しく pin する role に同じ `sha256` 行をもう一度足すだけで検査集合が空になる。
- **解決失敗まで拒否すると受理集合が縮む。** 形は正しいが commit が repo に無い三つ組は、
  そもそも何も pin していない別問題であり marker gate の責務ではない。従来は通っていた。
  「構文が壊れている」と「形は正しいが解決できない」を別 code で区別する。
- **全面禁止にできない。** `output/insights/2026-08-11_t139-pubcore-stage2/addendum-p-draft.md` は
  草案として marker を正当に持つ。marker の存在だけで赤にすると land 済み文書で即座に赤になる。
- **保証範囲を書かないと過大に読まれる。** 「marker gate があるから承認は安全」という読みは
  散文形式の承認宣言に対して成立しない。

**却下した選択肢:**

- **`check_docs.py` 側だけに置く** — `plan_fold()` を直接呼ぶ経路と resume 経路を覆えない。
- **marker を含む文書を repo 全体で禁じる** — 正当な草案が land 済みであり即座に赤になる。
- **解決できない pin を一律拒否する** — marker と無関係な既存 fragment の fold を止め、
  受理集合を縮める。本 wave が足してよいのは新しい deny だけである。
