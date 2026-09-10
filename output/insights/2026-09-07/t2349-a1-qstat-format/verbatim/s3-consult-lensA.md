## 1. 親の二標本だけでは QUE の受理を固定できない

- **(a) 主張:** RUN と PRR の二つの実機逐語だけを見る限り、観測された正規化結果はどちらも `RUN` であり、`QUE` を正例に含める根拠にはならない。plan の正例も二件とも `RUN` なので、`QUE` を誤って拒否する実装が全テストを通れる。
- **(b) 根拠:** `qstat-f-980043.nqsv.txt:7-8` は `Current State = Running`、`qstat-f-980062.nqsv.txt:7-8` は `Current State = Pre-running` で、`Queued` は `Previous State` にしかない。plan の正例も `plan.md:118-119` の二件だけである。ただし別の一次記録として、`F852.md:7-10` は実機の `Current State = Queued`、`D805.md:10-18` は `Staging` と別走の `Queued` を記録している。このため canonical domain `{QUE, RUN}` 自体は追加資料により支持される。
- **(c) 成果物への影響:** `QUE` 正例が無いままでは writer が実質 `{RUN}` でも通り、正常な queued または staging 投入が fail-closed する。A-1 は bench 前に止まり、brief が述べるとおりレポートと台帳へ A-1 の行が入らない。A-1 は non-certifying なので certified 選択値を直接変えるものではない。
- **(d) 判定:** **real**。受理集合そのものより、親 brief の根拠提示とテスト被覆が不足している。`Current State = Queued` と `Staging` をそれぞれ canonical `QUE` として通す統合正例が必要である。

## 2. 共有 parser の利用だけでは実機書式へ限定されない

- **(a) 主張:** plan は canonical state を `{QUE, RUN}` に絞るが、raw input の受理集合は実機で観測した `Current State` 書式より広い。実機 queue 行と、旧式の `Request State = QUE` または `State = RUN` を組み合わせた hybrid が受理されうる。
- **(b) 根拠:** 共有 leaf は `scheduler_nqsv.py:17-20` で `Request State`、`Current State`、`State` の三形式を認識し、`:44-66` では `waiting`、`wait`、`queue`、`stg`、`held`、各種終了語も正規化する。plan の producer 条件は正規化結果が `{QUE, RUN}` であることだけである (`plan.md:16-18,42-57`)。一方、D805 は証拠の無い `Request State` 枝の温存を明示的に却下している (`D805.md:23-29`)。
- **(c) 成果物への影響:** 実機で到達可能と確認していない state-field 形式でも visibility receipt が作られ、後続の completion、materialization、レポート台帳へ「投入時に可視だった」という証拠として入る。未知語 `Launching` を拒否しても、この hybrid は落ちない。
- **(d) 判定:** **real**。値の正規化は共有 leaf に任せつつ、A-1 producer では state field が `Current State` であることを別の構造条件として要求すべきである。少なくとも `Request State = QUE`、`State = RUN`、複数の整合 state field を実機 queue 行と組み合わせた負例が必要である。

## 3. 「12 語は過去だけ受理する」は実装上成立しない

