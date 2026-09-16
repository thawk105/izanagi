## 所見

以下、`L`＝[layer3_report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2718-layer3-lock-purpose/orchestrator/campaign/layer3_report.py)、`T`＝[test_layer3_report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2718-layer3-lock-purpose/orchestrator/tests/test_layer3_report.py)。行番号は適用後。静的レビューであり、pytest・変異試験は実走していない。

**RA-1 — 提示 patch は「12 hunks」ではなく11 hunks。**
- 対象：`s5-author-out.md:3,21`、`s5-author.patch:1`、`s4-ruling.md:29`。
- 主張・根拠：patch は実装6＋テスト5＝11 hunks、2ファイル。報告の12番目は `tools/t2718_real_corpus_probe.py` だが、提示 patch に存在しない。段4の2ファイル上限には当初のauthor成果物が違反していた一方、`real-probe-summary.md:3` によれば親がprobeをrepo外へ退避済み。提示差分には違反が残っていない。
- 自己判定：**real／nit**。最終記録を「適用差分2ファイル・11 hunks、外部probe別添」に訂正すること。存在しない第12 hunkをレビュー済みとは数えない。

**RA-2 — I5の実測は、63の正常なreport出力一致までは示していない。**
- 対象：`real-probe-summary.md:15–18`。
- 主張・根拠：正常生成後の比較はv1の1本。残る2本はadmission拒否の一致であり、63対照もrecords/threads検査で停止している。新規T:1996はdecoderの型・identity、T:2048はknowledge helperを検査するが、63のreport全体比較ではない。
- 自己判定：**real／nit**。I5違反を発見したわけではない。証拠を「v1出力一致・他2本の拒否一致」と限定し、I5全体を実測済みとするなら正常生成できる63 fixtureの前後比較を追加すること。

**RA-3 — certified受理集合が拡大する疑義は棄却。I1は成立。**
- 対象：`L:951,968,982,997,1068`、`campaign_lock.py:620,638,688,706`。
- 根拠：入力bytesを固定した場合、次の経路となる。

| grammar | 変更前→変更後のcertified経路 |
|---|---|
| exact-62 | 旧L:937→現L:951で通常decoder。`campaign_lock.py:638`のauthority検査で拒否。L:133で従来と同じ`Layer3ReportError("campaign.lock schema が不正")`へ変換し、codec例外をcauseとして保持 |
| exact-24 | exact-62と同じ。歴史decoderへ到達しない |
| 63 | L:951は同じ通常decoder。内側のL:767だけ歴史decoderになるが、`campaign_lock.py:706–707`で通常decoderへ委譲し、identityを維持。trial、HEAD、admission status、certified admission、receipt一致、E1検査は不変 |
| v1 | L:951は従来どおり通常decoder。内側も`campaign_lock.py:688–689`で同じdecoderへ委譲し、authorityはNone。既存のadmission／E0拒否を回避する変更なし |

`render_accepted`はL:1068でbuilderを呼び、成功後のL:1074だけで書く。既存出力拒否も不変。なお呼出し方向は`render_accepted → build_accepted_report`である。
- 自己判定：**refuted／must-fix該当なし**。並行書換えを含む保証とは区別する（RA-6）。

**RA-4 — identity渡しによるknowledge検査の緩和は認めない。ただしテスト単独では拒否箇所を固定していない。**
- 対象：`L:829`、`wal.py:1102,1135,1748–1769`、`T:2069–2078`。
- 根拠：通常decoded objectはwal:1748でそのまま返され、1768で`.identity`になる。schema_versionを持たないidentity dictは1752でdecoded扱いをせず、1769でそのまま返る。63／v1とも同じidentityに収束する。L:805付近のexact identityキー検査も先行しており、任意の未検証dictへ入口を広げていない。
- 拒否parityでは、T:2071の`dataclasses.replace`が持つidentityと、2073で直接渡すidentityは**同じdict**。片方だけ古いidentityを検査する構造ではない。wal:1135／1102のbinding経路に同じ値が渡るため、現実装で別理由の偶然一致を示す材料はない。
- 証拠の限界：許可されたwal抜粋には`_knowledge_lock_binding`本体とhelper後半がない。経路全体の確認は段4 A-2の親による読解報告に依存する。T:2076–2078自体はexact例外型と文言一致だけで、発生箇所・期待理由をassertしていない。
- 自己判定：検査緩和の疑義は**refuted／must-fix該当なし**。拒否箇所も固定したいなら、期待文言とbinding経路のtracebackを検査する強化は**nit**。現状のparityは段4の要求を満たす。

**RA-5 — purpose分岐・例外変換はD422／D1653と整合し、規律2の違反ではない。**
- 対象：`L:112–133,745,767,905`、`artifact_admission.py:180,1016,1539`。
- 根拠：
  - purposeは必須keywordで既定値なし。exact enum検査がread_text・decodeより前。
  - enumは定義済みの2値。bool／文字列による緩和を許さない。
  - 通常decoderと歴史decoderは別入口・別返却型を維持。consumerのunion注釈は通常decoderの受理集合をunion化しない。
  - 例外変換は従来のまま。失敗後のfallback・握り潰し・部分report返却なし。
  - `build_report`のadmissionは元からHISTORICAL_RAW固定。今回のreaderがそれに一致する。reportは引き続き`certifying_input=False`、`acceptance_receipt=None`。
  - 通常decoder／encode／resume／admission／wal実装への差分、私有purpose validatorのimportはない。
- 自己判定：**refuted／must-fix該当なし**。解消するのは歴史grammarによる再拒否だけであり、中央admissionの受理集合と材料reportの受理集合全体が一致するわけではない。

