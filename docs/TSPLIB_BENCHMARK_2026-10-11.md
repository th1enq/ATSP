# Kết quả chạy trên TSPLIB — 2026-10-11

## Phạm vi

Chạy nguyên pipeline hiện có: **ngưỡng Held–Karp → bộ dựng cây có chứng nhận → AKS → tour**. Không sửa bộ dựng cây hoặc AKS, không chạy thêm dữ liệu tổng hợp. Mã nguồn bộ dựng cây được ghi SHA256 và giữ nguyên trong suốt lượt chạy. Phần bổ sung là bộ đọc ma trận, adapter LP và phần đo chi phí gốc.

Đầu vào gồm **10 bộ trong [danh mục ATSP chính thức của TSPLIB](https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/atsp/atspindex.html)**, từ 17 đến 56 đỉnh. Do môi trường không tải trực tiếp được archive gzip, dùng dữ liệu văn bản từ bản sao TSPLib.Net qua công cụ web; không khẳng định đã so sánh từng byte với archive Heidelberg. URL thực tế, quy tắc chuẩn hóa khoảng trắng và SHA256 nằm trong [manifest](../instances/tsplib/manifest.json). Đây là một phần của danh mục 19 bộ.

Giữ nguyên mọi chi phí ngoài đường chéo. Không lấy metric closure. **Bottleneck là cạnh có chi phí gốc lớn nhất trong tour, kể cả cạnh đóng chu trình.** Không dùng điểm tối ưu tổng độ dài của ATSP làm chuẩn bottleneck.

