---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-03
wave: dev-wave-t2105-freeze-successor
seq: 2
---

## {{D:ax-topology-partial-conformance}}. 下位 A/X topology は正本の部分適合に留め、`A^ == Q` の代替述語を発明しない

**決定:** 凍結側の下位実装 `orchestrator/campaign/s8b_ratified_freeze.py` を
`docs/freeze-permanent-design-s2.md` §S2-1.14 へ適合させる作業のうち、本 wave が閉じるのは
**承認 A と有効 pointer X を別 commit とし、X の parent をちょうど A、各 commit を 1 record 追加のみ
とする部分だけ**とする。正本が同時に定める `A^ == Q` は実装しない。Q の代わりに世代導入 commit G を
A の parent として要求する代替述語も**新設しない**。gate `FREEZE-AX-TOPOLOGY` は
`nonconforming` のまま据え置く。

**理由:**

- 正本の列は `H_gen <- G <- R <- L_prod <- L_manifest <- Q <- A <- X` であり、Q は検査 receipt 4 件の
  導入 commit である。R / L_prod / L_manifest / Q はいずれも permanent freeze family の構成要素で、
  同 family の producer・resolver・CLI・世代 artifact・receipt・report は repository に 1 件も存在しない。
  存在しない入力を要求する述語は採用できない (D75 系の gate 入力実在要求)。
- 「Q が無いから G を代わりに要求する」案は正本に無い規則であり、足すと正本どおりの完全列
  `G <- R <- L_prod <- L_manifest <- Q <- A` を逆に拒否する。段 3 の敵対検査が逐語照合で構成した。
- **A の predecessor が無制約であることは本 wave が作った穴ではない。** 親が repo 外 probe で、
  G を別枝に置き A+X を同一 commit として merge した history が**変更前のコードで既に受理される**
  ことを実測した (`RESULT=ACCEPTED`)。本 wave はこの受理集合を広げも狭めもしない。
- 部分適合であることを隠さない。gate status を動かさず、`FREEZE-AX-TOPOLOGY` を `resolved` に
  しないことで、残る schema 差 4 件と Q 列の未実装が台帳上に見え続ける。

**却下した選択肢:**

- **G を Q の代替として A の parent に要求する** — 正本に無い規則であり、正本どおりの完全列を
  拒否する。順序の入れ替えを塞ぐ効果はあるが、塞ぎ方が正本と非同値である。
- **topology だけ直して gate を `resolved` にする** — 上位権限束設計 §12.4 が明文で禁じる。
  現行 parser は依然として正本どおりの bytes を拒否し、上位 A が参照する受理集合は旧 schema に
  支配されたままである。
- **approval / pointer / revocation / cancellation の schema も同時に正本へ寄せる** — 正本の
  approval は `bundle_digest` と 7 element の `components` を要求し、その 7 component は
  known / measurement / holdout / receipt と 3 report である。holdout 単独 family へ被せると
  実在しない入力を literal で埋めることになる。

## {{D:derived-pin-coordinated-update}}. 派生値 pin の協調更新は owner wave の想定手順であり、テストの弱体化と数えない

**決定:** `orchestrator/tests/fixtures/calibration_freeze_authority/` の case が宣言する
invocation digest、`manifest.v1.json` の `raw_sha256` / `entries_sha256`、および
`orchestrator/tests/calibration_freeze_authority_contract.py` の
`_EXPECTED_RAW_SHA256_BY_FIXTURE` / `_EXPECTED_FIXTURE_ENTRIES_SHA256` は、
**その fixture builder を所有する wave が、fixture の意味を変えないまま協調更新してよい**。
更新してよいのは派生値だけで、`expected_decision`、`single_mutation`、`builder`、`entrypoint`、
`binding_state`、`design_row_id`、および gate status と `_EXPECTED_REQUIRED_GATES` は変えない。

**理由:**

- invocation digest の原像には合成 repo の HEAD が入る (`_canonical_argument` が `Path` を
  `{"type": "git-repository", "head": ..., "status": ...}` へ写す)。builder の commit 構成を
  変えれば digest は**必ず**変わる。更新できないなら builder は永久に凍結される。
- pin の目的は不変性の保証ではなく、**builder の意図しない drift を可視化すること**である。
  contract module 側の pin は「case を変えて manifest を refresh しても pin は動かせない」ように
  manifest から独立させてあり (同 module の comment が明記)、更新を第三の場所での明示的な編集として
  露出させる設計である。owner wave が意味を保ったまま更新することは、その設計が想定する経路である。
- 先例が存在する。commit `b555a2986` は同 builder を変更し、case JSON 6 件と `manifest.v1.json` を
  同じ commit で更新したうえ、commit message に「contract 側のテストは旧値を固定しているため赤である。
  次の commit で同期する」と明記している。
- 凍結された design 文書側にこれらの hash の pin は無い (`docs/calibration-freeze-authority-bundle-design.md`
  と `docs/freeze-permanent-design-s2.md` を hash 値で検索して 0 件)。束縛は test / contract 層に閉じる。

**却下した選択肢:**

- **builder を同一 commit のまま据え置く** — 3 fixture の positive control (いずれも
  `expected_decision: accept`) が新しい topology 検査で拒否される。分けても分けなくても赤になり、
  据え置きは逃げ道にならない。
- **digest に合わせて fixture の狙いを書き換える** — テストを甘くする変更であり、絶対規律 2 に触れる。

## {{D:no-tautological-guard}}. 候補集合から恒真になる述語を正しさ防壁として新設しない

**決定:** 正本が pairwise 非同一を課していても、**候補の作られ方から常に真になる述語は新設しない**。
本 wave では `generation-pointer-same-commit` (X と世代導入 commit G の同一性拒否) を採用しない。
既に実装されている同型の guard は削除しないが、防壁として数えず、変異事前登録にも入れない。

**理由:**

- X は `_assert_user_commit` により raw / parsed とも逐語 `AI-Agent: none` を要求され、G は
  `_assert_candidate_commit` により `none` を拒否される。同一 commit が両方を満たすことはないため、
  この述語は実 resolver から到達不能である。
- 恒真な guard を防壁として数えると、実際には守っていないものを検査済みの保証として台帳や
  レポートへ計上することになる。段 3 の敵対検査が独立に構成した。
- 同じ理由で `approval-pointer-same-commit` も受理集合を狭めない。A == X なら追加 path 集合が
  `{approval, pointer}` となり A 側の exact-diff 検査が必ず拒否するためである。この guard は
  reason code を明瞭にする診断としてのみ置き、その旨をコード comment に明記した。

**却下した選択肢:**

- **正本の逐語に合わせて pairwise 非同一を全辺実装する** — 到達不能な reason code が増え、
  変異で kill できない guard が防壁の数に混ざる。
- **恒真な guard も「多重防御」として数える** — 実際の受理集合を守らないものを保証に計上する。
