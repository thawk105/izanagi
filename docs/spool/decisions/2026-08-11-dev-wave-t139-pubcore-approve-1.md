---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-11
wave: dev-wave-t139-pubcore-approve
seq: 1
---

## {{D:t139-publication-core-approval}}. 公表 core v2 と source 追補 B v2 の exact bytes、および将来の追補 P の p01 / p02 の値だけを承認 payload として固定する

**決定:** 次の payload は、**これを canonical 台帳へ fold した commit で初めて発効する。**
fold 前に spool fragment として存在する間は、いずれの blob の authority も投入可否も変えない。
その fold commit を `F_p` と呼ぶ。後続 land が凍結する追補 P は `F_p` を `core_ref.commit` として
literal で持つ。**resolver は manifest を信用する前に、`F_p` の `docs/decisions.md` から本 payload を
読み、role 集合・三つ組集合・`document_relations` の全 field・承認済み値集合・閉包条件が
本 payload と exact 一致することを要求しなければならない** (manifest だけを trust root にすると、
`approval_fold_commit` を保った偽 manifest が自分の宣言値で自己整合してしまう)。
`document_relations` を照合対象から外すと、三つ組と値を一致させたまま `depends_on` / `satisfies` /
`pins_source_study_one_way` だけを差し替えた manifest が通る。

