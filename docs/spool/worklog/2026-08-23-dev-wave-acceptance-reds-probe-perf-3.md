---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-23
wave: dev-wave-acceptance-reds-probe-perf
seq: 3
title: 非帰属判定を全走差分方式へ作り替えた。3 案の比較という枠組み自体が誤りで、直列では 5 分に入らないことが算術で確定した (コード+テスト、branch worktree-dev-wave-acceptance-reds-probe-perf)
---

## 本文

- 前 entry の時点で親は「collection 畳み込み + rc=128 リトライ」を成果物としていた。
  その後ユーザーから 2 つの指示が出て、**成果物の形が根本から変わった**。
  (1)「テストは最悪 5 分までだよ」(本セッションへ直接)、(2)「check_acceptance_reds.py を
  オフにしろ。使うな。41 分かかる？ふざけるな」(並行セッション経由)。
- **親の段 6 裁定が誤りだったと確定した。** 段 6 でレンズ B が
  「903 秒では 5 分制約に違反する (blocker)」と出したのを、親は
  「wave 自身のテストの走らせ方の作法であってツールの実行時間目標ではない」と読んで
  refuted にした。**この読みが誤りで、レンズ B が正しかった。**
  親が敵対レビューの blocker を握り潰していた。
- **直列では 5 分に入らないことが算術で確定した。** 親が同一混雑下で A/B 実測し、
  1 dispatch は約 22 秒の固定費と判明した (投入枠を 5 分へ絞って 22.30 秒、
  既定 1 時間で 21.86 秒、**有意差なし**)。26 件 × 22 秒 = 572 秒 > 300 秒 で、
  ローカル git を 0 と仮定してもなお超える。**walltime 仮説は親自身の実測で否定された** —
  約 22 秒は queue 待ちではなく job 起動・python 起動・後片付けの固定費である。
  親は先に peer へ「walltime 適正化が効きそう」と伝えており、訂正を送った。
- **手動実行で 58 分走って 26 件を完了しなかった** (06:51:46 開始、07:50:12 に親が SIGTERM)。
  collection 畳み込みを適用した後でもこの所要である。
  停止時の cleanup は正常完走した (`terminated by signal 15 after cleanup`、
  probe 残骸 0、worktree 登録 0)。本 wave で入れた signal 保留経路が実地で効いた。
- **3 案を比較するという枠組み自体が誤りだった。** 依頼は
  「並列化・worktree 再利用・submodule 初期化の共有化を比較して最小の変更から段階導入」
  だったが、**3 案とも採用しなかった**。worktree 再利用は状態隔離を証明できず
  ({{D:probe-worktree-reuse-cannot-prove-isolation}})、並列化は O(赤の件数) を残すため
  他セッションが実測した 4 つの失敗モード (rc=128 競合・probe 残骸放置・
  submodule config ロック競合・判定中の main 競走) が消えず、submodule 共有化は
  worktree 再利用に内包される。**どれだけ賢く直列を速くしても算術は超えられない。**
- **採用した設計は親の発案ではない。** T-755 セッションが「参考までに」と添えた
  「tested main で全走を 1 回だけ回して赤集合を差分する」形をユーザーへ選択肢として提示し、
  裁定を得た。詳細は {{D:full-run-difference-attribution}}。
- **「差分は通常空集合」という親の前提は実測で覆った。** T-755 の実測で、同一 branch・
  同一 tip 系列でも並行受入 3 本のとき 26 件、4 本のとき 36 件が落ち、
  差の 10 件は差分ではなく**並行度**に起因する。素朴な差分だとこの 10 件が
  attributable 候補になり、無関係な wave を再現しない形で止める。
  **したがって差分集合の再実行は例外経路ではなく常設経路である。**
  ただし per-node に分解せず 1 回の batch dispatch に畳むので O(1) は保たれる。
  この経緯を書かないと、後から読む人が「差分は空のはず」という古い前提で読んで
  batch 再実行の存在意義を見失う (裁定集約セッションの指摘)。
- **「tip 側の全走は判定器の追加コストではない」。** tip 側の全走は受入全走そのものである。
  ここを二重計上して「全走 2 回で 8 分」と読む誤解が起きやすいので明記する。
  判定器が新たに払うのは main 側の全走 1 回 (実測 196〜260 秒) だけである。
