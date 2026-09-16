## 正例が偽陽性になりうる道

- **主張:** 正例単独では campaign の誤配線を検出できない。ただし、別の配線テストが補完しており、今回の差分全体が恒真という指摘は成立しない。
- **根拠 (file:line):** `orchestrator/tests/test_s8b_floor_campaign.py:3938–3958` は生成器から gate を直接呼び、変更した binding／`floor_prepare` を通らない。したがって搬送を削除しても、この6ケースは変化しない。一方、同ファイル `:3834–3836` と `:3649–3653` が格納値と全 cell への搬送を検査する。
- **成果物影響:** 実 compiler テストの緑だけを根拠に配線完了とはいえない。配線テストとの組合せが必要。
- **重大度:** 情報。正例自体の欠陥とは判定しない。
- **是正案:** 正例は「指定した include path で supply arm が成立する証拠」として扱う。

`requested-default-preprocess-different` は config.h 供給専用の reason code ではない。`orchestrator/campaign/condition_meaning_gate.py:2612–2660` で compiler・argv・依存集合の整合とプリプロセス結果の差を確認した結果である。この fixture では実際の `#include` と sentinel 検査（テスト `:3922–3923`）が供給との関連を作っている。

## 負例が恒真・別理由になりうる道

- **主張:** **欠落原因を特定する assertion は弱い。** `config.h` の欠落と、存在する別の config.h による失敗を区別していない。
- **根拠 (file:line):** テスト `:3968–3971` は `preprocess-failed` と `"config.h"` の部分一致だけを見る。自身が挿入する `#error wrong config.h`（`:3923`）もこの条件を満たす。gate の同 reason は非ゼロ終了だけでなく、成功時の stderr にも使われる（`condition_meaning_gate.py:1610–1621`）。
- **成果物影響:** 負例が緑でも「config.h 不在だけが原因」という完了証拠にはならない。今回の実走で別原因だったと断定するものではない。
- **重大度:** 中。単一理由性を完了条件とするなら、その証明について要修正。
- **是正案:** compiler の欠落診断を確認し、同じ負例の探索先へ正しい config.h だけを置くと green へ戻る対照を加える。特に `empty` では同じ configure 引数を維持できる。

- **主張:** base/source 分離はこの fixture では有効。ただし fallback は実 FetchContent の再現ではなく、include path 選択の模型である。
- **根拠 (file:line):** テスト `:3908–3937` は別ディレクトリを作り、fallback 先に config.h がないことを確認する。実 CCBench は `FetchContent_Populate` 後の `masstree_SOURCE_DIR` を使う（`external/ccbench/cmake/ThirdParty.cmake:42–58,85`）。fixture は Populate を実行しない。
- **成果物影響:** 実機で SOURCE_DIR を省略した場合の取得処理・configure 成否までは代表しない。一方、裁定Cの最小 project による include 供給対照としては妥当。
- **重大度:** 情報。
- **是正案:** 実機の省略時挙動を検証したとは記録しない。

CMake 変数未定義・target 不在による configure 失敗は `configure-failed` になる（`condition_meaning_gate.py:1713–1715`）。したがって、それらが現在の負例 assertion を満たすという指摘は成立しない。

## 配線 pin test が恒真かどうか

- **主張:** 三者一致だけなら共通生成処理の誤りを見逃すが、テスト全体は恒真ではない。
- **根拠 (file:line):** テスト `:3829–3836` は生成器とは別に名前と期待 path の辞書を構成する。`:3889–3892` で三者一致・本数・重複・名前集合を検査する。共有部分は `p3_s4_loop.py:353–367` の正規化と token 生成である。
- **成果物影響:** SOURCE_DIR 入替え、搬送 field の空 tuple 化、余分な token などは静的には検出可能。
- **重大度:** 問題なし。ただし実 build の証拠ではない。
- **是正案:** 不要。射程を argv 配線に限定する。

`buildcache._run` の stub（テスト `:3743–3747`）により、CMake が引数を受理すること、依存取得、masstree build、config.h／archive の生成は検証されない。検証・materialize も stub（`:3789–3802`）なので、生成物の真正性もこのテストの射程外である。また `campaign_argv` は `_v2_commands` の直接呼出しであり、campaign が実際にその build を起動した証拠ではない。

## 既存 fixture へ既定値を足したことによる検出力の低下

- **主張:** 個々の fixture は引数欠落を許すが、従来の検出力が低下したとはいえない。
- **根拠 (file:line):** 例としてテスト `:2928–2931` の既定値は搬送欠落を拒否しない。しかし変更前の fixture はこの引数自体を要求していなかった。新しい搬送検査 `:3574,3649–3653` は、非空の期待 tuple と比較する。
- **成果物影響:** 他の既存テストが緑のままでも、搬送削除・空 tuple 化・sort 限定化は専用テストで検出できる構造。
- **重大度:** 問題なし。
- **是正案:** 全 fixture を必須引数に変更する必要はない。

## 揮発 payload と期待値の固定

- **主張:** 証明するのは二つの path／コメント内容でも同じ判定になることまで。
- **根拠 (file:line):** テスト `:3896,3908–3917` はディレクトリ名と config.h のコメントを変更する。`:3961–3966` は固定 digest を期待せず、各実行内の差と動的な owner path を確認する。
- **成果物影響:** 絶対 path・時刻・PID の期待値への焼込みはない。ただし二実行間の digest 不変性や、時刻・PID への耐性は証明していない。
- **重大度:** 情報。
- **是正案:** 「揮発情報全般に対する不変性」の証拠へ拡大解釈しない。

## 裁定違反の有無

- **主張:** 対象 commit に実装上の裁定違反は見つからない。
- **根拠 (file:line):** `s8b_floor_campaign.py:3475–3486` は既存生成器を再利用し、`:4343–4367` は全 cell の prepare に搬送する。`:2150–2194` の receipt/private 出力に新 field はない。`:4270–4271` の prebuild 条件、`:4446–4485` の sort 限定 build 注入は維持されている。commit の変更対象は指定の2ファイルだけ。
- **成果物影響:** 非 sort 単独 prebuild、新しい build 起動点、shell／登録簿の変更はない。gate の判定規則・reason code も変更されていない。
- **重大度:** 問題なし。
- **是正案:** 「受理集合不変」は、依存欠落解消による red→green まで否定する表現として使わない。

## 総括

**実装配線の不具合・裁定違反は確認できない。修正対象は、負例が「config.h 欠落」を特定できない assertion の弱さ。**

事前登録 M1〜M4 は、配線テストの期待値から静的には検出可能と判断する。ただし変異実行による KILLED は未確認。pytest・compiler は実行しておらず、親の「8 passed / 0 skipped」を独立に再検証したものではない。