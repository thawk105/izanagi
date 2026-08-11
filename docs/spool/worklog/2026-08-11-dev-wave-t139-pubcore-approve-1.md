---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-11
wave: dev-wave-t139-pubcore-approve
seq: 1
title: 公表 core v2 と source 追補 B v2 の凍結承認を payload として固定した — 追補 P は値だけ承認し blob は未承認のまま (docs のみ、実装差分ゼロ、branch worktree-dev-wave-t139-pubcore-approve)
---

## 本文

- **ユーザー裁定 Q1〜Q7 (2026-08-11 /rulings 第 5 回) を適用し、承認 payload を
  {{D:t139-publication-core-approval}} として固定した。**凍結承認は裁定だけでは発効せず、
  承認 payload を canonical 台帳へ fold した commit `F_p` が発効点である。
  本 payload が承認するのは公表 core v2 と source 追補 B v2 の **exact 2 三つ組だけ** (Q4 (a) / Q5 (a))。
  追補 P は `p01` / `p02` の**値だけ**を承認し (**Q6 (a) / Q7 (a)**)、blob は未承認のまま残した
  (blob を承認しない根拠は Q2 (a) + Q3 (b))。

- **段 3 の敵対レンズ 2 本がともに NO-GO を返した。blocker はレンズ A が 3 件
  (supersession の型付け・relation 写像・exact closure)、レンズ B が 2 件
  (Q1 gate 未実装・Q3 の台帳実体確定遷移) で、いずれも real として全採用した。**
  加えて must-fix 3 件 (`authority: none` の誤読経路・1 decision に束ねる判断・保証境界の縮小) も採った。
  親 brief と段 2 プランの誤りを、レンズが実際に見つけた。

  1. **段 2 プランが親の provisional 裁定 (P2) を倒し、その型付けをレンズ 2 本が独立に倒した。**
     親は「旧版 2 文書は初回承認だから失効処理は不要」と judged し、プランは
     「過去裁定 C-2 / C-4 に旧版の承認選択が残るので `forward_supersedes` が要る」と反論した。
     レンズ A と B はこれを**過大**と判定した — そこにあるのは**未実行の手続き選択**であって
     exact blob の authority ではない。存在しない承認を失効させると、履歴 resolver が
     旧 blob を「一度承認済み」として扱う受理枝が増える。
     結論として `supersession` を型から外し、`prior_exact_byte_authority = none` と
     `procedural_history` に分け、旧 blob は role 限定の拒否として書いた。
     **親の結論は維持されたが、親の理由は不十分だった。**

  2. **レンズ A が、denylist では塞がらない穴を実測で示した。**承認対象と**同じ path** に、
     承認対象でない中間 blob が実在する。親が独立に測り直して一致を確認した。

     ```text
     publication-core-v2.md  45d83e7ab471ef9db0aaf9705168a333a8c317de06674fa23ef9164428d03065
     addendum-b-v2.md        0ea71fff11c0f4c939cab213021487758bf6016db522ea29a3a527d2ee1c0658
     addendum-b-v2.md        2313a26151975fe65e6586dec5676df92da209c68126296b55592ec6ab8834df
     ```

     旧 path だけを列挙する denylist は同じ path の別 digest を落とせない。
     payload を **allowlist の閉集合契約**へ書き換えた。

  3. **レンズ B が親の誤った表現を倒した。**親は brief と handoff に
     「Q1 (a) の条件は既に履行されている」と書いたが、**これは強すぎる。**
     正しくは「公表層実装 wave の必須要件へ追記済みであることを確認した。
     source 側の本走 gate は未実装・未検証」である。追補 B v2 自身が旧 gate の削除を明記しており、
     現時点で active gate は存在しない。payload には `source_main_run_gate = not_implemented` と
     書き分けて記録した。

  4. **レンズ A が relation の欠落を指摘した。**追補 B は source core の `main_admission` が
     要求する `addendum_b` role を満たす従属文書、公表 core は独立 study の core である。
     この写像を書かないと、relation graph だけを読む resolver は追補 B を `main_admission` へ
     結線できないか、別の追補 A を公表入力として受理しうる。admission role 写像と、
     公表 core が source study を片方向に pin する 2 三つ組を payload へ入れた。

  5. **レンズ B が「1 decision に束ねる」は未裁定だと指摘した** (blocker ではなく must-fix)。
     Q4 と Q5 は別問である。親は束ねる裁定を維持したが、**その理由は段 6 で覆された**
     (下記)。

