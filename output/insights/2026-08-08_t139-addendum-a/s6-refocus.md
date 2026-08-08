## 対応表

`regressed` は、元の穴を動かしたものの、同じ面に新しい blocker を導入した場合とした。

| # | `s6-fix.md` の申告 | 再判定 | 理由 |
|---|---|---|---|
| A-1 | closed | **partial** | union bound の代数は成立するが、主統計量の `s_k` が未定義で、数値的な「認証」も成立していない |
| A-2 | closed | **partial** | Monte Carlo は除去したが、分布関数の誤差保証・丸め順序・境界処理がなく同じ `J` を保証できない |
| A-3 | closed | **closed** | 問題の単調性補題は削除されている |
| A-4 | escalated R2 | **still-open** | `a12` 自身が core §7 の較正義務を満たさないと明記している |
| A-5 | partial + escalated R3 | **partial** | canonical 台帳を要件化したが、台帳も原子的予約も未実体化 |
| A-6 | escalated R5 | **still-open** | 凍結 core の偽の同値と公表側 guard は未修正 |
| A-7 | closed | **closed** | `∅ → R13` の受理拡大へ正しく訂正済み |
| A-8 | partial + escalated R6 | **partial** | 完全 schema は存在せず、本文自身も schema 本体でないと認める |
| A-9 | closed | **partial** | `addendum-a.md` には追記済みだが、`README.md` に申告した全注意事項は載っていない |
| A-10 | closed | **regressed** | R1 の「erratum ちょうど 1 件」と、R2/R5 の追加 erratum が共存不能 |
| B-1 | closed | **closed** | `fields` の H2/H3 境界 grammar が明記された |
| B-2 | closed | **closed** | 2 operation、対象行、`old_text`、両 SHA-256 は target blob と一致 |
| B-3 | partial + escalated R1 | **partial** | manifest 契約は書かれたが実体がなく、複数 erratum の束縛も未定義 |
| B-4 | closed | **closed** | A-7 と同じ訂正が全関連文書へ反映済み |
| B-5 | closed | **partial** | 初回窓は置かれたが、preflight 内の順序・cap・直後の遷移が未確定 |
| B-6 | closed | **still-open** | 「外部証拠」の生成主体・完全性・認証・receipt field が未定義 |
| B-7 | closed | **closed** | `TERM_at=cap−10`、`KILL_at=cap`、phase 単位が明記された |
| B-8 | closed + escalated R4 | **regressed** | configure argv が probe と不一致で、`CMAKE_CXX_FLAGS` も二重指定 |
| B-9 | partial + escalated R6 | **partial** | raw pointer は追加されたが、完全な nested schema は未発行 |
| B-10 | closed | **regressed** | 生成元は一意になったが、6 build と receipt が 1500 秒 cap に収まる根拠がない |
| B-11 | closed | **closed** | R4(a) 時の 3 文書一括再提出が明記された |

### 所見 1 — `a10` の union bound は代数的には成立するが、`T_k` が本文上未定義

区分: **blocker**

根拠: [addendum-a.md:509](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-addendum-a/addendum-a.md:509)、[同:561](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-addendum-a/addendum-a.md:561)、[core:97](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:97)。

反例または検算:

- 本走 `J` cluster の不偏標本共分散を `\widehat S_J` とし、明示的に  
  `s_k = sqrt((\widehat S_J)_{kk})`  
  と定義すれば、各周辺は iid 正規なので
  \[
  T_k=\frac{\sqrt J\,\hat\mu_k}{s_k}\sim t_{J-1}(\delta_k),\qquad
  \delta_k=\frac{\sqrt J\,\mu_k}{\sqrt{\Sigma_{kk}}}.
  \]
  自由度は `J−1` で正しい。`n_p=8` は pilot の `Θ` 構築だけに使われ、取り違えはない。
- `(N,D)` 領域では
  \[
  \inf N=\bar N-q\sqrt{s_{NN}/J},
  \]
  また `G=D-N` 方向では
  \[
  \inf G=\bar G-q\sqrt{(s_{DD}+s_{NN}-2s_{ND})/J}
        =\bar G-q\sqrt{s_{GG}/J}.
  \]
  `H` は別の片側領域から同じ形になる。したがって、上の `s_k` 定義を置けば  
  `P_W1 ∧ P_W2 = ∩_{k=1}^6 {T_k>q}`  
  と書いてよい。統計的独立性は不要である。
- しかし `s_k` は文書内で一度も定義されていない。`S` の対角成分そのものと読めば統計量は t にならない。

