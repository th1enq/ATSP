# Nguồn chính đã đọc và lựa chọn hướng

Ngày khảo sát: 2026-10-19. Chỉ dùng paper, trang cuộc thi và repository tác giả
để xác định thuật toán, dữ liệu và baseline. Không dùng các tuyên bố tự đăng
về P=NP làm căn cứ chọn đề tài.

| Công trình | Vai trò trong nghiên cứu này |
|---|---|
| [An Efficient Branch-and-Bound Solver for Hitting Set, ALENEX 2022](https://arxiv.org/html/2110.11697) | Các cận dưới, packing và costly-discard. Đã tải và chạy findminhs v2.1.0; repository nói bản hiện tại có bổ sung so với bản paper. Không gọi đây là tái lập nguyên xi các con số của paper. |
| [UzL Solver for Dominating Set and Hitting Set, IPEC 2025](https://doi.org/10.4230/LIPIcs.IPEC.2025.39) | Baseline chính, đã biên dịch mã nguồn gốc. Paper mô tả presolve + EvalMaxSAT, nhánh clique nhỏ và nhánh SAT cho perfect matching đặc biệt. |
| [Minimum Hitting Set Computation via Core-Guided MaxSAT Solving, IPEC 2025](https://doi.org/10.4230/LIPIcs.IPEC.2025.37) | Cho thấy khởi tạo MaxSAT bằng packing/clique đã có; không dùng ý tưởng này đơn lẻ làm đóng góp mới. |
| [Analyzing Reformulation Performance in Core-Guided MaxSAT Solving, SAT 2025](https://doi.org/10.4230/LIPIcs.SAT.2025.26) | Một hướng thay thế có chiều sâu: cấu trúc OLL DAG và heuristic reformulation. Chưa chọn vì cần can thiệp sâu hơn vào solver và chưa có cải tiến thực nghiệm tương ứng. |
| [Exactly Solving Minimum Dominating Set and Its Generalization, IJCAI 2024](https://www.ijcai.org/proceedings/2024/0780.pdf) | BIBCO/BIBLP là đối thủ bổ sung cần thiết. Đã lấy [mã nguồn tác giả](https://github.com/forgottencsc/IJCAI24-MDS), biên dịch với HiGHS 1.12.0 và viết adapter I/O. |
| [Shadoks Approach to Minimum Hitting Set and Dominating Set, IPEC 2025](https://doi.org/10.4230/LIPIcs.IPEC.2025.34) | Baseline độc lập khác; dùng binary exact do tác giả cung cấp trong repository. |
| [CHILS, SEA 2025 / arXiv 2412.14198](https://arxiv.org/abs/2412.14198) | Hướng MWIS có code và benchmark, đã khảo sát ở mức lựa chọn ban đầu. Chưa thực nghiệm, không có bằng chứng để xếp trên hướng Hitting Set đã chạy. |
| [Efficient and Reliable Hitting-Set Computations for the Implicit Hitting Set Approach, AAAI 2026](https://doi.org/10.1609/aaai.v40i17.38439) | Related work mới cần xét nếu mở rộng sang weighted/incremental/implicit HS. Bản hiện thực hiện tại chỉ giải explicit unweighted HS. |

## Dữ liệu và mục tiêu đánh giá

- [Bộ dữ liệu do ban tổ chức PACE 2025 công bố](https://github.com/MarioGrobler/PACE2025-instances), gồm cả public và private đã giải mật.
- [Quy định Hitting Set](https://pacechallenge.org/2025/hs/): exact track dùng 1800 giây/instance, RAM 16 GB và chấm trên 100 private instances.
- [Bảng xếp hạng](https://pacechallenge.org/2025/results/): UzL đứng đầu exact HS với 79 instance. Đây là kết quả lịch sử trên máy và ngân sách cuộc thi, không được so trực tiếp với số instance giải trong 10 giây ở máy này.
- [Báo cáo PACE 2025, IPEC 2025](https://doi.org/10.4230/LIPIcs.IPEC.2025.32) mô tả các instance Watts–Strogatz khó và sự khác biệt public/private. Do đó báo cáo tách rõ cả bộ private với nhóm nhỏ/dense; không đánh đồng thành tích trên nhóm con với SOTA toàn bài toán.

## Đối chứng công bằng cho BIB

Bản thứ nhất chuyển HS thành EMDSP trên đồ thị incidence bipartite theo
định nghĩa của paper. Cách này hợp lệ nhưng có thể làm tăng overhead.
Vì thế đã tìm thêm các instance DS gốc tương đương trong bộ private,
phục hồi đổi nhãn bằng color refinement, rồi **kiểm tra chính xác** rằng
multiset closed neighborhoods sau đổi nhãn bằng multiset hyperedge HS.
Đã tìm và kiểm tra được đủ 30 ánh xạ.

`bib_direct.py` cho BIB chạy trên đồ thị DS gốc rồi đổi nhãn nghiệm ngược
về HS. Như vậy baseline này được hưởng biểu diễn đồ thị thuận lợi; lợi thế
không đến từ việc buộc BIB chạy trên đồ thị incidence lớn gấp đôi. Ánh xạ
dataset chỉ dùng trong adapter baseline, tuyệt đối không dùng trong solver
đề xuất. Mọi nghiệm đổi nhãn vẫn được kiểm tra trên input HS ban đầu.

## Điều chưa được chứng minh

Chưa chạy toàn bộ các solver từng tham gia PACE với đủ 1800 giây trên từng
instance. Chưa xác định một ID cụ thể nào là instance trước đây mọi đội đều
không giải được. Không tuyên bố giải open problem lý thuyết, lập kỷ lục mới,
hay chắc chắn được nhận paper từ các thực nghiệm ngắn này.
