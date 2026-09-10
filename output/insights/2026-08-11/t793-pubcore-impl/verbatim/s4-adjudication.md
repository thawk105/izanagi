# 段 4 裁定 — [T-793]

親が段 2 プランと段 3 レンズ A / B を real / refuted、採用 / 不採用、scope 内 / 外に裁定する。
**親が独立に実測した所見は「親実測」と記す。子の結論をそのまま採らない。**

## 0. 結論

**4 必須要件のうち、本 wave が閉じるのは (ii) と (iv) + (iv-b)、および (i) の識別束縛の半分だけである。**
(iii) と (i) の原子性は、**裁定時点で未見だった新事実**により本 wave では閉じられない。
`DW-S04` に従い、親が不採用にせず**新事実付きでユーザー再裁定へ戻す**。

**本 wave は「公表層を機械執行した」と主張しない。** §10.4 の 11 変異のうち、
実成果物経路で拒否できるのは **0/11**、直接 parser の負例として拒否できるのは **#7 と #9 の 2/11** である。

## 1. 所見の裁定

### real (親が独立に実測して確認した)

| id | 所見 | 親の実測 |
|---|---|---|
| **A6** | 計画の D291 parser は canonical `F_p` bytes を読めない | **親実測で確認。** `git show b13b7ea8:docs/decisions.md` に `## D292` は **0 件**。D291 が最後の見出しで、file は 13579 行で EOF。「D292 の直前まで」で切る parser は trust root そのものを読めない |
| **A4 / B1** | marker gate を `_discover()` だけに置くと fold 経路を覆えない | **親実測で確認。** `tools/spool_fold.py:2505-2506` が `if not args.dry_run and state_path.exists(): plan = _state_plan(_load_state(state_path))` で resume し、`plan_fold()` も `_discover()` も通らない。`apply_fold()` も plan を直接受ける |
| **B5** | land 2 は共有 file を変更しており「file 非重複」≠「統合面ゼロ」 | **親実測で確認。** land 2 は `preregistration/blobref.py`・`erratum.py`・`tests/test_t139_preregistration_binding.py` を変更している。**親 brief の「`__init__.py` すら衝突しない」は言い過ぎだった** |
| **B6** | JSONL の append-only / delete-recreate 拒否は既存 | **親実測で確認。** `orchestrator/campaign/trial_registry.py` に `_canonical_json_bytes`・`flock`・`fsync`・`_assert_history_append_only`・`_lifecycle_history_tip` (「path was deleted in committed history」で拒否) が実在する。**親 brief の純増検出力の見積もりは過大だった** |
| A1 / A2 | 台帳が worktree 選択で複製でき、予約行を canonical history に固定する transaction が無い | real。同一 Git common directory を共有する別 worktree から同じ `(root, kind, 1)` を二重取得できる。**scope 外へ (下記 2.)** |
| A3 / B2 / B3 | (iii) は実 caller が無く孤児 gate になる。`submit_main` が存在しない | real。**scope 外へ (下記 2.)** |
| A7 | `F_p` を caller が差し替えられる公開 parser | real。**採用 — 設計で閉じる** |
| A8 | 単一 role resolver が `exact_closure` の「集合ちょうど」を迂回する | real。**採用 — 単一 role API を作らない** |
| A9 | P exact-key parser に production caller が無い | real。**部分採用** — parser は作るが「production caller なし・単体検査のみ」と明記する |
| A11 | resolver が D291 の後続 supersession scope を無視する | real。**採用** — report は HEAD 側の supersede 有無を走査して明示する |
| A5 | `approved_blobs:` は全承認 decision の閉じた schema ではない | real。**部分採用** — guard の保証範囲を `approved_blobs:` 形式に限定して記録する。全承認への一般化は裁定へ |
| B4 | 0-byte tracked 台帳は既存検査を全部通る | real。**採用** — 台帳専用の独立 gate を持つ |
| B7 | 変異の帰属が成立しない組合せがある | real。**採用** — 変異事前登録 (下記 3.) に反映 |
| A10 | 親の「root 不一致は blocker でない」は一般化できない | **部分 real。** 互いに素性の結論は強まる方向という親の判断は維持する。しかし「承認済み文書の命題が偽のまま『適合』と報告される」という指摘は正しい。**裁定へ返す (下記 2.)** |

### refuted

| id | 所見 | 却下理由 |
|---|---|---|
| — | 段 2 プランの「`_discover()` に置けば全 fold 経路が共有する」 | **B1 が正しく、プランが誤り。** 親も実測で確認した |
| — | 親 brief (P5)「`spool_fold.py` を変更しない」 | **親自身の (P5) を撤回する。** (ii) が実効 gate であるためには `spool_fold.py` の変更が要る。B1 が指摘した所有境界の衝突は、親が (P5) を撤回することで解消する |

