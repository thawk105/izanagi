総合裁定は **条件付き採用を却下し、段階 B へ差し戻し**である。第一候補「write set の格納形式」は、非列挙性・現動作点での感度・安全な閉包の三点を同時に満たしていない。

以下、`brief.md` / `plan.md` は指定された `/tmp/.../scratchpad/wave-t140/` 配下を指す。

### 所見 B-1

- **深刻度**: blocker
- **主張**: 「任意 C++ 実装だから非列挙」という性質を、LLM 固有価値の証拠にすり替えており、研究上の比較命題が定義されていない。
- **裏取り**: `plan.md:123-125` は全空間を非列挙と宣言するだけで、機械側の生成文法・予算・同値関係を未定としている。`docs/roadmap.md:15-17,32-36,452` は、LLM が機械探索を上回ることをシステム成功条件から除外し、LLM 固有主張にはアブレーションを要求する。`docs/phase3-main-experiment.md:19-40,82-85` も同一編集面・同一予算の非 LLM 対照を要求する。
- **なぜ問題か**: container variant が certified になっても、それだけではレポートの「LLM 固有の成果」受理集合に入らない。非列挙性を根拠に入れると、試行台帳は有効でも帰属付き材料レポートが過大主張になる。
- **最小の直し方**: 機械ベースラインの生成文法・試行予算・比較判定を先に固定する。非列挙性は空間の性質に留め、LLM 固有価値は別アブレーションでのみ判定する。

### 所見 B-2

- **深刻度**: blocker
- **主張**: 三候補の比較は、格納形式だけに「完全な任意実装」を許し、他候補を有限順列・分割へ狭めた非対称比較であり、P1 の選定根拠にならない。
- **裏取り**: `plan.md:21-25` は格納形式には完全 container 合成を許す一方、検証順序を最大 `5!`、ロック表現を `B5` と数えている。さらに `plan.md:35` は「コードとして配送されてもコード片軸ではない」と分類を宣言するだけである。`docs/axis-onboarding.md:63-65` は既存軸の言い換えを新軸として認めない。
- **なぜ問題か**: 同じ自由度なら検証順序にも任意 scheduler、ロック表現にも任意 lock-table 実装を許せる。恣意的な空間設定で格納形式を選ぶと、誤った軸へ C 以降の費用と試行台帳を集中させる。
- **最小の直し方**: 三候補を同じソース量・構文自由度・安全境界で再比較する。安全上任意実装を許せない候補は、その理由を科学的価値ではなく実装可能性として別評価する。

### 所見 B-3

- **深刻度**: blocker
- **主張**: 現動作点で性能地形が生じる機序は立証されておらず、plan の記述は「持ちうる」という可能性列挙に留まる。
- **裏取り**: `orchestrator/campaign/pipeline.py:65-68` は max operation 10、read ratio 50。`external/ccbench/include/ycsb.hh:59-75` が示すのは期待 write 操作数 5 であって set 要素数ではない。read は `external/ccbench/cc/silo/transaction.cc:211-220`、write は同 `:524-547` で既存キーを重複追加しない。set は同 `:38-39,688-690` で `clear()` される。`plan.md:23,127-138` は allocation 効果が薄いと認めた上で locality・move・search 等を列挙するが、閾値や floor 超予測を示していない。
- **なぜ問題か**: M7 の「~5」は実測分布ではなく、重複排除前の期待操作数からの推論である。地形がなければ D で軸は死亡し、non-stock の certified 選択も比較レポートも成立しない。結果を見て max operation を増やせば、別 workload を勝つまで選ぶ選択的報告になる。
- **最小の直し方**: 現 S2 における実 set-size 分布と、どのサイズから何の機序が floor を超えるかを事前条件にする。動作点変更は独立に要求された workload として事前登録・floor 再較正できる場合だけ許し、それ以外は軸を捨てる。

### 所見 B-4

- **深刻度**: blocker
- **主張**: 任意の完全 container 実装を許したまま、構成的安全保証と偵察可能性を同時に得る方法がなく、plan はこの三すくみを未解決の gate 名で覆っている。
- **裏取り**: `plan.md:47-75` は constructor、iterator、memory management を含む完全型を coder に実装させるが、shape gate は「未実装・方式未定」。同 `:193-197` も C++ scope escape の検査方式を未定としている。現行検疫自身が `orchestrator/campaign/diff_quarantine.py:14-20` で C++ 意味論の完全防壁ではないと明記する。`docs/axis-onboarding.md:150-154` は有限列挙と構成的安全保証がなければ B へ戻すよう要求する。
- **なぜ問題か**: shape だけ通る不正な lifetime、phase 依存 iterator、操作省略を受理でき、certified 集合を誤って広げる。逆に信頼済み combinator/DSL に閉じれば有限機械探索へ戻り、T-140 の動機が消える。
- **最小の直し方**: 信頼済み実装と宣言的な構成パラメータに閉じて安全性を構成的に保証するか、任意 C++ 軸を却下する。有限化した場合は機械 sweep 型であることを正直に認める。

