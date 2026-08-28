# T-2000 legacy build probe 結果

- authority: none
- default_effect: no-state-change
- 対象commit: `de8be5cce11c9d5bed689fc1bf417ba872c08501`
- 裁定: **indeterminate**

## 結論

production build経路、admission、site、trace gateを変更せず、Pegasus計算ノードでT-2000専用probeを実行した。最終request `956856.nqsv` はchild rc=0だが、production admission preconditionが不成立で、3 armはすべて `not-run`、completion=`incomplete-precondition`、classification=`indeterminate` である。

したがって、本waveはlegacyからbuild_v2への移行候補、現状維持候補のどちらも支持しない。proxy依存、non-file Git transport不要性、arbitrary network不在、性能優劣、正式性能値の主張はしない。規律2とproduction admissionを緩めない。

## create-only artifact

- 最終raw: `raw/1a985aa14fac4e2332b35d544e6bcd849a449845b18f60479adbc6eabd00928e-56e2a38d3d211fd1a20d9ecb0b1d0d1452e5d5c88e6eb574b52c6d6d97d6ccd4.json`
- 最終digest: `digest/1a985aa14fac4e2332b35d544e6bcd849a449845b18f60479adbc6eabd00928e-56e2a38d3d211fd1a20d9ecb0b1d0d1452e5d5c88e6eb574b52c6d6d97d6ccd4.json`
- 最終raw SHA-256: `89d4b0f06fede1e3b98fb4e2daeca912c7d9b78a82c592c23bbc11583e7b32c3`
- 先行precondition raw/digestは `7125ec...-92ed08....json` として追記で保持した。

両raw/digestはendpoint、URL、proxy実値、stdout/stderr、例外本文、traceback、完全argvを保存せず、hashと固定enumだけを持つ。

## 実行履歴

- `956619.nqsv`: compute childへ到達したが、runnerのabsolute selector表現をexact-node gateが拒否。arm開始0、artifact無し。
- `956795.nqsv`: node gate修正後。tests dispatcherがambient TMPDIRを供給しないためcompute preconditionで停止。arm開始0、安全なraw/digest発行。
- `956856.nqsv`: runbookの `/scr/$PBS_JOBID` をjob-localに確立した後の最終real投入。production admission preconditionで停止。arm開始0、安全なraw/digest発行。以後の追加real投入は行わない。

## 限界と次の条件

3 armの取得経路・成否・wallは得られていない。次に進めるには、別waveでproduction admission不成立のexact原因を入力・source・contextの実体で確定する。admission/site/trace/correctness gateの緩和、production module変更、汎用probe API化はその解消手段にしない。
