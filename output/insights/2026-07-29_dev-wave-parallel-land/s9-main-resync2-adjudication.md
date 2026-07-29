# 段9 latest-main 再同期監査の親裁定

## 固定入力

- wave tip: `59c9484621b312366f9d5bdba69cf7f0eb5342f7`
- local main: `ff82133365cb8ba3015d82adeeaa741ed68995e5`
- merge base: `09129750c64a294b65db8d1b853d7214520a1b53`
- 独立監査: `s9-main-resync2-audit.md`
  (read-only Codex、exit 0、validator green、結論 `NO-GO`)

## 親の裁定

1. **`6b64d21` provenance 欠落 = closed。**
   main は incident 固有の forward correction と再構成統合を含み、固定 target・payload・lineage・
   selected set・correction 自身の通常監査を連言する。一般免除、履歴隠蔽、checker 弱体化ではない。
2. **`cached_input_tokens > input_tokens` = closed。**
   main の ledger は専用 issue で拒否し、negative test と記録も持つ。
3. **負の `reasoning_output_tokens` = real / 未解消。**
   `_validated_usage()` は型を検査するが、任意 field の負値を拒否せず result へ格納する。
   対応する negative test はなく、T-179 の凍結記録は将来形として負値受理を明記したままである。
4. **非 null 非 object の `token_count.payload.info` 黙殺 = real / 未解消。**
   ledger は `dict` 以外を一律 `continue` し、legacy `null` と list/string/bool を区別しない。
   T-180 launcher の拒否は T-179 ledger の受理集合を閉じない。
5. **model / reasoning identity = real / T-181・T-182 前の consumer gate。**
   今回の land helper 自体の blocker には追加しない。前回裁定どおり下流比較前に扱う。
6. **main との docs 衝突と採番 = merge 後に解消可能だが、現時点では merge しない。**
   生きた記録は `T-188 / D102 / F55 / worklog (67)` が現 SHA 基準の候補。
   `DW-O17` と `DW-O23` をともに保存すると reference aggregate が現 ceiling を 37 bytes超えるため、
   安全義務と予算を変えない意味保存縮約が必要である。これは ledger blocker が閉じた main の
   再監査後、固定 SHA merge の競合解消として行う。

## 終端

強制終了前の親裁定と handoff は、provenance と ledger blocker をともに閉じた新 main SHA を
再開条件としていた。今回のユーザー報告どおり provenance は閉じたが、ledger 2件は残る。
承認済み再開条件を緩めず、別タスクの実装を本 wave へ持ち込まない。

段9は `DW-STOP` に従い `NO-GO`。`ff82133` を wave へ merge せず、local main も変更しない。
main 所有側で ledger 2件を実装・negative test・記録まで閉じた新 SHA の後、fresh context で
既存 branch を再利用し、再監査 → 固定 SHA merge → 採番 / byte予算解消 → 全受入 → `DW-O23`
の順に再開する。
