# P2-5: LLM 誘導探索 vs 全探索 — silo フラグ空間での negative result と「自信ある早期停止」の害

**日付:** 2026-06-29
**status:** 完了 (Phase 2 主実験)。還元判断: 不要 (CCBench のバグでなく Izanagi 手法の評価結果)。
**データ:** `output/campaigns/p2-5-summary.json` (per-trial 軌跡)、replay 元 = P2-2 WAL (`output/campaigns/p2-2-silo-*-enumerate-*/runs/wal.jsonl`)。

## 問い (と、なぜ negative result に枠組みを定めたか)

P2-5 当初の問い = 「critic (leading indicators の帰属) で次の genome を選ぶ誘導探索は、ランダム/全探索より少ない評価回数で最適に到達するか」。
だが **silo の有効空間は 8 genome しかなく、実質 BACK_OFF=0 の 1 ビットでほぼ決まる自明な空間**であることを P2-2 WAL の直接復号で確認した:

| workload | winner | 上位の構造 | winner-tied set (floor 3.0% 内 equivalence class) |
|---|---|---|---|
| read-heavy | B0-T-W0 | 上位4=全 BACK_OFF=0 が 2.57% 以内、その下は 77% の崖 | **k=4 (空間の半分)** |
| balanced | B0-L-W0 | 2位 7.08% 下 (BACK_OFF=0 群が上位を独占) | **k=1** |
| write-heavy | B0-L-W0 | **2位 = B1-T-W0 (BACK_OFF=1!) が 11.49% 下** | **k=1** |

この構造から「誘導が速い」を論文の主張にはできない (設計を多エージェント workflow + 敵対的妥当性検証で固めた段階で判明)。理由:
- read-heavy は最適群 k=4 = 空間の半分。ランダムでも期待 1.80 本目で当たり、**到達判定がそもそも情報を持たない** → 主張対象外。
- 完璧なオラクル (初手ランダム制約下) でも到達期待は **2 − k/N**。k=1 で 1.88 本 = ランダム 4.50 から 2.62 本削減が**構造的上限**。これ以上速くなりようがない。
- このまま「誘導が速い」図を出すと、評価器の優位を評価器の定義で論証する循環 (D14・絶対規律6)。

→ **主成果を negative result に定めた** (ユーザー承認、phase2.md 完了条件を改訂)。問いを「誘導は速いか」から
**「誘導の知能 (LLM 帰属) は、機械的勾配 (digest 限界効果のみ) を超えてオラクル天井に近づくか」**に絞り、critic 抜きの貪欲を ablation の 4 系列目に加えて分離した。

## 方法 (replay、新規直列計測ゼロ = 絶対規律4 コスト0)

全 genome の fitness/leading indicators は P2-2 (全探索) で実測・WAL 永続化済み。よって探索戦略の比較は **P2-2 WAL の replay** で完結する (どの順序で genome を引いても記録値を配る)。誘導の非決定 (LLM の揺れ) で genome 選択列は変わるが、選ばれた genome の fitness は固定 lookup なので**探索アルゴリズムの比較に測定ノイズが混入しない**。4 系列:

1. **random** — 8 genome をランダム順。解析分布 P(初到達=j)=C(N−j,k−1)/C(N,k)、期待 (N+1)/(k+1)。
2. **critic 無し貪欲** — LLM を呼ばず `digest.axis_effects` の限界効果勾配だけで貪欲選択 (digest が機械的に提示する勾配そのもの)。
3. **オラクル天井** — 初手ランダム制約下の理論下限 2 − k/N。
4. **誘導 (LLM critic)** — 中立 critic-experiment エージェントの 30 試行 (balanced/write-heavy 各12 + read-heavy 6)。各試行は「評価済み genome の online digest だけ」を見て次手を 1 つ選び、確信したら早期停止。

### リーク制御 (絶対規律6/D14 — 出来レース化を物理的に塞ぐ)

- **online 非開示**: critic に渡す digest は誘導専用 WAL (評価済みだけが育つ) から作る。`online_digest` が『digest の genome 数 ≤ 評価回数』を実行時 assert (`LeakageError`)。未評価の fitness・到達判定・tied set は critic に**一切渡さない** (実探索では「これが最適」と分かる手段は無い。到達は事後に Python が軌跡から測る)。
- **答えの物理削除**: `critic.md` には最適解が literal で埋め込まれていた (「BACK_OFF=0 に固定、contention 域は L 優先」「BACK_OFF=1 は全 workload で latency 律速、再訪不要」)。実験用 `critic-experiment.md` ではこれを**物理削除**し、「結論を先取りせず観測データから帰属せよ」に絞った。
- **fresh context**: 各試行は新規エージェント = 本セッションの会話 (最適解を知っている) を見ない。エージェントには guided.py 以外のファイル (raw WAL) を覗くことを禁じた。
- **初手対称**: 誘導も random も初手は seed 固定ランダム (critic 信号は 2 手目以降)。

