# 段 1 brief — B-10 事前登録束縛から analysis_commit による再開拒否を外す

## scope

- 編集面は `orchestrator/campaign/b10_backoff_shape_sweep.py` と
  `orchestrator/tests/test_b10_backoff_shape_sweep.py` の 2 ファイルだけ。
- 除去対象は「現行 HEAD の commit ID と一致しない」ことだけを理由にした拒否 3 経路。
  (1) `PreregistrationBinding.core()` / `as_dict()` の `analysis_commit` (198/202/220/1393)
      — `assert_resumable_binding` の完全一致比較と `binding_sha256` に流入する。
  (2) `_validate_prior_block_records` の `row["analysis_commit"]` 比較 (2386)。
  (3) 同 `row["source_commit"] != prereg.binding.analysis_commit` 比較 (2388)。
- 内容ハッシュ束縛は 1 つも外さない: `analysis_code_sha256`、`spec_sha256`、`patch_sha256`、
  `formula_sha256`、`prereg_commit`、`prereg_blob_sha`。解析コード bytes を現 HEAD blob へ
  束縛する検査 (1378-1385) もそのまま残す。

## 確定済みユーザー裁定

- **D1163 (絶対規律 7)** — 現行コードとの差だけを単独の拒否理由にしない。
- **D1253** — 規律 7 を直接適用し、現行コードとの差だけを拒否理由にする具体的 consumer が
  見つかった場合だけ個別に修正する。事前登録・凍結・入力との束縛は維持する。
  本 wave はこの「個別修正」ちょうど 1 件である。
- **D1059** — 事前登録束縛が一致する既存 WAL への resume を許し、束縛の無い / 食い違う WAL は
  拒否する。束縛検査そのものは残す。
- **ユーザー引数** — 本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化は scope 外。

## 不変条件

- 絶対規律 2 を緩めない。本 wave は correctness gate に一切触れない。
- 内容ハッシュが食い違う WAL・ブロック記録は従来どおり拒否する。resume を無条件に許す変更にしない。
- 凍結事前登録文書 `docs/b10-backoff-shape-preregistration.md` を変更しない。
- `analysis_commit` の**記録はやめない** (規律 7)。束縛・比較・同一性ハッシュから外すだけで、
  provenance としてレポート行・ブロック記録には残す。

## 実測 (DW-S01 の前提検査・DW-O09 の pin 閉包)

- `analysis_commit` の出現は上記 2 ファイルに閉じる。`binding_sha256` の凍結 literal は repo に
  存在せず、すべて計算値。`docs/paper-story/figures/fig2c_b10_extended_backoff.provenance.json`
  にも 0 件。`p3_b4_admission_record.py` の `preregistration_binding` は別 schema
  (`repository_path`/`content_commit`/`content_sha256`) で無関係。
- 事前登録文書 §1 が列挙する束縛は「文書の blob SHA・その commit・patch SHA・式 SHA・
  spec SHA・解析コード SHA」で **analysis_commit を含まない**。`registration_rules` v4 閉集合
  (855-877) も束縛 field に触れない。よって除去は事前登録に反しない。
- `ANALYSIS_REL` は sweep 本体自身を指す。本 wave の編集自体が `analysis_code_sha256` を変える。
  既存 B-10 成果物の再開性はこの変更では回復しない (回復は目的でない)。
- `source_commit` は投入時 HEAD (471 行が `rev-parse HEAD` との一致を要求)。2388 行は過去 row の
  `source_commit` を現 HEAD と比べており、同型の偽の無効化である。
- 編集面重複: 稼働 branch tip・全 worktree の未 commit 差分ともに 0 件。

## 成果物影響 (DW-G05)

放置すると、B-10 の相 / workload 分割走で測定と無関係な commit が 1 つ入るだけで resume が
`PreflightError("resume-binding")` になり、完走済みブロック記録も `_validate_prior_block_records`
で棄却される。材料レポート `b10_backoff_shape_provenance.json` と report 表が組めず、
完走済み write-heavy の実測値ごと成果物から落ちる。

## (P1) 親の provisional 裁定 — 段 3 の攻撃対象

- **(P1-a)** `analysis_commit` は dataclass field として残し、`core()` から外す。全削除案
  (provenance も消す) は規律 7 の「記録はやめない」に反すると見る。
- **(P1-b)** `binding_sha256` の値が変わることを受け入れる。既存 on-disk 束縛は
  `analysis_code_sha256` の変化で同様に無効になるため増分の損失はゼロと見る。
- **(P1-c)** 2388 の `source_commit` 比較は代替検査へ置換せず単純除去する。`source_commit` は
  行の provenance として残す。
- **(P1-d)** 既存の `test_m17_and_p05_matching_bound_wal_is_resumable` と
  `test_m08_legacy_wal_without_binding_is_rejected_for_one_reason` は維持し、
  「解析コード bytes が同一で HEAD だけ違うとき resume が通る」正例と
  「`analysis_code_sha256` が違えば従来どおり拒否する」負例を新設する。

## 並列分割方針

段 2 plan 1 本。段 3 敵対相談 2 本 (レンズ A: 規律 2 / 束縛の弱体化、レンズ B: consumer 取り残しと
後方互換)。段 5 実装子 1 本 — 単一の producer/consumer 契約なので分割しない。段 6 review 2 本 + fix 1 本。
