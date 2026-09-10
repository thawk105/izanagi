## 総括

静的レビューの結論は **must-fix なし**です。production の変更は [`_registered_worktree_paths`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/tools/dev_wave_land.py:3449>) の `FileNotFoundError` 分岐だけで、plan v2 と不変条件 1〜6 に一致します。

受理集合の拡大は「不在登録を保持し、隔離 dir と重ならなければ fold gate を続行する」の 1 点だけです。不在登録が隔離 dir と重なる場合は従来どおり RC=31 です。

pytest は依頼どおり実行しておらず、以下は静的検査結果です。緑とは判定していません。

## must-fix 所見

該当なし。

## nit / backlog

1. T5 は `PermissionError` と `UnicodeError` だけを直接検査しており、`NotADirectoryError`、`OSError(ELOOP)`、`RuntimeError` は未固定です。

   - 根拠 (real): [`failure_kind`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/orchestrator/tests/test_dev_wave_land.py:9152>) は 2 case のみ。前二者は `OSError` 捕捉、`RuntimeError` は `_run_fold_gate` の包括捕捉で静的には閉じています。
   - land 値: 現行はすべて成功へ進まず RC=31。将来の捕捉変更に対する回帰検知範囲だけが不足します。

2. T7 単独の観測範囲は `_registered_worktree_paths` 内での prune に限定されます。

   - 根拠 (real): [`T7`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/orchestrator/tests/test_dev_wave_land.py:9223>) は同 helper だけを呼びます。ただし `_execute_fold_gate` 側の prune は T8、land 全体の prune は T9 の registry 事後確認でも赤になります。
   - land 値: 現差分には prune がなく値は不変。T7 単独では後段 prune による RC=31→続行を見逃しますが、追加 suite 全体では見逃しません。

3. T10 は dirt 拒否だけを実機構で固定し、no-touch / ff-only / provenance / lock の代表にはなっていません。

   - 根拠 (real): dirt は [`_locked_preflight`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/tools/dev_wave_land.py:2719>) で fold gate より前に拒否されるため、[`T10`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/orchestrator/tests/test_dev_wave_land.py:9357>) は新 helper を通りません。
   - land 値: 現差分では他拒否コードを一切編集しておらず不変。T10 が直接保証する値は dirt の `(RC_DIRT, "rejected")` だけです。

## 反証した懸念

4. 禁止された実装が混入した懸念は refuted です。

   - 根拠 (refuted): production 差分は `resolve(strict=True)` の内側に `except FileNotFoundError` と `absolute()` を追加した 1 hunkだけ。`prunable` 読取り、record 分割、登録破棄、`worktree prune`、`_paths_overlap_absolute` / `_execute_fold_gate` の変更はありません。差分中の `prunable` と `split(b"\n\n")` はテストの観測用だけです。
   - land 値: 禁止変更による追加の RC=31→成功、または成功→RC=31 はありません。

5. 不変条件 1「第三の実在登録との重なり拒否」は維持されています。

   - 根拠 (refuted): 実在 path は従来どおり strict resolve され、[`_execute_fold_gate`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/tools/dev_wave_land.py:3812>) が全登録へ既存 overlap 判定を適用します。例: 登録 `/repo/third`、隔離 `/repo/third/fold-isolation` は `_FoldGateFailure`。
   - land 値: 重なり入力は従来どおり RC=31 のままです。

6. 不変条件 2「`FileNotFoundError` 以外は fail-closed」は維持されています。捕捉も広すぎません。

   - 根拠 (refuted): 内側の捕捉範囲は [`resolve(strict=True)`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/tools/dev_wave_land.py:3461>) だけです。`PermissionError`、`NotADirectoryError`、`OSError(ELOOP)` は `OSError` の派生またはインスタンスなので外側で `_FoldGateFailure`。`UnicodeError` も同じ。symlink loop 等の `RuntimeError` は局所では漏れますが、[`_run_fold_gate`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/tools/dev_wave_land.py:3956>) が `_FoldGateInfrastructureFailure` に変換し、land が RC=31 にします。`absolute()` 自体の `OSError` も外側で閉じます。
   - land 値: これらの入力が `landed` へ変わる経路はなく、RC=31 のままです。

