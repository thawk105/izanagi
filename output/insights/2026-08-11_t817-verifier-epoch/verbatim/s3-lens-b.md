静的読解のみ。実装・プラン修正・pytest実走はしていない。指定された brief と plan は全文読了済み。

判定は現時点で **NO-GO**。最大の問題は、`verifier_selection` を replay/guided 系だけに挿入しても、同じ WAL・campaign identity を読む report、critic、freeze 検証、S8b 系が別経路で certified 選択を続けること。

## 1. consumer 取り残し：選択 gate の適用範囲が狭い

### (a) 何が壊れるか

プランの gate は replay、guided、search_baselines を主対象としているが、同じ `certified`、commit fitness、verify_done を読む既存 consumer が複数残る。したがって、P2-5 の replay は停止しても、report/critic/freeze が旧意味論で winner や certified 集合を作れる。

### (b) 根拠

- `orchestrator/campaign/p2_2_report.py:67-120` は WAL を直接読み、commit と median fitness で順位付けする。`verifier_selection` を通らない。
- `orchestrator/critic/digest.py:216-243` は committed variant の指標を直接収集する。
- `orchestrator/campaign/s1_report.py:257-329` は `verify_configs` と fitness を含む WAL segment を certified sample として扱うが、新しい selection assessment を見ない。
- `orchestrator/campaign/s1_known_axes_freeze.py:266-295` は commit の数値 fitness を直接集計し、`:337-369` で P2-2 の argmax を選ぶ。
- `orchestrator/campaign/layer3_report.py:476-530` は WAL の bench/verifications/aborts を直接 report 化する。
- `orchestrator/campaign/s8b_oracle_report.py:912-930` は verify_done の `certified` のみを検査する。
- `orchestrator/campaign/s8b_oracle_judge.py:124-269` は manifest と observations を判定し、verifier epoch を見ない。

### (c) 具体的な入力・状態

P2-2 の既存 WAL は、例えば `output/campaigns/p2-2-silo-balanced-enumerate-f1588056/runs/wal.jsonl:3` に `certified: true` を持つ verify_done がある一方、witness、receipt、workload binding がない。これを `p2_2_report`、critic、S1 report が直接読むと、selection gate が除外したはずの variant が別の certified/winner 集合に残る。

### (d) scope 内 / 外

replay/guided/search_baselines は scope 内。しかし `p2_2_report`、critic、S1 report、layer3 report、S8b report/judge、freeze 系は plan の scope 外または未接続。

### 成果物影響

P2-5 replay の停止とは別に、report の winner、critic の fastest variant、S1 freeze の selected variant、S8b observation/judge の certified 集合が旧値のまま残る。

---

## 2. `None = 歴史保存` は `screening_search_config` にしか成立していない

### (a) 何が壊れるか

plan は `verifier_epoch=None` を「key を追加しない歴史保存」として扱うが、既存 identity の全体では同じ意味論にならない。`screening_search_config(None)` は任意の screening key だけを省略する API であり、campaign identity 全体を旧 pre-image に保つ API ではない。

### (b) 根拠

- `orchestrator/campaign/ident.py:101-109` は `screening_search_config(None)` の場合だけ `{}` を返す。
- `orchestrator/campaign/ident.py:39-52` の `bind_admission_policy` は常に `search_config["build_admission"]` を追加する。
- `orchestrator/campaign/ident.py:151-178` の `canonical_preimage` は `build_admission` を必須とし、全 `search_config` を canonical pre-image に含める。
- `orchestrator/campaign/ident.py:432-497` は既存 lock を current build admission と照合する。
- 既存 P2-2 lock `output/campaigns/p2-2-silo-balanced-enumerate-f1588056/campaign.lock:1` には `build_admission` も epoch もない。
- `orchestrator/campaign/p2_2.py:121-146` はこの旧形状の raw config を `run_campaign` に渡す。
- `orchestrator/campaign/replay.py:93-111` は `<slug>-<search_tag>-*` prefix discovery で campaign directory を探す。

### (c) 具体的な入力・状態

既存 P2-2 directory を再開しつつ、writer 側の default epoch と `build_admission` が付いた config を使うと、次のいずれかになる。

1. 新しい campaign ID が生成され、旧 directory と新 directory が同じ prefix に並ぶ。
2. 旧 lock の `build_admission` 欠落で admission pre-image 検証に失敗する。
3. `discover_campaign_dir` が複数候補を見つけ、再開対象を一意に決められない。

従って、`None` で epoch key を省略しても、既存 identity 全体の pre-image が保存されるとは限らない。

### (d) scope 内 / 外