- **段 6 の敵対レビュー 2 本も NO-GO を返し、must-fix 6 件を採って fragment を書き直した。**
  段 3 が「プラン」を攻撃したのに対し、段 6 は**実際に書かれた bytes** を攻撃した。

  1. **`exact_closure` が `document_relations` を閉じていなかった** (レビュー C)。
     三つ組と値を一致させたまま `depends_on` / `satisfies` だけを差し替えた manifest が通り、
     追補 B を公表 core へ、追補 P を source core へ誤結線できた。関係の全 field を照合対象に加えた。
  2. **「exact 一致」の比較単位が未定義だった** (レビュー C・D が独立に指摘)。
     payload と追補 P では field 名が違い (`current_k` ↔ `current_study.k` など)、
     式・数値表記・集合順序の比較単位も無かった。**同じ追補 P を承認する後続 land でも
     実装ごとに受理・拒否が分岐する。**写像・比較単位・承認範囲外 field を `value_projection` として固定した。
  3. **裁定が触れていない field を承認範囲外と明記した。**追補 P 草案の
     `immutable_in_this_addendum` / `spending.domain` / `affects_primary_alpha` は
     Q6/Q7 の承認対象に含まれない。書かないと、正規の追補 P が「payload に無い field を持つ」
     だけで恒久的に一致不能になる。
  4. **decision-local な帰結を永久・global な拒否義務へ拡張していた** (レビュー D)。
     **これは親の新規立法であり、ユーザーは裁定していない。**閉包と旧候補拒否に
     「本 decision の承認集合について」「明示的な後続 canonical supersession まで」の scope を付けた。
     付けないと、後続の正当な再承認まで拒否されて承認履歴を前へ進められなくなる。
  5. **`approval_independence` は独立を保証していなかった** (レビュー D)。
     2 role は同じ `F_p` で同時発効し、parse 失敗は両方を落とす。**「独立である」という主張を撤回**し、
     `role_coupling` として実際の連結を列挙したうえで、独立なのは承認の**根拠**だけだと書き分けた。
     片側の更新・失効規則は本 payload では定めず、後続 decision の明示を要求する。
     **束ねた理由も書き換えた** — 親は「分けると `F_p` が二義化する」と書いたが、
     レビュー D がこれを**成立しないと示した** (追補 P が参照するのは公表 core の承認 fold であり、
     2 decision を同一 fold commit に入れることもできる)。実際の理由は proof chain の単純化である。
  6. **worklog の裁定番号を誤記していた** (レビュー D)。値承認の根拠を `Q2 (a) + Q3 (b)` と書いたが、
     値を承認したのは **Q6 (a) / Q7 (a)** である。canonical な裁定 provenance の誤記なので直した。
     blocker の内訳も実際のレンズ出力 (A 3 件 + B 2 件) に合わせた。

- **レビュー C が中間 blob の網羅性を実測した。**reachable な全 commit の tree を走査し、
  当該 2 path の unique blob は公表 core が 2 個 (承認 1 + 非承認 1)、追補 B が 3 個
  (承認 1 + 非承認 2) で、**payload に記載していない非承認 blob は 0 件**と確認した。
  payload の留保を「現時点では全件を確認済み。ただし履歴は伸びうるので網羅を担うのは allowlist」
  へ書き直した。

- **段 6 で refuted と判定された攻撃も記録する。**時制の分離 (fold 前後)、spool 書式、
  三つ組と digest の全件、[T-793] の既存 3 要件の保存、`authority_field_note` の保証偽装、
  scope 外 4 件の routing — いずれも問題なしと確認された。

- **焦点再レビューが closed 4 / partial 4 / **regressed 1** を返し、さらに 3 件を直した。**
  **fix が新たに壊した箇所を、焦点再レビューが実際に見つけた。**

  1. **regressed — `p02.spending.domain` を照合対象から外したのは後退だった。**
     親は「裁定が列挙していない field」として非照合にしたが、**定義域なしに spending 関数は
     同定できず**、`Σ_{k≥1} = 0.05` という承認の根拠自体が定義域に依存する。
     `k = 0` から始まる定義域へ差し替えられると累積 FWER 会計が変わる。承認範囲へ戻した。
  2. **partial — 式の比較手順が決定可能でなかった。**「定義域の全点で値が一致」と書いたが、
     数式の同値判定は一般に決定不能で、resolver ごとに受理が分岐する。
     **canonical form との文字列一致 (空白正規化のみ許容) へ変更した。**別表記が要るなら
     後続 decision が canonical form を更新する。
  3. **partial — `document_relations` の「全 field」の括弧内列挙から `required_core_ref`・
     `study_label`・`note` が落ちていた。**実装者が括弧を閉じた schema と読むと
     `required_core_ref` を差し替えられ、追補 P の lineage が変わる。
     括弧を**例示**と明記し、節全体を照合対象とした。

- **残る 2 件の partial は本 wave で閉じない。**
  (i) `addendum_p_freeze_precondition` の成立証拠 (誰がどの canonical 記録で「実体確定」を
  証明するか) は公表台帳の実体を決める [T-793] の責務として送った。
  (ii) **pilot / 本走の投入禁止の解除条件は Q1〜Q7 から一意に導けないため、
  裁定パッケージ `output/insights/2026-08-11_t139-pubcore-approve/package.md` の R1 として
  ユーザー裁定へ返す** (親の推奨は (c) = 解除権限だけを先に決める)。
  **本 land はこの答えを待たない** — payload は fold 時点の禁止状態を正しく記録しており、
  禁止を維持する限り台帳に嘘は生じない。

