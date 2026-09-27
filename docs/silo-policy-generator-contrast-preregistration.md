# silo-function-policy 軸の生成器対照 — LLM (C++ 形・IR 形) と非 LLM (random・進化) を同じ評価数で比べる事前登録 (草稿、未発効)

本書は、関数単位の合成空間 `silo-function-policy` (D2214) で、LLM が書く方策と非 LLM の探索が見つける方策を、
**同じ評価数の予算**で比べる対照の事前登録である。B-5 v2 (backoff の値 1 個での同じ対照) は発効せず見送られ、
「なぜ LLM か」の対照はこの軸で取り直すと決まった (D2259)。起草の記録と見積りの計算は
`output/insights/2026-09-27/t2867-silo-policy-contrast-draft/README.md` (以下「起草 insight」) に置く。

**本書は草稿であり、発効していない。本書の存在は、実装・試走・本走・計算投入のどれの認可でもない。**
発効は、§10 の欠ける部品が実在し、§12 の発効束を埋め、図 1 枚あたりの node 時間と LLM の時間をユーザーへ示して
確認を得た後 (D2212 項 4) の、日付付きの決定 (D 番号) による。

## 0. 版と効力

- 本書は草稿 (v1 の起草版) である。cohort 名は `silo-policy-contrast-v1`、登録版の文字列は `silo-policy-generator-contrast-v1`。
- **起草版の間 (発効の決定の前):** 規則は固定されない。規模の択一 (§11.3) をユーザーが選ぶので、発効の前に本書を同じ path で
  改めてよい。改めたときは §15 に日付と理由を追記する。どの系列の生成・測定より前でなければならない。
- **発効の後:** 発効の決定に本書の raw bytes の SHA-256 を写す。以後は既存本文の bytes を書き換えず、訂正は末尾の
  `## N. Erratum` への追記だけとする。結果を見た後の規則の変更は、向きを問わず事後改訂として別に報告する。
  本書自身の hash や本書を含む commit の hash を本文へ書かない (自己参照の禁止、B-5 v1 §0 と同じ)。
- 本書には解析器の pin も機械 gate も無い。凍結は文書上の契約である。

### 0.1 上位の決定と継承元

| 上位 | 本書が従う内容 |
|---|---|
| D2214 と設計 insight (`output/insights/2026-09-21/silo-function-synthesis-space/README.md`、以下「設計」) | 空間・受理契約 policy-C++ v1・骨格・型付き有限 IR。最小の arm は 非 LLM×IR・LLM×IR・LLM×C++。比較 A (同じ IR 上の探索法) と比較 B (LLM×C++ による空間拡張) を分ける (設計 §5) |
| D2256 | 段階 E の兄弟 driver `orchestrator/campaign/p3_s4_loop_policy.py`、検査の順、coder 入力の firewall、LLM 候補への auditor |
| D2220 と比較基盤設計 (`output/insights/2026-09-22/t2849-comparison-harness-design/README.md`、以下「比較基盤」) | 4 契約 (候補 identity・評価の要求・結果の分類・費用の計上)、情報構成 R0、K0 の LLM、共通の初期点、anomaly の波及と endpoint、S3 を足す条件 (比較基盤 §10) |
| B-5 v1 (`docs/b5-generator-contrast-preregistration.md`、発効時の版) | A / B の分離、機械故障の retry、session の契約と品質欠測、endpoint の再計測と fallback、系列単位の対検定と判定順 |
| D2258 (B-5 v2 の実行契約) | 1 評価 1 job、利用上限 (429) の保留、critic への入力の要請。本書が変える点は §5.6 に書く |
| D2249 追加項 | 時間帯の block を入れない。同時刻対照と系列の対づけは残す |

B-5 v2 は発効していないので、本書は v2 を差分登録の土台にしない。継承する規則は本書の本文に書き直した。本書が書かない事項を
B-5 から暗黙に持ち込まない。

## 1. 主張の形と、主張しないこと

### 1.1 主張しうること

> Silo の関数方策の空間 (D2214) で、write-heavy の較正動作点・固定した予算 (評価数の上限 B = 10、原提案の上限 A = 30、共通の初期点 2 個) の下、
> LLM の構成 X (C++ 形または IR 形) の探索系列が選んだ endpoint の score は、非 LLM の探索 (random と進化の両方) のそれに対し、
> 登録した独立性の仮定の下で [条件付き優越 / 比較 floor 内の同等 / 判定不能] だった。

- **族 A (比較 A):** 同じ IR 上の探索法の比較。LLM×IR 対 random×IR、LLM×IR 対 進化×IR の 2 比較。
- **族 B (比較 B):** 空間拡張を含む比較。LLM×C++ 対 random×IR、LLM×C++ 対 進化×IR の 2 比較。
  表現 (policy-C++ v1 と IR) と探索法を合わせた差であり、純粋な探索法の優劣とは言わない (設計 §5)。
- LLM 構成 X の条件付き優越は、その族の 2 比較の両方が §7.3 の条件を満たすときだけ述べる。片方への勝利だけでは述べない。
- B は共通の**上限**である。A を使い切って B が 10 に届かない系列は残る (§3)。結論には arm ごとの実消費 B の分布を添え、
  「同じ評価数を使った」とは書かない。
- LLM×C++ 対 LLM×IR は記述だけで、検定しない (比較基盤 §10「LLM×C++ は比較 B で 5 手法の族に入れない」)。
- 比べるのは**構成** (空間・支持集合・情報構成 R0・初期点・予算・役割の並びを含む) であって、LLM 単体・critic・auditor の因果効果ではない (比較基盤 §1.3)。

### 1.2 主張しないこと

- LLM の必要性 (「LLM でなければ到達できない」)。非 LLM 生成器一般 (BO・他の進化方式・大きい予算) に対する優越。
- 他の workload (balanced・read-heavy・TPC-C)、他の protocol、他の環境での成立。本書は write-heavy だけを測る。
- 経過時間・費用を揃えた比較。どの arm も B = 10 を上限として止まり (A の枯渇で B 未達もありうる)、LLM は評価の間に長い待ちを持つ (§11)。
- certified を全実行の正しさの証明と読むこと。certified は観測した有限の trace の判定で、verify と perf で同じ分岐を踏んだとは
  言えない (設計 §3.1)。「LLM が壊した CC 論理を verifier が捕らえた」ことも主張しない (D2214 項 2)。
