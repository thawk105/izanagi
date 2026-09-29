---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-29
wave: dev-wave-gen-opt-correctness-gate
seq: 1
title: LLM が新しい仕組みを書くときの正しさ関門を設計した — 迂回・取りこぼし・意味の拡張の 3 つの穴への関門、変異の計画、実装の分割 (docs のみ、branch dev-wave-gen-opt-correctness-gate)
---

## 本文

- 依頼: 新規最適化の創出へ活動範囲を広げる並行 wave の md_3 (`/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_3.txt`、共通指示 `common.txt`)。ユーザーは 2026-09-29 に提案 (`proposal.md`) の (a) に「この形に改めて良い」と答えた (`user-verbatim.txt`)。本文に「新しい仕組みを書くときの正しさ関門」を含む item は着手時の台帳に無かった。設計はこの wave で完了したので完了済みの item は立てず、残る実装を新規 item として起票した。
- 正本: `output/insights/2026-09-29/gen-opt-correctness-gate/README.md` (現状の実測、3 つの穴への設計、変異の計画、実装の分割、限界)。
- 主な結論: 今の関数方策の軸では迂回は構造上起こらない (提案文字列だけ・検疫・許可リスト文法)。段 A・B で読み書きの経路を開くと、trace の R/W と C 行の件数が検証と同じ集合から出ることが迂回の入口になる。workload 側の手順列と値の刻印、既存の commit 件数を独立の出所にした照合を fail-closed で設計した。
- 新事実: stock Silo は同じ取引で同じ key を読んでから書いて読み直すと最初に読んだ値を返し、2 度書くと最初の値を据えるコードになっている (`TxExecutor::read` / `TxExecutor::update`)。値の照合を標準の意味で入れると stock が赤になる見込みで (コードからの予想、未実走)、照合は緩めず CCBench 側の修正を前提条件に置いた。還元判断はユーザー確認待ち (一次資料 §3.5)。
- 軽量版で進めた (段 2・3 なし、実装面の差分ゼロで変異 matrix は免除)。段 6 の read-only review 1 本 (事実照合と規律 2・3 の攻撃の 2 レンズ) は NO-GO、must-fix 5 件 (修正前の D2b を一部の key だけで関門にする段階が「検査を甘くする選択肢」になる、初期版の読みの照合規則の欠落、D5 の走査範囲が既存の証拠面の CMake SOURCES だけでは `include/ycsb.hh` に届かない・C5 の単一理由性、B1 の発火計数、vhash の所要の最大値 6.6 秒の取り違え) と should-fix 3 件。親が実物で検算して全件 real と裁定し修正した。焦点再レビュー 1 巡で GO (残る must-fix 0、partial 1 件は親が直した)。
- エージェント工数: Codex review 1 (gpt-6-sol / medium、13 call、約 184 秒)・focus 1 (同、6 call、約 109 秒)。計算ノードの job なし。worktree の手動 add が 1 回目に「システムコール割り込み」(71% で EINTR) で失敗し、既存 branch を指定した 2 回目に成功した (既知の型)。受入全走はこの記録 commit の後に 1 回行う。

## 次の一手差分

### 新規

- {{T:gen-opt-gate-live-check}} **P2・新規**: 新しい仕組みを書くときの正しさ関門の生死確認。使い捨て patch で workload 側の手順列の記録 (`A` 行) と値の刻印を入れ、stock Silo が手順列と trace の key 集合の照合で 0 件の違反になること、読みを読み集合に載せない変異が赤になること、値の照合の取引内の部分が stock で何件反するかを 1 回ずつ測る。計算は約 0.5 node 時間の試算。根拠: `output/insights/2026-09-29/gen-opt-correctness-gate/README.md` §3.3・§7 の U0。
- {{T:gen-opt-gate-trace-witness}} **P2・新規**: 同関門の記録と判定器。CCBench の trace 計装 (`include/ycsb.hh`・`include/trace.hh` の `#if TRACE` 内、D16 の izanagi-trace 枝) に手順列と値の刻印を足し、判定器に手順列の照合・版と値の照合・取引の意図と値の照合・emitter の証拠面を足して意味の版を上げる。{{T:gen-opt-gate-live-check}} の後。根拠: 同 §3.2・§7 の U1・U2。
- {{T:silo-intra-txn-value-fix}} **P2・新規、還元判断はユーザー確認待ち**: stock Silo の `TxExecutor::read` を書き込み集合から先に探し、`TxExecutor::update` の 2 度目の書きで値を置き換える修正 (D16 の本物のバグ修正)。gen-opt の certified は取引の意図と値の照合を全 key で通すことを要求するので、この修正は gen-opt の評価開始の前提条件である (修正前に一部の key だけで照合する段階は関門にしない)。修正後の stock は別 build として扱い、修正前の測定は当時の事実として残す。採られなければ gen-opt の評価を始めずにユーザーへ判断を返す。根拠: 同 §3.5・§7 の U1b。
- {{T:gen-opt-gate-grammar}} **P2・新規**: 同関門の受理文法と骨格 API。gen-opt の候補を提案文字列の経路だけで受け、tuple への読み書きを骨格の関数に限り、trace・counter・集合の名前を許可リストに入れない。段 A の試し候補 (並行 wave md_2) が決まってから API を確定する。根拠: 同 §3.1・§7 の U3。
- {{T:cc-model-check-harness}} **P2・新規**: 仕組みごとの小さいモデルでの全場面検査の共通部品。`tools/vhash_forwarding_model/` から探索・閉路判定・場面の全列挙生成・反例の閉じた schema を切り出し、検査器自身への変異と自走 harness・inventory の登録を含める。根拠: 同 §4・§7 の U4。
- {{T:gen-opt-gate-driver}} **P2・新規**: gen-opt の driver に、仕様の digest ごとの小モデル結果を build 前に要求する関門 (欠ければ拒否) と、反例を閉じた field で `self_history` へ返す経路を足す。{{T:gen-opt-gate-grammar}} と {{T:cc-model-check-harness}} の後。根拠: 同 §4.4・§7 の U5。
- {{T:gen-opt-gate-mutation-run}} **P2・新規、計算はユーザー確認が要る**: 迂回の変異 7 本と負例 4 本を trace build で走らせ、事前登録した期待と照合する。試算約 2.3〜2.9 node 時間 (2 node 時間以上)。{{T:gen-opt-gate-trace-witness}} と {{T:silo-intra-txn-value-fix}} の後。根拠: 同 §3.4・§7 の U6。
- {{T:auditor-gen-opt-types}} **P3・新規**: auditor の入力に仕様の規則一覧・小モデルの結果の要約・Q1〜Q8 の申告を足し、型 27〜30 を追加する。role 本文の変更前 sha256 で pin を検索し、変更前後を同じ入力で比べる。根拠: 同 §6・§7 の U7。
