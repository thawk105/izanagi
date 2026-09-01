## 検算した主張

静的検査のみ実施した。ファイル変更・ビルド・テスト実走は行っておらず、緑は主張しない。

| allowlist 観測 | 定義性・union | data race | reward hack | 独立判定 |
|---|---|---|---|---|
| `max_rset_.obj_` | 通常構築時と `begin()` で `obj_=0`。更新元 `check.obj_` も先に代入されるため、hole での直接読取は非活性 union member 読取ではない。([transaction.hh:68-75](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/cc/silo/include/transaction.hh:68), [transaction.cc:55-59](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/cc/silo/transaction.cc:55), [transaction.cc:449-475](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/cc/silo/transaction.cc:449)) | 単一 owner 未証明。非 atomic な書込とhole読取が並行すれば UB | raw word から epoch、TID 世代、lock/latest/absent の符号化を観測可能 | 草案どおりの raw allowlist 採用は不可 |
| `max_wset_.obj_` | 同じく定義済み。更新元 `expected.obj_` は共有 tuple からの load 後に設定され、`max_wset_` へコピーされる。([transaction.cc:145-192](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/cc/silo/transaction.cc:145)) | 同上 | first-lock conflict では 0、途中 conflict では部分最大値となり、施錠進捗・transaction shape・record 世代を分類可能 | 草案どおりの raw allowlist 採用は不可 |

- `abort()` の全 caller は射影資料に無く、全経路が `begin()` を通ることは確認不能だった。ただし不定値読取という狭い懸念は constructor の 0 初期化だけで反証できる。`begin()` を欠く経路があっても値は stale になり得るだけで、不定にはならない。([transaction.hh:68-86](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/cc/silo/include/transaction.hh:68))

- `Tidword` は `obj_` と bitfield struct の union である。両 `max_*` 自身は `obj_` が活性だが、CC 本体は tuple の bitfield 書込と `obj_` 読取を混用しており、処理系依存の union type-punning に既に依存する。これは今回の直接読取が新設する UB ではないが、「bitfield 名を禁止したので union 問題全体が消える」とは言えない。([tuple.hh:12-30](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/cc/silo/include/tuple.hh:12), [tuple.hh:40-53](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/cc/silo/include/tuple.hh:40))

- starvation 条件は構成できる。worker A が同じ先頭 record を解放直後に再取得し続け、worker B が毎回 `expected.lock` で abort する schedule では、B に queue や優先権はなく、gate が常に false なら symmetry-breaking の待機もない。([transaction.cc:155-164](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/cc/silo/transaction.cc:155), [transaction.cc:27-52](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/cc/silo/transaction.cc:27)) 一方、write set は施錠前に整列されるため、単純な「A は X→Y、B は Y→X」で全員が永続的に abort する livelock はこのコードからは構成できない。([transaction.cc:383-438](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/cc/silo/transaction.cc:383))

- gate は現在の abort 後処理では GC と集合 clear の後に位置する。したがって serializability の反例は得られなかった。待機省略は epoch/leader/GC のタイミングやメモリ滞留、starvation には影響し得るが、示されたコードでは unsafe な早期回収や commit 経路改変には直結しない。([transaction.cc:27-52](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/cc/silo/transaction.cc:27), [transaction.cc:700-721](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/cc/silo/transaction.cc:700))

- 旧偵察の実測は一次 insight と整合し、軸が生きているという二値は検算した。拡張後も旧候補を完全に同じ意味で受理する場合に限り、「上位集合なので生存」は成立する。勝ち候補・数値・順位は転記しない。([recon:78-97](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/output/insights/2026-07-11_s8a-trigger-gating-recon.md:78))

## must-fix

1. raw `.obj_` は禁止した proxy を内包している。

   `Tidword` の上位 32 bit は epoch、次の 29 bit は TID、低位には状態 bit がある。commit TID は観測最大値、worker の直前 TID、thread-local epoch から作られて tuple に格納される。([tuple.hh:12-24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/cc/silo/include/tuple.hh:12), [transaction.cc:557-582](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/cc/silo/transaction.cc:557))

   したがって、例えば unsigned 比較だけでも `max_wset_.obj_ < <事前計算した epoch 境界>` により実行進捗で政策を切り替えられる。bitwise `&` も許すなら世代 bit や状態 bit の分割も可能である。草案は直接の epoch 観測を progress proxy として禁止しながら raw word を許可しており、禁止が綴りだけの恒真化になっている。([plan.md:63-70](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t1871-nonenum-axis-stage-b/plan.md:63), [plan.md:93-113](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t1871-nonenum-axis-stage-b/plan.md:93))

   stable な `thid_` そのものが TID に埋め込まれる証拠はないため「必ず特定 worker を復元できる」とまでは言えない。しかし record 世代、実行進捗、施錠位置、read-own-write 状態による偏りは具体的に構成できる。raw 二観測は撤回し、epoch/TIDを復元できない frame-owned な派生 boolean などへ B 段で再設計するか、この proxy を許すというユーザー裁定が必要である。

