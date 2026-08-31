## 総括

- B1: **一部 real、全体は refuted**。15 comparator の閉集合と name/value 束縛は妥当だが、trigger 軸と完全同形ではなく、stock=`None` は実 freeze に対応しない。
- B2: **refuted**。主要 consumer は押さえているが、portable receipt の生成・再検証・ratified schema と複数 fixture が列挙から落ちている。
- B3: **real**。ignored file を含む非切詰め検索で、現行 v4 prefix は独立 golden 2 件だけ。生きた成果物は 0 件だった。
- B4: **SHA 一致は real、実効的な bytes 不変関門は refuted**。2 JSON の SHA は manifest と一致するが、その検査は現在 held である。
- B5: **一部 refuted**。ptrace 部分は D1271 に直接必要だが、stock 特例と余分な公開 API は scope 外。逆に freeze generator pin 解決と `active_order` 負例が欠落している。
- B6: **refuted**。影響面が大きく、ptrace 制御フローの保証も未証明。さらに「oracle test は受入全走から恒久除外」という前提自体が現行コードでは偽である。
- B7: **refuted**。P1-b は `active_order` について明確に誤り。A11 も場所は合うが「実効的関門」という役割が現状と違う。
- この consult では pytest を実走しておらず、緑とは判定していない。

## B1

**判定: refuted。ただし stock を除いた 15 entry の核は real。**

- 機械導出元は 15 件で、名前重複・implementation 重複・stock 名衝突はいずれも無かった。[s6_sort_sweep.py:109-171](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2076-t493-sort-oracle-parent-reference/orchestrator/campaign/s6_sort_sweep.py:109)
- 実 JSON と導出値を byte exact で照合した結果は次のとおりだった。

  - balanced: `sp_dd`、268 bytes、exact 一致
  - write-heavy: `sk_ad`、262 bytes、exact 一致
  - read-heavy: `sk_ad`、262 bytes、exact 一致

  実 entry は [known_axes_freeze.json:158](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2076-t493-sort-oracle-parent-reference/output/s1-freeze/known_axes_freeze.json:158)、[:384](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2076-t493-sort-oracle-parent-reference/output/s1-freeze/known_axes_freeze.json:384)、[:610](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2076-t493-sort-oracle-parent-reference/output/s1-freeze/known_axes_freeze.json:610)。

- stock の実体は `sort_best` ではなく、flags と sources だけを持つ `stock_common` である。name も comparator も無い。[known_axes_freeze.json:211](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2076-t493-sort-oracle-parent-reference/output/s1-freeze/known_axes_freeze.json:211)
  従って `stock -> comparator=None` は現物の正規形ではなく、将来の仮想 `sort_best=stock` を受け入れる追加仕様である。今 wave から外すべきである。
- trigger 側は predicate を IR emitter から閉じ、別経路で name→mask を導出して突き合わせる。[trigger_gate_binding.py:85-108](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2076-t493-sort-oracle-parent-reference/orchestrator/campaign/trigger_gate_binding.py:85)、[s1_known_axes_freeze.py:101-175](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2076-t493-sort-oracle-parent-reference/orchestrator/campaign/s1_known_axes_freeze.py:101)
  sort 案は name と comparator の両方を同じ `CANDIDATES` tuple から得るため、closed membership と pair binding は同形だが、独立再導出性と outer-whitespace 正規化は同形ではない。
- read-heavy を `("sk_ad", write-heavy provenance implementation)` に束縛する位置は妥当。[s1_known_axes_freeze.py:483-505](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2076-t493-sort-oracle-parent-reference/orchestrator/campaign/s1_known_axes_freeze.py:483)
- `_validate_schema` は `verify_document()` の schema 検査入口として一意である。[s1_known_axes_freeze.py:803-836](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2076-t493-sort-oracle-parent-reference/orchestrator/campaign/s1_known_axes_freeze.py:803)
  生成側は `_sort_entry()` に別途入れる必要があり、plan の「両側」は呼出構造に合う。
- ただし新 module が import 時に index 構築して例外を出す設計では、CLI の `FreezeError` catch より前に失敗する。構造化された `FreezeError` にするなら遅延構築か明示的 import wrapper が必要である。

## B2

**判定: refuted。列挙は閉じていない。**

識別子の主な pin は次の層にある。