## 2. scope 外 — ユーザー再裁定へ返す (実装しない)

`DW-S04`「承認済み裁定を止めてよいのは裁定時点で未見の新事実がある場合だけ。
止めるときも親が不採用にせず、新事実付きのユーザー再裁定待ちへ戻す」に従う。

| # | 返す項目 | 未見だった新事実 |
|---|---|---|
| **R1** | **(iii) source 側の本走 gate (Q1 (a) の裁定条件)** | (a) 承認済み pubcore v2 §10.2 が「`submit_pilot` / `submit_main` が本書の存在を要求するようにしてはならない」と**明示的に禁じており**、Q1 (a) の条件と正面から衝突する。(b) `submit_main` は repo に**存在せず**、land 2 が scope 外と宣言した所有物である。(c) D291 自身の `operational_boundary` が「本 payload は source 本走および pilot の admission を保証しない」と明記する。→ **Q1 (a) の条件は本 wave では履行されない** |
| **R2** | **(i) の原子性・(root, ordinal) 一意性・予約 writer** | 同一 Git common directory を共有する worktree 間で、file lock と inode では一意性が成立しない (A1)。canonical main + land lock + 初出 commit 再導出との一体化が要る。これは `tools/dev_wave_land.py` (機械防壁) の変更であり、D291 の `operational_boundary` も「本 payload は公表台帳の実体・予約の原子性・(root, ordinal) の一意性を保証しない」と明記する |
| **R3** | **pubcore v2 §8.1 の偽命題の扱い** | 承認済み文書が「`family_root` が primary 系列と同じ commit である」と断言するが、land 済み primary 台帳は `dce4ae4f…` で公表側 `88d68f91…` と別 commit である (親実測、両レンズが独立に再現)。文書は承認 bytes なので編集できない。canonical erratum / decision で正す必要がある |
| **R4** | **marker gate の保証範囲** | guard が拒否できるのは `approved_blobs:` 形式で triple を宣言する fragment だけである (A5)。散文で承認を述べる fragment は target 空集合になり素通りする。「全承認に効く」と主張するには、blob authority を与える decision に機械可読 schema を必須とする裁定が要る |
| **R5** | **予約 entry の発行 (ordinal 1 の消費)** | 本 wave は発行しない。D292 が pilot / 本走の禁止解除を canonical decision に限定しており、「実装したから ordinal 1 を予約する」という推論は成立しない |

## 3. 本 wave で実装する (プラン v2)

### 3.1 実装するもの

新規 package `orchestrator/publication/`。**`orchestrator/preregistration/` は 1 file も変更しない**
(B5: land 2 が `blobref.py` / `erratum.py` を変更中。`BlobRef` / `read_pinned_blob` は **import のみ**)。

| lane | file | 内容 |
|---|---|---|
| **A** | `approval_d291.py` | D291 payload の parser + resolver。**A6 修正**: 節の終端は「次の `## ` 見出し **または EOF**」で決める (`F_p` では EOF)。**A7 修正**: 公開 loader は `F_p` を module 内 literal で固定し、caller に commit を選ばせる引数を持たない。任意 bytes を取る parser は private (`_parse_d291_payload`)。**A8 修正**: 単一 role を解決する公開 API を作らない — payload 全体を `exact_closure` (role 集合ちょうど 2、三つ組一致、`document_relations` 節全体一致、値集合、14 top-level key) で検証してから role→状態の写像を一括で返す |
| **A** | `report.py` | deny-only の report。`submission_authority = "not_granted"`、`pilot_submission = "forbidden"`、`main_submission = "forbidden"` を**常に**含める。**A11 修正**: HEAD 側の `docs/decisions.md` を走査し、D291 を supersede する後続 decision の有無を `supersession_scan` として報告する。見つかったら承認済みと断言しない |
| **B** | `ledger.py` | 公表台帳の**識別束縛のみ**。固定 literal (`family_root = 88d68f91…`、`ledger_kind = individual_publication`) から canonical path を導出し、**caller の引数・環境変数・設定 file の口を作らない**。entry 0 件の状態を「台帳は存在するが予約は無い」と一意に表す。**予約 writer は作らない (R2)**。Git 履歴による delete/recreate 拒否は `trial_registry` の既存 primitive と同型だが、公表固有の (root, kind) 束縛と primary 空間との互いに素性が純増分である (B6) |
| **C** | `approval_guard.py` | (ii) marker gate。`__UNRESOLVED_APPROVAL_FOLD_COMMIT__` / `__UNRESOLVED__` の exact 2 語だけを拒否する (一般の「未確定」語は拒否しない)。**B1/A4 修正**: `_discover()` だけでなく **`apply_fold()` の state / resume 適用前**にも同じ検査を通す |
| **C** | `addendum_p_envelope.py` | (iv-b) `{p01, p02, p03}` の exact-key wrapper。既存 `parse_addendum_fields()` に固定集合を渡す**薄い wrapper**に限定する (B6)。docstring に「production caller なし・単体検査のみ」と明記する (A9/B3) |
| **C** | `tools/spool_fold.py` の変更 | (ii) の結線。**親の (P5) を撤回して変更する** |

