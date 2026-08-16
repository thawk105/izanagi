---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-16
wave: dev-wave-floor-reseal-authority
seq: 1
title: 床値 protocol の再封印を AI へ開放した — issuer と組 index は dormant で land し、実発行は g2 chain へ渡す (コード + テスト + docs、branch worktree-dev-wave-floor-reseal-authority、変異 matrix = KILLED 11 / MISMATCH 1 / SURVIVED 0)
---

## 本文

- **2026-08-16 のユーザー裁定 (案 1 + 案 3) を実装した。** 案 1 = 床値 protocol のうち AI が
  更新してよいのは `contract_sha256` と `ccbench_pin` の 2 つだけ。案 3 = 床値は
  (環境契約 hash, ccbench pin) の組ごとに 1 件で、同じ組への 2 件目を機械的に拒否する。
  案 2 (測り直しの事前登録) は不採用。設計判断は {{D:ai-floor-reseal-authority}}。
  一次資料 = `output/insights/2026-08-16_floor-reseal-authority/`。
- **成果は dormant である。** 実 repo へ protocol artifact は 1 件も追加せず、
  固定 path を読む consumer 6 件 (Python 5 + shell 1) の resolution も切り替えていない。
  既裁定 Q3 (両成分がともに交代) を守るため、実発行は環境世代 g2 の活性化と同一 chain で行う。
  **「案 1 + 案 3 実装完了」「正しさ防壁が閉じた」とは記録しない。**
- **親 brief の中心的な主張を、親自身が実測で訂正した。** 初稿は「再封印できないと新しい組で
  何も走らない」と書いていたが、封印済み protocol は今日も live admission を通る
  (`validate_protocol` は `ccbench_pin` を HEAD と cross-check しない)。止まっているのは
  凍結チェーン側の 2 検査で、それは 2026-08-12 の裁定で保留中である。正しい記述は
  **「記録された測定条件が実体と食い違ったままで、新しい組で真正な物差しを封印できない」**。
- **裁定の「2 field だけ動かす」は、今日の実 repo では literally 1 field の差だった。**
  承認定数から組み立て直した protocol と封印済みの差は `ccbench_pin` のみで、他 17 key は完全一致。
- **敵対検証は 5 本すべてが NO-GO を返し、最後の 1 本で GO になった。**
  段 3 の 2 本、段 6 の 2 本、段 6 焦点再レビュー第 1 回がいずれも NO-GO。fix を 2 巡回した。
  親が独立に実測で裏取りした重い所見は 3 件で、いずれも設計を変えた。
  (i) 新しい置き場所を作るだけで launch certificate の未知 file 拒否が発火し既存 campaign が止まる、
  (ii) publish 直前の env contract 再照合は authority snapshot の PID cache により**恒真**、
  (iii) working tree の anchor を lineage authority にすると、`validate_protocol` を通る
  改変 seed / 閾値が全 successor へ継承される。
- **`--no-replace-objects` が要る、という所見をレビューが出した。** 引数ゼロ API にしても、
  ambient な `GIT_DIR` や replacement ref を置くだけで lineage anchor と pin を別 repository から
  読ませられる。issuer の全 Git read を衛生化環境と単一 commit OID へ束縛して閉じた。
  共有 helper `source_digest._sanitized_git_env` に残る同型の面は、独立 2 例が揃うまで
  族一般化しない (DW-G03) ため別タスクへ送った。
- **既存期待値の変更を 2 件だけ親が裁定して許した。** どちらも「揮発する期待値」である。
  (a) 実 repo index の `len(index) == 1` は、裁定どおり後続 wave が最初の versioned protocol を
  追加した時点で**偽の赤**になる。(b) 固定 commit 化により恒真になった gitlink 再読の
  呼出し回数 pin。それ以外の期待値は 1 件も緩めていない。
- **変異 matrix は 2 走した。** probe 走で失敗 node の完全集合を再導出し、本走で
  KILLED 11 / MISMATCH 1 / SURVIVED 0 / TIMEOUT 0 を得た (baseline PASSED)。
  唯一の MISMATCH は実体でなく node ID の表記差で、F24 系ではなく {{F:mutation-node-space-selfconsistency}}
  として起票した — harness が報告する node と collection 実在検査が要求する node の空間が
  内部で食い違い、**どちらの形で登録しても一致しない**。
  前回レビューが mask を指摘した 4 件は 2 層同時変異へ再照準して KILLED を得た。
- **codex 子は sandbox の制約で計算ノードへ dispatch できない。** 段 5 と fix 2 巡のすべてで
  pytest が rc=16 (`qstat -Q` preflight rc=1) となり、テストの実走は毎回親が行った。
  焦点走は 4 回、いずれも `--force-dispatch` 経由。bounded local は本 login node で
  cgroup attest 失敗により rc=16 になる。
- **計算資源:** PBS job = 焦点走 4 本 (913217 / 913218 / 913228 / 913276) + 変異 2 走 (probe / 本走)。
  codex 子 9 本 (plan 1 / consult 2 / author 1 / review 2 / fix 2 / focus 2)。

## 次の一手差分

### 新規

- {{T:floor-protocol-consumer-wiring}} **P1・新規**: 固定 path を読む consumer 6 件
  (`certified_writer_admission.py` / `s8b_holdout_admission.py` / `s8b_holdout_freeze.py` /
  `s8b_ratified_freeze.py` / `s8b_prediction_runner.py` / `tools/pegasus/floor_campaign.sh`) を
  組 index 経由の resolution へ切り替え、環境世代 g2 の活性化と同一 chain で最初の
  versioned protocol を実発行する。式 3 (盲検封印) の再封印を伴うため単独では進めない。
- {{T:shared-git-env-scrub-gap}} **P2・新規**: `source_digest._sanitized_git_env` は
  `GIT_REPLACE_REF_BASE` / `GIT_CONFIG*` / `GIT_NAMESPACE` / `GIT_GRAFT_FILE` /
  `GIT_SHALLOW_FILE` を除去せず `GIT_NO_REPLACE_OBJECTS` も設定しない。
  同型の穴を持つ第 2 の consumer を実測してから族一般化を裁定する (DW-G03)。
- {{T:ratified-pointer-namespace-binding}} **P2・新規**: ratified freeze の `floor_protocol`
  pointer が任意 canonical path を受理するため、組の一意性は sanctioned namespace 内に限る。
  pointer 側を namespace へ束縛するかを裁定して実装する。
- {{T:mutation-node-space-selfconsistency}} **P2・新規**: 変異 harness の報告 node と
  collection 実在検査の空間差を機構側で正規化する。詳細は {{F:mutation-node-space-selfconsistency}}。
- {{T:floor-reseal-residual-rulings}} **P1・ユーザー裁定待ち**: 案 3 の射程 (pin を進めれば
  新しい組で測り直せる)、親が Q3 の機械化として入れた「環境契約 1 世代につき床値 1 件」の妥当性、
  ratified pointer の束縛、versioned artifact を `FROZEN_MANIFEST` へ載せるか、
  run 層の測り直し ([T-1140] 問 1) との関係。裁定パッケージは
  `output/insights/2026-08-16_floor-reseal-authority/README.md` の「残る限界」節。
