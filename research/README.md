# Hồ sơ nghiên cứu chọn đề tài khóa luận

**Đề tài được chọn:** Thuật toán chính xác cho Minimum Hitting Set với
kiểm tra hoàn tất hai đỉnh bằng bitset đối ngẫu.

Đây là một nghiên cứu algorithm engineering trên CPU: có thuật toán cụ
thể, lập luận đúng đắn, mã nguồn chạy được, baseline từ paper, dữ liệu
chính thức và các thí nghiệm loại bỏ thành phần. Không cần GPU.

Kết quả định lượng cuối cùng nằm trong [RESULTS.md](RESULTS.md). Hồ sơ
nguồn ở [LITERATURE.md](notes/LITERATURE.md); thuật toán, độ phức tạp và
chứng minh ở [METHOD.md](notes/METHOD.md). Dữ liệu thô, nghiệm và metadata
đều được giữ trong `results/`, không chỉ có một bảng tổng hợp.

## Nội dung đóng góp phù hợp khóa luận

1. Thiết kế và phân tích thủ tục chính xác cho phần nghiệm còn thiếu tối
   đa hai đỉnh, dùng đồng thời hai chiều của ma trận incidence. Làm rõ vì
   sao có thể kiểm tra trên toàn bộ tập đỉnh và vẫn cắt nhánh an toàn.
2. Tích hợp thủ tục vào tìm kiếm theo kích thước nghiệm, cận tổng gain và
   phân nhánh theo hyperedge; xây dựng solver đầy đủ có fallback sang UzL,
   giữ nguyên ngữ nghĩa “chỉ xuất nghiệm khi đã chứng minh tối ưu”.
3. Đánh giá trên toàn bộ bộ private PACE HS 2025 và phân tích riêng nhóm
   dense nhỏ, có ablation, đổi nhãn dữ liệu, bản biên dịch portable, và
   kiểm chứng tối ưu độc lập trên các instance thật.

Phạm vi bài toán là **explicit, unweighted Minimum Hitting Set**. Bitset,
branch-and-bound và portfolio là kỹ thuật đã biết; đóng góp không được
viết thành việc “phát minh bitset” hoặc “giải P=NP”. Xem ranh giới tính mới
và những điều chưa chứng minh trong hai ghi chú liên kết ở trên.

## Chạy solver

Từ thư mục KLTN, với các binary đã được biên dịch trong phiên nghiên cứu:

```bash
python3 research/scripts/solve.py \
  < research/data/pace2025/private/hs/exact/private_exact_047.hgr \
  > /tmp/hs-solution.txt
```

Binary chuyên biệt đọc/ghi theo định dạng PACE:

```bash
research/bin/dense_v1 \
  < research/data/pace2025/private/hs/exact/private_exact_001.hgr
```

Giới hạn bản chuyên biệt là n,m≤512. `solve.py` xử lý các instance lớn
hơn bằng UzL. Probe mặc định 10 giây; đổi bằng `--dense-seconds`. Ngân
sách của cả tiến trình, nếu cần, phải được đặt bởi benchmark runner.

Biên dịch lại bằng `bash research/scripts/build.sh`. Cần g++, Rust/Cargo,
CMake, make và libclang cho UzL. Trong NixOS của máy này đã dùng
`nix-shell -p gnumake clang`; các đường dẫn thư viện và log build thực tế
được ghi trong `results/`. Mã và dữ liệu upstream được pin bằng commit và
SHA-256 trong `manifest.json`.

Để biên dịch adapter BIB sau khi cài HiGHS, chạy
`bash research/scripts/build_bib.sh /path/to/highs-prefix`.
Trong phiên này prefix là
`/nix/store/6a27mnj2a2kxd0b9hvva0nnfk1xdz2mz-highs-1.12.0`.

## Tái lập kiểm chứng

```bash
python3 research/scripts/check_exact.py
python3 research/scripts/check_regressions.py
research/bin/verify_enumeration \
  research/data/pace2025/private/hs/exact/private_exact_047.hgr \
  research/results/dense-v1-private/private_exact_047-r0.stdout
```

`check_exact.py` dùng vét cạn độc lập trên bài nhỏ. `check_regressions.py`
kiểm tra các biên 64 bit, n/m tới 512 và các đường fallback. Chương trình
`verify_enumeration` chỉ vét cạn các tập con theo chỉ số tăng dần, không
dùng cận, pivot hay thủ tục hai đỉnh của thuật toán đề xuất.

## Tái lập benchmark chính

```bash
python3 research/scripts/confirm.py \
  --solvers dense,uzl --seconds 10 --cpu 2 --output another-dense-run
python3 research/scripts/confirm.py \
  --solvers portfolio,uzl --all-private --shard 0/1 \
  --seconds 10 --cpu 2 --output another-full-run
```

Runner không ghi đè một thư mục kết quả đã có. Mỗi solver chạy một lần
một, được pin vào CPU chỉ định; lưu cả wall time, CPU time, timeout,
objective, nghiệm, stderr, hash binary và hash input. Vòng toàn bộ private
được chia thành ba shard trên ba lõi vật lý khác nhau trong phiên này.
Do đó đây không phải thí nghiệm trên máy hoàn toàn rảnh.

Timeout không có objective và không được tính là giải tối ưu. Các bảng
với ngưỡng 10 giây không thay thế bảng xếp hạng PACE dùng 1800 giây.

Đối chứng BIB native đã sửa runner có thể tái lập bằng
`confirm.py --solvers bibco_native,biblp_native --seconds 10 --cpu 2`.
Các đồ thị kiểm tra bổ sung được sinh bằng `holdout.py generate` sau khi
đã cố định binary; không gộp chúng vào điểm benchmark chính thức.

## Bố trí các hiện vật

| Đường dẫn | Nội dung |
|---|---|
| `scripts/dense_v1.cpp` | Phiên bản thuật toán được chọn và cố định cho vòng xác nhận |
| `scripts/dense.cpp` | Biến thể nghiên cứu: bỏ oracle, bỏ cận, hoặc học witness |
| `scripts/dense_v0.cpp` | Bản đầu tiên, trước khi loại chi phí sắp xếp trong oracle |
| `scripts/contract.cpp` | Phép co cặp sang MaxSAT đã thử nhưng không chọn |
| `scripts/solve.py` | Solver kết hợp chính xác, có fallback |
| `scripts/bib_hs.cpp`, `bib_ds.cpp`, `bib_direct.py` | Adapter baseline IJCAI 2024; không sửa thuật toán upstream |
| `scripts/map_ds.py` | Phục hồi rồi kiểm tra đầy đủ ánh xạ DS–HS cho baseline |
| `scripts/sat_baseline.py`, `milp.py` | Baseline encoding chuẩn |
| `vendor/` | Mã nguồn tác giả, giữ riêng để đối chiếu |
| `data/pace2025/` | Bộ dữ liệu chính thức, sparse checkout public/private exact |
| `results/` | Log và nghiệm từng lượt chạy, kiểm chứng, bảng và biểu đồ |

## Đánh giá mức độ tự tin

Có bằng chứng thực nghiệm cụ thể để chọn hướng này cho khóa luận, vượt
mức một ý tưởng chưa được hiện thực. Khối lượng lý thuyết, hiện thực và
đánh giá đã xác định rõ. Có cơ sở để phát triển thành một bài algorithm
engineering, nhưng chưa có căn cứ cam kết nhận paper, SOTA toàn diện ở
ngân sách cuộc thi, hoặc giải một open problem lý thuyết. Những khẳng định
đó không được dùng trong tên đề tài hay kết luận của hồ sơ này.
