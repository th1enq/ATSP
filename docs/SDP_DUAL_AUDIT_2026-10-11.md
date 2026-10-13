# Cận SDP bằng chứng nhận primal–dual — 2026-10-11

## Kết quả

Đã kiểm toán lại bước cập nhật cận dưới và bổ sung chứng nhận đối ngẫu hữu tỉ. Trên cùng terminal witness hai đỉnh/tám cạnh từng hết 30 giây ở truy vấn potential đầu tiên, backend Appendix A nay hoàn thành **63 truy vấn potential/SDP và một bước sparsification** trong **1,510 giây**, không gọi ellipsoid. Các khoảng SDP đã được phát lại độc lập bằng primal witness và dual multiplier.

**Phạm vi:** các ma trận SDP của đầu vào này cùng nằm trên một hướng hạng một. Terminal witness được cung cấp riêng, đã kiểm tra, chưa được sinh bằng continuation. Kết quả không chứng minh general continuation đã chạy xong, không phải benchmark TSPLIB, và chưa xác nhận thuật toán nguồn có hiệu năng tốt trên đầu vào bất kỳ.

## 1. Kiểm toán volume/collapse

Oracle cũ cập nhật `low=max(low,target-accuracy/8)` khi inner ellipsoid volume/collapse cutoff. Suy luận đó phụ thuộc vào inner-ball promise và các cận rounding của weak optimization. Repo chưa kiểm toán độc lập đầy đủ các giả thiết này; riêng việc xuất hiện exception không phải chứng nhận đối ngẫu.

**Đường trả interval hiện tại chỉ dùng cận dưới có chứng nhận kiểm tra chính xác.** Khi ellipsoid chạm volume/collapse mà chưa có chứng nhận đủ sát, oracle báo `UncertifiedSDPBound`, không nâng cận dưới bằng cutoff. Operational cap vẫn báo `IterationLimitReached`. Cả hai có thể khiến luồng dừng `incomplete`, không phải một khoảng nghiệm đã chứng nhận.

Đây là thay đổi có chủ đích về phạm vi bảo đảm: các interval đã trả có lower certificate; nhưng fallback chưa chứng minh luôn tìm được chứng nhận đủ sát cho mọi SDP.

## 2. Chứng nhận đối ngẫu tổng quát

Viết các LMI đã có trong mã dưới dạng

`F_j(u) = C_j + sum_k u_k A_jk >= 0`, objective `c.u`.

Một danh sách multiplier hữu tỉ `Z_j` là chứng nhận nếu:

- mọi `Z_j` đối xứng PSD;
- `sum_j <Z_j,A_jk> = c_k` cho từng biến;
- bound khai báo đúng bằng `-sum_j <Z_j,C_j>`.

Với mọi primal feasible, PSD inner product không âm, nên

`c.u = sum_j <Z_j,F_j(u)> - sum_j <Z_j,C_j> >= bound`.

Lập luận này dùng weak duality trực tiếp, không cần strong duality hoặc volume theorem. Bộ kiểm tra `sdp_dual_certificate.py` kiểm tra từng điều kiện bằng `Fraction` và PSD checker hữu tỉ. Đầu mút trên có primal point được separator chấp nhận; độ rộng interval phải không vượt accuracy yêu cầu.

Với hai Schur LMIs của Appendix A, đặt multiplier block

`Z_j = [[P_j,-W_j],[-W_j,Q_j]]`.

Chọn

`Tr(P1+P2)=1`, `Q1=epsilon I+F(P2)`, `Q2=epsilon I+F(P1)`.

Như vậy stationarity khớp objective, với `F(U)=384 sum_i psi_i A_i U A_i`. Giá trị dual là

`Tr(S(P1-P2)) + 2 Tr(W1+W2)`.

Các multiplier của LMI box được đặt bằng 0. Constructor chung dùng `P1=P2=I/(2d)` và `W=wI` với `w^2<=epsilon/(2d)`; nó áp dụng cả khi các ma trận không cùng hướng. Cận này có thể còn yếu. Ma trận `F(P)` PSD vì các `A_i` PSD và `psi_i>=0`; checker vẫn kiểm tra multiplier PSD trực tiếp.

## 3. Trường hợp cùng hướng

Nếu mọi ma trận khác 0 có `A_i=trace(A_i) R`, và checker xác nhận `R^2=R`, `Tr(R)=1`, thì

- `S=s R`;
- `F(U)=mu R U R`, với `mu=384 sum_i psi_i trace(A_i)^2`.

Mã tạo các `P`, `Q`, `W` từ tổ hợp hữu tỉ của `R` và `I-R`. Căn vô tỉ được thay bằng **cận căn dưới dyadic**, rồi các multiplier được kiểm tra PSD và stationarity chính xác. Trọng số được chuẩn hóa để trace bằng 1 chính xác.