```text
decision_kind = t139-publication-core-approval/v1

prior_exact_byte_authority = none
  本 payload より前に、公表 core と source 追補 B の exact bytes を承認した canonical decision は
  存在しない。D262 と D282 の approved_blobs にこの 2 role は無い。

procedural_history:
  過去の裁定 C-2 / C-4 は「現追補 B を source core 用として承認・発効する」「同一 land で新 core を
  承認する」という手続きの選択であり、canonical worklog が記録するとおり実行されていない。
  本 payload はこの選択の履歴を改変せず、supersede もしない — 失効させるべき exact-byte 承認が
  存在しないためである。

source_core:
  path   = output/insights/2026-08-07_t139-mainrun-design/preregistration.md
  commit = 88d68f9127b31df5aafc3d59607896626a1652e8
  sha256 = ac939af4de87dff0cd3964e37cef975d57919a709d57f4e9523c8b6a9fcd60e9

source_study_inputs:
  参照のみ。本 payload はこれらを再承認しない (承認の正本は D282)。
  addendum_a
    path   = output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md
    commit = 622bd786191d40bda388596fa2adbf119ee84c9a
    sha256 = f7db96ce8ecb12359fedf56baea24939c629d4d16a1ec167c183425ea198cfec

document_relations:
  source_addendum_b:
    role           = addendum_b
    satisfies      = source_core.main_admission (requires_addendum_a_and_b)
    depends_on     = source_core
    independent_of = publication_core
  publication_core:
    role        = independent_publication_core
    study_label = rf_partial_recovery / paired_cluster / individual_publication / core
    pins_source_study_one_way = [ source_core, source_study_inputs.addendum_a ]
    note = 独立 study の core であって source core の追補ではない。ただし入力となる source study を
           上記 2 つの三つ組で片方向に同定する。core 単独では公表解析は完結しない。
  future_publication_addendum_p:
    role          = addendum_p
    satisfies     = publication_core.analysis_admission (requires_addendum_p)
    depends_on    = publication_core
    blob_approved = false
    required_core_ref:
      path   = output/insights/2026-08-11_t139-pubcore-stage2/publication-core-v2.md
      commit = symbolic:F_p   (本 decision の fold commit を指す記号。hex40 の literal ではない)
      sha256 = ad326dae70584d86470ff861e9bfd517b4f5b8406247f8047ae6cdb3ddabef67

approved_blobs:
  publication_core
    path   = output/insights/2026-08-11_t139-pubcore-stage2/publication-core-v2.md
    commit = 66934dda7f28893110a64a2011e213c2bda5e821
    sha256 = ad326dae70584d86470ff861e9bfd517b4f5b8406247f8047ae6cdb3ddabef67
  source_addendum_b
    path   = output/insights/2026-08-11_t139-pubcore-stage2/addendum-b-v2.md
    commit = 25a66d2042a4fff1021e033c23fc2b814a735de9
    sha256 = ad12b60d29bb94ff67c3302b0779cb4765cd1c77768149d7cf6587698febb048

approved_values_for_future_addendum_p:
  approval_scope = values_only
  p01:
    candidate_cap       = 1
    admissible_ordinals = [ 1 ]
  p02:
    familywise_alpha          = 0.05
    spending_domain           = k = 1, 2, 3, …
    alpha_pub_k               = 0.05 / (k * (k + 1))
    current_k                 = 1
    alpha_pub                 = 0.025
    unspent_tail_reclaim      = false
    unspent_tail_redistribute = false
  p03_approved             = false
  addendum_p_blob_approved = false

  value_projection:
    承認した値と追補 P 側の field の対応を写像として固定する。左が本 payload、右が追補 P の field。
    **本表の 9 行が照合対象の全体である。**
      p01.candidate_cap             <-> p01.candidate_cap
      p01.admissible_ordinals       <-> p01.admissible_ordinals
      p02.familywise_alpha          <-> p02.familywise_alpha
      p02.spending_domain           <-> p02.spending.domain
      p02.alpha_pub_k               <-> p02.spending.alpha_pub_k
      p02.current_k                 <-> p02.current_study.k
      p02.alpha_pub                 <-> p02.current_study.alpha_pub
      p02.unspent_tail_reclaim      <-> p02.unspent_tail.reclaim
      p02.unspent_tail_redistribute <-> p02.unspent_tail.redistribute
    comparison_unit:
      数値 (familywise_alpha / alpha_pub / candidate_cap / current_k) は 10 進の数値として
      比較する。表記の差は問わない (0.025 と 2.5e-2 は一致とする)。
      admissible_ordinals は順序を無視した整数集合として比較する。
      真偽値 (unspent_tail_reclaim / unspent_tail_redistribute) は真偽値として比較する。
      **spending_domain と alpha_pub_k は canonical form との文字列一致で比較する。**
      空白の連続を 1 個へ畳み、前後の空白を落としたうえで比較する。canonical form は次で固定する。
        spending_domain canonical form : k = 1, 2, 3, …
        alpha_pub_k canonical form     : 0.05 / (k * (k + 1))
      数式の同値判定を resolver に委ねない — 一般には決定不能であり、実装ごとに受理が分岐する。
      別表記を使いたい場合は、後続の canonical decision が canonical form を更新する。
    not_covered_by_this_approval:
      追補 P 草案が持つ次の field は、本 payload の承認範囲に**含まれない**。
        p01.immutable_in_this_addendum / p02.affects_primary_alpha
      裁定が承認したのは上記 value_projection に挙げた値だけである。これらの field の値は
      追補 P を凍結する後続 land が core 適合として別途確認する。
      **本 payload の一致検査はこの 2 つを見ない** (任意の値を許すという意味ではない)。
      したがって「payload に無いから追補 P が一致不能」にはならない。

historical_candidates_rejected_for_role:
  publication_core role:
    path   = output/insights/2026-08-10_t139-publication-core/publication-core.md
    commit = db5e8dfce0449a6df5cb2e1ed494eff406600187
    sha256 = 9b7bc1932dd76e0e72f5cd98f9de2e01a62c4a065e8ac0e0eb6a59e5a3f66a64
  source_addendum_b role:
    path   = output/insights/2026-08-09_t139-addendum-b/addendum-b.md
    commit = 8e9a5b4dddfb85f7d31f671090cd24a7a4192e42
    sha256 = 5071acbd9db18f022cb9603acef3a8cd3394ed17de80cc794468c1b1f5baa384
  note = これらは exact-byte 承認を一度も持たない。**本 payload が承認する role の対象ではなく、
         本 payload に照らす限り resolver はこれを拒否しなければならない。**
         歴史的な手続き選択の記録は改変しない。
         この拒否は永久ではない — 後続の canonical decision がこれらを明示的に承認すれば、
         その decision が本 payload を supersede する (下の scope を見よ)。

exact_closure:
  scope = 本 decision が承認する集合について、**明示的な後続 canonical supersession があるまで**。
    本節は将来のあらゆる manifest を無期限に縛る立法ではない。後続の canonical decision が
    role を追加・変更・失効させたときは、その decision が新しい閉包を定める。
  1. 本 payload が承認する approved_blobs は、上記 2 role・2 三つ組の集合**ちょうど**である。
     余剰 role、role の欠落、同一 path の別 digest は、本 payload に照らす限り解決失敗とする。
     allowlist であり denylist で代替しない。
  2. 承認は path ではなく (path, commit, sha256) の三つ組で決まる。**digest が一致しない blob は、
     path が同じでも承認対象ではない。** 本 payload の作成時点で、承認対象と同じ path に
     次の非承認 blob が実在する。
       publication-core-v2.md : 45d83e7ab471ef9db0aaf9705168a333a8c317de06674fa23ef9164428d03065
       addendum-b-v2.md       : 0ea71fff11c0f4c939cab213021487758bf6016db522ea29a3a527d2ee1c0658
       addendum-b-v2.md       : 2313a26151975fe65e6586dec5676df92da209c68126296b55592ec6ab8834df
     本 payload の作成時点では、reachable な全 commit の tree を走査してこの 3 件が
     非承認 blob の**全件**であることを確認した (当該 2 path の unique blob は
     publication core が 2 個 = 承認 1 + 非承認 1、追補 B が 3 個 = 承認 1 + 非承認 2)。
     ただし履歴は伸びうるため、網羅を担うのは列挙ではなく 1. の allowlist である。
  3. approved_values_for_future_addendum_p の value field は exact に { p01, p02 } であり、
     その内訳と比較単位は value_projection が定める。
  4. 後続 land が凍結する追補 P の p01 / p02 は、F_p の docs/decisions.md が持つ本 payload の値と
     value_projection の写像・比較単位で一致しなければならない。一致しない追補 P を承認してはならない。
  5. 追補 P の blob と、確定後の p03 には、本 payload とは別の承認が要る。
  6. document_relations は**節全体**が本 payload と exact 一致することを要する。
     nested を含む全 field が対象であり、次はその**例示であって列挙ではない** —
     role / satisfies / depends_on / independent_of / pins_source_study_one_way /
     study_label / note / blob_approved / required_core_ref (その path・commit・sha256 を含む)。
     **括弧内に挙がっていない field も照合対象である。**節に無い key の追加も、
     節にある key の削除も、解決失敗とする。

operational_state_on_fold:
  addendum_p_blob  = not_approved
  p03              = not_determined
  pilot_submission = forbidden
  main_submission  = forbidden
  deny_basis       = 先行裁定 B8 (a) および本 payload の根拠となった裁定 Q3 (b)
  addendum_p_freeze_precondition =
    公表台帳の実体が確定していること。実体の同定は公表層実装 wave の裁定事項であり、
    それが済むまで追補 P を凍結してはならない。pilot もそれまで投入しない。
  source_main_run_gate = not_implemented
    「source 側の本走 gate の新設 (旧 b03 の投入前 admission の復元)」を公表層実装 wave の
    必須要件へ記載済みであることは確認した。**これは要件の記載であって gate の実装・検証ではない。**
    本 payload の fold は source 本走の admission を閉じない。

authority_field_note:
  fold 後も、承認した 2 文書の bytes は authority: none のままである。文書を編集すると
  承認した bytes ではなくなるため編集しない。**承認状態の正本は本 decision であって、
  文書内の envelope ではない。** 先行の source core も authority: none のまま発効している。

role_coupling:
  **「2 role は独立である」とは主張しない。** 1 つの decision に束ねた結果、次は実際に連結している。
    - 両者は同じ F_p で同時に発効する。
    - 本 payload の parse 失敗・trust root 失敗は両承認を同時に落とす。
    - exact_closure 1. の role 集合検査に両 role が入る。
  独立しているのは**承認の根拠**だけである — source_addendum_b が満たすのは source core の
  main_admission であり、publication_core の承認を前提としない (逆も同じ)。
  **片側だけを更新・失効・再承認する規則は、本 payload は定めない。**
  例えば source 追補 B の次版だけを承認する場合、publication_core の承認を preserve するのか
  同時に失効させるのかは、その承認を行う後続 canonical decision が明示しなければならない。
  後続 actor が本 payload から推測してはならない。
  なお追補 P が参照する F_p は publication_core の承認 fold としての F_p である。
  source_addendum_b の更新はこの参照を動かさない。

operational_boundary = """
この保証は、指定された一つの canonical local main、その Git common directory、
tools/dev_wave_land.py が同一 land lock 下で本 payload を fold した履歴、および F_p の
docs/decisions.md と指定 commit の tree を毎回再検査する trusted resolver / report の範囲に限る。
独立 clone、別 common directory、権威台帳外の投入、履歴を共有しない writer、
同一権限の非協調 writer、canonical main の外で作られた宣言は保証しない。
本 payload は、公表台帳の実体・予約の原子性・(root, ordinal) の一意性、resolver / producer /
validator / consumer の実装、source 本走および pilot の admission を保証しない。
"""
```