- producer dataclass、結果検査、wire、contract 導出、receipt 生成: [sort_swo_oracle.py:217-249](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2076-t493-sort-oracle-parent-reference/orchestrator/campaign/sort_swo_oracle.py:217)、[:410-476](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2076-t493-sort-oracle-parent-reference/orchestrator/campaign/sort_swo_oracle.py:410)、[:1460](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2076-t493-sort-oracle-parent-reference/orchestrator/campaign/sort_swo_oracle.py:1460)、[:1653](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2076-t493-sort-oracle-parent-reference/orchestrator/campaign/sort_swo_oracle.py:1653)、[:2250](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2076-t493-sort-oracle-parent-reference/orchestrator/campaign/sort_swo_oracle.py:2250)、[:2546-2630](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2076-t493-sort-oracle-parent-reference/orchestrator/campaign/sort_swo_oracle.py:2546)
- WAL／attempt への値射影: [sort_swo_oracle.py:2915-2994](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2076-t493-sort-oracle-parent-reference/orchestrator/campaign/sort_swo_oracle.py:2915)
- portable receipt schema と exact pin: [s8b_sort_swo_receipt.py:36-56](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2076-t493-sort-oracle-parent-reference/orchestrator/campaign/s8b_sort_swo_receipt.py:36)、[:114-137](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2076-t493-sort-oracle-parent-reference/orchestrator/campaign/s8b_sort_swo_receipt.py:114)、[:159-215](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2076-t493-sort-oracle-parent-reference/orchestrator/campaign/s8b_sort_swo_receipt.py:159)
- critic current schema／receipt loader: [digest.py:313-470](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2076-t493-sort-oracle-parent-reference/orchestrator/critic/digest.py:313)、[:632-682](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2076-t493-sort-oracle-parent-reference/orchestrator/critic/digest.py:632)、[:858-1048](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2076-t493-sort-oracle-parent-reference/orchestrator/critic/digest.py:858)

段 2 に無い実 consumer は少なくとも次である。

- `orchestrator/campaign/s8b_floor_campaign.py:148-151,4401-4408` — portable receipt producer。
- `orchestrator/campaign/s8b_binary_admission.py:32-35,420-431` — portable receipt の再検証入口。
- `orchestrator/campaign/s8b_ratified_freeze.py:184-191,2622-2627` — ratified artifact の許可 schema。
- `orchestrator/campaign/s1_direct_comparison.py:128-145,1012-1014` — result ID／receipt の追加射影。
- `orchestrator/tests/test_s8b_binary_admission.py:22-24,144-150`
- `orchestrator/tests/test_s8b_floor_campaign.py:91-94,638-640`
- `orchestrator/tests/test_s8b_floor_stats.py:59-62,227-232`
- `orchestrator/tests/test_s8b_freeze_io.py:30,380-383`
- `orchestrator/tests/test_s8b_ratified_freeze.py:47-50,459-463`
- `orchestrator/tests/test_s8b_ratified_verify.py:42-45,356-362`
- `orchestrator/tests/s8b_v2_freeze_fixture.py:136-139,325-331`

多くは current 定数を fixture 経由で使うためコード編集不要だが、consumer 全件という主張と検証対象一覧には入れる必要がある。また [sort_swo_oracle.py:3-16](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2076-t493-sort-oracle-parent-reference/orchestrator/campaign/sort_swo_oracle.py:3) の module docstring も新保証と矛盾するため更新対象である。

`PROTOCOL_VERSION` は外部 receipt の独立 field ではなく、wire header、TU semantics、contract ID を介して束縛される。この形自体は妥当である。

## B3

**判定: real。legacy-v4 は不要。**

`rg --hidden --no-ignore --text 'sort-swo-v4-corpus2-protocol3-checker3-grammar1' .` の非切詰め結果は次の 2 件だけだった。

- [test_sort_swo_oracle.py:2050-2056](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2076-t493-sort-oracle-parent-reference/orchestrator/tests/test_sort_swo_oracle.py:2050)
- [test_critic.py:98-103](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2076-t493-sort-oracle-parent-reference/orchestrator/tests/test_critic.py:98)

いずれも独立 golden であり、campaign、WAL、receipt、freeze、ignored artifact には hit が無い。legacy-v4 generation／loader を追加しない判断は正しい。

## B4

**判定: SHA 一致は real、実効性は refuted。**

実 SHA-256 は manifest と一致した。

- `known_axes_freeze.json`: `354f4b875a3c8106169252afc71cee1fd08df83b0f3024c72bda0a791e11f516`
- `measurement_freeze.json`: `203de36b9749b9021d1b944d26fad4c8ed617a0fdd1438435cb67e90a0efcf7a`

manifest 値は [test_frozen_artifacts.py:41-45](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2076-t493-sort-oracle-parent-reference/orchestrator/tests/test_frozen_artifacts.py:41) と一致する。

ただし次の二重問題がある。