成果物影響: `s_k` の実装解釈によって `p_k(J)`、`L_J`、選択される `J` が変わる。

提案: `s_k²=(\widehat S_J)_{kk}`、不偏分母 `J−1`、`G` の分散写像を `a10` に逐語で追加する。

### 所見 2 — `p_k` の「上向き丸め」は認証された上界になっていない

区分: **blocker**

根拠: [addendum-a.md:529](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-addendum-a/addendum-a.md:529)。

反例または検算: 真値が `0.12345678900005`、相対誤差 `1e-12` 内の近似値が `0.12345678899995` なら、近似値を小数第9位で切り上げても `0.123456789` であり、真値より小さい。「相対誤差 `1e-12`」と通常の数値近似だけでは上向き保証にならない。また、各 `p_k` を丸めてから合計するのか、合計後の `L_J` だけを丸めるのかも固定されていない。

成果物影響: `L_J` が真の下界を上回る、または `L_J=0.80` 近傍で実装ごとに `J` が分岐しうる。

提案: CDF の認証区間 `[p_k^L,p_k^U]` を求め、`1−Σp_k^U` の下側端だけを使う。丸め境界または `0.80` を誤差区間が跨ぐ場合は fail-closed とし、reference vectors も固定する。

### 所見 3 — `Θ` の被覆式は正しいが、`d⁻` の等式は gate 通過枝に限る

区分: **確認済み。ただし明確化必須、単独 blocker ではない**

根拠: [addendum-a.md:478](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-addendum-a/addendum-a.md:478)、[同:492](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-addendum-a/addendum-a.md:492)。

反例または検算:

- Hotelling の `M` は 0.975 被覆であり、
  \[
  \mu_k^-=\bar Y_k-\sqrt{c_M(S_p)_{kk}/n_p}
  \]
  は正しい支持関数解である。
- 正規周辺について `ν(S_p)_{kk}/Σ_{kk}∼χ²_ν` は正しく、各失敗確率を `0.025/6` とすれば `V` は Bonferroni で 0.975 以上、`M∩V` は依存していても 0.95 以上である。
- `q` の `α_k=0.025` は本走の型 I 誤り、`Θ` の 95% は pilot の power planning uncertainty であり、別の確率層である。式上は混線していない。
- `μ_k^-≥0` の枝では
  \[
  \inf_\Theta\min_k\frac{\mu_k}{\sqrt{\Sigma_{kk}}}
  =\min_k\frac{\mu_k^-}{\sqrt{\Sigma^+_{kk}}}=d^-.
  \]
  しかし `μ_k^-<0` なら、`V` は分散の下限を持たないため真の infimum は `−∞` になりうる。したがって無条件の等式ではない。ただしその枝は `d^-<1` で必ず終了するため、現 gate の判定結果は変わらない。

成果物影響: 現行 gate の受理集合は変わらないが、proof chain が `d⁻` を無条件の infimum と記載すると偽になる。

提案: 「`d⁻≥1` の候補枝では上記 infimum と一致する」と条件付きで記す。planning 用 95% を `β_plan`、型 I 用を `α_k` と別記号にする。

### 所見 4 — core §7 の較正義務は明示的に未達

区分: **blocker**

根拠: [core:219](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:219)、[addendum-a.md:622](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-addendum-a/addendum-a.md:622)。

反例または検算: `a12` は自ら「core §7 の義務を満たしたと扱ってはならない」「本 wave は解消していない」と記している。J=1 residual は未観測の cluster 効果を拘束できず、元レビューの weak-null 反例も残る。

成果物影響: stress check を較正完了として扱うと、未制御の型 I 誤りで certified pass が可能になる。

提案: R2 について、独立 cluster データによる較正、新 core、または義務を弱める明示 erratum のいずれかをユーザー裁定するまで凍結しない。

### 所見 5 — alpha ordinal は規範化されたが、権威はまだ存在しない

区分: **blocker**

根拠: [addendum-a.md:712](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-addendum-a/addendum-a.md:712)、[同:725](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-addendum-a/addendum-a.md:725)。

反例または検算: 本文は canonical 台帳での原子的予約を要求するが、その台帳は未実装である。現状では複数 study が同じ `F,k=1` を自己申告できるという元反例を機械的に拒否できない。

成果物影響: primary 系列の累積誤り率が 0.05 を超えうる。

提案: R3(a) を裁定し、caller 非選択の台帳 path、atomic create、重複検査、失敗時の番号保持まで実装・受入するまで pilot を禁止する。