- 公平性 (worker 間の偏り)。機械的な観測点は無い (設計 §3.4)。
- K0 を「事前学習知識なし」と読むこと。K0 は外部の実験知識の射影を入れないという意味である。
- 本書の結果を B-5・T-2850 の試走・偵察 (段階 D・小比較・再測) の標本と混ぜること (§8)。

## 2. 空間・候補・支持集合

- **編集面:** `cc/silo/transaction.cc` の単一 EVOLVE-BLOCK (D2214 項 3)。LLM が書くのは 3 関数 (abort 後の待機量・lock 競合時の
  retry / abort・成功 commit 時の状態更新) と補助関数・状態型だけ。validation と lock の仕組みは開かない。
- **受理契約:** policy-C++ v1 (D2214 項 4)。IR 形の候補は `parse_policy_ir` → `render_policy` の後の本文に同じ検査を掛ける (D2256 項 2)。
- **骨格の上限:** abort 後 1000 µs、lock 1 回 50 µs、tuple ごと 32 周回 (D2214 項 6)。全 arm に共通の試走設計値で、最適値ではない。
- **候補 identity:** genome flags + 骨格 / PIN + 材料化した全 source の source_digest (比較基盤 §2.2、設計 §5)。
- **支持集合 (比較基盤 §10 の択一を、結果を見る前にここで選ぶ):**
  - LLM×C++: policy-C++ v1 の受理集合。
  - LLM×IR・random×IR・進化×IR: 型付き有限 IR (`orchestrator/campaign/silo_policy_ir.py` の `validate_ir` が受ける木。深さ ≤ 4、
    node ≤ 64、状態 ≤ 4 field) の全体を名目の支持集合とする。
  - ただし random と進化の生成器は定数を §4.4 の有限集合から引くので、実効の支持集合は IR 全体より狭い。族 A は
    「定数の分布を含む構成の比較」と明記する (比較基盤 §10 の後者の択)。

## 3. 予算・停止・計上

各 arm の各系列の予算を次に固定する。

| 量 | 値 | 意味 |
|---|---:|---|
| B | 10 | pipeline へ投入した評価の数。anomaly で reject された候補、投入後の候補起因の失敗も 1 消費する |
| A | 30 | 原提案 (候補提出の機会) の上限。空出力・不正出力・検査の拒否を含む |
| k | 2 | 共通の初期点の数 (§4.6)。B の外 |
| 系列開始 stock | 1 session | B の外 |
| N_eval | 5 | endpoint の再計測の session 数 |

- **A だけを消費するもの:** 空出力、schema 不合格、driver の検査 (共有検疫・型付き構文検査・単独 TU compile) の拒否、
  auditor の veto・digest 不一致 (LLM 由来の候補だけに掛かる。比較基盤 §5.3 の開示)。所要は物理費用に入れる。
- **B を消費するもの:** 上の検査を通って pipeline (build・legacy verify・性能構成 verify・bench) へ投入した時点で 1。
  build 失敗・anomaly・投入後の時間切れも B を返さない (B-5 v1 §3.1)。成功して certified になった候補だけを数える運用は禁止する。
- **重複:** 同じ系列で既に評価した identity を再び提出した場合も A と B を消費し、fresh に測る (比較基盤 §5.2)。一意な identity の数と
  重複率を別に報告する。
- **停止:** B 完走または A 到達まで進める。性能を理由とする早期停止はしない。A 到達時に B 未達でも系列を差し替えない (B-5 v1 §3.2)。
- **driver の停止規則は使わない。** 段階 E の driver は反復 10 回または 3600 秒で止め、preview の拒否も反復を 1 消費する
  (`p3_s4_loop.MAX_ITER`・`MAX_WALLTIME_S`、D2256 項 3・項 6)。本書の系列は複数の job にまたがり A ≤ 30 の拒否を含むので、
  系列の予算は対照の台帳が A と B で持つ。driver の停止判定が系列を止めない実行経路を §10 の前提とする。
- **機械故障:** 同じ候補・同じ入力・同じ論理 slot で追加 2 回まで retry。上限を超えたら endpoint の有無を問わずその時点で系列を終え、
  score を欠測とする (B-5 v1 §3.3、比較基盤 §4.6 の 2)。walltime を超えた打切りは候補起因で B を消費する。

## 4. 生成器の操作的定義

### 4.1 LLM の 2 arm に共通

- **構成:** K0 (外部の実験知識の射影なし)・R0 (空間外の参照値を渡さない)・planner なし (D2214 項 8)。役割は coder・auditor・critic。
  - coder: C++ 形は `coder-v4-autonomous-policy`、IR 形は `coder-v4-autonomous-policy-ir` (D2256 項 7 でユーザーが差分を承認済み)。
  - auditor: LLM 由来の全候補に掛ける (違反型 1〜26、deny-only veto と digest 照合、D2256 項 2・項 5)。
  - critic: 原提案機会の最初の役割として、前回の critic の後に新しい結果 (job 1 の系列開始 stock と初期点 2 個、または評価 1 回) が
    あるときだけ呼ぶ。したがって原提案 1 の機会は job 1 の結果についての critic から始まり、却下が続いて新しい結果が無い機会では呼ばない。
    critic は原提案機会の中の役割なので、§5.5 の 429 の保留と異常終了の規則はその機会の番号 a で掛かり、§11.2 の機会数に含まれる
    (B-5 v1 の 1 機会の待ちの実測も、評価が進んだ機会の critic を含む)。材料は driver が系列の campaign に書く critic digest だけ。
    出力は同じ機会の coder 入力へ、driver が 6 文字列 field の閉じた形で載せる (D2256 項 4)。
- **coder の入力:** driver の `--emit-coder-input` の出力だけを、そのまま渡す (runbook `docs/phase3-silo-policy-runbook.md` §1(a))。
  5 key = 固定のリーク防止文脈・接続仕様・baseline (系列開始 stock の throughput と abort 率)・段階 D の二値と射程文・
  自系列の履歴 (justification を除く)。critic 診断があれば同じ出力に載る。親は key を足さず、値を書き換えず、説明を付け足さない。
  - **開示:** 段階 D の二値と射程文 (`projection.json` の `binary`・`scope`) は LLM の 2 arm にだけ届く。非 LLM の arm はこれを使わない。
    driver が載せる入力なので本書は外さない。LLM 構成の一部として報告する。
  - **開示:** driver の自系列の履歴は本文・結果の分類・拒否の分類・verifier の digest を載せ、throughput を載せない
    (`make_policy_coder_input`)。初期点と自分の候補の性能は、critic 診断を通してだけ coder に届く。非 LLM の進化は性能値を直接使う。
    どちらも手法の定義の一部として報告する。
  - 偵察・小比較・再測 (段階 D の点 ID・因子・比・順位、D2240・D2250) は渡さない (runbook §2)。