### 3.2 実装しないもの (明記する)

予約 writer、`submit_main` への結線、`admission.py` の成功系、追補 P の凍結、
公表 validator / renderer / consumer、`FROZEN_MANIFEST` の増減、
`orchestrator/preregistration/` の全 file、`output/registry/t139-alpha-reservations.jsonl` への追記。

### 3.3 D292 との整合 (不変条件)

- `is_submission_allowed` / `ready_for_main` / `admitted` / `can_submit` / `approval_complete` を
  **作らない**。成功を `True` で返す API を作らない (例外で落ちる `require_*` 型にする)。
- report の成功・実装完了・台帳の存在のいずれも D292 の解除条件にしない。

## 4. 変異事前登録 (`DW-M01`。B7 の帰属不成立を反映)

**単一理由性を確保するため、1 fixture 1 変異に分離する。**
B7 が挙げた競合 (digest gate が relation gate を先取りする、marker gate が後段の spool guard を
先取りする) を避けるため、**bytes parser の seam (`_parse_d291_payload`) に対して変異を当てる**。

| # | 変異位置 | 期待 | 単一理由性の確認 |
|---|---|---|---|
| M1 | `approval_d291.py` の節終端判定を「次の `## ` 見出し」→「`## D292` 固定」へ | KILLED | `F_p` bytes を読む正例テストだけが落ちる。前後に同じ入力を拒否する層は無い |
| M2 | top-level exact-key 集合から 1 key を削除 | KILLED | 14 key 検査だけが落ちる |
| M3 | `document_relations` の節全体一致を role 名一致へ緩める | KILLED | `note` を 1 文字変えた負例が bytes parser seam で落ちる (実 blob path を通さないので digest gate と競合しない) |
| M4 | `approved_blobs` の role 集合検査を「2 以上」へ緩める | KILLED | 余剰 role の負例だけが落ちる |
| M5 | 三つ組照合から `sha256` を外す | KILLED | 同一 path 別 digest の負例だけが落ちる |
| M6 | `ledger.py` の canonical path 導出に caller 引数を通す口を開ける | KILLED | 「caller が path を選べない」負例だけが落ちる |
| M7 | `ledger.py` の `ledger_kind` 閉集合検査を外す (§10.4 #7) | KILLED | 閉集合外 kind の負例だけが落ちる |
| M8 | `approval_guard.py` の marker 集合を空へ | KILLED | marker 負例だけが落ちる |
| M9 | marker gate の結線を `apply_fold()` から外す | KILLED | resume 経路の負例だけが落ちる (`_discover()` 経路の正例は緑のまま) |
| M10 | `addendum_p_envelope.py` の期待集合を `{p01,p02}` へ (§10.4 #9) | KILLED | `p03` 欠落検出の負例だけが落ちる |
| M11 | `report.py` から `submission_authority` を落とす | KILLED | deny-only report の負例だけが落ちる |
| M12 | `report.py` の `supersession_scan` を常に空へ | KILLED | supersede 検出の負例だけが落ちる |

**過剰拒否の正例 (受理集合を縮小する wave のため `DW-M01` が要求):**

| # | 正例 | 期待 |
|---|---|---|
| P1 | 実 `F_p` bytes の D291 payload | **受理**する (A6 の回帰。これが落ちたら trust root が読めていない) |
| P2 | `addendum-p-draft.md` (marker 入りの草案) が insights に置かれているだけの状態 | **fold を止めない** (全面禁止にしない) |
| P3 | `{p01, p02, p03}` ちょうどの追補 P envelope | **受理**する |
| P4 | entry 0 件の canonical 公表台帳 | **「台帳は存在するが予約は無い」として受理**する (不在と区別する) |

## 5. 段 5 の分割

| lane | 所有 path (素集合) |
|---|---|
| A | `orchestrator/publication/approval_d291.py`, `report.py`, `orchestrator/tests/test_t793_approval_d291.py`, `test_t793_report.py` |
| B | `orchestrator/publication/ledger.py`, `orchestrator/tests/test_t793_publication_ledger.py` |
| C | `orchestrator/publication/approval_guard.py`, `addendum_p_envelope.py`, `tools/spool_fold.py`, `orchestrator/tests/test_t793_approval_guard.py`, `test_t793_addendum_p_envelope.py` |

`orchestrator/publication/__init__.py` は lane A が作り、B / C は触らない (統合後に親が確認)。