- **e2e consumer test が production の実バグを捕まえた。** 再設計後、
  `test_dev_wave_land.py::test_real_non_attributable_waiter_receipt_passes_real_land_end_to_end`
  が rc=70 で赤になった。原因は fixture ではなく production 側で、checker が
  collect-only 出力中の `IZANAGI_EFFECTIVE_SCHEDULER_V1` marker 行を collected nodeid と
  数えていた (`collection footer count mismatch: selected=1 nodeids=2`)。
  **実際の `run_tests.py` も同じ marker を出すため実運用でも必ず踏む欠陥だった。**
  `DW-O26` の「変更した production file を参照する consumer test も焦点走に含める」が
  無ければ受入まで持ち込んでいた。
- **変異 matrix (再設計後、repo_head e8671324):** baseline PASSED。
  差分判定を常に偽にする変異 (= 全件を non-attributable へ丸める、
  **この設計における規律 2 違反の最短経路**) は 11 テストが落ちて KILLED。
  常に真にする変異 (過剰拒否) は 18 テストで KILLED。いずれも過剰決定 (MISMATCH) だが
  生存ではない。scheduler marker の許容集合を空にする変異は初回 SURVIVED だったが、
  原因は**殺し手 (`test_dev_wave_land.py` の e2e) が runner 引数の外にあった**ことで、
  runner を両 file へ広げて再走した。
- **変異生存の原因が 3 回とも「テストが弱い」ではなかった。** 本 wave 通算で、
  (1) 相互マスク (両層が補償し合う。`defer` handler と `except _TerminationSignal` の
  どちらか片方の変異は互いに補償され、両層同時変異で初めて KILLED)、
  (2) 到達不能コード (cleanup 経路では handler が例外を出さないため except 節に制御が渡らない)、
  (3) 殺し手が runner 引数の外。**いずれもテストを足しても直らず、原因の特定が要った。**
- **変異 baseline が真の flaky を 1 件確定させた。**
  `test_dev_wave_land.py::test_exploration_external_root_keeps_wave_clean` が
  **同一 commit (e8671324) の数分差の 2 走で、1 回は通り 1 回は落ちた**
  (焦点走 722 passed → 変異 baseline で赤)。`DW-M05` に従い `--deselect` で外して再走した。
  **恒久除外ではなく、production も test も変更していない。**
  親は今朝この test を clean main で 1 回再現したことから「決定的な赤」と分類していたが、
  **1 回の再現を決定性の根拠にしたのが誤りだった**。flaky 担当セッションへ訂正と一次資料を渡した。
  同型の誤り (1 回ないし数回の再現を決定性の証拠とする) が本日 3 セッションで独立に起きている。
- **偽の裁定 message を 1 件検出した。** 「`check_acceptance_reds.py` は廃止対象、
  全走差分方式も含めて機構自体が不要」という内容が、裁定集約セッションと**同一の socket・
  同一の from-name** を名乗って届いたが、**当該セッションが送信を否認し台帳にも記録が無かった**。
  当該 message は**閉じタグが `</cross-session-message>` でなく `</parameter>` に壊れていた**
  (同セッションからの他 4 通は正常)。内容は検証済みの作業を放棄させる方向で、
  **親自身が集めた実測を正確に引用して論拠に使い**、末尾で判断を親へ委ねる形だった。
  規律 6 が定義する型に一致する。**親は従っていない** — 中継を権威として扱わず
  一次資料 (main の `docs/decisions.md`) を先に確認し、D678 が「使わない」までで
  file の存廃に触れておらず、機構廃止の記録が存在しないことを自分で確かめた。
  本日、裁定集約セッションの中継が 2 回撤回されており、裏取りを習慣にしていたのが効いた。
  出所と特徴を当該セッションへ報告し、他セッションへの同種混入の確認を促した。
- **裁定との整合を確認した。** D678 (着地 5 分以内・判定器を受入経路で使わない) の
  却下節に「判定器を残したまま高速化する」が入っているが、これは
  「赤を 1 件ずつ再走して帰属を確かめる構造が残る限り」という理由であり、
  O(1) の全走差分はその構造を持たない。file の削除を求める裁定は存在せず、
  裁定集約セッターも「放置でよい」と確認した。