7. 不変条件 3「worktree 行ゼロ」は維持されています。

   - 根拠 (refuted): [`if not paths`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/tools/dev_wave_land.py:3470>) は無変更。空 stdout や marker-only stdout は同じ例外になります。
   - land 値: RC=31→続行の変化はありません。

8. 不変条件 4「他の land 拒否が変わる」懸念は refuted です。

   - 根拠 (refuted): production の唯一の変更点には dirt / no-touch / ff-only / provenance / lock の分岐・定数・順序が含まれません。既存 test の期待値変更もありません。
   - land 値: 各拒否入力の従来 rc/status は 1 bit も変わりません。

9. 不変条件 5「registry を prune する」懸念は refuted です。

   - 根拠 (refuted): production に `worktree prune` は追加されておらず、T7 と T9 は admin dir と porcelain の事後状態を確認します。
   - land 値: 不在登録が消えて overlap 拒否 RC=31 が成功へ変わる経路は追加されていません。

10. 不変条件 6「不在登録を捨てる」懸念は refuted です。

   - 根拠 (refuted): `FileNotFoundError` 時にも `paths.append(path)` へ必ず到達します。T2 は `missing in registered`、T8 は同 path との overlap を直接要求します。
   - land 値: 不在 path と隔離 dir が一致すれば RC=31、非重複なら今回だけ続行可能です。

11. 既存テストが甘くされた懸念は refuted です。

   - 根拠 (refuted): test 差分は helper と T1〜T10 の追加だけで、既存期待値の反転・緩和・削除・skip/xfail はありません。現行 hash の差込みや揮発 job payload の焼込みもありません。
   - land 値: 既存拒否を緑に見せる期待値変更はなく、従来の land 判定値は保持されます。

## テストの恒真化リスク

| # | テスト | 実機構と反証結果 | 不変条件を破った場合の land 値 |
|---:|---|---|---|
| 12 | T1 | 本物の `worktree add` と porcelain。temp dir だけ差替え。第三登録を落とす実装は事前 assert、overlap 無効化は期待例外で赤。 | RC=31→続行を検知。 |
| 13 | T2 | 本物の add→`rmtree`→porcelain。不在 path 自体を返り値で assert するため `continue` 実装は確実に赤。 | 不在登録破棄による潜在的 RC=31→続行を検知。 |
| 14 | T3 | 本物の add、`.git` のみ削除、本物の prunable porcelain。marker 除外は linked path assertion で赤。 | 壊れた linkage の登録を無視した場合の潜在的 RC=31→続行を検知。 |
| 15 | T4 | 本物の改行 path と porcelain。固定された行走査が得る prefix を assert しており、marker/record 除外は赤。実際の改行込み `linked` 自体を返す期待ではない点は裁定どおり。 | marker 除外による潜在的 RC=31→続行を検知。 |
| 16 | T5 | 本物の porcelainに `resolve` / `fsdecode` の失敗だけ注入。`except OSError` への拡張、strict=False、Unicode 捕捉削除を殺せる。 | 非不在エラーの RC=31→続行を検知。 |
| 17 | T6 | 対象 stdout は monkeypatch 合成。空判定削除なら例外が出ず赤になるため恒真ではない。 | 空 registry の RC=31→続行を検知。 |
| 18 | T7 | 本物の registry と事後 porcelain/admin dir。`_registered_worktree_paths` 内の prune は確実に赤。 | registry 削除による潜在的 RC=31→続行を検知。 |
| 19 | T8 | 本物の add/porcelain。登録取得後だけ missing path を隔離 dir として再作成。破棄実装では overlap メッセージが発生せず赤になる。 | **不在登録破棄による RC=31→続行を直接検知。** |
| 20 | T9 | 本物の `land()`、`_run_fold_gate`、`_execute_fold_gate`、porcelainを通る。fold planner・node selection・fragment receipt は seam、nodeids 空なので子 pytest は走らない。旧実装なら missing の strict resolve で RC=31。 | 旧 RC=31→期待 `(0, "landed")` を固定。T9 単独は「捨てる実装」を殺さないが T2/T8 が殺す。 |
| 21 | T10 | 本物の land dirt preflight。registry の存在は本物の porcelain で事前確認するが、dirt が先に拒否するため `_registered_worktree_paths` には到達しない。 | dirt 拒否の `(RC_DIRT, "rejected")` を固定。 |