### 所見 B-5

- **深刻度**: blocker
- **主張**: 提案された conservation shadow は候補 container から独立しておらず、自己整合型の操作欠落をなお偽緑にできる。
- **裏取り**: `plan.md:116-120` は shadow を `emplace` / `erase` 点で更新し、container と照合する。だが `external/ccbench/cc/silo/transaction.cc:524-547` では候補 iterator を使う `searchWriteSet()` の結果で `emplace_back` 自体が省略される。trace、lock coverage、実 write も同じ候補 iterator を同 `:601-623,630-682` で再利用する。`plan.md:72` は static/thread-local 状態しか禁じず、container 内の呼出回数状態は禁じていない。
- **なぜ問題か**: 反例として、conservation 検査時だけ全要素を返し、その後の lock・trace・write で要素を隠す container が契約面に残る。意図した write が実行も trace 記録もされず、verifier が anomaly 0 のまま certified と判定し得る。
- **最小の直し方**: container 分岐前の API/procedure 意図を信頼側 shadow に記録し、各消費 phase で独立照合する。それでも任意の時限挙動は有限試験で排除できないため、B-4 の出力空間制限も必須とする。

### 所見 B-6

- **深刻度**: must-fix
- **主張**: 具体戦略を文書へ書いたまま E/F の入力射影を定義しておらず、F12 型の文書経由リークを閉じていない。
- **裏取り**: `plan.md:23,123-132` は `inline/spill`、`segmented`、inline 領域、hot/cold field、write-heavy を具体的候補として列挙する。`docs/axis-onboarding.md:160-165,181-184,231-234` は具体勝ち点・実装・planner direction・文書経由の遮断を要求する。`docs/failures.md:124-129` が F12 を具体戦略例示による coder 誘導として記録する。既存 patch の骨格コメントは `patches/silo-sort-variant.patch:42-53` の対象・stock・禁止面の説明に留まる。
- **なぜ問題か**: 実際に coder へ届いた事実は未確認だが、届かないことを保証する経路もない。coder が inline/spill を返した場合、発明と文書からの転写を分離できず、性能試行は残せても LLM 帰属付きレポートは受理不能になる。
- **最小の直し方**: panel の戦略名・source・順位を隔離成果物へ移し、E/F へは生死の二値と中立な API 契約だけを射影する。射影内容と隔離元 digest を provenance に固定する。

### 所見 B-7

- **深刻度**: blocker
- **主張**: 「B01〜B12 が全緑になるまで C に進まない」は、C で初めて実装できる条件を C の入口に置いた循環である。
- **裏取り**: `plan.md:228-278` は新 pin、baseline 改修、実 TU build、shape gate、law harness、trace positive control の実走を全て C 着手前に要求する。対して `docs/axis-onboarding.md:24-30,98-110` は B を条件リストの凍結、C を機構実装・positive control と分離する。`brief.md:18-20,82` と `plan.md:280-284` は本 wave の実装なしを明記する。
- **なぜ問題か**: 正規手順では永久に C へ遷移できない。実務上は誰かが条件を無視するしかなくなり、decision の状態、試行台帳の開始条件、certified 記録の参照が不一致になる。
- **最小の直し方**: B 出口を「検査仕様・失敗条件・所有層を凍結」に限定する。実装結果の緑は C 出口へ移し、B decision には未充足条件として参照を残す。

### 所見 B-8

