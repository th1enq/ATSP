# Kiểm chứng thực nghiệm phần tiền xử lý chính xác

**Cập nhật 2026-10-11:** báo cáo dưới đây ghi phạm vi tiền xử lý tại ngày
2026-10-08. Các thành phần khung, ký dấu và nhiều vòng làm thưa đã được nối
thành pipeline thực nghiệm với AKS trong `EXPERIMENTAL_PIPELINE_2026-10-11.md`.
Pipeline có chứng chỉ kiểm tra được trên mẫu nhỏ; bảo đảm hằng số phổ quát
và kiểm toán đầy đủ bổ đề nguồn vẫn chưa hoàn thành.

**Ngày:** 2026-10-08. **Phạm vi:** kiểm tra nghiệm Held–Karp hữu tỉ và nén bội số cạnh theo Mục 6 của [bản thảo thuật toán strong thin tree](https://github.com/openai/math/blob/main/preprints/A-polynomial-time-construction-of-strong-thin-trees-September-23-2026/paper.pdf). Đây là một phần của chương phương pháp và thực nghiệm cho khóa luận; chưa phải kết quả triển khai toàn bộ thuật toán xây cây.

## Phương pháp và bất biến

Đầu vào HK gồm các tử số nguyên không âm `q_uv` và mẫu số chung `D>0`. Chương trình kiểm tra `sum_v q_uv = sum_u q_uv = D` ở từng đỉnh. Đối với mọi lát cắt có hướng, nó tính giá trị nhỏ nhất bằng `2(n-1)` bài toán max-flow nguyên: chọn đỉnh gốc `0`, xét cả `0→v` và `v→0`. Mọi lát cắt không tầm thường được bao phủ bởi một trong hai chiều này. Chấp nhận khi min-cut ít nhất `D`.

Đặt `c_uv=q_uv+q_vu`, `k=2D`. Tính `c'_uv=min(c_uv,k)` và `a_uv=floor(2n²c'_uv/k)` hoàn toàn bằng số nguyên, không tạo `c_uv` bản sao. Với đầu vào đa đồ thị tổng quát `n,k,{c_uv}`, chương trình kiểm tra min-cut vô hướng ban đầu ít nhất `k` trước khi nén. Nó tính lại min-cut của đồ thị nén; đồng thời kiểm tra `sum a_uv<n⁴` và bất đẳng thức theo từng cặp `k a_uv≤2n²c_uv`. Cặp có `a_uv=0` vẫn hiện trong chứng chỉ.

Lập luận cho cận dưới: cắt `c'` có tải ít nhất `k`, vì nếu một cặp bị chặn thì riêng cặp đó đã đóng góp `k`; nếu không, tải cắt không đổi. Mỗi cặp qua cắt mất dưới một đơn vị khi lấy sàn, có tối đa `n²/4` cặp. Do đó `a(δS)>2n²-n²/4≥n²`. Cận trên suy ra trực tiếp từ phép lấy sàn. Việc kiểm tra lại min-cut trong chương trình là kiểm tra thực thi, không thay thế lập luận này.

## Ca kiểm tra

- Witness 6 đỉnh: min-cut HK bằng `2`, `k=4`, đồ thị nén có `216` bản sao và min-cut `72` so với cận yêu cầu `36`; mọi cắt được đối chiếu trực tiếp.
- Nhân tử và mẫu của witness với số nguyên hơn `4096` bit: bội số nén và số bản sao không đổi.
- Đa đồ thị có bội số `2^8192`: nhánh `min(c,k)` chạy mà không cấp phát theo giá trị bội số.
- Cặp có bội số nhỏ dẫn tới `a_uv=0`; chứng chỉ vẫn hợp lệ. Chứng chỉ sai về bậc, lát cắt và độ kết nối bị từ chối.
- 30 nghiệm HK ngẫu nhiên cân bằng trên `n=3..7`: min-cut có hướng và min-cut sau nén khớp với liệt kê mọi lát cắt. Seed cố định `20261008`.

Chạy lại: `python3 tests/test_certify_compress.py` và `ctest --test-dir build --output-on-failure`.

## Đo thời gian

`benchmarks/bench_certify_compress.py` tạo chu trình Hamilton có hướng với mẫu số 1 hoặc 4096 bit, đo một lần cho từng cấu hình bằng `perf_counter` và `tracemalloc`. Dữ liệu thô ở `results/exact_compression.csv` (Python 3.14.4, máy x86_64 8 CPU). Các số đo đơn lẻ chỉ minh họa chi phí thực thi; chúng không chứng minh thời gian đa thức.

| n | bit mẫu số | thời gian (s) | bộ nhớ Python đỉnh (byte) | số bản sao nén |
|---:|---:|---:|---:|---:|
| 6 | 1 | 0.001191 | 61,720 | 216 |
| 6 | 4096 | 0.001504 | 121,274 | 216 |
| 12 | 1 | 0.003251 | 228,088 | 1,728 |
| 12 | 4096 | 0.004858 | 425,582 | 1,728 |
| 24 | 1 | 0.031849 | 822,438 | 13,824 |
| 24 | 4096 | 0.014744 | 1,591,774 | 13,824 |
| 48 | 1 | 0.057122 | 1,242,550 | 110,592 |
| 48 | 4096 | 0.070659 | 2,068,038 | 110,592 |

Thời gian thay đổi giữa các lần chạy; so sánh 24 đỉnh cho thấy rõ nhiễu đo. Chứng minh độ phức tạp của **phần tiền xử lý này** dựa trên số lần gọi max-flow là `O(n)` và thuật toán Dinic có số phép toán đa thức theo `n,m`; phép toán trên số nguyên có độ dài bit đa thức theo độ dài đầu vào. Không suy rộng kết luận này sang thuật toán dựng cây.

## Phạm vi kết luận và công việc còn lại

Repo hiện xác nhận được đường `HK hữu tỉ → đa đồ thị bội số nhị phân → đồ thị nén`; graphic matroid partition và kiểm tra PSD hữu tỉ đã có như các thành phần độc lập. `construct-certified` nối cây với AKS trên mẫu nhỏ nhưng vét cạn và chỉ nhận `D≤10^9`. Kiểm toán sau đó đã suy ra các cận số **có điều kiện theo bổ đề nguồn** trong `EXPLICIT_THRESHOLD_AUDIT.md`. Để phát biểu đã triển khai thuật toán đa thức của Theorem 1.1, còn phải kiểm toán độc lập các bổ đề nguồn, cài oracle LP/lồi hữu tỉ, khung vector, ký dấu xác định, bước làm thưa, vòng lặp dựng cây, rồi nối đầu ra với AKS trên đường số học chính xác. Khóa luận cần ghi đúng ranh giới này.
