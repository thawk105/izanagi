## 正しさ境界の所見

以下、`R` は指定 worktree、`J` は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1643-has-include-pair`、`V` は `R/output/insights/2026-07-28/t148-review-verbatim`。repo 内の相対参照は `R` 基準。

1. **「blanket reject だから真偽差は受理集合へ届かない」は射程過大。**
   根拠：`orchestrator/campaign/source_digest.py:1842` は渡された source の字句を走査し、`:1895` は `EVOLVE_BLOCK_SOURCES` の各ファイルだけを渡す。対象は `:85` の３ファイルで、include 先を再帰走査する処理ではない。さらに normalize とマクロ照会は `:1662`、`:1712` で `#include` 行を除去する。
   **成果物への影響：** `include/backoff.hh` 自身の条件式は走査されるが、その先の非対象 header 内の条件式まで拒否されるとはいえない。include 先の式を source として直接 guard に渡して拒否させても、実際の駆動経路の証明にはならない。`J/s2-plan-out.md:95` の実関数確認は「渡した fixture に対する拒否」に限定し、補助 header 列との結合時にもこの区別を残す必要がある。これは現時点で欠陥・偽 cache hit の成立を示す所見ではない。

2. **compute の system `g++` は、条件付きの compiler 選択結果。**
   根拠：`buildcache.py:1838` は compute の場合に `gcc/g++` を返すが、`pipeline.py:1792` と `:1947` は expected manifest を優先する。
   **成果物への影響：** 「admission toolchain 実測」と呼べる列は、対象 admission の manifest 有無・compiler 解決結果と結び付ける必要がある。login の `g++` 11.4.0、同じ requested name、同じ version のいずれも、その結び付けの代わりにならない。段２の `:219`、`:220` の反論は妥当。

3. **式の列挙数や compiler 数から、族全体の安全性へ一般化できない。**
   根拠：`J/s2-plan-out.md:58` の行群は有限の fixture 群。`docs/dev-wave/core.md:69` の DW-G03 は、制度一般化について「異なる producer/consumer で独立に２件」を要求している。同一実体への `g++`／`g++-11` の別名は独立例ではない。
   **成果物への影響：** 言ってよいのは「記録した compiler・argv・cwd・env・入力位置で、この式がこの値／診断になった」。言ってはいけないのは「`__has_include` 族一般が安全」「別 compiler・別 header 探索順でも同じ」。独立２例があっても、本依頼が禁じる制度一般化の追加は scope 外である。

## 整合・実効性の所見

1. **F660 による実測不能は、この設計には必然ではない。既登録の `generic` 経路がある。**
   main 側現物の [`admission_registry.json:52`](/work/1/SFC/tanab/izanagi/tools/pegasus/admission_registry.json:52) は `tools/pegasus/dispatch_compute.py` を `local-ok` と登録している。dispatcher は main と当該 worktree で同一内容だった。

   exact な経路は、probe 作成後、当該 worktree から次の形で呼ぶ既存 CLI である。

   ```bash
   python3 tools/pegasus/dispatch_compute.py --task generic -- python3 tools/t1643_has_include_pair_probe.py
   ```

   根拠：

   - `docs/pegasus-runbook.md:607` は任意 argv の `generic` 投入を明示的に認める。
   - `tools/pegasus/dispatch_compute.py:154` が登録済み task、`:1318` が非空 argv の受理、`:4482` が CLI。
   - 同 `:1583` が compute hostname を要求し、`:1623` が渡された argv を子として実行する。
   - `hooks/guard_bash.py:263` は hook 自身の repo root の登録簿を読み、`:614` と `:1205` が登録判定を行う。計画上の probe は `tools/t1643_...py` で、新設 `tools/pegasus/` 実行体ではない。

   **成果物への影響：** 「login だけで測り admission 未完」以外の選択肢がある。新規投入機構も登録変更も不要で、F660 の絶対 path 迂回にも当たらない。ただし、これは**静的に利用可能な経路の確認**であり、今日のキュー可用性・投入成功・compute 実測成功は未確認。

2. **`generic` で測った compute 環境を、そのまま本番 admission 環境とは呼べない。**
   根拠：dispatcher の `:154` は `env_mode="clean"`、`:335` の保持対象に `CPATH`／`CPLUS_INCLUDE_PATH` 等はなく、`:1406` がその環境を構成する。cwd は `:1585` で repo root に固定される。一方、段２ `:18` は関連環境変数を勝手に消さず再現条件として記録するとしている。
   **成果物への影響：** compute 上の探索・version/hash・probe は実施可能だが、まず「generic の compute 環境での観測」である。本番 admission と探索環境まで対応した根拠がなければ、完全な実 pair の認定は保留する。子の実効 env を記録するという既存計画がここでも必要になる。

