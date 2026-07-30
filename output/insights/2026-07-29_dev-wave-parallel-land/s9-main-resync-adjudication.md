# 段 9 fresh-context main 再同期監査の親裁定

## 固定入力

- wave tip: `c63a0058e5e5b1d4b30bd9ef0ab74af5b2905938`
- local main: `7be05ef7e3487dd62b553c672627845a444e1ff9`
- merge base: `09129750c64a294b65db8d1b853d7214520a1b53`
- main 側監査列:
  `72f8858` → `98670a7` → `c75982c` → `6b64d21` → `7be05ef`
- 独立監査:
  `s9-main-resync-audit.md`（read-only Codex、validator green、結論 `NO-GO`）

## 親の再現と裁定

1. **`6b64d21` の provenance 欠落 = real / 段 9 blocker。**
   local main で `python3 tools/check_ai_provenance.py` を実走し、
   `533 件中 1 違反`、rc=1 を再現した。違反は同 merge commit の
   `AI-Agent` trailer 欠落である。子孫 commit で既存 message は修復できず、
   rebase / force / checker 弱体化 / 例外追加は `DW-STOP`、`DW-O23`、
   `docs/ai-provenance.md` の境界に反する。固定 SHA `7be05ef` は merge しない。
2. **T-179 token 不変条件の欠落 = real / main 所有側の受入前 blocker。**
   `tools/codex_worker_ledger.py` の `_validated_usage()` は
   `cached_input_tokens <= input_tokens` と負の `reasoning_output_tokens` を検査せず、
   `_billable()` は負値を生成できる。既存 negative test は required 4 field の単独負値だけである。
3. **非 null 非 object `token_count.payload.info` の黙殺 = real / main 所有側の受入前 blocker。**
   `_stream_rollout()` は `info` が dict でなければ無条件に読み飛ばすため、
   legacy の `null` だけでなく list / string / bool も issue 無しで過少集計する。
4. **model / reasoning identity 欠落 = real、ただし T-181 / T-182 前の consumer gate。**
   T-186 の local-main land 自体の実装を変える所見ではないが、T-179 完了を下流の比較根拠に
   使う前に main 所有側で裁定と negative test が必要である。
5. **F / worklog ID 衝突 = real、merge 後に解消可能。**
   main の T-179 を `F54` / worklog `(64)` として保持し、T-186 を `F55` / `(65)` へ振り直す。
   凍結済み prompt / review / brief は当時の番号を保持し、live docs と erratum だけを追随させる。
   両 worklog entry の単純併合は 100,000-byte 上限を超えるため、再同期時に正本の rotation 契約も
   適用する。この解消は上記 blocker が閉じた新 main SHA の監査後に行う。
6. **T-186 実装・mutation の回帰所見 = refuted。**
   main の net diff は T-186 の helper、checker、共通 dev-wave reference、
   M1〜M13 の anchor を変更していない。今回の停止は T-186 実装赤ではなく、
   `DW-O23` が要求する新 upstream の監査で正しく検出した外部 blocker である。

## 段 8 と終端

本 wave の自己改善候補は T-186 本体として `43c4ec4`〜`c63a005` に実装済みである。
今回の再開で新しい dev-wave 手順欠落は実測していない。むしろ新設した fresh-context
audit / fixed-SHA / provenance / stale-main 境界が危険な upstream を land 前に停止した。
追加の command / reference / failures / decisions 編集は行わない。

段 9 は `DW-STOP` に従い `NO-GO` で閉じる。main 所有側が provenance と ledger blocker を
裁定・是正し、新しい main SHA ができた後の fresh context で、既存 branch
`codex/dev-wave-skill` を再利用して再監査 → 固定 SHA merge → ID / worklog 解消 →
全受入 → `DW-O23` の順に再開する。
