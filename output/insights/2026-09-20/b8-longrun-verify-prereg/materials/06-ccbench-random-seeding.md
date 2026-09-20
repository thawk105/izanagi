# CCBench (現行 pin、submodule の作業木) の乱数シードに関わる source の逐語射影

## external/ccbench/include/random.hh — class Xoroshiro128Plus の冒頭 (init と splitMix64)

```cpp
class Xoroshiro128Plus {
public:
  Xoroshiro128Plus() { init(); }

  uint64_t s[2];

  inline void init() {
    std::random_device rnd;
    s[0] = rnd();
    s[1] = splitMix64(s[0]);
  }

  uint64_t splitMix64(uint64_t seed) {
    uint64_t z = (seed += 0x9e3779b97f4a7c15);
    z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9;
    z = (z ^ (z >> 27)) * 0x94d049bb133111eb;
    return z ^ (z >> 31);
  }

```

## external/ccbench/include/ycsb.hh — ycsb の gflags 定義 (seed の flag は無い)

```cpp
DEFINE_bool(ycsb_rmw, false,
            "True means read modify write, false means blind write.");
DEFINE_uint64(ycsb_max_ope, 10,
              "Total number of operations per single transaction.");
DEFINE_uint64(ycsb_rratio, 50, "read ratio of single transaction.");
DEFINE_uint64(ycsb_tuple_num, 1000000, "Total number of records.");
DEFINE_double(ycsb_zipf_skew, 0, "zipf skew. 0 ~ 0.999...");
```

## external/ccbench/include/ycsb.hh — class YcsbWorkload の冒頭 (constructor で rnd_.init())

```cpp
class YcsbWorkload {
public:
  Xoroshiro128Plus rnd_;
  FastZipf zipf_;

  YcsbWorkload() {
    rnd_.init();
    FastZipf zipf(&rnd_, FLAGS_ycsb_zipf_skew, FLAGS_ycsb_tuple_num);
    zipf_ = zipf;
  }

```

## external/ccbench/common/runner.hh — worker_body (worker thread ごとに Workload を構築)

```cpp
template <typename Tx, typename TransactionStatus, typename Workload,
          typename MakeTx, typename WorkerInit, typename WorkerAfterStart>
requires TxExecutorLike<Tx>
void worker_body(std::size_t thid, char& ready, const bool& start,
                 const bool& quit, const MakeTx& make_tx,
                 const WorkerInit& worker_init,
                 const WorkerAfterStart& worker_after_start) {
  // `Backoff` on the worker's stack so its lifetime covers `trans`.
  // Constructed even for protocols that don't use it (silo etc.) - the
  // ctor is one integer multiply, not worth a template branch.
  Backoff backoff(FLAGS_clocks_per_us);
  // C++17 guaranteed copy elision: `make_tx(thid, quit, backoff)`
  // returns a prvalue and is constructed directly into `trans`, so
  // `Tx` does not need to be move-constructible.
  Tx trans = make_tx(thid, quit, backoff);
  Workload workload;
  if constexpr (HasPrepare<Workload, Tx>) { workload.prepare(trans, nullptr); }

  worker_init(trans, thid);

  storeRelease(ready, static_cast<char>(1));
  while (!loadAcquire(start)) _mm_pause();
  worker_after_start(trans, thid);
  while (!loadAcquire(quit)) {
    workload.template run<Tx, TransactionStatus>(trans);
  }
}

```
