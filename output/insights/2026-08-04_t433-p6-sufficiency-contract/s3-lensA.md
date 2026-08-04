## 所見台帳

### 1. BLOCKER — 「限界効果」を出力値で代用しており、実際の判定効果がゼロでも認定できる

- 対象: [s2-plan.md:70](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/s2-plan.md:70)、[s2-plan.md:84](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/s2-plan.md:84)、[s2-plan.md:126](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/s2-plan.md:126)、[P6 README §3.5:254](/work/1/SFC/tanab/izanagi/output/insights/2026-08-03_t244-p6-contract/README.md:254)
- 構成的実証: handler は `B=hypothesis.extrapolation_set` と fixture の `C_exact` を集合演算し、C-01 で `marginal_keys={k1}` を返す。各負例にも指定 code を返す一方、generalized-cut enforcer は no-op にする。C-12 は禁止集合外候補の既存 exact-cut/verifier 経路だけなので通る。SC-01〜SC-11 の変異も各入力検査を実装すれば全て KILLED にできる。しかし「P6 無効なら k1 が admission を通り、P6 有効なら k1 が generalized cut だけを理由に拒否される」という A/B ケースは一件もない。検査者の実走項目にも禁止集合内候補の判定反転がない。
- 影響: 非空なのは報告上の `marginal_keys` だけで、受理集合への限界効果ゼロの実装を「実装済み」と認定できる。

### 2. BLOCKER — case ID を隠しても、有限ケースの構造暗記で全 calibration を通過できる

- 対象: [s2-plan.md:80](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/s2-plan.md:80)、[s2-plan.md:93](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/s2-plan.md:93)、[s2-plan.md:101](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/s2-plan.md:101)、[s2-plan.md:157](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/s2-plan.md:157)、[P6 README §3.3:197](/work/1/SFC/tanab/izanagi/output/insights/2026-08-03_t244-p6-contract/README.md:197)
- 構成的実証: 入力を `(witness kind, shape-valid, truncated, precommit-order, falsified, B\\C_exact が空か, abort reason)` に射影する表駆動 handler を作れる。cycle normalizer は rotation だけ正しく処理し、reason・key 分割・version 等値関係を捨てる。各 integrity adapter は `kind` と `counter>0` だけから同じ定数 class を返す。未公開 rotation/key-renaming/version-shift はこの射影を変えないので全部通る。SC-03 の rotation 除去変異も殺せるが、残りの意味は空のままである。C-10L/W/P は witness 表現も同値関係も未定義なので、申請者自身がこの定数 adapter に合う constructor を作れる。
- 影響: 固定 corpus の名前でなく形を暗記しただけの実装が、全 adapter の意味的実装として認定される。

### 3. BLOCKER — 変異契約は「一つの生きた飾り」でゲーム化でき、弱化不能条項の削除まで許す

- 対象: [brief.md:68](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/brief.md:68)、[s2-plan.md:66](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/s2-plan.md:66)、[s2-plan.md:117](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/s2-plan.md:117)、[s2-plan.md:131](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/s2-plan.md:131)
- 構成的実証: SC-03 は内部整合、reason、rotation、key/version、class-set、切詰めを一行に束ねるが、対応変異は rotation 除去だけである。他の全 conjunct を恒真にしても行は KILLED になる。同様に一条項一変異では、calibration 専用の `compliance_bits` を各変異が壊すようにすれば、実処理と無関係に全変異を殺せる。さらに排除規則は「反転しない条項を契約から削除」とするため、SC-08 の verifier 条項をうまく変異できなければ実装を拒否するのでなく条項を落とせる。
- 影響: mutation score が意味の証明にならず、最悪時には規律 2 の条項自体を削除する fail-open 契約になる。

### 4. BLOCKER — verifier 必須性は一つの統合 fixture にしか掛からず、別入口で省略できる

- 対象: [s2-plan.md:73](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/s2-plan.md:73)、[s2-plan.md:97](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/s2-plan.md:97)、[s2-plan.md:160](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/s2-plan.md:160)、[P6 README §3.6:299](/work/1/SFC/tanab/izanagi/output/insights/2026-08-03_t244-p6-contract/README.md:299)
- 構成的実証: tested caller では canonical-looking verifier を呼び C-12 を通す一方、direct/programmatic caller では `if p6_certified: accept_without_verify` とできる。C-12 の入力形状だけで呼出しを分岐しても case ID は不要である。契約には候補 query 全入口の閉集合、canonical verifier の identity/hash、全入口での call 証明がない。SC-08 の変異を tested caller にだけ適用すれば KILLED になり、別入口の bypass は残る。D114 が三入口を個別に閉じた先例とも非対称である。[D114:5335](/work/1/SFC/tanab/izanagi/docs/decisions.md:5335)
- 影響: 「P6 認定済み」を verifier 省略条件へ転用する実装が、契約の字面を守って通過できる。