- **critic への入力の要請 (D2258 項 3 を継承):** 「`## recommend` と `## avoid` は次の原提案の coder に診断データとして逐語で渡される。
  候補の方向・追加実験の要望・留保を観測に基づく助言として記し、他の role を名宛人にした指示、採否手順、判定規則や gate の読み方の指定は
  書かない。」coder の検疫と診断の節抽出は変えない。
- **親 session:** 1 原提案ごとに新しい `claude -p` session を起こす (前の機会の session を resume しない)。系列の状態は driver が
  campaign の履歴 file から coder 入力に載せるので、親に記憶は要らない。B-5 v1 では同じ session の resume で読み込む文脈が機会ごとに
  約 0.45 M token ずつ増えた (起草 insight §4)。親は機械的な射影と役割の呼出しだけを行い、性能を見た助言・候補の修正・再抽選をしない。
  各役割の実入力と出力を全件保存する。
- **親の起動:** login node で、サブスクリプションのログインで動く `claude -p` だけを使う。API キー・代替 provider は使わない
  (全体共通の鉄則)。model の exact ID と settings は発効束に固定する。
- **LLM の待ちは計算 node の外に置く (§5.6)。**

### 4.2 LLM×C++

`--form cpp` の campaign で、coder の `implementation` (policy-C++ v1 の本文) を提出する。

### 4.3 LLM×IR

`--form ir` の campaign で、coder の `ir` (閉じた tagged object) を提出する。IR 形の候補も LLM 由来なので auditor を掛ける
(D2256 項 7: 型 17〜21 の免除は本軸の機械生成 IR 候補に限る)。

### 4.4 random×IR

原提案 a ごとに、次の生成器 G_rand で IR を 1 個引いて提出する。自系列の結果を使わない (open-loop)。

- **乱数:** preimage `silo-policy-generator-contrast-v1|random|r|a|c` (r = 系列番号、a = 原提案番号、c = 引き直しの counter、0 始まり) の
  SHA-256 から決定的に作る。v1 の preimage と値の列は発効前に誰も見ない。
- **状態:** field 数 m を {0, 1, 2, 3, 4} から一様に引く。各 field の型を {u32, u64, bool} から一様に、初期値を下の定数分布から引く。
- **式:** 各 hook の出力 (abort の待機量 u32、lock の action と待機量 u32) と、各 hook の `next_state` を型付きの grow 法で引く。
  `next_state` は hook ごとに確率 1/2 で省略 (全 field 保持)、残りは field ごとに式を引く。
  - 深さ d < 4 の node は確率 1/2 で葉、残りは要求型を返せる演算子 (比較・条件式・min・max・飽和加算・飽和減算・有界 shift) から一様。
    深さ 4 は葉。
  - 葉は要求型を返せるもの (定数、`Reason` は abort hook の中だけ、`Attempt` は lock hook の中だけ、同じ型の field の参照) から一様。
- **定数分布:** u32 / u64 の整数は 0 と、B-5 の log-uniform 重み (`b5_generator_contrast.integer_log_weights`、1..1000) の混合
  (0 を確率 1/8)。shift 量は型の幅未満から一様。bool は一様。abort 要因は 8 値から一様。action は {retry, abort} から一様。
- **引き直し:** node 数が 64 を超えた、または `validate_ir` が拒否した木は c を 1 進めて引き直し、A を消費しない。
  引き直しは 1 原提案あたり 1000 回までとし、超えたら空出力として A を 1 消費する (起きないはずの値として記録する)。
- **検査:** 描画した本文には LLM と同じ driver の検査 (共有検疫・型付き構文検査・単独 TU compile) を掛け、拒否は A を消費する。
  auditor は掛けない (D2214 項 8)。
- 上の確率・重みは設計の案の値で、較正していない。発効の後に性能を理由に変えない。

### 4.5 進化×IR

型付き GP (Montana 1995) の subtree 変異の最小形 (1+1) の再実装と名乗る (比較基盤 §6.3・§6.4)。交叉は使わない。

- **親:** 自系列の certified・品質正常の点 (初期点を含む) のうち、探索時の session median throughput が最大の点。同値は slot の早い方。
  親の値は 1 session の値で、測り直さない (雑音に弱いことは定義の一部として開示する)。
- **子 (原提案 a ごと):** preimage `silo-policy-generator-contrast-v1|evo|r|a|c` の SHA-256 から決定的に、次のどちらかを行う。
  - 確率 4/5 (field が 4 個のときは常に): 親の全 site (各 hook の出力と `next_state` の式の全 node、field の初期値) から 1 個を一様に選び、
    同じ型の部分木を G_rand の式の規則 (§4.4、残りの深さの範囲) で引いて置き換える。省略された `next_state` は、各 field の自己参照を
    並べた形に展開してから site を数える。
  - 確率 1/5: field を 1 個足し (型・初期値は G_rand の規則)、続けて上の置き換えを 1 回行う。field を足すとき、`next_state` が明示されている
    hook にはその末尾に新 field の自己参照 (値を保つ) を足し、省略されている hook は省略のまま (全 field 保持) とする。
- **引き直し:** 子の本文が親の本文と同じ、node 数が 64 超、`validate_ir` が拒否した場合は c を進めて引き直し、A を消費しない
  (上限 1000 回、超えたら空出力)。親以外の既評価点と同じ子は引き直さず提出する (重複は A・B を消費、§3)。
- **親の更新:** 子が certified・品質正常で、探索時の値が親より真に大きければ親を置き換える。同値・失敗なら親を保つ。
- **親が無いとき** (初期点が 2 つとも不成立で、探索でも certified が無い): G_rand で 1 個引いて提出する (preimage は `…|evo-fallback|r|a|c`)。
- 局所探索なので「親の近傍を動く探索」として報告し、全域探索とは呼ばない。検査と auditor の扱いは random と同じ。

### 4.6 共通の初期点 (k = 2)

