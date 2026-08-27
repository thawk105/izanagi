---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-28
wave: worktree-dev-wave-t1434-oracle-realdata
seq: 1
title: [T-1434] catalog-backed oracle wiring sliceでtask-specific束縛を実発火させた (code + docs、branch worktree-dev-wave-t1434-oracle-realdata、mutation baseline PASSED・6/6 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- 依頼は、組込みmanifestのPOS/NEG finding集合が同一で一度も発火していなかったtask-specific oracle束縛を、
  既存task catalogと§8契約を使う最小実データ経路で発火させ、accept/reject例を示すこと。D674が見送った
  電力・外部custodian・署名、D767がunboundに固定したtask acceptance、served-model attest、汎用platformは
  scope外に固定した。決定は{{D:t189-oracle-wiring-slice}}。
- 起動時にT-1817、T-2008等の稼働worktree/processと編集面を照合した。T-1817はheadline sizing 3 file、
  T-2008はartifact/report/plot面で、今回の`codex_reasoning_ab.py`、専用verifier/test、T-189 docs/outputとの
  重複は0件だった。wave中にmainは41 commit進んだが、merge-baseからの再照合でも今回path重複は0件。
- task catalogの`T-1222-population-closure:plan:0`と
  `dev-wave-t1393-finish-trial-indeterminate:plan:0`をexact joinし、互いに素なfinding IDを1件ずつ持つ
  `task-oracle-wiring-slice-v1.json`を作った。sliceはexplicit profile、canonical/raw SHA、verifier tool SHA、
  closed schema、許可6 verb、evidence joinをpinする。blind時は2 IDのunionを許し、reveal後はtask自身の1 IDへ
  狭める。T-1393 packetへT-1222 IDを置くcross-task例はfull `verify`/`aggregate`でfail-closedになった。
- 段3は意味/整合レンズで7件/11件を提示し、完全§8 ledgerへの誤昇格、optional verifier迂回、T-181 provenance
  流用、LF/digest逆転を実装前に棄却した。段6 reviewはdowngrade、failure normalization、tool pin、path TOCTOU、
  strict JSON等を検出し、3 fix巡で閉じた。fix2後の6赤はprofile責務の内部伝播とDecimal reasonの実装欠陥で、
  9 node再走で9 passed。fix3はfinal-path swap testのctime/path診断raceを、拒否順序の決定化で閉じた。
- 焦点走は関連4 fileで698 passed / 2 existing growth-hold skips。fix3後のslice/OR関連は40 passed、
  node名付き9 caseも9 passed。portable/physical verifierは2 task verifiedで、physical modeはjobs rootの
  prompt/receipt bytesも照合した。関連検査と`check_codex_agents`/`check_docs`は緑。
- mutationはprobeで失敗node完全集合を採取後、fix3 commit `644695f7b`とspec SHA
  `058b1ca7...f7b8f`へ再束縛して本走した。baseline PASSED、OR-M1〜M6が6/6 KILLED・完全一致、
  SURVIVED/MISMATCH/PARSE_ERROR/TIMEOUT 0。OR-M1はdiagnostic sensitivity、OR-M2〜M6の5件を
  correctness/integrity killとして数える。artifactは
  `output/insights/2026-08-28_t1434-oracle-wiring/`。
- mutationの最初の全file baselineはnested submodule未初期化の既存fixtureでPARSE_ERRORとなり、変異0件で停止。
  isolated cloneとmutation関連node限定へ切り替えた。probeはSURVIVED期待なので6 MISMATCHが正しい観測で、
  final matrixへ数えていない。旧scratchは削除せずretained directoryへ移し、Git worktree登録だけpruneした。
- Codex subprocessは11本 (plan 1、consult 2、author 1、review 2、fix 3、focus 2)、全て
  `gpt-5.6-sol@xhigh`、completed。model call 334、CLI reported 1,989,671、worker wall合計7,168秒。
  実装面はD95のCodex author、親はartifact/docs/統合・test/mutation/受入を担当した。

## 次の一手差分

### 更新

- [T-1434] **P1・[T-189] 事前登録文書の実装・実走**: task manifest CLI、費用の部分正規化、
  adjudicationのtask別束縛に加え、catalog実在2行の限定wiring sliceでaccept/cross-task rejectを発火させた。
  組込みPOS/NEGは同一集合のまま変更していない。sliceは`section8_complete=false`、content review
  `not-established`、task acceptance `unbound`、routing evidence `inconclusive`を固定する。
  残るscope外論点は、§8独立ledger本体の作成・凍結・独立content review、§8 coverage集計、task固有acceptance、
  cache書込数量、費用certified化、schema世代/移行契約、served-model attest、model既定化2経路、sol/luna各1回を
  固定しないblock検査、v3 cardinality自己導出、schema v2/欠落schedule互換、standalone verify-snapshot未接続。
  base: ac027f9981b4ea011fc87e758a398437d66416f698abd8dbb6b8e54f83e16f3c
