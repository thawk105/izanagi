## 次に落ちる層

以下、`P`＝`tools/pegasus/probes/t316_sandbox_backend_probe.py`、`G`＝`orchestrator/campaign/condition_meaning_gate.py`、`H`＝`orchestrator/campaign/patchharness.py`。相対パスは指定 worktree 内を指す。実走はしていない。

### 1. 「案 B の直後に masstree の config.h 不在で落ちる」は refuted

- **根拠:** P:1859 は `FETCHCONTENT_SOURCE_DIR_MASSTREE` に cache を指定する。`external/ccbench/cmake/ThirdParty.cmake:58` は `"${masstree_SOURCE_DIR}/config.h"`、同:85 はその source directory を include path に設定する。include chain は `cc/silo/ycsb_silo.cc:14` → `include/masstree_wrapper.hh:20` の `#include <config.h>`。親が報告したファイルがその実行時にも読めれば、この欠落は回避される。
- **成果物影響:** この入力で「次は config.h 欠落」と台帳へ記録すると、未観測の失敗を原因として固定してしまう。
- **通る正例:** 報告済み cache を requested／stock 共通の `FETCHCONTENT_SOURCE_DIR_MASSTREE` に指定する。

ただし、**config.h の存在だけで full build 成功までは証明できない**。同 CMake:66–78 は archive も生成対象にし、同:86 は archive をリンクする。段2:174 は archive の存在も報告しているが、内容・リンク適合性の確認ではない。

### 2. 「続いて A-2 の root path 差で必ず落ちる」も refuted

- **根拠:** G:2663–2699 は raw bytes 一致と root-location-only の双方を緑として発行する。P:124–133 は両 exact pair を許可し、P:340 は `"comparison": supply.evidence.get("comparison")` を記録する。追加射影の D1625:10–16、D1849:38–42 はこの現行契約を明示する。
- **成果物影響:** A-2 当時の「裁定待ち」を現在も blocker と扱うと、既に許可された pair を使う B を誤って除外する。
- **通る正例:** closure に属する `__FILE__` の source-root 差だけが残り、`stock-inert-preprocess-root-location-only`／`stock-inert-root-location-only` が発行される場合。

**次の確定的な失敗箇所は、読んだコードからは名指せない。** 案 B 後の順序は、依存 build → requested configure → stock configure → owner preprocess → inert 比較 → outside CCBench build → inside 依存／CCBench build。G:2619 の `compile-command-drift`、G:2703 の `stock-inert-mismatch` は次の拒否候補だが、今回それが発火するという証拠はない。「第2層を越えれば必ず緑」も未証明である。

## sandbox と identity の整合

### 3. 「案 B は sandbox 内の Git 書込みで破れる」は refuted

- **根拠:** 段2:79 は「patch 適用は outside / inside 合計1回、host 側」、同:112–114 は host で生成・破棄し、requested を scratch 外から readonly mount すると明記する。P:1889 の関門呼出しも host 上。sandbox 化は P:1909 の `profile.run(...)`。`.pbs:109–112` は Python を直接起動し、namespace は P:827–839 の bwrap subprocess で作る。
- **成果物影響:** この設計を「sandbox 内で worktree add する」と読んで却下すると、実際には実行されない経路を理由に B を除外する。
- **通る正例:** host の一時 requested 木を S6 profile の readonly roots に追加し、両 build に同じ絶対パスを渡す。

P:847–851 の mount 順では scratch の writable bind が後なので、**requested を scratch 内へ置く実装は段2の構成を満たさない**。また S3 の `write_repo`／`source_read_only` は P:1236–1238 の元 repo 上の marker を測るため、それだけを新 requested 木の実測証拠として流用できない。

### 4. 「checkout の使い捨て木へ applied を使うのは契約違反」は refuted

- **根拠:** H:24–27 は逐語で `with checkout(pin) as sub: with applied(patch, pin, sub): ...` を指定する。H:115 の lock key は渡された `sub` の realpath。H:255–263 は同じ `sub` を lock・apply・revert に渡し、H:221 はその木で `git checkout -- .` を実行する。
- **成果物影響:** 契約違反として除外すると、harness が明示的に提供する使い捨て requested 構成を誤って失う。
- **通る正例:** `checkout` の返り値を `applied` の第3引数へ明示的に渡す。

