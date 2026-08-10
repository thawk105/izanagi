---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-11
wave: dev-wave-t8b-restart-integration
seq: 1
title: 8b 再開の統合 wave — 実装は T-749 の 1 件に縮み、W-1/W-3/W-4 と R-4 は新事実つきで裁定へ返した (コード + docs、受入 8412 passed / 20 skipped / 515.68 秒 / rc=0、変異 7 KILLED + 1 MISMATCH = 実質 8/8、branch worktree-dev-wave-t8b-restart-integration)
---

## 本文

- **起票根拠 = worklog 383 の裁定 [T-747]〜[T-750] と、検分 wave (380) の再開手順書。**
  並走ガード 3 条件は起票文へ記載済み。**キュー投入の直前に毎回 `qstat` で再確認**し、
  走行中は他 wave の汎用テスト dispatch (`izdw-*`) だけで T-139 の pilot / 本走 job は
  wave を通じて一度も走っていなかった。ノード同居なし。裁定要求は A 系の後ろに並べる
- **preflight (手順書 §2) は P1〜P3 とも期待どおり**: ccbench gitlink `d706650c…` 一致、
  凍結成果物 manifest 2 passed / rc=0、oracle gate-check は rc=2 で拒否 2 件 exact
  (`floor-null` と `budget-null`)。`holdout-freeze-verify:` の混入なし
- **[T-747] (a) の実装前提が段 1 実測で覆った。** `ExecutionEnvironmentContract` へ `toolchain`
  field を 1 つ足して実測したところ (模擬でなく実編集、F29)、`campaign.env_contract` は
  **import 時点で fail-closed** した (`pegasus g2 contract_sha256 が reviewed golden と一致しない`)。
  `contract_sha256` は全 field の canonical JSON の sha256 で、`_build_registry()` が import 時に
  reviewed golden literal と照合するため。編集は即時復元 (`git diff` 空、commit と一致)。
  pegasus g1 hash は発効記録・floor protocol・selector 予測封印の **3 つの pin** が同時に握っており、
  作り直すと事前登録性 (式 3) に触れる。手順書 §4 が「迂回してはならない」とした経路である
- **段 3 の敵対 2 レンズ (max) がいずれも NO-GO** (BLOCKER は A が 6 件、B が 5 件)。
  W-1 の中核だった「固定 FD で scheduler の spool bytes を独立取得する」は恒真化であり
  (呼び出し側が選んだファイルを開くだけで、wrapper を経ない子が同じ三者一致を作れる)、
  受領証を unlock にすると D86(8) が禁じた「記録があるから認可済み」を再導入して
  任意の clean revision が official になる。admission 証拠は certificate v1・journal schema・
  ratified verifier のどこにも残らず、下流は本物と自己整合な偽物を区別できない
- **段 4 で実装 scope を [T-749] の 1 件へ縮めた。** W-1 / W-3 / W-4 は `DW-S04` に従い
  親が不採用にせず、新事実つきで再裁定へ返す。逐語と択一は
  `output/insights/2026-08-11_t8b-restart-integration/`
- **親の実測 2 件を敵対レンズの指摘で訂正した。** (i) 「gcc-13 は物理的に閉じている」は言い過ぎで、
  module / spack / conda / 個人 modulefiles には無いが `apt` の PPA に候補があり (root 必要)、
  singularity / apptainer / docker も実在するためコンテナ経路が残る。
  (ii) 「既定 toolchain を替えると偽 hit する」は legacy `cache_key` 限定であり、床値は `build_v2` を
  使い pre-image に cc/cxx と toolchain manifest hash を含むため保護されている
- **副産物**: `buildcache.compilers_for_current_site()` が既に存在し Pegasus compute で system
  compiler を返すこと、`pegasus_floor_scoping.py` が既にそれを使い床値 campaign だけが
  `DEFAULT_CC/CXX` を直接渡していることを実測した。R-4 の択 (B) の実装コストを下げる材料である
