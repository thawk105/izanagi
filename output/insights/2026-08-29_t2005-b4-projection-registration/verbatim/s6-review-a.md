## 攻撃した箇所

- certified continuation の関門: 成立。文書値は `VerifiedB4AdmissionRecord`、右辺は `projection_sha256(kind)` で別源であり、恒真ではない。`B4AdmissionRecordError` は握り潰されず、provider 構築前に伝播する。
- `verified_admission is None`: test-only factory に限定され、`evidence_class="test-only"` と certified controller の整合検査がある。certified への直接昇格経路は確認できない。
- production bootstrap: 不成立。verifier 後に新しい live 3 値照合を通らず実 driver へ到達する。
- 時間的一貫性: 不成立。pair 作成後は選択 driver しか再照合せず、未選択 driver の stale 化を許す。
- raw 行 grammar: ASCII の指定負例は拒否するが、NFKC 前の raw bytes に対する exact grammar ではない。
- 所有外波及: continuation は関門を通る。bootstrap は迂回する。launcher test は shared helper を import しており、既定 fixture 全件が新 3 値形へ変わる。

grammar と変異感度は次のとおり。

|入力・変異|静的結果|対応する最小保護変異|
|---|---|---|
|旧 1 値形|拒否、テストあり|regex を旧 projection 節へ戻すと負例が通り、テストは赤|
|tag 欠落|拒否、テストあり|sort 節を外すと負例が通り、赤|
|tag 重複|拒否、テストあり|trigger literal を重複可能にすると赤|
|順序違い|拒否、テストあり|tag を順不同で読むと赤|
|末尾余剰|拒否、テストあり|`fullmatch` を `match` / `search` にすると赤|
|ASCII tag の大小文字違い|拒否、テストなし|exact literal により拒否|
|ASCII 区切り空白違い|拒否、テストなし|`; ` の exact literal により拒否|
|ASCII 大文字 hex|拒否、テストなし|`[0-9a-f]` により拒否|
|ASCII で 64 桁以外|拒否、テストなし|`{64}` により拒否|
|NFKC 互換 tag・空白・hex|受理され得る、テストなし|正規化後に regex を適用しているため|
|未選択 sort stale|拒否テストは有効|全件 loop 削除または選択 driver のみに縮小すると provider mock まで到達して赤|
|3 件すべて stale|拒否テストは有効|右辺を文書値自身へ替えると provider mock まで到達して赤|

skip、反転、テスト削除は見つからない。ただし旧 verifier の「record projection と文書 projection の不一致」負例は削除され、pair 作成テストへ移されたため、bootstrap が無保護になっている。

## 所見

### 1. 高: production bootstrap が 3 値 live 関門を迂回する

- file:line: [p3_b4_admission_record.py:747](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/campaign/p3_b4_admission_record.py:747)、[p3_b4_launcher.py:346](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/campaign/p3_b4_launcher.py:346)、[p3_b4_launcher.py:528](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/campaign/p3_b4_launcher.py:528)
- なぜ問題か: verifier は文書 3 値を返すだけで record の単一 projection と照合しない。bootstrap はその写像を捨て、`_prepare_b4_closed_critic_pair` を呼ばず、sidecar を書いて実 driver を起動する。親の推論を支える 2 照合がどちらも走らない production 経路である。
- 成果物の値・受理集合: model と prompt が一致し行が構文的に正しければ、record projection が文書 3 値のどれとも違う、または文書 3 値がすべて stale な record でも bootstrap sidecar と driver 成果物を生成できる。
- 落ちる負例の構成: committed fixture の文書 3 値を stale、record projection を別の lowercase 64 hex にし、`launch_bootstrap` の driver spy が呼ばれないことを要求する。現状は呼ばれる。既存 [test_p3_b4_launcher.py:328](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/tests/test_p3_b4_launcher.py:328) は壊れた JSON しか試していない。

### 2. 高: pair 作成後の未選択 driver stale 化を検出しない

- file:line: [p3_b4_closed_critic.py:1158](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/campaign/p3_b4_closed_critic.py:1158)、[p3_b4_closed_critic.py:878](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/campaign/p3_b4_closed_critic.py:878)、[p3_b4_closed_critic.py:1902](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/campaign/p3_b4_closed_critic.py:1902)
- なぜ問題か: 全 3 値照合は pair 作成時の一度だけである。invoke 時は選択 driver の closure しか再計算せず、最終 certification も文書を再解析するだけで文書 3 値と live を再照合しない。
- 成果物の値・受理集合: base pair 作成後に sort 固有 member を変更しても base invocation、provider query、certified receipt は通る。文書 sort 値が stale な certified 成果物を受理できる。
- 落ちる負例の構成: live 3 値で base pair を作り、pair 作成後に sort の `projection_sha256` だけが変わる状態を作ってから invoke する。provider call 数 0 を要求するテストは現状で落ちる。既存 stale テストは作成前の変化しか覆わない。