### 5. 「別 session の worktree 作成と並行すると共有 source を壊す」は refuted。ただし無競合の一般化は nit

- **根拠:** H:362–364 は一意な親 directory の下へ `worktree add --detach` する。元 working tree の checkout は行わない。一方、base の Git 管理領域を共有するのは事実で、`_tree_lock` は add/remove を覆わない。H:91–95 の retry も worktree add を対象にしない。
- **成果物影響:** 通常の並行 add だけで source 汚染すると断定する根拠はないが、Git 操作失敗時には S6 が例外終了する。
- **通る正例:** 同じ base の pin から、各 session が別の一意パスへ detached worktree を作る。

「Git 管理領域まで競合しない」「常に成功する」との保証は読めない。ただし今回の具体的な競合失敗は示されておらず、新しい共通 lock の追加を must-fix にする根拠もない。

### 6. 「outside-control 短絡で cleanup が飛ぶ」は refuted

- **根拠:** P:2060–2064 の短絡は通常の式評価である。段2:67–79 のように両 build を context 内へ置けば、H:262–263 の `finally: revert_worktree(...)`、続いて H:373–379 の worktree remove／確認が走る。body の例外でも同じ。
- **成果物影響:** この短絡自体では patch 木を次回へ持ち越さない。
- **通る正例:** outside が `success=False` を返し、inside を省略して二重 `with` を抜ける場合。

保証されるのは cleanup の**実行**であり、remove 自体の成功や強制終了時の cleanup までではない。

### 7. 「元 HEAD だけ検査して別木を build する不一致を再生産する」は、段2の記載どおりなら refuted

- **根拠:** 段2:100 は「checkout 直後の requested 木にも、同じ expected HEAD を使う現行検査」、同:101–105 は identity を「patch 前の基底」と定義する。P:1785–1787 の検査は HEAD だけでなく clean・replace refs・tree SHA 形状も要求する。
- **成果物影響:** requested の基底検査を実装せず元木の記録だけ残すと、`source_identity_valid=True` が build 対象の導出根拠を示さなくなる。
- **通る正例:** requested 自身の patch 前 identity を記録し、束縛した固定 patch を適用した同じ木を gate と両 build が使う。

段4で確定すべき点は、`source_identities` のどの entry に requested の path／基底 identity を保持するかである。patch 後の木を「clean な pin そのもの」と記録する実装は、この設計とは異なる。

## 時間予算

### 8. 「追加処理で必ず予備を食い潰す」は refuted。「収まる根拠がない」は real

- **根拠:** 実際の stage budget は共有 `policy.json` ではなく、`tools/pegasus/policies/t316_sandbox_backend_v1.json:7–14` にある。PBS は5400秒、probe deadline は5100秒、S6 開始条件は残3600秒、CCBench build cap は**片側1200秒**。P:1843–1848 の依存処理 cap 合計は片側1200秒、CCBench configure は片側300秒。したがって既存処理だけでも cap 合計は `2 × (1200 + 300 + 1200) = 5400秒`、関門等は別途である。
- **成果物影響:** 予算内到達を未測定のまま完了扱いすると、実経路で `S6_WALLTIME_RESERVE_REACHED` になる余地を残す。
- **通る正例:** 同一実経路の実行記録で、checkout・両関門・両 build・cleanup が残時間内に終わることを示す。

cap は実行時間の下限ではないため、5400秒という和から timeout 必至とは言えない。追加 checkout／patch は一回で、関門 configure も既存処理である。一方、P:1889 の関門には `deadline_ns` が渡らず、G:302 の subprocess timeout は個別120秒。段4には**処理時間の内訳を含む既存 t316 確認走**が必要であり、静的に「余裕あり」とは判定できない。

## 実測設計の実効性

### 9. login driver が現状の記述だけで実行可能、という扱いは real の欠落

