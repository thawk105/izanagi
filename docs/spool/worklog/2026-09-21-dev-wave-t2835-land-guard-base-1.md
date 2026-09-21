---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-21
wave: dev-wave-t2835-land-guard-base
seq: 1
title: [T-2835] 呼び手の land 前 guard を D987 / D1234 の比較基点に揃えた — DW-O23 に「取込由来の追加再受入は tested main と固定 SHA の runner blob 差だけ、他の拒否は維持」を 1 文、原資は同節の重複削除 (D782 の 1 段目)、land の memory の旧 guard を是正。変更後の経路の初回実測は未了 (docs のみ、branch dev-wave-t2835-land-guard-base)
---

## 本文

- **D2206 項 2 (第 29 回 /rulings) の実施。** 限定は「『runner 差だけ』は取り込み由来の追加の再受入条件に限り、受領証の不一致・不正な merge 形状など
  他の拒否を外す意味にしない」「F524 の待ち手・launcher・runner 検査は受入投入前だけ」「変更後の経路 (旧受領証で前方 merge → land) は最初の 1 回を実測で確認」。
  wave 開始時 (14:0x) には D2206 は未着地で、決定文は `worktree-rulings-all-20260921c` の decisions fragment 項 2 から読んだ。
- **source で確かめた前提:** `tools/dev_wave_land.py` の `_verify_forward_main_runner_blob` は受領証の tested main と取り込み列の最終 main の
  `tools/run_tests.py` tree entry (型 blob・SHA) を比べる。waiter は tested tip、checker は非帰属赤の受領証のとき tested main / tested tip、
  launcher は tested main (bootstrap 時だけ tested tip) の tree に束縛され、取り込む main 側の waiter / checker / land の差分それ自体を
  再受入の理由にする比較は無い。
- **過剰 guard の出所は repo docs ではなかった。** D987 / D1234 / DW-O20 / DW-O23 / DW-O25 / F524 / D822 に land 時の 4 file 検査を求める文は無く、
  出所は land の memory の旧節 (2026-09-01、merge-base 基点で `run_tests.py` と `dev_wave_wait.py` を diff) と、それを 4 file に広げた
  t2803 の使い捨て wrapper (`land-go.sh`) だった。相談 B の repo 全体検索 (旧比較式・再受入・取り直しの表現、insight の過去記録は除く) では
  旧 guard を手順として書く現行文書は見つからなかった。repo 外の wrapper 全体の是正済みは主張しない。
- **DW-O23 の変更:** 「取込由来の追加再受入はtested mainと固定SHAの`tools/run_tests.py` blob差だけ(D987)。他の拒否は維持。」を足した。
  L1 が 10,623 / 10,625 bytes だったので D782 の 1 段目 (既存記述の削減) で原資を作った — 「T/D/F採番・canonical3台帳追記・worklogローテは1度だけ。」
  を削除 (DW-S07 の「canonical への追記・採番・ローテーションは段 9 の land が lock 内で一度だけ行う」に包含)、「他session所有物・rebase・force・remote・pushで解消しない。」
  を「remoteで解消しない。」に縮小 (他session所有物・rebase・force は入口の終端、push は入口の凍結境界が段 9 の land 競合で同じく禁じる)、
  冒頭 2 行 (監査列を渡す / 監査列は固定) を意味を変えず 1 行に畳んだ。適用後の L1 は 10,619 bytes、DW-O23 は 974 bytes (check_docs の層計算関数を
  呼ぶ使い捨て probe で実測、job dir `materials/l1_probe.py`)。独立 3 例の例外・上限引き上げは使っていない。commit `766a0701d` の木で
  `python3 tools/check_docs.py` は「違反なし」rc=0 (job dir `check_docs-1.log`)、全史 `check_ai_provenance.py` は 12,363 件・新規違反なし (`provenance-1.log`)。
- **land の memory (repo 外 `land-discipline`) の旧節を是正した。** 見出しを「取り込み由来の追加再受入は runner blob の net 差だけで決める」に改め、
  比較 1 つ (受領証の tested main と今回取り込む固定 main SHA の `git rev-parse <sha>:tools/run_tests.py`)、取得不能・非 blob は再利用可と判断せず原因を確かめる、
  取り込みが 2 回以上でも基点は tested main 固定、他の拒否と F524 は外さない、を書いた。末尾の 2026-09-21 補足の同内容 bullet は上の節への指し示しに縮めた (矛盾の解消)。
