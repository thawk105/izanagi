# 段 1 brief — [T-548] gflags / glog の versioned な共通調達経路を新設する

## 研究前進

**土台。** 止めている研究は 2 つで、いずれも実測済み。(1) [T-2625] の sealed snapshot 実 CMake
qualification は計算ノード job 998862 (bnode098) が 0.31 秒で `Could NOT find gflags` で落ち、
D1439(c) の artifact が取れていない (`output/insights/2026-09-15_t2625-sealed-snapshot-qualification/README.md:63`)。
(2) D1737 は `p3_s4_loop_pegasus.sh` の同じ停止を「job body に供給経路が無いため」と帰属済み。
最小差分は、gflags / glog を **機体固有の絶対 path ではなく version (url + 40 hex pin) で指す
共通調達経路**を 1 本立て、既存の cache / hydrate 機構でそこへ運ぶこと。
完了判定 = hydrate した source から建てた prefix で、**本番と同じ finder (実 CCBench configure)** が
gflags / glog を解決する。

## 確定済みユーザー裁定

- 2026-08-16 /rulings 全件 第 3 回 索引 19 = 択 (b)「versioned な共通調達経路を新設」。
  却下 = (a) 共有 policy の locator 貼り替え、(c) probe ごとの env seam。[T-585] と同じ面。
- 本依頼の追補 = 「本題の調達経路だけ。仮想リスク向けの一般化・互換層の追加は scope 外」。
- D1736 = 名指し外の gate・検査・台帳・一般化は scope 外。

## 段 1 実測 (親)

1. **login node に system の gflags / glog は無い。** 素の `cmake -S external/ccbench` は
   `cmake/Findgflags.cmake:9` → `CMakeLists.txt:33` で `Could NOT find gflags`、rc=1。
   **module mode が走って失敗しており、config mode への fallback は起きない。**
2. **prefix を与えると通る。** `-DCMAKE_PREFIX_PATH=<残骸 prefix>` で
   `Found gflags: …/libgflags.a` / `Found glog: …/libglog.a`、rc=0。機構は確認済み。
3. **user package registry は他 wave の残骸で汚れている。** `~/.cmake/packages/gflags` は 1 件、
   `glog` は 27 件。実在するのは `dev-wave-t756-fn2-trace-v2/emitter-probe2/prefix` など一部で、
   1 件は稼働中の t2625 worktree 内を指す。**最小 cmake project の probe は config mode で緑になるが、
   本番の反証にならない。**
4. **pin 済み source は現存**し HEAD は policy と一致する (`/work/SFC/tanab/github/{gflags,glog}`)。
   今すぐ壊れてはいないが、D200 で一度 home から消失した前歴がある。
5. **既存 3 依存の versioned 経路は gflags / glog を受け付けない。**
   `silo_ladder_rung1.third_party_policy()` は `THIRD_PARTY_NAMES` との exact 一致と
   `external/ccbench/cmake/ThirdParty.cmake` の `CCBENCH_<NAME>_{REPO,TAG}` literal 同期を要求する。
   gflags / glog は FetchContent ではなく `find_package` なので同 list に足すと ContractFailure。
6. **`gflags_source_path` を読む tracked file は 28 本** (job body 14、test 10、他)。
   D200 時点の 10 本から増えている。
7. **login node から github.com の名前解決は通る。** 取得は login、運搬は hydrate という既存形と整合。

## scope

- **入る:** versioned な調達記述 (url + 40 hex pin) の新設、その列挙権威、既存 cache / hydrate 機構の
  拡張、pinned-clean 検証、**実 CCBench configure まで通す生死証拠**、および bytes を変えた場合の
  凍結 pin 閉包の更新。
- **入らない:** 14 本の job body の一括移行 ([T-585] 本体)、CCBench 本体の改変、
  fallback / 互換層、仮想リスク向けの一般化。

## 不変条件

- 規律 2 を緩めない。pinned HEAD 照合・dirty 拒否・fail-closed を弱める変更は採らない。
- 事前検査は本番と同じ finder で行う。最小 cmake project の config mode probe を証拠にしない。
- `external/ccbench/` を改変しない (D1737 が `find_package` の optional 化を却下済み)。
- 凍結 evidence (`silo_ladder_rung1.json` 等) の歴史 binding を書き換えない (D200)。
- policy.json の bytes を変えるなら、`EXPECTED_CURRENT_PEGASUS_POLICY_SHA256` は
  **親が変更前 bytes から独立に算出した値**を与える (D200。実装子が編集後 file から算出すると自己成就 pin)。
- 名指ししていない consumer の受理・拒否挙動を変えない。

## 割れうる前提 (親の provisional 裁定・段 3 の攻撃対象)

- **(P1) D1737 の却下欄と本裁定の向き。** D1737 は「`fetch_third_party.py` の cache へ gflags/glog を
  足して hydrate 経路で運ぶ」を「同じ依存を 2 つの経路で pin することになる」として却下した。
  **親の provisional 裁定 = この却下は「floor 系の policy 経路を残したまま第 2 経路を足す」ことへの
  却下であり、単一の versioned 経路へ寄せる T-548 の裁定を止めない。** 逆に読めるなら段 4 で
  ユーザー再裁定へ返す。
- **(P2) 調達記述の置き場所。** 案 X = `tools/pegasus/policy.json` へ追加 (identity churn と
  golden sha 更新、D115 の先例では 2 node が赤)。案 Y = `tools/pegasus/policies/` 配下の
  task 別 file へ新設し registry へ登録 (policy.json の bytes 不変、ただし
  gflags/glog の正本が 2 箇所に割れる危険)。**親の provisional = 案 X。** 単一正本を優先する。
  段 2 は両案を file:line で比較し、段 3 は「正本が割れないか」「凍結 pin の更新が
  歴史の改竄にならないか」で攻める。
- **(P3) 完了の下限。** 親の provisional = 「経路の新設 + 実 CCBench configure まで通る生死証拠」を
  完了とし、job body 14 本の移行は [T-585] として残す。**consumer ゼロの機構は DW-G04 違反**という
  反論がありうるので、段 2 は「最小 1 本の実 consumer 結線」案も file:line で出す。

## 成果物の形

コード + テスト (実装面あり → 変異 matrix 対象)。記録は spool fragment。
insight = `output/insights/2026-09-16_t548-versioned-dep-procurement/`。

## 並列分割方針

段 2 の plan が所有 path を素集合に割れると判定した場合だけ並列化する。
既定は単一単位 — `policy` 記述・列挙権威 (`silo_ladder_rung1.py`)・`fetch_third_party.py` は
密結合で、素集合に割ると patch 展開が競合する。test は同単位に含める。