- **根拠:** 段2:199 は「既存依存 install prefix」を入力とし、同:209 は無ければ準備するとする。しかし親の報告は gflags／glog の source directory の存在まで。`external/ccbench/CMakeLists.txt:33–34` は両者を `find_package(... REQUIRED)` する。
- **成果物影響:** source の存在だけで測定開始可能と扱うと、A/B の値を得る前に依存解決で停止し、択一記録が作れない。
- **通る正例:** 利用可能な install prefix と実効 toolchain を確定して driver に渡すか、依存準備を含め計算ノードで確認する。

**g++-13 不在そのものは blocker として refuted。** P:1839–1840 は gcc／g++ への fallback を持つ。ただし login の g++ で得た結果を、別 compiler が選ばれる計算ノードへ一般化はできない。

よって、現資料から「計算ノードでしか一切測れない」とまでは言えないが、**login での成立は未確定。最終目的の inside build は計算ノード実経路でしか確認できない。**

### 10. 「runner 経由で build する」の実装経路が空白なのは real・must-fix

- **根拠:** 段2:211 は「build 部分は既存の `tools/run_tests.py` 経由」とする。実装は `tools/run_tests.py:563` で `cmd = [python_executable, "-m", "pytest"]` を構築し、同:2397 は入力を `pytest_args` として処理する。記述された任意の Python driver／CMake command をそのまま起動する build 入口ではない。
- **成果物影響:** この空白を残すと、使い捨て driver は所定の実行経路に接続できず、採用判断の実測成果物が得られない。
- **通る正例:** runner が実行できる pytest entry から測定 body を呼ぶ具体形を定める、または最終確認を既存 t316 実行体に担わせる。

「未読なので command を書かない」という慎重さ自体は矛盾ではない。しかし「経由して実行できる」と確定する根拠にはならない。**段4が入口・引数・実行場所を埋める必要がある。**

### 11. 「判定式が両案で同じ値を返して択一不能」は refuted。ただし実測だけで選べるという親の前提は real の不足

- **根拠:** 段2:151–160 の A は `E_A ∧ C_A`、B は `G_B ∧ B_B` で、同じ判定ではない。同:162 は両方成立なら実測だけでは決まらないと明記し、同:166 は `K_A` 不成立を認める。
- **成果物影響:** binary 一致をそのまま案 A の採用可能性に読み替えると、測定した技術条件と採用判断が食い違う。
- **通る正例:** `G_B`・`B_B` と既存契約の両立を確認し、A の binary 比較結果とは分けて段4の採用理由を記す。

## 親 brief の検査

### 12. 一般化しすぎている箇所は real

- **根拠:**
  - **P1-2（brief:52–53）:** A-2 の空 build tree から、SOURCE_DIR 直指定でも config.h が欠けると推論している。今回の報告済み cache については所見1で反証。
  - **P1-3（brief:54–55）:** F934 の逐語:107–108 が証明するのは認定経路の binary SHA 一致。t316 の toolchain／prefix／build 入力での一致は別であり、brief 自身も「未実測」と留保している。
  - **実測環境（brief:64–66）:** login driver を既定にするには install prefix と runner 入口が不足している。
  - **先例（brief:81）:** `backoff_sweep.py:437–438` は checkout を stock に使い、元木へ patch を当てる。さらに A-2 README:45 は同 driver の inert 経路を「未実測」とする。「緑に到達している対照実装」から t316 の inert 成功へは一般化できない。
- **成果物影響:** これらを確定事実へ昇格すると、択一理由と失敗台帳が別経路の証拠を t316 の到達証拠として参照する。
- **通る正例:** 「この cache のヘッダ欠落は回避」「F934 の一致は当該経路のみ」「t316 の family・inside build は未測定」と範囲を限定して記録する。

## 総括

**案 B を必ず停止させる次層は、静的検査では確定しなかった。** config.h 欠落、既知の root path 差、sandbox 内 Git 操作、`checkout → applied` の契約違反、通常短絡での cleanup 漏れという攻撃は反証された。

段4で埋めるべき実効性の空白は次の3点。

1. 使い捨て driver の実行入口と、依存 install prefix・実効 compiler。
2. requested の基底 identity を既存記録へどう保持するか。
3. 既存 t316 実経路で、発火した exact pair・inside build・残時間を確認する手順。

**現時点の判定は「実装候補として残るが、目的状態への到達は未証明」。** ファイル変更、Git 状態変更、pytest、configure、build は実施していない。