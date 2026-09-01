---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-01
wave: dev-wave-t2027-root-class2
seq: 1
title: [T-2027] 消える根の第 2 クラスを manifest schema v3 の根クラスにした (code + tests + insight、branch worktree-dev-wave-t2027-root-class2、変異 6/6 KILLED)
---

## 本文

- **D1322 が求めた D1192 の統合条件を、落ちた job 952631 の実 completion で実測した。**
  4 条件のうち「同一 cache entry」と「同一 descriptor」は満たす (同じ completion の同じ
  manifest、`target` / `input_policy` / `contract_sha256` / `full_build_digest` が同一)。
  **残る 2 つは親と段 3 の敵対相談 2 本で読みが割れた。** 割れた事実を消さずに書く。
  - 「同一拒否述語」— 根が消えた入力を validator へ通すと両クラスとも同じ述語で落ちる
    (コードの性質)。**しかし production の lifetime では同じでない。** クラス 1 は build 自身が
    staging を捨てた後の受領書発行で落ちるが、クラス 2 の `/scr/0_<jobid>` は受領書発行時に
    まだ生きており、現に落ちていない。
  - 「同一是正 3 択」— 3 択の集合は同じだが効き方が違う。(b) base 絶対 path を identity へ
    入れる案は、クラス 1 では staging が identity 確定の後に PID + nonce で作られるので
    **構造的に不可能**、クラス 2 では**既に適用済み**。(c) 消えた entry の cache miss 降格は
    クラス 1 を直さず、クラス 2 には cross-job hit が無いので空振り。
  - **親は「どちらのクラスでも remedy になるのは (a) だけで、選択は分かれない」と読んで
    束ねた。** F151 の再発防止が守ろうとしたのは是正の選択が分かれないことだから、という
    理由である。**レンズ 2 本は「効き方まで同一でなければ 4/4 とは書けない」と読み、
    先行条件は未充足で差し戻しと判定した。** この読みの相違は {{T:d1192-merge-condition-reading}}
    としてユーザー裁定へ返す。後者を採るなら本 wave の実装は差し戻しになる。
- **親が段 1 で「承認済み裁定の前提を覆す新事実」と書いた 2 件は、新事実ではなかった。**
  cache identity が job 専用 path を持つため別 job が同じ entry を選べないことは、
  **D1220 (2026-08-28) が既に裁定として記録していた** — 「cache hit が起きない事実は
  限界として記録する」。D1322 は 9/1 の裁定なので、これを承知のうえで下されている。
  親は段 4 直前の再走査で D1220 を見つけて裁定を組み直した。**既裁定の照合を T 番号や
  D 番号ではなく機構名 (`source_root` + `cache`) で引いて初めて出た。**
- **したがって D1322 の狙いは cache hit を起こすことではなく、記録から job 番号を外すことである。**
  実装した形は {{D:dependency-prefix-root-class}} に書いた。**「これで床値の主経路が緑になる」
  とも「cross-job の再束縛が発火する」とも主張しない。** 発火しないことは D1220 が
  受け入れ済みの限界であって、本 wave の欠陥ではない。
- **形 B (identity から job 専用 path を外す) は実装していない。** D1220 が却下済みであることに
  加え、段 2 plan が「compiler manifest は link 入力のうち `.o` しか集めず gflags/glog の
  `.a` を持たないので、path を外すと同じ header・違う library を同一視して受理集合を広げる」と
  指摘した。塞ぐには install tree 専用 digest という新機構が要り、しかもそれでも hit は起きない。
- **段 6 の敵対レビューが must-fix を 2 件出し、親が実測で裏を取って fix した。**
  (1) 根の解決を入力のタグを見る前に全要素へ必須化していたため、configure された
  `CMAKE_PREFIX_PATH` に stale な要素が 1 つあるだけで収集・cache hit・受領書発行が止まった。
  親が repo 外 probe で 7 ケース再現した。これは根クラス 1 の監査が見つけた同型の 2 例目なので
  {{F:root-resolution-required-where-unused}} を立てた。1 例目は F 台帳に登録されておらず、
  そのため 2 例目の設計時に参照されなかった。
  (2) 段 4 裁定が名指しで落とした形 B 由来の test node が実装に復活していたので削除した。
- **レビュー所見の 1 件は、採用裁定を出した後に「受理面では純増ゼロ」と判明した。**
  `None` (context 未提示) と明示的な空 tuple を区別せよという指摘に対し、実装は明示的な
  `None` 拒否を足したが、直後の canonical 化関数が同じ条件で同じ入力を既に拒否していた。
  変異の単一理由性検査で分かった。裁定は撤回しない (診断は明確になる) が**受理面の強化として
  数えない**。経緯は {{F:redundant-none-guard-counted-as-strengthening}}。
- **変異は事前登録の 6 件のうち 1 件を実装後の現物で外し、両層同時変異へ再照準した。**
  m06 (`None` 拒否条件の単層変異) は上記の冗長 gate に mask されるので `DW-M08` の
  diagnostic sensitivity pin へ別枠記録し、m06b (明示条件の削除 + `None` を空 tuple 扱い) を
  kill 期待つきで登録し直した。**本走は 6/6 KILLED、baseline PASSED、期待 node 完全一致
  (matching=6)、SURVIVED 0・MISMATCH 0・TIMEOUT 0。** 期待 node は probe で観測してから登録した。
  m06b も KILLED なので、再照準の判断は実測で裏が取れた。
