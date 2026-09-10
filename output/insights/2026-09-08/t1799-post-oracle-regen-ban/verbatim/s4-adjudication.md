# 段 4 裁定 (親) — [T-1799] / D984

段 2 plan と段 3 の 2 レンズを裁定し、plan v2 と変異事前登録を確定する。

## 所見の裁定

| # | 所見 (出所) | 裁定 | 扱い |
|---|---|---|---|
| 1 | `build_v2` API では binding base A と `masstree_source_dir` B の不一致が現行 validation を通り、実効根は B になる (段 2、レンズ A、レンズ B) | **real** | 採用。build 前の実効根 exact 一致を要求する |
| 2 | ただし official floor caller に限れば A/B は常に一致し、この述語は恒真 (レンズ A) | **real** | 採用。**恒真ではあるが必要**。保護を掛ける根が build に使われる根と同じであることを保証しなければ、保護自体が空振りする |
| 3 | `make_snapshot_non_writable()` は root だけでなく **parent (= FETCHCONTENT_BASE_DIR)** の write bit も外し、`<base>` 直下への新規 entry 作成 (別依存の populate、`izanagi-masstree-prebuild`) を巻き添えで壊す (レンズ B) | **real** | 採用。**既存 primitive の as-is 再利用を却下**。親を触らない専用の保護を書く |
| 4 | 全 untracked node の型と chmod 可否を新しい受理条件にする副作用がある (レンズ B) | **real** | 採用。保護対象を「build 根の直下 tree」に限り、chmod 不能な node は保護失敗として fail-closed にする (受理を広げない) |
| 5 | plan の `effective_root` 再利用は、build 後の root drift 検査を実質的に消し、受理を広げる (レンズ B) | **real・規律 2 違反** | **plan から撤回**。build 前の `protected_root` と build 後の再取得値を別変数にし、既存 build 後 assert を必ず再実行する |
| 6 | SIGKILL / OOM / PBS walltime で `finally` が走らず、保護した tree が読取専用のまま残る (レンズ B) | **real** | **限界として明記し、この wave では機構を足さない**。official floor の base は PBS job ごとの `/scr/<jobid>` を create-only で作り、official mode は caller 指定 base を拒否する (レンズ B が実測) ため、poison は死んだ job 自身の scratch に閉じる。復旧台帳・daemon の新設は仮想リスク向けの追加であり scope 外 |
| 7 | 同じ base を共有する 2 つの保護 context は相互排他でなく、交差復元で禁止が破れる (レンズ B) | **real** | **限界として明記**。実効的な排他は process 間 lock を要し、D953 が「別審査に属する」と明記済み。この wave では作らない |
| 8 | レンズ B の推奨「private snapshot へ戻す」 | **不採用** | D984 は 2 手段を**どちらも**許可している。private snapshot は masstree/mimalloc/googletest の 2 回目の全 tree copy、binding 導出、postflight 期待値、cleanup lifetime の連動変更を要し (段 2 が file:line で列挙)、`s8b_floor_campaign.py` へ波及する。所見 3〜5 を直せば書込み不能化が最小で閉じる。**所見 6・7 の限界は private snapshot でも lock なしでは同型に残る** (別 process が同じ private root を指せる) |
| 9 | 書込み不能化は custom command の最初の source write を EACCES で止め、非 0 が `_run()` から Python まで伝播する。source tree 外へ出る bypass は無い (レンズ A が 5 command 全ての `WORKING_DIRECTORY` で確認) | **real** | 機序の根拠として採用 |
| 10 | up-to-date な post-oracle build は masstree source root へ何も書かないので保護と両立する (レンズ A、保存済み build log の正例あり) | **real** | 正例の根拠として採用 |
| 11 | 親 brief の DW-G05「A-2 / A-6 の certification が材料の同一性を主張できるようになる」は誇張 (レンズ A・B が独立に反証) | **real** | **brief を訂正**。本変更が直接改善するのは **S8b floor の `sort_best` cell の proof chain** (binary、admission receipt、`sort_swo_oracle` record) である。A-2 / A-6 は別 driver で generic `run_campaign()` を通り、post-oracle binding を渡さない |
| 12 | 親 brief の確定裁定一覧が D954 を落としている (レンズ B) | **real** | **brief を訂正**。D954 (実効値は build 自身の成果物から読み、argv を証拠にしない) は本件の直接前提 |
| 13 | 親 brief の「buildcache.py の変異は drift mask に必ず吸収される」は言い過ぎ。吸収されるかは選んだ焦点 node 次第 (レンズ A) | **real** | **brief を訂正**。ただし変異の狙い先を lock closure 外の file に置く判断自体は維持する (帰属が確実なため) |
| 14 | 段 2 が正例の根拠に挙げた `test_real_prebuilt_masstree_material_is_pinned_when_explicitly_configured` は build を fake に差し替えており、実 CMake build の根拠にならない (レンズ A) | **real** | 記録する。protected 実 build は本 wave で実走しない。根拠は静的機序 + 保存済み非 protected build log であると明記する |
| 15 | 既存 test の破損予測 0 件 (段 2) | **反証されず** | 受け入れる。ただし親の焦点走で実測する |