- `HOLD.HELD=True` であり、known_axes／measurement を含む held 4 件は実 SHA 検査から外される。[freeze_verification_hold.py:14-25](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2076-t493-sort-oracle-parent-reference/orchestrator/campaign/freeze_verification_hold.py:14)、[test_frozen_artifacts.py:162-179](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2076-t493-sort-oracle-parent-reference/orchestrator/tests/test_frozen_artifacts.py:162)
  従って plan の「既存 test を bytes 不変の関門にする」は現状では偽である。
- freeze 記録の generator SHA は `1d4d45...364e0`。[known_axes_freeze.json:5-8](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2076-t493-sort-oracle-parent-reference/output/s1-freeze/known_axes_freeze.json:5)
  現行 generator の実 SHA は既に `a9edc1...d55b4` であり、`verify_document()` は無条件不一致にする。[s1_known_axes_freeze.py:840-843](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2076-t493-sort-oracle-parent-reference/orchestrator/campaign/s1_known_axes_freeze.py:840)

単位 2 で generator を編集すれば JSON bytes を直接書かなくても generator pin はさらに変わる。物理 bytes 不変と「現行 generator で freeze を verify できること」は両立していない。段 2 はこの経路を落としている。

## B5

**判定: 一部 refuted。**

今 wave から外すべきもの:

- 実 artifact に存在しない stock=`None` 特例、`STOCK_IMPL_NOTE` 拒否、stock comparator 用正例。
- 利用先のない公開 read-only mapping と、`is_authorized_*`／`require_*` の二重 API。private index と一つの exact binding helper で足りる。
- legacy-v4 reader。B3 のとおり live artifact が無い。

直接必要なので残すもの:

- 15 comparator の exact membership と name/comparator 束縛。
- read-heavy の流用 provenance gate。
- 生成側と `_validate_schema` 側の負例。
- D1271 を満たすための broker-owned 観測。ただし方式の妥当性は B6 の裁定前提。
- contract bump と current consumer 追随。

目的に必要なのに欠けているもの:

- `active_order` 書換えの独立負例。
- freeze generator SHA と bytes 不変方針の裁定。
- ptrace setup 不可、trap 欠落、候補から trap helper を直接呼ぶ場合の分類テスト。
- B2 の portable receipt／binary admission／ratified schema consumer の検証。
- oracle module docstring の新保証への更新。

## B6

**判定: refuted。現 plan は 1 wave の実装準備済み規模ではない。**

概算である。

- plan が指定する `sort_swo_oracle.py` の既存 line window は約 **1,037 行**。
- `test_sort_swo_oracle.py` の指定 window は約 **744 行**。
- 新 authority と専用 test は約 **290 新規行**。
- s1 generator、critic、receipt、consumer golden を含めると、レビュー対象は少なくとも **2,500 行超**、実 diff も概算 **800〜1,400 行級**になりうる。

受入前提も誤っている。現行では `SANCTIONED_EXCLUSIONS=()` である。[test_selection_contract.py:53-61](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2076-t493-sort-oracle-parent-reference/orchestrator/test_selection_contract.py:53)
collection contract も除外表が空で oracle sibling を除外しないことを固定し、explicit oracle file の収集正例を持つ。[test_pytest_collection_config.py:346-353](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2076-t493-sort-oracle-parent-reference/orchestrator/tests/test_pytest_collection_config.py:346)、[:1085-1089](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2076-t493-sort-oracle-parent-reference/orchestrator/tests/test_pytest_collection_config.py:1085)
従って D669 の歴史は別として、現行 acceptance は oracle test を恒久除外していない。

失敗分類は plan だけでは閉じていない。

- ptrace 権限／`PTRACE_TRACEME`／broker launch の失敗が現行 `_EvaluationUnavailable` 経路へ入れば `UNAVAILABLE` となり、PASS せず campaign を停止する。[sort_swo_oracle.py:2244-2249](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2076-t493-sort-oracle-parent-reference/orchestrator/campaign/sort_swo_oracle.py:2244)、[:2883-2896](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2076-t493-sort-oracle-parent-reference/orchestrator/campaign/sort_swo_oracle.py:2883)
- trap が最適化や実装不良で全候補から消えた場合、plan は trace protocol の candidate `EXECUTION` reject に倒すよう読める。trusted control でも再現する欠陥は infrastructure `UNAVAILABLE` に分離すべきである。
- outer validator は単一 `sort(...)` 文しか閉じず、lambda 内の任意 C++ を制限しない。[sort_swo_oracle.py:523-540](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2076-t493-sort-oracle-parent-reference/orchestrator/campaign/sort_swo_oracle.py:523)
  候補が trap helper を直接呼び、stack／return address を偽装する攻撃に対して、plan の「trusted return address 照合」だけで十分という証明が無い。

fork 案は小さく見えるが同じ保証を持たない。