### 所見 6 — R1 の singleton erratum と R2/R5 の追加 erratum は共存不能

区分: **blocker**

根拠: [erratum-core-s15.md:138](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-addendum-a/erratum-core-s15.md:138)、[package.md:107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-addendum-a/package.md:107)、[同:233](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-addendum-a/package.md:233)。

反例または検算: R1 の resolver は target core に一致する erratum 件数が `==1` でなければ失敗する。一方、推奨 R2(a) は同じ core に 1-operation の「第2 erratum」を追加する。別 blobなら一致件数が2となり失敗し、現在の blobへ追加すれば「operations はちょうど2」「§15以外を supersede しない」に違反する。R5(b) も同じ衝突を増やす。

成果物影響: 推奨どおり R1(a)+R2(a) を裁定しても preregistration resolver が必ず失敗する。

提案: manifest を `(target_core, erratum_id)` の承認済み exact set として束縛し、全 erratum の順序・非重複 locator・合成後 digest を検査するか、新 coreへ統合する。現パッケージのまま R1/R2 を裁定しない。

### 所見 7 — 初回観測窓は preflight cap と実行遷移に閉じていない

区分: **blocker**

根拠: [addendum-a.md:70](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-addendum-a/addendum-a.md:70)、[同:99](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-addendum-a/addendum-a.md:99)、[同:143](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-addendum-a/addendum-a.md:143)。

反例または検算: preflight cap は180秒、TERMは170秒で送られる。観測を「実際の phase の末尾10秒」とするなら、観測を170秒までに終えるため他の preflight 作業を160秒までに終える必要があるが、その順序・sub-capがない。「cap の末尾10秒」と読めば termination grace と重なる。また観測終了から marker 作成・最初の exec までの最大間隔も定義されず、別作業や任意待機を挟める。

成果物影響: 同じ counter でも、観測時刻と最初の run の間隔により cluster の適格性が分岐する。

提案: `他の preflight 完了 → 10秒観測 → 判定 → marker作成 → Δ_max以内にexec` を逐語で固定し、各 deadlineを配分する。

### 所見 8 — `a04` の「外部証拠」は trust root になっていない

区分: **blocker**

根拠: [addendum-a.md:183](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-addendum-a/addendum-a.md:183)、[同:186](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-addendum-a/addendum-a.md:186)、[record-items.md:161](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-addendum-a/record-items.md:161)。

反例または検算: `job stdout/stderr` は append-only に保存されても内容の生成者は job、すなわち producer であり、偽の「process未起動」を出力できる。append-only は改竄防止であって、内容の真実性・全 exec の完全捕捉を保証しない。さらに `record-items.md` には外部証拠の writer identity、pointer、認証値、sequence が存在しない。

成果物影響: 不利な開始後 attempt を開始前 failure に偽装し、予備で置換できる経路が残る。

提案: producer 権限外の exec broker／collectorを生成主体とし、全 process launch の完全な sequence、署名または scheduler 側 digest、receipt pointerを必須化する。

### 所見 9 — `a08` の最終 configure argv は内部矛盾し、probe とも一致しない

区分: **blocker**

根拠: [addendum-a.md:342](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-addendum-a/addendum-a.md:342)、[同:345](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-addendum-a/addendum-a.md:345)、[probe:394](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/tools/pegasus/probes/t139_positive_control_probe.sh:394)、[同:420](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/tools/pegasus/probes/t139_positive_control_probe.sh:420)。

反例または検算:

- template 自体の末尾に `-DCMAKE_CXX_FLAGS=...` があるのに、結合規則でも同じ token を再度追加する。
- probe は `COMMON` 内の3番目に `-DCCBENCH_TRACE=0` を置き、`extra` は `ADD_ANALYSIS`、`CXX_FLAGS` の順である。
- 修正文は template 全体の後ろへ `TRACE, ADD_ANALYSIS, CXX_FLAGS` を置くため、実 probe の argv でもなく、既存 template + extra でもない。
- compiler bytes は依然として「最初の build が自己基準」であり、R4(a) を採らない枝では事前期待値がない。

成果物影響: 異なる configure argv・compiler・binary が同じ arm identity として受理されうる。

提案: 6 build それぞれの exact argv 配列を重複なしで凍結し、probe から意図的に変える tokenは差分として明記する。compiler期待値は凍結前 probeで pinする。

### 所見 10 — 唯一の生成元へ6 buildを集約したが、1500秒 capが閉じない

区分: **blocker**

