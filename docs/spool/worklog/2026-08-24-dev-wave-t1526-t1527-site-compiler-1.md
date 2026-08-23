---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-24
wave: dev-wave-t1526-t1527-site-compiler
seq: 1
title: [T-1526][T-1527] source-digest 受入を available compiler で実走化し fake mocc source を補完した
---

## 本文

- ユーザー裁定どおり、受入testだけを `_any_cxx()` 系へ寄せ、production qualificationのexact
  gcc-13/g++-13契約は変えなかった。通常checkoutのT-1526 campaign 8 nodeは即実走6 +
  conditional-first 2、T-1527 directは別の9件目である。実装前9 skipから実装後7 pass / 2
  conditional skipへ変わった。compiler版横断保証は作っていない。
- 起動時は指定どおり全registered worktree/local branch/handoffをfile-level照合した。照合中に
  T-1520がlandしたが対象pathと非重複。T-1593だけがREADMEへ1行追加を所有していたためauthorから
  READMEを外し、T-1593 land後のmain取込で同1行を保持して親がcompiler節を同期した。
- Codex工数はplan 1、consult 2、author 1、review 2、fix 1、focus 1。reviewのreal所見から
  compiler単独cache軸、missing-define偽緑、conditional順序、qualified/scope-aware consumerを閉じた。
  逐語・裁定・変異詳細は`output/insights/2026-08-24_t1526-t1527-site-compiler/`。
- 焦点走は14 passed / 2 conditional skipped。file単独はcampaign 377 passed / 3 skipped、direct
  97 passed、skip-classification 6 passed。段6受入はtested main `c6c98f4b`、tested tip
  `dfeb9684`、child-green、14941 passed / 60 skipped、red 0、flake 0。
- 変異は最終baseline PASSED、8/8 KILLED、SURVIVED 0、MISMATCH 0。初走M4はreal-repoの
  `@real-repo` suffixで期待側だけMISMATCH、suffix付き期待はcollectionに存在せず起動前停止する
  既知F95だったため、meta nodeへ再照準した。初走もerratum ledgerとして残した。
- scope外として、legacy cacheがplain `g++`のresolved executable/versionを束縛しない所見、
  production site compilerとの要求名同一性、他testのg++-13整理、shared resolver、cross-version
  portability一般化は実装しなかった。`prepare_toolchain`のfail-closedと規律2は緩めていない。

## 次の一手差分

### 完了

- [T-1526] campaignのcompiler依存8 nodeをavailable compilerへ配線し、cache identityと受理/拒否集合を正負例で確認した。
  remaining: none
  base: 3f22b9d11f8b9a5942f8cfdfb3fee5428b156c5de9038c72d3a8153809e6543c
- [T-1527] direct fake repoへmocc owner CMakeと`cc/mocc/transaction.cc`を供給し実走化した。
  remaining: none
  base: c2123646ee6ff5afa612e6d4e77af49fbcdeda1bf91b2531563d5101b0153c01