帰属が本物だった証拠: 例えば balanced-s2 の critic は B0-T-W0 から BACK_OFF 軸を分離 (B1 で throughput −53%・ipc 1.05→0.38・latency 倍 = spin 希釈と帰属)、次に no_wait 軸を WAL=0 固定で清浄比較し L>T を発見、WAL 軸も統制した。**no_wait の L↔T 符号反転 (B1 では T 有利・B0 では L 有利) を自力で発見**した試行も複数あった。覗かずに leading indicators から機序を組み上げている。

## 結果

floor = between-run noise floor 3.0% (D19)。到達本数 = winner-tied set 初到達位置。**誘導の未到達 (critic が tied を踏まず確信停止) は予算上限 N=8 (最悪) に算入** (早期の誤収束を低コストの成功と誤計上しない、批判3-#9)。

| workload | k | random | オラクル天井 | 貪欲(LLMなし) | **誘導(LLM)** | P(誘導<random) | 誤収束 |
|---|---|---|---|---|---|---|---|
| read-heavy | 4 | 1.80 | 1.50 | 1.76 | 1.67 | 0.357 | 0/6 |
| balanced | 1 | 4.50 | 1.88 | 4.23 | **3.75** | 0.531 | 0/12 |
| write-heavy | 1 | 4.50 | 1.88 | 4.36 | **6.33** | 0.208 | **8/12** |

(P=0.5 が「差なし」。0.5 を有意に超えて初めて「誘導が速い」と言える。)

### 読み

- **read-heavy (k=4)**: 全戦略に余地なし (オラクル天井 1.50 ≈ random 1.80)。到達判定が情報を持たない → 主張対象外。
- **balanced (k=1)**: 誘導 3.75 が random 4.50 / 貪欲 4.23 を**僅かに**上回る (P=0.531、誤収束 0/12)。BACK_OFF=0 支配が clean で限界効果が素直に出るため、critic は 4 手前後で正しく B0-L-W0 に収束する。だが **P=0.531 は 0.5 と区別できず** (n=12)、削減は 0.75 本 = **オラクル天井の余地 2.62 本の約 1/4 しか取れていない**。「有意に速い」とは言えない。
- **write-heavy (k=1)**: 誘導 6.33 が random 4.50 / 貪欲 4.36 を**下回る** (P=0.208)。**12 試行中 8 試行で critic が winner B0-L-W0 を評価せず別 genome に確信停止 (誤収束)**。誤収束先は BACK_OFF=1 genome (B1-T-W1 ×3, B1-L-W0 ×3) と B0-T-W0 ×2。

### write-heavy の失敗機序 (この実験の最重要発見)

write-heavy は唯一 **BACK_OFF=1 が競争力を持つ** workload (B1-T-W0 が実 2 位、winner の −11%)。BACK_OFF=1 は abort 率を大きく下げる (backoff が衝突を間引く) ので、critic が「低 abort = 良い」方向に帰属すると BACK_OFF=1 に引き込まれる。**clean な balanced (BACK_OFF=0 が圧倒的支配) で校正された「自信ある帰属」が、deceptive な write-heavy で誤誘導される。** しかも critic は確信すると**早期停止**するため、winner B0-L-W0 を評価しないまま誤った genome で打ち切る。

対照的に random/貪欲は早期停止しない (tied に当たるか予算を使い切るまで進む) ので**必ず最後には当てる**。つまり:

> **critic の「知能」(自信ある帰属 + 早期停止) こそが、deceptive 構造での失敗の原因。** 無情報なランダムの方がこの罠に落ちない。

これは絶対規律 (過信した最適化圧力が正しさ/妥当性を攻撃する) の鏡像であり、**評価器の自信は signal が deceptive なとき負債になる**ことの定量実証。

## 結論

**silo 8 genome では、LLM 誘導の知能は random / 機械的貪欲を有意に上回らない (balanced は余地の 1/4・有意でない、read-heavy は余地なし)。さらに deceptive 構造 (write-heavy) では誘導はむしろ有害 (誤収束 8/12、random より遅い)。** = Phase 2 主実験の negative result。

- **手法上の含意**: 探索空間が小さく自明だと、(a) 全探索が安価すぎて「速い」の説得力が本質的に弱く、(b) 賢い critic の早期停止が deceptive 帯で誤収束を起こす。**critic の価値を実証するには空間拡大 (cicada 2^6 / oze 2^7) が前提**。これは任意項 (規律5) かつ trace-hook 拡張 (S1) を要するので Phase 3 隣接で判断する。
- **Phase 3 への設計教訓**: critic は確信度を校正し、deceptive 帯では早期停止を抑える (uncertainty を出して探索を続ける) べき。本実験は「自信ある早期停止」の失敗モードを再現可能に切り出した。
- **Phase 2 全体の物語 (P2-4 との対比)**: フラグ空間の探索は自明 (本 negative result) → だから価値は**空間の外の合成**にある (P2-4 backoff ケーススタディ: critic 駆動でフラグ空間外に静的 backoff variant を合成し contention 域で stock 最良を +38%/+11% 上回った)。negative result は「薄い結果」でなく、**合成 (Phase 3) がなぜ要るかを定量的に動機づけるキーストーン**。

## 規律と限界

- **規律4 (スケール)**: 新規直列計測ゼロ。replay で between-run ドリフトの交絡も消えた。
- **規律2/3 は non-load-bearing**: replay は certified 済みの genome を配るので正しさゲートは常に真。本実験は規律4 (測定妥当性) と規律6/D14 (循環回避) のテストであって、規律2/3 のテストではない。誘導が空間外 (livelock (0,0)) を提案したら guided.py が検疫拒否し S4 配線まで止めるトリガを機械化済み (今回は発火せず)。
- **小N (実効 workload n=2)**: k=1 は balanced/write-heavy のみ。「k 依存」を 2 点で一般化しない。P(誘導<random) を 0.5 から有意分離するには K≈50-80 必要だが、実測 P が 0.53 (balanced)/0.21 (write-heavy) で天井/床に張り付くため、**K を増やしても有意化しない (= 効果が天井に埋もれる)** を事前停止規則とした (後追いで K を増やさない、D14 循環回避)。
- **未到達 penalty**: N=8 算入は誘導不利側の保守的計上。penalty 非依存の頑健な統計は **誤収束率そのもの** (write-heavy 8/12 = 67%) で、これがこの結果の headline。
- **C1 (campaign-id drift)**: replay loader は P2-2 dir を名前 prefix で discover (id 再計算は現 pin で食い違う)。WAL 中身は commit 非依存ゆえ数値忠実性は無傷。
- **residual**: 空間拡大なしには「k 依存」は本質的に解消不能 — negative result + 空間拡大の判断材料として正直に出す。fresh エージェントの raw WAL 覗き穴は prompt + fresh context + 帰属の事後監査で抑えたが物理封鎖ではない (headless CLI 不在のため)。

---

## 2026-07-02 追記: 指標再校正 (D29) — p_lt の系統バイアスと確率優越 a への置換

**上の本文の P(誘導<random) 列 (p_lt) には系統バイアスがあることが判明した。** p_lt は tie を
勝ちに数えないため、戦略が random と**完全同分布でも 0.5 を下回る** (null: k=1 で 0.4375、
k=4 で 0.3222)。本文の「(P=0.5 が「差なし」)」という校正宣言は誤りだった。tie を半分数える
確率優越 **a = P(<) + 0.5·P(=)** (同分布で厳密 0.500) に再校正した結果 (方法・感度分析は
`p2-5-summary.json` の `recalibration_2026_07_02`、検算は独立 2 エージェントの敵対検証で全一致):

| workload | 貪欲 a | 誘導 a | 誘導 vs 貪欲 A | 再校正後の読み |
|---|---|---|---|---|
| read-heavy (k=4) | 0.506 | 0.548 | — | 余地なし、主張対象外 (不変)。null p_lt=0.32 なので旧表の 0.357 を 0.5 基準で読むのは特に誤り |
| balanced (k=1) | **0.533** | 0.594 | 0.581 | **貪欲は random より有意に速い** (exact p≈0.005, n=500 — ただし削減 0.27 本は天井の 1 割)。誘導の a=0.594 は有意と主張しない (実体は大外れ回避の分散縮小。exact p≈0.14、Holm 非有意)。誘導 vs 貪欲は有意差なし (p≈0.16) |
| write-heavy (k=1) | 0.517 | 0.271 | **0.230** | **誘導は貪欲より有意に有害** (permutation p<10⁻⁴、打ち切り感度・Holm に頑健)。機序は探索順序でなく自信ある早期停止の負債 (誤収束 8/12。到達した 4 試行のコスト [1,3,4,4] は貪欲と遜色ない)。vs random の a=0.271 は未到達=8 算入依存 (感度幅 0.23–0.39) で単体では掲げない |

**何が変わるか:**
- 「機械的貪欲はゼロしか取れない」(worklog 2026-06-29) は**撤回** — 貪欲は balanced で有意に正。
  これにより「誘導 vs 貪欲」の ablation が negative 結論の主支柱になる。
- 「P が天井/床に張り付くため K を増やしても有意化しない」という事前停止規則の前提は、
  張り付きの約半分 (6.25pt) が指標バイアスだったため弱まる。ただし a でも誘導 vs random の
  exact 検定は非有意 (p≈0.14) であり、停止judgment 自体の結論は変わらない。

**何が変わらないか (総合結論は不変、むしろ強化):**
- 誘導は機械的勾配 (貪欲) で達成できる水準を超えない (A=0.581、有意差なし)。
- deceptive 構造での有害性は貪欲比でも有意 (A=0.230) — 「自信ある早期停止の負債」という
  headline (誤収束 8/12、penalty 非依存) はそのまま。
- 「フラグ探索は自明 → 価値は空間外の合成にある」という Phase 2 の物語・Phase 3 の動機づけ。
