NO-GO

## 固定 SHA と commit 列

提示値は実体と一致しました。

```text
wave: 43c4ec4 → 16e418b → 08adb89(+0912975) → c63a005 → 59c9484

main:
7be05ef
├─ 24d2672 → de0a9ad → 677c32a → 6447a0c → 7cda754
└─ 6d7141d → c9c3de5
                    ↘
               226f7fd → ff82133
```

- `HEAD == codex/dev-wave-skill == 59c9484`
- `main == origin/main == ff82133`
- merge-base は `0912975`
- `7be05ef` は `ff82133` の ancestor
- 制約どおり checker・pytest・一時ファイル生成は実行していません。

## Findings — blocker

1. `reasoning_output_tokens < 0` は未修正です。

   `ff82133:tools/codex_worker_ledger.py:205` は型だけを検査し、負値をそのまま保存します。負値テストも `ff82133:orchestrator/tests/test_codex_worker_ledger.py:469` の必須4 fieldだけで、任意 field の reasoning は対象外です。

   記録も閉鎖を主張しておらず、凍結 T-179 README は欠落・負値等を「受理する」としています（`ff82133:output/insights/2026-07-29_t179-worker-ledger-verbatim/README.md:77`）。実装・negative test・記録の三者とも未閉鎖です。

2. 非 null・非 object の `token_count.payload.info` は依然黙殺されます。

   `ff82133:tools/codex_worker_ledger.py:475` は `info` が dict でなければ無条件に `continue` します。したがって list/string/bool は issue なしで model call/token を過少集計します。

   テストは `info:null` の legacy 正例（`ff82133:orchestrator/tests/test_codex_worker_ledger.py:454`）と object 内の usage 異常だけで、非 null 非 object の負例がありません。T-180 launcher 自体は同ケースを拒否しますが、T-179 ledger は未修正です。

## Findings — must-fix

1. `docs/dev-wave/operations.md` は lossless な単純併合ができません。

   3-way merge は次の5文書で textual conflict を返します。

   - `docs/decisions.md`
   - `docs/dev-wave/operations.md`
   - `docs/failures.md`
   - `docs/phase3.md`
   - `docs/worklog.md`

   特に operations では、main の hardened `DW-O17`（`ff82133:docs/dev-wave/operations.md:89`）と wave の `DW-O23`（`59c9484:docs/dev-wave/operations.md:119`）を両方保存する必要があります。

   しかし意味どおりの union は `docs/dev-wave/** = 24,037 bytes` となり、24,000-byte hard ceiling（`59c9484:tools/check_docs.py:170`）を37 bytes超えます。少なくとも37 bytesの意味保存縮約が必要です。片側採用は、O17の安全な commit手順またはO23 land契約を失うため不可です。

2. ID衝突は前回より拡大しています。

| 種別 | wave側 | `ff82133` main側 | 現SHA基準の候補 |
|---|---|---|---|
| T | T-186 = parallel land | T-186 = envelope残余、T-187 = provenance | T-188 |
| D | D100 = parallel land | D100 = envelope、D101 = provenance | D102 |
| F | F54 = parallel land | F54 = T-179誤帰属 | F55 |
| worklog | (64) = parallel land | (64)=T-179、(65)=T-180、(66)=T-187 | (67) |

   根拠は `59c9484:docs/phase3.md:558` と `ff82133:docs/phase3.md:572`、`ff82133:docs/decisions.md:4422`、`ff82133:docs/failures.md:1010`、`ff82133:docs/worklog.md:715` です。

   ただし main側の blocker 修正が先に land すれば候補番号も消費され得ます。D70上、並行branchは番号を予約しないため、実際の corrected-main tip で再走査が必要です。

3. 現在の wave checkout は land helper に対して dirty です。

   未追跡の `s9-main-resync2-audit.log` と prompt が残っています。helper は wave側の status が1件でもあれば拒否します（[tools/dev_wave_land.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/dev_wave_land.py:792)）。既存所有物なので、本監査では触れていません。