- 新骨格の中の静的待機 5 µs と 10 µs の 2 方策 (abort 後はどの要因でも一定の待機、lock 競合では待機 0 で即 abort、状態なし)。
  IR で書き、描画した本文を各 arm の campaign の形 (C++ 形では描画後の本文、IR 形では IR) で評価する。設計 §5 の新骨格内 seed で、
  段階 D の固定 16 点の `0000`・`0001` と同じ方策である (§8)。
- 各系列の job 1 で fresh に測り (§5.6)、最初の原提案の前に全 arm の自系列の履歴に入る。系列間で共有しない。順序は 5 µs → 10 µs。
- endpoint の候補に含める。報告では endpoint が初期点か探索点か、探索点の最良が初期点の最良を超えたかを系列ごとに数える (比較基盤 §4.5)。
- 初期点が不成立 (anomaly・失敗・品質欠測) でも差し替えない。

## 5. 共通の評価経路

### 5.1 経路と正しさ (規律 2)

- 全 arm の全候補・初期点・endpoint の再計測は、同じ driver の同じ gate と pipeline を通る: 検査 → 書込 → digest 再照合 →
  trace-enabled build → legacy verify 1 本 → 性能構成 verify 5 本 → trace-disabled build → bench (D2256 項 2)。
- **anomaly が 1 件でもあればその候補を即 reject する。** 性能値を取らない。5 本すべてが通るまで bench へ進まない。
  性能値は trace-disabled build の値だけを使う (規律 1)。
- 性能構成の trace 5 本は直列・専有で取得し、取得済みの 5 本を同時に検査する (D2251 の `--verify-performance-concurrent`)。
  検査する本数・verifier・判定規則・bench 前の関門は変えない。失うのは 1 本目の anomaly で残りを検査しない早期打ち切りだけで、
  費用の差である。同時検査の後の初回静定待ちの上限は 120 s (D2251 項 4、write-heavy の本番順序の実測は 67 s・77 s)。
- 機械生成の候補を LLM が生成したものと偽って記録しない。

### 5.2 動作点

write-heavy の較正動作点だけ: records 1,000,000・threads 48・extime 3 秒・reps 5、rratio 5・skew 0.9・rmw なし・操作数 10
(`p3_s4_loop.calibrated_perf("write-heavy")`、driver の `default_perf()`)。性能構成 verify と bench は numactl interleave。

### 5.3 session

1 session = bench 1 回 (5 rep、rep 内の変動が閾値を超えれば静定して測り直し、最大 3 round)。3 round で不安定なら品質欠測
(B も A も返さず、fallback で埋めない)。1 session の値は採用 round の 5 rep の median throughput (B-5 v1 §5.3)。

### 5.4 stock と参照

- 候補と初期点の genome は driver の既定 (`BACK_OFF=1`・`NO_WAIT_LOCKING_IN_VALIDATION=1`・`NO_WAIT_OF_TICTOC=0`・`WAL=0`、
  軸 macro `SILO_POLICY_VARIANT=1`) で、方策の本文だけが違う。
- **stock** = 同じ 4 flag で軸 OFF (`SILO_POLICY_VARIANT` 既定 0、固定 backoff なし) = Cicada 型の適応 backoff。
  **無 backoff (`BACK_OFF=0`) ではない。**
- **系列開始 stock:** 各系列の job 1 で 1 session。LLM の baseline に使う (比較基盤 §4.3)。非 LLM の arm には届くが使わない。
- **参照 job (実行 batch 1〜3 に 1 本ずつ、計 3 本):** stock 5 session と、既知最良の静的 10 µs (元の適用方法 = `patches/silo-backoff-fixed.patch`、
  `BACK_OFF=1`・`BACKOFF_FIXED=10`、D2240 と同じ形) 5 session。stock の 15 session は §6 の fallback と §7.2 の floor に使う。
  静的 10 µs は endpoint との比を記述するだけで、生成器へ渡さない (R0)。
- 探索 job ごとの stock の対測定は行わない。

### 5.5 利用上限 (429) の保留 (D2258 項 2 を継承)

- LLM 親の終了記録 (`claude -p --output-format json` の出力) が JSON として読め、`is_error` が真かつ `api_error_status` が 429 のときだけ、
  その原提案機会を**保留**とする。期限を置かず、同じ原提案番号 a で再開する (再開の試行は 15 分おき)。文言だけで 429 と判定しない。
  読めない出力を 429 と推定しない。
- 保留は A・B・機械故障の retry のどれも消費せず、系列を欠測にしない。本書では LLM の待ちが計算 node の外にあるので、保留中に
  node を消費しない (B-5 v2 の「job 1 の待ち中の保留で stock を測り直す」規則は要らない)。
- 保留からの再開では、完了した role の出力をそのまま使い、最終応答を得られなかった role の呼出しだけを同じ入力で行い直す。
- 正常終了 (`is_error` が偽、終了 code 0) で提案も明示の却下も無い = 空出力 (A を 1 消費)。model の不一致の記録があれば系列を
  分類不能欠測で終える。他の異常終了は同じ a で追加 2 回まで。
- 保留の回数・時刻・長さを全件記録して報告する。保留は暦時間を延ばす。

### 5.6 job の単位 (D2258 項 1 を継承し、job 1 の中身を変える)

全 arm で同じ切り方にする。

| job | 中身 |
|---|---|
| job 1 | 系列開始 stock 1 session + 初期点 2 (5 µs → 10 µs)。原提案を待たない |
| job 2〜11 | 評価 1 回ずつ (原提案が公開され、継承検査を通ってから投入) |
| 最終 job | endpoint の score 5 session |
| 参照 job | stock 5 + 静的 10 µs 5 (batch ごとに 1 本) |

- **D2258 との違い:** B-5 v2 は「系列開始 stock と評価 1 を同じ job」に置き、LLM の原提案 1 をその job の中で待った。本書は同じ job の対照を
  初期点が担うので、評価 1 を job 2 に回し、LLM の待ちを全部 node の外 (login の起動器) に置く。
- 却下された原提案 (A だけ消費) は job を起こさない。1 系列に同時に走る job は 1 つ。
- 計算 job は起動時に、要求された単位が台帳から導いた次の単位と一致することを確かめ、違えば session を始めずに終わる。
- job が途中で死んだ跡 (結果の無い slot 開始記録) がある系列は、自動で再投入せず止めて報告する (分類は §3 の機械故障の規則)。
- walltime は job 種別ごとに発効束に固定し、全 arm 同一とする (実測の最大所要への倍率、D2217)。