### 5. BLOCKER — V1 推奨 (a) は run identity と allowance の意味が未定義で、(b)/(c) と安全に区別できない

- 対象: [brief.md:39](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/brief.md:39)、[brief.md:65](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/brief.md:65)、[s2-plan.md:174](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/s2-plan.md:174)、[s2-plan.md:184](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/s2-plan.md:184)、[s2-plan.md:210](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/s2-plan.md:210)
- 構成的実証:
  - (a) 表は「非主張 run は allowance を消費しない」とし、逐語案は「その run に allowance を付与しない」とする。前者を採れば全 generation を `NOT_CLAIMED` として消費ゼロにでき、後者を採れば当該 run では (b) と同じく cap が開かない。「revision・origin・運転構成」は run ID ではなく複数 run を含めうるため、同一 tuple 内では standing 免責にも読める。
  - (b) 状態ラベル上だけ失敗に数えず、唯一の操作である cap-lift を禁止すれば、U2 の免責を運用上は失敗と同じにする。逆に「構成」を申請者が細分化できれば、claim 用構成で承認を取り、実運転を非主張構成へ切り替えられる。
  - (c) 一度 calibration facade を認定させた後、全実運転を global `NOT_CLAIMED` にすれば、D138 の限界効果ゼロのまま cap を開けられる。
  現行 gate は per-run allowance でなく単一の `MAX_APPROVED_GENERATIONS` を三入口で検査する構造であり、必要な receipt field は案自身が T-434 へ先送りしている。[p3_autonomous_workload_trial.py:249](/work/1/SFC/tanab/izanagi/orchestrator/campaign/p3_autonomous_workload_trial.py:249)
- 影響: 親の (P2) は最悪ケースで tuple 内 global 免責か、U2 を実質無効にする局所禁止のどちらも許す。

### 6. MAJOR — 「fresh context」は独立検査者の偽装を防がない

- 対象: [s2-plan.md:75](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/s2-plan.md:75)、[s2-plan.md:128](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/s2-plan.md:128)、[s2-plan.md:135](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/s2-plan.md:135)
- 構成的実証: 申請者自身が会話履歴を捨てた新 context を起動し、申請者作成の corpus・constructor・変異表を渡して fresh checkout 上で再走すれば、定義された独立性を逐語的に満たす。検査者が実装・fixture・変異の作成へ関与していないこと、検査者自身が hidden case と変異対象を選んだこと、検査結果と対象 revision の束縛を示す証拠は要求されない。
- 影響: 独立性が「別ウィンドウで自己検査した」という儀式へ退化し、自己申告の別名になる。

### 7. MAJOR — DW-O13 台帳と検査可能度分類が矛盾し、型境界も C-11 で崩れている

- 対象: [s2-plan.md:35](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/s2-plan.md:35)、[s2-plan.md:48](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/s2-plan.md:48)、[s2-plan.md:70](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/s2-plan.md:70)、[s2-plan.md:93](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/s2-plan.md:93)、[s2-plan.md:96](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/s2-plan.md:96)
- 構成的実証: `B` と `C_exact` は handler 署名の入力 field ではなく代数上の中間値で、hypothesis、matrix、`marginal_keys` も未実装なのに SC-05 は現在形で「機械検査できる」とされる。C-10L/W/P は構造化 witness と同値関係が存在しないまま正例 oracle を宣言する。さらに冒頭では `NOT_CLAIMED` と四値結果を別型としたのに、C-11/SC-09 では `P6Derived → NOT_CLAIMED` を一つの判定反転として扱う。状態 classifier と per-run artifact は T-434 所有で、D150 も判定 field がゼロと明記する。[D150:7446](/work/1/SFC/tanab/izanagi/docs/decisions.md:7446)
- 影響: calibration 入力を申請者が後付け定義でき、機械検査可能という分類が自己申告か永久保留の二択になる。

### 8. MINOR — 親の「P6 要素 0 件」は名前検索から意味的不在へ一般化している

- 対象: [brief.md:24](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/brief.md:24)、[D150:7416](/work/1/SFC/tanab/izanagi/docs/decisions.md:7416)
- 構成的実証: 四つの識別子を `orchestrator/`・`tools/` の Python に検索して 0 件でも、別名、inline 実装、別言語、別 path の同等機構は排除できない。D150 自身が path 名・test node 名を実装証拠に数えないとしており、名前不在を意味的不在の十分条件にするのも同型である。現状結論は他の実在台帳から支持されるが、この実測単独からは導けない。
- 影響: 現在の `NOT_IMPLEMENTED` 結論より、親が提示した census の一般化強度だけが過大である。

## 総括

- **NO-GO**
- 件数: **BLOCKER 5 / MAJOR 2 / MINOR 1**
- 最重要所見: **#1** — 非空 `marginal_keys` を返すだけで、実際の候補判定を一度も変えない実装が calibration・全変異・独立再計算を通過できる。