- **[T-749] の実装**: CLI 専用 helper を足し、受領証が受領済みの drift だけを許す。
  `verify()` / `verify_document()` / `generate` / `search` と oracle driver の受理集合は不変。
  段 6 の敵対レビュー 2 本 (high) がいずれも NO-GO を返し、所見 9 件を fix した。
  絶対 sibling import は既存 module と同じ module 先頭の `__package__` bootstrap へ置き換え、
  `campaign-absolute-sibling-import` invariant に抵触しない形にした
- **変異 baseline で F57 が再発した。** 1 回目の変異本走は baseline が
  `test_codex_worker_launch.py::test_all_repo_policy_reasoning_values_are_accepted[xhigh]` 1 件で
  赤になり (523.38 秒、`failed_predicates=["process_group_residual","termination_verified"]`、
  `loadavg=(12.67, 3.24, 1.68)`)、harness が production write 前に fail-closed で中止した (rc=2)。
  同 file の単独再走は **77 passed / 6.00 秒 / rc=0** で再現しない。2 回目の baseline は
  **PASSED / rc=0 / 533.56 秒**
- **変異 matrix は 8 件中 7 KILLED / 1 MISMATCH / SURVIVED 0。** MISMATCH は MU-1 で、
  期待 node は正しく落ちた一方 `test_campaign.py::test_pipeline_stale_screening_falls_back_to_verify_first_and_records_trace`
  が同時に落ちた。同 test file は `s8b_holdout_freeze` を 1 箇所も参照せず変異は到達しえない。
  単独再走は **1 passed / 2.60 秒 / rc=0** で再現しないため `DW-O18` により帰属せず、
  `DW-M02` に従い初回結果を消さず erratum として残す。**実質は KILLED 8 件である**
- **検査の実測**: 受入全走 **8412 passed / 20 skipped / 515.68 秒 / rc=0**。
  対象 6 ファイルの部分走 196 passed / 1 skipped / rc=0 (計算ノード job 901134、250.75 秒)。
  repo scan gate rc=0 (両 holdout の conjunction hit 0 件)、`check_docs` 違反なし、
  provenance full 監査 rc=0。実 repo の CLI verify は **rc=1 から rc=0** へ変わった
- **エージェント工数**: codex 子 6 本 (プラン 1 = max / 敵対相談 2 = max / 実装 1 = high /
  レビュー 2 = high) + fix 1 本 = 7 本。親は brief・裁定・統合・実走・記録
- **段 8 自己改善**: 候補 1 件を予算超過で**起票へ回した**。`DW-O09` は「path 検索が見つけるのは
  path を key にする pin だけ」と述べるが、**同一性 hash を全 field から導く dataclass**
  (env contract) は path でも role 名でもなく、本 wave はこれを runbook §4 からの連想で測った。
  該当 reference 節への 1 行統合を試したところ `DW-O09` が 1063 bytes となり単節予算 1000 を超えた。
  「予算のために安全義務を削除・弱化しない」に従い撤回し、下記「新規」へ起票する
- **ユーザー手番**: 裁定 5 件 (下記「新規」)。push は行わない

## 次の一手差分

### 完了

- [T-749] 単体 verify CLI を T-080 受領証参照へ寄せ、恒常赤を解消した。
  `verify()` 本体と oracle gate は不変で、受領証に無い drift は従来どおり赤のまま。
  remaining: none
  base: 1b01dd9da713229a9407a1b1cea7407fe31e79b291f4b5f1960ea1f750d241ca

### 更新

- [T-747] **P1・再裁定待ち (B 系)**: (a) の実装前提が段 1 実測で覆った。contract へ field を足すと
  登録済み全世代の hash が変わり `env_contract` が import 時 fail-closed し、発効記録・floor protocol・
  selector 予測封印の 3 pin が同時に外れる。択 = (A) 協調再凍結 / (B) 束縛層を contract の外へ置く
  (親推奨、`calibration_ref` は既に hash 束縛で compiler path/version を保持) / (C) [T-657] の
  恒久機構を待つ。材料 = `output/insights/2026-08-11_t8b-restart-integration/`
  base: f506ec57cb46e674c282b5b851db111ce0cb853e6e27cfa52be281773c2d0335