epoch の canonicalization と lock codec は scope 内。しかし、既存 P2-2、S1、autonomous trial、旧 campaign の再開 writer 全体を `None` 経路へ接続することは plan で未確定。

### 成果物影響

既存 campaign の再開先・directory discovery・campaign ID が変わり、S1 report や P2-5 の参照対象が空集合または別 directory になる。

---

## 3. restart/recovery が epoch-less WAL や lock を再び生成し得る

### (a) 何が壊れるか

selection assessor だけを read-only にしても、通常の再開経路は WAL 修復・interrupted attempt recovery を行う。ここで epoch を認識しない abort/recovery record が追加されるため、歴史保存と現在 policy の境界が崩れる。

### (b) 根拠

- `orchestrator/campaign/ident.py:389-412` の `ensure_resumable_wal` は identity 確認後に `wal.repair_truncated_tail` と `wal.recover_interrupted_attempts` を呼ぶ。
- `orchestrator/campaign/wal.py:1335-1456` の recovery は `build_admission` と topology を検査するが、verifier epoch や verifier selection assessment を検査しない。
- `orchestrator/campaign/wal.py:1461-1515` の `wal.replay` は orphan abort を WAL に append し得る。
- `orchestrator/campaign/wal.py:1518-1535` は stage の last-wins を提供する一方、verify_done の反復や consumer 側の全件処理も想定している。
- `orchestrator/campaign/s8a_trigger_sweep.py:482-494`、`orchestrator/campaign/loop.py:273-284` も `wal.replay` を呼ぶ。

### (c) 具体的な入力・状態

旧 lock、途中で切れた WAL、verify_done なしの build_start が残った状態で `ensure_resumable_wal` を呼ぶ。recovery が epoch-less abort を追加すると、その WAL は「変更されていない歴史資料」ではなく、新しいコードが生成した混合世代の資料になる。

### (d) scope 内 / 外

`ident` と resume は scope 内で要確認。WAL recovery、S8A、loop の全 consumer は plan では明示的に扱われていない。

### 成果物影響

WAL hash、abort 数、attempt topology、後続 report の受理集合が変わり、同じ campaign の admission 判定が再実行前後で変わる。

---

## 4. artifact admission の positive branch が実装可能な形になっていない

### (a) 何が壊れるか

plan は「pre-policy Git snapshot 内の stdout receipt が証明できれば旧成果物を受理」とするが、現行 admission API はその snapshot の commit/path を decision に返さない。さらに、現行 overlay に P2-2 の membership がない。

そのため、正当な旧 P2-2 を「receipt があるので受理」または「receipt がないので構造化 exclusion」と分けることができず、selection gate 到達前に admission で止まる可能性がある。

### (b) 根拠

- `orchestrator/campaign/artifact_admission.py:367-392` の `_is_proven_pre_policy_artifact` は snapshot proof を内部で boolean 判定するだけで、snapshot commit や対象 path を返さない。
- `orchestrator/campaign/artifact_admission.py:656-709` は旧 schema の場合、exact trusted pre-policy snapshot proof がなければ legacy classification にする。
- `orchestrator/campaign/artifact_admission.py:796-810` は `legacy-unclassified` だけを拒否し、その他を admitted とする。
- `orchestrator/campaign/artifact_admission.py:283-305` は legacy ledger の exact record count と path/hash を要求する。
- `orchestrator/campaign/legacy_admission_overlay_v1.json:25-43` にあるのは p3-s4-loop、p3-s5-sort-loop、p3-s8a-trigger-loop の 3 件であり、P2-2 は記録されていない。
- P2-2 の旧 lock/WAL は上記の `campaign.lock:1`、`runs/wal.jsonl:1-5` にある。

### (c) 具体的な入力・状態

P2-2 の旧成果物を `require_admitted_campaign` に渡し、receipt がなく、overlayにも campaign-specific record がない状態。現行コードからは、P2-2 が selection assessor に渡る positive/negative の構造化経路が確認できない。

### (d) scope 内 / 外

artifact admission と verifier selection は scope 内。overlay の対象 campaign 拡張、snapshot provenance API、P2-2 の historical admission policy は裁定パッケージ候補。

### 成果物影響

有効な receipt を持つ variant まで受理不能になるか、逆に admission を迂回して旧 `certified: true` が受理集合へ残る。

---

## 5. `verifier_policy_sha256` と `spec_sha256` の namespace 衝突

### (a) 何が壊れるか

plan は過去 docs の `verifier_policy_sha256` を未実装語として扱うが、repo 全体では同名 field が Reflux authority domain ですでに実装されている。また並走 T-804 は `spec_sha256` を manifest schema と mutation ledger へ伝播している。新 epoch の意味を曖昧にすると、policy digest、campaign verifier epoch、spec identity が混同される。

