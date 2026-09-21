---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-21
wave: dev-wave-silo-function-synthesis-space
seq: 2
---

## {{D:silo-function-policy-axis}}. Silo の待機と lock 競合応答を関数単位で合成する軸 `silo-function-policy` を条件付き採用する — LLM には方策だけを開き、受理する C++ を型付きの部分言語に閉じ、状態は worker 内に 1 個だけ置く

**決定:** VLDB 方針のユーザー裁定 項 3 (LLM が関数単位でコードを書ける合成空間を開く、正しさゲートは不変) を受け、軸オンボーディングの段階 B として軸 `silo-function-policy` を条件付き採用する。設計の正本は `output/insights/2026-09-21/silo-function-synthesis-space/README.md`、各レンズの逐語は同 dir の `verbatim/`。実装・計算投入はしていない。

1. **境界は方策と仕組みの分離。** LLM が書くのは 3 関数と補助関数・状態型だけ。
   - abort 後の待機量を返す関数
   - lock 競合時に retry / abort を返す関数
   - 成功 commit 時に自分の状態を更新する関数
   CAS・unlock・absent 検査・validation・tid 生成・writePhase・trace・同じ txn の再試行は、人間が一度入れる骨格が持つ。validation と lock の仕組みは v1 で開かない。
2. **安全の主張は条件付きに限る。** 「メモリ安全・外部干渉なし・契約適合の方策が正常に返る限り、方策の選択は固定骨格の直列化可能性条件を弱めない」までを言う。任意 C++ の適合性、全実行の正しさ、停止性、公平性、verify と perf で同じ分岐を踏むことは構成上保証しない。certified は有限の観測履歴についての判定である。v1 は「LLM が壊した CC 論理を verifier が捕らえる」ことを実証しない。
3. **置き場は `cc/silo/transaction.cc` の include 列の後の単一 EVOLVE-BLOCK。** 既存の編集面・`ALLOWLIST` の中で、拡張は要らない。
   - 骨格型は `izanagi_silo_api` に置き、単独 TU 用の api header と同じ正本から作る。
   - hole は `izanagi_silo_policy` の本体だけとし、namespace の外枠は marker 外の骨格に置く。
   - 骨格 helper と状態の実体は hole の後の `izanagi_silo_skel` に置く。
   - 骨格からの呼出しは完全修飾の noipa wrapper 経由、action の判定は組込型比較とする。
   - 軸 macro `SILO_POLICY_VARIANT` (既定 0) では、領域・骨格・呼出し点がすべて消えて inert になる。
   - 軸 ON で `BACK_OFF` が 1 でない、または no-wait 系 flag が固定値 (1 / 0) でなければ `#error` にする。
4. **受理する C++ は、型付きの許可リスト部分言語 policy-C++ v1 に閉じる。**
   - 算術・bit・shift の被演算子は `uint32_t` (= `unsigned int`) / `uint64_t` (= `unsigned long`) だけ。`bool` は論理・比較・条件・`static_cast` にしか使えない。
   - 整数 literal の接尾辞は `u` / `ul` だけ。結果の型は C++17 の通常算術変換に従う (`/ %` も同じ)。
   - `/` `%` `<<` `>>` とその複合代入の右辺は literal だけ (除数は非零、shift 量は左辺の型の幅未満)。
   - 宣言・引数・戻り値に使える型を列挙で閉じる (README §2.7)。
   - 初期化子の中で宣言中の変数を参照しない。非 void 関数の最後の文は `return` とする。
   - 代入・複合代入は独立した文としてだけ書ける (部分式に埋め込まない)。`++` `--` とカンマ演算子は禁止する。
   - 禁止: pointer・配列・loop・再帰・記憶域指定子・template・演算子 overload・例外・代替綴りと digraph・`__` を含む識別子。
   - 識別子は名前解決し、自前の宣言・骨格型・許可した標準の 2 関数だけを指すことを要求する。
   - 機械執行は build 前の 4 段: 既存の DiffQuarantine、既存の effect gate、型付きの構文検査、候補本文を CC ヘッダ抜きの単独 TU で `-Werror` compile する検査。
   - この構文検査が既存 hole の閉じた領域制約に代わるのは、この軸だけである。既存 3 軸の受理集合は変えない。