## 6. endpoint と score

- **endpoint:** 各系列で、自系列の初期点と探索点のうち、資格のある certified・品質正常の点で探索時の session median が最大のもの。
  同値は slot の早い方。endpoint の identity・source・出所 slot を再計測の前に固定する。他系列の候補や既知の勝者を補充しない。
- **anomaly の波及:** ある identity で anomaly が 1 件でも観測されたら (探索・初期点・再計測のどこでも、どの系列・arm でも)、
  その identity は全系列で endpoint の資格を失う (比較基盤 §4.6)。先行する certified 記録は歴史事実として残す (規律 7)。
  score 確定後に波及した場合は、その系列の endpoint を資格なしとして下の「欠測と fallback の優先」を 1 から当て直し
  (他の資格ある点へ選び直さない。優先 1〜3 に当たれば欠測・判定不能、当たらなければ優先 4 の fallback)、失敗条件 (a) に記録して、
  日付付きの「結果の訂正」として報告する (Erratum ではない、B-5 v1 §6 と同じ)。この判定は生成器へ還流しない。
- **score:** endpoint を N_eval = 5 の fresh session で再計測し、その 5 session の median throughput。同じ 5 session から endpoint の CV を求める。
- **欠測と fallback の優先 (比較基盤 §4.6 と同じ順):**
  1. stock (系列開始 stock または参照 job の stock) の正しさか測定が成立しない → 当該比較は判定不能。
  2. 機械故障が retry 上限を超えた → endpoint の有無を問わずその時点で系列を終え、score 欠測。
  3. endpoint が無く、自系列に品質欠測が 1 件でもある → score 欠測。
  4. endpoint が無く、失敗がすべて候補起因 (anomaly・検査の拒否・build 失敗) → 参照 job の stock 15 session の median を score にする
     (**fallback**、候補の不採用)。この 15 件は全 arm の不採用系列に共通で、共有を明記する。
  5. endpoint の再計測で anomaly → 採用せず fallback。次点へ選び直さない。
  6. endpoint の再計測で品質欠測・機械欠測 → score 欠測。
- anomaly を 0 tps や −100 % へ変換しない。score は「候補を採用できなければ stock を使う」運用の性能である。各 arm の certified endpoint 数
  (12 中) を必ず併記する。
- **公平性の目視 (D2214 項 8):** 全 arm・全系列の endpoint と、各比較で勝った側の endpoint の本文を、score の確定後・報告の前に auditor が
  目視し、worker の駐車や偏りの疑いを所見として報告に併記する。目視の所見を理由に score・判定・系列を変えない (事後の除外をしない)。
  非 LLM の候補は探索中に auditor 段を通らないので、この目視が唯一の点検である。

## 7. 母集団・配置・floor・判定

### 7.1 母集団と配置

- 主セルは 4 arm (LLM×C++・LLM×IR・random×IR・進化×IR)、各 **n = 12 系列**、計 48 系列 (規模の択一は §11.3)。
- 同じ系列番号 r の 4 系列を 1 組とする。組の中の開始順は 4 × 4 の巡回ラテン方格 (基本順 LLM×C++・LLM×IR・random×IR・進化×IR を
  (r − 1) mod 4 だけ左へ巡回) で、各 arm が各位置に 3 回ずつ来る。表は発効束に固定する。
- 系列番号 1〜4・5〜8・9〜12 を**実行 batch** 1〜3 と呼ぶ。batch は実行の名札であり、時間を空ける規則も、batch ごとの再現を判定の条件にする規則も
  持たない (D2249 追加項)。参照 job は batch ごとに 1 本。
- 起動器は組を系列番号順に開く。同時に進める系列数と同時に動く LLM 親の数の上限は発効束に固定する (推奨: 系列 16 = 4 組、LLM 親 4)。
  組の 4 系列が同じ時刻に揃って進むことは要求しない。系列間で LLM context と探索状態を引き継がない。

### 7.2 floor と等価域

- `CV_stock` = 参照 job の stock 15 session の session median の標本 CV (分母 n − 1)。
- 等価域 `f = max(0.03, CV_stock)`、`δ = ln(1 + f)`。3 % は保守下限であり、今回測った雑音の値とは呼ばない。
- 精度 gate: endpoint の 5 session の CV が `2 × f` を超える対は精度不足。floor が欠測・非有限なら判定不能。

### 7.3 優越の検定

- 検定単位は系列。対差 `d_r = ln(score_X,r / score_Y,r)` (X = LLM の arm、Y = 非 LLM の arm)。統計量は対差の算術平均。符号を全 2^n 通り
  反転する片側 exact permutation (観測値以上を tail に含める)。
- **前提 (登録する仮定):** 帰無の下で、対差は互いに独立で、各々の符号が対称である。支えは、系列が fresh context・別 preimage で始まること、
  組の 4 arm がラテン方格の順で走ること。**支えないもの:** 同じ時期に走った組に共通に入る機体・負荷の変動、§5.5 の保留で組の中の
  LLM の arm が非 LLM の arm と異なる時期に測られること、fallback の stock を全 arm で共有すること。依存を検出する検定も防壁も持たない。条件付き優越には必ず「登録した独立性の仮定の下で」を添え、対差の一覧を併記する。
- **fallback 対と副解析:** 同一比較で fallback を含む対が 2 以上なら、fallback を含む対を除いた副解析を判定に使い、残った対が 6 未満なら対不足で
  判定不能 (B-5 v1 §7.3 から block の条件を外した形)。副解析の結論は「候補を採用できた系列の対に限った」と書き、除いた対の数と arm を添える。
- **族と多重性:** 族 A (2 比較) と族 B (2 比較) を別々に Holm 法、各族の family-wise α = 0.05 (各族の初段の閾値 0.025)。判定不能・規約不適合の
  比較も族から除かず、計算上 p = 1。
- **LLM 構成 X の条件付き優越:** その族の 2 比較それぞれで (i) Holm 補正後に有意、(ii) median(d) > δ、の連言。

### 7.4 判定順と結末

比較ごとに次の順で判定し、先に該当した結末で止める (B-5 v1 §7.4 から block の条件を外した形)。