**理由:**

- **凍結承認は裁定だけでは発効しない。** 追補は `core_ref.commit` を「承認決定を canonical 台帳へ
  fold した commit」と逐語で定義しており、承認より前の内容 commit を書けば既存意味では
  永続的に解決失敗する。D282 が確立した 2 段 land (承認 payload を先に fold し、後続文書が
  その fold commit を literal で持つ) と同型にするしかない。
- **supersession として書かない。** 旧版 2 文書は exact-byte 承認を一度も持たない。
  過去の手続き選択を「承認」と型付けして失効させると、存在しない authority を台帳に生み、
  履歴 resolver が旧 blob を「一度承認済み」として扱う受理枝が増える。
  そこで `prior_exact_byte_authority = none` と `procedural_history` に分け、
  旧 blob は role 限定の拒否として書いた。
- **allowlist にする。** 同一 path には承認対象でない中間 blob が実在する (`exact_closure` 2. に
  実測値を挙げた)。旧 path だけを列挙する denylist では、同じ path の別 digest を落とせない。
  承認を三つ組で閉じ、集合ちょうどであることを resolver の要求にした。
- **2 つの core を書き分ける。** 追補 B は source core の `main_admission` が要求する `addendum_b`
  role を満たす従属文書であり、公表 core は独立 study の core である。ただし公表 core は
  入力 source study を片方向に pin するため、source core と承認済み追補 A の三つ組を
  参照として置いた (再承認ではない)。relation を書かないと、resolver は追補 B を
  `main_admission` へ結線できないか、別の追補 A を公表入力として受理しうる。
