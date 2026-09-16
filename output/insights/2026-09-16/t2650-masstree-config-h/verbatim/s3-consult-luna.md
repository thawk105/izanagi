## config.h が書かれる dir と gate へ渡す dir の一致 (行番号)

以下、`campaign/` は `orchestrator/campaign/`、`tests/` は `orchestrator/tests/` を指す。判定は静的検査による。

- **主張:** plan の配線先は生成先と一致する。`config.h` 欠落の修正として成立する。
  **根拠:** [ThirdParty.cmake:58](external/ccbench/cmake/ThirdParty.cmake:58) は `${masstree_SOURCE_DIR}/config.h` を OUTPUT とし、同 69–74 行はその source dir 内で bootstrap／configure／make を実行する。同 85 行が同じ dir を include path にする。`campaign/buildcache.py:2056–2072,2090–2096` は明示 source dir を configure に渡し、`masstree_build` を完了させる。床値の source は `campaign/s8b_floor_campaign.py:2630–2632,3421–3426` により `<effective_base>/masstree-src`。plan.md:49–54 はその **同じ `prepare_kwargs["masstree_source_dir"]`** を gate 用生成器へ渡す。
  **成果物影響:** gate が参照するのは prebuild 済み `masstree-src/config.h`。`izanagi-masstree-prebuild/config.h` や oracle 用コピーへの誤配線ではない。
  **重大度:** 阻害所見なし。ただし実前処理成功は未実証。

通常の job では、具体的な生成先は **`/scr/${PBS_JOBID//:/_}/izanagi-floor-fetchcontent/masstree-src/config.h`**。根拠は `floor_campaign.sh:269`、`s8b_floor_campaign.py:197,3173–3201`。

## prebuild と gate の順序保証、飛ばせる経路の有無

- **主張:** production かつ `sort_best` を含む campaign では、prebuild 成功前に cell の gate へ進む経路はない。
  **根拠:** `s8b_floor_campaign.py:4215,4259–4260` が条件、4290–4296 行が prebuild、4328 行が cell ループ、4359–4362 行が preparation。prebuild の例外は 3427–3454 行で送出され、4318–4326 行でも送出される。握り潰してループへ続行しない。
  **成果物影響:** backoff cell が先頭でも、共有 prebuild は完了済みになる。
  **重大度:** 阻害所見なし。

- **主張:** resume は「prebuild を飛ばして同じ preparation ループに入る」抜け道ではない。
  **根拠:** `s8b_floor_campaign.py:7725` の L 状態 resume は `build_cells` を呼び、4713 行から同じ実装へ入る。7766–7786 行の manifest 保有経路は既存 binary を読み検証し、preparation 自体を行わない。非 sort 単独／注入 `prepare_fn` は 4259 行の条件から外れる。
  **成果物影響:** resume に由来する今回の順序欠陥はない。非 sort 単独の未修復は後述。
  **重大度:** 阻害所見なし。

## pristine 検査との衝突

- **主張:** prebuild 後にも同検査関数へ入る経路はあるが、生成物を拒否する設定ではない。
  **根拠:** `s8b_floor_campaign.py:3396` の初回検査は既定 `tracked_only=False`（2568 行）。一方、2943–2947 行からの再検査は 3715–3718 行で **`tracked_only=True`** を渡す。2742–2746 行では、この場合 `--untracked-files=no` となり、`--ignored=matching` も付けない。
  **成果物影響:** `config.h`、`.o`、archive の生成だけで postflight が赤になるという懸念は反証できる。今回の配線は検査回数・設定を変えない。
  **重大度:** 阻害所見なし。

- **主張:** 使用済み base を新しい preparation の入力として再利用すれば、初回 pristine 検査に落ち得る。ただし既存の制約である。
  **根拠:** 同 3396 行は毎回 full pristine 検査を行う。通常 staging は 3220–3225 行で既存 destination を拒否する。
  **成果物影響:** 生死確認で既存生成物を持つ base をそのまま `_prepare_floor_oracle_dependency` に再投入する手順は不適切。fresh な staged source が必要。
  **重大度:** 注意。今回の must-fix ではない。

## 他 consumer への波及

- **主張:** plan の変更範囲なら、他の `prepare_cell` consumer の引数・動作は変わらない。
  **根拠:** 追加先は床値ローカル closure（`s8b_floor_campaign.py:4344–4356`）。共通受け口は既存の `s1_direct_comparison.py:836,966–971`。`s8b_materialization.py:128–136` は渡された `prepare_fn` を呼ぶだけ。`s8b_oracle_driver.py:1440–1441,1669–1673` は独自の prepare 経路、`s8b_oracle_n_pilot.py:926–945,961–967` は独自 closure で、いずれも今回の床値 closure を使わない。
  **成果物影響:** oracle driver／pilot の未供給問題を修復する変更ではないが、新たな引数注入も起きない。
  **重大度:** 阻害所見なし。

## 先例との差と、binding が無い経路の扱い

- **主張:** 床値にも、receipt 分岐に相当する「binding がある場合だけ」という分岐はある。生成器を無条件に呼ぶ案ではない。
  **根拠:** `p3_s4_loop.py:1914–1925` は receipt の有無で分岐。床値は `s8b_floor_campaign.py:4332` が分岐し、plan.md:47 は prebuild 成功後に生成する。生成器自身は `p3_s4_loop.py:369–374` で token 数を要求するため、空入力で呼べば失敗する。
  **成果物影響:** plan の位置関係を維持すれば、binding なしで生成器が例外を出す回帰はない。
  **重大度:** 阻害所見なし。