1. **規約不適合** — 配置逸脱、発効束との不一致。
2. **判定不能 (欠測・不成立)** — 12 系列のいずれかが機械故障・品質欠測、stock の測定または正しさが不成立、floor が欠測・非有限。
3. **生成不成立** — arm ごとに「certified・品質正常の探索点 (初期点を除く) を 1 つ以上持つ系列」の数 (12 中) を数え、両方が 6 未満なら
   「双方生成不成立」、片方だけなら「その arm の生成不成立」。記述だけを報告する。初期点は endpoint の候補に入るので、certified endpoint の数では
   生成器の力を測れない (B-5 v1 の定義からの変更)。
4. **判定不能 (対不足・精度不足)** — 判定に使う解析の対が 6 未満、または精度不足の endpoint を含む。
5. **条件付き優越** — §7.3 の (i)(ii)。
6. **同等 = 失敗条件 (c) の成立** — `|median(d)| ≤ δ`。観測差が比較 floor 内だったという判定で、母集団の等価性の証明ではない。
7. **逆向きの記述的差** — `median(d) < −δ`。有意な逆向き優越とは書かない (検定は片側)。
8. **判定不能 (残り)**。

- 全 12 対を使う場合の最小片側 p は 1/4096。差の絶対値が等しい例では、正が 11/12 なら p = 13/4096 ≈ 0.0032 で初段 0.025 を通り、
  10/12 なら p = 79/4096 ≈ 0.0193 で初段を通る (2 段目は 0.05)。9/12 なら p = 299/4096 ≈ 0.073 で通らない。p は差の大きさにも依存する。
  これは p 値の解像度の根拠で、検出力の保証ではない。結果を見て n を増減しない。
- 報告: 全 4 arm の score、全 4 比較、記述の LLM×C++ 対 LLM×IR、各 arm の endpoint の静的 10 µs 比と stock 比 (参照 job の median に対する記述)、
  全未完走・anomaly・fallback・欠測・floor・raw p・補正 p・batch 別の median(d) (記述)・certified endpoint 数・certified・品質正常の探索点を持つ系列の数 (§7.4 の手順 3 の根拠)・endpoint が初期点だった系列数・
  A の使用数と拒否の内訳 (検査段・auditor)・実消費 B の分布と B 未達の系列・一意な identity の数・§5.5 の保留の全件・§6 の目視の所見。
  本書の主 cohort は 1 回だけとする。

## 8. 既知結果台帳と HARKing の境界

**本書は、この軸の偵察の結果を見た後に作られた。** 前向きに固定するのは、新 cohort の生成・測定・判定の規則である。
起草した親 (Claude) は次の材料を読んだ。一次成果物を直接読んだものと、記録を通して知ったものを起草 insight §6 で区別する。

| 既知材料 | 内容と本書での扱い |
|---|---|
| 段階 C (`output/insights/2026-09-22/t2857-silo-policy-stage-c/README.md`、記録を通して) | 手書き方策の生死確認。初期点の値 (5・10 µs) の出所 |
| 段階 D の偵察 (`output/insights/2026-09-23/t2863-silo-policy-stage-d/README.md`) | 固定 16 点 (LSRM) すべてが両 verify で certified、同 job の即 abort 比 1.34〜1.78。二値 = true。初期点 2 個は `0000`・`0001` と同じ方策 |
| 既知最良との小比較 (D2240) と別 job 再測 (D2250) | 既知最良は静的 10 µs (元の適用方法)。16 点の静的 10 µs 比は 0.836〜1.069、L = 1 の 3 点 (`1001`・`1110`・`1111`) が別 job でも 5〜7% 上回った。初期点の 2 方策は 0.98 前後 |
| B-5 v1 の閉鎖 (v1 §15) と B-5 v2 の準備 (`output/insights/2026-09-26/t2797-b5-v2-prep/README.md`) | 費用の単価、LLM の週上限、write-heavy の LLM 系列の却下の原因。本書の見積りと実行契約の根拠 |
| B-5 試走・P2-5 | 値 1 個の空間で LLM・random・sweep の差 1.06%、LLM 誘導は機械的探索と差が無いか有害。本軸を選んだ理由 (D2259) |

- 設計選択との対応: 初期点に静的 5 / 10 µs を選んだ (段階 C・D を見た)、random の定数分布に 0..1000 の log 尺度を選んだ (B-5 の分布と、
  骨格の上限 1000 µs を見た)、進化の親に初期点を含めた (比較基盤 §3.3 の S1 の規則と同じ)、G_rand に `Attempt`・`retry` を含めた
  (IR の文法どおりで、L = 1 の点が良いことを見た後の選択だが、文法から外す理由も無い)。
- 偵察・小比較の値を本書の標本・予測的再現に使わない。既知の点と同じ方策が fresh に生成されることは許す。
- 発効時は exact な artifact と閲覧者・閲覧時点を台帳へ追記し、その間に得た知見も差分として残す (B-5 v1 §8 と同じ)。

## 9. 失敗条件 (a)〜(e) の本書版

- **(a)** anomaly が出た候補は即 reject し、B を消費し、endpoint の資格を失う。正しさの失敗を性能の観測に変換しない。
- **(b)** 差が等価域以下なら、有意性だけで優越と書かない。stock に対する利得と、生成器間の利得を区別する。
- **(c)** 同じ評価予算の random×IR または進化×IR が等価域内で再現すれば成立。失敗した実験として隠さず、正当な negative の結末として報告する。
- **(d)** 他 protocol の最良への優越は測らない。
- **(e)** write-heavy だけで探索し、他 workload で再計測しない。workload 特化と退行の不在は示せない。

## 10. 既存機構での実行可能性 (D2258 の流用可否を含む)

2026-09-27 時点の local main `ad114fba0` で親が読んだ結果。「実在」は部品の存在であって、本書の契約に接続済みという意味ではない。
流用元のコード位置の詳細は起草 insight §2。