3. **login 実行の「自動判定」という説明は配線されていない。**
   根拠：`J/s1-brief.md:85` は一時 probe に runbook §7.0.0 の自動判定を援用するが、`docs/pegasus-runbook.md:379` が挙げる実装は `tools/run_tests.py` と `tools/check_ai_provenance.py`。段２ `:45` の configure は compiler 検査・依存処理も伴い、単なる式の preprocess と同じ軽量性を前提にできない。
   **成果物への影響：** 一時 probe 全体が自動的に資源判定されるとは書けない。compute の既存経路を使う選択は可能。実走しない場合は、configure 未取得列を段２ `:52` の再構成列として残す。

4. **恒久化の scope 越えは確認できないが、成立範囲の表示は必須。**
   根拠：段２ `:120` の一時配置、`:192` の一時対照、`:50` の stdin 化による限界、`:52` の再構成列の区別。
   **成果物への影響：** 一時 probe の正負対照・JSON 記録は依頼内であり、新設 gate と扱う必要はない。ただし、生成 command 由来の探索実測、再構成、header 補助観測、実ガード直呼びを一つの「admission 成功」に畳むと完了主張が過大になる。

5. **規律６違反の具体的な指示経路は、現プランには確認できない。**
   根拠：`CLAUDE.md:91` は CCBench ソース・出力をデータと定める。段２ `:44`、`:48`、`:135` は configure 条件・command・診断を採取する設計であり、外部コメントや診断に作業方針を委ねる記述はない。
   **成果物への影響：** command・response file・stdout/stderr の内容は観測データとして保存する。そこにある指示文から compiler 代替、警告抑制、ゲート省略を採用することは、この設計の許可に含まれない。違反が起きたとの断定や、新規検査の提案は不要。

## 親 brief への反論

1. **既存被覆を「１式だけ」と総称するのは過小で、純増 (b) は過大。**
   根拠：`V/review-focus-claude-closed-partial-table.md:15` は貼り合わせ式の明示的な `0/1` pair を記録する。しかし `V/review-B-codex-layers-and-test-teeth.md:59` には literal の `#define` 間接形、同 `:101` には angle/system header `<atomic>` の preprocess error があり、`V/findings-and-rulings.md:11` と `:15` に採用・修正の記録がある。
   **成果物への影響：** 「明示的な真偽 pair の記録として確認した１式」と限定するべき。間接形・angle・system header の話題全体を未被覆と数えず、今回増える exact 条件、診断分離、header 文脈、compiler 対応を純増として示す。既存記録から、それらすべての完全な pair 実測済みとも断定できない。

2. **D30 系の g++-13 実測は、今回の `__has_include` pair の既測証拠ではない。**
   根拠：`docs/decisions.md:801` の実測対象は `#ifdef __x86_64__`。`:813` は computed include の known-limitation。
   **成果物への影響：** 過去の g++-13 実測自体は維持するが、今回の族の実測件数に加えない。また known-limitation の再記述だけを新知見とも数えない。

3. **過去の compute 不在を、今日の不可能性へ昇格させている。**
   根拠：`J/s1-brief.md:29` の「台帳も一致する」から `:31` の無限定な「実測できない」へ進む箇所。さらに `J/verbatim-rulings.md:62` は補足で「現在の Pegasus には g++-13 が無い」と断定する。根拠の `docs/failures.md:8023` と D293 は過去の記録であり、親の今日の探索は `J/verbatim-rulings.md:128` の login に限る。
   **成果物への影響：** 今日の login は探索範囲付きの不在記録、compute は未探索なら `environment_unavailable`。compute に `compiler_missing` を転記してはいけない。brief `:69` は来歴を明記しているが、それでも本文の断定は支えない。純増 (c) は「不在の初発見」ではなく、今日の環境別の可否確認である。

## 裁定パッケージ候補 (scope 外の real 所見)

- **走査範囲外の include 先について、一般安全性は今回の証拠で確定できない。**
  根拠：`source_digest.py:85`、`:1895`、`:1662`。非再帰の走査境界は実在する。ただし、そこから許可された variant が実際に別挙動・stock identity 継承へ到達するかは未証明。
  **成果物への影響：** 今回は安全性主張の除外範囲として記載する。現行の変更制約を満たす具体的な到達例が実測された場合に限り、その証拠を裁定パッケージ候補へ返す。checker 変更・受理集合変更・新規 gate の実装案にはしない。

## 総括

**既登録 `generic` により、この wave から compute probe を行う静的な経路はある。F660 を理由に login 限定へ落とす必要はない。** ただし、compute 実行だけで admission 環境との対応が完成するわけではない。

親へ戻す必須修正は、blanket reject の走査範囲、既存被覆と純増、過去の不在観測と今日の未測の区別。compiler probe・configure・pytest・投入は実行しておらず、欠陥の成立も未判定。