- **深刻度**: must-fix
- **主張**: 出口条件の複数が gate 名だけで、判定対象・期待値・未知時の扱いを固定していない。
- **裏取り**: shape gate は `plan.md:75,197` で方式未定なのに B07 が同 `:254-256` でその緑を要求する。B06 の production compiler manifest と分類器は同 `:250-252` に path/schema がない。B08 は同 `:258-260` で対象サイズ・capacity 境界・例外経路を定めない。representative panel は同 `:123-125` で未定のまま B11 同 `:270-272` の条件に置かれる。B01 同 `:230-232` は `adopt_with_conditions` を許しつつ未解決条件の扱いを定めない。
- **なぜ問題か**: 同じ成果物でも裁定者ごとに緑・赤を変えられ、実質的な無条件通過になる。特に unknown を pass 扱いすると unsafe proposal が build・certification の受理集合へ入る。
- **最小の直し方**: 各条件に artifact path、schema、実行 nodeid、期待値、negative control の reason、missing/unknown 時の fail-closed 結果を固定する。人間判断項目は機械緑と呼ばず、署名・digest 付き裁定として分離する。

### 所見 B-9

- **深刻度**: blocker
- **主張**: `DW-B03` の「全 source が ALLOWLIST の部分集合」という述語は、digest 対象外ファイルの ALLOWLIST 追加を許すため、編集面 drift を閉じない。
- **裏取り**: `plan.md:238-240` が要求するのは `EVOLVE_BLOCK_SOURCES ⊆ ALLOWLIST` だけである。現行集合は `orchestrator/campaign/source_digest.py:68-71`、digest は同 `:187-194` の source だけから作られる一方、tracked 改変拒否は同 `:299-335` の ALLOWLIST だけを見る。
- **なぜ問題か**: 例えば build に効く別 header が ALLOWLIST に追加されても source 集合の部分集合条件は緑のまま、その header の変更は許可されるが digest に入らない。別バイナリが同じ variant ID/cache/WAL を再利用し、certified 選択結果と proof-chain 参照を破壊する。
- **最小の直し方**: ALLOWLIST を `EVOLVE_BLOCK_SOURCES + 型付き例外` の完全一致にする。各例外について identity への取り込み方法を必須化し、任意ファイル追加が赤になる mutation test を置く。

### 所見 B-10

- **深刻度**: must-fix
- **主張**: 本 wave の裁定パッケージは、実効に必要な全層と原子的な導入順を固定しておらず、次 wave が B の設計を再発見しなければ実装できない。
- **裏取り**: 未定の shape gate、trace tag/Integrity field、panel は `plan.md:75,116,125,197` に残る。必要層は trusted baseline/pin、編集面三定義、shape/law gate、trace＋verifier、coverage driver、loop/coder/runbook/sweep にまたがるが、ファイル所有と導入順は凍結されていない。`docs/dev-wave/workers.md:16-17` は、効く全層を scope に入れるか裁定パッケージとして返すことを要求する。
- **なぜ問題か**: header allowlist・pin・digest だけを先行すると identity と旧 WAL 参照を変える一方、正しさ受理集合を守る gate は存在しない。逆に verifier だけ先行しても候補経路に結線されず恒真 gate になる。
- **最小の直し方**: 各層の正確な対象ファイル、変更する値・受理集合、依存先、導入段階を DAG として凍結する。本 wave では一項目も実装済み扱いせず、部分 landing を禁止する。

## 親 brief 自体への攻撃

親の **(P1)「第一候補は格納形式」選定は誤り**である。

`brief.md:77-78` は「難所が最も濃く出る」ことを選定理由にしているが、実装難度は科学的感度でも非列挙性でもない。むしろ次の三点が反証になる。

- `brief.md:33` の「両 set は ~5 要素」は実測値ではない。確認できるのは 10 回の operation と read 確率 50%までで、実 set は重複 key、read-own-write、早期 abort により別分布になる。
- 定常 allocation は消えており、plan が具体化した残りの安全な候補は vector、inline/spill、segmented と容量値へ縮退している。P2-5 型の有限 panel で尽くせない機序は示されていない。
- 格納形式だけに任意 C++ を許して「非列挙」とする比較は、他二候補を有限化した作為的な勝たせ方である。

(P2) の単一 marker 案も却下すべきである。単一 marker が保証するのは物理行の封じ込めだけで、完全型の constructor・iterator・destructor の意味的逸脱を閉じない。未定の shape gate を後付け前提にして採用とは判定できない。

(P3) に反対できる実装項目はない。本 wave で一部だけ実装すれば identity・pin・受理集合の整合を壊す。したがって正しい親裁定は、**P1/P2 を差し戻し、P3 のまま設計不成立で閉じる**ことである。現 S2 で機序を持ち、同一安全境界で非列挙性を操作的に定義できる下位軸が見つからなければ、動作点を勝つまで動かすのではなく、この軸を捨てるべきである。

ファイル変更・テスト実行は行っておらず、緑は主張していない。