- **(a) 主張:** schema version を変えずに reader の 12 語を維持すると、`STG`、`HLD`、`EXT`、`MIG`、`SUS` などは過去 receipt だけでなく、今後作られた任意の同 schema receipt でも受理される。「legacy read only」という境界は存在しない。
- **(b) 根拠:** reader は origin や作成時期を見ず、単純な集合 membership だけを使う (`paper_story_a1_paired.py:2982-2984,3537-3542,3583-3591`)。特に prior visibility の 12 語 membership は disappearance を認可する条件になる (`:3571-3610`)。plan 自身も schema と reader 集合を維持するとしている (`plan.md:20-38`)。射影されたテスト内で構築される submission receipt の state は `QUE` だけである (`test_paper_story_a1_paired.py:702-725`)。brief の「過去 receipt に STG」という主張 (`brief.md:45-46`) と plan の引用 (`plan.md:128`) には、実 receipt の path、bytes、hash、state inventory が伴っていない。
- **(c) 成果物への影響:** 例えば `state=HLD` の receipt も prior visibility として通り、その後の disappearance completion を認可できる。これにより scheduler 証拠が曖昧でも group completion と materialization が通り、レポートと台帳の complete 状態が変わりうる。
- **(d) 判定:** **real**。author 前に実在 receipt を列挙し、path と state の実値を確定すべきである。reader 集合は「新 writer の `{QUE,RUN}` と実在 legacy 値の和集合」に限る必要がある。それでも legacy 値を将来 receipt から排除できないため、D805 を厳密に満たすなら submission schema を version 分離し、新 version は stdout を再解析して `{QUE,RUN}` だけを受理する必要がある。scope を広げないなら、この矛盾は親の明示裁定が必要である。

## 4. A-1 reader は qstat stdout を再検証できず、membership が恒真になる

- **(a) 主張:** 新 writer が `{QUE,RUN}` と `gen_S` しか書かないなら、直後の reader にある「state が 12 語」「queue が gen_S」という条件は新規 producer 出力に対して常に真である。これは後方互換性の確認であり、scheduler 観測の有効性検査ではない。
- **(b) 根拠:** producer の返却値には state、queue、時刻しかなく、qstat stdout、stderr、rc は保存されない (`paper_story_a1_paired.py:2892-2898,3297-3304`)。reader の検査は保存値への membership に留まる (`:2982-2989,3537-3552`)。対照的に A-2 は receipt の qstat stdout と stderr を保持し (`paper_story_a2_certification.py:1113-1128`)、共有 parser で stdout を再解析して保存 state と一致させる (`:1150-1178`)。
- **(c) 成果物への影響:** reader が実際に落とすのは、12 語外の値、`gen_S` 以外、型、時刻、ID 不一致だけである。raw qstat と保存 state の不一致や、12 語内への改変は落とさない。その receipt は acquisition、completion、consumer、materializer まで再利用される (`paper_story_a1_paired.py:6493-6508,8342-8351,8384-8397`)。
- **(d) 判定:** **real**。新 submission schema に qstat stdout、stderr、returncode を持たせ、consumer が共有 parser、queue parser、canonical state を独立再検証するのが安全な解決である。schema を維持する場合、reader の membership を「有効性検査」と説明してはならない。

## 5. terminal の writer と legacy reader も分離されていない

- **(a) 主張:** P3 の「terminal parser を変更しない」は reader 互換だけでなく、新 producer にも旧 PBS 型の `scheduler-end-state` を書かせ続ける。到達不能枝を過去読取り専用にする設計にはなっていない。
- **(b) 根拠:** `_parse_qstat_terminal` は旧式の state と exit status を解析する (`paper_story_a1_paired.py:547-564`)。production の `_observe_scheduler_terminal` 自身がこの parser を呼び、`scheduler-end-state` を新規作成する (`:3746-3792`)。既存テストの terminal 正例も実機 NQSV 逐語ではなく `State: EXT` である (`test_paper_story_a1_paired.py:819-845,3438-3468`)。plan は実機終了形を disappearance と認めつつ枝を残す (`plan.md:59-71`)。
- **(c) 成果物への影響:** 旧式または合成された qstat 出力が新規 terminal receipt として受理され、scheduler terminal reason、state、exit status がレポートと台帳へ入る。group completion と materialization も同じ validator を通る。A-1 の `formal=False`、`promotion_prohibited=True` は維持される (`paper_story_a1_paired.py:4135-4140`) が、A-1 成果物の complete 判定は変わりうる。
- **(d) 判定:** **real**。新 producer は実測済み disappearance だけを書き、旧 visible-terminal は versioned legacy reader だけに残すべきである。schema を分けない限り、「過去だけ」という主張は P1 と同じ理由で成立しない。

