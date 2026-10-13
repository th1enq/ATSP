# Một bước trên mẫu nhiều hướng — 2026-10-11

## Kết quả đã kiểm tra

Đã hoàn thành một bước sparsification trên đa đồ thị **ba đỉnh, 16 cạnh**, gồm 8 bản sao cạnh `0–1` và 8 bản sao cạnh `1–2`.

- Đầu vào `r=8`, extraction từ terminal witness chọn 7 cây, tức 14 cạnh.
- Có **hai hướng ma trận khác nhau**, không cùng một ray như mẫu hai đỉnh trước.
- Ký dấu Appendix A giữ **6 cạnh** và packing đầu ra có **3 cây**; `r_next=3` thỏa giới hạn halving.
- **343 khoảng SDP** đã hoàn thành với primal–dual certificate; phát lại độc lập đều hợp lệ.
- Thời gian construction đo được **32,666 giây**, không gọi inner ellipsoid. SDP có ma trận 4×4 và **21 biến**.

**Phạm vi:** hai projector của mẫu này trực giao chính xác. Đây là kết quả nhiều hướng, nhưng vẫn thuộc một lớp có cấu trúc; chưa phải lời giải hiệu quả cho SDP không giao hoán. Terminal witness được cung cấp riêng, chưa sinh bằng continuation. Chưa có benchmark TSPLIB mới.

## Thay đổi thuật toán

`scripts/sdp_orthogonal.py` nhận các nhóm `A_i=trace(A_i) R_j`, với các projector hạng một khác nhau. Mã kiểm tra bằng số hữu tỉ:

`R_j^2=R_j`, `Tr(R_j)=1`, `R_j R_k=0` khi `j!=k`.

Nếu không đạt điều kiện, nhánh này bị từ chối. Từ các nhóm, đặt

`S=sum_j s_j R_j`, `F(U)=sum_j mu_j R_j U R_j`.

Các mode chia sẻ biến `t`. Với `u_j=t^2-s_j^2>4 mu_j`, chọn

`k_j=2/(1+sqrt_lower(1-4 mu_j/u_j))`,

`x_j=k_j/(t-s_j)`, `y_j=k_j/(t+s_j)`.

Căn dưới dyadic cho `k_j` nằm giữa hai nghiệm của phương trình Schur. Mã vẫn kiểm tra toàn bộ primal LMIs và box sau khi dựng `X,Y`, không coi công thức proposal là chứng nhận mặc định. Các mode bổ sung dùng `x0=y0=1/t`.

Decimal tìm proposal cho `t` bằng đạo hàm một chiều của objective. `t` được chuyển thành dyadic hữu tỉ. Độ chính xác Decimal và tìm kiếm chỉ phục vụ proposal: **primal feasible, dual PSD/stationarity và gap hữu tỉ đủ nhỏ mới cho phép trả interval**. Không giảm accuracy của oracle nguồn.

Trọng số dual của từng mode được lấy từ các phương trình complementarity, rồi chuẩn hóa toàn bộ để `Tr(P1+P2)=1`. Các `Q` được tính theo coupling operator để stationarity khớp chính xác; `W` dùng căn dưới dyadic. Bộ kiểm tra đối ngẫu chung xác nhận PSD và stationarity đầy đủ.

Nhánh cũ cho một ray vẫn hoạt động. Nhánh mới xử lý nhiều ray trực giao; generic dual/fallback vẫn dành cho các đầu vào khác, nhưng có thể chưa tìm được gap đủ sát.

## Tối ưu chi phí thực thi

Lần đầu với nhánh nhiều hướng, construction đã chứng nhận được 134 interval nhưng hết ngân sách 60 giây trước khi xong. Chi phí dựng LMI được giảm bằng:

1. Gộp các ma trận `A_i` trùng nhau trong coupling operator, cộng các hệ số `psi_i` chính xác.
2. Dùng `A B A=Tr(A B) A` **chỉ khi đã kiểm tra A hạng tối đa một**. Ma trận hạng cao dùng phép nhân đầy đủ với các hệ số khác 0.
3. Trong kiểm tra dual, bỏ phép nhân hệ số 0 và bỏ multiplier bằng 0 sau khi kiểm tra kích thước.

