---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-20
wave: dev-wave-t1283-launch-authority-design
seq: 1
---

## {{D:acceptance-gate-launch-authority-insight}}. launcher 起動 authority を main 起点 gate へ分離する設計を、将来 (a) 再訪時のために記録する

**決定:** D569 の (c)「現状維持・新規実装なし」は変更しない。T-1283 が指す残余 (i) (改変された
tip 側待ち手が `tools/acceptance_launcher.py` を経由せず受領証を自作できる) を将来
(a) (待ち手にも bootstrap 層を新設) として再訪する際の具体設計を、次の内容で**記録するに
留める。実装は承認しない。**

1. **確認した事実。** 現行 `tools/dev_wave_land.py` の独立検証 (`_verify_acceptance_receipt`
   / `_valid_fingerprint`) は、launcher/waiter/runner の blob 内容 SHA-256・
   tested_main/tip 等値・fingerprint の形式・verdict 別の構造的自己無矛盾のみを検査し、
   **「launcher が実際に起動されたこと」を独立に証言する field を持たない**。加えて
   `tools/acceptance_launcher.py` 自身の receipt 生成は、`pre_fingerprint`
   (`_Config` の CLI 引数、`acceptance_launcher.py:85`)・`post_fingerprint`・
   `effective_scheduler`・checker 系 field・`red_nodeids`/`flake_nodeids`
   (いずれも `completion_reader()` 経由で待ち手から供給、`acceptance_launcher.py:461-463`) を
   **待ち手からの自己申告のまま**採用する。launcher 自身が独立に検証・再計算するのは
   `child_rc`・`log_sha256`・`runner_executed_sha256` の3値だけである
   (`acceptance_launcher.py:436-450`)。
2. **設計方向 (将来候補、未実装)。** 「launcher 呼び出しの実行権限」だけを待ち手から抽出し、
   常に `tested_main` から起動される最小 gate に閉じ込める案は、T-1373 当初案が
   D403 と衝突した理由 (待ち手全体を main から起動し、tip 編集を反映しなくなる) を
   回避できる可能性がある — waiter・runner 自体は tip 実行のまま残せるため。
3. **この設計候補が閉じる範囲 (仮に将来実装した場合)。** 親が常に main 起点 gate を起動し、
   gate が launcher の process 起動と receipt publish を独占し、land が gate の
   execution record と receipt の結合を要求する、という3条件が揃えば、tip 側待ち手が
   launcher を一度も呼ばずに `child_rc`/`log_sha256`/`runner_executed_sha256` を
   偽装する経路は閉じる。
4. **この設計候補が閉じない範囲 (未解決のまま記録する)。**
   - gate の launch 対象である**親の起動点自体**が、wave 相対 path で待ち手を直接起動する
     現行 runbook 記法 (`docs/pegasus-runbook.md` §7.3) のままなら、待ち手が gate 呼出しを
     省略する経路は残る。gate 側の設計だけでは閉じない。
   - gate 自身が `tested_main` から不変 bytes として起動される保証は、PATH・symlink・
     `python3`/`git` の名前解決・cwd を通じた差し替えを排除する trust root を別途設計
     しない限り成立しない。改変された gate が自身の `gate_source_revision`/
     `gate_blob_sha`/`gate_executed_sha256` を自己申告できるなら、F385 と同型の
     自己証明が gate の層で再発する。
   - gate 自体を導入・改訂する wave に許す `tested-tip-bootstrap` 相当の例外は、
     導入期間中の起動 authority を一時的に wave tip へ戻す。「常に main 起点」は
     定常運用限定の主張であり、無条件の保証ではない。
   - `completion protocol` (launcher が待ち手から受け取る `post_fingerprint`/
     `effective_scheduler`/checker 系 field) の exact field 集合検査
     (`acceptance_launcher.py:272-301`) は構造的整形式性だけを検査し、内容の真正性・
     供給元の実行実在を証言しない。launcher 起動権を gate へ移すだけでは、この経路の
     自己申告面 (fingerprint・checker path) は閉じない。閉じるには、checker 起動と
     fingerprint 計算にも同型の gate 分離を再帰的に適用する必要があるが、その具体設計は
     本記録の範囲外とする。
   - (ii) bounded/dispatch 内側の pathname 実行、(iii) land verifier 自身の候補コード性は
     引き続き T-696 の協調境界に残す (対象外)。
5. **検証方法 (設計のみ、テストコードは書かない)。**
   - **negative control**: `tested_main` に regular launcher blob、`tested_tip` に
     regular waiter/runner blob がある fixture で、launcher/waiter/runner を一切実行せず
     v5 receipt を静的に組み立て、`_verify_acceptance_receipt` を直接呼ぶ。全 27 field
     (`acceptance_launcher.py:365-397`) を仕様どおり埋めれば (hash は小文字 64 桁 hex、
     JSON は `acceptance_launcher.py:89-101` の canonical 形式) 現行実装は
     `_acceptance_rejected` を発火せず受理する。これは D524 の独立検証が
     「著者の同一性」(公開 Git 内容の知識) しか証明しないことの直接証拠になる。
   - **positive control (将来 gate 実装後)**: 同じ偽 receipt を、(a) 新 schema
     (v5 fallback なし) が拒否するか、(b) gate の execution record が結合されていない
     receipt を land が gate record 欠落として拒否するか、の2段で検査する設計とする。
     ただし「完成度の高い偽 completion protocol は launcher の exact field 検査を
     すり抜けうる」(整形式性は実行実在の証明にならない) ことを検証方法自体にも明記し、
     この経路を執行実在の証明として過大評価しない。

**この決定が保証する範囲:** D569 は変更しない。実装着手は承認しない。将来 (a) を
外部露出運用への移行時に再訪する際、上記4節の未解決点を先に設計しない限り、
「起動権を wave tip の外へ出す」という目的は部分的にしか達成されない、という
評価水準を残すことが本記録の目的である。

**理由:**
- D569 (2026-08-20) は (c) 現状維持を採用しつつ「(a) の将来的な価値を否定しない」と
  明記した。本記録はその将来再訪のための具体設計を、実装せずに残す。
- T-1283 の元裁定 (rulings 第7回) と D524 は残余 (i) を明示的に未閉鎖のまま記録しており、
  「閉じた」と誤って記録しないことが F385 の記録条件でもある。
- 段3 の敵対相談2レンズが、素朴な gate 案の楽観的な想定 (bootstrap 例外の安全性、
  completion protocol の positive control としての妥当性) に real な欠陥を発見した。
  これを反映せず「gate 案は残余を閉じる」と記録すると、次にこの記録を読む wave が
  過大な保証を前提に実装へ進みかねない。

**却下した選択肢:**
- D569 に反して直ちに実装する — 現在は内部研究用途で悪用動機を持つ主体が実在せず、
  規律5 (段階導入・盛らない) に照らし時期尚早。
- gate 案を「残余 (i) を閉じる設計」として無条件に記録する — 段3 の敵対相談が
  bootstrap 例外・completion protocol 経路に real な未解決点を発見しており、
  無条件の記録は次に読む wave を誤導する。
- 記録自体を見送る — D569 が明記した「将来的な価値」を再導出コストなしに再訪できなくする。
