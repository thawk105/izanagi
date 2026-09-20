## 結論と読了範囲

**P1・P2・P4・P5 の方向を採用し、実装の基本編集面は gate module とその test の 2 file に限定する案です。** ただし、P6 の「総数だけで全箇所観測を保証できる」という解釈と、P7 の m4・m5 は補正が必要です。

指定された射影 3 資料、gate、test、consumer、fixture、driver、patch を読みました。書き込み・pytest・実 TU 前処理は行っていません。以下の実測値は親資料の記録であり、本段で再現した結果ではありません。

行番号は現行 worktree 基準です。以下では次を略記します。

- **G** = [orchestrator/campaign/condition_meaning_gate.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-witness-requested-us/orchestrator/campaign/condition_meaning_gate.py)
- **T** = [orchestrator/tests/test_condition_meaning_gate.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-witness-requested-us/orchestrator/tests/test_condition_meaning_gate.py)

## 現行挙動

| 現物 | 確認した契約 |
|---|---|
| G:147–150 | REQUESTED_US は既に supply domain 内。cache route、owner は `cc/silo/transaction.cc`、patch は `silo-backoff-requested-us.patch`。変更不要。 |
| G:258–344 | 枝選択登録は 21 macro。主宣言は 2-tuple、箇所数は別 mapping、未指定は 1。 |
| G:1010–1033 | 通常の `#if` は要求 1／既定 0、かつ主 `source_rel in spec.owner_tus` が条件。NOINLINE の header 宣言だけ既存特例。 |
| G:690–707、3219–3226 | 宣言を登録簿と等値照合する。副 file 用に偽の `ConditionalBranchMeaningDeclaration` を作ってはいけない。 |
| G:2931–2988 | 指定した 1 file を no-follow で capture し、その本文と `CapturedFileEvidence` を返す。 |
| G:2991–3030 | 逐語一致した N 箇所すべてに同じ selected／completed marker を挿入する。N=1 の不一致は従来 reason、N>1 は site-count-mismatch。 |
| G:3044–3094 | 主 file が owner TU なら浅い鏡像。それ以外は深い鏡像。現在は計装 file を 1 個しか書かない。 |
| G:3356–3376 | 要求・対照の総数を `(N·v,N)` と完全一致で判定。 |
| G:3981–4062 | green schema の key 集合、登録簿、source digest、観測数を再検証する。 |
| G:817–841 | dataclass の通常 field は既定値が `None`／空 tuple でも canonical JSON に出る。値による省略はない。 |

patch の逐語箇所は `patches/silo-backoff-requested-us.patch:29,41,60,178`。header の signature／return と、owner の counter／abort 内です。fixed→requested-us の順は `backoff_requested_us.py:1087,1105` と一致します。

NOINLINE fixture は `supplied/cc/silo/transaction.cc:12–15`、stock 側 `:7–10` で関数本体から header を include します。この fixture と既存の深い鏡像経路は維持します。

## 最小変更：宣言・計装・shadow

**宣言形は P1 の別 mapping を採用します。**

| 案 | 判断 |
|---|---|
| 主 2-tuple を維持し、副 file を別 mapping | 採用。既存 21 entry の値・順序・bytes と consumer 契約を維持できる。 |
| 登録簿 value を tuple of tuples に変更 | 不採用。既存 consumer、宣言等値検査、factory まで変更が波及する。 |
| `_CONDITIONAL_BRANCH_SITE_COUNTS` を file 別 mapping に変更 | 不採用。既存の整数契約と S1 helper を変える必要がない。 |

G:323 の直前に主 entry を末尾追加し、G:324–327 に主 file の `2` を追加します。副 mapping はその直後に置きます。

```python
# 主登録簿の末尾
"BACKOFF_REQUESTED_US": (
    "cc/silo/transaction.cc", "#if BACKOFF_REQUESTED_US",
),

# 主 file の箇所数
"BACKOFF_REQUESTED_US": 2,

# 新しい副 file 宣言
_CONDITIONAL_BRANCH_COMPANION_SITES = {
    "BACKOFF_REQUESTED_US": (
        ("include/backoff.hh", "#if BACKOFF_REQUESTED_US", 2),
    ),
}
```

副 file は factory の主 entry に渡さないので、G:1026–1028 の owner 条件に抵触しません。`DefineSpec`、factory の要求値条件、宣言 dataclass は変更しません。

