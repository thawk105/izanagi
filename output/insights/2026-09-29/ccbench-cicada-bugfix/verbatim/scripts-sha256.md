# job dir の script と patch の sha256 (投入時点、`$J` = /work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929)

Codex author の job body と使い捨て patch (`$J/scripts/`、最終版 = scripts-v4):

```
c107ed3e307d938e4c37729f6c0b2268dc9de45f1918f9481d4f2df7217a0441  build_genomes.py
61e2df369c29af0c3559bda445a998665653ad6d16857cdbad471acd7cf53d29  check_format_ci.sh
15c800021bb79af95c1e8176171d942bf57de5d5cb4411f466d9b1a28a36ccd5  check_patch_apply.sh
feaab9b6a98baf4be13cdb93e4cc7478ae5eeaf41aa3830a247dd5bfd8c1b3a3  instr-cicada-trace-promotion-diag.patch
d4ce662ebe5dd35af50df060f81d1c730284e9eccddffb15d6432593e0b1a70b  launch_cicada_run_g.py
4f4d6ba529ddb1a9c61b577815a2b449981877a264178bd9abe1e1d6cdfb66d1  patch-apply-F.json
2d1ad49ba07d50201abdda05231346524c5c615e779ba8cfaf6d8d7b5068cfd7  restore-promotion-dup-emplace.patch
c51a304c9348842dc57ad82a70ed041c7c34a7cd76e47550f06f0abf1f27eb98  run_ci_build.sh
ae057282b49a48e4eccb3d0b7e9be2b42d3b4e1fca95e92b706f3856af512bbd  run_judge.sh
```

版の履歴: scripts-v1 (実装子 B) → v2 (fix B2) → v3 (fix B3、run_judge.sh) → v4 (fix B4、DIAG と戻し patch)。build-1・ci-1・trace-1・judge-1 は v2、judge-2 は v3、diag-1 は v4 で走った (各 job log の冒頭に sha256 を記録)。

親の投入・commit script:

```
92ce76493dfbe19cad5412ec05158ce4e681509719f5b31efeeb50d029995068  run-job.sh
f06e4b6987714258bcf9d8f84058428ea7c433317b86ea92629f49d779970140  mk-G.sh
dc1f369f53674b2c9231f1f9b8ede54a59acb29643d42e8c6ea84afbf5b51b21  detach.sh
9880ffe45986cf7b88a5d26a27b545f9acd01d2716cfa805ff9ed281e36d6cac  login-checks-G.sh
6ace830a3b87fc7c40512823610901defcbd1e81dd4fdc26fa72e0fbf28e15af  fetch-G-to-childb.sh
59f989177320eb26be2cdc5fd9d0affa5e269f11e77b66912dc8dac1db627cb3  probe_syntax.py
```
