## 攻撃した箇所

- 旧 1-driver 文法の残存: 攻撃不成立。固定 3 tag と `fullmatch` の計画なら旧形は拒否される。
- projection の driver 取り違え: 値そのものの取り違えは拒否されるが、record artifact の driver 身元には穴がある。
- 3 driver の陳腐化拒否: 攻撃成立。production 関門は選択 driver しか検査しない。
- 検査の恒真化: freshness tripwire 自体は恒真ではない。一方、draft record の検査名と証明範囲に過大主張がある。
- D1000、D1060 との整合: 攻撃成立。
- 実測表示: 段 2 は静的確認だけで、実測したとは書いていない。段 1 の「実測した事実」には静的推論が混在する。

## 所見

1. 選択されなかった 2 driver の stale 値を production 関門が受理する。

   - file:line: `artifacts/s2-plan.md:53-65,129-135,169-171,228-241,253`、`p3_b4_closed_critic.py:1157-1166`
   - なぜ問題か: verifier は `projection_by_driver[expected_driver_kind]` だけを record と照合し、既存 runtime 検査もその record と選択 driver の live closure だけを照合する。残る 2 値は 64 桁 hex であればよい。tripwire は unit test であり、production 経路からは呼ばれない。この制限はプラン自身も 253 行で認めている。
   - 成果物の値・受理集合がどう変わるか: base 実走では `[base]` だけが current なら、`[sort]` と `[trigger]` が stale な事前登録文書も runtime の受理集合に入る。
   - 落ちる負例の構成: 全 §5 欄を埋め、文書を `[base]=H_base_current`、`[sort]=H_sort_old`、`[trigger]=H_trigger_current` とし、base record に `H_base_current` を置く。base production factory は通る。予定された repository freshness test だけは、実行すれば落ちる。

2. v1 record には driver 身元がなく、「sort record を base 実走へ渡せば落ちる」という断言は artifact 単位では成立しない。

   - file:line: `artifacts/s2-plan.md:38-40,194-202,239`、`p3_b4_admission_record.py:115-137,185-205`
   - なぜ問題か: record schema と `VerifiedB4AdmissionRecord` は単一 projection を持つだけで、driver field がない。プランはファイル名も意図的に無視する。このため「どの driver 用に発行された record か」は record 自身から証明できない。
   - 成果物の値・受理集合がどう変わるか: driver の scoped path を意味の一部と考える場合、別 driver 名の path にある record でも、実走 driver の hash が内容に入っていれば受理される。
   - 落ちる負例の構成: `phase3-b4-prerun-admission-sort.json` に誤って base hash を入れ、正しい文書 binding とともに commitする。その path を base launch context と factory に渡す。verifier は文書 `[base]`、factory は live base と比較するため両方通る。予定された path 別 repository test は実行すれば落とせるが、runtime は落とさない。

3. D1060 を supersede する根拠なしに、段 1 と段 2 が「1 セルも埋めない」を「他の 9 欄を埋めない」へ変えている。

   - file:line: `materials/decisions-d1060.md:3-5`、`materials/s1-brief.md:48-49,70-74`、`artifacts/s2-plan.md:173-175,250`
   - なぜ問題か: 射影された最新裁定は当該 wave で §5 を 1 セルも埋めないと明記する。brief は D1060 を引用しながら対象セルの記入を成果物にしている。T-2005 が新しい superseding 裁定であるなら、その権限と変更された解除条件を明示する必要がある。exact model slug の提供だけでは、この裁定衝突は解消されない。
   - 成果物の値・受理集合がどう変わるか: 文書 166 行が `未記入` から 5 宣言へ変わり、D1060 が拒否した source artifact 状態を受理する。
   - 落ちる負例の構成: model slug と current 3 hash を提供して計画どおりセルを埋める。projection 関連テストは通り得るが、`§5 の値欄は全セル現状維持` という D1060 compliance 検査を置けば必ず落ちる。

4. full verifier が必ず拒否する JSON を「prerun admission record」「登録証拠」と呼ぶのは証明範囲を越える。

   - file:line: `artifacts/s2-plan.md:194-202,228-242,250-251`、`p3_b4_admission_record.py:600-607,707-718`、`materials/decisions-d998-d1000.md:51-60`
   - なぜ問題か: 他セルの sentinel が残るため、新規 3 record は `verify_b4_admission_record` を通らない。narrow parser による値の対応確認は、D998 の Git binding と full §5 admission を証明しない。`test_repository_preregistered_projection_map...` や「T-2005 の登録証拠」という表現は、draft candidate 以上の効力を示唆する。
   - 成果物の値・受理集合がどう変わるか: runtime の受理集合は増えないが、repository に admission record と誤分類され得る無効 artifact が 3 件増える。
   - 落ちる負例の構成: 新規 record のいずれかを現在の draft 文書に束縛して full verifier へ渡す。projection が正しくても、残る `未記入` により source-cell contract で落ちる。プラン自身の draft-gate 負例がこれを再現する。

## 反証できなかった懸念

- 提案どおり `_EXPECTATION_ROW_RE` を完全置換して `fullmatch` を維持するなら、旧 1-driver 形を通す経路は構成できなかった。
- record に本当に driver A の live hash が入り、実走が driver B で、両 hash が異なる場合は、文書の B tag 照合または live closure 照合で落ちる。所見 2 は record の身元が内容以外に存在しない問題である。
- 文書の固定値と live `projection_sha256(kind)` を独立に比較し、片側だけを変異させる freshness test は恒真ではない。実際に落ちる負例を構成できる。
- 段 2 は冒頭と 246 行で未実行を明記しており、走らせていない検査を緑とは報告していない。段 1 の 7、8 番は実測値というより静的導出と一般化だが、段 2 が再実測した事実ではない。

## 総括

最大の穴は、3 値を宣言しても production が 1 値しか検査せず、残る 2 値の stale を受理する点である。  
v1 を維持するなら、record の driver 身元を主張せず、全 3 closure の runtime 照合を別途閉じる必要がある。  
D1060 の明示的 supersession がない限り、セル記入と admission 名の JSON 発行は停止対象である。  
検査は実行しておらず、以上は許可された資料だけによる静的検査結果である。