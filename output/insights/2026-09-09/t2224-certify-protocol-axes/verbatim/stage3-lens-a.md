## 総括

最重所見は、R2 が patched build を `pinned_clean=true` と記録し、さらに silo 固定の条件関門を非 silo の実効化証明として流用する点である。これは認定 provenance を直接偽にする blocker である。  
Cicada alias 案も、旧 cache 名単独を拒否しないため、実コンパイル値 0 を genome 1 と記録できる。  
現プランのまま段 5 へ進めず、技術的には R1 へ改訂するか、権限上それができなければ R3 で裁定へ返すべきである。  
以下は test・build を行わない静的検査結果である。

## 所見

### 1. R2 は patched source を pinned-clean と偽記録する

- 重大度: **blocker**
- 成果物影響 1 行: patched binary の登録 record が `ccbench.head_sha=<stock pin>, pinned_clean=true` と記録され、binary の実 source が成果物から復元不能になる。
- 根拠の file:line:
  - `tools/pegasus/certify_calibration.sh:657-662`
  - `orchestrator/calibrator/schema_v2.py:522-526`
  - `patches/silo-backoff-fixed.patch:1-28`
  - `orchestrator/campaign/condition_meaning_gate.py:70-78`
- 再現手順または反例:
  1. detached `BUILD_SOURCE` に `patches/silo-backoff-fixed.patch` を適用する。
  2. tracked file である `cmake/Options.cmake` と `include/backoff.hh` が HEAD と異なる。
  3. launcher はそれでも candidate に `"pinned_clean": True` を無条件で書く。
  4. false に直すと accepted schema が拒否するため、現行 receipt 形のまま R2 を正直に表現できない。
  5. 加えて条件関門は常に owner=`cc/silo/transaction.cc`、target=`ycsb_silo.exe` であり、mocc/tictoc/cicada target への実効化を測っていない。

### 2. Cicada alias 案は旧 cache 名単独を false genome として受理する

- 重大度: **blocker**
- 成果物影響 1 行: 実 binary が `INLINE_VERSION_OPT=0` なのに、登録 calibration の genome を `INLINE_VERSION_OPT=1` として発行できる。
- 根拠の file:line:
  - `orchestrator/calibrator/cli.py:429-460`
  - `external/ccbench/cmake/Options.cmake:51-54`
  - `external/ccbench/cc/cicada/CMakeLists.txt:4-6`
  - `stage2-plan.md:47`
  - `measured-facts.md:33-47`
- 再現手順または反例:

  Cicada receipt の configure argv を次のようにする。

  ```text
  -DCCBENCH_TRACE=0
  -DCCBENCH_BACK_OFF=1
  -DCCBENCH_INLINE_VERSION_OPT=1
  -DCCBENCH_INLINE_VERSION_PROMOTION=1
  -DCCBENCH_REUSE_VERSION=1
  -DCCBENCH_WRITE_LATEST_ONLY=0
  &&
  cmake --build build --target ycsb_cicada.exe
  ```

  `CCBENCH_INLINE_VERSION_OPT` は CMake に未使用とされ、コンパイラには `_CICADA` の既定値 0 が届く。一方、提案された処理は `_CICADA` を論理名へ変換するだけなので、旧名 `INLINE_VERSION_OPT=1` 単独はそのまま missing-axis を満たし、genome 1 として受理される。両名同時だけを重複拒否してもこの反例は閉じない。

### 3. 較正本体なしでは「生産できる protocol」を確定できない

- 重大度: **must-fix**
- 成果物影響 1 行: insight の生産可能集合へ、実際には accepted calibration を一件も発行できない protocol が載りうる。
- 根拠の file:line:
  - `brief.md:18-19`
  - `brief.md:65-69`
  - `stage2-plan.md:194-205`
  - `tools/pegasus/certify_calibration.sh:810-840`
  - `orchestrator/calibrator/cli.py:978-1029`
- 再現手順または反例:

  プランの 8 段を全部通しても、実行したのは receipt/genome の事前検査までである。正式経路はその後に protocol binary を実行し、測定品質を判定して `registered/calibration-*.json` を publish する。そこを一度も走らせずに証明できるのは「較正開始前まで到達可能」であり、「認定 record を生産可能」ではない。

### 4. `--skew 0.90` が不適切に新規受理される

- 重大度: **must-fix**
- 成果物影響 1 行: 実効 skew が 0.9 と同じ record を `"0.90"` で登録し、`"0.9"` を要求する floor consumer から一致不能な孤立 record にする。
- 根拠の file:line:
  - `stage2-plan.md:83-90`
  - `orchestrator/holdout_observation.py:550-562`
  - `orchestrator/campaign/layer3_report.py:595-600`
  - `tools/pegasus/submit_certify.sh:24-39`
- 再現手順または反例:

  変更前の `submit_certify.sh --skew 0.90` は unknown argument で rc=2。提案後の `0|0.<digits>` 規則では受理される。しかし repository の既存 canonical decimal 規則は末尾 0 を拒否する。CCBench は double として 0.9 を実行する一方、成果物と downstream 比較は exact string `"0.90"` を使う。