`_declared_site_count`（G:330）の意味は**主宣言 file の N**のまま維持します。「owner TU の N」と呼ぶと、主宣言が header の NOINLINE には不正確です。新しい `_declared_total_site_count(macro)` は主 N と副 mapping の N の和を返し、G:3356 と G:4039 の 2 箇所だけを総数へ切り替えます。

総数を既存 helper に持たせる案は helper を減らせますが、S1 の `test_s1_direct_comparison.py:719–729` が owner に 4 箇所を作ることになり、宣言した「owner 2＋header 2」と一致しません。

具体的な変更点は次のとおりです。

| 現行位置 | 変更 |
|---|---|
| G:2991–3001 | `_instrument_declared_owner_source` の既存 2 引数呼出しを保持し、対象 file を選ぶ keyword を追加。対象の directive／N は主登録または副 mapping から得る。副宣言 object は作らない。 |
| G:3002–3012 | REQUESTED_US の不一致だけ file を含める。例：`detail="… include/backoff.hh"`、`expected="include/backoff.hh:2"`、`observed="include/backoff.hh:1"`。既存 macro の reason/detail/expected/observed は逐語維持。 |
| G:3228–3231 | 主＋副を順に capture し、file ごとに計装。capture は既存 no-follow 関数をそのまま再利用する。 |
| G:3033–3044 | shadow writer に副 file の `{rel: text}` keyword を追加。内部で主を含む mapping を作り、浅い経路は「主==owner かつ副なし」に限定する。 |
| G:3085–3093 | 深い鏡像では mapping にある全 file を symlink 対象から除き、全計装本文を書いてから owner path を返す。 |
| G:3287–3290 | 全計装 file を同じ shadow writer 呼出しへ渡す。 |
| G:3102–3204 | owner compile operand の置換、通常の前処理、総 marker 計数は維持。追加 subprocess は不要。 |

「symlink を作った後に `write_text` で上書き」は禁止です。元 source への書き込みになり得るため、G:3088 の除外対象を**全計装 file**へ広げる必要があります。

浅い鏡像では、実 TU の `include/transaction.hh` が通る directory symlink の先で `../../../include/backoff.hh` が元 root へ解決されます。また root の `include` 自体も symlink になり得ます。主が owner でも副がある場合に深い鏡像を使う理由はここです。

## 全箇所観測の境界と P6 への補正

要求された個別負例は、総数の完全一致だけで拒否できます。

| 構成 | 要求／対照の観測 | G:3370–3376 |
|---|---|---|
| owner 2＋header 2、header を 1 回 include | `(4,4)/(0,4)` | green 候補 |
| header 未 include | `(2,2)/(0,2)` | mismatch |
| pragma once なしの header を合計 2 回 include | `(6,6)/(0,6)` | mismatch |
| header を合計 3 回 include | `(8,8)/(0,8)` | mismatch |
| owner の 1 箇所を外側条件で無効化 | `(3,3)/(0,3)` | mismatch |

**ただし、総数一致から各箇所の観測を一般には導けません。** 静的に構成できる反例は、owner の 2 箇所を外側 `#if 0` で無効にし、pragma once のない header を 2 回 include する入力です。各 file の逐語箇所数は 2 のままですが、header の 2 箇所がそれぞれ 2 回観測され、総数は `(4,4)/(0,4)` になります。

したがって「未到達箇所はすべて red」という I5 を保つには、次の限定補正を段 3 に提出します。

- **複数 file macro に限り、file・site ごとの識別 marker を追加する。**
- G:3019–3028 の計装で、既存総数 marker に加えて各箇所固有の selected／completed token を同じ位置へ置く。
- G:3184–3200 で同じ前処理出力から各 token を数える。期待は箇所ごとに `(v,1)`。
- 総数が不一致の入力は従来どおり G:3370 で拒否し、総数が一致した場合にも個別不一致を拒否する。生成 token の collision も G:3013 相当で検査する。
- 既存 21 macro の計装本文・argv・record は変えない。既存 observation field、追加 subprocess、新 module は不要。

これは未宣言条件の一般走査ではなく、**宣言した 4 箇所の識別**です。実 patch の `#pragma once` は親資料により確認されていますが、gate が受け取る別本文まで一回性が保証されるわけではありません。補正を採用しない場合、P6 の個別負例は成立しても、I5 の無条件な全箇所主張は成立しないと明記すべきです。