- **受領証の発行経路に穴が残る。** 判定器を使わないと受領証は「全緑」でしか出ず、
  赤が 1 件でもある wave は着地できない。ただし穴の性質は限定的で、
  新しい赤が自分の回帰なら着地できないのが正しい挙動であり、
  非帰属の新しい赤は D662 点 4/5 の経路 (known-violation 登録 → D679 でテスト側を止める →
  修理を高優先度タスクへ) で解消できる。**本当に変わったのは「自分のものでない」と
  判定する主体が道具から人間・AI の判断へ移ったこと**である (裁定集約セッションの整理)。
- **`stale-main` について。** 受入 3 分台でも land が `stale-main` で弾かれる事象が
  他セッションで実測されている。親は連結スクリプト (main 取り込み → 受入 → land を 1 本)
  を用意したが、**位置づけは「窓を縮めて当たる確率を下げる」ではなく
  「弾かれたときに素早くやり直せる 1 本の経路を持つ」**とした。lease を握らず、
  他 wave を待たせず、main も止めないので D662 が問題視した直列化構造には当たらない。
  弾かれたら D662 どおり通常の競合解消 (fetch → 再 merge → 再投入) に落とす。
  構造的な解は `tools/dev_wave_land.py` 側であり本 wave の編集面外である。
- **子の工数 (receipt 実測、再設計分を含む累計):** codex 子 12 本。
  内訳は plan 1 / consult 2 / author 2 / review 2 / fix 5。

## 次の一手差分

### 新規

- {{T:red-check-receipt-path-without-checker}} **P1・新規**: 判定器を受入経路で使わない
  (D678) 前提では、受入受領証が「全緑」でしか発行されない。非帰属の新しい赤が出た wave が
  着地できるよう、`tools/dev_wave_wait.py` 側の受領証発行経路を整える。
  現状は D662 点 4/5 の手順 (known-violation 登録 → テスト側で止める → 修理を別タスク) で
  回避できるが、判定主体が道具から人間・AI の判断へ移ったことは記録に値する。
  担当が未確定である。
- {{T:main-red-set-shared-cache}} **P2・新規**: 全走差分方式の `R_main` は
  tested_main の SHA だけで決まり wave に依存しないので、
  `<main SHA, runner 内容ハッシュ>` を鍵に repo 外へ cache して全 wave で共有すれば、
  同じ main を tested_main とする 2 本目以降の main 側全走を省ける。
  **安全性の向きが良い**: cache が古く `R_main` が小さめに出ても差分が増えて
  batch 再実行が増えるだけで、regression を隠す方向には倒れない。
  ただし **cache key に repo の内容だけを入れると足りない** —
  `/tmp` の oracle memo キャッシュのような機体側の状態を捉えないため、
  無効化契機の設計でこの点を明示的に扱う。出典 = T-755 セッション。
- {{T:dev-wave-docs-budget-raise-backlog}} **P3・新規**: 本 wave の段 8 で
  予算に弾かれて撤回した 2 件を、D671 (dev-wave docs の分量上限は必要な分だけ
  引き上げてよい) の下で入れ直す。(a) `DW-O01` の `--reasoning` 記述不足
  (`--stage review/focus/author/fix` 以外では必須で、無指定は rc=2。
  行を延ばすと dispatcher route 行の exact pin が破れるので**独立行として追記する**)、
  (b) `DW-O19` へ「防護ツリー内は guard が削除を拒み原状回復できないので
  probe と生死実験は使い捨て worktree で行う」「変異走行中に tree へ書くと
  untracked 検出で止まる」。実測した必要量は `DW-O19` 節が 1192 > 1000 bytes、
  L1.5 footprint が 9622 > 9566 bytes。予算定数は `tools/check_docs.py` にあり
  実装面なので Codex `role=author` が要る。
- {{T:exploration-external-root-flaky-cause}} **P2・新規**:
  `orchestrator/tests/test_dev_wave_land.py::test_exploration_external_root_keeps_wave_clean`
  が同一 commit の数分差の 2 走で通ったり落ちたりする。失敗署名は
  `execution_guard.require_certified_writer_authorization` /
  `numactl = ('numactl', '--interleave=all')` / `env_contract = None`。
  原因未特定のため flaky registry の受理条件 (D679: 原因が理解された壊れたテストだけ) を
  満たさない。原因が特定されれば registry へ entry を 1 つ足すだけで隔離できる。
