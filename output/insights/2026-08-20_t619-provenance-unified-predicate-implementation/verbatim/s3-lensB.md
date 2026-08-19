大筋では、repo 全体の実行時 consumer は `main()` と対象テストだけで、他の tool・hook・CI 相当の呼び出しは見つかりませんでした。B2/B4 や新 ledger kind に踏み込む記述もありません。ただし、次は段2プランに反映すべきです。

[must-fix] [s2/plan.md:183-191; orchestrator/tests/test_check_ai_provenance.py:3660-3661] explicit `--range` でも `_scope_policy_commit(None)` / `_implementation_policy_commit(None)` と呼ぶため、既存の no-arg monkeypatch が `TypeError` になる。`test_forward_correction_merge_base_rc128_fails_closed_with_rc2` が意図した merge-base エラー検査に到達しない → `authoritative` 時だけ `head` を渡し、非 authoritative 時は従来どおり引数なしで呼ぶ。併せてこの回帰テストを維持する。

[must-fix] [s2/plan.md:366-420, 720-744] HEAD を一度だけ固定する処理と終了時 drift の実装案はあるが、固定 SHA が policy resolver・epoch resolver・ancestry builder 全体に伝播すること、および drift 時に rc=2 で出力を抑止することを検証するテストがない → default audit 専用に「HEAD の二重取得がない」「開始後の HEAD 変更は rc=2」の独立テストを追加する。

[must-fix] [s2/plan.md:660-671] authoritative epoch の side-branch fixture が scope 違反と Codex author 欠落を同時に持つため、DW-M01 の「単一理由」変異にならない → scope-only と implementation-only の fixture に分割する。shallow/graft/replace、policy add 非一意、HEAD drift、CAB、ledger 欠落も各 mutation を単独理由で登録する。

[must-fix] [s2/plan.md:528-536, 752-762] 新 ledger の ruling `"worklog(299) 2026-08-07 /rulings"` は archive 済み entry 299 を指す旧記法で、T-720 以降の self-locating 規約と不整合 → 例えば次へ変更し、literal test も更新する。

`2026-08-07 [T-619] D230 統一述語の既定監査導入・333605d6 登録 (ユーザー裁定 entry 299)`

[must-fix] [docs/decisions.md:10798-10817] D230 は元の設計 wave では実装しないという歴史的 decision なので、D230 自体を書き換えると履歴意味が変わる。段2プランは新 D の内容と stage7 記録を具体化していない → D230 は保持し、次の canonical D を追記して「D230 の実装 wave への展開」「entry 299 の五項目」「333605d6 と docs byte 改訂」を参照付きで記録する。新 worklog entry も追加し、旧 archive と insight package は変更しない。

[nit] [s2/plan.md:625-637; tools/check_docs.py:219-252, 4928-4940] `check_docs.py` の実行時検査（4890-5310）はほぼ網羅されているが、provenance dispatch contract と bounded file-map 構築の定義範囲が棚卸しリストから漏れている → 検査項目一覧に追加する。挙動上の漏れではない。

[nit] [scope: 外] [tools/check_ai_provenance.py:1170-1176] `_scope_policy_commit` の `-S "scope="` 非一意性は design B2/T629 の対象外 → 本 wave では uniqueness 検査や新 ledger kind を追加せず、T629 へ委譲する。段2プランの境界は適切。

[nit] [scope: 外] [tools/check_ai_provenance.py:1413-1446] `_build_ancestry` の ARG_MAX・bitset scaling は design B4/T630 の対象外 → authoritative 用の tip/mask 変更に留め、入力分割や bitset 再設計は行わない。段2プランの境界は適切。

`docs/failures.md` の F361 と `docs/spool/FOLDED.md` の T619 allocation は歴史記録であり、333605d6 の直接参照切れは見つかりませんでした。更新対象は新 D と新 worklog で、既存 archive/FOLDED の書き換えではありません。

## 総括

consumer 網羅性と scope は問題ありません。実装前に、explicit-range monkeypatch 回帰、HEAD pin/drift の実証、単一理由 mutation、ruling 表記、D230 を保持した新 D の五点をプランへ追加すべきです。