## Evidence と schema

**案 A を採用します。** REQUESTED_US の green evidence にだけ `companion_sources` を追加し、既存 proof_kind を維持します。

副証拠は登録順の tuple とし、各要素を次の厳密な mapping にします。

```text
source_rel
start_directive
site_count
source_sha256
source_file       # CapturedFileEvidence
```

輸送方法も固定します。G:3215、3378–3394 の private 関数の返り値を、既存 `CompileTimeBranchSelectionEvidence` と副証拠 tuple のペアに変更し、G:3427 で unpack します。既存 dataclass に field を足しません。静的検索上、この関数の production caller は evaluator の 1 箇所で、T:1529 の直接呼出しは例外検査です。

G:3450–3473 の現行 dict をまず同じ内容で組み立て、副宣言があるときだけ副 key を加えます。副証拠を後から再 capture せず、**計装に用いた capture 結果そのもの**を運びます。

G:3981–3993 と G:4024–4035 の近傍で次を検査します。

1. 副宣言の有無は `record.macro` から登録簿で決める。record の key の有無から決めない。
2. 副宣言ありなら `companion_sources` 必須。なしなら同 key は unexpected。
3. 外側 tuple の型・長さ、各 mapping の key 集合、登録順を完全一致で検査。
4. `source_rel`・`start_directive`・`site_count` を独立した登録値へ束縛。`site_count` は exact int とし bool を拒否。
5. `source_file` の exact type、relative_path、sha256 を当該 row へ束縛。
6. digest 形式、before／after／path_after の identity と等値を現行 source_file と同様に検査。
7. 総数は evidence の申告値ではなく登録簿から導出し、G:4039–4062 の観測検証に使う。

案 B の別 proof_kind は、同じ owner-TU 枝選択という主張に別の validator 分岐を増やします。今回の差は登録された source 集合なので不要です。

案 C の optional field は不採用です。G:818–823 は既定値を省略しません。`metadata={"canonical": False}` という除外機構はありますが、それを使って証拠を canonical record の外に置く案も今回の目的には合いません。

## Test 設計と具体正負例

fixture は **T:241–290 の builder を拡張**し、新しい fixture directory は作りません。REQUESTED_US の分岐を G の登録簿参照より前に置き、登録削除変異でも fixture が `KeyError` にならないようにします。

T:59 の既存期待表は維持し、独立した複数 file 期待表に以下を literal で宣言します。

```text
REQUESTED_US:
  主: cc/silo/transaction.cc, #if BACKOFF_REQUESTED_US, 2
  副: include/backoff.hh,     #if BACKOFF_REQUESTED_US, 2
  対照: 0
```

fixture の N を production mapping から生成してはいけません。owner と header に別名の本文を両腕へ置き、対照の前処理結果も空にならないようにします。owner→`include/transaction.hh`→`../../../include/backoff.hh` の中継を生成し、D1613 の `..` 解決を通します。負例用 header には pragma once を置きません。

新設 node の予定名と期待を固定します。

| Node | 検査 |
|---|---|
| `test_requested_us_multifile_supply_meaning_and_admission` | supply／meaning green、`(4,4)/(0,4)`、admitted、未確立空。副証拠は header の capture と一致。 |
| `test_requested_us_multifile_site_count_mismatch[owner]` | owner の 1 箇所欠落。owner を指す expected 2／observed 1。 |
| `test_requested_us_multifile_site_count_mismatch[header]` | header の 1 箇所欠落。同様に header を指す。 |
| `test_requested_us_multifile_site_count_mismatch[header-verbatim]` | header の 1 行だけ `#if (BACKOFF_REQUESTED_US)` に変更。逐語不一致で拒否。 |
| `test_requested_us_multifile_include_counts[missing]` | header 未 include、completed 2/4、mismatch。 |
| `test_requested_us_multifile_include_counts[twice]` | header 合計 2 回 include、completed 6/4、mismatch。 |
| `test_requested_us_multifile_include_counts[pragma-once]` | pragma once ありで 2 回 include、実観測 4/4、green。 |
| `test_requested_us_multifile_assert_requires_total_count` | missing-include 入力を `_assert…` に直接渡す。schema に依存せず総数拒否を検査。 |
| `test_requested_us_multifile_shadow_instruments_all_files` | 両 file が通常 file、中継 directory が実体、元 file の bytes 不変。 |
| `test_requested_us_multifile_uninstrumented_header_is_red` | shadow 作成後の副 file 本文だけを元本文へ戻す test 内注入。completed 2/4 で拒否。 |
| `test_requested_us_multifile_rejects_compensated_missing_sites` | owner 不活性＋header 二重 include。総数は 4 でも個別観測で拒否。 |
| `test_requested_us_multifile_green_schema[mutation]` | 副 key 欠落、空 tuple、重複 row、誤 path／directive／N／digest／identity、row の余分な key を拒否。 |
| `test_single_file_green_schema_rejects_companion_sources` | SORT の green に空の副 key を足しても unexpected。 |
| `test_requested_us_cli_establishes_multifile_meaning` | `condition_gate_cli` を直接呼び、3 record と未確立空を検査。新 subprocess 呼出しは足さない。 |