### 5. brief は出所不明の歴史的 record を silo と断定している

- 重大度: **must-fix**
- 成果物影響 1 行: 後続 insight が legacy 仮定を確認済み protocol と表示すれば、floor の根拠強度が実際より強く記録される。
- 根拠の file:line:
  - `brief.md:13-16`
  - `docs/decisions.md:43808-43825`
  - `measured-facts.md:108-111`
- 再現手順または反例:

  既存 2 record は genome も protocol の手掛かりも持たない。D1374 は silo への一致を歴史的仮定としてのみ許し、`genome-absent-legacy-record` と表示するよう要求している。brief の「genome 欄なしの silo」は確認済み事実ではない。

### 6. producer write-path の列挙は不完全

- 重大度: **nit**
- 成果物影響 1 行: 直接の selected 値への追加影響は所見 3 に包含され、ここでは変更面一覧の完全性だけが損なわれる。
- 根拠の file:line:
  - `brief.md:86-93`
  - `tools/pegasus/certify_calibration.sh:810-836`
  - `orchestrator/calibrator/cli.py:1005-1029`
- 再現手順または反例:

  brief は job-staging の `calibrate.stdout` / `calibrate.stderr` を落としている。正式生産まで主張するなら、calibrator の `candidate.json`、`calibration.json`、登録 record、publish/rejection 系も protocol・workload・genome により変化する。逆に P1-d どおり本体を走らせないなら、それらを生産可能性の証拠には数えられない。

## 検査した 5 項目への回答

### 1. 恒真化

案 (a) の推奨方向は妥当だが、案 (b) で `missing_axes` が「全面的に恒真になる」という説明は強すぎる。b でも serialized receipt の欠落・改変は検出できる。死ぬのは「producer 自身が SPACES 軸を落としたことを、独立な正本で見つける歯」である。

| 検査 | 守るもの | 案 (a) | 案 (b) |
|---|---|---|---|
| target の exact-one・形 | protocol を `ycsb_<p>.exe` target から一意に導出する | 生存 | 生存 |
| binary basename 一致 | 測定 binary と build target の取り違え防止 | 生存 | 生存 |
| SPACES 登録 | 未登録 protocol の certified genome 化を拒否 | shell 表との差を独立検出 | producer 選択には恒真的だが receipt 改変には生存 |
| build argv の CCBENCH define 禁止 | configure 後の flag 差し替えを防止 | 生存 | 生存 |
| define 文法・重複 | 値なし・非整数・同名多重指定による曖昧化を拒否 | 生存 | 生存 |
| TRACE=0 ちょうど1回 | trace-enabled binary の性能較正への混入を拒否 | 生存 | 生存 |
| missing axes | protocol の全探索軸を genome に残す | producer 表と SPACES が独立なので生存 | producer omission 検出は死亡、receipt 欠落検出だけ生存 |

根拠は `orchestrator/calibrator/cli.py:373-464`。

案 (a) の交差テストは、shell 表を実際に parse して `SPACES` と比較するなら恒真ではない。二つの独立した実体間の drift を検出する。ただし同一 commit で表とテストと SPACES を同時に誤変更できる限界は `CLAUDE.md:97-105` の D387 型であり、「完全な防壁」とは主張できない。テストが SPACES から shell 表まで生成する形なら、その時点で b と同じ恒真化になる。

### 2. 嘘の記録

- genome とコンパイラ値は常には一致しない。所見 2 の `CCBENCH_INLINE_VERSION_OPT=1` 単独が反例である。
- 二択なら、**現状の alias 案より Cicada を生産可能集合から外す方が規律 2 に正しい**。false reject は生じるが false certified genome を発行しないためである。
- ただし正しい raw cache 名 `_CICADA` を必須にし、旧 raw 名単独を拒否できるなら、既定値 0 の Cicada 全体を除外する必要はない。M3 が否定したのは値 1 の build であり、既定値 0 の protocol 生産ではない。
- 「届かない値を genome として記録する」は D1374 の却下型に当たる。`docs/decisions.md:46945-46967` は genome を build の忠実な写像とするための決定であり、未使用 cache 値を実 compiler define と同じ顔で記録するのは、その理由を破る。
- 一方、正しい `_CICADA` 値を current CMake の論理名へ正規化すること自体は嘘ではない。問題は raw route を exact に閉じない案である。

### 3. 条件関門 M4 の扱い