| 部品 | 流用元 | 本書で使えるか | 欠ける部分 |
|---|---|---|---|
| 1 評価 1 job の系列制御 (D2258 項 1) | `orchestrator/campaign/b5_generator_contrast.py` の `run_series_step`・`next_series_action`・`SeriesLedger` | **規則は継承、コードはそのままでは使えない** | 評価の起動が `p3_s4_loop` の argv に固定 (`slot_argv`)、候補が backoff 値 (`_genome`・`validate_backoff_value`)、LLM の提案が K2 の閉じた schema と planner を要求。`SeriesLedger`・session の分類は呼べる候補 (比較基盤 §7 と同じ区分)。`select_endpoint` は同値を候補値 v で破る (`(fitness 降順, v, b)`) ので、slot 順で破る本書 §6 には使わない |
| 429 の保留 (D2258 項 2) | `tools/pegasus/b5_llm_parent.py` の `classify_exit` と保留の再試行 | **判定規則はそのまま使える** | config の field・指示文・許可 tool (`tools/b5_llm_round.py` 固定)・同じ session の resume が B-5 固有 |
| LLM 親の起動器 (D2258 項 1) | `tools/pegasus/b5_contrast_launch.py` の v2 経路 | **形は継承、コードは使えない** | schedule・job 定義・K2 設定・`p3_s4_loop` の import が B-5 固有 |
| report の v2 判定 | `orchestrator/campaign/b5_generator_contrast_report.py` | **統計の核は呼べる** (`exact_sign_flip_p`・任意の族の `_holm`・`stock_cv_floor(v2=True)`・`decide_comparison(v2=True)`・`pair_differences`) | 台帳の読込・検証・射影は B-5 の schema に結合。族は 6 / 4 比較の固定 |
| critic への入力の要請 (D2258 項 3) | `tools/b5_llm_round.py` の v2 の要請文 | 文言は使える | round tool 自体は K2・planner・backoff 値に結合 |
| 同時検査 (D2258 項 4) | campaign 設定の `verify_performance_concurrent` (`orchestrator/campaign/loop.py` が読み `pipeline.evaluate` へ渡す) | write-heavy は実測済み (D2251) | 政策 driver の campaign 設定 (`default_cfg`) にこの key が無い |
| 政策 driver | `orchestrator/campaign/p3_s4_loop_policy.py` (D2256) | 検査の順・coder 入力・auditor の digest 照合は使える | 初期点と系列開始 stock を系列の campaign の履歴と critic digest に載せる口 (§4.1 の critic が job 1 の後に読む)、系列ごとの campaign identity (cfg に cohort・arm・系列番号が無く、形ごとに 1 campaign)、§3 の停止規則の切り離し、機械生成 IR 候補を auditor なしで通す口、stock と静的 10 µs 参照の口、session の分類 (B-5 の slot sidecar に当たるもの)、同時検査、計算ノードの job body (`tools/pegasus/p3_s4_loop_pegasus.sh` は `p3_s4_loop` 固定) |
| random×IR・進化×IR の生成器 | `orchestrator/campaign/silo_policy_ir.py` | IR の型・検証・描画は使える | 乱数の生成器と変異は不在 (偵察の固定 16 点の列挙だけ) |

- **政策 driver と `tools/pegasus/` の変更は並走の [T-2865] (段階 F) の担当で、本書の起草では触れない。** 生成器・系列制御・round tool・report は
  別の実装単位で、いずれも Codex author が書き、新しい gate・検査・台帳は足さない。
- 発効の前に、段階 F の実 LLM の 1 iteration (C++ 形・IR 形) と、機械生成 IR の 1 評価を計算ノードで通し、job Elapse を実測する (DW-G01 の生死確認)。
  その実測が §11 の換算を置き換える。

## 11. 費用の見積り (投入しない)

出所の区別: **実測** = 記録の値、**換算** = 実測を本書の構成へ当てた値、**試算** = 仮定を置いた値、**契約上限** = walltime × job 数。
計算は起草 insight §4。

### 11.1 node 時間 (推奨規模 = 4 arm × n = 12)

| 項目 | 値 | 出所 |
|---|---:|---|
| 1 系列の論理 session | 18 (stock 1 + 初期点 2 + B 10 + N_eval 5) | 本書 §3 |
| 1 系列の計算 (直列の検査のままなら) | 約 7,700 s | 換算 (B-5 v1 の write-heavy の完走系列: 評価 1 回平均 407 s、score 1 session 平均 510 s、stock 251〜265 s) |
| 同時検査による縮小 | ×0.51〜0.60 | 換算 (B-5 費用見直しの模型、write-heavy、冷却 60 s 込み) |
| job の準備 | 1 job 29〜35 s × 12 job | 1 job の単価は実測 (B-5 v1 の job Elapse と計算の和の差)、12 job 分は換算 |
| 1 系列 | 1.19〜1.40 h | 換算 |
| 48 系列 | 57.0〜67.1 h | 換算 |
| 参照 job 3 本 (30 session) | 1.7〜2.0 h | 換算 (stock は 258 s、静的 10 µs は score の 510 s と置いた) |
| **図 1 枚の合計** | **約 59〜69 node 時間** | 換算 |

- 含まないもの: queue 待ち、品質再測定 (最大 3 倍)、機械故障の retry、発効前の生死確認 (§10)。LLM の待ちは node の外なので入らない。
- 政策の候補での単価は未測定である。段階 D・小比較の偵察 driver は 1 方策あたり約 130 s (verify は性能構成 1 本、6 方策 1 job の Elapse 平均 772 s) で、
  本書の経路 (性能構成 5 本の同時検査) とは違う。
- **契約上限 (確保枠):** walltime を例えば job 1 = 60 分・評価 job = 30 分・score job = 90 分とすると、48 × (1 + 10 × 0.5 + 1.5) + 参照 3 × 1.5 ≈ 364.5 node 時間。
  walltime は発効前の実測で決めるので、この値は例である。

### 11.2 LLM の直列時間

| 項目 | 値 | 出所 |
|---|---:|---|
| LLM の系列数 | 24 (2 arm × 12) | 本書 §7.1 |
| 原提案の機会 | 240〜720 (系列あたり 10〜30) | 本書 §3 |
| 1 機会の待ち | 255〜1,021 s (平均 599 s、中央値 473 s) | 実測 (B-5 v1 の 22 機会、role は critic・planner・coder。本書は planner が無く auditor が加わり、C++ 形は出力が長い) |
| 直列の LLM 時間 | 平均で 40〜120 h (両端 17〜204 h) | 換算 |
| 同時 4 親の理想の下限 | 平均で 10〜30 h | 換算 |
| 週上限に当たるまでの機会 | 不明 | B-5 v1 は他 session と共有の枠で 22 機会 (resume 運用、cache read 計 114 M token) で週上限に達した (F1050) |
| 暦時間 | 不明 (仮に 1 週 57 機会なら 4〜13 週) | 試算: 1 原提案ごとに新 session (§4.1) で 1 機会の cache read を B-5 の 1 機会目の 2.0 M token と置き、B-5 v1 が 429 までに使った 114 M token (他 session と共有の枠の中での使用量であって枠そのものではない) を週の枠と仮に置いた。1 週に回せる機会数は測れていない |