schema test は T:1571–1578、2086–2097 と同じく、変更後 evidence から public record を作り直して `require_issuer=False` で検査します。古い digest や issuer 欠如に遮られた失敗を schema の検出と数えません。

patch 束縛は T:293–328 を拡張します。REQUESTED_US について全 `+++ b/` を走査した matches が、header pair×2＋owner pair×2 と一致することを独立期待で確認します。他 file の余剰一致も拒否します。既存 macro の `[pair] * count` は維持し、返す主 pair も維持できます。

T:1034–1052 は副 file の fixture 本文と副 mapping も照合。T:1359 の全 registry 正例は REQUESTED_US の期待総数を独立期待表から 4 とします。T:1990 の非対値例にも REQUESTED_US を追加します。

## 変異候補と失敗 node の予測

以下は**実装後の予定位置に対する置換設計と静的予測**です。最終 node 完全集合は親の probe 後に確定します。`R` は `BACKOFF_REQUESTED_US` を表します。

| ID | G の置換位置・内容 | 主な失敗 node／帰属 |
|---|---|---|
| m0 | G:327 後の新副 mapping 行末へ comment を追加 | 等価。全 node が通るべき。 |
| m1 | 新副 mapping の header N `2 → 1` | `test_compile_time_branch_registry_and_fixtures_are_bound_to_real_patches`、`test_compile_time_branch_selection_accepts_each_registry_macro[R]`、新 multifile 正例。独立 fixture は 2 箇所のため宣言不一致。 |
| m2 | G:3092 相当の mapping 書出しで、副 file を計装本文でなく元本文にする | 新 multifile 正例、shadow 検査、全 registry 正例 `[R]`。後段で completed 2/4。file 自体を消して include failure にする変異とは区別する。 |
| m3 | G:3356 の新 `_declared_total_site_count(request.macro)` を `_declared_site_count(request.macro)` に戻す | 新正例は期待 2 による過剰拒否。`test_requested_us_multifile_assert_requires_total_count` は missing-include の 2/2 を直接 assert が通して失敗。公開 evaluator では schema の総数 4 が別途拒否する。 |
| m4 原案 | G:3002–3012 の file 別不一致検査を副 file に限り通過させる | `site_count_mismatch[header/header-verbatim]` の reason 検査が落ちる。ただし後段は引き続き拒否するため、これだけで family 受理集合の変化を立証できない。 |
| **m4′ 推奨** | G:3184–3200 に加える複数 file の個別 marker 等値検査を無効化 | `test_requested_us_multifile_rejects_compensated_missing_sites`。総数 4 の相殺入力が green へ転じる単一理由。 |
| m5 補正版 | G:3981 以後の副 schema 適用条件を、登録簿だけでなく `"companion_sources" in evidence` に依存させる。required 追加と副 row 検証を同じ誤った条件で囲む | `test_requested_us_multifile_green_schema[missing]`。副証拠を省いた public green record が受理される。 |
| m6 | G:323 前の R 主 entry を削除 | registry／patch 束縛、全 registry 正例 `[R]`、新正例、CLI、T:3067 の集合 pin。fixture を独立生成し、factory None／unestablished を観測する。 |
| m7 | G:4024 相当の副検証から `source_file.sha256 != row["source_sha256"]` の項だけ除去 | `test_requested_us_multifile_green_schema[digest]`。形式が正しい別 digest に片側だけ変更し、他の型・identity 検査を通す。 |
| m8 | G:3450–3473 の副 key 挿入条件を無条件にする | T:1607 の既存 key pin、全既存 macro 正例、新しい既存 serialization pin。通常は bytes 比較以前に `_issue_arm_record` の schema 検査で拒否される。過剰拒否として帰属する。 |

