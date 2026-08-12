# 段 1 brief 追補 — D291 (公表 core 承認 payload) の land が resolver の scope を変える

**この追補は段 2 プランナが読んでいない。** 段 2 のプランは D291 land 前の main を前提にしている。
段 3 の両レンズはこの追補を必読とし、段 4 で親が裁定する。

## 事実 (peer 通知 + 親が local main の逐語を確認)

- 2026-08-11、peer (`t139 core c2c2bc4` / wave `t139-pubcore-approve`) が公表 core 段階 2 の承認
  payload を land した。**local main = `b13b7ea8`**。この fold commit が **`F_p`** である。
- 採番は **D291**「公表 core v2 と source 追補 B v2 の exact bytes、および将来の追補 P の
  p01 / p02 の値だけを承認 payload として固定する」。
- **本 wave にとって決定的なのは次の 1 点である。**

```text
D291.approved_blobs:
  publication_core
    path   = output/insights/2026-08-11_t139-pubcore-stage2/publication-core-v2.md
    commit = 66934dda7f28893110a64a2011e213c2bda5e821
    sha256 = ad326dae70584d86470ff861e9bfd517b4f5b8406247f8047ae6cdb3ddabef67
  source_addendum_b                        <-- これ
    path   = output/insights/2026-08-11_t139-pubcore-stage2/addendum-b-v2.md
    commit = 25a66d2042a4fff1021e033c23fc2b814a735de9
    sha256 = ad12b60d29bb94ff67c3302b0779cb4765cd1c77768149d7cf6587698febb048
```

- `document_relations.source_addendum_b` は `role = addendum_b`、
  `satisfies = source_core.main_admission (requires_addendum_a_and_b)`、`depends_on = source_core`。
  すなわち **これは D234 の `submit_main` が要求する追補 B そのものである。**
- **D282 (`F_r`) の `approved_blobs` に `addendum_b` role は存在しない。**
  D291 は `source_study_inputs` で `addendum_a` を「参照のみ。承認の正本は D282」と明記し、
  逆に自分は `source_addendum_b` の exact bytes を承認している。
- D291 は D282 と同型の第 1 矢印を要求する — 「resolver は manifest を信用する前に、`F_p` の
  `docs/decisions.md` から本 payload を読み、role 集合・三つ組集合・`document_relations` の全 field・
  承認済み値集合・閉包条件が本 payload と exact 一致することを要求しなければならない」。
- D291 `exact_closure` は **allowlist 契約**である。`historical_candidates_rejected_for_role` は
  旧追補 B (`8e9a5b4dddfb85f7d31f671090cd24a7a4192e42` /
  `5071acbd9db18f022cb9603acef3a8cd3394ed17de80cc794468c1b1f5baa384`) を挙げ、
  **「本 payload に照らす限り resolver はこれを拒否しなければならない」** と課す。
  D282 の `not_approved_as_record_items_root` と同型の要求が 1 件増えた。
- `exact_closure` 6. は `document_relations` を**節全体**の exact 一致対象とし、
  「括弧内に挙がっていない field も照合対象」「key の追加も削除も解決失敗」と課す。
- `operational_state_on_fold`: `pilot_submission = forbidden` / `main_submission = forbidden`、
  `source_main_run_gate = not_implemented`。**本 payload の fold は source 本走の admission を
  閉じない。**

## これが本 session の何を変えるか

段 1 brief は「承認根は D282 @ `F_r` の 1 本」を暗黙の前提にしていた。**この前提は誤りになった。**

`resolve_effective_preregistration(repository_root, *, core_ref, addendum_a, addendum_b=None)` は
D234 決定 (7) の署名であり、**`addendum_b` を引数に取る。** 本 session がこの引数を
「承認根なしで」解決すると、それは §S7 #1 が指摘した穴 (未承認 blob が承認済み identity になる) を
`addendum_b` role で**新設する**ことになる。

## 親の provisional 裁定 (P6) — 攻撃対象

**(P6) resolver は承認根を 2 本読む。**
`core_ref` / `addendum_a` / `record_items` / `receipt_schema` / erratum 系は D282 @ `F_r` の payload、
`addendum_b` は D291 @ `F_p` の payload を trust root とする。
`addendum_b` が渡されたときは D291 の `source_addendum_b` 三つ組と exact 一致を要求し、
`historical_candidates_rejected_for_role.source_addendum_b` を明示的に拒否する。

**却下する代案と理由 (段 3 は両方を攻撃してよい):**

- (b) 本 session の resolver は `addendum_b=None` だけ受理し、非 None は fail-closed で次 session へ。
  → 親は反対する。D291 が land した今、承認済み追補 B の三つ組は**実在する**。
  非 None を必ず落とす実装は恒真 deny であり、`DW-S04` の「通る正例を 1 つ添える」を満たせない。
- (c) `addendum_b` も D282 から読む。
  → **誤りである。** D282 に `addendum_b` role は存在しない。

## 段 3 の両レンズへの追加の問い (必答)

1. **(P6) は正しいか。** 承認根が 2 本になることで、第 1 矢印の照合が甘くなる経路はないか。
   特に「どちらの payload を読むかを caller / manifest が選べる」経路を作っていないか。
2. **manifest の設計はこれで変わるか。** manifest は `approval_fold_commit` を 1 個持つ設計だったが、
   `F_r` と `F_p` の 2 個を持つのか、role 別に持つのか、それとも `addendum_b` は manifest の外か。
   **D291 の `exact_closure` 1. は「余剰 role、role の欠落、同一 path の別 digest は解決失敗」と課す。**
   D282 の閉包と D291 の閉包を 1 つの manifest に同居させる設計は、どちらかの閉包を破らないか。
3. **`document_relations` 節全体の exact 一致検査**を実装すると、production 行数はどれだけ増えるか。
   RP-1 (a) の「1 session」に入るか。**入らないと判断するなら、どこで切るのが正しいかを提案せよ**
   (裁定パッケージ候補として返すこと。親は勝手に scope を削らない)。
4. **`pilot_submission = forbidden` / `main_submission = forbidden` が fold 時点の状態である。**
   本 session の resolver が「解決成功」を返すことが、
   **「投入してよい」と読まれる経路**を作っていないか。`submit_pilot` / `submit_main` は
   本 session の scope 外である。解決成功と投入可否の分離をどう機械的に固定するか。
5. peer は **未裁定 1 件** を報告している — pilot / 本走の投入禁止の**解除条件・成立証拠・解除権限**が
   Q1〜Q7 から導けない (裁定パッケージ = `$R/output/insights/2026-08-11_t139-pubcore-approve/package.md`
   の R1、親推奨は (c) 解除権限だけ先に決める)。**これは本 session の RP-4 と重なる可能性がある。**
   重なるなら、本 session が実装してよい範囲がどこまでかを述べよ。
   **本 session は pilot を投入しないので、この未裁定は本 session の blocker ではない**というのが
   親の判定である。これを攻撃せよ。

## 取り込みの段取り (親の運用)

段 2 プランナが worktree を read-only で読んでいる最中なので、`b13b7ea8` の取り込みは
**段 3 完了後・段 4 の前**に行う。今 merge すると段 2 プランの `file:line` がずれる。
段 4 の裁定は取り込み後の tree に対して行う。