Giá trị tối ưu đối chiếu lấy từ Bảng 5 của LaRusic & Punnen, [The asymmetric bottleneck traveling salesman problem: Algorithms, complexity and empirical analysis](https://cedric.cnam.fr/~bentzc/INITREC/Files/CB1.pdf), Computers & Operations Research 43 (2014), 20–35.

## Kết quả

Giới hạn **180 giây cho toàn bộ pipeline mỗi bộ**, bao gồm LP và dựng cây. Thời gian dưới đây là thời gian thực trôi qua, không chỉ thời gian AKS. Timeout ghi nhận lúc đang ở bước dựng cây; không có tour được công bố cho những ca này.

| Bộ | n | Metric | HK / tối ưu công bố | Mẫu số HK | Bottleneck tour | Tour / tối ưu | Vòng sparsification | Thời gian (s) |
|---|---:|:---:|---:|---:|---:|---:|---:|---:|
| br17 | 17 | Không | 8 / 8 | 2 | 8 | 1.0000 | 0 | 0.63 |
| ftv33 | 34 | Có | 113 / 113 | 1 | 113 | 1.0000 | 0 | 5.37 |
| ftv35 | 36 | Có | 113 / 113 | 6 | Timeout | — | — | 180.01 |
| ftv38 | 39 | Có | 113 / 113 | 2 | 143 | 1.2655 | 0 | 28.25 |
| p43 | 43 | Không | 5008 / 5008 | 1 | 5008 | 1.0000 | 0 | 8.60 |
| ftv44 | 45 | Có | 113 / 113 | 1080 | Timeout | — | — | 180.01 |
| ftv47 | 48 | Có | 104 / 104 | 144 | Timeout | — | — | 180.02 |
| ry48p | 48 | Không | 577 / 577 | 40 | Timeout | — | — | 180.01 |
| ft53 | 53 | Có | 977 / 977 | 137 | Timeout | — | — | 180.03 |
| ftv55 | 56 | Có | 64 / 64 | 4 | 220 | 3.4375 | 1 | 146.58 |

**5/10 bộ trả được tour; 5/10 timeout.** Trong 5 tour hoàn thành, 3 tour đạt tối ưu (`br17`, `ftv33`, `p43`); `ftv38` cao hơn tối ưu 26,55%; `ftv55` cao hơn tối ưu 243,75% (tỉ số 3,4375). Không tính các timeout như tour tối ưu hoặc tour có chi phí bằng 0.

Có 7 bộ thỏa bất đẳng thức tam giác. `br17`, `p43`, `ry48p` lần lượt có 488, 6738, 1540 bộ ba vi phạm; chúng nằm ngoài giả thiết metric của bảo đảm xấp xỉ. Trong 7 bộ metric, 3 bộ trả được tour và 4 bộ timeout.

## Bước nào thực sự chạy được?

- **Held–Karp:** cả 10 bộ có nghiệm hữu tỉ được kiểm tra đẳng thức bậc và mọi ràng buộc subtour bằng min-cut nguyên. Ngưỡng thấp hơn liền trước có chứng nhận Farkas hữu tỉ về tính bất khả thi. Ngưỡng HK bằng tối ưu bottleneck công bố trên cả 10 bộ; đây là quan sát trên tập dữ liệu này.
- **Dựng cây:** bốn ca `br17`, `ftv33`, `ftv38`, `p43` có mẫu số 1 hoặc 2 và dừng tại ngưỡng packing hiện có, nên không chạy vòng sparsification. Trong đó `ftv33` và `p43` đã có nghiệm HK nguyên là chu trình Hamilton. Các ca này không đo được hiệu quả của bộ signing/frame.
- **Sparsification thật trên benchmark:** `ftv55` có mẫu số 4; hoàn thành một vòng `r=4 → 1`, giữ 110 trong 224 bản sao cạnh, chọn cây 55 cạnh và chuyển sang AKS. Dựng cây mất 133,06 giây; kiểm chứng/chạy AKS mất 4,12 giây; toàn pipeline mất 146,58 giây. Tour đạt bottleneck 220 so với tối ưu 64.
- **Nghẽn thời gian:** `ftv35`, `ftv44`, `ftv47`, `ry48p`, `ft53` timeout ở dựng cây với mẫu số HK lần lượt 6, 1080, 144, 40, 137. Chưa thể kết luận chúng không giải được với thời gian dài hơn. Số đỉnh không phải yếu tố duy nhất quyết định độ khó của bản cài đặt hiện tại.

Bộ dựng cây đang chạy là `checked_laplacian_sparsification` với các giới hạn hiện có, không phải toàn bộ phép continuation tổng quát của Result 174. Cận beta dùng bởi AKS là cận hỗ trợ `min(D,(n−1)/2)` hiện có; không tính thinness tối ưu bằng vét cạn. Kết quả này chưa chứng minh một bảo đảm xấp xỉ hằng số độc lập với đầu vào của bản cài đặt.

## Không dùng thuật toán trâu

Adapter dùng SciPy 1.16.1 / HiGHS dual simplex cho hệ đẳng thức bậc và các cut được bổ sung bằng separation. Sau mỗi nghiệm LP, chuyển sang số hữu tỉ và dùng min-cut nguyên để chấp nhận hoặc bổ sung ràng buộc. Ngưỡng không khả thi được kiểm tra bằng chứng nhận Farkas chính xác. Không gọi `held_karp_feasible_allcuts`, không liệt kê tập con, không duyệt cây khung, không chạy Hamiltonian DP hay solver tối ưu tour.

C++ nhận cây của bộ dựng hiện có qua `round-supported-tree`. Trường `metric_bottleneck` trong stdout C++ là số bước trên đồ thị hỗ trợ HK, **không phải chi phí TSPLIB**. Bảng kết quả dùng `bottleneck` tính lại trực tiếp từ ma trận gốc.

## Tái chạy và kiểm tra

Đầu vào: [instances/tsplib](../instances/tsplib/README.md). Dữ liệu kết quả: [summary.csv](../results/tsplib/summary.csv), mỗi bộ có JSON, đầu vào HK và chứng nhận cây nếu hoàn thành. Phiên bản, môi trường và hash trong [environment.json](../results/tsplib/environment.json).

```bash
python3 -m pip install -r benchmarks/requirements-tsplib.txt
g++ -std=c++20 -O2 -Wall -Wextra -Wpedantic -Iinclude src/main.cpp -o /tmp/kltn-batsp
python3 benchmarks/bench_tsplib.py --batsp /tmp/kltn-batsp --timeout 180
```

Trong workspace NixOS hiện tại đã có wheel cache:

```bash
bash benchmarks/run_tsplib_cached.sh --batsp /tmp/kltn-batsp --timeout 180
```

Kiểm tra kết quả đã lưu bằng Python chuẩn, không giải lại LP:

```bash
python3 benchmarks/bench_tsplib.py --verify-results
python3 scripts/experimental_tree.py --verify results/tsplib/ftv55.tree.json
```

Đã kiểm tra độc lập chi phí của cả 5 tour và chứng nhận ngưỡng HK của cả 10 bộ. Năm kiểm tra adapter đã qua: kích thước/hash dữ liệu, phân biệt metric, tính đúng cạnh đóng tour, từ chối ma trận thiếu dữ liệu, và loại cycle cover rời nhau bằng cut/Farkas.

**Kết luận:** pipeline hiện tại đã có kết quả trên benchmark thực, gồm một vòng sparsification được chứng nhận ở 56 đỉnh. Chất lượng tour và thời gian dựng cây còn hạn chế rõ rệt: tỉ số quan sát cao nhất 3,4375 trên các ca hoàn thành, và một nửa tập dữ liệu vượt giới hạn thời gian.