同じ箇所には短い TOCTOU もある。選択値を line 1158 と line 1170 で別々に読み、record 照合は最初の値を使う。closure bytes を A、B、A と切り替えると、record=A、文書=B のまま両照合と invoke 再照合を通せる。

### 3. 中: exact grammar が raw bytes ではなく NFKC 後の grammar になっている

- file:line: [p3_b4_admission_record.py:83](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/campaign/p3_b4_admission_record.py:83)、[p3_b4_admission_record.py:517](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/campaign/p3_b4_admission_record.py:517)、[p3_b4_admission_record.py:637](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/campaign/p3_b4_admission_record.py:637)
- なぜ問題か: table cell 全体を NFKC 正規化してから `fullmatch` する。U+00A0 の区切り空白、互換幅の tag 文字、互換 hex 文字が ASCII へ変換される。U+FB00 は `ff` へ展開されるため、raw では 64 文字未満の hash も正規化後 64 桁になり得る。Cf と default-ignorable は拒否されるが、この互換変換は拒否されない。
- 成果物の値・受理集合: committed document の raw 行が文書で指定した固定 tag・ASCII `; `・raw 64 hex と異なっても、正規化後の ASCII 値として verified mapping に格納され受理される。
- 落ちる負例の構成: full section 5 document の区切り空白を U+00A0 に替える、または hash 内の `ff` を U+FB00 1 文字に替え、拒否を要求する。現状は受理される。新設 [test_p3_b4_admission_record.py:261](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/tests/test_p3_b4_admission_record.py:261) は narrow parser を直接呼ぶため、この経路を通らない。

### 4. 中: D998 の provider 前より強い順序条件を満たさない

- file:line: [p3_b4_closed_critic.py:1261](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/campaign/p3_b4_closed_critic.py:1261)、[p3_b4_closed_critic.py:1152](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/campaign/p3_b4_closed_critic.py:1152)、[p3_b4_closed_critic.py:1160](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/campaign/p3_b4_closed_critic.py:1160)
- なぜ問題か: provider 構築前という裁定は満たすが、live 3 値照合より先に `shutil.which("claude")` と executable 解決を行い、さらに artifact root を作る。D998 の「executable 探索・artifact 作成より前」という強い順序には達していない。
- 成果物の値・受理集合:受理集合は変わらないが、stale record でも空の artifact root が残り、同じ path での正規な再試行が `exist_ok=False` により拒否される。
- 落ちる負例の構成: stale sort fixture で `which` 未呼出し、artifact root 不在を要求する。現状の 2 stale テストは provider だけを mock しており、この負例を検出しない。

### 5. 低: D1000 に対して証明名と文書が範囲を越える

- file:line: [test_p3_b4_admission_record.py:318](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/orchestrator/tests/test_p3_b4_admission_record.py:318)、[phase3-b4-reflux-ablation-preregistration.md:788](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/docs/phase3-b4-reflux-ablation-preregistration.md:788)
- なぜ問題か: `bind_three_values` は実際には record と model・prompt の 2 値を照合し、projection は文書から返すだけである。文書の「3 値すべてを実走前に live と照合する関門は閉じた」も bootstrap と pair 後 stale 化を覆わない。
- 成果物の値・受理集合: 文言自体は成果物値を直接変えないため、1 行の直接影響にはできない。後続 consumer が未証明経路を閉じたと扱う危険がある。
- 落ちる負例の構成: record projection と文書 base 値を異ならせて verifier 単体を呼ぶと成功し、`bind_three_values` の広い読みを反証できる。

## 反証できなかった懸念

- pytest と acceptance-duration meta-test は実行していない。静的検査結果を緑とは扱わない。
- 許可された 7 repository file 外の caller は調べていない。確認できた所有外波及は launcher bootstrap/continuation と、launcher tests が import する shared helper に限る。
- 安定した worktree 上の certified continuation pair に限定すれば、3 値照合の右辺は live 計算であり恒真ではなく、provider 構築前の例外伝播も成立する。
- 新設された 5 grammar 負例と 2 stale 負例は恒真テストではなく、対応する保護を緩めれば赤になる。

## 総括

certified pair 作成時の核心 loop は実効性があり、恒真でも例外握り潰しでもない。  
ただし production bootstrap、pair 作成後の未選択 stale 化、live 値の二重読みに穴がある。  
raw exact grammar は NFKC により受理集合が広い。  
したがって「機構は閉じた」「残るのは値の指名だけ」は現状では成立しない。