- **段 3 の相談 2 本 (read-only、luna、gpt-6-astra / medium) はどちらも NO-GO・must-fix 1 件で、両方採用した。** A (正しさ境界): 初案の文が「追加の」と
  「他の拒否は維持」を欠き、runner 比較を旧受領証の再利用の十分条件と読める (例: launcher bootstrap の受領証は runner が同じでも land が locked main 検査で拒否する)。
  B (過剰・削除): 初案は「他session所有物・rebase・force・remote・pushで解消しない。」を丸ごと削ったが、「remote」は入口の「push・remote branch 操作は禁止」より広く
  DW-STOP にも無いので残す。should 4 件 (A3 launcher bootstrap と incoming の land 変更の扱い、A4 取得不能・非 blob の扱い、A7 36.4 分は回避候補区間で
  削減実測でない、B7 初回実測の未了の明記) は memory と本文に反映。refuted 8 件 (A2 waiter / checker 束縛と F524 の限定、A5 複数回取り込みの基点、
  B2 T/D/F 採番文の包含、B3 D782 の 1 段目で閉じられ F266 の括弧は残す、B4 旧 guard を書く現行文書が検索範囲に無い、B5 probe の計算、B6 pin・fixture、
  B8 変異 matrix 免除)。A2・A5 の補足は memory に入れた。判定不能 1 件 (A6 後着の依頼の原文) は依頼原文を job dir `materials/origin.md` に逐語で置いて解消。
- **段 6 の read-only review 1 本 (gpt-6-astra) は GO・must-fix 0 件。** should 3 件はすべて記録の精度 (相談所見の内訳の番号対応、断定の範囲と記録の所在、
  memory の「未実測」の範囲と既存補足の「本 wave」の出所) で、親が直した。主張を狭める修正だけなので焦点再レビューは省いた。
  refuted 3 件 (比較基点と拒否条件の境界、削除・縮約の包含と commit message の一致、bytes の算術)。
- **D2206 項 12 (T-2834 は DW-O23 を変えない) との関係:** 項 12 は T-2834 の内容 (land loop の順序) の置き場を決めたもので、本 wave は T-2834 の内容を DW-O23 に
  入れていない。本 wave の依頼 (14:0x、裁定受領 13:3x の後) は予算に当たれば D782 で閉じると明示していた。
- **起動コスト wave との編集面の照合 (wave 開始時):** `worktree-dev-wave-wave-startup-cost` の未着地 commit `71f7c5fbb` の差分は
  `output/insights/2026-09-21/wave-startup-cost/` と spool fragment 2 本 (22 file)、同 worktree の `docs/dev-wave/operations.md` は main と同一 blob
  (`38581ff31`)。本 wave の編集面 (`docs/dev-wave/operations.md` と repo 外 memory) との重なりは 0。
- **[T-2835] の fragment の扱い:** wave 開始時は未着地の rulings fragment が [T-2835] を「更新」していたので触れずに待ち、D2206 の着地 (14:42、fold `f646e7e85`) 後に
  同 SHA を固定で取り込んで base digest を取り直した。
- **受入と land:** 本 entry を含む tip で門番付きの受入全走を投入し、child-green の受領証で land する (本 entry の着地がその緑の証拠)。land 前 guard は本 wave の
  新しい基点で判定する — 受領証の tested main と取り込む固定 main SHA の `tools/run_tests.py` blob が同じなら旧受領証のまま前方 merge → land。
- **変更後の経路の初回実測は未了。** 旧受領証で前方 merge → land する形そのものは診断の母集合 11 本で通っているが、取り込む main が waiter / checker / land を変えて
  runner は同じ、という形は t2803 で未実測のまま。本 wave の land がこの形に当たったかは land 時点で決まり、受入後に commit を足すと land が rc=23 で止まるので
  本 entry には書けない。当たった場合は memory `land-discipline` の同節に 1 行で残し、repo 台帳へは次に [T-2835] を扱う wave が写す。
- **実装面の差分は 0。** 変異 matrix は免除 (DW-S04)。
- 工数: codex 子 3 本 (consult 2、review 1)。計算ノード job は受入のみ。

## 次の一手差分

### 更新

- [T-2835] **P2・docs 修正済み (D2206 項 2) → 変更後の経路の初回実測の記録待ち (AI)**: DW-O23 に「取込由来の追加再受入はtested mainと固定SHAの
  `tools/run_tests.py` blob差だけ(D987)。他の拒否は維持。」を足し、land の memory の旧 guard (merge-base 基点・4 file) を是正した (本エントリ)。
  残りは初回実測の記録だけ — 旧受領証のまま前方 merge → land し、取り込む main が受領証の tested main から `tools/dev_wave_wait.py` /
  `tools/check_acceptance_reds.py` / `tools/dev_wave_land.py` のどれかを変えて `tools/run_tests.py` は同じ、という land が最初に起きたら、
  tested main・取り込んだ main・変わった file・land 結果を worklog に 1 行で写して完了にする (該当した land は memory `land-discipline` の同節にも残す)。
  「runner 差だけ」は取り込み由来の追加条件に限り、他の拒否と F524 (受入投入前) は外さない。新しい gate・台帳は足さない。
  base: deb11a10988dce1c88923a3da69d393658fff21153be794720f8a74b9af0ed50