- **主張:** 非 sort 単独 campaign は、同じ欠落を残す。「従来どおり空」は成功の保証ではない。
  **根拠:** `s8b_floor_campaign.py:4259–4260` により prebuild も binding もなく、4331–4332 行から既存 prepare を使う。`s1_direct_comparison.py:836` の既定値は空。fresh な FetchContent source では `ThirdParty.cmake:66–78` の生成処理を configure だけでは実行しない。
  **成果物影響:** 該当 owner TU が masstree を含む非 sort 単独実行は、依存取得に成功しても同じ `config.h` 欠落を起こし得る。修復範囲は「sort を含む official campaign」と明記すべき。
  **重大度:** 中、既存欠陥の残存。brief.md:25–27 の既存 prebuild 搬送という scope では修復対象外。prebuild 新設を本 wave に追加する必要はない。

## 実機前提との噛み合わせと、安い生死確認の形

- **主張:** job の前段と plan は噛み合う。prefix token がなくても、既存の環境供給がある。
  **根拠:** `floor_campaign.sh:1033–1068,1103–1139` は gflags／glog を `$TMPDIR` に build・install し、1148 行で `CMAKE_PREFIX_PATH` を export。1199 行で診断 staging を指定する。依存 source の実際の複製は Python 側 `s8b_floor_campaign.py:3158–3165,3173–3201`。gate の `condition_meaning_gate.py:1581–1596` は環境を置き換えず subprocess を起動する。
  **成果物影響:** 現行床値では offline token **4 本**が正しい。shell 編集や明示 prefix 新設は不要。
  **重大度:** 阻害所見なし。

- **主張:** 「CCBench 全体の configure に gflags/glog が必要」は正しいが、「実 CMake の生死確認には必ずその build が必要」は過大な主張。
  **根拠:** `external/ccbench/CMakeLists.txt:33–34` は両者を REQUIRED とする。しかし既存 `tests/test_condition_meaning_gate.py:505–518` は小さい fixture で実 CMake・実 compiler を使う。`tests/condition_gate_test_support.py:128–150` にも実 compiler fixture の道具がある。なお、REQUIRED 宣言だけでは login node 上のインストール不存在までは証明できない。
  **成果物影響:** [T-548] の shell を編集せずに、新配線の生死確認を追加できる。
  **重大度:** 中、検証計画の修正が必要。

具体的には、親で既存の実 compiler fixture を使い、owner TU に `#include <config.h>`、include path に渡された masstree source dir を使わせる。正しい引数で supply が成功し、SOURCE_DIR を除去・未生成 directory に変更すると `preprocess-failed` になる対照を取る。実行は既存 `tools/run_tests.py` を通す。これは新しい実行機構を必要としない。

さらに実生成先を動的に確認するなら、小さい CMake project から現行 `ThirdParty.cmake` を include し、fresh な３依存 source を指定して既存 `masstree_build` target を実行できる。CCBench 上位の gflags/glog 探索を必要としない。ただし、これらは **official owner TU／cell build 全体の成功とは別の証拠**である。

## 親 brief の (P1-a)〜(P1-d) の判定

- **P1-a — real。ただし「5 定義固定」は refuted。**
  **主張:** 既存生成器の再利用は妥当。
  **根拠:** `p3_s4_loop.py:346–376` は prefix 有無を扱う。床値の `s8b_floor_campaign.py:3414–3425` は prefix を渡さず、`buildcache.py:2034` の既定値は空。
  **成果物影響:** plan の４本 assertion が正しい。５本必須にすると正しい床値配線を拒否する。
  **重大度:** 低。plan では訂正済み。

- **P1-b — real、cell build identity を変えないという射程で支持。**
  **主張:** gate への供給と非 sort build への base 注入は区別できる。
  **根拠:** `docs/decisions.md:17630–17634,17657–17658` は非 sort の cache identity／binary 変更を問題にする。plan は `s8b_floor_campaign.py:4434–4473` の sort 限定 build 分岐を維持する。
  **成果物影響:** 非 sort の gate は改善するが、cell build の依存引数は追加されない。
  **重大度:** 阻害所見なし。

- **P1-c — real、提案された２ファイル差分について。**
  **主張:** 凍結 bytes の変更も argv 構造検査の破壊も必要ない。
  **根拠:** `tests/test_frozen_artifacts.py:41` 以降の manifest、`condition_meaning_gate.py:3550–3559,3718–3726`。plan.md:44 は搬送フィールドを永続 receipt に追加しない。
  **成果物影響:** 新規 gate 証跡の argv は変わるが、既存凍結 artifact を書き換える必要はない。
  **重大度:** 阻害所見なし。

- **P1-d — refuted。**
  **主張:** 既存実測の継承だけでは修正後の生死確認にならない。
  **根拠:** brief.md:3–6 の既存実測は失敗例。plan.md:78–81 は prebuild 実行を stub 化し、gate の最初の configure 呼び出しで例外停止する。したがって config.h の実生成も compiler による読込みも観測しない。
  **成果物影響:** 提案テストが全部通っても、brief の完了条件「supply が失敗せず cell build 段を越える」を満たしたとは報告できない。
  **重大度:** 高、**完了判定の must-fix**。親の検証計画に上記の実前処理対照を含めること。official cell build 通過を完了条件に残すなら、その実測も必要であり、未実施なら完了未確認と明記する。

## 総括

**配線案は静的には成立する。変更すべき中心は実装方針ではなく P1-d の検証・完了判定である。**

生成先の不一致、prebuild 順序の逆転、生成物による pristine 再検査失敗、他 consumer への引数波及は確認できなかった。非 sort 単独経路の欠落は残るが、本 wave の既存 prebuild 搬送という範囲外。

実装・書込み・commit・push・テスト実行は行っていない。実 CMake／実前処理成功も未確認。