## 6. 負例 matrix は主要な弱実装を殺せない

- **(a) 主張:** plan の負例は未知語、wrong queue、duplicate queue、non-signature disappearance には効くが、共有 parser の利用、producer の `{QUE,RUN}` 制限、stderr 条件、target binding の全条件を固定できない。
- **(b) 根拠:** 提案 matrix は `plan.md:114-128`。`Launching` は共有 parser 自体が `None` にするため、author が `{QUE,RUN}` membership を忘れて全 canonical state を受けても落ちる。`HLD` または `Completed` ならその欠陥を殺せる。submission の不存在負例は現行実装でも request ID、state、queue が無いため既に拒否される (`paper_story_a1_paired.py:2885-2891`)。また matrix には、非零 rc、非空 stderr、wrong または duplicate Request ID、state-before-ID、duplicate/conflicting state field、legacy `Queue: gen_S`、別 server、queue-before-ID が無い。
- **(c) 成果物への影響:** ローカルの弱い regex を残した実装、共有 parser の target-bound 条件を迂回した実装、`HLD/END` まで submission-visible とする実装、stderr を無視する実装がテストを通り、誤った visibility receipt を proof chain に入れられる。
- **(d) 判定:** **real**。追加すべき最小変異は、`Queued` と `Staging` の正例、`Held` と `Completed` の負例、旧 state-field hybrid、wrong/duplicate ID、state-before-ID、duplicate/conflicting field、非零 rc、非空 stderr、旧 queue syntax、別 server、queue-before-ID である。テストは subprocess と時刻だけを差し替え、共有 parser や対象 helper 自体を stub してはならない。

## 7. disappearance の stdout 完全一致は概ね妥当だが、実測 fixture が欠ける

- **(a) 主張:** 「完全一致は必ず締めすぎ」という攻撃は refuted である。単一 ID を問い合わせるこの経路では、別の非空行、複数 request、権限診断を許す方が受理集合を不当に広げる。ただし実測 raw bytes が射影されておらず、正常な改行変種に対する availability risk は未評価である。
- **(b) 根拠:** A-1 は常に `["qstat", "-f", request_id]` の単一対象で呼ぶ (`paper_story_a1_paired.py:3750-3755`)。A-2 の先例 regex は leading/trailing horizontal whitespace と通常の optional LF/CRLF を許し、それ以外を fullmatch で拒否する (`paper_story_a2_certification.py:85-88,1235-1240,1760-1765`)。したがって「末尾 LF だけで落ちる」は誤りである。一方、今回の disappearance は raw file ではなく brief の説明だけで (`brief.md:34-35`)、plan の fixture もその説明から作るとしている (`plan.md:112`)。
- **(c) 成果物への影響:** 条件を緩めて任意の追加行を許すと、permission error や別 request の診断を disappearance と誤認して complete にできる。逆に実機が余分な空行を通常出力するなら、現在案は正常 completion を fail-closed し、レポートと台帳の materialization を止める。
- **(d) 判定:** 「追加行も許すべき」は **refuted**。ただし raw fixture 不在は **real** な証拠不足である。親は stdout の実バイト、stderr、rc を保存してから grammar を固定すべきである。許容するなら「空白だけの行を除いて非空行がちょうど一つ、その一行が対象 ID の signature」という上限までとし、他の非空行、複数 ID、permission 文は拒否する。

## 8. 空 stderr 条件は consumer が再検証できない