m4 原案は診断契約の検査として残せますが、「受理集合を変える変異」の成果には数えません。m5 も required 集合から key を消すだけでは、後続の参照で例外になる可能性があり、欠落証拠の受理を検査できません。

m1・m2・m6・m8 は単一の変更から複数 node が落ちます。fixture 生成の `KeyError`、schema による二次拒否、目的の判定箇所での失敗を台帳で分離します。

## 不変条件と既存 pin の波及

**I1 は「schema 不変」と「実評価結果の差分」を分けて検査します。**

T:1561 は count/value/argv 変異検査です。実際の key pin は **T:1607–1626** にあります。この test を既存 21 macro に広げ、次を追加します。

- `CompileTimeBranchSelectionEvidence` も含む 3 dataclass の field 集合を literal で固定。
- 既存 green evidence の key 集合を literal で固定。
- 決定的な既存 evidence を `_assert…` の返り値として与え、evaluator が発行する canonical record を変更前に採取した固定期待と比較する serialization test。期待値を production dataclass の field 列挙から作らない。
- 実 compiler 経路は既存正例・負例と、親の変更前後 leaf 比較で別に担保する。

serialization test だけでは source capture や shadow の挙動差を証明できません。逆に、key 集合だけでは reason・値・nested field の差を検出できません。

親の I1 比較手順は次のとおりです。

1. base `482f19b88` と最終実装を、同じ実 patch 木・同 driver-id・同 configure・同 toolchain で実行。
2. SORT 1/0、NOINLINE 1/0 の supply／meaning／admission をそれぞれ比較。
3. 一時 root を役割別 placeholder に正規化し、その影響が伝播する `record_digest`／`record_id`／`admission_digest` を区別して報告。
4. key 集合、source identity/hash、dependency closure、前処理 digest/bytes、counts、define_value、reason、proof_kind は一致を要求する。hash 全般を一括除外しない。
5. 既存 21 macro 全体の比較は、同じ合成 source roots を変更前後で再利用すれば実 submodule なしでも可能。ただし fresh copy 間では inode/mtime 等も変わるため、source roots を作り直さない。

実行間の一時 path が異なる raw canonical JSON の完全一致を主張してはいけません。I1 の「1 byte も変わらない」は、同一入力での serialization 契約と、許可した揮発差分を除く実 record 比較に分けて記録します。

その他の不変条件・pin は次の扱いです。

| 対象 | 扱い |
|---|---|
| G:77–256 `DEFINE_SPECS` | diff なしを確認。supply domain は 40 のまま。 |
| D1491 | G:678、3933、3952、4284 の BACKOFF_FIXED 固定を維持。T:2027 の CLI 旧経路拒否に R も加える。 |
| 規律 2 | R の同一要求 1/0 は unestablished admit→green admit／red reject。非対値は factory None のまま。他 macro の factory・供給・意味条件を変えない。 |
| T:33–55 | R を末尾追加。既存 21 件の順序を保存。 |
| T:3067 | meaning 集合は独立列挙の追加に追随し 23。supply 集合は不変。 |
| G:13、T:3305 | `Twenty-one`→`Twenty-two`。test 名の `38` は本題外なので改名不要。 |
| T:1964 | 未登録例は SS2PL_LOCK_IMPL のまま。 |
| T:1154、1199、2013、2100 | NOINLINE の inert・1/0・factory・schema 契約をそのまま回帰検査。 |
| MOCC consumer 3 件 | `test_mocc_mutation_proof.py:177`、`test_mocc_template_proof.py:267`、`test_mocc_proof_surface.py:569` は変更不要。前 2 件は tuple 比較、後者は unpack。 |
| S1 helper `:719` | 主 N の意味を保つ。将来 R を生成する場合には header 生成も必要であり、この helper を複数 file 対応済みとは主張しない。 |
| B-4 static inventory | production module を追加しないため件数 pin の変更不要。 |
| spawn inventory `test_ccbench_spawn_sites.py:123` | `_run_process` の subprocess site 数 1 を維持。 |

## 所有 path と配線しない根拠

author の基本編集面は次の 2 file です。