### (b) 根拠

- `docs/phase3-8c-wiring-design.md:55-74`、`:148-157` は `verifier_policy_sha256` を authority/cell identity の構成要素として定義している。
- `orchestrator/campaign/reflux_origin_ledger.py:238-261` は実在する `AuthorityManifest.verifier_policy_sha256` を持つ。
- `orchestrator/campaign/reflux_origin_ledger.py:444-493` は同値を manifest と origin/cell key に組み込む。
- `orchestrator/campaign/reflux_origin_ledger.py:1837-1862` は derived identity と duplicate cell を同値で検証する。
- `docs/archive/worklog-phase3-0811-419.md:530-534` は T-804 が `spec_sha256` を manifest schema、driver、report、judge 全層へ伝播させる作業であることを示す。
- `tools/mutation_harness.py:40-101`、`:1909-1943` は `spec_sha256` を persisted schema と resume/ledger 検証に使う。
- build admission の実在 digest は `orchestrator/campaign/build_admission.py:129-145`、`:470-495` の `policy_sha256`。

### (c) 具体的な入力・状態

同じ JSON/manifest に `verifier_policy_sha256` を「campaign verifier epoch」として追加し、Reflux の authority policy digest と同じ値・同じ用途だと解釈する。あるいは T-804 の `spec_sha256` を verifier identity の代用にする。

### (d) scope 内 / 外

新 field 名の分離は scope 内。Reflux/S8C authority、T-804 manifest schema、既存 `policy_sha256` の意味変更は裁定パッケージ候補。

### 成果物影響

origin ID、cell key、manifest admission、mutation resume の参照値が変わり、別 policy の成果物を同一 identity と扱うか、同一成果物を別 identity と扱う。

---

## 6. freeze bytes は不変でも、freeze 検証時の意味論は不変ではない

### (a) 何が壊れるか

「freeze producer を走らせないので bytes 不変」は、ファイルの hash については成立する。しかし freeze 検証は selection/reconstruction code を実行するため、epoch 導入後に selected variant、expected report、known-axis の意味が変わる可能性がある。

### (b) 根拠

- `orchestrator/tests/test_frozen_artifacts.py:38-85` は固定 path と SHA256 を確認するだけで、再生成や新 selection gate は確認しない。
- `orchestrator/campaign/s1_known_axes_freeze.py:710-730` の `build_document` は `_p2_entry` を呼び、P2-2 の commit fitness argmax を再計算する。
- `orchestrator/campaign/s1_known_axes_freeze.py:831-879` の `verify_document` は expected document を再構築して比較する。
- `orchestrator/campaign/s1_measurement_freeze.py:390-447` も known-axes verification と document reconstruction を呼ぶ。
- `orchestrator/campaign/s1_known_axes_freeze.py:337-369` の `_p2_entry` は verify witness/receipt/epoch を見ない。

### (c) 具体的な入力・状態

既存 P2-2 WAL に複数 commit があり、トップの commit が witness-less verify_done に対応している状態で freeze verification を実行する。bytes は書き換えられなくても、再構築した expected selected variant と selection gate が選ぶ admitted set が一致しない。

### (d) scope 内 / 外

freeze bytes の再生成禁止は明示的 scope 外。freeze 検証が新 selection 意味論に追随するかは裁定パッケージ候補。

### 成果物影響

`output/s1-freeze/*` の bytes は同じでも、known-axis report の selected variant、expected fitness、freeze verification の pass/fail が変わる。

---

## 7. S8b は独立 identity/report/judge 層で、role 名 pin も見落としやすい

### (a) 何が壊れるか

S8b は通常の `ident.campaign_id` と異なる manifest/driver/report/judge 契約を持つ。campaign verifier epoch を通常 campaign identity にだけ追加すると、S8b の成果物は旧 verifier semantics のまま残る。逆に S8b の manifest に同じ field を追加すると、凍結 manifest の pre-image が変わる。

### (b) 根拠

- `orchestrator/campaign/s8b_oracle_manifest.py:43-62` は manifest key set と generator source を独自に固定している。
- `orchestrator/campaign/s8b_oracle_manifest.py:676-702` の campaign config pre-image に verifier epoch はない。
- `orchestrator/campaign/s8b_oracle_driver.py:982-1025` は通常の five-key lock ではなく、manifest/block/campaign の独自 lock を書く。
- `orchestrator/campaign/s8b_oracle_driver.py:1305-1410` は pipeline evaluate を呼ぶが、独自 lock への verifier epoch binding がない。
- `orchestrator/campaign/s8b_oracle_report.py:912-930` は `certified` の真偽を主に見る。
- `orchestrator/campaign/s8b_oracle_judge.py:124-269` は manifest/observation 判定で verifier epoch を見ない。
- `orchestrator/campaign/s8b_ratified_freeze.py:71-82`、`:2898-2925` は `role` 名から selector role path/hash を解決する。
- `orchestrator/campaign/s8b_selector_freeze.py:51-79`、`:211-225` は role provenance と `role_file_sha256` を exact pin する。

