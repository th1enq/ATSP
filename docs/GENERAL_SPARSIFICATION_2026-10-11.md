# Luồng một bước sparsification theo nguồn — 2026-10-11

## Đã triển khai

`scripts/general_sparsification.py` nối **continuation ellipsoid → extraction/packing → gradient frame → Appendix A → kiểm tra chứng nhận**. Luồng này không gọi tìm kiếm các ma trận `c L_H`, balancing, Frobenius hay liệt kê tất cả cây/cut. Các backend thực nghiệm cũ vẫn có giao diện riêng.

Đầu vào là đa đồ thị **đã tường minh**, JSON `{n, edges, r}`; mỗi phần tử `edges` là một bản sao cạnh với đỉnh đánh số từ 0. `r` được kiểm tra bằng oracle phân hoạch trước khi chạy. Giao diện này chưa nhận trực tiếp ma trận chi phí TSPLIB hay bội số nhị phân: bước HK/nén và AKS có sẵn trong pipeline khác, chưa ghép vào luồng mới.

Mỗi đáp ứng continuation được lưu bằng phân số chính xác. Bộ `verify` phát lại đáp ứng bằng separator, kiểm tra invariant và shortcut cone, rồi kiểm tra:

- các cây rời nhau và cạnh low resistance;
- weights dương và leverage của frame, bằng nghịch đảo ma trận hữu tỉ;
- khối trên `L_A <= L_B/2 + epsilon X`;
- khối dưới của frame, bằng phép đồng dư trên Laplacian có trọng số, không cần căn ma trận;
- ký dấu trên các cột rational đã chuẩn hóa;
- packing thực tế `r/4 <= r_next <= r/2`, cut bound và ratio bound.

Bộ kiểm tra không chạy lại ellipsoid, gradient hay trình tìm ký dấu. Nó xác nhận các bất đẳng thức của **đầu vào đó**, không xác nhận nguồn gốc thuật toán của một vector ký dấu được cung cấp bên ngoài.

## Đối chiếu nguồn và mã

Nguồn được đọc từ clone `math`, commit `adc7f1241b42e322a6451854ab7e4b4c146bf78a`, thư mục `preprints/A-polynomial-time-construction-of-strong-thin-trees-September-23-2026/build/source/sections/`.

| Phần nguồn | Mã thực thi | Kiểm tra và giới hạn |
|---|---|---|
| Mục 3, lịch `s=(1+t)s`, `Q=Q-2grt` | `continuation_state.py`, `continuation_solver.py` | Replay từng response; đã thêm truyền giới hạn số vòng ellipsoid và lưu response. Chưa kiểm toán độc lập inner ball promise. |
| K cone và extraction low resistance | `verify_shortcut_cone`, `finalize_shortcut` | Chứng nhận PSD + multiplier tam giác và packing matroid. Số cây chưa đủ thì bước bị từ chối. |
| Mục 4, normalized frame | `find_frame_weights` | Gradient backend; kiểm tra leverage chính xác. Không dùng balancing trong luồng mới. |
| Mục 5, hai khối và padding | `prepare_stacked_columns`, `sign_stacked_data_appendix_a` | Kiểm tra signed matrix và hai khối đầu ra. Padding có thể triệt tiêu bằng cặp dấu; không cần dựng toàn bộ các bản sao. Precision/bit complexity chưa được chứng minh độc lập toàn bộ. |
| Appendix A | `AppendixASigner` | Có thuật toán finite difference/SDP. Giới hạn số bước không chặn thời gian của một truy vấn SDP; CLI bổ sung ngân sách wall time. Các cận đạo hàm/inner ball vẫn cần audit sâu. |
| Lemma 6.1, packing/cut | `verify_sparsification`, `verify_frame` | Chứng nhận instance kiểm tra trực tiếp packing, khối trên và dưới. Không suy ra bảo đảm tiệm cận cho mọi input từ các test nhỏ. |
| Mục 6, dừng dưới `R0` | `run_step` | Mặc định dùng ứng viên **có điều kiện** `R0=2^4097`; dưới ngưỡng trả một cây và ghi `rounds=0`. Đây không phải bước sparsification thành công. |

Hai khoảng trống được sửa trực tiếp: đường chạy continuation trước đây không truyền giới hạn ellipsoid xuống từng response, và kết quả automatic step chưa lưu weights/edge order/epsilon để kiểm tra độc lập. Bộ replay mới cũng kiểm tra khối dưới của frame, vốn chưa nằm trong checker sparsification cũ (checker cũ dùng packing thực tế để chứng nhận kết luận).

## Chạy lại

Nhánh dừng đúng cấu trúc nguồn:

```sh
python3 scripts/general_sparsification.py step \
  instances/general-sparsification/parallel-eight.json \
  --output /tmp/source-small.json
python3 scripts/general_sparsification.py verify /tmp/source-small.json
```

Thử một đáp ứng continuation thật, ngoài miền hứa hẹn đủ lớn:

