# 親 brief — dev-wave 8b 再開の残余 (段 1)

wave `dev-wave-t8b-restart-residue` / branch `worktree-dev-wave-t8b-restart-residue` / base main `0c336b8e`。
手順の正本 = `docs/phase3-8b-restart-runbook.md`。状態の正本 = worklog 末尾。

## 確定済みユーザー裁定 (前提)

- **[T-747] R-4 = (B)** (worklog 403)。toolchain 束縛は env contract へ field を足さず契約の外へ置く。
  contract 内 `calibration_ref` の実 calibration bytes を derived toolchain authority とし、
  attempt 実測値と `build_v2` toolchain manifest を照合する。実装単位は **[T-783]**。
- **[T-748]** (worklog 403)。(B) の束縛検査実装後に床値実測 (W-2) を投入できる。第 1 世代で実測する方針。
- **[T-770] R1 = (b) + (c) 起票 / R2 = (a)** (worklog 403)。patch 窓は開けず分類を正す。
- **[T-781] = 択保留・調査先行** (worklog 404)。W-1 (official 解禁) は実装しない。
- **[T-750] = 未裁定のまま** (worklog 403/404 が明記)。W-3 / W-4 は着手不可。

## 段 1 実測 (すべて本 wave で実物から採取。既存 docs を根拠にしていない)

preflight P1〜P4 は期待どおり (handoff の表)。加えて次を測った。

- **M-1 (裁定の前提を覆す新事実)。** 床値実測 (W-2) は **W-1 が開かない限り投入できない**。
  機械的事実は 3 点。(i) `s8b_floor_campaign._assert_official_permitted` は `official` を
  無条件拒否したまま (`:207-217`)。(ii) `assemble_result` は `eligible_for_refreeze=True` を
  `mode == "official"` 限定にする (`:2453`) ため、**pilot 実測は再凍結に使えない**。
  (iii) 投入 script `tools/pegasus/floor_campaign.sh:962` は `--mode official` を固定で渡し、
  pilot 投入の経路を持たない。→ **[T-748] の「投入できる」は成立しない。**
  (i) は worklog 既記録だが **(ii)(iii) は裁定文にも worklog にも記録がない。**
- **M-2 (R-4 (B) の材料は実在する)。** pegasus g1 契約 (`contract_sha256=e576e9cd…`、
  `floor_protocol.json` が pin する世代) の `calibration_ref` は
  `output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json`。同 bytes は
  `/acquisition_receipt/toolchain/{compiler_path,compiler_version,cmake_version}` と
  `/acquisition_receipt/ccbench/build_argv` を持ち、build_argv に
  `-DCMAKE_C_COMPILER=/usr/bin/x86_64-linux-gnu-gcc-11` と
  `-DCMAKE_CXX_COMPILER=/usr/bin/x86_64-linux-gnu-g++-11` が **両方** 入っている。
  照合相手の `buildcache._toolchain_manifest` (`:237`) は `{cc,cxx,cmake}` × `{requested,realpath,version_first_line}`。
- **M-3 (runbook §1.2 の記述が実測と食い違う)。** 「計算ノードは `g++-12`」とあるが、
  **両世代の calibration は計算ノード (g1=bnode011 / job 867876、g2=bnode048 / job 892707) で取得され、
  記録された既定 compiler は gcc 11.4.0** (`/usr/bin/x86_64-linux-gnu-gcc-11`)。login も 11.4.0 で
  `/usr/bin` に gcc-9/11/12 が同居し gcc-13 は無い。→ `compilers_for_current_site()` が Pegasus compute で
  返す bare `gcc`/`g++` は authority と一致する見込みで、(B) は設計として閉じる。
- **M-4 (DW-O09 pin 閉包)。** `FROZEN_MANIFEST` (23 件) に `.py` は 1 件も無い。
  `floor_protocol.json` が pin するのは `contract_sha256` / `ccbench_pin` / `freeze` の 3 つで、
  **床値 driver の source を pin する台帳・trust root は無い** (path 検索・role 名検索とも hit 0、
  `ReviewId.S8B_FLOOR` は `build_admission.py:74` の enum 定義のみ)。→ 本 wave の編集は凍結 bytes を変えない。
- **M-5 (DW-O10 producer write-path)。** 床値 producer が書くのは run_dir
  (`output/calibration/s8b-floor-{mode}/…`、`:3265`) 配下の journal.jsonl (append-only)・manifest・
  result.json・result.md・launch cert store。**現時点で 1 件も存在しない** (`output/calibration/` 自体が不在)。
  よって既存 bytes は変わらない。
