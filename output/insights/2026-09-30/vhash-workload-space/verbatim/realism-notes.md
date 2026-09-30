# 現実性の節の材料 (2026-09-30 親が原典で確認した逐語)

- YCSB 本体 `core/src/main/java/site/ycsb/generator/ZipfianGenerator.java` (GitHub brianfrankcooper/YCSB master、2026-09-30 取得): `public static final double ZIPFIAN_CONSTANT = 0.99;`
- YCSB `workloads/workloada`: `readproportion=0.5`、`updateproportion=0.5`、`requestdistribution=zipfian`
- YCSB `workloads/workloadb`: `readproportion=0.95`、`updateproportion=0.05`、`requestdistribution=zipfian`
- CCBench 論文 (Tanabe ら PVLDB 13(13)) Table 2 (`/work/1/SFC/tanab/tmp/vhash-related-work-2026-09-29/src/ccbench-nolayout.txt` 536〜549 行): "(ζ) Skew (from 0.6 to 0.99)."、"() Payload size (from 4 to 1000 bytes)"、"(δ) Transaction size (from 10 to 100 operations)"、"(α) Cardinality (from 10^3 to 10^9 records)"
- Cicada 論文 (Lim ら SIGMOD 2017) (`cicada-nolayout.txt` 1586〜1589 行): "contended YCSB using 16 requests per transaction, 50% read/50% RMW, and Zipf skew of 0.99."、Figure 7 "Read-intensive YCSB. 1 request per transaction, skew of 0.99." (1670 行)
- 長い read-only の用途: `output/insights/2026-09-29/vhash-motivation-evidence/README.md` §1 表 (Steam CH-benCHmark OLAP 1 + OLTP 1、SAP HANA の 1 時間超の cursor 6 件、LeanStore の snapshot を開いて sleep する tx、MySQL の mysqldump --single-transaction)