**RA-6 — decodeとdigest照合の読取り窓は既存課題として残る。**
- 対象：`L:767,810`、`s4-ruling.md:9`。
- 主張・根拠：decodeした文字列自体ではなく、後から読み直したファイルをadmission digestと比較する構造は残る。差分はこの構造を新設しておらず、固定入力に対するI1の反例にはならない。
- 自己判定：既存課題として**real／裁定パッケージ候補**、本変更の回帰としてはrefuted。段4どおり別項目へ送る。実corpusのrecords/threads対応も別項目であり、今回完全生成できたとの記載は不可。

## hunk × 裁定 対応表

第1～11行が提示patchの全hunk。第12行はauthor報告との照合用。

| # | 適用後の対象 | 変更 | 裁定との対応・判定 |
|---|---|---|---|
| 1 | L:112 | 必須purpose、exact型検査、decoder分岐、union返却型 | P1、I6、D422／D1653、M01～04・06・08・09。適合 |
| 2 | L:205 | HEAD helper引数のunion化 | brief scope #5。注釈のみ、適合 |
| 3 | L:388 | calibration helper引数のunion化 | brief scope #5。注釈のみ、適合 |
| 4 | L:767 | HISTORICAL_RAW明示 | P3、scope #2、M05。適合 |
| 5 | L:829 | WALへ`.identity`を渡す | P2、A-2／B-4、M07。適合 |
| 6 | L:951 | CERTIFIED_ACCEPTANCE明示 | I1、scope #3、M04。適合 |
| 7 | T:9 | Enum import | B-6の別Enum負例に必要。適合 |
| 8 | T:569 | 歴史fixture helper追加 | B-7、実admission、committed closure、既存issuing context。適合 |
| 9 | T:1915 | 新規7関数・14ケース | grammar正負例、固定epoch、purpose境界、HEAD fallback、knowledge parity。適合。parityは別関数／parametrizeではなく既存新規関数内のloopだが要求する比較は実施 |
| 10 | T:2448 | 既存callerへcertified purpose追加 | B-3。既存期待値不変 |
| 11 | T:2470 | 同上 | B-3。既存期待値不変 |
| 12 | author報告のprobe | 提示patchに存在しない | repo内なら規模上限違反。親報告ではrepo外へ退避済み。コードレビュー対象外 |

生産コードのimport・既存検査順序・既存例外文面を変更するhunkはない。追加のTypeError文面と、型検査を読取り前に置く順序は裁定内。

## 変異 × test 殺傷表 (M01〜M10)

以下は静的な検出予測。「殺せる」は実走済みの意味ではない。

| 変異 | 検出するtest／失敗箇所 | 判定 |
|---|---|---|
| M01 常に通常decoder | `test_historical_exact_grammar_build_report[62/24]`：T:1921で予期しないschema例外。1925以降のassertへ到達できない | 殺せる |
| M02 分岐反転 | 上記正例がT:1921で失敗。`test_read_campaign_lock_current_and_v1_by_purpose`もT:2012のexact型assertで失敗 | 殺せる |
| M03 常に歴史decoder | `...current_and_v1_by_purpose[CERTIFIED_ACCEPTANCE-*]`のT:2012が失敗。accepted負例も初期codec拒否を失い、T:1960／1961で区別する | 殺せる |
| M04 accepted入口をHISTORICAL_RAWへ | `test_accepted_report_rejects_historical_exact_grammar_at_lock[62/24]`：初期codec拒否が消える。後段拒否ならT:1960の全文一致、拒否自体がなければT:1955の`raises`が失敗 | 殺せる |
| M05 material入口をCERTIFIED_ACCEPTANCEへ | historical正例のT:1921で通常decoderが旧grammarを拒否 | 殺せる |
| M06 exact型検査を除去 | `test_read_campaign_lock_rejects_non_exact_purpose`：存在する63 lockで文字列が通常decoderへ流れて成功し、T:1986の`raises(TypeError)`が失敗 | 殺せる |
| M07 WALへdecoded objectを戻す | historical正例のT:1921。歴史decoded型はwal:1754–1755で拒否され、L:832以降でknowledge例外へ変換。knowledgeなしでもwal:1135は実行される | 殺せる |
| M08 purposeへ既定値追加 | `test_read_campaign_lock_requires_purpose`：T:1967の`raises(TypeError)`が失敗 | 殺せる |
| M09 型検査をread_text後へ移動 | non-exact purpose testの`missing.lock`ケース。TypeErrorより先に読取り失敗となり、T:1986が失敗。try内ならLayer3ReportError、外ならFileNotFoundError | 殺せる |
| M10 等価変異 | L:128の`return campaign_lock.decode_historical_campaign_lock(text)`を`decoded = campaign_lock.decode_historical_campaign_lock(text)`＋`return decoded`へ変更。呼出し回数・順序・返却object・例外を維持 | **SURVIVED期待**、`expected_nodes=[]` |

M01～M09に、静的に生存すると判断したものはない。M03は返却型assertだけでも検出でき、accepted負例の後段挙動に依存しない。

## 総括

- **must-fix 0件、静的レビューはGO。固定入力に対するI1は成立。**
- 提示差分は2ファイル・11 hunks。probeを第12 hunkとしてレビュー済みに数えないこと。
- 親への要求：M01～M10の実走結果を照合し、I5の実測範囲を正確に記録すること。
- 実corpusの到達点はrecords/threads拒否まで。完全生成・全試験完了は本レビューからは宣言しない。