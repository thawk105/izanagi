単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2273-issue-subprocess

作業木 (あなたが書いてよい唯一の木): /work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273is-impl (branch fix-t2273is-impl-1、HEAD は段 5 の実装を含む)
所有 path (これ以外を編集しない): `orchestrator/campaign/s8b_holdout_freeze.py`、`orchestrator/tests/test_s8b_holdout_freeze.py`。
docs は編集しない。commit しない (起動器が終端で記録する)。

必読事項の射影 (読めなければ即停止し、読めなかった path を書いて終われ):
- /work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/s6-ruling.md — 段 6 裁定。**A1 の処置と M7 の登録が仕様の正本。A2・A3 は直さない。**
- /work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/codex/s6-review-a-out.md — レビュー A (A1 の反例)。
- /work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/s4-ruling.md — 段 4 裁定 (plan v2 と規模上限: 変更 file は上の 2 file まで)。
- /work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/codex/s5-author-impl-prompt.md — 段 5 の実装子契約 (変える前の受理・拒否挙動、自己汚染の禁止、検査の走らせ方、報告の規則)。**全文を継承する。**

## 作ること

1. `_scan_one` の共通判定 cache (`_ScanMemo.contains_by_literal_rel` と memo なし時の局所 dict) の値に、判定した text object 自体を持たせ、再利用は cache 済み text object が現在の `text` と同一 object (`is`) のときだけにする。一致しなければ判定し直して上書きする。他の挙動・既存 helper の signature・発火回数は変えない。
2. 正例 test を 1 本: `types.MappingProxyType(backing)` と `_ScanMemo(proxy)` を作り、literal A を含まない text で式 1 を走査 → `backing` の同じ rel の値を別 str (literal を含み式 2 に一致) へ書き換え → 同じ proxy と memo で式 2 を走査し、hit すること・`_reference_scan_one` と report bytes が一致することを固定する。式 1 と式 2 は同じ共通 literal を持つ別の式 (合成 key、実軸の key と値を連続で書かない)。
3. M7 (identity 照合を外し literal と rel だけで再利用) を一時的に当てて 2 の test だけが単一理由で赤になることを確かめ、元に戻す。M1〜M6 と P0 の結果が変わらないことも確かめる (M6 の共通判定回数の番人が 2 のままであること)。

## 禁止

**既存 test の期待値を変更しない。** 反転・緩和・skip・削除をしない。既存 test が赤になったら実装側が誤りとして直す。期待値が誤りだと考えるなら、実装を変えずに報告して止める。

## 検査と報告

段 5 契約の「検査」「報告」をそのまま適用する (走らせ方は `PYTHONPATH=. python3 orchestrator/tests/test_s8b_holdout_freeze.py` か `pytest.main` 埋め込み)。報告の見出しは「## 修正」「## test」「## 変異の確認」「## 実走」「## 未実走・懸念」「## 総括」。