- **値の承認と blob の承認を分ける。** ユーザー裁定は追補 P の `p01` / `p02` の**値**を承認したが、
  追補 P の blob は承認していない (`p03` の確定条件が公表台帳の実体に依存し、実体は
  公表層実装 wave の裁定事項であるため)。`approval_scope = values_only` と
  `addendum_p_blob_approved = false` を併記し、後続 land が値を変えられないよう
  `exact_closure` 4. で `F_p` の値との exact 一致を要求した。
- **要件の記載を gate の完成と書かない。** 旧 `b03` が持っていた投入前 admission は再発行で失われた。
  その復元は公表層実装 wave の必須要件として記載済みだが、実装も検証もされていない。
  `source_main_run_gate = not_implemented` と明記しないと、本 payload の fold が
  source 本走 admission を閉じたと誤読される。
- **`authority: none` は発効の否定ではない。** 発効済みの source core も `authority: none` のままである。
  承認した bytes を保つには文書を編集できないため、承認状態の正本が本 decision であることを
  payload 自身に書いた。**これは規範であって機械強制ではない** — 強制する resolver は未実装であり、
  `operational_boundary` で保証対象外と明示している。
- **「exact 一致」の比較単位を定義した。** 定義しないと、同じ追補 P を承認する後続 land でも
  実装ごとに受理・拒否が分岐する。payload と追補 P では field 名が異なる
  (`current_k` ↔ `current_study.k` など) ため写像を固定し、数値は 10 進値、
  `alpha_pub_k` は定義域全点での関数一致、`admissible_ordinals` は順序無視の集合として比較する。
  裁定が触れていない field (`immutable_in_this_addendum` と `affects_primary_alpha`) は
  承認範囲外と明記した — そう書かないと、正規の追補 P が「payload に無い field を持つ」だけで
  一致不能になる。
- **spending の定義域は承認範囲に含める。** 定義域なしに spending 関数は同定できず、
  `Σ_{k≥1} = 0.05` という承認の根拠そのものが定義域に依存する。
  `k = 0` から始まる定義域へ差し替えられると累積 FWER 会計が変わる。
- **式は canonical form との文字列一致で比較する。** 数式の同値判定は一般に決定不能であり、
  「数学的に同値なら一致」と書くと resolver ごとに受理が分岐して追補 P の authority が
  一意に決まらない。空白正規化だけを許し、別表記が要るなら後続 decision が canonical form を
  更新する形にした。
- **閉包に scope を付けた。** ユーザー裁定が承認したのは本 decision の集合であって、
  「将来のあらゆる manifest を無期限に縛る」ことではない。scope を付けないと、
  後続の正当な再承認まで拒否され、承認履歴を前へ進められなくなる。

**却下した選択肢:**

- **承認を 2 つの decision に分ける** — Q4 と Q5 は別問なので分割も成立する。
  **「分けると `F_p` が二義化する」という理由は成立しない** — 追補 P が参照するのは
  publication core の承認 fold であり、2 decision を同一 fold commit に入れることもできる。
  束ねたのは、1 つの裁定パッケージへの応答を 1 つの承認記録に対応させ、
  proof chain を単純に保つためである。代償として生じる連結は `role_coupling` に明示した。
- **追補 P を同じ land で凍結する** — 承認 fold commit が存在しない時点では `core_ref.commit` を
  書けない。内容 commit を書けば既存意味で解決失敗し、内容 commit 意味へ緩めれば
  未承認 bytes を受理する集合が開く。
- **`F_p` を予測して literal で書く** — fold 前に存在しない値であり、必ず外れる。
  先行 payload も記号だけを持ち、literal は後続 land が書いている。
- **旧版を「非承認」の 1 語で片づける** — 過去の手続き選択の記録と矛盾する。role と時点を限定した。
- **D282 の `operational_boundary` を逐語継承する** — 予約台帳と予約履歴を含むが、
  本 payload は公表台帳を作らない。保証していない性質を保証したと書くことになる。
- **文書側の `authority: none` を書き換えて発効を表現する** — 承認した bytes でなくなる。