- **LLM の週上限が律速になりうる。** 1 週に回せる機会数が測れていないので、暦時間は上下限を示せない。§5.5 の保留で系列は欠測にならず、
  待つ間 node を消費しないが、暦時間は延びる。

### 11.3 規模の択一 (発効の前にユーザーが選ぶ)

| 案 | arm | 系列 | node 時間 (換算) | LLM の機会 | 失うもの |
|---|---|---:|---:|---:|---|
| **推奨** | 4 (LLM×C++・LLM×IR・random・進化) | 48 | 約 59〜69 | 240〜720 | — |
| 進化を外す | 3 | 36 | 約 44〜52 | 240〜720 | 非 LLM が random だけになり、「巨大な文法上の乱択は藁人形」の査読に答えられない |
| LLM×IR を外す | 3 | 36 | 約 44〜52 | 120〜360 | 族 A (同じ IR での探索法の比較) が消え、族 B だけになる |
| n = 10 | 4 | 40 | 約 49〜58 | 200〜600 | 最小 p が 1/1024。等しい大きさの差なら 9/10 勝ちで p ≈ 0.011 (初段 0.025 を通る)、8/10 は p ≈ 0.055 で通らない。report の系列数 (流用候補の `pair_differences` は系列 1..12 固定) も変える |

- 推奨の理由: 「なぜ LLM か」に効くのは、フィードバックを使う非 LLM の探索 (進化) との差である (random との差だけでは LLM の事前知識と
  フィードバックの利用を分けられない)。差分分析 P2 は比べる手法に進化探索を挙げる。n = 12 は B-5 v2 でユーザーが選んだ規模である (D2249 項 1)。
- 一括承認にしない。発効の決定の前に、生死確認 (§10) の実測単価で取り直した値を示す。

## 12. 発効束と確認事項

発効の決定に次の実値を書く。一覧は機械 gate の新設指示ではない。

- 計算確認の日付・決定番号・対象 commit (§10 の欠ける部品の実装が着地した commit を含む)。本書の raw bytes の SHA-256。
- CCBench の PIN、較正 record、toolchain、verifier の版。correctness・bench の exact 引数。
- LLM の model の exact ID と settings、親の指示文、各役割の入力の形 (driver の出力 schema の版)。
- G_rand と進化の実装 (commit と file の SHA-256) と、§4.4・§4.5 の確率・重みの実値。v1 の preimage で引いた値は発効の前に閲覧しない。
- 48 系列の schedule (組・ラテン方格の順・batch)、同時に進める系列数と LLM 親の数の上限。
- job 種別ごとの walltime とその根拠 (生死確認の実測の最大所要への倍率)。
- 規模の択一 (§11.3) の選択。推奨以外を選んだときは、本文の arm と族 (§1.1・§7.1・§7.3)、系列数に依る全箇所 (§7.4 の「12 系列」「12 中」
  と p 値の例、§11 の系列数、schedule の組の数) と report の系列数を選んだ案の値へ書き換えた版を、本書の起草版として発効の前に着地させる。
- 既知結果台帳の差分。

発効の確認で、ユーザーへ示す事項:

1. 規模 (§11.3) と図 1 枚の node 時間、LLM の機会数と暦時間 (不明であること)。
2. 構成: K0・R0、段階 D の二値と射程文が LLM にだけ届くこと (§4.1)、1 原提案ごとの新 session、planner なし、auditor は LLM 候補だけ。
3. 実行契約: 1 評価 1 job で job 1 に評価を置かないこと (D2258 項 1 との違い、§5.6)、429 の保留。
4. 閉じないもの (§14)。

## 13. 過大主張チェックリスト

`docs/paper-story/2026-09-17.md` の既存項目に加え、本書の結果を書くときは次を守る。

- 主張は登録した構成どうしの、固定予算下の条件付き優越に限る。「必要性」「発見」と書かない。
- 族 A (同じ IR) と族 B (空間拡張) を混ぜない。族 B の差を探索法の優劣と書かない。
- write-heavy だけの結果であることを添える。
- random と進化の支持集合は定数の分布で狭められている (§2)。
- LLM だけが段階 D の二値と射程文を受け取る (§4.1)。LLM 候補だけに auditor が掛かる (§3)。
- 評価数の上限を揃えた比較で、時間・費用を揃えた比較ではない。LLM の待ちと暦時間、実消費 B を別に報告する。
- certified の射程 (有限の観測、verify と perf の分岐の一致は言えない) を添える。
- stock (適応 backoff) と既知最良 (静的 10 µs、元の適用方法) を混同しない。偵察の 16 点の値を本書の結果と並べるときは別 job・別登録と書く。
- 非有意、等価域内の同等、欠測・精度不足による判定不能、生成不成立を分ける。条件付き優越には「登録した独立性の仮定の下で」を添える。

## 14. 本書が閉じないもの

- 実装 (§10) と、試走・本走の認可と実施。
- 他 workload・TPC-C・MOCC での成立、BO など他の非 LLM 手法との比較。
- LLM 単体・critic・auditor・段階 D の二値それぞれの寄与の分離。
- 統計の前提 (対差の独立性と符号対称性) の成立の証明。
- T-2850 の試走・本比較 (S1) との統合。標本を混ぜない。
- D2219 項 6 (open-weight LLM) の再提示の要否。本書の比較も LLM の直列時間が律速になりうるが、同項の条件は T-2850 の本比較を名指すので、
  本書は条件を広げず事実だけを発効の提示に添える。

## 15. 改訂履歴 (起草版の間だけ使う)

- 2026-09-27: 起草 ([T-2867])。
- 2026-09-27: 起草 wave の段 6 レビュー (Codex 2 本) と親の点検を受けて改めた (着地前): critic を job 1 の後にも回す・性能が critic 経由でだけ
  LLM に届くことの開示、後発 anomaly の score 訂正、公平性の目視、B を上限と明記、進化の field 追加の規則、生成不成立の定義、
  `select_endpoint` の流用不可、n = 10 案の report 系列数、週上限の書き方。裁定の記録は起草 insight §7。
- 2026-09-27: 同じ wave の焦点再レビューを受けて改めた (着地前): critic を原提案機会の中の役割にした、後発 anomaly の訂正に欠測の優先を当て直す、
  推奨以外の規模を選んだときの書き換え範囲、生成不成立の根拠の数の報告、B を上限とする表現の統一。