Primal proposal cũng dùng dạng `X=xR+x0(I-R)`, `Y=yR+y0(I-R)`. Mã tính `t` từ các điều kiện Schur rồi kiểm tra lại **toàn bộ LMI**, kể cả box. Không bỏ biến theo một phép biến đổi không được kiểm tra.

Tìm proposal có dùng float và tìm kiếm một chiều. **Float không chứng nhận tối ưu hoặc tính đúng.** Chỉ primal feasible, dual feasible và khoảng cách hữu tỉ đủ nhỏ mới cho phép trả interval. Nếu proposal không đạt accuracy rất nhỏ hoặc không có cấu trúc cùng hướng, đường này không tự tuyên bố thành công; fallback vẫn có thể dừng do chưa có dual đủ sát.

Các truy vấn trong lần chạy ghi nhận đều đạt accuracy gốc. Không giảm precision để làm cho test chạy qua.

## 4. Dữ liệu và phát lại

- `results/appendix-a-profile/dual-budget.json`: thời gian, 63 truy vấn đã hoàn thành, input SDP, primal/dual certificate của từng truy vấn.
- `results/general-sparsification/appendix-a-dual.json`: chứng nhận bước đầu ra.

```sh
python3 scripts/check_sdp_value.py results/appendix-a-profile/dual-budget.json
python3 scripts/general_sparsification.py verify results/general-sparsification/appendix-a-dual.json
```

Bộ phát lại SDP dựng LMI từ input đã lưu, kiểm tra PSD/stationarity, primal feasible và primal–dual gap; không chạy trình tìm proposal hay ellipsoid. Kết quả: **63 interval hợp lệ, 0 truy vấn SDP dở dang**. Certificate bước kiểm tra lại weights, hai khối, signing, packing và cut bound.

Chạy lại construction có lưu chứng nhận SDP:

```sh
python3 benchmarks/profile_appendix_a.py --separator sparse \
  --iteration-cap 100000 --seconds 30 --certificates \
  --output /tmp/dual-budget.json
```

So với số đo cũ, đây là thay đổi về số inner solve, không chỉ nhanh hơn từng vòng ellipsoid: lần mới có **0 inner ellipsoid solve**, lần cũ 30 giây vẫn chưa hoàn tất query đầu tiên. Thời gian là một lần đo trên mẫu đặc biệt, không phải thống kê hoặc tốc độ trên benchmark.

## 5. Bước sparsification và giới hạn

Đầu vào có `r=8`; extraction từ witness chọn 7 cây. Ký dấu Appendix A giữ 3 cạnh và packing đầu ra có `r_next=3`, thỏa `r/4<=r_next<=r/2`. Trên đa đồ thị hai đỉnh này, cut thực tế duy nhất giảm từ 8 cạnh xuống 3 cạnh.

Certificate vẫn dùng epsilon theo cận nguồn `2^20*g(r)`, nên cut load factor ghi trong chứng nhận là **2097153/2**, ratio loss bound **2796204**: hợp lệ nhưng rất lỏng và không hữu ích trên mẫu nhỏ dưới cutoff. Cut thực tế `3/8` của mẫu này không được coi là một cận chất lượng cho các đồ thị khác. Không có tuyên bố đã kiểm chứng bảo đảm thinness tổng quát của nguồn.

## 6. Kiểm tra và bước tiếp

Test mới gồm: interval scalar bao nghiệm thật `2 sqrt(2)`; projector xoay hữu tỉ với signing input khác 0; generic dual trên input không cùng hướng; sửa multiplier/PSD/stationarity/bound; sửa primal/endpoint; volume không có dual bị từ chối; và một bước Appendix A thực sự hoàn thành khi ngân sách ellipsoid bằng 0.

Nút thắt tiếp theo là **tìm dual đủ sát cho các ma trận không cùng hướng**, đồng thời sinh terminal witness bằng continuation. Có thể dùng các proposal số học thực để tìm multiplier rồi chiếu/chỉnh thành chứng nhận hữu tỉ; không được dùng lower endpoint số học thực trực tiếp. Chưa nối lại TSPLIB vào backend mới.

Kết quả kiểm tra cuối: `python3 -m unittest discover -s tests -q` chạy **78 test**, không có lỗi, **1 test LP/SciPy bỏ qua** do thiếu phụ thuộc tùy chọn.

## Cập nhật nhiều hướng

Đã mở rộng sang nhiều projector trực giao và hoàn thành một bước trên mẫu ba đỉnh/hai nhóm hướng, với 343 khoảng SDP được phát lại. Xem [MULTI_DIRECTION_SDP_2026-10-11.md](MULTI_DIRECTION_SDP_2026-10-11.md). Các hướng không giao hoán vẫn cần bộ tìm dual đủ sát.