- **(a) 主張:** plan は producer と consumer の双方で `stderr == ""` を要求したように記述するが、A-1 completion schema は qstat stderr を保存しないため、consumer 側では検査不能である。
- **(b) 根拠:** plan の P4 は空 stderr を論理積に含め (`plan.md:79-94`)、schema は変えないとしている (`:94`)。実際の `scheduler_terminal` key 集合には qstat stderr が無い (`paper_story_a1_paired.py:3678-3688`)。producer の返却 dictionary にも無い (`:3766-3775,3783-3791`)。A-2 は terminal receipt に stderr を持ち、空文字を検査する (`paper_story_a2_certification.py:1213-1226`)。
- **(c) 成果物への影響:** stdout が正確な disappearance signature でも stderr に warning や権限診断が出た観測を、保存後の consumer は正常観測と区別できない。completion receipt の再検査、group completion、materialization、レポート台帳が空 stderr を証明したように見える。
- **(d) 判定:** **real**。completion schema に `qstat_stderr` とその hash を追加して再検証するか、少なくとも「空 stderr は producer-only 条件であり、artifact consumer は証明できない」と成果物の主張を狭める必要がある。

## 9. 共有 leaf を source closure 外に置く案は provenance を欠く

- **(a) 主張:** 新たな直接依存を import しながら source binding の列挙から外す案は、即時の受理集合拡大ではないが、成果物が列挙する parser provenance を不完全にする。
- **(b) 根拠:** source path 集合には `scheduler_nqsv.py` が無い (`paper_story_a1_paired.py:161-179`)。source binding は列挙された path だけを hash 化し (`:4383-4407`)、consumer も同じ列挙だけを再検査する (`:7199-7223`)。plan は import を追加しつつ closure を変えない (`plan.md:16,157,166`)。一方、submit と materialize は HEAD 一致と clean tree を要求するため (`paper_story_a1_paired.py:3225-3228,7207-7208,7231-7233`)、現在の run で別 bytes を読み込む直接経路は抑えられている。
- **(c) 成果物への影響:** runtime の即時誤受理は HEAD pin により抑えられるが、レポートと台帳の `source_binding.files` に投入 gate の実装本体が現れない。「どの parser bytes が state を認可したか」という source-routed evidence が欠落する。
- **(d) 判定:** **real**。受理集合バグではなく provenance バグであり、nit ではない。共有 leaf を A-1 source closure に追加するか、HEAD pin のみを authority とするという明示裁定が必要である。

## 10. 絶対規律 2 への混入

- **(a) 主張:** 現在の plan に benchmark verifier、correctness gate、anomaly 判定を緩める変更は見当たらない。
- **(b) 根拠:** brief は scheduler 観測二経路だけを scope とし、correctness gate を明示的に除外する (`brief.md:9-17,24-26`)。plan の変更表も submission visibility、scheduler completion、関連 receipt validator とテストに限られる (`plan.md:96-109`)。
- **(c) 成果物への影響:** 計画どおりなら性能値、verifier 結果、anomaly 判定の受理集合は変わらない。変わるのは scheduler evidence により completion と materialization へ進める集合である。
- **(d) 判定:** **refuted**。ただし scheduler receipt validator も proof chain の gate なので、単に「correctness verifier ではない」ことを理由に上記の受理集合問題を許容してはならない。

## 総括

plan はこのまま author へ渡せない。最大の問題は、writer と reader を論理上だけ分け、schema と保存証拠では分離していないことである。12 語 reader と legacy terminal branch は「過去だけ」ではなく将来 receipt にも到達可能であり、D805 の到達不能枝禁止と衝突する。

親が先に裁定すべき事項は次の三つである。

- 実在する A-1 receipt の state と terminal reason を path、bytes、hash 付きで棚卸しし、legacy 受理集合を実値へ縮める。
- 新 submission/completion schema を設け、qstat stdout、stderr、rc を保存して consumer が再解析する。scope を維持して schema migration を拒むなら、legacy 枝温存を D805 の明示例外として裁定する。
- test matrix に canonical `QUE` 正例、`HLD/END`、旧 field hybrid、共有 parser の target-binding 変異、rc/stderr、queue binding 変異を追加する。

disappearance の単一行 fullmatch 自体は fail-closed として妥当である。ただし brief の文章から fixture を再構成せず、実測 raw bytes を保存して通常改行と空白の許容範囲を固定すべきである。