5. **状態は、骨格が所有する `thread_local` の 1 個を参照で渡す。**
   - 寿命は worker thread で、骨格は reset しない。成功 commit ごとに方策へ通知する。
   - hole は書換え可能な持続状態 (静的・thread 記憶域の可変変数) を定義しない。namespace scope の `constexpr` 定数は不変なので書ける。
   - 観測は abort 要因 (骨格が 7 記録点で記録)、同じ tuple での lock 試行番号、骨格の乱数だけ。
   - 時刻・set の大きさ・競合位置・共有状態は渡さない。thid・key・pointer・epoch・FLAGS・計測カウンタは、受理契約と単独 TU compile で参照できない。
6. **待機の上限は骨格が持つ。** abort 後 1000 µs、lock の 1 回 50 µs、tuple ごとに 32 周回で、CAS 失敗も数える。待機後は再読込し、上限到達・abort・未知の action は stock の abort 出口を通す。これは全生成器に共通の試走設計値で、最適値ではない。
7. **探索の共通表現は領域の C++ 本文、identity は既存の source_digest。**
   - random / sweep / 非 LLM 進化は型付き有限 IR (policy-C++ v1 の部分集合、停止と算術安全を構成で保証) の上で動く。
   - 比較は 2 つに分ける。同じ IR 上の探索法比較 (非 LLM×IR と、IR JSON を出して同じ IR admission・renderer を通る LLM×IR) と、LLM×C++ による空間拡張の比較である。最小の arm はこの 3 つ。BO は後段とする。
   - LLM×C++ の全候補と比較の全 arm に、legacy と性能構成の両方の verify を適用する。
8. **planner は外す。**
   - 兄弟 driver と tool なしの coder role (C++ 版と IR 版の出力形) を新設する。coder の justification は台帳に残すが、critic と次の coder には渡さない。
   - LLM 由来の候補には auditor の digest gate を通す。非 LLM の IR 候補は auditor 段を省くが、全系列の endpoint 候補と勝ち候補に公平性の目視を課す。
   - auditor の目録に、名前解決の乗っ取り・マクロ識別子による判別・保存域の迂回・メモリ安全の迂回・hook 別の空振りを足す案を置く。
   - `.claude/agents/` の変更はユーザー明示承認を条件にする。

**実装着手前の必須条件:**
- 受理契約を、coder の接続仕様 (C++ 版と IR 版) と検査器の両側で一致させる。
- 骨格仕様を固定する (namespace の外枠、完全修飾と noipa、lock の周回上限の位置、再読込、prefix unlock、要因の 7 点写像、`BACK_OFF` と no-wait flag の `#error`、api header の単一正本)。
- 正例・負例・検査器の自己試験を事前登録する。
  - inert / honest identity
  - 既存 3 負例 (norw・lockskip・early-unlock) を軸 ON の経路に積み直し、即 abort と最大待機の 2 方策で走らせる
  - 機構の変異 (3 hook の配線解除を含む)
  - 契約負例と検査段ごとの自己試験、UBSan harness 1 回
- C 段のタスク合計の node 時間を見積もり、投入前にユーザー確認を取る (設計時の換算は 2.41〜4.12 h)。
- 手順書 §4 の第 3 列と planner 例外を、C 段の前の docs 変更で反映する。

段の順序は C (骨格・検査・手書き方策の生死確認) → D (IR の機械偵察、投入前に確認) → 人間判断 → E (driver・role、承認) → F (別セッション) とする。条件付き採用は実装完了ではない。

**理由:**
- 既存の軸 (値 1 個・79 値・5 bit) は列挙し尽くせる。B-5 試走の LLM・random・sweep の差は 1.06% で、床 3% の内側だった。LLM の出番を測るには、関数を書く空間が要る。
- 段 2 の草稿と段 3 の 3 レンズ (codex 2 本 + auditor role) が、いずれも adopt_with_conditions を返した。
  - include より前に領域を置いて CC の大域を未宣言にする親の当初案は不成立である。最初の CC include で `std::atomic` と CC の大域が同時に見える。
  - 「構成上壊せない」という親の主張は、自由 C++ の未定義動作を無視していた。
  - 草稿の封じ込めには、骨格の文面を変えずに意味を変える穴が 4 つあった (auditor)。マクロ識別子と大域への到達、保存域の非排他、同じ namespace での overload による名前解決の乗っ取り、局所変数のメモリ安全である。
  - いずれも、部分言語・単独 TU compile・骨格所有の状態・別 namespace で閉じた。