- **文書は 1 byte も編集していない。**承認対象を編集したら承認した bytes ではなくなる。
  帰結として、fold 後も 2 文書の envelope は `authority: none` のままである。
  これは先行の source core も同じであり、`authority` field は発効マーカーではない。
  承認状態の正本が本 decision であることを payload 自身へ書いた。

- **scope 外の real 所見 4 件は実装せず、公表層実装 wave の責務として記録する。**
  (i) source 側本走 admission の復元 (要件は記載済み、実装・検証は未了)、
  (ii) 根から唯一の公表台帳実体への束縛・原子予約・ordinal 非再利用、
  (iii) 追補 P の未確定 marker と `p` 系 exact-key を検出する機械 gate (現状は規律だけが止めている)、
  (iv) **fold 後の `authority: none` を canonical decision の approved role へ解決する
  resolver / report 層** — レンズ B が新たに挙げた層であり、取り残しを防ぐため明示する。

- **実装差分ゼロ。**コード・テスト・script・機械設定を 1 byte も足していない。
  変異 matrix は `DW-S04` により免除 (kill を観測する実装面が無い)。
  repo 外に置いた運転 script (codex 起動・待ち手・base 算出) は repo へ入れていない。

- **`base` digest は `spool_fold` の `_extract_latest_active` で算出した。**
  見た目の行を sha256 しても carry 解決後の値にはならず、CLI も無い。

- **受入全走の結果値は本エントリに含まれない。**land は wave HEAD と tested tip の厳密一致を
  要求するため、走行後に結果を足すと land が拒否される。値は wave の報告と handoff が持つ。

## 次の一手差分

### 更新

- [T-139] **P1・凍結承認の payload を fold 済み (`F_p` = 本 fold commit)。次は追補 P の凍結だが
  前提未達**: 公表 core v2 と source 追補 B v2 の exact bytes は
  {{D:t139-publication-core-approval}} で承認・発効した (Q4 (a) / Q5 (a))。
  **追補 P は blob 未承認**で、値 `p01` = 1 / `α_pub` = 0.025 だけが承認済み (Q6 (a) / Q7 (a))。
  追補 P の凍結は**公表層実装 wave が公表台帳の実体を確定した後**に限り、pilot もそれまで
  投入しない (Q3 (b))。後続 land は `F_p` を追補 P の `core_ref.commit` へ literal で書き、
  `p01` / `p02` が `F_p` の payload と exact 一致することを確認する。
  **本走・pilot は B8 (a) と Q3 (b) により依然投入不可。**source 側の本走 gate は未実装。
  land 2 (branch `worktree-dev-wave-t139-manifest-w2` 継承、S6 (a) で複数 session 可・
  land は最後に 1 回) は継続。
  **未裁定 1 件**: pilot / 本走の投入禁止の解除条件・成立証拠・解除権限 (Q1〜Q7 から導けない)。
  裁定パッケージ = `output/insights/2026-08-11_t139-pubcore-approve/package.md` の R1、
  親の推奨は (c) = 解除権限だけ先に決める。承認済み裁定 =
  `output/insights/2026-08-11_t139-pubcore-stage2/package.md`。
  base: dc79c0260f916db7b1cfdb9781792494e33c5a6678dcf995e576edfc7ecacb51

- [T-793] **P2・必須要件を 4 つへ (承認 payload の fold で (iv) が確定)**: 公表層の機械執行を
  既存 producer 実装 wave 系列へ足す (裁定 C-5 (a))。**land 2 の必須要件 §S7 #7
  (`b03` 個別公表系列台帳) を具体化して同じ producer 系列へ結線するものであり、
  別 ownership の並行実装ではない。**
  対象 = 公表 validator、`qualification_status` の複写元となる source validator、
  公表台帳の実体化と create-only 予約、公表表の consumer、`p` 系 exact-key 検査
  (現在の exact-key 検査は source study 専用である)。
  **必須要件として次の 4 つを含む** — (i) **根から唯一の台帳実体への束縛**
  (これが無いと空台帳への差し替えで同じ番号を取り直せる)、
  (ii) 追補の未確定 marker を検出して承認・fold を止める機械 gate、
  (iii) **source 側の本走 gate の新設** — Q1 (a) で旧 `b03` から失われた投入前 admission
  (予約一意性が成立しないまま本走を投入しない) を source 側に復元する (Q1 裁定の条件)。
  **要件は台帳に記載済みだが実装・検証は未了であり、承認 payload の fold は
  source 本走 admission を閉じていない**、
  (iv) **`F_p` の canonical payload を trust root として承認 role を解決する resolver / report 層** —
  承認した 2 文書は fold 後も `authority: none` のままであり、decision を読まない reader は
  未承認と誤判定する。
  **公表台帳の実体の同定はこの wave の裁定事項**であり、それが決まるまで追補 P は凍結できない。
  base: dee6012ebc7980b1a7139ad3648957e7c8749b7eae164195b5de6c4927d04d2e
