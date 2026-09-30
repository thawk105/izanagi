# 段 6 裁定 9 — md_33 (wave dev-wave-cicada-certified-m、2026-09-30)

入力: focus3.md (焦点再レビュー 3 巡目 = 上限、NO-GO)。上限に達したので残る所見は親が裁定し、実測で閉じる (DW-O16)。

| ID | 裁定 | 処置 |
|---|---|---|
| D1〜D10、N1 | closed (focus3 の表。D7 は smoke-4 の再分類 `runs/reclassify-v5-smoke-4.json` で実走済み、failed=false・10 run 期待どおり) | なし |
| D11 MV-U | 処置中 (s6-ruling-8、fix8-u1) | MUT の取り直しで閉じる |
| N2 B の帰属は tx 単位 | real (一次資料の文言) | 一次資料は「B 違反の全件が、壊しで下限を実際に上げた tx に帰属した」までを書き、「全件が壊しによって起きた」とは書かない。版単位で EVENT の版 pointer と一致したのは smoke-5 で 1,925 / 6,988 件 (focus3 の照合値) であることも併記する |
| N3 同一性の命令列比較が行き先と記号を潰す | real (must-fix) | U2: TRACE=0 同一性の命令列比較を強める。各 TU の object を `objdump -dr --no-show-raw-insn` (relocation 付き) で逆アセンブルし、address・行き先・relocation の記号名を潰さずに比べる (比べないのは object の path を含む先頭の見出し行だけ)。既存の正規化比較も残し、両方を result に記録する。`equal` は両方の一致を要求する。取り直し: IDENT 1 本 |
| N4 tx 単位の B 母集団等式は実質恒真 | real (限界) | 実装は変えない。一次資料で「独立な証拠は要素単位の等式 `b_registered = b_elements_checked` と、commit 数・begin 差の等式。tx 単位の `b_end_checked_* = tx_end_reads_nonempty` は今の配置では独立でない」と書く |