## Findings — advisory

- model/reasoning identity は `partial` です。T-180 launcher は CLI指定値と `turn_context` を照合します（`ff82133:tools/codex_worker_launch.py:772`）が、ledger は欠落を空文字、null/object等を `str(...)` へ変換して受理します（`ff82133:tools/codex_worker_ledger.py:440`）。T-181/T-182を進める前の consumer gateとして残ります。
- `98670a7` のClaude-only trailerにCodex逐語を含むという前回の completeness 所見は未変更です。ただし通常 trailer自体は存在し、今回採用された incident限定 correction の対象ではないため、hard blockerではなく規約解釈の advisory とします。
- 記録の `full-history provenance 541件` は親 `226f7fd` 時点の件数です。記録commit `ff82133` を含む静的選択数は542件なので、最終merge後は必ず新HEADでfull-history監査が必要です。

## 前回 blocker の状態

| 前回所見 | 状態 | 判定 |
|---|---|---|
| `6b64d21` trailer欠落 | closed | targetは履歴中に残り、`6d7141d`がstrict descendant。correction候補はexact 1件 |
| `cached > input` | closed | 実装拒否、負例、M13、worklog記録あり |
| 負の reasoning token | partial | 型検査のみで負値を受理。対応負例なし |
| 非 null 非 object `info` | partial | ledgerの早期`continue`が残存。対応負例なし |
| model/reasoning identity | partial | launcher経路のみ閉鎖、ledger経路は未閉鎖 |
| F/worklog衝突 | regressed | T/D/worklogの占有が増え、候補は T-188/D102/F55/(67) へ進んだ |
| worklog容量 | closed | mainが(49)〜(58)をarchive済み。main現行worklogを基準にwave entryだけ追加すべき |

`6b64d21` correction は一般免除ではありません。checkerは固定target/payload（`ff82133:tools/check_ai_provenance.py:72`）、raw/canonical/final-block exact（同:237）、selected-set・strict lineage・実欠落・correction自身green（同:622）を連言し、対象のmissing findingだけを除外します。

また、local-onlyで不正だった `cb79147` は最終mainのancestorではなく、Codex authorが実際に1行寄与した `677c32a`へ再構成されています。一方 `6b64d21` 自体はmain/originのancestorとして保持され、旧系列もlocal refから参照可能です。履歴隠蔽ではありません。

## merge時の保存事項

- mainの `DW-O17`、短縮済み `DW-O20`、waveの `DW-O23`をすべて保存する。
- waveの `tools/dev_wave_land.py`、dispatcher、`DW-S09`、Skill、`tools/check_docs.py`、関連テスト・M1〜M13 anchorを維持する。mainとの実装path overlapはありません。
- mainの provenance checker・規約・T-179/T-180実装とテストを維持する。
- mainのworklog `(64)〜(66)` と archive `(49)〜(58)`を権威とし、wave `(64)`だけを再構成して追加する。wave側worklog全体を採用しない。
- living docsは現SHA基準で `T-188 / D102 / F55 / (67)`へ追随させる。凍結prompt・review・旧audit・既存commit件名は旧番号のまま保持し、erratumで対応関係を示す。
- operationsを最低37 bytes、意味を変えずに縮約する。安全義務やchecker予算を削って合わせない。
- main側で reasoning/info blockerを修正し、negative tests・新mutation・erratum記録を追加した新SHAを作る。その新SHAをfresh contextで再監査してから固定SHA mergeと全受入へ進む。
- merge commitは自動messageを使わず、`--no-ff --no-commit`、message-file preflight、`commit -F`、commit後full-history監査の順を守る。

## 総括

`6b64d21` の一回限り provenance correction と `cached > input` は閉じています。しかし、負の reasoning tokenと非 null 非 object `info` はT-179 ledgerに残存し、negative tests・記録も揃っていません。さらにlosslessなoperations統合は37 bytesの予算超過を起こします。

したがって `ff82133` はwaveへmergeせず、main側修正後の新SHAをfresh contextで再監査すべきです。