### (c) 具体的な入力・状態

S8b manifest と ratified freeze が既存の selector role hash、manifest SHA、campaign config pre-image を凍結している状態で、epoch を通常 campaign の path 検索だけで探す。role key 経由の pin は path 名に `campaign_verifier_epoch` が現れないため、単純な grep では漏れる。

### (d) scope 内 / 外

通常 P2-5 の selection gate は scope 内。S8b manifest/driver/report/judge と role provenance は plan で未接続のため、裁定パッケージ候補。

### 成果物影響

S8b の observations、judge status、selector role provenance は新 epoch と無関係なまま certified 判定されるか、manifest pre-image 変更で既存 freeze 検証が失敗する。

---

## 8. guided は「certified に見えるが新証拠がない」WAL を書く

### (a) 何が壊れるか

guided の `_log_eval` は `certified` と `verdict` を書くが、plan が admission に要求する witness、verify config、stdout receipt を書かない。selection gate を guided write 前に置くだけでは、guided の生成物自体が後続 raw consumer に誤って certified と解釈される余地が残る。

### (b) 根拠

- `orchestrator/campaign/guided.py:126-141` は verify_done に `certified` と `verdict` を記録するが、`commit_witness`、`verify_configs`、stdout receipt はない。
- `orchestrator/campaign/guided.py:163-193` は gate 前に lock/meta を作る。
- `orchestrator/campaign/guided.py:196-227` は `ensure_resumable_wal` を先に実行する。
- `orchestrator/campaign/artifact_admission.py:711-785` は post-policy schema で current build admission/topology/receipt を検査する。
- `orchestrator/campaign/artifact_admission.py:49-60`、`:91-131` の receipt/decision schema は selection assessment を含まない。
- `orchestrator/campaign/autonomous_trial_completeness.py:49-56` は admission decision の exact key set を固定している。

### (c) 具体的な入力・状態

guided trial が `certified: true` を記録したが、witness/receipt がない状態。その WAL を `p2_2_report`、critic、将来の generic WAL consumer が読む。

### (d) scope 内 / 外

guided の pre-write gate は scope 内。guided WAL の schema と downstream report の統一は未完で、裁定パッケージ候補。

### 成果物影響

guided variant が受理集合へ誤って入り、または逆に admission で拒否され、guided report の certified 件数・winner・再現対象が変わる。

## 親の実測・前提への判定

- M3 はコード上は支持される。`orchestrator/campaign/pipeline.py:917-928`、`:982-1064` で trace を一時保存し、解析後に削除している。
- M5 は bytes hash の主張としては支持されるが、上記 6 の通り freeze 検証時の再選択までは不変性を意味しない。
- P1 は成立しない。replay/guided 以外の direct consumer が残る。
- P2 は成立しない。`screening_search_config(None)` と campaign identity 全体の history preservation は同じ意味ではない。
- P3 は旧 record shape から epoch を推定するだけでは不十分で、実際の WAL consumer への接続が未確認。
- P4 は未充足。現在の artifact admission API は positive snapshot proof の provenance を外へ返さず、P2-2 の overlay membership も確認できない。
- M1/M2 の件数自体は再測定していない。今回の判定は、件数が正しいとしても consumer 被覆と identity 整合が不足するという静的所見である。

## 裁定パッケージ候補

1. S1 report、S1 known-axes freeze、layer3 report、critic を本 wave で gate 対象に含めるか。
2. S8b manifest/driver/report/judge と selector role provenance を本 wave の identity scope に含めるか。
3. P2-2 旧成果物を artifact admission の正式な historical record として追加するか。
4. `verifier_policy_sha256`、`policy_sha256`、`spec_sha256`、新 `campaign_verifier_epoch` の namespace を固定するか。
5. guided の `certified` WAL を分析専用にするか、witness/receipt を生成する正式 producer にするか。

## 総括

**NO-GO。**

最大の所見は、P2-5 の replay/guided を止める gate を追加しても、`p2_2_report`、critic、S1/freeze、layer3、S8b が旧 `certified`/fitness 選択を継続する点である。加えて、`None` による歴史保存は campaign identity 全体には成立せず、既存 campaign の再開・directory discovery・WAL recovery を壊す可能性がある。