1. `orchestrator/campaign/condition_meaning_gate.py`
2. `orchestrator/tests/test_condition_meaning_gate.py`

既存 `_SUPPLIED`／stock fixture、patch、driver、MOCC consumer、S1 helper、B-4 inventory、spawn inventory は編集対象にしません。shadow writer の引数を既存呼出し互換で拡張するため、T:1256、1287 の header shadow test も現形を保持できます。

**driver は配線しません。** 根拠を分けると明確です。

- `backoff_sweep.py:194–209` は非 FIXED に `declaration=None`。helper 自体は `:215–228` で admission を作り、返しています。
- `backoff_requested_us.py:127–140` は helper の返り値を返しますが、実 caller の `:1107–1111` がそれを捨てています。続く `source_digest.resolve_evidence` は別証拠で、condition admission の永続化ではありません。
- `backoff_sweep.py:452–467` も helper の返り値を捨て、ここで要求しているのは FIXED のみです。

したがって「helper が admission を作らない」ではなく、**対象 driver の成果物へ載せていない**ことが D1492 の根拠です。

CLI は G:4291–4292 で既に factory を呼びます。機構実装と登録の追加により、CLI 配線変更なしで R 1/0 が評価対象になります。ただし登録だけで green が保証されるわけではなく、供給・4 箇所の活性・観測一致が条件です。

## 段 6 レビュー観点と親 brief への反論

段 6 では次を優先します。

1. **全箇所性**：総数が一致する相殺入力を拒否するか。未 include と二重 include を別々に試すだけで済ませない。
2. **shadow**：全計装 path が通常 file で、元 source に書き込まず、実 include 経路の `..` が shadow に留まるか。
3. **証拠の対応**：capture した副本文を計装し、その同じ capture evidence を record に載せているか。
4. **schema**：副証拠の要否を registry で決め、row の N や digest を自己申告で通していないか。
5. **互換性**：既存 21 entry、dataclass fields、reason/detail、単一 file shadow 経路と canonical key 集合が変わっていないか。
6. **変異の帰属**：直接 assert と public schema を別々に検査し、二次防壁の拒否を一次防壁の成功に数えていないか。
7. **実 TU**：最終 production 登録簿で、pin `e9e477ca1`、fixed→requested-us、official 同形供給により login／計算ノード双方の `(4,4)/(0,4)` と admission を取得したか。
8. **configure 境界**：BACK_OFF=0 の completed 3/4 を拒否するか。BACK_OFF を companion define に足していないか。

親 brief への具体的な修正提案は以下です。

- **P1・P2・P4・P5 は採用。** P4 の呼称だけ「owner」から「主宣言 file」へ正確化する。
- **P6 は部分採用。** 個別の未 include／重複 include は総数で拒否できるが、相殺まで fail-closed とはいえない。宣言箇所の識別を複数 file macro に限定して追加する。
- **P7 の m4 は原案のまま受理集合変異に数えない。** 個別観測を無効化する m4′へ置換する。
- **P7 の m5 は required 集合だけの削除では不十分。** 欠落 key が実際に受理される schema 条件の変異へ具体化する。
- **m8 は bytes pin より先に schema で落ち得る。** 正しい検出だが、検出箇所を偽って報告しない。
- **I1 の raw bytes と leaf 比較を混同しない。** 親資料自身が許可する一時 path と派生 digest の差を明示する。
- **header を合計 2 回 include した期待は 6/4。** 8/4 は合計 3 回の場合。
- **P8 の既取得 login-pre は比較条件を照合して使用。** 最終 production の実 TU 実測を、本段の静的確認で代替しない。

親が行う焦点走は `tools/run_tests.py --force-dispatch` 経由とし、gate test、MOCC consumer 3 件、S1、spawn inventory、関連 static inventory を含めます。受入・docs／agent checker・commit 後 provenance は親の段階で実施し、本段では実走済み扱いにしません。

## 総括

最小の基本形は、**主 2-tuple 維持＋副 mapping＋同一の深い shadow＋REQUESTED_US 限定の副 evidence key**です。既存 21 macro の経路を保ち、driver は配線しません。

段 3 の主要論点は、総数の相殺を塞ぐ箇所識別と、m4／m5 の変異設計です。ここを補正してから author へ渡すことを推奨します。全作業は読取のみで、編集・テスト実走はしていません。