- 段 4 後の版の焦点再レビューで、codex は NO-GO (must-fix 8)、auditor は条件付き採用を維持 (must-fix 2) とした。指摘は次の 3 点で、型付きの規則・自己参照禁止・return 位置規則・字句段の全拒否で閉じた。
  - bool の `int` 昇格による signed overflow と負値 shift、初期化子の自己参照、`-fsyntax-only` で return 欠落が警告されないこと。これらは型をそろえるだけでは除けない。
  - 代替綴りと digraph で、pointer と添字の禁止を迂回できること。
  - 状態の射程について、各レンズの判定の要約が逐語を超えていたこと。
- 型付きの部分言語は、OOB・signed overflow と負値 shift・初期化前読出し・非停止・return 欠落・過大 shift と零除算を構造的に除く。そのため、候補ごとの sanitizer は要らない。検査器の誤りは、C 段の UBSan harness 1 回と検査段ごとの自己試験で見る。
- validation を開かない理由。既存の検出力の証拠 (lock 被覆検査・broken patch の負例) から、LLM が書いた CC 機構への検出力は一般化できない。機構を開く後続版の前提は、検出力の測定 (差分分析 P0) である。
- 状態の射程は択一であり、各レンズの立場は次のとおり。
  - レンズ A は txn 内状態を推奨した。txn 内でも局所的な競合適応は表現できると明記している。worker 内の txn 間履歴は型 3・12・15 を増やすが、メモリ安全で骨格が固定なら害は進行性・性能・一般化に留まる、と判定した。
  - レンズ B は、worker 内の限定した txn 間履歴と成功通知を推奨した。
  - auditor は txn 内状態を支持した。txn 間履歴と共有状態を併せた場合、契約が守られる限り害は性能値の歪みに留まる、と判定した。ただし例外を 2 つ付けた。data race と、型 3 と組んで認証した経路と計測した経路が別になることである。
  - 親は、依頼が名指しした「競合の状態に応じた待機方策」のうち、txn をまたぐ負荷追従を表現するため worker 内の txn 間履歴を採った。auditor の例外は次のように扱う。
    - data race は、共有状態を入れないことで除く。
    - 型 3 の留保は、全候補への性能構成の verify と、「verify と perf で同じ分岐を踏んだとは言えない」という報告上の限定で扱う。
  - 根拠のユーザー裁定は項 3 と依頼文である。D48 の読取禁止は trigger 軸の契約として不変で、D1409 が保留した trigger 軸の問いも解消・変更しない。両者は新しい軸での代理の許容を承認した根拠ではない。
- 上限付きの lock 待ちは auditor 目録の型 10 (no-wait の wait 化) と同じ害を持たない。取得順は sort 済みで deadlock せず、上限もある。残る convoy と偏りは性能側の限界として記す。

**却下した選択肢:**
- include の前に領域を置く封じ込め — 必要な型と禁止したい大域が同時に見える。
- 別 TU に分ける — protocol の CMakeLists と `ALLOWLIST` の変更を要する。
- validation・lock の仕組みを v1 で開く — 検出力の一般化の根拠がなく、certified の意味が保てない。
- 状態を txn 内に限る (レンズ A と auditor の支持) — 局所的な競合適応は表現できるが、txn をまたぐ負荷追従を表現できない。部分集合として残る (方策が on_commit で自ら reset すれば再現できる)。
- 共有状態・時刻を v1 で渡す — worker 選出・協調的な liveness 崩し・data race の経路が増える。
- 許可する型を unsigned 中心にするだけで UB を除いたとする — bool・比較結果の `int` 昇格が残る。部分式ごとの型規則が要る。
- 候補ごとの sanitizer harness、候補ごとの TRACE hook 計数と PIN 前進、新しい X 理由、per-worker commit 分布の記録 — 次の理由で見送る。
  - 型付きの部分言語と既存の `trace-timeout` で足りる。または ALLOWLIST 外である。
  - lock 方策は既定で「verify 中の発火証拠なし」と表示する。公平性はコードの形の発火条件で見る。
- IR と自由 C++ の比較を「同一空間比較」と呼ぶ — 到達可能な集合が違う。
- planner-v4 の再利用 — 増加 / 低下の方向契約が複数 hook・状態型に合わない。