- **anchor の一意性検査で 1 件を差し替えた。** m02 の `if len(matches) != 1:` は同じ file の
  別箇所にも存在するので、`DW-M04` の「置換対象が一箇所でなければ停止」に従い raise 本文まで
  含めた 4 行へ広げた。
- **並行 wave が所有する test file を編集せずにテスト閉包を閉じた。** 段 2 plan は
  「build から受領書へ根が渡ることを検査する node は `test_s8b_floor_campaign.py` にしか
  置けず、所有制約下では閉包が成立しない」と報告したが、**所有競合しない新規 module**
  `orchestrator/tests/test_s8b_dependency_prefix_bridge.py` に置けば閉じる。変異 m05 は
  この新規 file の正例と負例の両方で殺されており、閉包が実効を持つことを実測で示した。
- **子は 6 本 (段 2 plan 1、段 3 敵対相談 2、段 5 実装 1、段 6 レビュー 2、段 6 fix 1 の計 7 本)。**
  全部 rc=0 で `check_codex_output.py` も緑。**実装子と fix 子はいずれも計算ノードへ
  dispatch できず (`rc=16`)、両方とも「実装済み・未実走」と正しく申告した。実測はすべて親が
  行った。**
- **焦点走はすべて親が実走した。** 編集面 4 file + メタ契約 = 309 passed、v1 fixture と
  名前 pin の 8 file = 517 passed、floor campaign + oracle driver = 589 passed / 9 skipped、
  `test_campaign.py` = 381 passed / 3 skipped。いずれも rc=0。
- **3 file を混ぜた走で 12 件の赤が出たが、本 wave の差分に帰属しない。** 各 file 群は
  単独では緑で、赤は組み合わせたときだけ出る。赤の内訳は launch certificate と wall clock
  台帳で、本 wave の編集面 (compiler input manifest の根タグ) と交わらない。`DW-O18` の
  「差分到達不能は単独再走、非再現なら受入再走」に従い受入全走で最終判定した。
- **床値 job の実投入はしていない。** 依頼は [T-2043] の確認として実投入を求めたが、
  `tools/pegasus/floor_campaign.sh` は 10 時間の walltime を要求する campaign で、
  事前登録と凍結の契約を持つ計測系列である。correctness の確認として片手間に投げる形にすると、
  計測系列の契約と混ざる。**投入せずに開いたまま残した。**

## 次の一手差分

### 完了

- [T-2027] 消える根の第 2 クラス (job 専用作業領域 7 件) を manifest schema v3 の
  `dependency-prefix` 根クラスとして記録し、収集・cache hit 検証・受領書発行の各時点で
  現在の prefix 要素へ束縛し直す実装を land した。D1322 が求めた D1192 の統合条件は
  実測して記録し、読みが割れた 2 条件は {{T:d1192-merge-condition-reading}} へ分けた。
  remaining: none
  base: 7fb501c07135785793d078d1f5ee8635117e77c6508fe50c02f89eac8e2f365d

### 更新

- [T-2043] **P1・根クラス 2 の是正は着地。実投入は未実施**: 発行段を止めていた根クラス 2 の
  記録形は本 wave で直った。残るのは床値 job を 1 回投入して受領書発行段を実機で通す観測だが、
  10 時間 walltime の計測 campaign なので本 wave では投入していない。
  **cross-job の再束縛の閉包は D1220 の限界により本項では閉じない** — 閉じるなら
  {{T:d1220-limit-reconciliation}} の裁定が先である。
  base: 0d0fca10afaddc3c761dedb673ba07e402904aabaa7a86f5e193c7fc352295bf

### 新規

- {{T:d1192-merge-condition-reading}} **P1・ユーザー裁定待ち**: D1192 の「同一の是正 3 択」を
  「選択が同一なら足りる」と読むか「効き方まで同一でなければならない」と読むかで、親と段 3 の
  敵対相談 2 本が割れた。親は前者で進めて根クラス 2 を束ねた。後者を採るなら本 wave の実装は
  差し戻しになる。実測の内訳は本エントリ本文と
  `output/insights/2026-09-01_t2027-root-class2/` にある。
- {{T:dependency-root-origin-authority}} **P2・設計裁定待ち**: `dependency-prefix` 根の entry は
  manifest の自己申告した根と相対 path と hash しか持たず、origin への帰属を検証できない。
  根クラス 1 (`fetchcontent-masstree`) も同じ弱さを持つので、durable な root commitment を
  入れるなら両方へ一度で入れる設計判断になる。本 wave は既存 canonical 性検査の射程合わせだけを
  行い、新機構は作っていない。
- {{T:d1220-limit-reconciliation}} **P2・台帳整合**: D1192 は「run 間の cache 再利用は失わない」を
  代替案の却下理由に置いているが、D1220 は正式 S8b 経路で cache hit が起きないことを限界として
  受け入れている。実測でも identity は `dependency_prefix` と `admission.source.source_root`
  の 2 系統で job ごとに分かれる。D1192 の理由部分と D1220 の関係を台帳で明示するかを決める。
- {{T:kwargs-collector-failclosed-seam}} **P3・backlog**: `_collect_compiler_inputs()` の
  signature introspection は `**kwargs` を持つだけの collector を external policy 下で
  受理する。変更前から存在する seam で production collector は明示 signature を持つため、
  成果物への影響を 1 行で書けない。`DW-G05` に従い本 wave では直していない。