- **M-6 (純増検出力 — 性質で検索)。** 「build に使った compiler 実体・版が、承認済み calibration が
  記録したものと違う」を検出する経路は現状 **存在しない**。`compiler_path`/`compiler_version` は
  生成側 (`calibrator/schema_v2.py`、`silo_ladder_rung1.py`) にしか現れず、consumer が無い。
  `execution_guard.py:596` は calibration **ファイル** を契約へ束縛するだけで build toolchain を見ない。
  `build_v2` の preimage は toolchain manifest hash を含むが authority との照合はしない。

## scope (実装する)

- **A. [T-783] + [T-747] (B) — 床値 build の toolchain 束縛。**
  A-1 `s8b_floor_campaign` の 2 箇所 (`:1079` の `resolve_evidence(cxx=…)`、`:1094-1095` の
  `build_fn(cc=,cxx=)`) を `buildcache.DEFAULT_CC/CXX` 直渡しから
  `buildcache.compilers_for_current_site()` へ寄せる。
  A-2 契約の `calibration_ref` から derived toolchain authority を導く純関数を新設し
  (**sha256 検証を経た bytes だけを読む**)、attempt の `build_v2` toolchain manifest と照合して
  不一致を fail-closed で拒否する。env contract の field 構成・`contract_sha256` は 1 bit も変えない。
- **B. [T-770] R1 (b) + R2 (a) — 分類の訂正 (docs)。** `orchestrator/tests/README.md` と census の
  分類語を「外部依存物の不在」から「条件付き未実走 (repo 内で満たせるが開けていない)」へ改める。
  R1 (c) の隔離 checkout wave は起票のみ。
- **C. runbook の更新 (§6 更新契約)。** §1 の表・§1.2・§3 を M-1 / M-3 の実測値で更新する。

## scope 外 → 新事実つきで裁定へ返す (`DW-S04`。親が不採用にしない)

- **W-2 の Pegasus 投入** — M-1 (ii)(iii) が新事実。**本 wave では投入しない。**
- **W-3 / W-4 / W-5** — [T-750] 未裁定。freeze v2 再凍結と oracle 実走は着手しない。
- **[T-785] legacy `cache_key`** — 手当ての方式が未裁定。A-1 は build_v2 経路のみで legacy を触らない。

## 不変条件 (破ったら停止)

1. `ExecutionEnvironmentContract` の field 集合と全世代の `contract_sha256` を変えない (402 の実測 M2)。
2. `FROZEN_MANIFEST` 23 件の bytes・key-set を変えない。`floor_protocol.json` の 3 pin を変えない。
3. `_assert_official_permitted` の拒否意味論を変えない。production の bypass flag / 環境変数を作らない。
4. 新設する束縛は **fail-closed のみ**。「記録があるから認可済み」型の unlock を作らない (D86(8))。
5. authority は sha256 検証済み calibration bytes からのみ導く。attempt の自己申告を authority にしない。
6. キュー投入をしない wave とする (M-1 により床値投入が不可のため)。並走ガード 3 条件は維持。

## 成果物影響 (`DW-G05`、1 行ずつ)

- **A を実装しない場合:** 承認済み calibration と違う compiler で測った床値が無検査で通り、
  freeze v2 の `floor`/`budget` に別 toolchain の値が焼き込まれて certified 選択の判定境界が変わる。
- **B を実装しない場合:** 受入全走の 4 skip が「外部依存物の不在」と誤分類されたままとなり、
  source digest の alias 防止・macro fail-closed が恒久未検査であることが台帳から読み取れない。
- **C を実装しない場合:** 手順書が W-2 を「R-4 さえ済めば投入可」と示し続け、次 wave が
  投入して計算ノードで rc=2 に倒れる (実測 M-1)。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** 束縛の照合粒度は「cc/cxx の realpath 完全一致 + cc の `version_first_line` 完全一致 +
  cmake の version 完全一致」とする。cxx の version は calibration に authority が無い (build_argv は
  realpath のみ) ため照合対象にしない。
- **(P2)** authority の導出は build_argv の `-DCMAKE_{C,CXX}_COMPILER=` を第一とし、
  `/acquisition_receipt/toolchain/compiler_path` とは **cc について交差検証** して不一致なら拒否する。
- **(P3)** 束縛検査は `official` / `pilot` の両 mode で発火させる (pilot だけ素通りさせない)。
- **(P4)** 検査の設置点は floor campaign の build 呼び出し直後 (`build_fn` の戻り値の
  toolchain manifest を見る) とし、`buildcache` 本体には手を入れない。

## 並列分割

本 wave は **受理集合を変える gate を新設する** ため `DW-C00` により軽量版にしない。
段 2 プラン 1 本、段 3 敵対 2 レンズ、段 5 実装 1 本 (A のみ。B/C は親が docs として書く)、
段 6 レビュー 2 本。B と C は A と file が重ならない。
