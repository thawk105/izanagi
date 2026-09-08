単独段 dispatch: stage=consult; lane=luna; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib

## 必読事項の射影

次を読め。読めなければ即停止し、その旨だけを報告せよ。

- `/home/SFC/tanab/.claude/jobs/9ece0216/tmp/t2288/brief.md` — 親の段 1 brief v2 (逐語)。
- `/home/SFC/tanab/.claude/jobs/9ece0216/tmp/t2288/s2b-plan.md` — 段 2 の plan (逐語)。
- `/home/SFC/tanab/.claude/jobs/9ece0216/tmp/t2288/verbatim-rulings.md` — D1641 全文と事前登録 §5 floor 欄・§5.1 floor 解除条件の逐語。
- `/home/SFC/tanab/.claude/jobs/9ece0216/tmp/t2288/handoff.md` — 親が実測した現在地の表。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/floor_pair_driver.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/tests/test_floor_pair_driver.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/tests/test_p3_b4_floor_artifact_issuer.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/p3_b4_floor_artifact_issuer.py`

repo の path は上記 worktree のものだけを使う。親 checkout の path を使ってはならない。

## 段の宣言

これは段 3 (敵対相談) のレンズ B である。sandbox は read-only で、書込可能な tmp は無い。
**pytest を実走して緑にすることは求めない。静的検査と読解だけでよい。** 実測は親が段 6 で行う。
実走していない検査を「通した」と書いてはならない。
コードを編集してはならない。commit してはならない。plan を守る立場に立ってはならない。

予算が尽きそうなら、その時点の途中結論を下記の出力形式どおりに書いて終われ。無出力が最悪である。

出力に結合文字 U+0300〜U+036F を使うな。

## あなたのレンズ — 変更面の閉包、実効性、変異の帰属、scope

**plan と親 brief の両方が検査対象である。**

段 2 の plan は (γ) を選び、`SPEC_SCHEMA` を `floor-pair-spec/v3` から `v4` へ上げ、
binder の workload 一致 2 行を除き、test を 213 node へ、受入所要台帳を更新する形にした。
あなたの仕事は、この閉包が本当に閉じているかを敵対的に検証することである。

1. **`SPEC_SCHEMA` v4 bump の閉包漏れ。** bump は spec document の bytes を変えるので、
   spec の canonical bytes・sha256・plan hash・window header・summary を経由する pin すべてに波及する。
   次を**現物で数えて**列挙せよ。
   - `test_floor_pair_driver.py` の中で spec document の sha256 / plan sha256 / HMAC 順序 /
     canonical bytes を**literal で pin している箇所**。plan は「fixture が `F.SPEC_SCHEMA` を
     参照するので golden は変わらない」と主張する。**その主張が全 golden について成り立つか**を、
     literal な 64 桁 hex や期待順序列を grep して確かめよ。
   - `test_p3_b4_floor_artifact_issuer.py` が spec document を組む経路。issuer test は
     driver の spec loader を通るため v4 へ追従する必要がある。追従が自動か手当てが要るかを判定せよ。
   - `orchestrator/tests/acceptance_duration_ledger.json` の `nodeid_count` などの集計 field と、
     `test_floor_pair_driver.py` / `test_p3_b4_floor_artifact_issuer.py` の nodeid 集合。
   - 行番号で張られた pin。plan は issuer docstring の `759-776, 1136-1147` を
     `798-816, 1181-1194` と `412-413` へ書き換える案を出している。**その新しい行番号が
     変更後の実際の行と一致するか**を、plan の差分を仮想適用して確かめよ。
     他に行番号 pin がないかも識別子でなく行番号側から探せ。
   - `test_all_floor_pair_dataclass_fields_have_no_defaults`、`NOT_PROVEN` の件数 pin、
     `REQUIRED_FIELD_PATHS`、`SESSION_STATUSES` など件数・集合を pin する meta-test。
2. **plan の数値主張の検証。** plan は「現 test file は 210 node」「変更後は 213 node」
   「台帳全体は 22155 から 22158」と書いている。**現物で数え直し、一致するか報告せよ。**
   一致しないなら正しい数を書け。pytest は実走しなくてよい (静的展開で数えよ)。
3. **これは本当に律速か。** plan の変更を入れた後、実際に凍結 spec を作れるようになるか。
   `load_frozen_spec` と `_bind_checkout_inputs` を上から順に辿り、**実在しない入力を要求する行**を
   すべて挙げよ (tracked build receipt、binary、実 spec instance)。
   **入れても spec を作れないなら、そう言え。** そのうえで「D1641 準拠には必要だから直す価値がある」のか
   「発火 artifact が無いので DW-G04 により設計メモに留めるべき」なのか、どちらが支持されるか判定せよ。
   DW-G04 と DW-G05 の逐語は `docs/dev-wave/core.md` と入口 `.claude/commands/dev-wave.md` を読め。
4. **変異の帰属。** plan は 5 件を登録候補、4 件を非登録としている。各々について
   **赤理由が一つに絞れるか**を独立に判定せよ。とくに
   - 候補 1 (workload equality を戻す) は、新しい二 workload 正例だけが赤になるか。
     他の既存 test が同時に赤になるなら帰属は一意でない。
   - 候補 5 (`SPEC_SCHEMA` を v3 へ戻す) は、4 schema pin と v3 拒否 test の**両方**が赤になる。
     これは過剰決定 (DW-M03) にあたるか。
   - 非登録とした env_tag / clocks の冗長 gate について、plan の「production では verifier が
     先に拒否する」という主張が正しいか。
   **plan が挙げていない、帰属が成立する変異点があれば追加せよ。**
5. **親の実測値とその一般化。** 親は「T-2316 が稼働中だが編集面は素集合」と実測した
   (根拠: `ps -eo args` に現れた codex prompt の逐語が `p3_b4_launcher.py` と
   `test_p3_b4_launcher.py` に限定していた)。**prompt の逐語から編集面を結論できるか。**
   本 wave の編集面 (`floor_pair_driver.py`、`test_floor_pair_driver.py`、
   `test_p3_b4_floor_artifact_issuer.py`、`acceptance_duration_ledger.json`) と衝突しうる
   稼働 wave の兆候を repository 内から探せ (`.codex/worktrees/`、`.claude/worktrees/` の branch 名など)。
   **受入所要台帳は並行 wave と必ず衝突する面である。** 衝突をどう避けるかを述べよ。
6. **scope の膨張と不足。** plan に依頼の本題から離れた追加実装・一般化・互換層・台帳・検査が
   混ざっていないか。逆に、閉じるのに必要なのに plan が落としている面がないか。
   混ざっているものは「scope 外として裁定へ返すもの」と「単に不要なもの」に分けよ。

## 禁止

- plan を弁護してはならない。同意する場合も同意の根拠 file:line を自分で挙げよ。
- 一般化した framework・汎用 gate の新設を提案してはならない。
- 事前登録 §5 を埋める案、事前登録本文を書き換える案を出してはならない。
- 権威 floor の発行そのもの、calibrator の実行、Pegasus への測定投入を提案してはならない。
- 仮想リスク向けの新しい gate・検査・台帳を足す提案をしてはならない。実在する構成可能な穴だけを挙げよ。

## 出力形式

以下の H2 見出しをこの順で使え。各所見には `real 候補` / `refuted 候補` の自己判定と、
根拠の file:line、そして「放置すると成果物 (certified 選択・レポート・台帳) の値・受理集合・参照が
どう変わるか」を 1 行で付けよ。

## v4 bump の閉包漏れ
## plan の数値主張の検証
## 律速の判定と DW-G04
## 変異の帰属
## 親の実測値の検証
## scope の膨張と不足
## 総括