2. 単一 owner の証明を C 段へ送るのは遅い。

   `max_*` は public な非 atomic memberで、射影内の writer は constructor、`begin()`、`lockWriteSet()`、`validationPhase()` に存在する。worker 生成・executor 受渡し・callback 実行モデルは射影外なので並行 writer 不在を証明できない。([transaction.hh:33-58](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/cc/silo/include/transaction.hh:33), [transaction.cc:55-59](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/cc/silo/transaction.cc:55), [transaction.cc:191](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/cc/silo/transaction.cc:191), [transaction.cc:474](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/cc/silo/transaction.cc:474))

   草案自身も未証明を認めている。([plan.md:74](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t1871-nonenum-axis-stage-b/plan.md:74), [plan.md:165](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t1871-nonenum-axis-stage-b/plan.md:165), [plan.md:182](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t1871-nonenum-axis-stage-b/plan.md:182)) 証明失敗時に二観測を落とすと軸定義そのものが変わるため、これは C の実装確認ではなく B の allowlist 決定事項である。worker lifecycle を B の射影へ追加して今証明するか、現 B では禁止へ倒すべきである。呼出元を追わず性質を分類した過去型 F142 に該当する。([failures.md:F142](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/docs/failures.md:5492))

3. admission 契約が機械判定可能な形まで閉じていない。

   「unsigned の全域演算」は operator token の閉じた集合になっていない。また「`kUnset` は全 member 値について true」は型検査だけでは保証できず、任意の再帰式に対する意味検査が必要になる。([plan.md:36](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t1871-nonenum-axis-stage-b/plan.md:36), [plan.md:124-139](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t1871-nonenum-axis-stage-b/plan.md:124))

   operator の exact allowlist、literal 型、AST grammar、`kUnset` の証明方式を B で凍結する必要がある。`kUnset` は marker 外の frame で最終的に `true` へ上書きする構造にすれば、難しい意味検査を避けて機械執行できる。

4. positive control は現在の記述だと reject-all gate でも全件合格する。

   禁止 identifier、動的ゼロ除算、副作用、`kUnset=false` はいずれも一行の broken candidate として構成でき、現 `DiffQuarantine` の構造検査を通過する。例えば `result_ != nullptr`、`max_rset_.obj_ / max_wset_.obj_`、`++max_rset_.obj_`、`reason != kUnset` である。検疫は明示的に C++ 意味 admission を保証しない。([diff_quarantine.py:14-23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/orchestrator/campaign/diff_quarantine.py:14), [diff_quarantine.py:464-523](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/orchestrator/campaign/diff_quarantine.py:464))

   しかし草案は拒否される負例しか要求していない。全候補を拒否する恒偽 admission でも全 mutation-red が期待どおり赤になる。各 allowlist 観測を実際に使う非自明な正例、public materialization 経路、各負例が他層でなく対象 gate 単独で拒否されたことの subtype 照合、最後の実 build が必要である。これは F9、F19、F28、F143、F568 の再発面である。([failures.md:F9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/docs/failures.md:218), [failures.md:F19](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/docs/failures.md:357), [failures.md:F28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/docs/failures.md:838), [failures.md:F143](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/docs/failures.md:5507), [failures.md:F568](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/docs/failures.md:15977))

## should-fix

- brief の M2 は過剰一般化である。`clear()` が保証するのは論理要素数 0 であり、capacity、bucket、storage address まで情報を失うわけではない。草案側の訂正が正しい。([brief.md:67](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t1871-nonenum-axis-stage-b/inputs/brief.md:67), [plan.md:8](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t1871-nonenum-axis-stage-b/plan.md:8), [transaction.cc:38-40](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/cc/silo/transaction.cc:38))