Sau bước 1–2, cả 343 interval và bước sparsification chạy xong trong **43,656 giây**. Sau bước 3, thời gian là **32,666 giây**. Hai lần chạy hoàn chỉnh có cùng hash chuỗi điểm/target separator, cùng 343 truy vấn và cùng accuracy. Đây là một lần đo mỗi phiên bản, không phải thống kê tốc độ trên mọi input.

Các accuracy SDP của lần chạy là `1/8` và `6193/9710862336000000` (khoảng `6,38e-13`). Không cần hạ precision để chạy qua.

## Mẫu không trực giao

Đã thêm mẫu tam giác ba đỉnh, mỗi cặp có 8 cạnh song song, cùng terminal witness hợp lệ. Nhánh nhiều ray trực giao từ chối cấu trúc này. Chẩn đoán đặt **ngân sách inner ellipsoid bằng 0** dừng tại query SDP đầu tiên bằng `IterationLimitReached`; không có interval hoặc bước thành công được ghi nhận.

Phép thử này xác nhận phạm vi của nhánh mới và việc fallback không trả chứng nhận thiếu cận. Nó **không chứng minh** mẫu tam giác vô nghiệm, không thể chạy được, hoặc sẽ hết ngân sách nếu cho ellipsoid chạy lâu hơn. Generic dual hiện chưa đủ sát để khép interval cho truy vấn này mà không tìm thêm.

## Dữ liệu và chạy lại

Đầu vào/witness:

- `instances/general-sparsification/path-three.json`, `path-three-terminal.json`;
- `instances/general-sparsification/triangle-three.json`, `triangle-three-terminal.json`.

Kết quả:

- `results/general-sparsification/path-three-dual.json`: chứng nhận bước hoàn chỉnh;
- `results/appendix-a-profile/path-three-dual.json.gz`: 343 chứng nhận SDP và số đo;
- `path-three-before-coupling.json.gz`, `path-three-before-inner.json.gz`: các số đo lịch sử;
- `results/general-sparsification/triangle-three-diagnostic.json`, `results/appendix-a-profile/triangle-three-diagnostic.json`: chẩn đoán budget 0, trạng thái incomplete.

Phát lại không chạy optimizer:

```sh
python3 scripts/check_sdp_value.py results/appendix-a-profile/path-three-dual.json.gz
python3 scripts/general_sparsification.py verify results/general-sparsification/path-three-dual.json
```

Chạy lại construction và lưu cả chứng nhận bước lẫn các interval:

```sh
python3 benchmarks/profile_appendix_a.py \
  --input instances/general-sparsification/path-three.json \
  --terminal-witness instances/general-sparsification/path-three-terminal.json \
  --iteration-cap 0 --seconds 60 --certificates \
  --output /tmp/path-three-dual.json.gz --step-output /tmp/path-three-step.json
```

Ngân sách ellipsoid bằng 0 vẫn cho phép proposal đã chứng nhận trả interval; cap này chỉ ngăn inner ellipsoid cập nhật, không vô hiệu hóa checker. File `.json.gz` được nén để tránh giữ hàng chục MB JSON thô; checker đọc được trực tiếp.

## Kiểm tra và giới hạn chất lượng

Bộ kiểm tra cuối: **82 test**, không có lỗi; **1 test LP/SciPy bỏ qua** do thiếu phụ thuộc tùy chọn. Test mới gồm nghiệm nhiều mode đối xứng có giá trị biết trước, hai projector xoay hữu tỉ với weights/signing khác nhau, từ chối ray không trực giao, và đối chiếu coupling rank-one/rank-two với phép nhân đầy đủ.

Chứng nhận bước vẫn dùng epsilon rất lỏng của nguồn tại `r=8`: cut load factor `2097153/2`, ratio bound `2796204`. Trên mẫu đường đi này, mỗi nhóm cạnh thực tế giảm `8 -> 3`, nên mọi cut có tỷ lệ **3/8**; đó là tính chất của riêng mẫu này. Không suy ra thinness tốt cho dữ liệu lớn từ cut ratio của mẫu nhỏ.

**Mốc nhiều hướng đã đạt trong lớp trực giao.** Công việc tiếp là tạo proposal primal–dual đủ sát cho các hướng không giao hoán, bắt đầu bằng mẫu tam giác đã lưu, rồi mới sinh witness bằng continuation và ghép lại benchmark thực tế. Những phần này chưa hoàn thành.