根拠: [addendum-a.md:84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-addendum-a/addendum-a.md:84)、[probe:416](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/tools/pegasus/probes/t139_positive_control_probe.sh:416)。

反例または検算: probe 実装の command cap は各 buildにつき configure 60秒 + build 180秒であり、6本で `6×240=1440` 秒。phase TERMは1500秒ではなく1490秒に送るため、compile manifest取得・cache照合・`nm`・hash・receipt 6組に残るのは最大50秒である。実 elapsed 証拠はなく、収まる保証はない。

成果物影響: verification allocation が時間切れで `design_not_feasible` となり、唯一の性能 binary生成経路も失われる。

提案: 実測前に各作業のsub-capを固定し、総和を1490秒以下にするか、build phase capを増やして全phase合計を再計算する。

### 所見 11 — R6へ送った schema 要件自体にも記録不能な失敗経路がある

区分: **blocker**

根拠: [record-items.md:160](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-addendum-a/record-items.md:160)、[同:173](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-addendum-a/record-items.md:173)。

反例または検算:

- 観測は `actual_runs[]` にしか置けないが、観測不成立なら当該 run は実行されず `actual_runs[]` に要素がない。
- schema 要件は counterを8整数とする一方、`a03` は8列未満を zero-fillせず失敗として保存する。8列未満の rawを表現できない。
- `a04` の trusted external evidence用 fieldもない。
- ファイル名・package・READMEはなお「closed schema」と呼ぶが、§3.1は完全 schemaでないと明記する。

成果物影響: 正当な pre-run failureをreceiptへ保存できず、attemptの脱落・捏造・validator分岐を招く。

提案: R6の完全 schema前に、attempt-level `environment_observations[]`、可変長raw line pointer、外部証拠objectを要件へ追加し、「closed schema」の呼称をschema本体発行まで外す。

### 所見 12 — erratum の2行は target core と逐語一致する

区分: **確認済み（blocker なし）**

根拠: [erratum-core-s15.md:59](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-addendum-a/erratum-core-s15.md:59)、[core:404](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:404)、[core:424](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:424)。

反例または検算: target commit `88d68f9…` の LF込み行hashは、404行が `6e87b981…681e`、424行が `b5e2c7b2…b7d1` で、erratum記載値と一致した。`old_text` も逐語一致し、差分は `a12→a13` のみである。

成果物影響: B-2の対象行同定には新しい穴を認めない。

提案: 変更不要。ただし所見6の複数erratum合成問題は別途修正する。

### 所見 13 — READMEと対応表が修正後の限界を過大申告する

区分: **major**

根拠: [s6-fix.md:26](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-addendum-a/s6-fix.md:26)、[README.md:23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-addendum-a/README.md:23)、[同:66](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-a/output/insights/2026-08-08_t139-addendum-a/README.md:66)。

反例または検算: `s6-fix.md` は README に `L_J` の保守性、`a12` の `1−δ_MC`、compiler bytes未pinも追加したとするが、README末尾にあるのは主に正規model条件だけである。またREADMEは `a10` を「認証された下界」「再現性問題も解消」と断言する一方、所見1・2の未閉鎖条件を示さない。R5の公表guardもまだ提案だけである。

成果物影響: ユーザー裁定と材料レポートが、実際より強い保証を前提にしうる。

提案: READMEとpackageの断言を対応表の再判定へ合わせ、未解決事項を明記する。

## 総括

- blocker: **10件**。重複している A-8/B-9 は1根として数えた。
- 判定: **NO-GO**。追補A・erratum・schema案の凍結、承認fold、pilot投入へ進めない。
- ユーザー裁定が要る点:

  1. **R1/R2/R5のerratum合成方式**。現選択肢は相互矛盾するため、現在のままでは裁定不能。exact set型manifestか新coreかを先に再提示する必要がある。
  2. **R2**: core §7をstress checkへ弱めるか、独立clusterデータで較正するか、新coreにするか。
  3. **R3**: caller非選択のcanonical alpha台帳と原子的予約を採るか。
  4. **R4**: 凍結前に `gen_S` probeを行い、`a03`閾値・TRACE build・compiler identityを確定するか。推奨はprobe先行。
  5. **R5**: 公表側の正分母guardを必須化するか。少なくとも現状維持は不可。
  6. **R6**: 完全な機械可読schemaをpilot前に発行しdigest束縛するか。

`a10` の記号・数値認証、`a03/a04/a08`、1500秒capはユーザー裁定以前の本文must-fixである。テスト・build・simulationは実行しておらず、緑は主張しない。