- brief の M3 は生存 member の全数列挙に見えるが非網羅である。`gc_records_`、WAL、`quit_`、`callback_`、boolean 群などが残る。草案の訂正を最終 brief に反映すべきである。([brief.md:68](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t1871-nonenum-axis-stage-b/inputs/brief.md:68), [transaction.hh:35-62](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/cc/silo/include/transaction.hh:35))

- 「正しさを原理的に壊せない」は「serializability safety を直接変更しない」へ限定すべきである。starvation は反例になるが、system-wide livelock は射影された retry loop と scheduler だけでは未証明である。草案が fairness/liveness を characterization 不可能な死角として分離した点は正しい。([plan.md:39](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t1871-nonenum-axis-stage-b/plan.md:39), [plan.md:128-139](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t1871-nonenum-axis-stage-b/plan.md:128))

- hole 外執行は module 単体では確認した。別ファイル、marker 外削除・挿入、frame 変更を拒否する。だが複数行・任意 C++ 意味は許し、`head_text` 無しの縮退 mode もある。実 caller が trusted `git diff` と HEAD bytes を渡して `validate()` を必ず消費する配線は射影外で、end-to-end の「機械執行」は未確認である。([diff_quarantine.py:285-309](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/orchestrator/campaign/diff_quarantine.py:285), [diff_quarantine.py:420-540](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/orchestrator/campaign/diff_quarantine.py:420)) 説明が実装・配線より強くなる F564 型を避けるため、保証を module-level と end-to-end に分けるべきである。([failures.md:F564](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/docs/failures.md:15910))

- 旧 5-bit 部分空間から拡張空間への生存一般化は、旧候補が admission で受理され、materialized bytes と動作意味が保存されることを正例で確認した後に限定すべきである。単なる集合表記だけでは F19 型の実体化差を排除できない。([brief.md:42-44](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t1871-nonenum-axis-stage-b/inputs/brief.md:42), [plan.md:169-174](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t1871-nonenum-axis-stage-b/plan.md:169))

## nit

- 静的 reject を「positive control」とだけ呼ぶと正例受理との区別が曖昧になる。「admission negative controls」と「nontrivial acceptance controls」を分けるとよい。([plan.md:124-139](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t1871-nonenum-axis-stage-b/plan.md:124))

## refuted (草案・brief の主張のうち、根拠を確認して支持したもの)

- 両 `max_* .obj_` の直接読取が不定値または非活性 union member 読取になる、という懸念は反証した。通常構築後は `begin()` 未通過でも定義済みである。

- `max_wset_` は成功済み write 要素まで、`max_rset_` は検証通過済み read 要素までしか反映せず、失敗要素自身は反映前という草案の説明を確認した。([transaction.cc:155-192](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/cc/silo/transaction.cc:155), [transaction.cc:449-475](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/cc/silo/transaction.cc:449))

- `DiffQuarantine` は marker 外を行単位で拒否するが、意味 admission や単一代入性を保証しない、という草案の内訳は正しい。

- `transaction.cc` は source identity 対象と file allowlist に含まれ、preprocess digest と TRACE diff-of-diffs の対象になる。これは marker 境界執行とは別の保証である。([source_digest.py:81-96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/orchestrator/campaign/source_digest.py:81), [source_digest.py:2051-2086](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/orchestrator/campaign/source_digest.py:2051), [source_digest.py:2195-2250](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/orchestrator/campaign/source_digest.py:2195))

- 型付き pre-build admission は仮想リスク向けの過剰防壁ではない。現在の structural quarantine が実際に任意 C++ 意味を通すため、契約拡張と同時に必要となる一次防壁である。B 段では仕様だけを凍結し、実装を C 段へ送ること自体は scope 違反ではない。([axis-onboarding.md:323-334](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t1871-nonenum-axis-stage-b/inputs/axis-onboarding.md:323))

## verdict

reject

## 総括

直接の `.obj_` 読取は定義済みで、abort 後の gate が serializability を直接壊す反例も得られなかった。問題はそれより上流にある。raw `obj_` は、草案が禁止した epoch・進捗・transaction 状態の proxy を丸ごと露出し、単一 owner も B 段で未証明である。さらに admission の exact 契約と非恒真な positive control が未完成である。

従って現在の「raw `max_rset_.obj_` と raw `max_wset_.obj_` の二観測だけを採用」という中核結論は凍結できない。B 段へ戻し、proxy を復元できない派生観測への再設計、worker lifecycle の証明、admission の exact grammar と正負両 control を揃えてから再レビューすべきである。