```sh
python3 scripts/general_sparsification.py step \
  instances/general-sparsification/response-small.json \
  --below-cutoff --max-steps 1 --max-response-iterations 2000 --seconds 30 \
  --output /tmp/continuation-prefix.json
```

Chạy phần sau extraction với một **terminal witness cung cấp riêng**:

```sh
python3 scripts/general_sparsification.py step \
  instances/general-sparsification/parallel-eight.json \
  --terminal-witness instances/general-sparsification/parallel-eight-terminal.json \
  --signing-cap 20 --seconds 30 --output /tmp/appendix-a-budget.json
```

Witness này có `X=L_H`, `s=2`, `Q=8`; checker xác nhận điều kiện terminal cho input, nhưng **nó không được tạo ra bằng lịch continuation**. Trường `origin` lưu sự khác biệt này và checker từ chối gán nó thành `source-initial-state`.

Exit code 0: nhánh dừng hoặc chứng nhận bước thành công. Exit code 2: quá trình chưa hoàn thành. `incomplete` có thể lưu prefix hợp lệ; đó không phải chứng minh vô nghiệm. File malformed hoặc giả thiết đầu vào sai bị từ chối.

## Kết quả hiện tại

Các file chạy thật nằm ở `results/general-sparsification/`:

- `source-small-branch.json`: trả cây, **0 vòng sparsification**, theo nhánh dưới ngưỡng nguồn.
- `continuation-prefix.json`: giải được **1 response ellipsoid thật**, replay thành công; dừng theo cap trước khi terminal.
- `appendix-a-budget.json`: đi qua kiểm tra terminal witness, extraction và frame; **hết ngân sách 30 giây ở Appendix A**, chưa có chứng nhận bước hoàn chỉnh.

Test checker có một chứng nhận cung cấp riêng `r=8 → 4`, cut factor `1/2`, được tạo bằng backend Frobenius cũ để kiểm tra replay và chống sửa dữ liệu. Đây là **fixture của bộ kiểm tra**, không được tính là kết quả thành công của backend nguồn mới.

Chưa có lần chạy hoàn chỉnh từ `source-initial-state` qua một vòng general sparsification. Chưa có kết quả TSPLIB mới hay bằng chứng chất lượng đã tăng. Ngưỡng `R0` ở trên là cận đủ có điều kiện trong `EXPLICIT_THRESHOLD_AUDIT.md`, không phải ngưỡng nhỏ nhất hay một giả thiết đã kiểm toán độc lập đầy đủ.

## Công việc tiếp theo có căn cứ

Điểm cần xử lý trước khi mở rộng benchmark là chi phí của oracle SDP trong Appendix A: giới hạn số bước ngoài không kiểm soát số truy vấn và thời gian bên trong. Sau đó mới thử extraction đầy đủ dưới một miền tham số được chứng nhận hoặc có witness đủ điều kiện. Thay đổi thực nghiệm để giảm ngưỡng cần có lập luận riêng; việc bỏ ngưỡng nguồn không tự tạo bảo đảm tổng quát.

## Kiểm tra mã

`python3 -m unittest discover -s tests -v`: 66 test trước khi bổ sung callback báo pha, qua với 1 test LP/SciPy bỏ qua do thiếu phụ thuộc tùy chọn. Sau đó 8 test của module mới và các test sparsification/backend thực nghiệm được chạy lại; bao gồm cap Appendix A thật, replay không gọi optimizer, sửa response, thiếu trace, sai ký dấu/weights/packing/bound và khối dưới frame.

## Cập nhật profiling và ngân sách

Đã đo và tối ưu oracle SDP/cập nhật ellipsoid; thêm `--sdp-iteration-cap`, `--value-query-cap` và sửa việc phân biệt operational cap với volume cutoff. Xem [APPENDIX_A_PROFILE_2026-10-11.md](APPENDIX_A_PROFILE_2026-10-11.md). Các JSON ngân sách 30 giây ở thư mục kết quả ban đầu là số đo lịch sử trước tối ưu, không bị ghi đè.

## Cập nhật chứng nhận đối ngẫu

Sau khi bổ sung primal–dual oracle, đã có một bước Appendix A hoàn chỉnh trên terminal witness cung cấp sẵn của mẫu hai đỉnh, `r=8 -> 3`. Đây chưa phải lần chạy từ `source-initial-state`. Xem [SDP_DUAL_AUDIT_2026-10-11.md](SDP_DUAL_AUDIT_2026-10-11.md).

## Cập nhật mẫu nhiều hướng

Đã có bước hoàn chỉnh trên mẫu ba đỉnh/hai hướng trực giao, `r=8 -> 3`, sử dụng terminal witness cung cấp sẵn. Chứng nhận được phát lại độc lập. Xem [MULTI_DIRECTION_SDP_2026-10-11.md](MULTI_DIRECTION_SDP_2026-10-11.md).