| 案 | 規律 2 判定 | 理由 |
|---|---|---|
| R1: `BACKOFF_FIXED=-1` を渡さない | **弱めない。技術的推奨** | 現行 pin では供給も実効化もされず、M8 では flag 有無の binary/`CXX_DEFINES` が同一。渡さない値を genome から消す方が正直である。D1198 の義務は patch define を渡す driver に掛かる (`docs/decisions.md:39910-39918`)。ただし brief の exact-argv 後方互換は改訂が必要。 |
| R2: patch を materialize | **現案では規律 2 を破る** | patched source を `pinned_clean=true` と記録する。また `_DEFINE_SPECS["BACKOFF_FIXED"]` は silo target 固定なので、非 silo の実効化を証明しない。 |
| R3: 裁定へ返す | **弱めない** | 赤を green と扱わず、矛盾したまま生産可能と記録しない。R1 を採る権限が親にない場合の正しい停止形。 |

既存テストが `BACKOFF_FIXED` の literal を pin していることは R1 を拒否する理由にならない。D1199 も「テストが固定しているのは現状であって正しさではない」としている (`docs/decisions.md:39930-39944`)。削除だけで済ませず、「現行 pin では供給しない・genome に記録しない」という新しい正しい契約へ置換すべきである。

### 4. 受理集合の変化

protocol / skew / rmw の qsub 経路は、プラン上は次で閉じる。

1. submitter が staging 前に whitelist/range 検査する (`stage2-plan.md:83-90,213-217`)。
2. 検査済み文字列だけを qsub `-v` に追加する (`stage2-plan.md:92-97`)。
3. job が env を同じ規則で再検査する (`stage2-plan.md:213-217`)。
4. submit receipt と job の実効値を exact string で再照合する (`stage2-plan.md:219-223`)。
5. acquisition receipt と calibrator CLI の protocol/workload を bench 前に完全一致させる (`stage2-plan.md:131-139`)。

カンマによる `-v` 注入、protocol の slash/未知値、rmw の未知値はこの二重検査で閉じる。

しかし新たに不当に受理される具体例がある。

```text
submit_certify.sh --protocol silo --skew 0.90 --rratio 50 --rmw 0
```

変更前は `--skew` 自体が未知で rc=2。変更後案では `0.<digits>` に合致して通るが、既存 canonical decimal 契約は末尾 0 を拒否する。その結果、実行条件 0.9 と同値なのに record は `"0.90"` となり、`layer3_report.py:595-600` の exact workload 比較で `"0.9"` campaign に一致しない。

R2 の場合はさらに、

```text
submit_certify.sh --protocol mocc --skew 0.9 --rratio 50 --rmw 0
```

も受理してはならない。通過する条件関門が実際に検査するのは `ycsb_silo.exe` であり、mocc binary の patch define 実効化を証明していないためである。

### 5. 親 brief 自身の誤り

- `brief.md:13-16` の「genome 欄なしの silo」は確認済み事実ではなく、D1374 が明示する legacy 仮定である。
- 同じ箇所の「受け手は既に protocol 一般」は偽。Cicada の cache/logical 名差を処理できず、receipt に protocol/workload binding を載せる schema もない。
- P1-a (`brief.md:58-60`) の積は不足している。認定 producer の受理には condition gate、trace separation、receipt/schema、actual calibration quality、publication がある。
- P1-d (`brief.md:65-69`) で言えるのは「calibration 前到達可能集合」まで。「生産できる集合」ではない。calibrator は protocol-independent でもなく、実際に protocol binary を実行する。
- 変更面表 (`brief.md:71-84`) は `cli.py`、acquisition writer/schema、calibrator の workload/protocol 照合、README と関連 schema test を欠く。段 2 自身も `stage2-plan.md:131-140,238-255` で認めている。
- 後方互換 (`brief.md:43-44`) は R1 と両立しない。規律 2 上 R1 を採るなら、この約束を正しさより優先してはならない。
- producer write-path (`brief.md:86-93`) は所見 6 のとおり不完全である。

## 親の実測への反論

- **M1:** 観測自体は有効。ただし母集合は「一つの default configure から build した4 target」であり、planned per-protocol define、条件関門、fresh configure、receipt、較正本体を含まない。「認定 record を生産できる4 protocol」への一般化は不可。
- **M2:** 「全軸をすべて既定と違う値にした」は Cicada について偽。`INLINE_VERSION_OPT=0` は `_CICADA` の既定値 0 と同じである。ただし未使用変数 warning により、旧 cache 名が到達しないという結論自体は支持される。
- **M3:** `INLINE_VERSION_OPT_CICADA=1` という一点の build failure は有効。これから言えるのは Cicada の登録済み探索空間全域を生産できないことまでで、既定値 0 の Cicada protocol 全体を生産不能とする一般化はできない。
- **M4:** unpatched source で現行 gate が赤という結論は有効。ただし registry が silo target 固定なので、patch 適用後の結果を mocc/tictoc/cicada の実効化証明へ一般化できない。「認定経路で一度も実走していない」という結論には反論なし。
- **M5:** なし。
- **M6:** なし。むしろ brief の「silo」断定を支持せず、genome 不在を確認している。
- **M7:** なし。
- **補足 M8:** 指定された M1〜M7 の外だが、現行 pin・同一 build path に限って R1 が binary を変えないことを強く支持する。将来 patch 入り source へは一般化できない。