- 子の exit status は候補が `_Exit()` して偽造でき、comparator の正常 return を証明しない。
- 1 candidate 当たり 2 corpus × 3 order × 648 比較なので、比較ごとの fork は最大 **3,888 process**。現行 2 秒 timeout と両立しにくい。
- D825 が却下した「fork 後に fd を閉じる」能力境界にも再接触する。

より小さくするなら、broker が trusted `noinline` comparator wrapper の entry／return に外部 breakpoint を置く prototype は検討余地がある。ただし hostile control-flow の証明は依然必要で、今 wave の確定案とはみなせない。別案は verified IR へ受理言語を縮めることだが、これは別裁定である。

## B7

**判定: refuted。**

アンカー表の実差分:

- A2: `_TU_PREFIX:764` は正しいが、`Known residual` は実際には [sort_swo_oracle.py:916-924](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2076-t493-sort-oracle-parent-reference/orchestrator/campaign/sort_swo_oracle.py:916)。`:900 前後` はややずれている。
- A7: `_sort_entry:483` は正しいが、実際の comparator 型検査は `:493-494` と `:524-525`。検証側 `_validate_schema` には comparator 検査自体が無い。
- A9: 掲載された direct consumer の行番号は概ね正しいが、B2 の floor campaign、binary admission、ratified freeze を落としており「実アンカー全件」ではない。
- A10: fixture の `:17-46` は raw receipt の途中で終わる。guarantee boundary は `:61`、outer ID は `:67`、portable receipt は `:74-107` まで続く。[s8b_floor_evidence_fixture.py:40-107](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2076-t493-sort-oracle-parent-reference/orchestrator/tests/s8b_floor_evidence_fixture.py:40)
- A11: `FROZEN_MANIFEST:41` という位置は正しいが、held 中は known_axes bytes を検査しないため「凍結 bytes 不変の実効関門」という役割が誤り。
- A1、A3〜A6、A8 は実コードと概ね一致する。

P1-b は半分だけ正しい。

- `relation[]` は [sort_swo_oracle.py:946](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2076-t493-sort-oracle-parent-reference/orchestrator/campaign/sort_swo_oracle.py:946) で書かれるだけで、報告 frame には読まれない。
- 一方 `active_order` は lhs/rhs の relation 添字を決める。[sort_swo_oracle.py:939-946](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2076-t493-sort-oracle-parent-reference/orchestrator/campaign/sort_swo_oracle.py:939)
  broker も自身の order を使って matrix を canonicalize する。[sort_swo_oracle.py:1425-1438](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2076-t493-sort-oracle-parent-reference/orchestrator/campaign/sort_swo_oracle.py:1425)
  候補が worker 側 `active_order` を変えれば、実 comparator 入力と broker が解釈する cell がずれる。従って「報告経路に効かない」は明確に誤りである。

## scope 裁定への推奨

現 plan のまま author 段へ進めないことを推奨する。D1271 が同一変更単位を要求するため、T-493 だけを先行 land するのも避ける。

今 wave に残す確定範囲は次である。

- 実在する 15 comparator のみの private authority。
- balanced／write-heavy／read-heavy の生成時 binding と `_validate_schema` binding。
- 集合外、name/value 不一致、`active_write_set`、`active_order` の直接負例。
- 採用する oracle 機構の contract bump、portable receipt、critic、全 consumer closure。
- legacy-v4 は追加しない。

裁定パッケージへ送るもの:

- frozen JSON bytes 不変と generator SHA pin 不一致のどちらを優先するか。
- ptrace trap 状態機械を本 wave の実装として承認するか、broker breakpoint prototype または verified IR へ戻すか。
- ptrace 不可時を明示的 `UNAVAILABLE` とし、trusted trap 欠陥と candidate protocol 違反をどう分離するか。
- stock=`None` は実 artifact が無いため不採用とする確認。

## 見落とし

- 現 freeze と generator SHA の不一致は今回の変更前から既に存在する。既存 test 自身も実 frozen artifact の drift に非依存と明記している。[test_s1_known_axes_freeze.py:549-557](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2076-t493-sort-oracle-parent-reference/orchestrator/tests/test_s1_known_axes_freeze.py:549)
- ptrace 案は「候補が trap helper を名前で呼べない」ことを暗黙に期待してはいけない。D825 の隠蔽非依存原則と同様、helper 名、RIP、return address が全て候補に既知でも破れない証明が必要である。
- `SORT_SWO_GUARANTEE_BOUNDARY` を保証側へ動かす前に、trusted control で同じ trace が成立し、直接 helper 呼出し・順序飛ばし・return address 偽装が全て赤になることを独立に示す必要がある。現 plan の負例一件では足りない。