- [T-748] **P1・[T-747] の再裁定待ちで停止 (B 系)**: 第 1 世代で実測する方針は変わらないが、
  [T-747] の択が確定するまで床値実測は投入できない (投入してもビルド段で fail-closed に倒れる)。
  W-1 の解禁も下記のとおり止まっている
  base: 2e143a933f26d6d371915f39034d69da93ef40ee19b9077cfbb3fcdcc53ac02c
- [T-750] **P2・再裁定待ち (B 系)**: freeze v2 producer と oracle manifest CLI を同一 wave で実装する
  方針は変わらないが、実装前に決める点が段 3 で 2 件出た — producer identity (transition table が
  `/generator/path` の変更を拒むため新 module は proof chain に記録されない) と budget authority
  (有限非負しか検査されず、巨大値で探索予算を無効化できる)。材料 = 同 insights
  base: c2ecb14be693a7aeb7dfff6052df56a4e49bd7b2c669854c33639b52405ad3e3

### 新規

- {{T:t088-admission-authority}} **P1・新規 (ユーザー裁定待ち、B 系)**: W-1 (official 解禁) の認可設計。
  D86 §4 の「独立取得した spool bytes」は実装手段が無く、受領証を unlock にすると D86(8) の禁止に
  抵触する。択 = (A) spool 証拠の取得方式を設計し直す / (B) 認可を機械化せず運用前提に留める
  (受理集合が全 clean revision へ広がることを明示受諾) / (C) ユーザーが指した revision を束縛する
  authority を新設 (D86(3) を覆す) / (D) admission 証拠を certificate v2・journal・ratified verifier へ
  通す (D86(5) の先送りを解除。(A)〜(C) と独立に必要)。**親の推奨は無い**
- {{T:oracle-manifest-schedule-authority}} **P1・新規 (ユーザー裁定待ち、B 系)**: W-4 の schedule authority。
  exact key 検査は schedule の内容を束縛しないため、各 holdout を 1 configuration に間引いた
  完全 block schedule を作れば judge が `unique-best` を返し **certified 選択を直接改変できる**。
  択 = (a) active ratified freeze 限定 + 全 cell 積 + 承認済み `n`/`master_seed` 束縛まで含めて実装 /
  (b) reviewed spec を凍結成果物として先に作り CLI は hash 照合だけ行う / (c) oracle 結線 wave へ送る
- {{T:floor-campaign-site-compiler}} **P2・新規 (B 系)**: 床値 campaign だけが
  `buildcache.compilers_for_current_site()` を使わず `DEFAULT_CC/CXX` を直接渡している。
  `pegasus_floor_scoping.py` / `pipeline.py` / `loop.py` / `screening_driver.py` は既に site 解決を使う。
  [T-747] の択が (B) に決まった場合の実装単位として起票する
- {{T:dw-o09-hash-bound-dataclass}} **P3・新規 (段 8 発、ユーザー裁定待ち)**: `DW-O09` の pin 閉包に
  「同一性 hash を全 field から導く dataclass・schema」を含める明確化。1 行統合を試したが
  単節予算 1000 bytes を 63 bytes 超過した。択 = (a) `DW-O09` の既存文を意味等価に縮めて空ける /
  (b) 予算値の独立審査 / (c) 見送り。**予算のために安全義務を削除・弱化する案は採らない**
- {{T:legacy-cache-key-default-toolchain}} **P2・新規 (B 系)**: legacy `buildcache.cache_key` は
  既定 toolchain を key から省く後方互換規則を持つため、既定を替えると旧ビルドと偽 hit する。
  床値の `build_v2` は保護されているが legacy 経路の production caller は複数実在する。
  [T-747] の択に関わらず手当てが要る