## plan v2 (確定)

**方式: D984 手段 (b) 書込み不能化。ただし対象を build 根だけに限る。**

1. `orchestrator/campaign/sort_swo_dependency_material.py` に、post-oracle 専用の
   context manager を 1 つ足す。責務は次の 4 点だけ。
   - (a) 呼び手が渡した **実効 build 根**と、binding が指す source 根
     (`<binding.fetchcontent_base_dir>/masstree-src`) を canonicalize し、**exact 一致**を要求する。
     不一致なら yield 前に `CanonicalDependencyMaterialError` へ倒す (build を 1 度も起動させない)。
   - (b) 一致した根**そのものと、その配下の全 node** から write bit を外す。
     **親 directory には触らない。**
   - (c) 保護後に write bit が残る node があれば fail-closed で倒す。
   - (d) 成功・build 失敗・検査失敗の全経路で `finally` により exact mode を復元し、
     復元に失敗したら raise する。
   汎用 flag、skip knob、trace 分岐、台帳、CLI、process 間 lock は持たせない。
2. `orchestrator/campaign/buildcache.py` の `_build_v2_impl` で、post-oracle 束縛がある場合だけ、
   configure 後の既存 2 assert の**後**に `_masstree_source_root_from_cmake_cache(staging)` を呼び、
   その値を上記 context へ渡してから `cmake --build` を実行する。
3. **既存 assert を 1 つも削らず、緩めず、順序も変えない。**
   初期 assert、configure 前 assert、configure 後の disconnected + material assert、
   build 後 material assert、build 後の実効根照合はすべて残す。
4. **build 後の `effective_root` は必ず取り直す。** 保護のために configure 後に読んだ値を
   後段の compiler-input / receipt 検査へ流用しない (所見 5)。
5. 公開 API・configure argv・cache identity・receipt schema・submodule pin は変えない。
   束縛なし呼び出しは 1 byte も変わらない。
6. docs は段 7 の fragment のみ。新規 CLI・新規台帳・新規成果物 schema は作らない。

## 明記する限界 (成果物へ書く)

- 保護は同一 uid の協調的 process に対する discretionary-mode 保護である。
  owner が自ら chmod を戻す actor と privileged actor は阻止しない。
- SIGKILL / OOM / job の壁時計切れで復元が走らない場合、保護した根は読取専用のまま残る。
  official floor では base が PBS job ごとの create-only な job-local root であるため
  影響はその job の scratch に閉じる。復旧機構はこの wave で作らない。
- 同じ根を指す 2 つの保護 context の交差復元は防げない。実効的な排他は process 間 lock を要し、
  D953 が別審査に属すると裁定済みである。

## 変異事前登録 (DW-M01、実装前)

すべて `orchestrator/campaign/sort_swo_dependency_material.py` の新 context 内に置く
(同 file は `campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS` に含まれず、drift mask に吸収されない)。

| ID | 変異 | 期待して赤になる検査 | 単一理由性の確保 |
|---|---|---|---|
| M1 | (a) の exact 一致を恒真化する | 実効根が binding source 根と異なる入力で、**build が 0 回**であること (`events == ["configure"]`) | 既存の build 後 root drift 検査が同じ入力を最終的に拒否するため、赤の帰属を「例外型」でなく**「build を起動しなかった」時点差**に置く |
| M2 | (b) の write bit 除去を no-op にする | 保護中に判定根の `config.h` と archive を**同一 bytes で**再書込みする試行が成功してしまうこと | 既存の前後 manifest / config / archive / HEAD 照合はすべて同じ値を見るので赤にならない。この変異に固有 |
| M3 | (d) の `finally` 復元を削除する | context 退出後に元 mode が exact 復元されていること | 復元は他のどの層も行わない。この変異に固有 |
| M4 | (b) を親 directory まで広げる (**承認外の過剰拒否の正例**) | 保護中に `<base>` 直下へ新しい entry を作れること | 過剰拒否は他のどの層も検出しない。この変異に固有 |

実装後に各変異の単一理由性を実測で確認し、成立しなければ登録せず実効 gate へ再照準する (F820/F28)。

## 分割方針

実装子 1 本 (Codex `role=author`、`sandbox=workspace-write`)。変更面が
2 file + 2 test file の単一単位であり、所有を割らない。
